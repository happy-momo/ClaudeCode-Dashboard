"""Main API router aggregating all sub-routers"""

from fastapi import APIRouter

from .skills import router as skills_router
from .mcp import router as mcp_router
from .plugins import router as plugins_router
from .stats import router as stats_router
from .conversations import router as conversations_router
from .system import router as system_router
from .sessions import router as sessions_router

api_router = APIRouter(prefix="/api/v1")


# Add a simple health check endpoint at /api/v1/status
@api_router.get("/status")
async def health_check():
    """Health check endpoint for development server status."""
    return {"status": "ok", "service": "Claude Dashboard API"}

api_router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
api_router.include_router(mcp_router, prefix="/mcp", tags=["mcp"])
api_router.include_router(plugins_router, prefix="/plugins", tags=["plugins"])
api_router.include_router(stats_router, prefix="/stats", tags=["stats"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(system_router, prefix="/system", tags=["system"])
