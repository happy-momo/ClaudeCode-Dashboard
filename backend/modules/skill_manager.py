"""Skill manager for CRUD operations on Claude skills (.md files or directories with SKILL.md)"""

import os
from pathlib import Path
from typing import List, Optional

import aiofiles

from config import get_config_path
from models.skill import SkillResponse
from modules.config_manager import get_disabled_list, set_disabled_list


def _skills_dir(scope: str) -> Path:
    """Get the skills directory for a given scope."""
    return get_config_path(scope) / "skills"


def _other_scope(scope: str) -> str:
    """Get the opposite scope."""
    return "global" if scope == "project" else "project"


def _parse_description(content: str) -> str:
    """Parse the first line of a skill file as description."""
    lines = content.strip().splitlines()
    if not lines:
        return ""
    first = lines[0].strip()
    # Remove markdown heading prefix
    if first.startswith("#"):
        first = first.lstrip("#").strip()
    return first


async def _read_skill_content(skill_path: Path) -> Optional[str]:
    """Read skill content from either a .md file or a directory with SKILL.md."""
    # Case 1: Direct .md file
    if skill_path.is_file() and skill_path.suffix == ".md":
        try:
            async with aiofiles.open(str(skill_path), "r", encoding="utf-8") as f:
                return await f.read()
        except OSError:
            return None

    # Case 2: Directory with SKILL.md
    if skill_path.is_dir() or (skill_path.is_symlink() and skill_path.resolve().is_dir()):
        skill_file = skill_path / "SKILL.md"
        # Follow symlink if needed
        if skill_path.is_symlink():
            skill_file = skill_path.resolve() / "SKILL.md"
        if skill_file.exists():
            try:
                async with aiofiles.open(str(skill_file), "r", encoding="utf-8") as f:
                    return await f.read()
            except OSError:
                return None

    return None


async def list_skills(scope: str) -> List[SkillResponse]:
    """Scan skills directory and return list of Skill objects.
    Also checks the other scope for overrides.

    Supports both:
    - Direct .md files: ~/.claude/skills/skill-name.md
    - Directories with SKILL.md: ~/.claude/skills/skill-name/SKILL.md
    - Symlinked directories: ~/.claude/skills/skill-name -> ~/.agents/skills/skill-name/
    """
    skills: List[SkillResponse] = []
    skills_path = _skills_dir(scope)

    if not skills_path.exists():
        return skills

    disabled = await get_disabled_list(scope, "disabledSkills")
    other_scope = _other_scope(scope)
    other_skills_path = _skills_dir(other_scope)
    other_skill_names: set = set()

    if other_skills_path.exists():
        # Handle both .md files and directories
        for f in other_skills_path.iterdir():
            if f.suffix == ".md" and f.is_file():
                other_skill_names.add(f.stem)
            elif f.is_dir() or (f.is_symlink() and f.resolve().is_dir()):
                other_skill_names.add(f.name)

    for file_path in sorted(skills_path.iterdir()):
        # Support both .md files and directories with SKILL.md
        is_md_file = file_path.suffix == ".md" and file_path.is_file()
        is_dir_with_skill = (
            file_path.is_dir() or (file_path.is_symlink() and file_path.resolve().is_dir())
        ) and (file_path / "SKILL.md").exists()

        if not is_md_file and not is_dir_with_skill:
            continue

        name = file_path.stem if is_md_file else file_path.name

        content = await _read_skill_content(file_path)
        if content is None:
            continue

        description = _parse_description(content)
        overridden = None
        if name in other_skill_names:
            overridden = {"scope": other_scope, "name": name}

        skills.append(
            SkillResponse(
                name=name,
                description=description,
                content=content,
                scope=scope,
                active=name not in disabled,
                overridden=overridden,
                source=str(file_path),
                path=str(file_path),
            )
        )

    return skills


async def get_skill(name: str, scope: str) -> Optional[SkillResponse]:
    """Read a single skill file or directory and return its content."""
    skills_path = _skills_dir(scope)

    # Try both .md file and directory with SKILL.md
    file_path = skills_path / f"{name}.md"
    if not file_path.exists():
        # Try directory structure
        file_path = skills_path / name
        if not file_path.exists() or not ((file_path / "SKILL.md").exists()):
            return None

    content = await _read_skill_content(file_path)
    if content is None:
        return None

    disabled = await get_disabled_list(scope, "disabledSkills")
    description = _parse_description(content)

    return SkillResponse(
        name=name,
        description=description,
        content=content,
        scope=scope,
        active=name not in disabled,
        source=str(file_path),
        path=str(file_path),
    )


