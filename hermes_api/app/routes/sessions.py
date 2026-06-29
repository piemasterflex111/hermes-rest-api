"""
Session endpoints — create, list, and delete agent sessions.

Each session corresponds to one AIAgent instance with its own:
- Conversation history
- Tool configuration
- Model settings

Endpoints:
- POST   /api/sessions       — Create a new session
- GET    /api/sessions        — List all sessions
- DELETE /api/sessions/{id}   — Delete a session
- GET    /api/sessions/{id}   — Get session info
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.sessions import session_store


class SessionCreateRequest(BaseModel):
    """Request to create a new agent session."""
    model: str = ""
    base_url: str = ""
    max_turns: int = 10
    enabled_toolsets: Optional[List[str]] = None
    disabled_toolsets: Optional[List[str]] = None
    save_trajectories: bool = False
    verbose: bool = False


class SessionResponse(BaseModel):
    """Response after creating or retrieving a session."""
    session_id: str
    created_at: str
    model: str
    max_turns: int
    enabled_toolsets: Optional[List[str]] = None
    disabled_toolsets: Optional[List[str]] = None
    message_count: int = 0
    status: str


class SessionsList(BaseModel):
    sessions: List[SessionResponse]


router = APIRouter()


@router.post(
    "/sessions",
    response_model=SessionResponse,
)
def create_session(req: SessionCreateRequest) -> SessionResponse:
    """
    Create a new agent session.

    This instantiates a new AIAgent with the requested configuration.
    The agent is ready to receive messages immediately.
    """
    session_data = session_store.create(
        model=req.model,
        base_url=req.base_url,
        max_turns=req.max_turns,
        enabled_toolsets=req.enabled_toolsets,
        disabled_toolsets=req.disabled_toolsets,
        save_trajectories=req.save_trajectories,
        verbose=req.verbose,
    )

    return SessionResponse(**session_data)


@router.get("/sessions")
def list_sessions() -> SessionsList:
    """List all active sessions."""
    sessions = session_store.list_sessions()
    return SessionsList(
        sessions=[SessionResponse(**s) for s in sessions]
    )


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> SessionResponse:
    """Get info about a specific session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(**session)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str) -> dict:
    """
    Delete a session and clean up its agent.

    This frees memory and stops the agent from consuming resources.
    """
    deleted = session_store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"deleted": True, "session_id": session_id}
