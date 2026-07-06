"""System API endpoints"""

from fastapi import APIRouter, Header
from typing import Optional

from models.common import EffectiveCapability
from modules import system_manager
from config import DEFAULT_PORT

router = APIRouter()


@router.get("/status")
async def get_service_status():
    return system_manager.get_service_status(DEFAULT_PORT)


@router.get("/dashboard-url")
async def get_dashboard_url():
    return {"url": system_manager.get_dashboard_url(DEFAULT_PORT)}


@router.get("/effective-capabilities", response_model=list[EffectiveCapability])
async def get_effective_capabilities(
    x_claude_session_id: Optional[str] = Header(None)
):
    """Get a unified list of all skills and MCPs with their effective source and status.

    If X-Claude-Session-Id header is provided, uses that session's project directory.
    """
    return await system_manager.get_effective_capabilities(x_claude_session_id)


@router.post("/export-config")
async def export_config_package():
    return await system_manager.export_config_package()
