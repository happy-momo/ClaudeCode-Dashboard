from pydantic import BaseModel
from typing import Optional

from .common import Scope


class SkillBase(BaseModel):
    name: str
    description: Optional[str] = ""
    content: Optional[str] = ""


class CreateSkillRequest(SkillBase):
    scope: Scope = "project"


class UpdateSkillRequest(BaseModel):
    description: Optional[str] = None
    content: Optional[str] = None
    scope: Optional[Scope] = None


class ImportSkillRequest(BaseModel):
    name: str
    content: str
    scope: Scope = "project"
    format: str = "markdown"  # "markdown" or "frontmatter"


class SkillResponse(BaseModel):
    name: str
    description: str = ""
    content: str = ""
    scope: Scope
    active: bool = True
    overridden: Optional[dict] = None
    source: Optional[str] = None
    path: Optional[str] = None


class MoveSkillRequest(BaseModel):
    target_scope: Scope
