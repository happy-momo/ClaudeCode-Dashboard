"""Path resolution and safety helpers for Claude Code config directories.

Extracted from config.py to separate *path finding* from *security validation*.
"""

from __future__ import annotations

import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Public constants (migrated from config.py)
# ---------------------------------------------------------------------------

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18080
API_PREFIX = "/api/v1"


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _find_project_root() -> Path:
    """Find the project root by traversing up from cwd.

    Respects CLAUDE_PROJECT_DIR env var first.  Falls back to looking for
    CLAUDE.md or .claude directory.
    """
    current = Path.cwd()

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        return Path(project_dir)

    for parent in [current] + list(current.parents):
        if (parent / "CLAUDE.md").exists() or (parent / ".claude").is_dir():
            if parent.name == "backend":
                return parent.parent
            return parent

    if current.name == "backend":
        return current.parent

    return current


def get_global_config_path() -> Path:
    """Return the global Claude config directory (~/.claude)."""
    return Path.home() / ".claude"


def get_project_config_path() -> Path:
    """Return the current project's .claude directory."""
    return _find_project_root() / ".claude"


def get_config_path(scope: str) -> Path:
    """Dispatch to global or project config path based on scope string."""
    if scope == "global":
        return get_global_config_path()
    return get_project_config_path()


def get_stats_dir() -> Path:
    """Return project stats directory."""
    return get_project_config_path() / "stats"


def get_conversations_dir() -> Path:
    """Return project conversations directory."""
    return get_project_config_path() / "conversations"


def ensure_directories() -> None:
    """Create all required config directories if they don't exist."""
    dirs = [
        get_global_config_path(),
        get_global_config_path() / "skills",
        get_project_config_path(),
        get_project_config_path() / "skills",
        get_stats_dir(),
        get_conversations_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------

def resolve_safe_path(base: Path, name: str) -> Path:
    """Resolve *name* inside *base* and verify it stays within *base*.

    Raises ``ValueError`` if path traversal is detected.

    This function:
      1. Constructs the full path from base / name.
      2. Resolves symlinks (``resolve()``).
      3. Verifies the resolved path is a descendant of *base*.
    """
    target = (base / name).resolve()
    base_resolved = base.resolve()

    if not _is_descendant(target, base_resolved):
        raise ValueError(
            f"Path traversal detected: '{name}' resolves outside '{base}'"
        )
    return target


def _is_descendant(path: Path, parent: Path) -> bool:
    """Return True if *path* is equal to or inside *parent*.

    Uses the ``instem`` / ``is_relative_to`` API available from Python 3.9+.
    Falls back to string comparison for older versions.
    """
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        # Fallback for Python < 3.9
        try:
            return str(path).startswith(str(parent.resolve()) + os.sep)
        except ValueError:
            return False