async def create_skill(name: str, content: str, scope: str) -> SkillResponse:
    """Write a new skill as {name}/SKILL.md in the skills directory."""
    skills_path = _skills_dir(scope)
    skills_path.mkdir(parents=True, exist_ok=True)

    skill_dir = skills_path / name
    skill_file = skill_dir / "SKILL.md"

    if skill_dir.exists():
        raise FileExistsError(f"Skill '{name}' already exists in {scope} scope")

    skill_dir.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(str(skill_file), "w", encoding="utf-8") as f:
        await f.write(content)

    description = _parse_description(content)
    return SkillResponse(
        name=name,
        description=description,
        content=content,
        scope=scope,
        active=True,
        source=str(skill_file),
        path=str(skill_file),
    )


async def update_skill(name: str, content: str, scope: str) -> Optional[SkillResponse]:
    """Overwrite an existing skill file."""
    skill_dir = _skills_dir(scope) / name
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return None

    async with aiofiles.open(str(skill_file), "w", encoding="utf-8") as f:
        await f.write(content)

    disabled = await get_disabled_list(scope, "disabledSkills")
    description = _parse_description(content)

    return SkillResponse(
        name=name,
        description=description,
        content=content,
        scope=scope,
        active=name not in disabled,
        source=str(skill_file),
        path=str(skill_file),
    )


async def delete_skill(name: str, scope: str) -> bool:
    """Remove a skill directory. Returns True if deleted, False if not found."""
    skill_dir = _skills_dir(scope) / name
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return False

    import shutil
    shutil.rmtree(str(skill_dir), ignore_errors=True)

    # Also remove from disabled list if present
    disabled = await get_disabled_list(scope, "disabledSkills")
    if name in disabled:
        disabled.remove(name)
        await set_disabled_list(scope, disabled, "disabledSkills")

    return True


async def toggle_skill(name: str, scope: str, active: bool) -> bool:
    """Add or remove skill from the disabled list in settings.json."""
    skill_dir = _skills_dir(scope) / name
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return False

    disabled = await get_disabled_list(scope, "disabledSkills")
    if active:
        if name in disabled:
            disabled.remove(name)
    else:
        if name not in disabled:
            disabled.append(name)

    await set_disabled_list(scope, disabled, "disabledSkills")
    return True


async def move_skill(name: str, from_scope: str, to_scope: str) -> bool:
    """Copy skill content to target scope, then delete from source scope."""
    source_skill = await get_skill(name, from_scope)
    if source_skill is None:
        return False

    # Create in target scope
    target_dir = _skills_dir(to_scope) / name
    target_file = target_dir / "SKILL.md"
    target_dir.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(str(target_file), "w", encoding="utf-8") as f:
        await f.write(source_skill.content)

    # Delete from source scope
    await delete_skill(name, from_scope)
    return True


async def import_skill(name: str, content: str, scope: str, format: str = "markdown") -> SkillResponse:
    """Import a skill from content. Supports markdown with optional YAML frontmatter.

    If format is 'frontmatter', parse YAML frontmatter (--- delimiters) to extract
    name and description. Otherwise, treat the entire content as the skill body.
    """
    import re

    description = ""
    processed_content = content

    # Parse YAML frontmatter if present
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if frontmatter_match:
        fm_text = frontmatter_match.group(1)
        # Simple YAML parsing (no pyyaml dependency)
        for line in fm_text.splitlines():
            if ':' in line:
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == 'name' and value:
                    name = value
                elif key == 'description' and value:
                    description = value
        # Use the full content including frontmatter
        processed_content = content

    if not description:
        description = _parse_description(processed_content)

    # Create the skill directory and SKILL.md file
    skills_path = _skills_dir(scope)
    skills_path.mkdir(parents=True, exist_ok=True)

    skill_dir = skills_path / name
    skill_file = skill_dir / "SKILL.md"

    if skill_dir.exists():
        raise FileExistsError(f"Skill '{name}' already exists in {scope} scope")

    skill_dir.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(str(skill_file), "w", encoding="utf-8") as f:
        await f.write(processed_content)

    return SkillResponse(
        name=name,
        description=description,
        content=processed_content,
        scope=scope,
        active=True,
        source=str(file_path),
        path=str(file_path),
    )
