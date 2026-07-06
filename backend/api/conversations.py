"""Conversations API endpoints"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from models.conversation import ConversationResponse, ConversationDetail
from modules import conversation_manager
from modules.session_registry import registry

router = APIRouter()


@router.get("", response_model=list[ConversationResponse])
@router.get("/", response_model=list[ConversationResponse])
async def list_conversations(
    x_claude_session_id: Optional[str] = Header(None)
):
    """List all conversations from Claude Code session files.

    If session_id is provided, validates the session exists.
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

    return await conversation_manager.list_conversations()


@router.get("/{session_id}", response_model=ConversationDetail)
async def get_conversation(
    session_id: str,
    x_claude_session_id: Optional[str] = Header(None)
):
    """Get full conversation detail for a session.

    If X-Claude-Session-Id header is provided, validates it matches the requested session.
    """
    # If header session_id is provided, verify it matches the requested session
    if x_claude_session_id and x_claude_session_id != session_id:
        raise HTTPException(
            status_code=403,
            detail="Session ID mismatch. You can only access the current session."
        )

    conversation = await conversation_manager.get_conversation(session_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail=f"Conversation '{session_id}' not found")
    return conversation


@router.delete("/{session_id}")
async def delete_conversation(
    session_id: str,
    x_claude_session_id: Optional[str] = Header(None)
):
    """Delete a conversation session file.

    If X-Claude-Session-Id header is provided, validates it matches the requested session.
    """
    # If header session_id is provided, verify it matches the requested session
    if x_claude_session_id and x_claude_session_id != session_id:
        raise HTTPException(
            status_code=403,
            detail="Session ID mismatch. You can only delete the current session."
        )

    deleted = await conversation_manager.delete_conversation(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Conversation '{session_id}' not found")
    return {"message": f"Conversation '{session_id}' deleted", "success": True}
