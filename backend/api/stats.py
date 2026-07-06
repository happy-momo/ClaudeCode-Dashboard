"""Stats API endpoints"""

from fastapi import APIRouter, Query, Header
from typing import Optional

from models.stats import ContextWindow, UsageTimeSeriesPoint
from modules import stats_manager
from modules.session_registry import registry

router = APIRouter()


@router.get("/context", response_model=ContextWindow)
async def get_context_window(
    session_id: str = Query("default"),
    x_claude_session_id: Optional[str] = Header(None)
):
    """Get context window usage for the current session.

    Returns the last request's actual input tokens (context sent to model)
    plus conversation totals for input, output, and tool calls.

    If X-Claude-Session-Id header is provided, uses that session instead.
    """
    # Use header session_id if provided
    effective_session_id = x_claude_session_id or session_id
    return await stats_manager.get_context_window(effective_session_id)


@router.get("/usage", response_model=list[UsageTimeSeriesPoint])
async def get_usage_time_series(days: int = Query(14, ge=1, le=90)):
    """Get daily token usage for the last N days (including today).

    Each day shows total tokens with proportional breakdown by type.
    """
    return await stats_manager.get_usage_time_series(days)


@router.get("/aggregate")
async def get_usage_aggregate():
    """Get aggregate token usage statistics.

    Returns total input, output, tool calls, and combined token counts.
    """
    return await stats_manager.get_usage_aggregate()


@router.post("/events")
async def record_token_event(event: dict):
    """Record a token event (placeholder for future implementation).

    Currently returns success without storing events.
    """
    return {"status": "ok", "message": "Event recorded (placeholder)"}
