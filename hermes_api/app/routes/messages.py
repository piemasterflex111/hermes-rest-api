"""Message routes for session interactions."""

from fastapi import APIRouter, HTTPException
from app.schemas import MessageCreate, MessageResponse
from app.sessions import session_store

router = APIRouter()


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id: str, req: MessageCreate):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = session_store.get_agent(session_id)
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    response = agent.run(req.content)
    session_store.increment_message_count(session_id)

    return MessageResponse(
        session_id=session_id,
        message_id=str(uuid4()),
        reply=response,
        message_count=session["message_count"],
    )
