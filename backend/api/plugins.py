"""Plugins API endpoints — delegates to ``services.plugin_service`` (CLI-first)."""

from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional

from models.plugin import (
    PluginResponse,
    TogglePluginRequest,
    CatalogPluginEntry,
    InstallPluginRequest,
    InstallLocalPluginRequest,
    UpdateVersionRequest,
)
from services import plugin_service
from services.claude_cli_service import CliResult
from core.paths import _find_project_root
from modules.session_registry import registry

router = APIRouter()


def _get_project_root() -> str:
    """Get the current Claude Code project root directory.

    Uses _find_project_root() which:
    1. Respects CLAUDE_PROJECT_DIR env var first
    2. Falls back to finding CLAUDE.md or .claude directory
    3. Handles backend subdirectory case

    This ensures the plugin system works correctly both in development
    (when running from backend/ directory) and in production (when running
    as a Claude Code plugin).
    """
    return str(_find_project_root())


def _normalize_scope(scope: str) -> str:
    """Normalize scope to CLI-accepted values."""
    # The old code uses "global" but CLI expects "user"
    if scope == "global":
        return "user"
    return scope


@router.get("")
@router.get("/", response_model=list[PluginResponse])
async def list_plugins(
    project_root: Optional[str] = Query(None),
    x_claude_session_id: Optional[str] = Header(None)
):
    """List installed plugins: global plugins + current project's plugins.

    When no explicit project_root is given, uses the Claude Code project root
    (determined by _find_project_root()) to filter project-scoped plugins.

    If session_id is provided, verifies session exists.
    """
    # If session_id is provided, verify session exists
    if x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{x_claude_session_id}' not found. "
                       "Please restart Claude Code to get a new session link."
            )
        # Use session's project directory if not explicitly provided
        if not project_root:
            project_root = session.project_dir

    # Use project root from _find_project_root() when not specified
    # This ensures we use the correct Claude Code project directory
    if not project_root:
        project_root = _get_project_root()

    return plugin_service.list_plugins(project_root)


@router.get("/catalog", response_model=list[CatalogPluginEntry])
async def list_catalog():
    """List available plugins from the marketplace catalog."""
    # For now, delegate to the existing plugin_manager for catalog
    # TODO: Implement marketplace scanning in plugin_service
    from modules import plugin_manager
    return await plugin_manager.list_catalog()


@router.get("/{plugin_id}", response_model=PluginResponse)
async def get_plugin(plugin_id: str):
    """Get plugin details."""
    # Scan cache for this plugin
    from pathlib import Path
    cache_dir = Path(plugin_service._get_installed_plugins_path().parent / "cache")

    if not cache_dir.exists():
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    # Try exact match first
    target = cache_dir / plugin_id
    if not target.exists():
        # Try partial match
        for entry in cache_dir.iterdir():
            if entry.is_dir() and plugin_id in entry.name:
                target = entry
                break
        else:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    manifest = plugin_service._scan_plugin_dir(target)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' manifest not found")

    installed = plugin_service._read_installed_plugins()
    is_installed = plugin_id in installed or target.name in installed

    return PluginResponse(
        id=plugin_id,
        name=manifest.get("name", target.name),
        version=manifest.get("version", "unknown"),
        description=manifest.get("description", ""),
        level="global",
        active=is_installed,
        skills=[],
        mcps=[],
        path=str(target),
    )


@router.post("/install", status_code=201)
async def install_plugin(data: InstallPluginRequest):
    """Install a plugin from the marketplace via Claude CLI."""
    cli_scope = _normalize_scope(data.scope)

    # Use project root from _find_project_root() for project-scoped installs
    # This ensures the CLI installs to the correct Claude Code project
    project_root = _get_project_root() if cli_scope == "project" else None

    result = plugin_service.install_plugin(data.plugin_name, data.marketplace, cli_scope, project_root)
    if not result.ok:
        # Check if it's a "not found" error
        if "not found" in result.stderr.lower() or "notfound" in result.stderr.lower().replace(" ", ""):
            raise HTTPException(status_code=404, detail=f"Plugin '{data.plugin_name}' not found")
        raise HTTPException(
            status_code=400,
            detail=f"Plugin installation failed: {result.stderr[:200] if result.stderr else 'unknown error'}"
        )
    return {"message": f"Plugin '{data.plugin_name}' installed", "success": True, "cli_output": result.stdout}


@router.post("/install-local", status_code=201)
async def install_local_plugin(data: InstallLocalPluginRequest):
    """Install a plugin from a local directory path."""
    # For local install, copy to cache and register
    from modules import plugin_manager
    result = await plugin_manager.install_plugin_from_path(data.path, data.scope)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid plugin path or already installed"
        )
    return result


