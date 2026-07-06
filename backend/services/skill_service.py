"""Skill service — safe CRUD for Claude skills.

Uses atomic writes, path-traversal validation, and name sanitization.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from core.errors import ApiError
from config import get_config_path
from models.skill import SkillResponse
from utils.atomic_file import atomic_write_text, create_backup, read_text_file, write_markdown
from utils.security import sanitize_skill_name, validate_path_traversal
from .settings_service import SettingsService

logger = logging.getLogger(__name__)

settings_service = SettingsService()


def _skills_dir(scope: str) -> Path:
    return get_config_path(scope) / "skills"


def _other_scope(scope: str) -> str:
    return "global" if scope == "project" else "project"


def _parse_description(content: str) -> str:
    """Parse the first non-empty line (stripping ``#`` heading prefix) as description."""
    for line in content.strip().splitlines():
        stripped = line.strip()
        if stripped:
            if stripped.startswith("#"):
                stripped = stripped.lstrip("#").strip()
            return stripped
    return ""


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def list_skills(scope: str = "project") -> List[SkillResponse]:
    """Scan the skills directory for this scope."""
    skills: List[SkillResponse] = []
    skills_path = _skills_dir(scope)
    if not skills_path.exists():
        return skills

    settings = await settings_service.get(scope)
    disabled = settings.get("disabledSkills", [])
    other_scope = _other_scope(scope)
    other_settings = await settings_service.get(other_scope)
    other_skill_names: set = set()

    other_path = _skills_dir(other_scope)
    if other_path.exists():
        for f in other_path.iterdir():
            if f.suffix == ".md" and f.is_file():
                other_skill_names.add(f.stem)
            elif f.is_dir() or (f.is_symlink() and f.resolve().is_dir()):
                other_skill_names.add(f.name)

    for entry in sorted(skills_path.iterdir()):
        is_md = entry.suffix == ".md" and entry.is_file()
        is_dir = entry.is_dir() or (entry.is_symlink() and entry.resolve().is_dir())

        if not is_md and not is_dir:
            continue

        name = entry.stem if is_md else entry.name
        content = await _read_content(entry)
        if content is None:
            continue

        overridden = {"scope": other_scope, "name": name} if name in other_skill_names else None

        skills.append(
            SkillResponse(
                name=name,
                description=_parse_description(content),
                content=content,
                scope=scope,
                active=name not in disabled,
                overridden=overridden,
                source=str(entry),
                path=str(entry),
            )
        )

    return skills


async def get_skill(name: str, scope: str = "project") -> Optional[SkillResponse]:
    """Read a single skill by name."""
    skills_path = _skills_dir(scope)
    file_path = skills_path / f"{name}.md"
    if not file_path.exists():
        file_path = skills_path / name

    if not file_path.exists():
        return None

    content = await _read_content(file_path)
    if content is None:
        return None

    settings = await settings_service.get(scope)
    disabled = settings.get("disabledSkills", [])

    return SkillResponse(
        name=name,
        description=_parse_description(content),
        content=content,
        scope=scope,
        active=name not in disabled,
        source=str(file_path),
        path=str(file_path),
    )


async def _read_content(path: Path) -> Optional[str]:
    """Read content from a skill file or directory SKILL.md."""
    if path.is_file() and path.suffix == ".md":
        return read_text_file(path)

    if path.is_dir() or (path.is_symlink() and path.resolve().is_dir()):
        skill_file = path.resolve() / "SKILL.md"
        if skill_file.exists():
            return read_text_file(skill_file)
    return None


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

async def create_skill(name: str, content: str, scope: str = "project") -> SkillResponse:
    """Create a new skill with safety checks.

    Skills are stored as directories with SKILL.md file:
    - User scope: ~/.claude/skills/{skill-name}/SKILL.md
    - Project scope: <project>/.claude/skills/{skill-name}/SKILL.md
    """
    safe_name = sanitize_skill_name(name)
    skills_path = _skills_dir(scope)
    skills_path.mkdir(parents=True, exist_ok=True)

    # Path safety
    try:
        _resolve_safe(skills_path, safe_name)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    # Create skill directory and SKILL.md file
    skill_dir = skills_path / safe_name
    skill_file = skill_dir / "SKILL.md"

    if skill_dir.exists():
        raise FileExistsError(f"Skill '{safe_name}' already exists in {scope} scope")

    skill_dir.mkdir(parents=True, exist_ok=True)
    create_backup(skill_file)
    write_markdown(skill_file, content)

    return SkillResponse(
        name=safe_name,
        description=_parse_description(content),
        content=content,
        scope=scope,
        active=True,
        source=str(skill_file),
        path=str(skill_file),
    )


def _resolve_safe(base: Path, name: str) -> Path:
    """Resolve name inside base and verify it stays within base."""
    target = (base / name).resolve()
    base_resolved = base.resolve()
    try:
        target.relative_to(base_resolved)
    except ValueError:
        raise ValueError(f"Path traversal detected: '{name}' resolves outside '{base}'")
    return target


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

async def update_skill(name: str, content: str, scope: str = "project") -> Optional[SkillResponse]:
    """Update an existing skill."""
    skill_dir = _skills_dir(scope) / name
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return None

    create_backup(skill_file)
    write_markdown(skill_file, content)

    settings = await settings_service.get(scope)
    disabled = settings.get("disabledSkills", [])

    return SkillResponse(
        name=name,
        description=_parse_description(content),
        content=content,
        scope=scope,
        active=name not in disabled,
        source=str(skill_file),
        path=str(skill_file),
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def delete_skill(name: str, scope: str = "project") -> bool:
    """Delete a skill directory and clean up disabled list."""
    skill_dir = _skills_dir(scope) / name
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return False

    create_backup(skill_file)
    import shutil
    shutil.rmtree(str(skill_dir), ignore_errors=True)

    # Remove from disabled list
    settings = await settings_service.get(scope)
    disabled = settings.get("disabledSkills", [])
    if name in disabled:
        disabled.remove(name)
        await settings_service.patch_disabled_list(scope, disabled, "disabledSkills")

    return True


# ---------------------------------------------------------------------------
# Move scope
# ---------------------------------------------------------------------------

async def move_skill(name: str, from_scope: str, to_scope: str) -> bool:
    """Copy skill to target scope, then delete from source."""
    source = await get_skill(name, from_scope)
    if source is None:
        return False

    target_dir = _skills_dir(to_scope) / name
    target_file = target_dir / "SKILL.md"
    target_dir.mkdir(parents=True, exist_ok=True)
    write_markdown(target_file, source.content)

    await delete_skill(name, from_scope)
    return True


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

async def import_skill(
    name: str,
    content: str,
    scope: str = "project",
    format: str = "markdown",
) -> SkillResponse:
    """Import a skill, optionally parsing YAML frontmatter.

    Skills are stored as directories with SKILL.md file:
    - User scope: ~/.claude/skills/{skill-name}/SKILL.md
    - Project scope: <project>/.claude/skills/{skill-name}/SKILL.md
    """
    import re

    description = ""
    processed = content

    if format == "frontmatter":
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            fm_text = match.group(1)
            for line in fm_text.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key == "name" and value:
                        name = value
                    elif key == "description" and value:
                        description = value
            processed = content

    if not description:
        description = _parse_description(processed)

    safe_name = sanitize_skill_name(name)
    skills_path = _skills_dir(scope)
    skills_path.mkdir(parents=True, exist_ok=True)

    # Create skill directory and SKILL.md file
    skill_dir = skills_path / safe_name
    skill_file = skill_dir / "SKILL.md"

    if skill_dir.exists():
        raise FileExistsError(f"Skill '{safe_name}' already exists in {scope} scope")

    skill_dir.mkdir(parents=True, exist_ok=True)
    write_markdown(skill_file, processed)

    return SkillResponse(
        name=safe_name,
        description=description,
        content=processed,
        scope=scope,
        active=True,
        source=str(skill_file),
        path=str(skill_file),
    )


# ---------------------------------------------------------------------------
# Fork
# ---------------------------------------------------------------------------

async def fork_skill(skill_id: str, from_scope: str, to_scope: str) -> Optional[SkillResponse]:
    """Fork a skill into another scope."""
    source = await get_skill(skill_id, from_scope)
    if source is None:
        return None

    target_dir = _skills_dir(to_scope) / skill_id
    target_file = target_dir / "SKILL.md"
    target_dir.mkdir(parents=True, exist_ok=True)
    write_markdown(target_file, source.content)

    return SkillResponse(
        name=skill_id,
        description=source.description,
        content=source.content,
        scope=to_scope,
        active=True,
        source=str(target_path),
        path=str(target_path),
    )
