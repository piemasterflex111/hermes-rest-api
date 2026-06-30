"""Session lifecycle routes."""

from fastapi import APIRouter, HTTPException
from uuid import uuid4
from app.schemas import SessionCreate, SessionResponse
from app.sessions import session_store

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse)
async def create_session(req: SessionCreate):
    session = session_store.create(
        model=req.model,
        base_url=req.base_url,
        max_turns=req.max_turns,
        enabled_toolsets=req.enabled_toolsets,
        disabled_toolsets=req.disabled_toolsets,
        save_trajectories=req.save_trajectories,
        verbose=req.verbose,
    )
    return SessionResponse(**session)


@router.get("/sessions")
async def list_sessions():
    return session_store.list_sessions()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    deleted = session_store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}
