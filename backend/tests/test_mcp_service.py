"""Tests for the MCP service layer."""

import pytest

from services.mcp_service import (
    create_server,
    delete_server,
    detect_conflicts,
    list_servers,
    toggle_server,
    update_server,
)


@pytest.fixture(autouse=True)
def clean_settings():
    """Clean settings.json after each test."""
    yield
    import sys
    from pathlib import Path
    test_dir = Path(__file__).parent / "_test_data"
    for d in [test_dir / "project", test_dir / "global"]:
        settings = d / "settings.json"
        if settings.exists():
            settings.unlink()


@pytest.mark.asyncio
async def test_list_servers_empty():
    result = await list_servers("project")
    assert result == []


@pytest.mark.asyncio
async def test_create_server():
    from models.mcp import McpServerConfig
    config = McpServerConfig(command="node", args=["server.js"], env={})
    result = await create_server("my-server", config, "project")
    assert result.name == "my-server"
    assert result.active is True


@pytest.mark.asyncio
async def test_create_server_duplicate():
    from models.mcp import McpServerConfig
    config = McpServerConfig(command="node", args=[], env={})
    await create_server("dup", config, "project")
    with pytest.raises(ValueError, match="already exists"):
        await create_server("dup", config, "project")


@pytest.mark.asyncio
async def test_list_servers_after_create():
    from models.mcp import McpServerConfig
    config = McpServerConfig(command="python", args=["app.py"], env={})
    await create_server("list-srv", config, "project")
    result = await list_servers("project")
    assert len(result) == 1
    assert result[0].name == "list-srv"


@pytest.mark.asyncio
async def test_update_server():
    from models.mcp import McpServerConfig
    config1 = McpServerConfig(command="node", args=["old.js"], env={})
    await create_server("upd-srv", config1, "project")
    config2 = McpServerConfig(command="node", args=["new.js"], env={})
    result = await update_server("upd-srv", config2, "project")
    assert result is not None
    assert result.config.args == ["new.js"]


@pytest.mark.asyncio
async def test_update_server_not_found():
    from models.mcp import McpServerConfig
    config = McpServerConfig(command="node", args=[], env={})
    result = await update_server("nonexistent", config, "project")
    assert result is None


@pytest.mark.asyncio
async def test_delete_server():
    from models.mcp import McpServerConfig
    config = McpServerConfig(command="node", args=[], env={})
    await create_server("del-srv", config, "project")
    assert await delete_server("del-srv", "project") is True
    assert await delete_server("del-srv", "project") is False


@pytest.mark.asyncio
async def test_delete_server_not_found():
    assert await delete_server("nonexistent", "project") is False


@pytest.mark.asyncio
async def test_toggle_server():
    from models.mcp import McpServerConfig
    config = McpServerConfig(command="node", args=[], env={})
    await create_server("tog-srv", config, "project")
    assert await toggle_server("tog-srv", "project", False) is True
    servers = await list_servers("project")
    assert servers[0].active is False


@pytest.mark.asyncio
async def test_detect_conflicts():
    """Conflicts happen when same name exists in both scopes."""
    from models.mcp import McpServerConfig
    config = McpServerConfig(command="node", args=[], env={})
    await create_server("shared-srv", config, "project")
    await create_server("shared-srv", config, "global")
    conflicts = await detect_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0].name == "shared-srv"


@pytest.mark.asyncio
async def test_no_conflicts():
    from models.mcp import McpServerConfig
    config = McpServerConfig(command="node", args=[], env={})
    await create_server("proj-only", config, "project")
    await create_server("glob-only", config, "global")
    conflicts = await detect_conflicts()
    assert len(conflicts) == 0
