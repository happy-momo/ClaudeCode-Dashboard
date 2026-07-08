from pydantic import BaseModel
from typing import Optional, Dict, List

from .common import Scope


class McpServerConfig(BaseModel):
    command: str = ""
    args: Optional[List[str]] = []
    env: Optional[Dict[str, str]] = {}
    url: Optional[str] = None
    transport: Optional[str] = None  # "stdio", "http", "sse"


class CreateMcpRequest(BaseModel):
    name: str
    command: str = ""
    args: Optional[List[str]] = []
    env: Optional[Dict[str, str]] = {}
    scope: Scope = "project"
    url: Optional[str] = None
    transport: Optional[str] = None


class UpdateMcpRequest(BaseModel):
    command: str = ""
    args: Optional[List[str]] = []
    env: Optional[Dict[str, str]] = {}
    scope: Scope = "project"
    url: Optional[str] = None
    transport: Optional[str] = None


class McpServerResponse(BaseModel):
    name: str
    config: McpServerConfig
    scope: Scope
    active: bool = True
    overridden: Optional[dict] = None
    source: Optional[str] = None


class ConnectivityResult(BaseModel):
    name: str
    status: str  # unknown, testing, connected, error
    message: Optional[str] = None
    latency: Optional[float] = None


class McpConflict(BaseModel):
    name: str
    project_config: McpServerConfig
    global_config: McpServerConfig
