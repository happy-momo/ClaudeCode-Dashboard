from pydantic import BaseModel
from typing import Optional, Literal

Scope = Literal["project", "global"]


class ScopeQuery(BaseModel):
    scope: Scope = "project"


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    error: str
    details: Optional[dict] = None


class EffectiveCapability(BaseModel):
    """A unified view item representing either a skill or MCP server."""
    name: str
    type: Literal["skill", "mcp"]
    scope: Scope
    source: str  # "project_native", "global_native", "project_plugin", "global_plugin"
    active: bool = True
    overridden_by: Optional[str] = None  # Which scope overrides this item
    plugin_name: Optional[str] = None  # If provided by a plugin, which one
