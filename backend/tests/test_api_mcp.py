"""Tests for MCP API endpoints"""

import pytest


@pytest.mark.asyncio
async def test_list_mcp_empty(client):
    r = await client.get("/api/v1/mcp?scope=project")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_add_mcp_server(client):
    r = await client.post("/api/v1/mcp", json={
        "name": "test-server",
        "command": "python test.py",
        "args": ["--port", "3000"],
        "scope": "project",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "test-server"
    assert data["config"]["command"] == "python test.py"


@pytest.mark.asyncio
async def test_toggle_mcp_server(client):
    await client.post("/api/v1/mcp", json={
        "name": "toggle-test",
        "command": "node server.js",
        "scope": "project",
    })
    r = await client.patch("/api/v1/mcp/toggle-test/toggle?scope=project", json={"active": False})
    assert r.status_code == 200

    r = await client.get("/api/v1/mcp?scope=project")
    server = next(s for s in r.json() if s["name"] == "toggle-test")
    assert server["active"] is False


@pytest.mark.asyncio
async def test_remove_mcp_server(client):
    await client.post("/api/v1/mcp", json={
        "name": "to-remove",
        "command": "python rm.py",
        "scope": "project",
    })
    r = await client.delete("/api/v1/mcp/to-remove?scope=project")
    assert r.status_code == 200

    r = await client.get("/api/v1/mcp?scope=project")
    assert all(s["name"] != "to-remove" for s in r.json())


@pytest.mark.asyncio
async def test_mcp_conflicts(client):
    r = await client.get("/api/v1/mcp/conflicts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_remove_nonexistent_mcp(client):
    r = await client.delete("/api/v1/mcp/nonexistent?scope=project")
    assert r.status_code == 404
