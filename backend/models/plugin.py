from pydantic import BaseModel
from typing import Optional, List

from .common import Scope


class PluginResponse(BaseModel):
    id: str
    name: str
    version: str = "0.0.0"
    description: str = ""
    level: str = "project"  # project or global (legacy, kept for compatibility)
    scope: str = "user"  # user, project, or local (current scope)
    active: bool = True
    skills: List[str] = []
    mcps: List[str] = []
    path: Optional[str] = None


class TogglePluginRequest(BaseModel):
    active: bool


class CatalogPluginEntry(BaseModel):
    """A plugin entry from the marketplace catalog."""
    name: str
    description: str = ""
    marketplace: str = ""
    skills_count: int = 0
    mcps_count: int = 0
    has_mcp_server: bool = False
    installed: bool = False


class InstallPluginRequest(BaseModel):
    plugin_name: str
    marketplace: str = "claude-plugins-official"
    scope: Scope = "global"


class InstallLocalPluginRequest(BaseModel):
    """Install a plugin from a local directory path."""
    path: str
    scope: Scope = "project"


class UpdateVersionRequest(BaseModel):
    """Update a plugin's version in its manifest."""
    version: str
