"""
Hermes REST API — Data models (Pydantic schemas for request/response).

These enforce the API contract. Every endpoint accepts and returns
well-defined types — no ad-hoc dicts leaking through.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    """Request body for sending a message to a session."""
    content: str = Field(..., min_length=1, max_length=64000)
    role: Optional[MessageRole] = MessageRole.USER


class MessageResponse(BaseModel):
    """A single message in the conversation history."""
    id: str
    session_id: str
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    """Session metadata returned by the API."""
    id: str
    title: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime
    continuity_score: Optional[float] = None
    matched_session_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SessionCreate(BaseModel):
    """Request body for creating a new session."""
    title: Optional[str] = None


class SessionListResponse(BaseModel):
    """Paginated list of sessions."""
    sessions: list[SessionResponse]
    total: int


class ContinuityCheck(BaseModel):
    """
    Response from the continuity engine — compares a new session against
    prior conversations to detect repeated topics.
    """
    is_repeat: bool
    confidence: float
    matched_session_id: Optional[str] = None
    matched_session_title: Optional[str] = None
    prior_decisions: list[str] = []
    matched_entities: list[str] = []


class HealthResponse(BaseModel):
    """Health check endpoint response."""
    status: str
    version: str
    governor_reachable: bool
    timestamp: datetime


class ErrorDetail(BaseModel):
    """Standardized error response."""
    error: str
    detail: Optional[str] = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
