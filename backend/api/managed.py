"""Managed settings API — read-only access to organization-managed configuration."""

from fastapi import APIRouter

from services import managed_service

router = APIRouter()


@router.get("/")
async def get_managed():
    """Get all managed configuration (read-only).

    Returns:
      - settings: main managed settings from managed-settings.json
      - mcp: managed MCP servers from managed-mcp.json
      - extra: additional settings from managed-settings.d/
      - editable: False (always read-only)
      - warnings: any issues encountered during loading
    """
    return managed_service.get_all_managed()


@router.get("/settings")
async def get_managed_settings():
    """Get managed settings only."""
    settings = managed_service.get_managed_settings()
    if settings is None:
        return {"settings": {}, "warning": "managed-settings.json not found"}
    return {"settings": settings}


@router.get("/mcp")
async def get_managed_mcp():
    """Get managed MCP servers only."""
    mcp = managed_service.get_managed_mcp()
    if mcp is None:
        return {"mcp": {}, "warning": "managed-mcp.json not found"}
    return {"mcp": mcp}