@router.patch("/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, data: TogglePluginRequest):
    """Enable or disable a plugin via Claude CLI."""
    from services.plugin_service import _read_installed_plugins

    installed_data = _read_installed_plugins()
    scope = None

    if isinstance(installed_data, dict):
        plugins = installed_data.get("plugins", {})
        if plugin_id in plugins:
            versions = plugins[plugin_id]
            if isinstance(versions, list) and versions:
                v = versions[0]
                if isinstance(v, dict):
                    s = v.get("scope", "user")
                    scope = "project" if s == "project" else "user"
        else:
            # Try partial match (plugin_id might be without marketplace suffix)
            for key in plugins.keys():
                if key.startswith(plugin_id + "@") or key.endswith("@" + plugin_id):
                    versions = plugins[key]
                    if isinstance(versions, list) and versions:
                        v = versions[0]
                        if isinstance(v, dict):
                            s = v.get("scope", "user")
                            scope = "project" if s == "project" else "user"
                    break

    # Use project root from _find_project_root() for project-scoped operations
    # This ensures the CLI operates on the correct Claude Code project
    project_root = _get_project_root() if scope == "project" else None

    action = "enable" if data.active else "disable"
    if data.active:
        result = plugin_service.enable_plugin(plugin_id, scope, project_root)
    else:
        result = plugin_service.disable_plugin(plugin_id, scope, project_root)

    # Treat "already enabled"/"already disabled" as success (idempotent).
    if not result.ok and plugin_service._is_already_in_state(result.stderr, action):
        return {"message": f"Plugin '{plugin_id}' already {action}d", "success": True}

    if not result.ok:
        if "not found" in result.stderr.lower():
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
        raise HTTPException(
            status_code=400,
            detail=f"Plugin toggle failed: {result.stderr[:200] if result.stderr else 'unknown error'}"
        )
    return {"message": f"Plugin '{plugin_id}' {'enabled' if data.active else 'disabled'}", "success": True}


@router.patch("/{plugin_id}/version", response_model=PluginResponse)
async def update_plugin_version(plugin_id: str, data: UpdateVersionRequest):
    """Update a plugin's version in its manifest file."""
    from modules import plugin_manager
    result = await plugin_manager.update_plugin_version(plugin_id, data.version)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
    return result


@router.delete("/{plugin_id}")
async def uninstall_plugin(plugin_id: str):
    """Uninstall a plugin via Claude CLI."""
    from services.plugin_service import _read_installed_plugins

    installed_data = _read_installed_plugins()
    scope = None
    plugin_found = False

    if isinstance(installed_data, dict):
        plugins = installed_data.get("plugins", {})
        # Try exact match first
        if plugin_id in plugins:
            plugin_found = True
            versions = plugins[plugin_id]
            if isinstance(versions, list) and versions:
                v = versions[0]
                if isinstance(v, dict):
                    s = v.get("scope", "user")
                    scope = "project" if s == "project" else "user"
        else:
            # Try partial match (plugin_id might be without marketplace suffix)
            for key in plugins.keys():
                if key.startswith(plugin_id + "@") or key.endswith("@" + plugin_id):
                    plugin_found = True
                    versions = plugins[key]
                    if isinstance(versions, list) and versions:
                        v = versions[0]
                        if isinstance(v, dict):
                            s = v.get("scope", "user")
                            scope = "project" if s == "project" else "user"
                    break

    # If plugin not found in installed_plugins.json, try to get scope from CLI
    if not plugin_found:
        # Default to user scope and let CLI determine the actual scope
        scope = None

    # Use project root from _find_project_root() for project-scoped operations
    # This ensures the CLI operates on the correct Claude Code project
    project_root = _get_project_root() if scope == "project" else None

    result = plugin_service.uninstall_plugin(plugin_id, scope, project_root)
    if not result.ok:
        if "not found" in result.stderr.lower():
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
        raise HTTPException(
            status_code=400,
            detail=f"Plugin uninstallation failed: {result.stderr[:200] if result.stderr else 'unknown error'}"
        )
    return {"message": f"Plugin '{plugin_id}' uninstalled", "success": True}


@router.get("/cache")
async def list_plugin_cache():
    """List plugin cache entries (read-only)."""
    return plugin_service.scan_plugin_cache()


@router.get("/marketplaces")
async def list_marketplaces():
    """List configured marketplaces."""
    result = plugin_service.list_marketplaces()
    if not result.ok:
        return {"marketplaces": [], "error": result.stderr}
    # Parse stdout for marketplace names
    lines = result.stdout.strip().split("\n") if result.stdout else []
    return {"marketplaces": lines}


@router.post("/marketplaces", status_code=201)
async def add_marketplace(source: str):
    """Add a marketplace source."""
    result = plugin_service.add_marketplace(source)
    if not result.ok:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to add marketplace: {result.stderr[:200] if result.stderr else 'unknown error'}"
        )
    return {"message": "Marketplace added", "success": True}


@router.post("/marketplaces/update")
async def update_marketplace(name: Optional[str] = None):
    """Update marketplace(s)."""
    result = plugin_service.update_marketplace(name)
    if not result.ok:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update marketplace: {result.stderr[:200] if result.stderr else 'unknown error'}"
        )
    return {"message": "Marketplace updated", "success": True}
