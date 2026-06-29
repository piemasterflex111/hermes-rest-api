"""
Message endpoints — send messages to agents and retrieve history.

Endpoints:
- POST   /api/sessions/{id}/messages      — Send a message to an agent
- GET    /api/sessions/{id}/messages      — Get message history
- POST   /api/sessions/{id}/messages/stream — Send message with SSE streaming
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

from app.sessions import session_store


class MessageRequest(BaseModel):
    """Request to send a message to an agent."""
    message: str
    stream: bool = False


class MessageResponse(BaseModel):
    """Response from an agent after processing a message."""
    session_id: str
    message_id: str
    response: str
    tool_calls: List[dict] = []


class MessagesList(BaseModel):
    messages: List[dict]


router = APIRouter()


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: str) -> MessagesList:
    """Get the message history for a session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = session_store.get_messages(session_id)
    if messages is None:
        return MessagesList(messages=[])

    return MessagesList(messages=messages)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=MessageResponse,
)
def send_message(session_id: str, req: MessageRequest) -> MessageResponse:
    """
    Send a message to an agent and get its response.

    This is the main entry point for agent interaction. The agent:
    1. Receives the message
    2. Runs its reasoning loop
    3. Executes any requested tools
    4. Returns the final response
    """
    # Verify session exists
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the agent
    agent = session_store.get_agent(session_id)
    if not agent:
        raise HTTPException(status_code=400, detail="Session has no active agent")

    # Run the agent
    try:
        result = agent.run(req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Increment message counter
    session_store.increment_message_count(session_id)

    import uuid
    message_id = str(uuid.uuid4())

    return MessageResponse(
        session_id=session_id,
        message_id=message_id,
        response=result if isinstance(result, str) else str(result),
    )
