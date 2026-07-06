from pydantic import BaseModel
from typing import Optional, List, Literal


class ContextSegment(BaseModel):
    label: str
    value: int
    color: str
    percentage: float


class ContextWindow(BaseModel):
    total: int
    used: int
    remaining: int
    max_context: int = 200000
    segments: List[ContextSegment] = []
    input_tokens: int = 0  # Total input tokens from conversation
    output_tokens: int = 0  # Total output tokens from conversation
    tool_calls: int = 0  # Total tool calls from conversation
    session_id: str = ""  # The actual session ID being monitored


class UsageTimeSeriesPoint(BaseModel):
    date: str
    input: int = 0
    output: int = 0
    tools: int = 0
    total: int = 0  # Total tokens for the day


class TokenEvent(BaseModel):
    session_id: str
    event_type: Literal["session_start", "user_prompt", "post_tool", "message_stop"]
    token_count: Optional[int] = None
    text: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    timestamp: Optional[str] = None
