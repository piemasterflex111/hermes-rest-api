"""
Pydantic models for the Hermes REST API.

These define the shape of every request and response in our API.
This is the contract between client and server — what data each
endpoint accepts and returns.

Engineering principle: Define your API contract BEFORE you implement
the endpoints. This forces you to think about what clients actually
need.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionCreate(BaseModel):
    """Request to create a new agent session."""
    model: Optional[str] = None
    base_url: Optional[str] = None
    max_turns: int = Field(default=10, ge=1, le=50)
    enabled_toolsets: Optional[list[str]] = None
    disabled_toolsets: Optional[list[str]] = None
    save_trajectories: bool = False
    verbose: bool = False


class SessionInfo(BaseModel):
    """Response with session details."""
    session_id: str
    model: Optional[str]
    base_url: Optional[str]
    max_turns: int
    enabled_toolsets: Optional[list[str]]
    disabled_toolsets: Optional[list[str]]
    save_trajectories: bool
    verbose: bool
    created_at: str
    message_count: int = 0
    is_active: bool = True


class MessageRequest(BaseModel):
    """Request to send a message to a session."""
    message: str


class MessageResponse(BaseModel):
    """Response from agent after processing a message."""
    response: str
    api_calls: int = 0
    completed: bool = True
    duration_seconds: float = 0.0


class SSEEvent(BaseModel):
    """Single SSE event during streaming."""
    event_type: str  # "token", "tool_call", "tool_result", "error", "done"
    data: dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    agent_available: bool


class ErrorResponse(BaseModel):
    """Error response shape."""
    error: str
    detail: Optional[str] = None
