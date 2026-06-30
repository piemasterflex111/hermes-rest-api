"""Request and response schemas."""

from pydantic import BaseModel
from typing import Optional, List


class SessionCreate(BaseModel):
    model: str = "default"
    base_url: str = ""
    max_turns: int = 10
    enabled_toolsets: Optional[List[str]] = None
    disabled_toolsets: Optional[List[str]] = None
    save_trajectories: bool = False
    verbose: bool = False


class SessionResponse(BaseModel):
    session_id: str
    model: str = "default"
    max_turns: int = 10
    status: str = "running"


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    session_id: str
    message_id: str
    reply: str
    message_count: int = 0
