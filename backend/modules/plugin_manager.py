"""Plugin manager for discovering and managing Claude plugins"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles

from config import get_global_config_path, get_project_config_path
from models.plugin import PluginResponse, CatalogPluginEntry
from modules.config_manager import read_settings, write_settings


def _global_plugins_dir() -> Path:
    return get_global_config_path() / "plugins"


def _project_plugins_dir() -> Path:
    return get_project_config_path() / "plugins"


async def _scan_plugin_dir(plugins_dir: Path, level: str) -> List[PluginResponse]:
    """Scan a directory for plugins. Each plugin is a directory with plugin.json or .claude-plugin/plugin.json.

    Scans the following structures:
    1. Direct plugins: <plugins_dir>/<plugin-name>/plugin.json
    2. Marketplace plugins: <plugins_dir>/marketplaces/<marketplace>/plugins/<plugin-name>/plugin.json
    3. Cache: <plugins_dir>/cache/<marketplace>/<plugin-name>/<version>/plugin.json
    """
    plugins: List[PluginResponse] = []
    if not plugins_dir.exists():
        return plugins

    disabled_plugins = await _get_disabled_plugins()
    seen_plugin_ids: set = set()

    # Helper function to process a plugin directory
    async def process_plugin_dir(entry: Path, plugin_level: str) -> Optional[PluginResponse]:
        # Check both plugin.json (legacy) and .claude-plugin/plugin.json (official)
        manifest_path = entry / "plugin.json"
        if not manifest_path.exists():
            manifest_path = entry / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            return None

        try:
            async with aiofiles.open(str(manifest_path), "r", encoding="utf-8") as f:
                content = await f.read()
                manifest = json.loads(content)
        except (json.JSONDecodeError, OSError):
            return None

        plugin_id = manifest.get("id", entry.name)

        # Skip if already processed (avoid duplicates)
        if plugin_id in seen_plugin_ids:
            return None
        seen_plugin_ids.add(plugin_id)

        name = manifest.get("name", entry.name)

        # Try to get version from multiple sources
        version = manifest.get("version")
        if not version or version == "0.0.0":
            # Try to extract version from directory name (e.g., cache/<plugin>/<version>/)
            if entry.parent.name and entry.parent.name != "plugins":
                # Check if parent directory name looks like a version
                parent_name = entry.parent.name
                if any(c.isdigit() for c in parent_name) and not parent_name.startswith('.'):
                    version = parent_name
        if not version:
            # Try installed_plugins.json
            installed_path = plugins_dir.parent / "installed_plugins.json" if plugins_dir.name != "cache" else plugins_dir.parent.parent / "installed_plugins.json"
            if installed_path.exists():
                try:
                    with open(str(installed_path), "r", encoding="utf-8") as f:
                        installed_data = json.loads(f.read())
                        for key, versions in installed_data.get("plugins", {}).items():
                            if isinstance(versions, list):
                                for v_info in versions:
                                    if v_info.get("installPath") == str(entry):
                                        version = v_info.get("version", "unknown")
                                        break
                except Exception:
                    pass
        if not version or version == "0.0.0":
            # Fallback to git commit sha if available
            git_sha = manifest.get("gitCommitSha", "")
            if git_sha:
                version = git_sha[:8]  # Short SHA
            else:
                version = "latest"  # Friendly fallback

        description = manifest.get("description", "")

        # Discover skills from skills/ subdirectory
        skills = []
        skills_dir = entry / "skills"
        if skills_dir.exists() and skills_dir.is_dir():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skills.append(skill_dir.name)
                elif skill_dir.is_file() and skill_dir.suffix == ".md":
                    skills.append(skill_dir.stem)

        # Discover MCPs from mcp-servers/ subdirectory
        mcps = []
        mcp_dir = entry / "mcp-servers"
        if mcp_dir.exists() and mcp_dir.is_dir():
            for server_dir in mcp_dir.iterdir():
                if server_dir.is_dir():
                    mcps.append(server_dir.name)

        # Also check manifest for declared skills/mcps
        # Handle both array format ["skill1", "skill2"] and path format "./skills/"
        declared_skills = manifest.get("skills", [])
        if isinstance(declared_skills, str):
            # Path format - ignore, directory scan already handles this
            declared_skills = []
        elif not isinstance(declared_skills, list):
            declared_skills = []

        declared_mcps = manifest.get("mcps", [])
        if isinstance(declared_mcps, str):
            declared_mcps = []
        elif not isinstance(declared_mcps, list):
            declared_mcps = []

        for s in declared_skills:
            if isinstance(s, str) and s not in skills:
                skills.append(s)
        for m in declared_mcps:
            if isinstance(m, str) and m not in mcps:
                mcps.append(m)

        return PluginResponse(
            id=plugin_id,
            name=name,
            version=version,
            description=description,
            level=plugin_level,
            active=plugin_id not in disabled_plugins,
            skills=skills,
            mcps=mcps,
            path=str(entry),
        )

    # Scan direct plugins (legacy structure)
    for entry in sorted(plugins_dir.iterdir()):
        if not entry.is_dir():
            continue
        # Skip special directories
        if entry.name in ("cache", "marketplaces", "data", ".claude"):
            continue

        plugin = await process_plugin_dir(entry, level)
        if plugin:
            plugins.append(plugin)

    # Scan marketplace plugins
    marketplaces_dir = plugins_dir / "marketplaces"
    if marketplaces_dir.exists():
        for marketplace_dir in marketplaces_dir.iterdir():
            if not marketplace_dir.is_dir():
                continue

            # Scan native plugins: marketplaces/<marketplace>/plugins/<plugin-name>/
            plugins_subdir = marketplace_dir / "plugins"
            if plugins_subdir.exists():
                for plugin_dir in plugins_subdir.iterdir():
                    if plugin_dir.is_dir():
                        plugin = await process_plugin_dir(plugin_dir, level)
                        if plugin:
                            plugins.append(plugin)

            # Scan external plugins: marketplaces/<marketplace>/external_plugins/<plugin-name>/
            external_subdir = marketplace_dir / "external_plugins"
            if external_subdir.exists():
                for plugin_dir in external_subdir.iterdir():
                    if plugin_dir.is_dir():
                        plugin = await process_plugin_dir(plugin_dir, level)
                        if plugin:
                            plugins.append(plugin)

    # Scan cache: cache/<marketplace>/<plugin-name>/<version>/
    cache_dir = plugins_dir / "cache"
    if cache_dir.exists():
        for marketplace_dir in cache_dir.iterdir():
            if not marketplace_dir.is_dir():
                continue
            for plugin_dir in marketplace_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                # Get the latest version (most recently modified)
                version_dirs = [d for d in plugin_dir.iterdir() if d.is_dir()]
                if version_dirs:
                    latest_version = max(version_dirs, key=lambda d: d.stat().st_mtime)
                    plugin = await process_plugin_dir(latest_version, level)
                    if plugin:
                        plugins.append(plugin)

    return plugins


async def _get_disabled_plugins() -> list:
    """Get list of disabled plugin IDs from project and global settings.

    Handles both legacy 'disabledPlugins' list and Claude Code native 'enabledPlugins' dict.
    """
    project_settings = await read_settings("project")
    global_settings = await read_settings("global")

    # Combine disabled plugins from both settings
    disabled = set(project_settings.get("disabledPlugins", []))
    disabled.update(global_settings.get("disabledPlugins", []))

    # Also check enabledPlugins dict (Claude Code native format)
    # If a plugin is NOT in enabledPlugins, it's considered disabled
    enabled_global = global_settings.get("enabledPlugins", {})
    if isinstance(enabled_global, dict):
        # Get all plugin keys from installed_plugins.json
        installed_path = _global_plugins_dir() / "installed_plugins.json"
        if installed_path.exists():
            try:
                with open(str(installed_path), "r", encoding="utf-8") as f:
                    installed_data = json.loads(f.read())
                for key in installed_data.get("plugins", {}).keys():
                    if key not in enabled_global and enabled_global != {}:
                        # Plugin is not enabled (only if enabledPlugins is not empty)
                        pass  # Don't add to disabled, we use explicit disabledPlugins
            except (json.JSONDecodeError, OSError):
                pass

    return list(disabled)


async def list_plugins() -> List[PluginResponse]:
    """List all installed plugins based on installed_plugins.json."""
    installed_path = _global_plugins_dir() / "installed_plugins.json"
    plugins: List[PluginResponse] = []
    disabled_plugins = await _get_disabled_plugins()
    seen_plugin_ids: set = set()

    if not installed_path.exists():
        return []

    try:
        async with aiofiles.open(str(installed_path), "r", encoding="utf-8") as f:
            installed_data = json.loads(await f.read())
    except (json.JSONDecodeError, OSError):
        return []

    plugins_dict = installed_data.get("plugins", {})

    for key, entries in plugins_dict.items():
        if not isinstance(entries, list):
            continue

        for entry in entries:
            install_path = entry.get("installPath", "")
            if not install_path:
                continue

            plugin_dir = Path(install_path)
            if not plugin_dir.exists():
                continue

            # Read plugin manifest
            manifest_path = plugin_dir / "plugin.json"
            if not manifest_path.exists():
                manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
            if not manifest_path.exists():
                continue

            try:
                async with aiofiles.open(str(manifest_path), "r", encoding="utf-8") as f:
                    manifest = json.loads(await f.read())
            except (json.JSONDecodeError, OSError):
                continue

            plugin_id = manifest.get("id", plugin_dir.name)

            # Skip if already processed
            if plugin_id in seen_plugin_ids:
                continue
            seen_plugin_ids.add(plugin_id)

            name = manifest.get("name", plugin_dir.name)
            version = entry.get("version", manifest.get("version", "unknown"))
            description = manifest.get("description", "")
            scope = entry.get("scope", "user")
            level = "global" if scope == "user" else "project"

            # Discover skills
            skills = []
            skills_dir = plugin_dir / "skills"
            if skills_dir.exists() and skills_dir.is_dir():
                for skill_dir in skills_dir.iterdir():
                    if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                        skills.append(skill_dir.name)
                    elif skill_dir.is_file() and skill_dir.suffix == ".md":
                        skills.append(skill_dir.stem)

            # Discover MCPs
            mcps = []
            mcp_dir = plugin_dir / "mcp-servers"
            if mcp_dir.exists() and mcp_dir.is_dir():
                for server_dir in mcp_dir.iterdir():
                    if server_dir.is_dir():
                        mcps.append(server_dir.name)

            # Also check manifest for declared skills/mcps
            declared_skills = manifest.get("skills", [])
            if isinstance(declared_skills, str):
                declared_skills = []
            elif not isinstance(declared_skills, list):
                declared_skills = []

            declared_mcps = manifest.get("mcps", [])
            if isinstance(declared_mcps, str):
                declared_mcps = []
            elif not isinstance(declared_mcps, list):
                declared_mcps = []

            for s in declared_skills:
                if isinstance(s, str) and s not in skills:
                    skills.append(s)
            for m in declared_mcps:
                if isinstance(m, str) and m not in mcps:
                    mcps.append(m)

            plugins.append(PluginResponse(
                id=plugin_id,
                name=name,
                version=version,
                description=description,
                level=level,
                active=plugin_id not in disabled_plugins,
                skills=skills,
                mcps=mcps,
                path=str(plugin_dir),
            ))

    return plugins


async def get_plugin_details(plugin_id: str) -> Optional[PluginResponse]:
    """Read plugin.json manifest and return plugin details."""
    all_plugins = await list_plugins()
    for plugin in all_plugins:
        if plugin.id == plugin_id:
            return plugin
    return None


async def toggle_plugin(plugin_id: str, enabled: bool) -> bool:
    """Update plugin active state in settings.

    Handles both legacy 'disabledPlugins' list and Claude Code native 'enabledPlugins' dict.
    """
    plugin = await get_plugin_details(plugin_id)
    if plugin is None:
        return False

    # Use the plugin's scope to determine which settings file to update
    # For global plugins (level="global"), update global settings
    # For project plugins (level="project"), update project settings
    scope = plugin.level  # "global" or "project"
    settings = await read_settings(scope)

    # Handle disabledPlugins list (legacy format)
    disabled = settings.get("disabledPlugins", [])
    if enabled:
        if plugin_id in disabled:
            disabled.remove(plugin_id)
    else:
        if plugin_id not in disabled:
            disabled.append(plugin_id)

    settings["disabledPlugins"] = disabled

    # Also handle enabledPlugins dict (Claude Code native format) for global scope
    if scope == "global":
        plugin_key = f"{plugin_id}@claude-plugins-official"
        enabled_plugins = settings.get("enabledPlugins", {})
        if not isinstance(enabled_plugins, dict):
            enabled_plugins = {}

        if enabled:
            enabled_plugins[plugin_key] = True
        else:
            if plugin_key in enabled_plugins:
                del enabled_plugins[plugin_key]

        settings["enabledPlugins"] = enabled_plugins

    await write_settings(scope, settings)
    return True


async def uninstall_plugin(plugin_id: str) -> bool:
    """Remove plugin directory and clean up installed_plugins.json."""
    plugin = await get_plugin_details(plugin_id)
    if plugin is None:
        return False

    # Remove plugin directory
    if plugin.path and Path(plugin.path).exists():
        shutil.rmtree(plugin.path)

    # Remove from installed_plugins.json
    installed_path = _global_plugins_dir() / "installed_plugins.json"
    if installed_path.exists():
        try:
            async with aiofiles.open(str(installed_path), "r", encoding="utf-8") as f:
                installed_data = json.loads(await f.read())

            # Find and remove the plugin entry
            for key in list(installed_data.get("plugins", {}).keys()):
                entries = installed_data["plugins"][key]
                # Filter out entries that match the plugin path
                new_entries = [
                    e for e in entries
                    if not (e.get("installPath") == plugin.path)
                ]
                if new_entries:
                    installed_data["plugins"][key] = new_entries
                else:
                    del installed_data["plugins"][key]

            async with aiofiles.open(str(installed_path), "w", encoding="utf-8") as f:
                await f.write(json.dumps(installed_data, indent=2))
        except (json.JSONDecodeError, OSError):
            pass

    # Also remove from disabled list if present
    settings = await read_settings("project")
    disabled = settings.get("disabledPlugins", [])
    if plugin_id in disabled:
        disabled.remove(plugin_id)
        settings["disabledPlugins"] = disabled
        await write_settings("project", settings)

    return True


async def list_catalog() -> List[CatalogPluginEntry]:
    """List available plugins from the marketplace catalog cache + directory scan.

    Scans in order of priority:
    1. Marketplace directories (marketplaces/*/plugins/)
    2. Cache directories (cache/*/*/*/ - installed plugins)
    3. Catalog cache file (plugin-catalog-cache.json - fallback)
    """
    # Get installed plugins with their scopes for marking
    installed_plugins = await list_plugins()
    # Track which scope each plugin is installed in
    installed_in_project = {p.name for p in installed_plugins if p.level == 'project'}
    installed_in_global = {p.name for p in installed_plugins if p.level == 'global'}
    installed_names = installed_in_project | installed_in_global

    entries_dict: Dict[str, CatalogPluginEntry] = {}

    # Helper function to process a plugin directory for catalog
    def process_plugin_for_catalog(plugin_dir: Path, marketplace_name: str, parent_plugin_name: Optional[str] = None) -> None:
        """Process a plugin directory and add to entries_dict.

        Args:
            plugin_dir: The plugin directory (may be version directory in cache)
            marketplace_name: The marketplace name
            parent_plugin_name: Optional parent directory name (for cache structure)
        """
        if not plugin_dir.is_dir():
            return

        # Determine plugin name: use parent name if provided (for cache structure),
        # otherwise use current directory name (for marketplace structure)
        # This will be overridden by manifest name if available
        plugin_name = parent_plugin_name if parent_plugin_name else plugin_dir.name

        description = ""
        skills_count = 0
        mcps_count = 0
        has_mcp_server = False
        manifest_name = None  # Will be used to override plugin_name if found

        # Read plugin manifest
        manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            manifest_path = plugin_dir / "plugin.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                # Use manifest name if available (more reliable than directory name)
                manifest_name = manifest.get("name")
                if manifest_name:
                    plugin_name = manifest_name
                description = manifest.get("description", "")
                # Check for MCP servers in manifest
                mcps = manifest.get("mcps", [])
                if isinstance(mcps, list) and len(mcps) > 0:
                    mcps_count = len(mcps)
                    has_mcp_server = True
            except (json.JSONDecodeError, OSError):
                pass

        # Skip if already processed (check after reading manifest to get correct name)
        if plugin_name in entries_dict:
            return

        # Count skills
        skills_dir = plugin_dir / "skills"
        if skills_dir.exists():
            skills_count = sum(
                1 for d in skills_dir.iterdir()
                if d.is_dir() and (d / "SKILL.md").exists()
            ) + sum(
                1 for f in skills_dir.iterdir()
                if f.is_file() and f.suffix == ".md"
            )

        # Check for .mcp.json file (MCP configuration)
        mcp_json = plugin_dir / ".mcp.json"
        if mcp_json.exists():
            try:
                mcp_data = json.loads(mcp_json.read_text(encoding="utf-8"))
                if isinstance(mcp_data, dict) and len(mcp_data) > 0:
                    has_mcp_server = True
                    mcps_count = max(mcps_count, len(mcp_data))
            except (json.JSONDecodeError, OSError):
                pass

        # Check for server.ts/server.js (MCP server files)
        if (plugin_dir / "server.ts").exists() or (plugin_dir / "server.js").exists():
            has_mcp_server = True
            mcps_count = max(mcps_count, 1)

        entries_dict[plugin_name] = CatalogPluginEntry(
            name=plugin_name,
            description=description,
            marketplace=marketplace_name,
            skills_count=skills_count,
            mcps_count=mcps_count,
            has_mcp_server=has_mcp_server,
            installed=plugin_name in installed_names,
            installed_in_project=plugin_name in installed_in_project,
            installed_in_global=plugin_name in installed_in_global,
        )

    # 1. Scan marketplace directories
    marketplaces_dir = _global_plugins_dir() / "marketplaces"
    if marketplaces_dir.exists():
        for marketplace_dir in marketplaces_dir.iterdir():
            if not marketplace_dir.is_dir():
                continue
            marketplace_name = marketplace_dir.name

            # Scan native plugins
            plugins_dir = marketplace_dir / "plugins"
            if plugins_dir.exists():
                for plugin_dir in plugins_dir.iterdir():
                    process_plugin_for_catalog(plugin_dir, marketplace_name)

            # Scan external plugins (MCP servers)
            external_dir = marketplace_dir / "external_plugins"
            if external_dir.exists():
                for plugin_dir in external_dir.iterdir():
                    process_plugin_for_catalog(plugin_dir, marketplace_name)

    # 2. Scan cache directories (installed plugins)
    cache_dir = _global_plugins_dir() / "cache"
    if cache_dir.exists():
        for marketplace_dir in cache_dir.iterdir():
            if not marketplace_dir.is_dir():
                continue
            marketplace_name = marketplace_dir.name
            for plugin_dir in marketplace_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                # Get the latest version
                version_dirs = [d for d in plugin_dir.iterdir() if d.is_dir()]
                if version_dirs:
                    latest_version = max(version_dirs, key=lambda d: d.stat().st_mtime)
                    # Pass plugin_dir.name as parent_plugin_name since latest_version is a version directory
                    process_plugin_for_catalog(latest_version, marketplace_name, parent_plugin_name=plugin_dir.name)

    # 3. Fallback to catalog cache file for plugins not found in directories
    catalog_path = _global_plugins_dir() / "plugin-catalog-cache.json"
    if catalog_path.exists():
        try:
            async with aiofiles.open(str(catalog_path), "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
            catalog = data.get("catalog", {})
            plugins_data = catalog.get("plugins", {})

            for key, info in plugins_data.items():
                parts = key.split("@")
                plugin_name = parts[0] if parts else key
                marketplace = parts[1] if len(parts) > 1 else ""

                # Skip if already populated from directory scan
                if plugin_name in entries_dict:
                    continue

                components = info.get("components", {})
                skills_list = components.get("skills", [])
                mcps_list = components.get("mcps", [])
                description = info.get("description", "")

                entries_dict[plugin_name] = CatalogPluginEntry(
                    name=plugin_name,
                    description=description,
                    marketplace=marketplace,
                    skills_count=len(skills_list),
                    mcps_count=len(mcps_list),
                    has_mcp_server=len(mcps_list) > 0,
                    installed=plugin_name in installed_names,
                )
        except (json.JSONDecodeError, OSError):
            pass

    entries = list(entries_dict.values())
    # Sort: not-installed first, then alphabetically
    entries.sort(key=lambda e: (e.installed, e.name))
    return entries


async def install_plugin(plugin_name: str, marketplace: str, scope: str) -> Optional[PluginResponse]:
    """Install a plugin from the marketplace to the target scope.

    Tries multiple sources in order:
    1. Marketplace cache (already downloaded version)
    2. Marketplace source directory (git repo)
    3. Clone from git marketplace
    """
    source_dir = None

    # Try marketplace cache first
    cache_dir = _global_plugins_dir() / "cache" / marketplace / plugin_name
    if cache_dir.exists():
        version_dirs = [d for d in cache_dir.iterdir() if d.is_dir()]
        if version_dirs:
            source_dir = max(version_dirs, key=lambda d: d.stat().st_mtime)

    # Fall back to marketplace source directory
    if source_dir is None:
        # Try native plugins directory
        market_plugins_dir = _global_plugins_dir() / "marketplaces" / marketplace / "plugins" / plugin_name
        if market_plugins_dir.exists() and market_plugins_dir.is_dir():
            source_dir = market_plugins_dir

    # Try external plugins directory
    if source_dir is None:
        market_external_dir = _global_plugins_dir() / "marketplaces" / marketplace / "external_plugins" / plugin_name
        if market_external_dir.exists() and market_external_dir.is_dir():
            source_dir = market_external_dir

    # If still not found, try to clone from git marketplace
    if source_dir is None:
        # Read known marketplaces
        known_marketplaces_path = _global_plugins_dir() / "known_marketplaces.json"
        if known_marketplaces_path.exists():
            try:
                with open(str(known_marketplaces_path), "r", encoding="utf-8") as f:
                    known_marketplaces = json.loads(f.read())

                if marketplace in known_marketplaces:
                    mp_info = known_marketplaces[marketplace]
                    mp_source = mp_info.get("source", {})
                    install_location = Path(mp_info.get("installLocation", ""))

                    if mp_source.get("source") == "github" and mp_source.get("repo"):
                        repo = mp_source["repo"]
                        # Clone the marketplace if it doesn't exist
                        if not install_location.exists():
                            import subprocess
                            install_location.parent.mkdir(parents=True, exist_ok=True)
                            subprocess.run(
                                ["git", "clone", f"https://github.com/{repo}.git", str(install_location)],
                                check=True,
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                            )

                        # Try to find the plugin in the cloned repo
                        market_plugins_dir = install_location / "plugins" / plugin_name
                        if market_plugins_dir.exists() and market_plugins_dir.is_dir():
                            source_dir = market_plugins_dir

                        # Also check external_plugins
                        if source_dir is None:
                            market_external_dir = install_location / "external_plugins" / plugin_name
                            if market_external_dir.exists() and market_external_dir.is_dir():
                                source_dir = market_external_dir
            except Exception:
                pass  # Ignore cloning errors

    if source_dir is None:
        return None

    # Read version from source plugin manifest
    version = "0.0.0"
    git_sha = ""
    source_manifest = source_dir / "plugin.json"
    if not source_manifest.exists():
        source_manifest = source_dir / ".claude-plugin" / "plugin.json"
    if source_manifest.exists():
        try:
            async with aiofiles.open(str(source_manifest), "r", encoding="utf-8") as f:
                src_manifest = json.loads(await f.read())
            version = src_manifest.get("version", "0.0.0")
            git_sha = src_manifest.get("gitCommitSha", "")
            if git_sha:
                version = git_sha[:8]
        except (json.JSONDecodeError, OSError):
            pass

    # Target directory in cache: ~/.claude/plugins/cache/{marketplace}/{plugin_name}/{version}/
    target_dir = _global_plugins_dir() / "cache" / marketplace / plugin_name / version

    # If target already exists, ensure it's registered in installed_plugins.json
    if target_dir.exists():
        installed_path = _global_plugins_dir() / "installed_plugins.json"
        installed_data: Dict = {"version": 2, "plugins": {}}
        if installed_path.exists():
            try:
                async with aiofiles.open(str(installed_path), "r", encoding="utf-8") as f:
                    installed_data = json.loads(await f.read())
            except (json.JSONDecodeError, OSError):
                pass

        key = f"{plugin_name}@{marketplace}"
        if key not in installed_data["plugins"]:
            installed_data["plugins"][key] = []

        # Check if this entry already exists
        already_registered = any(
            entry.get("installPath") == str(target_dir)
            for entry in installed_data["plugins"].get(key, [])
        )

        if not already_registered:
            entry = {
                "scope": "user" if scope == "global" else "project",
                "installPath": str(target_dir),
                "version": version,
                "installedAt": __import__("datetime").datetime.now().isoformat(),
            }
            if git_sha:
                entry["gitCommitSha"] = git_sha
            installed_data["plugins"][key].append(entry)

            async with aiofiles.open(str(installed_path), "w", encoding="utf-8") as f:
                await f.write(json.dumps(installed_data, indent=2))

        # Return the plugin from installed list
        return await get_plugin_details(plugin_name)

    # Create the target directory and copy the plugin
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(source_dir), str(target_dir))

    # Update installed_plugins.json
    installed_path = _global_plugins_dir() / "installed_plugins.json"
    installed_data: Dict = {"version": 2, "plugins": {}}
    if installed_path.exists():
        try:
            async with aiofiles.open(str(installed_path), "r", encoding="utf-8") as f:
                installed_data = json.loads(await f.read())
        except (json.JSONDecodeError, OSError):
            pass

    key = f"{plugin_name}@{marketplace}"
    if key not in installed_data["plugins"]:
        installed_data["plugins"][key] = []

    # Check if this entry already exists
    already_registered = any(
        entry.get("installPath") == str(target_dir)
        for entry in installed_data["plugins"].get(key, [])
    )

    if not already_registered:
        entry = {
            "scope": "user" if scope == "global" else "project",
            "installPath": str(target_dir),
            "version": version,
            "installedAt": __import__("datetime").datetime.now().isoformat(),
        }
        if git_sha:
            entry["gitCommitSha"] = git_sha
        installed_data["plugins"][key].append(entry)

        async with aiofiles.open(str(installed_path), "w", encoding="utf-8") as f:
            await f.write(json.dumps(installed_data, indent=2))

    # Return the newly installed plugin
    return await get_plugin_details(plugin_name)


async def move_plugin(plugin_id: str, target_scope: str) -> bool:
    """Move a plugin directory between global and project scope."""
    plugin = await get_plugin_details(plugin_id)
    if plugin is None:
        return False

    source_path = Path(plugin.path) if plugin.path else None
    if not source_path or not source_path.exists():
        return False

    # For cache-based plugins, update the scope in installed_plugins.json
    if "cache" in str(source_path):
        # Update installed_plugins.json
        installed_path = _global_plugins_dir() / "installed_plugins.json"
        if installed_path.exists():
            try:
                async with aiofiles.open(str(installed_path), "r", encoding="utf-8") as f:
                    installed_data = json.loads(await f.read())

                # Find and update the plugin entry
                for key in installed_data.get("plugins", {}).keys():
                    for entry in installed_data["plugins"][key]:
                        if entry.get("installPath") == str(source_path):
                            entry["scope"] = "user" if target_scope == "global" else "project"

                async with aiofiles.open(str(installed_path), "w", encoding="utf-8") as f:
                    await f.write(json.dumps(installed_data, indent=2))
            except (json.JSONDecodeError, OSError):
                pass
        return True

    # For legacy non-cache plugins, move the directory
    target_dir = (_global_plugins_dir() if target_scope == "global" else _project_plugins_dir()) / source_path.name
    if target_dir.exists():
        return False

    shutil.copytree(str(source_path), str(target_dir))
    shutil.rmtree(str(source_path))

    return True


async def install_plugin_from_path(source_path: str, scope: str) -> Optional[PluginResponse]:
    """Install a plugin from a local directory path.

    Copies the source directory into ~/.claude/plugins/cache/local/{plugin_name}/local/
    and updates installed_plugins.json.
    """
    src = Path(source_path)
    if not src.exists() or not src.is_dir():
        return None

    # Validate it looks like a plugin (has plugin.json or .claude-plugin/plugin.json)
    has_manifest = (src / "plugin.json").exists() or (src / ".claude-plugin" / "plugin.json").exists()
    if not has_manifest:
        return None

    # Read plugin info from manifest
    manifest_path = src / "plugin.json"
    if not manifest_path.exists():
        manifest_path = src / ".claude-plugin" / "plugin.json"

    plugin_name = src.name
    version = "local"
    git_sha = ""

    if manifest_path.exists():
        try:
            with open(str(manifest_path), "r", encoding="utf-8") as f:
                manifest = json.loads(f.read())
            version = manifest.get("version", "local")
            git_sha = manifest.get("gitCommitSha", "")
            if git_sha:
                version = git_sha[:8]
        except (json.JSONDecodeError, OSError):
            pass

    # Target directory in cache: ~/.claude/plugins/cache/local/{plugin_name}/{version}/
    target_dir = _global_plugins_dir() / "cache" / "local" / plugin_name / version
    if target_dir.exists():
        return None  # Already installed

    # Create the target directory and copy the plugin
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(src), str(target_dir))

    # Update installed_plugins.json
    installed_path = _global_plugins_dir() / "installed_plugins.json"
    installed_data: Dict = {"version": 2, "plugins": {}}
    if installed_path.exists():
        try:
            async with aiofiles.open(str(installed_path), "r", encoding="utf-8") as f:
                installed_data = json.loads(await f.read())
        except (json.JSONDecodeError, OSError):
            pass

    key = f"{plugin_name}@local"
    if key not in installed_data["plugins"]:
        installed_data["plugins"][key] = []

    # Check if this version is already installed
    already_installed = any(
        entry.get("version") == version and entry.get("scope") == ("user" if scope == "global" else "project")
        for entry in installed_data["plugins"].get(key, [])
    )

    if not already_installed:
        entry = {
            "scope": "user" if scope == "global" else "project",
            "installPath": str(target_dir),
            "version": version,
            "installedAt": __import__("datetime").datetime.now().isoformat(),
        }
        if git_sha:
            entry["gitCommitSha"] = git_sha
        installed_data["plugins"][key].append(entry)

        async with aiofiles.open(str(installed_path), "w", encoding="utf-8") as f:
            await f.write(json.dumps(installed_data, indent=2))

    # Return the newly installed plugin
    plugins = await _scan_plugin_dir(_global_plugins_dir(), "global")
    for p in plugins:
        if p.name == plugin_name:
            return p

    return None


async def update_plugin_version(plugin_id: str, new_version: str) -> Optional[PluginResponse]:
    """Update a plugin's version in its manifest file (plugin.json or .claude-plugin/plugin.json).

    Returns the updated PluginResponse, or None if the plugin is not found.
    """
    plugin = await get_plugin_details(plugin_id)
    if plugin is None:
        return None

    source_path = Path(plugin.path) if plugin.path else None
    if not source_path or not source_path.exists():
        return None

    # Locate the manifest file
    manifest_path = source_path / "plugin.json"
    if not manifest_path.exists():
        manifest_path = source_path / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        return None

    # Read, update, write back
    try:
        async with aiofiles.open(str(manifest_path), "r", encoding="utf-8") as f:
            manifest = json.loads(await f.read())

        manifest["version"] = new_version

        async with aiofiles.open(str(manifest_path), "w", encoding="utf-8") as f:
            await f.write(json.dumps(manifest, indent=2, ensure_ascii=False))
    except (json.JSONDecodeError, OSError):
        return None

    # Return the updated plugin details
    updated = await get_plugin_details(plugin_id)
    return updated
