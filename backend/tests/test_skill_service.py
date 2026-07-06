"""Tests for the skill service layer."""

import pytest

from services.skill_service import (
    create_skill,
    delete_skill,
    fork_skill,
    get_skill,
    import_skill,
    list_skills,
    move_skill,
    toggle_skill,
    update_skill,
)


@pytest.fixture(autouse=True)
def clean_skills():
    """Clean skill files after each test."""
    yield
    import sys
    from pathlib import Path
    # Get the test directory from conftest
    test_dir = Path(__file__).parent / "_test_data" / "project" / "skills"
    if test_dir.exists():
        for f in test_dir.iterdir():
            if f.suffix == ".md":
                f.unlink()


@pytest.mark.asyncio
async def test_create_skill():
    result = await create_skill("test-create", "# Test\nContent", "project")
    assert result.name == "test-create"
    assert result.active is True


@pytest.mark.asyncio
async def test_create_skill_raises_duplicate():
    await create_skill("dup-test", "# Test", "project")
    with pytest.raises(FileExistsError):
        await create_skill("dup-test", "# Another", "project")


@pytest.mark.asyncio
async def test_list_skills_empty():
    result = await list_skills("project")
    assert result == []


@pytest.mark.asyncio
async def test_list_skills_after_create():
    await create_skill("list-test", "# List Test", "project")
    result = await list_skills("project")
    assert len(result) == 1
    assert result[0].name == "list-test"


@pytest.mark.asyncio
async def test_get_skill():
    await create_skill("get-test", "# Get Test", "project")
    result = await get_skill("get-test", "project")
    assert result is not None
    assert result.name == "get-test"


@pytest.mark.asyncio
async def test_get_skill_not_found():
    result = await get_skill("nonexistent", "project")
    assert result is None


@pytest.mark.asyncio
async def test_update_skill():
    await create_skill("upd-test", "# Old", "project")
    result = await update_skill("upd-test", "# Updated", "project")
    assert result is not None
    assert result.content == "# Updated"


@pytest.mark.asyncio
async def test_update_skill_not_found():
    result = await update_skill("nonexistent", "# New", "project")
    assert result is None


@pytest.mark.asyncio
async def test_delete_skill():
    await create_skill("del-test", "# Delete", "project")
    assert await delete_skill("del-test", "project") is True
    assert await get_skill("del-test", "project") is None


@pytest.mark.asyncio
async def test_delete_skill_not_found():
    assert await delete_skill("nonexistent", "project") is False


@pytest.mark.asyncio
async def test_toggle_skill():
    await create_skill("tog-test", "# Toggle", "project")
    assert await toggle_skill("tog-test", "project", False) is True
    skill = await get_skill("tog-test", "project")
    assert skill is not None
    assert skill.active is False


@pytest.mark.asyncio
async def test_move_skill():
    await create_skill("move-test", "# Move Me", "project")
    # Move from project to global
    moved = await move_skill("move-test", "project", "global")
    assert moved is True
    # Should not exist in project anymore
    assert await get_skill("move-test", "project") is None
    # Should exist in global
    result = await get_skill("move-test", "global")
    assert result is not None
    assert result.name == "move-test"


@pytest.mark.asyncio
async def test_import_skill_frontmatter():
    content = """---
name: imported-skill
description: Imported via frontmatter
---

# Body content
"""
    result = await import_skill("before", content, "project", format="frontmatter")
    assert result.name == "imported-skill"
    assert result.description == "Imported via frontmatter"


@pytest.mark.asyncio
async def test_import_skill_no_frontmatter():
    content = "# Plain skill\nNo frontmatter here"
    result = await import_skill("plain-skill", content, "project", format="markdown")
    assert result.name == "plain-skill"
    assert result.description == "Plain skill"


@pytest.mark.asyncio
async def test_fork_skill():
    """Fork a skill from one scope to another."""
    await create_skill("fork-src", "# Fork Source", "project")
    result = await fork_skill("fork-src", "project", "global")
    assert result is not None
    assert result.name == "fork-src"
    assert result.scope == "global"
