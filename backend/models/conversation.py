from pydantic import BaseModel
from typing import Optional, List, Literal


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: str
    timestamp: Optional[str] = None
    tokens: Optional[int] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    date: str
    tokens: int = 0
    turns: int = 0
    project: Optional[str] = None
    project_folder: Optional[str] = None


class ConversationDetail(ConversationResponse):
    messages: List[ConversationTurn] = []
