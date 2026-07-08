"""MCP servers API endpoints — delegates to ``services.mcp_service``."""

from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional

from models.mcp import (
    CreateMcpRequest,
    UpdateMcpRequest,
    McpServerResponse,
    ConnectivityResult,
    McpConflict,
)
from services import mcp_service
from services.operation_planner import OperationPlanner
from modules.session_registry import registry

router = APIRouter()


@router.get("")
@router.get("/", response_model=list[McpServerResponse])
async def list_mcp_servers(
    scope: str = Query("project", pattern="^(project|global)$"),
    x_claude_session_id: Optional[str] = Header(None)
):
    """List MCP servers. If session_id is provided and scope=project, uses that project's MCPs."""
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

    return await mcp_service.list_servers(scope)


@router.post("")
@router.post("/", response_model=McpServerResponse, status_code=201)
async def add_mcp_server(
    data: CreateMcpRequest,
    x_claude_session_id: Optional[str] = Header(None)
):
    """Create a new MCP server. Requires session_id for project scope."""
    import os

    # Set CLAUDE_PROJECT_DIR for project scope
    if data.scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{x_claude_session_id}' not found. "
                       "Please restart Claude Code to get a new session link."
            )
        os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    plan = OperationPlanner.plan("create", "mcp_server", data.name, data.scope)
    if plan.mode == "readonly":
        raise HTTPException(status_code=405, detail="MCP server creation is not allowed in this scope")
    try:
        from models.mcp import McpServerConfig
        config = McpServerConfig(
            command=data.command or "",
            args=data.args or [],
            env=data.env or {},
            url=data.url,
            transport=data.transport,
        )
        return await mcp_service.create_server(
            name=data.name,
            config=config,
            scope=data.scope,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("")
@router.put("/{name}", response_model=McpServerResponse)
async def update_mcp_server(
    name: str,
    data: UpdateMcpRequest,
    x_claude_session_id: Optional[str] = Header(None)
):
    """Update an existing MCP server. Requires session_id for project scope."""
    import os

    # Set CLAUDE_PROJECT_DIR for project scope
    if data.scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{x_claude_session_id}' not found. "
                       "Please restart Claude Code to get a new session link."
            )
        os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    try:
        from models.mcp import McpServerConfig
        config = McpServerConfig(
            command=data.command or "",
            args=data.args or [],
            env=data.env or {},
            url=data.url,
            transport=data.transport,
        )
        result = await mcp_service.update_server(
            name=name,
            config=config,
            scope=data.scope,
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found in {data.scope} scope")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/{name}")
async def remove_mcp_server(
    name: str,
    scope: str = Query("project", pattern="^(project|global)$"),
    x_claude_session_id: Optional[str] = Header(None)
):
    """Delete an MCP server. Requires session_id for project scope."""
    import os

    # Set CLAUDE_PROJECT_DIR for project scope
    if scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{x_claude_session_id}' not found. "
                       "Please restart Claude Code to get a new session link."
            )
        os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    removed = await mcp_service.delete_server(name, scope)
    if not removed:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    return {"message": f"MCP server '{name}' removed", "success": True}


@router.post("/{name}/test", response_model=ConnectivityResult)
async def test_connectivity(
    name: str,
    scope: str = Query("project", pattern="^(project|global)$"),
    x_claude_session_id: Optional[str] = Header(None)
):
    """Test MCP server connectivity. Requires session_id for project scope."""
    import os

    # Set CLAUDE_PROJECT_DIR for project scope
    if scope == "project" and x_claude_session_id:
        session = await registry.get_session(x_claude_session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{x_claude_session_id}' not found. "
                       "Please restart Claude Code to get a new session link."
            )
        os.environ["CLAUDE_PROJECT_DIR"] = session.project_dir

    return await mcp_service.test_connectivity(name, scope)


@router.get("/conflicts", response_model=list[McpConflict])
async def detect_conflicts():
    return await mcp_service.detect_conflicts()
