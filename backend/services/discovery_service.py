"""Discovery service — aggregate resource discovery across all scopes.

Returns a unified view of:
  - User settings and skills (~/.claude/)
  - Project settings and skills (.claude/)
  - Managed settings (read-only, platform-specific)
  - Plugin cache (read-only)
  - Claude CLI status
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_global_config_path, get_project_config_path
from services.claude_cli_service import ClaudeCLIService
from services.managed_service import get_all_managed

logger = logging.getLogger(__name__)

_cli = ClaudeCLIService()


# ---------------------------------------------------------------------------
# Resource types
# ---------------------------------------------------------------------------

class ResourceInfo:
    """Base class for resource information."""
    def __init__(
        self,
        id: str,
        name: str,
        scope: str,
        source: str,
        path: str,
        editable: bool,
        warnings: Optional[List[str]] = None,
    ):
        self.id = id
        self.name = name
        self.scope = scope
        self.source = source
        self.path = path
        self.editable = editable
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "scope": self.scope,
            "source": self.source,
            "path": self.path,
            "editable": self.editable,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Discovery functions
# ---------------------------------------------------------------------------

def discover_user_settings() -> Dict[str, Any]:
    """Discover user-level settings."""
    path = get_global_config_path() / "settings.json"
    return {
        "id": "user-settings",
        "name": "User Settings",
        "scope": "user",
        "source": "user",
        "path": str(path),
        "exists": path.exists(),
        "editable": True,
    }


def discover_user_skills() -> List[Dict[str, Any]]:
    """Discover user-level skills."""
    skills_dir = get_global_config_path() / "skills"
    if not skills_dir.exists():
        return []

    result = []
    for entry in skills_dir.iterdir():
        if entry.suffix == ".md" and entry.is_file():
            result.append({
                "id": entry.stem,
                "name": entry.stem,
                "scope": "user",
                "source": "user",
                "path": str(entry),
                "editable": True,
            })
        elif entry.is_dir() and (entry / "SKILL.md").exists():
            result.append({
                "id": entry.name,
                "name": entry.name,
                "scope": "user",
                "source": "user",
                "path": str(entry / "SKILL.md"),
                "editable": True,
            })
    return result


def discover_project_settings(project_root: Optional[str] = None) -> Dict[str, Any]:
    """Discover project-level settings."""
    if project_root:
        path = Path(project_root) / ".claude" / "settings.json"
    else:
        path = get_project_config_path() / "settings.json"

    local_path = path.parent / "settings.local.json"

    return {
        "id": "project-settings",
        "name": "Project Settings",
        "scope": "project",
        "source": "project",
        "path": str(path),
        "local_path": str(local_path),
        "exists": path.exists(),
        "local_exists": local_path.exists(),
        "editable": True,
    }


def discover_project_skills(project_root: Optional[str] = None) -> List[Dict[str, Any]]:
    """Discover project-level skills."""
    if project_root:
        skills_dir = Path(project_root) / ".claude" / "skills"
    else:
        skills_dir = get_project_config_path() / "skills"

    if not skills_dir.exists():
        return []

    result = []
    for entry in skills_dir.iterdir():
        if entry.suffix == ".md" and entry.is_file():
            result.append({
                "id": entry.stem,
                "name": entry.stem,
                "scope": "project",
                "source": "project",
                "path": str(entry),
                "editable": True,
            })
        elif entry.is_dir() and (entry / "SKILL.md").exists():
            result.append({
                "id": entry.name,
                "name": entry.name,
                "scope": "project",
                "source": "project",
                "path": str(entry / "SKILL.md"),
                "editable": True,
            })
    return result


def discover_plugin_cache() -> List[Dict[str, Any]]:
    """Discover plugin cache entries (read-only)."""
    cache_dir = get_global_config_path() / "plugins" / "cache"
    if not cache_dir.exists():
        return []

    result = []
    for entry in cache_dir.iterdir():
        if not entry.is_dir():
            continue

        # Try to read plugin.json
        manifest_paths = [
            entry / "plugin.json",
            entry / ".claude-plugin" / "plugin.json",
        ]
        manifest = None
        for mp in manifest_paths:
            if mp.exists():
                try:
                    import json
                    manifest = json.loads(mp.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                break

        if manifest:
            result.append({
                "id": manifest.get("id", entry.name),
                "name": manifest.get("name", entry.name),
                "scope": "user",
                "source": "plugin_cache",
                "path": str(entry),
                "editable": False,  # Cache is read-only
                "version": manifest.get("version", "unknown"),
            })
    return result


def discover_managed() -> Dict[str, Any]:
    """Discover managed settings (read-only)."""
    managed = get_all_managed()
    return {
        "id": "managed",
        "name": "Managed Configuration",
        "scope": "managed",
        "source": "managed",
        "editable": False,
        "settings": managed.get("settings", {}),
        "mcp": managed.get("mcp", {}),
        "extra": managed.get("extra", []),
        "warnings": managed.get("warnings", []),
    }


def discover_cli_status() -> Dict[str, Any]:
    """Discover Claude CLI status."""
    installed = _cli.check_installed()
    version = _cli.get_version() if installed else None

    return {
        "id": "claude-cli",
        "name": "Claude Code CLI",
        "scope": "system",
        "source": "cli",
        "installed": installed,
        "version": version,
        "editable": False,
    }


# ---------------------------------------------------------------------------
# Main discovery function
# ---------------------------------------------------------------------------

def discover_all(project_root: Optional[str] = None) -> Dict[str, Any]:
    """Discover all resources and return a unified view.

    Args:
        project_root: Optional project root path for project-scoped resources.

    Returns:
        Dict with keys:
          - user: {settings, skills}
          - project: {settings, local_settings, skills}
          - managed: {settings, mcp, extra, warnings}
          - plugin_cache: [plugins]
          - cli: {installed, version}
          - summary: {total_skills, total_mcp, editable_count, readonly_count}
    """
    user_settings = discover_user_settings()
    user_skills = discover_user_skills()
    project_settings = discover_project_settings(project_root)
    project_skills = discover_project_skills(project_root)
    plugin_cache = discover_plugin_cache()
    managed = discover_managed()
    cli = discover_cli_status()

    # Calculate summary
    total_skills = len(user_skills) + len(project_skills)
    editable_count = (
        (1 if user_settings["exists"] else 0) +
        (1 if project_settings["exists"] else 0) +
        len(user_skills) +
        len(project_skills)
    )
    readonly_count = len(plugin_cache) + (1 if managed["settings"] or managed["mcp"] else 0)

    return {
        "user": {
            "settings": user_settings,
            "skills": user_skills,
        },
        "project": {
            "settings": project_settings,
            "skills": project_skills,
        },
        "managed": managed,
        "plugin_cache": plugin_cache,
        "cli": cli,
        "summary": {
            "total_skills": total_skills,
            "total_plugin_cache": len(plugin_cache),
            "editable_count": editable_count,
            "readonly_count": readonly_count,
        },
    }
