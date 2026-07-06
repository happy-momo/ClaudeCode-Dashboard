"""Tests for Plugins API endpoints"""

import pytest


@pytest.mark.asyncio
async def test_list_plugins_empty(client):
    r = await client.get("/api/v1/plugins")
    assert r.status_code == 200
    # The endpoint returns a list (may be non-empty if CLI is installed)
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_catalog(client):
    r = await client.get("/api/v1/plugins/catalog")
    assert r.status_code == 200
    # Catalog may be empty in test env, but endpoint should work
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_plugin_not_found(client):
    r = await client.get("/api/v1/plugins/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_toggle_plugin_not_found(client):
    r = await client.patch("/api/v1/plugins/nonexistent/toggle", json={"active": True})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_uninstall_plugin_not_found(client):
    r = await client.delete("/api/v1/plugins/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_install_plugin_not_found(client):
    r = await client.post("/api/v1/plugins/install", json={
        "plugin_name": "nonexistent-plugin",
        "marketplace": "claude-plugins-official",
        "scope": "global",
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_move_plugin_not_found(client):
    r = await client.patch("/api/v1/plugins/nonexistent/scope", json={
        "target_scope": "global",
    })
    assert r.status_code == 404
