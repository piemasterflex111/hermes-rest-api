"""Hermes REST API — FastAPI application.

Exposes the Hermes AI agent as HTTP endpoints, mimicking
hermes --cli and Hermes Desktop capabilities.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import HOST, PORT
from app.models import (
    SessionCreate,
    SessionResponse,
    SessionStatus,
    MessageRequest,
    MessageResponse,
    HealthResponse,
)
from app.services.session import SessionManager
from app.services.agent import AgentExecutor

logger = logging.getLogger("hermes_api")

# Global state
session_mgr = SessionManager()
agent_executors: dict[str, AgentExecutor] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Hermes REST API starting")
    yield
    logger.info("Hermes REST API shutting down")

app = FastAPI(
    title="Hermes REST API",
    description="REST API wrapping the Hermes AI agent — exposes tool use, "
                "terminal, filesystem, skills, memory, and cron as HTTP endpoints.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Health ──

@app.get("/v1/health")
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        active_sessions=len(session_mgr.list_sessions()),
    )

# ── Sessions ──

@app.post("/v1/sessions", response_model=SessionResponse)
async def create_session(req: SessionCreate = SessionCreate()) -> SessionResponse:
    session_id = session_mgr.create_session()
    executor = AgentExecutor(session_id)
    agent_executors[session_id] = executor

    session_info = session_mgr.get_session(session_id)
    return SessionResponse(
        id=session_id,
        status=SessionStatus.RUNNING,
        created_at=session_info["created_at"],
    )

@app.get("/v1/sessions")
async def list_sessions() -> list:
    return session_mgr.list_sessions()

@app.get("/v1/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    session = session_mgr.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.delete("/v1/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    agent_executors.pop(session_id, None)
    if session_mgr.delete_session(session_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

# ── Messages ──

@app.post("/v1/sessions/{session_id}/message", response_model=MessageResponse)
async def send_message(session_id: str, req: MessageRequest) -> MessageResponse:
    executor = agent_executors.get(session_id)
    if not executor:
        raise HTTPException(status_code=404, detail="Session not found")

    response_text = await executor.execute(req.message)

    return MessageResponse(
        session_id=session_id,
        response=response_text,
    )

@app.get("/v1/sessions/{session_id}/stream")
async def stream_message(session_id: str, message: str):
    executor = agent_executors.get(session_id)
    if not executor:
        raise HTTPException(status_code=404, detail="Session not found")

    return StreamingResponse(
        executor.execute_stream(message),
        media_type="text/event-stream",
    )

@app.get("/v1/sessions/{session_id}/history")
async def get_history(session_id: str) -> dict:
    executor = agent_executors.get(session_id)
    if not executor:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"history": executor.get_history()}

# ── Error handling ──

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": "internal_error"},
    )
