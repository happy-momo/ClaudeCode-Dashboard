"""Configuration manager for reading/writing Claude settings.json"""

import json
from typing import Any, Dict

import aiofiles

from config import get_config_path

DEFAULT_SETTINGS: Dict[str, Any] = {"mcpServers": {}}


async def read_settings(scope: str) -> Dict[str, Any]:
    """Read settings.json for the given scope. Return defaults if file doesn't exist."""
    config_path = get_config_path(scope) / "settings.json"
    if not config_path.exists():
        return DEFAULT_SETTINGS.copy()
    try:
        async with aiofiles.open(str(config_path), "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content) if content.strip() else DEFAULT_SETTINGS.copy()
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()


async def write_settings(scope: str, data: Dict[str, Any]) -> None:
    """Write settings.json for the given scope, preserving existing fields."""
    config_path = get_config_path(scope) / "settings.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing settings first
    existing = await read_settings(scope)

    # Merge: new data overrides existing, but existing fields not in data are preserved
    existing.update(data)

    async with aiofiles.open(str(config_path), "w", encoding="utf-8") as f:
        await f.write(json.dumps(existing, indent=2, ensure_ascii=False))


async def get_mcp_servers(scope: str) -> Dict[str, Any]:
    """Extract mcpServers field from settings."""
    settings = await read_settings(scope)
    return settings.get("mcpServers", {})


async def set_mcp_servers(scope: str, servers: Dict[str, Any]) -> None:
    """Update mcpServers field in settings."""
    await write_settings(scope, {"mcpServers": servers})


async def get_disabled_list(scope: str, key: str = "disabledSkills") -> list:
    """Get a disabled-items list from settings."""
    settings = await read_settings(scope)
    return settings.get(key, [])


async def set_disabled_list(scope: str, items: list, key: str = "disabledSkills") -> None:
    """Set a disabled-items list in settings."""
    await write_settings(scope, {key: items})
