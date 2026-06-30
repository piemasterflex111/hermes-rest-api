"""
Hermes REST API — Main application entry point.

This is the FastAPI application that exposes the Hermes AI agent
through a REST interface.

Architecture:
-------------
The app is organized in layers:

1. Routes (app/routes/)
   - HTTP endpoints that validate requests
   - Thin layer — just input validation and routing

2. Session Store (app/sessions.py)
   - Manages agent lifecycle
   - Tracks active sessions and their state

3. Agent Factory (app/agent_factory.py)
   - Creates AIAgent instances
   - Handles model selection and CLI integration

For the full implementation guide, see:
https://hermes-agent.nousresearch.com
"""

from fastapi import FastAPI

from app.routes import sessions, messages
from app.schemas import SessionCreate, SessionResponse


app = FastAPI(title="Hermes REST API", description="REST interface for the Hermes AI agent")

app.include_router(sessions.router, prefix="/v1", tags=["Sessions"])
app.include_router(messages.router, prefix="/v1", tags=["Messages"])


@app.on_event("startup")
async def startup_event():
    """Initialize on server startup."""
    pass


@app.get("/")
@app.get("/health")
async def health_check():
    """Health check."""
    from app.sessions import session_store
    return {
        "status": "healthy",
        "active_sessions": len(session_store.list_sessions()),
    }
