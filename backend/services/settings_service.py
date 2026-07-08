"""Settings service — safe, atomic settings management.

Wraps ``settings.json`` reads/writes with atomic-file operations and
secret detection.  Existing routers can call ``get()``, ``patch()``,
``backup()``, and ``restore()``.

MCP servers are stored in different locations:
- Global: ~/.claude.json (mcpServers key)
- Project: <project>/.mcp.json (mcpServers key)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from config import get_config_path, get_mcp_config_path
from utils.atomic_file import (
    atomic_write_json,
    create_backup,
    patch_json_file,
    read_json_file,
)
from utils.security import detect_secrets

logger = logging.getLogger(__name__)

# Keys that are safe to patch in settings.
_SETTINGS_KEYS = {
    "disabledSkills",
    "disabledMcpServers",
    "disabledPlugins",
    "enabledPlugins",
    "allowedTools",
    "deniedTools",
    "hooks",
    "permissions",
}


class SettingsService:
    """Manages ``settings.json`` files across scopes."""

    @staticmethod
    def _settings_path(scope: str) -> Path:
        return get_config_path(scope) / "settings.json"

    @staticmethod
    def _mcp_settings_path(scope: str) -> Path:
        """Return the MCP config file path for the given scope.

        - global: ~/.claude.json
        - project: <project>/.mcp.json
        """
        return get_mcp_config_path(scope)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get(self, scope: str) -> dict[str, Any]:
        """Return the full settings dict for *scope*."""
        path = self._settings_path(scope)
        data = read_json_file(path, default={})
        if not isinstance(data, dict):
            data = {}
        return data

    async def get_mcp_settings(self, scope: str) -> dict[str, Any]:
        """Return the MCP settings dict for *scope*.

        Reads from the correct MCP config file:
        - global: ~/.claude.json
        - project: <project>/.mcp.json
        """
        path = self._mcp_settings_path(scope)
        data = read_json_file(path, default={})
        if not isinstance(data, dict):
            data = {}
        return data

    # ------------------------------------------------------------------
    # Patch (preserves unknown fields)
    # ------------------------------------------------------------------

    async def patch(self, scope: str, update: dict[str, Any]) -> dict[str, Any]:
        """Atomically patch settings for *scope*, returning the updated dict.

        Only top-level keys in *update* are applied; all other keys are kept.
        Secret detection runs on the full update payload before writing.
        """
        warnings = detect_secrets(update)
        if warnings:
            logger.warning("Secret warnings for scope %s: %s", scope, warnings)

        path = self._settings_path(scope)
        updated = patch_json_file(
            path,
            patch_func=lambda existing: {**existing, **update},
            default_factory=lambda: {},
        )
        return updated

    async def patch_mcp_settings(self, scope: str, update: dict[str, Any]) -> dict[str, Any]:
        """Atomically patch MCP settings for *scope*.

        Writes to the correct MCP config file:
        - global: ~/.claude.json
        - project: <project>/.mcp.json
        """
        warnings = detect_secrets(update)
        if warnings:
            logger.warning("Secret warnings for MCP scope %s: %s", scope, warnings)

        path = self._mcp_settings_path(scope)
        updated = patch_json_file(
            path,
            patch_func=lambda existing: {**existing, **update},
            default_factory=lambda: {},
        )
        return updated

    async def patch_mcp_servers(self, scope: str, servers: dict[str, Any]) -> dict[str, Any]:
        """Atomically set the ``mcpServers`` key in MCP settings.

        Writes to the correct MCP config file:
        - global: ~/.claude.json
        - project: <project>/.mcp.json
        """
        return await self.patch_mcp_settings(scope, {"mcpServers": servers})

    async def patch_disabled_list(
        self,
        scope: str,
        items: list[str],
        key: str = "disabledSkills",
    ) -> dict[str, Any]:
        """Atomically set a disabled-items list key."""
        return await self.patch(scope, {key: items})

    # ------------------------------------------------------------------
    # Backup & restore
    # ------------------------------------------------------------------

    async def backup(self, scope: str) -> Path:
        """Create a timestamped backup of the settings file.

        Returns the backup path.
        """
        path = self._settings_path(scope)
        return create_backup(path)

    async def backup_mcp(self, scope: str) -> Path:
        """Create a timestamped backup of the MCP settings file."""
        path = self._mcp_settings_path(scope)
        return create_backup(path)

    async def restore(self, scope: str, backup_path: str) -> dict[str, Any]:
        """Restore settings from a backup path.

        Returns the restored dict.
        """
        src = Path(backup_path)
        dst = self._settings_path(scope)
        if not src.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        atomic_write_json(dst, read_json_file(src, default={}))
        return await self.get(scope)