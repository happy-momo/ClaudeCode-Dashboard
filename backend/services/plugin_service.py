"""Plugin service — CLI-first plugin management.

All plugin lifecycle operations (install, uninstall, enable, disable, move-scope)
go through the Claude Code CLI. Direct file modifications are avoided.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_global_config_path, get_project_config_path
from models.plugin import PluginResponse
from services.claude_cli_service import ClaudeCLIService, CliResult
from services.operation_planner import OperationPlanner
from core.errors import CliNotFoundError

logger = logging.getLogger(__name__)

_cli = ClaudeCLIService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_installed_plugins_path() -> Path:
    """Path to the installed_plugins.json cache file."""
    return get_global_config_path() / "plugins" / "installed_plugins.json"


def _read_installed_plugins() -> Dict[str, Any]:
    """Read installed plugins from cache file."""
    path = _get_installed_plugins_path()
    if not path.exists():
        return {}
    try:
        import json
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _scan_plugin_dir(plugin_path: Path) -> Optional[Dict[str, Any]]:
    """Scan a plugin directory for manifest info."""
    manifest_paths = [
        plugin_path / "plugin.json",
        plugin_path / ".claude-plugin" / "plugin.json",
    ]
    for mp in manifest_paths:
        if mp.exists():
            try:
                import json
                return json.loads(mp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
    return None


def _is_already_in_state(stderr: str, action: str) -> bool:
    """Check if CLI stderr indicates the plugin is already in the desired state.

    The CLI returns errors like "Plugin is already enabled at project scope"
    when the desired state is already achieved.  This should be treated as
    success (idempotent).
    """
    if not stderr:
        return False
    low = stderr.lower()
    if action == "enable":
        return "already enabled" in low
    if action == "disable":
        return "already disabled" in low
    return False


# ---------------------------------------------------------------------------
# List plugins
# ---------------------------------------------------------------------------

def list_plugins(project_root: Optional[str] = None) -> List[PluginResponse]:
    """List installed plugins.

    Prefers ``claude plugin list --json`` as the authoritative source because
    the CLI correctly resolves project-scoped plugin status (enabled/disabled)
    based on the working directory.  Falls back to reading
    ``installed_plugins.json`` directly when the CLI is unavailable.
    """
    # --- Try CLI first (authoritative) ---
    try:
        result = _cli.plugin_list(project_root=project_root)
        if result.ok and result.stdout.strip():
            plugins = _parse_cli_plugin_list(result.stdout)
            if plugins is not None:
                return plugins
            logger.warning("Failed to parse 'plugin list --json' output; falling back to file scan")
    except CliNotFoundError:
        logger.info("Claude CLI not found; falling back to file-based plugin scan")
    except Exception as exc:
        logger.warning("CLI plugin list failed (%s); falling back to file scan", exc)

    # --- Fallback: read installed_plugins.json directly ---
    return _list_plugins_from_file(project_root)


def _parse_cli_plugin_list(stdout: str) -> Optional[List[PluginResponse]]:
    """Parse the JSON output of ``claude plugin list --json``.

    Returns *None* (not an empty list) when parsing fails so the caller can
    distinguish "CLI returned empty" from "CLI output was unparseable".
    """
    try:
        items = json.loads(stdout)
    except json.JSONDecodeError:
        return None

    if not isinstance(items, list):
        return None

    plugins: List[PluginResponse] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        plugin_id = item.get("id", "")
        scope = item.get("scope", "user")
        level = "project" if scope in ("project", "local") else "global"
        enabled = item.get("enabled", False)
        install_path = item.get("installPath", "")

        # Enrich with manifest metadata (name, description, version)
        name = plugin_id
        description = ""
        version = item.get("version", "unknown")
        if install_path:
            manifest = _scan_plugin_dir(Path(install_path))
            if manifest:
                name = manifest.get("name", plugin_id)
                description = manifest.get("description", "")

        plugins.append(
            PluginResponse(
                id=plugin_id,
                name=name,
                version=version,
                description=description,
                level=level,
                scope=scope,
                active=enabled,
                skills=[],
                mcps=[],
                path=install_path,
            )
        )

    return plugins


def _list_plugins_from_file(project_root: Optional[str] = None) -> List[PluginResponse]:
    """List plugins by reading installed_plugins.json (fallback when CLI is unavailable).

    Only returns:
    1. Global plugins (scope: "user")
    2. Plugins for the current project (matching project_root)
    """
    from core.paths import _find_project_root

    plugins: List[PluginResponse] = []
    plugins_dir = get_global_config_path() / "plugins"
    cache_dir = plugins_dir / "cache"

    # Read installed_plugins.json for authoritative list
    installed_data = _read_installed_plugins()
    installed_plugins = installed_data if isinstance(installed_data, dict) else {}

    # Get enabled/disabled plugins from settings.json (NOT installed_plugins.json)
    # enabledPlugins is a dict like {"plugin-id@marketplace": true}
    # disabledPlugins is a list like ["plugin-id@marketplace", ...] or version strings
    disabled = []
    enabled_plugins = {}
    try:
        settings_path = get_global_config_path() / "settings.json"
        if settings_path.exists():
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            disabled = settings.get("disabledPlugins", [])
            enabled_plugins = settings.get("enabledPlugins", {})
    except Exception:
        pass  # Ignore errors, use empty lists

    # Normalize project_root for comparison
    # Use _find_project_root() to get the correct Claude Code project directory
    current_project = _find_project_root() if not project_root else Path(project_root).resolve()

    # Process each installed plugin
    for plugin_id, versions in installed_plugins.get("plugins", {}).items():
        if not isinstance(versions, list):
            continue

        # Get the first version's info
        version_info = versions[0] if versions else {}
        install_path = version_info.get("installPath", "")
        version = version_info.get("version", "unknown")

        # Get the plugin's scope and projectPath
        plugin_scope = "user"  # default
        project_path = None
        if isinstance(versions, list) and versions:
            v = versions[0]
            if isinstance(v, dict):
                s = v.get("scope", "user")
                if s == "project":
                    plugin_scope = "project"
                    project_path = v.get("projectPath")
                elif s == "local":
                    plugin_scope = "local"
                else:
                    plugin_scope = "user"

        # Skip project-scoped plugins that don't belong to the current project
        if plugin_scope == "project":
            if not project_path:
                continue  # Skip if no projectPath recorded
            # Normalize paths for comparison
            normalized_project_path = os.path.abspath(project_path)
            if normalized_project_path != current_project:
                continue  # Skip plugins from other projects

        # Try to read manifest from install path
        manifest = None
        if install_path:
            manifest = _scan_plugin_dir(Path(install_path))

        # Fallback: scan cache directory
        if not manifest and cache_dir.exists():
            for entry in cache_dir.iterdir():
                if entry.is_dir():
                    m = _scan_plugin_dir(entry)
                    if m and (m.get("id") == plugin_id or entry.name == plugin_id):
                        manifest = m
                        if not version or version == "unknown":
                            version = m.get("version", "unknown")
                        break

        if manifest:
            # Determine if plugin is active based on enabledPlugins dict
            is_enabled = enabled_plugins.get(plugin_id, False) is True
            is_disabled = plugin_id in disabled
            is_active = is_enabled and not is_disabled

            # level is "global" for user scope, "project" for project/local scope
            level = "project" if plugin_scope in ("project", "local") else "global"

            plugins.append(
                PluginResponse(
                    id=plugin_id,
                    name=manifest.get("name", plugin_id),
                    version=version,
                    description=manifest.get("description", ""),
                    level=level,
                    scope=plugin_scope,
                    active=is_active,
                    skills=[],
                    mcps=[],
                    path=install_path or str(cache_dir / plugin_id),
                )
            )

    # If installed_plugins.json doesn't exist or is empty, scan cache directory directly
    if not plugins and cache_dir.exists():
        for entry in cache_dir.iterdir():
            if not entry.is_dir():
                continue

            manifest = _scan_plugin_dir(entry)
            if not manifest:
                continue

            plugin_id = manifest.get("id", entry.name)
            is_installed = plugin_id in installed_plugins.get("plugins", {})

            plugins.append(
                PluginResponse(
                    id=plugin_id,
                    name=manifest.get("name", entry.name),
                    version=manifest.get("version", "unknown"),
                    description=manifest.get("description", ""),
                    level="global",
                    active=is_installed,
                    skills=[],
                    mcps=[],
                    path=str(entry),
                )
            )

    return plugins


# ---------------------------------------------------------------------------
# Install plugin (CLI)
# ---------------------------------------------------------------------------

def install_plugin(plugin_name: str, marketplace: str = "claude-plugins-official", scope: str = "global", project_root: Optional[str] = None) -> CliResult:
    """Install a plugin via Claude CLI.

    Args:
        plugin_name: Plugin reference (e.g., "my-plugin@my-marketplace")
        marketplace: Marketplace name (default: claude-plugins-official)
        scope: "global" or "project"
        project_root: Project directory (required for project-scope installs
            so the CLI knows which project to target via cwd).

    Returns:
        CliResult with exit_code, stdout, stderr
    """
    plan = OperationPlanner.plan("install", "plugin", plugin_name, scope)
    if plan.mode != "cli":
        logger.warning("Plugin install planned as %s, but using CLI anyway", plan.mode)

    plugin_ref = f"{plugin_name}@{marketplace}" if "@" not in plugin_name else plugin_name
    return _cli.plugin_install(plugin_ref, scope, project_root)


# ---------------------------------------------------------------------------
# Uninstall plugin (CLI)
# ---------------------------------------------------------------------------

def uninstall_plugin(plugin_id: str, scope: Optional[str] = None, project_root: Optional[str] = None) -> CliResult:
    """Uninstall a plugin via Claude CLI."""
    return _cli.plugin_uninstall(plugin_id, scope, project_root)


# ---------------------------------------------------------------------------
# Enable/disable plugin (CLI)
# ---------------------------------------------------------------------------

def enable_plugin(plugin_id: str, scope: Optional[str] = None, project_root: Optional[str] = None) -> CliResult:
    """Enable a plugin via Claude CLI."""
    return _cli.plugin_enable(plugin_id, scope, project_root)


def disable_plugin(plugin_id: str, scope: Optional[str] = None, project_root: Optional[str] = None) -> CliResult:
    """Disable a plugin via Claude CLI."""
    return _cli.plugin_disable(plugin_id, scope, project_root)


# ---------------------------------------------------------------------------
# Marketplace operations (CLI)
# ---------------------------------------------------------------------------

def list_marketplaces() -> CliResult:
    """List configured marketplaces."""
    return _cli.marketplace_list()


def add_marketplace(source: str) -> CliResult:
    """Add a marketplace source."""
    return _cli.marketplace_add(source)


def update_marketplace(name: Optional[str] = None) -> CliResult:
    """Update marketplace(s)."""
    return _cli.marketplace_update(name)


# ---------------------------------------------------------------------------
# Scan plugin cache (read-only)
# ---------------------------------------------------------------------------

def scan_plugin_cache() -> List[Dict[str, Any]]:
    """Scan the plugin cache directory (read-only).

    Returns a list of plugin metadata dicts.
    """
    cache_dir = get_global_config_path() / "plugins" / "cache"
    if not cache_dir.exists():
        return []

    result = []
    for entry in cache_dir.iterdir():
        if not entry.is_dir():
            continue
        manifest = _scan_plugin_dir(entry)
        if manifest:
            manifest["_path"] = str(entry)
            result.append(manifest)

    return result
