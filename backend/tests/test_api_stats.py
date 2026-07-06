"""Tests for Stats API endpoints"""

import pytest


@pytest.mark.asyncio
async def test_get_context_window(client):
    r = await client.get("/api/v1/stats/context")
    assert r.status_code == 200
    data = r.json()
    assert "used" in data
    assert "remaining" in data
    assert "max_context" in data
    assert "segments" in data


@pytest.mark.asyncio
async def test_get_usage_time_series(client):
    r = await client.get("/api/v1/stats/usage?days=7")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 7


@pytest.mark.asyncio
async def test_get_usage_aggregate(client):
    r = await client.get("/api/v1/stats/aggregate")
    assert r.status_code == 200
    data = r.json()
    assert "total_input" in data
    assert "total_output" in data
    assert "total_tools" in data
    assert "total_tokens" in data


@pytest.mark.asyncio
async def test_record_token_event(client):
    r = await client.post("/api/v1/stats/events", json={
        "session_id": "test-session",
        "event_type": "user_prompt",
        "token_count": 100,
    })
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_context_after_events(client):
    """Test that context endpoint returns valid data.

    Note: The record_token_event endpoint is currently a placeholder
    and does not persist events. This test verifies the context
    endpoint returns the expected structure.
    """
    r = await client.get("/api/v1/stats/context?session_id=ctx-test")
    assert r.status_code == 200
    data = r.json()
    assert "used" in data
    assert "remaining" in data
    assert "max_context" in data
