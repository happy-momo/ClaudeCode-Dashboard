"""Tests for System API endpoints"""

import pytest


@pytest.mark.asyncio
async def test_get_service_status(client):
    r = await client.get("/api/v1/system/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "running"
    assert "port" in data
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_get_dashboard_url(client):
    r = await client.get("/api/v1/system/dashboard-url")
    assert r.status_code == 200
    data = r.json()
    assert "url" in data
    assert data["url"].startswith("http://")


@pytest.mark.asyncio
async def test_get_effective_capabilities_empty(client):
    r = await client.get("/api/v1/system/effective-capabilities")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_effective_capabilities_with_skills(client):
    # Create a project skill
    await client.post("/api/v1/skills", json={
        "name": "project-skill",
        "content": "# Project Skill",
        "scope": "project",
    })

    # Create a global skill
    await client.post("/api/v1/skills", json={
        "name": "global-skill",
        "content": "# Global Skill",
        "scope": "global",
    })

    r = await client.get("/api/v1/system/effective-capabilities")
    assert r.status_code == 200
    data = r.json()

    skill_names = [c["name"] for c in data if c["type"] == "skill"]
    assert "project-skill" in skill_names
    assert "global-skill" in skill_names


@pytest.mark.asyncio
async def test_get_effective_capabilities_override_detection(client):
    # Create skill in both scopes with same name
    await client.post("/api/v1/skills", json={
        "name": "shared-skill",
        "content": "# Project Version",
        "scope": "project",
    })
    await client.post("/api/v1/skills", json={
        "name": "shared-skill",
        "content": "# Global Version",
        "scope": "global",
    })

    r = await client.get("/api/v1/system/effective-capabilities")
    assert r.status_code == 200
    data = r.json()

    # Both should appear, with override info
    shared_items = [c for c in data if c["name"] == "shared-skill"]
    assert len(shared_items) == 2

    # Project version should have overridden_by = "global"
    project_item = [c for c in shared_items if c["scope"] == "project"]
    assert len(project_item) == 1
    assert project_item[0]["overridden_by"] == "global"

    # Global version should have overridden_by = "project"
    global_item = [c for c in shared_items if c["scope"] == "global"]
    assert len(global_item) == 1
    assert global_item[0]["overridden_by"] == "project"


@pytest.mark.asyncio
async def test_get_effective_capabilities_with_mcp(client):
    # Create an MCP server with unique name
    await client.post("/api/v1/mcp", json={
        "name": "eff-cap-test-server",
        "command": "node",
        "args": ["server.js"],
        "scope": "project",
    })

    r = await client.get("/api/v1/system/effective-capabilities")
    assert r.status_code == 200
    data = r.json()

    mcp_names = [c["name"] for c in data if c["type"] == "mcp"]
    assert "eff-cap-test-server" in mcp_names
