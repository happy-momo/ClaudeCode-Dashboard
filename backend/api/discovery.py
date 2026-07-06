"""Discovery API — resource discovery across all scopes."""

from fastapi import APIRouter, Query
from typing import Optional

from services import discovery_service

router = APIRouter()


@router.get("/")
async def discover_resources(project_root: Optional[str] = Query(None)):
    """Discover all Claude Code resources.

    Returns a unified view of:
      - user: settings, skills
      - project: settings, local settings, skills
      - managed: managed settings/MCP (read-only)
      - plugin_cache: cached plugins (read-only)
      - cli: Claude CLI status
      - summary: counts
    """
    return discovery_service.discover_all(project_root)


@router.get("/cli")
async def discover_cli_status():
    """Get Claude CLI installation status."""
    return discovery_service.discover_cli_status()


@router.get("/managed")
async def discover_managed():
    """Get managed configuration (read-only)."""
    return discovery_service.discover_managed()


@router.get("/user/skills")
async def discover_user_skills():
    """List user-level skills."""
    return discovery_service.discover_user_skills()


@router.get("/project/skills")
async def discover_project_skills(project_root: Optional[str] = Query(None)):
    """List project-level skills."""
    return discovery_service.discover_project_skills(project_root)


@router.get("/plugin-cache")
async def discover_plugin_cache():
    """List plugin cache entries (read-only)."""
    return discovery_service.discover_plugin_cache()
