"""Pydantic models for Hermes REST API."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SessionStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class SessionCreate(BaseModel):
    """Request to create a new session."""
    model: Optional[str] = None
    provider: Optional[str] = None
    toolsets: Optional[List[str]] = None

class SessionResponse(BaseModel):
    """Session information."""
    id: str
    status: SessionStatus
    created_at: datetime
    pid: Optional[int] = None

class MessageRequest(BaseModel):
    """Request to send a message to an agent."""
    message: str
    stream: bool = False

class MessageResponse(BaseModel):
    """Response from agent."""
    session_id: str
    response: str
    tools_used: List[str] = []

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "0.1.0"
    active_sessions: int = 0
