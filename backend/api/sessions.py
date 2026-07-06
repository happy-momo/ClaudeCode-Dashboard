"""Session API - Register and manage Claude Code sessions."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from modules.session_registry import registry, SessionInfo

router = APIRouter()


class RegisterSessionRequest(BaseModel):
    """Request to register a Claude Code session."""
    session_id: str
    project_dir: str
    pid: Optional[int] = None


class RegisterSessionResponse(BaseModel):
    """Response after registering a session."""
    success: bool
    session_id: str
    message: str = ""


class SessionListResponse(BaseModel):
    """Response with list of active sessions."""
    sessions: List[SessionInfo]


@router.post("/register", response_model=RegisterSessionResponse)
async def register_session(data: RegisterSessionRequest) -> RegisterSessionResponse:
    """Register a Claude Code session.

    Called by the session_start hook when Claude Code CLI starts.
    """
    await registry.register(data.session_id, data.project_dir, data.pid)
    return RegisterSessionResponse(
        success=True,
        session_id=data.session_id,
        message=f"Session registered: {data.session_id}"
    )


@router.get("", response_model=SessionListResponse)
@router.get("/list", response_model=SessionListResponse)
async def list_sessions() -> SessionListResponse:
    """List all active Claude Code sessions."""
    sessions = await registry.list_sessions()
    return SessionListResponse(sessions=sessions)


@router.get("/{session_id}")
async def get_session(session_id: str) -> SessionInfo:
    """Get details of a specific session."""
    session = await registry.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. "
                   "The session may have expired or Claude Code is not running."
        )
    return session
