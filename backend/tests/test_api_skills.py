"""Tests for Skills API endpoints"""

import pytest


@pytest.mark.asyncio
async def test_list_skills_empty(client):
    r = await client.get("/api/v1/skills?scope=project")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_skill(client):
    r = await client.post("/api/v1/skills", json={
        "name": "test-skill",
        "content": "# Test Skill\nA test skill description",
        "scope": "project",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "test-skill"
    assert data["scope"] == "project"
    assert data["active"] is True


@pytest.mark.asyncio
async def test_get_skill(client):
    await client.post("/api/v1/skills", json={
        "name": "my-skill",
        "content": "# My Skill",
        "scope": "project",
    })
    r = await client.get("/api/v1/skills/my-skill?scope=project")
    assert r.status_code == 200
    assert r.json()["name"] == "my-skill"


@pytest.mark.asyncio
async def test_get_skill_not_found(client):
    r = await client.get("/api/v1/skills/nonexistent?scope=project")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_toggle_skill(client):
    await client.post("/api/v1/skills", json={
        "name": "toggle-test",
        "content": "# Toggle",
        "scope": "project",
    })
    r = await client.patch("/api/v1/skills/toggle-test/toggle?scope=project", json={"active": False})
    assert r.status_code == 200

    r = await client.get("/api/v1/skills/toggle-test?scope=project")
    assert r.json()["active"] is False

    r = await client.patch("/api/v1/skills/toggle-test/toggle?scope=project", json={"active": True})
    assert r.status_code == 200

    r = await client.get("/api/v1/skills/toggle-test?scope=project")
    assert r.json()["active"] is True


@pytest.mark.asyncio
async def test_delete_skill(client):
    await client.post("/api/v1/skills", json={
        "name": "to-delete",
        "content": "# Delete",
        "scope": "project",
    })
    r = await client.delete("/api/v1/skills/to-delete?scope=project")
    assert r.status_code == 200

    r = await client.get("/api/v1/skills/to-delete?scope=project")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_duplicate_skill(client):
    await client.post("/api/v1/skills", json={
        "name": "dup",
        "content": "# First",
        "scope": "project",
    })
    r = await client.post("/api/v1/skills", json={
        "name": "dup",
        "content": "# Second",
        "scope": "project",
    })
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_import_skill_with_frontmatter(client):
    r = await client.post("/api/v1/skills/import", json={
        "name": "imported-skill",
        "content": "---\nname: imported-skill\ndescription: A skill imported with frontmatter\n---\n\n# Imported Skill\n\nThis is the skill body.",
        "scope": "project",
        "format": "frontmatter",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "imported-skill"
    assert data["active"] is True


@pytest.mark.asyncio
async def test_import_skill_without_frontmatter(client):
    r = await client.post("/api/v1/skills/import", json={
        "name": "plain-skill",
        "content": "# Plain Skill\nA simple skill without frontmatter.",
        "scope": "global",
        "format": "markdown",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "plain-skill"
    assert data["scope"] == "global"


@pytest.mark.asyncio
async def test_import_duplicate_skill(client):
    await client.post("/api/v1/skills", json={
        "name": "existing",
        "content": "# Existing",
        "scope": "project",
    })
    r = await client.post("/api/v1/skills/import", json={
        "name": "existing",
        "content": "# Duplicate",
        "scope": "project",
        "format": "markdown",
    })
    assert r.status_code == 409
