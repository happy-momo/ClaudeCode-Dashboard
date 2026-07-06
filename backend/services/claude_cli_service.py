"""Claude Code CLI service — unified wrapper around the ``claude`` CLI.

All Claude Code *stateful* operations (plugin lifecycle, OAuth, trust, etc.)
should go through this service rather than directly editing config files.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass, field
from typing import Any, Optional

from core.errors import (
    CliNotFoundError,
    CommandFailedError,
)

logger = logging.getLogger(__name__)

# Secrets that must be masked in log output.
_SECRET_WORDS = {"token", "password", "secret", "api_key", "bearer"}


@dataclass
class CliResult:
    """Structured result from a CLI invocation."""
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


def _mask_secrets(args: list[str]) -> list[str]:
    """Return a copy of *args* with secret-like values replaced by ***."""
    masked: list[str] = []
    for arg in args:
        low = arg.lower()
        if any(w in low for w in _SECRET_WORDS):
            masked.append("***")
        else:
            masked.append(arg)
    return masked


class ClaudeCLIService:
    """Encapsulates all calls to the Claude Code ``claude`` CLI.

    Only exposes explicitly approved operations — no arbitrary command execution.
    """

    CLI_NAME = "claude"

    # ------------------------------------------------------------------
    # Basic introspection
    # ------------------------------------------------------------------

    def _resolve_cli_path(self) -> Optional[str]:
        """Return the fully-resolved path to the ``claude`` CLI, or None.

        On Windows, ``shutil.which("claude")`` may return a ``.CMD`` wrapper
        (e.g. ``claude.CMD``).  While ``shutil.which`` accepts the name without
        extension, ``subprocess.run(["claude", ...])`` on Windows raises
        ``FileNotFoundError`` because the CreateProcess API does not honour
        PATHEXT the same way the shell does.  Returning the resolved absolute
        path (including the ``.CMD`` extension) fixes this.
        """
        return shutil.which(self.CLI_NAME)

    def check_installed(self) -> bool:
        """Return True if the ``claude`` CLI is available in PATH."""
        return self._resolve_cli_path() is not None

    def get_version(self) -> Optional[str]:
        """Return the Claude CLI version string, or None if unavailable."""
        cli_path = self._resolve_cli_path()
        if not cli_path:
            return None
        try:
            import subprocess
            result = subprocess.run(
                [cli_path, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    # ------------------------------------------------------------------
    # Generic command runner (sync)
    # ------------------------------------------------------------------

    def run(
        self,
        args: list[str],
        cwd: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> CliResult:
        """Run ``claude <args>`` synchronously and return a structured result."""
        cli_path = self._resolve_cli_path()
        if not cli_path:
            raise CliNotFoundError()

        import subprocess
        cmd = [cli_path, *args]
        masked = _mask_secrets(cmd)
        logger.info("Running claude command: %s", " ".join(masked))

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout or 60,
            )
            return CliResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            raise CommandFailedError(
                details={"args": masked},
                warnings=["CLI command timed out"],
            )
        except FileNotFoundError:
            raise CliNotFoundError()

    # ------------------------------------------------------------------
    # Plugin lifecycle (CLI-only)
    # ------------------------------------------------------------------

    def plugin_install(
        self,
        plugin_ref: str,
        scope: str,
        project_root: Optional[str] = None,
    ) -> CliResult:
        """Install a plugin via ``claude plugin install``.

        The CLI determines the current project via the working directory (cwd),
        not via a ``--project`` flag.  When *project_root* is provided it is
        passed as ``cwd`` so that ``--scope project`` installs into the correct
        project.
        """
        args = ["plugin", "install", plugin_ref, "--scope", scope]
        return self.run(args, cwd=project_root)

    def plugin_uninstall(
        self,
        plugin_ref: str,
        scope: Optional[str] = None,
        project_root: Optional[str] = None,
    ) -> CliResult:
        """Uninstall a plugin via ``claude plugin uninstall``.

        The CLI determines the current project via the working directory (cwd).
        When *project_root* is provided it is passed as ``cwd`` so that
        ``--scope project`` operates on the correct project.
        """
        args = ["plugin", "uninstall", plugin_ref]
        if scope:
            args.extend(["--scope", scope])
        return self.run(args, cwd=project_root)

    def plugin_enable(
        self,
        plugin_ref: str,
        scope: Optional[str] = None,
        project_root: Optional[str] = None,
    ) -> CliResult:
        """Enable a plugin via ``claude plugin enable``.

        The CLI determines the current project via the working directory (cwd).
        When *project_root* is provided it is passed as ``cwd`` so that
        ``--scope project`` operates on the correct project.
        """
        args = ["plugin", "enable", plugin_ref]
        if scope:
            args.extend(["--scope", scope])
        return self.run(args, cwd=project_root)

    def plugin_disable(
        self,
        plugin_ref: str,
        scope: Optional[str] = None,
        project_root: Optional[str] = None,
    ) -> CliResult:
        """Disable a plugin via ``claude plugin disable``.

        The CLI determines the current project via the working directory (cwd).
        When *project_root* is provided it is passed as ``cwd`` so that
        ``--scope project`` operates on the correct project.
        """
        args = ["plugin", "disable", plugin_ref]
        if scope:
            args.extend(["--scope", scope])
        return self.run(args, cwd=project_root)

    def plugin_list(self, project_root: Optional[str] = None) -> CliResult:
        """List installed plugins as JSON.

        The CLI determines the current project via the working directory (cwd),
        not via a ``--project`` flag (which ``plugin list`` does not support).
        Passing *project_root* as ``cwd`` ensures project-scoped plugins are
        reported with the correct ``enabled`` status.
        """
        return self.run(["plugin", "list", "--json"], cwd=project_root)

    # ------------------------------------------------------------------
    # Marketplace
    # ------------------------------------------------------------------

    def marketplace_list(self) -> CliResult:
        """List configured marketplaces."""
        return self.run(["plugin", "marketplace", "list"])

    def marketplace_add(self, source: str) -> CliResult:
        """Add a marketplace source."""
        return self.run(["plugin", "marketplace", "add", source])

    def marketplace_update(self, name: Optional[str] = None) -> CliResult:
        """Update marketplace(s)."""
        args = ["plugin", "marketplace", "update"]
        if name:
            args.append(name)
        return self.run(args)
