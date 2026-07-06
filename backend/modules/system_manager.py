"""System manager for service status, configuration export, and effective capabilities"""

import os
import time
from typing import Any, Dict, List, Optional

from config import DEFAULT_HOST, DEFAULT_PORT, get_global_config_path, get_project_config_path
from models.common import EffectiveCapability


_start_time = time.time()


def get_service_status(port: int = DEFAULT_PORT) -> Dict[str, Any]:
    """Return service status information."""
    uptime = time.time() - _start_time
    return {
        "status": "running",
        "host": DEFAULT_HOST,
        "port": port,
        "uptime_seconds": round(uptime, 1),
        "mcp_connected": True,
        "project_dir": str(get_project_config_path()),
        "global_dir": str(get_global_config_path()),
    }


def get_dashboard_url(port: int = DEFAULT_PORT) -> str:
    """Return the dashboard URL."""
    return f"http://{DEFAULT_HOST}:{port}"


async def get_effective_capabilities(session_id: Optional[str] = None) -> List[EffectiveCapability]:
    """Get a unified list of all skills and MCPs across both scopes,
    including those provided by plugins.

    Resolution rules:
    - Project scope overrides global scope for same-name items
    - Items from plugins are marked with their source
    - Active state is determined by the disabled lists

    Args:
        session_id: Optional session ID to use for project directory resolution
    """
    from modules.skill_manager import list_skills
    from modules.mcp_manager import list_mcp_servers
    from modules.plugin_manager import list_plugins
    from modules.session_registry import registry

    # If session_id is provided, set CLAUDE_PROJECT_DIR to use that session's project directory
    if session_id:
        session = await registry.get_session(session_id)
        if session:
            os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    capabilities: List[EffectiveCapability] = []

    # Collect all skills
    project_skills = await list_skills("project")
    global_skills = await list_skills("global")

    project_skill_names = {s.name for s in project_skills}
    global_skill_names = {s.name for s in global_skills}

    # Project skills (always shown, they override globals with same name)
    for skill in project_skills:
        # Project scope has highest priority - never overridden
        overridden_by = None

        # Determine source: check if from a plugin
        source = "project_native"
        plugin_name = None
        if skill.source and "plugin" in str(skill.source).lower():
            source = "project_plugin"

        capabilities.append(EffectiveCapability(
            name=skill.name,
            type="skill",
            scope="project",
            source=source,
            active=skill.active,
            overridden_by=overridden_by,
            plugin_name=plugin_name,
        ))

    # Global skills (only shown if NOT overridden by project)
    for skill in global_skills:
        if skill.name in project_skill_names:
            # This global skill is overridden by a project one - still show it but mark as overridden
            capabilities.append(EffectiveCapability(
                name=skill.name,
                type="skill",
                scope="global",
                source="global_native",
                active=skill.active,
                overridden_by="project",
                plugin_name=None,
            ))
        else:
            # Not overridden - show normally
            capabilities.append(EffectiveCapability(
                name=skill.name,
                type="skill",
                scope="global",
                source="global_native",
                active=skill.active,
                overridden_by=None,
                plugin_name=None,
            ))

    # Collect all MCP servers
    project_mcps = await list_mcp_servers("project")
    global_mcps = await list_mcp_servers("global")

    project_mcp_names = {m.name for m in project_mcps}
    global_mcp_names = {m.name for m in global_mcps}

    # Project MCPs (they override globals with same name)
    for mcp in project_mcps:
        # Project scope has highest priority - never overridden
        overridden_by = None

        source = "project_native"
        plugin_name = None
        if mcp.source and "plugin" in str(mcp.source).lower():
            source = "project_plugin"

        capabilities.append(EffectiveCapability(
            name=mcp.name,
            type="mcp",
            scope="project",
            source=source,
            active=mcp.active,
            overridden_by=overridden_by,
            plugin_name=plugin_name,
        ))

    # Global MCPs
    for mcp in global_mcps:
        if mcp.name in project_mcp_names:
            capabilities.append(EffectiveCapability(
                name=mcp.name,
                type="mcp",
                scope="global",
                source="global_native",
                active=mcp.active,
                overridden_by="project",
                plugin_name=None,
            ))
        else:
            capabilities.append(EffectiveCapability(
                name=mcp.name,
                type="mcp",
                scope="global",
                source="global_native",
                active=mcp.active,
                overridden_by=None,
                plugin_name=None,
            ))

    # Collect plugin-provided items
    plugins = await list_plugins()
    for plugin in plugins:
        if not plugin.active:
            continue

        plugin_scope = "global" if plugin.level == "global" else "project"
        source_prefix = "global_plugin" if plugin.level == "global" else "project_plugin"

        for skill_name in plugin.skills:
            # Don't duplicate if already listed as native
            existing_names = {c.name for c in capabilities if c.type == "skill"}
            if skill_name not in existing_names:
                capabilities.append(EffectiveCapability(
                    name=skill_name,
                    type="skill",
                    scope=plugin_scope,
                    source=source_prefix,
                    active=plugin.active,
                    overridden_by=None,
                    plugin_name=plugin.name,
                ))

        for mcp_name in plugin.mcps:
            existing_names = {c.name for c in capabilities if c.type == "mcp"}
            if mcp_name not in existing_names:
                capabilities.append(EffectiveCapability(
                    name=mcp_name,
                    type="mcp",
                    scope=plugin_scope,
                    source=source_prefix,
                    active=plugin.active,
                    overridden_by=None,
                    plugin_name=plugin.name,
                ))

    return capabilities
