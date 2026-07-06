"""Skills API endpoints — delegates to ``services.skill_service``."""

from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import ValidationError
from typing import Optional

from models.skill import (
    CreateSkillRequest,
    ImportSkillRequest,
    SkillResponse,
    UpdateSkillRequest,
    MoveSkillRequest,
)
from services import skill_service
from services.operation_planner import OperationPlanner
from modules.session_registry import registry

router = APIRouter()


@router.get("")
@router.get("/", response_model=list[SkillResponse])
async def list_skills(
    scope: str = Query("project", pattern="^(project|global)$"),
    x_claude_session_id: Optional[str] = Header(None)
):
    """List skills. If session_id is provided and scope=project, uses that project's skills."""
    import os

    # If session_id is provided and scope is project, use that project's directory
    if scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{x_claude_session_id}' not found. "
                       "Please restart Claude Code to get a new session link."
            )
        # Set CLAUDE_PROJECT_DIR to the session's project directory
        os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir
    elif scope == "project" and not x_claude_session_id:
        # No session_id provided for project scope - cannot determine project directory
        raise HTTPException(
            status_code=400,
            detail="X-Claude-Session-Id header is required for project-level skills. "
                   "Please ensure the frontend is sending the session ID in requests."
        )

    return await skill_service.list_skills(scope)


@router.get("/{name}", response_model=SkillResponse)
async def get_skill(
    name: str,
    scope: str = Query("project", pattern="^(project|global)$"),
    x_claude_session_id: Optional[str] = Header(None)
):
    """Get a skill by name. Requires session_id for project scope."""
    import os

    # Set CLAUDE_PROJECT_DIR for project scope
    if scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session:
            os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    skill = await skill_service.get_skill(name, scope)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    return skill


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(
    data: CreateSkillRequest,
    x_claude_session_id: Optional[str] = Header(None)
):
    """Create a new skill. Requires session_id for project scope."""
    import os

    # Set CLAUDE_PROJECT_DIR for project scope
    if data.scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session:
            os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    plan = OperationPlanner.plan("create", "skill", data.name, data.scope)
    if plan.mode == "readonly":
        raise HTTPException(status_code=405, detail="Skill creation is not allowed in this scope")
    try:
        return await skill_service.create_skill(data.name, data.content, data.scope)
    except (FileExistsError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/import", response_model=SkillResponse, status_code=201)
async def import_skill(
    data: ImportSkillRequest,
    x_claude_session_id: Optional[str] = Header(None)
):
    """Import a skill. Requires session_id for project scope."""
    import os

    # Set CLAUDE_PROJECT_DIR for project scope
    if data.scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session:
            os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    try:
        return await skill_service.import_skill(data.name, data.content, data.scope, data.format)
    except (FileExistsError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("/{name}", response_model=SkillResponse)
async def update_skill(
    name: str,
    data: UpdateSkillRequest,
    x_claude_session_id: Optional[str] = Header(None)
):
    """Update an existing skill. Requires session_id for project scope."""
    import os

    scope = data.scope or "project"
    # Set CLAUDE_PROJECT_DIR for project scope
    if scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session:
            os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    if data.content is None:
        raise HTTPException(status_code=400, detail="Content is required for update")
    skill = await skill_service.update_skill(name, data.content, scope)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    return skill


@router.delete("/{name}")
async def delete_skill(
    name: str,
    scope: str = Query("project", pattern="^(project|global)$"),
    x_claude_session_id: Optional[str] = Header(None)
):
    """Delete a skill. Requires session_id for project scope."""
    import os

    # Set CLAUDE_PROJECT_DIR for project scope
    if scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session:
            os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    deleted = await skill_service.delete_skill(name, scope)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    return {"message": f"Skill '{name}' deleted", "success": True}


@router.post("/{name}/move")
async def move_skill(
    name: str,
    data: MoveSkillRequest,
    scope: str = Query("project", pattern="^(project|global)$"),
    x_claude_session_id: Optional[str] = Header(None)
):
    """Move a skill between scopes. Requires session_id for project scope."""
    import os

    # Set CLAUDE_PROJECT_DIR for project scope (either from_scope or target_scope)
    if (scope == "project" or data.target_scope == "project") and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session:
            os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    moved = await skill_service.move_skill(name, scope, data.target_scope)
    if not moved:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found in {scope} scope")
    return {"message": f"Skill '{name}' moved to {data.target_scope}", "success": True}
