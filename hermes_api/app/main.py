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
   - Configures model, tools, and settings

4. AIAgent (Hermes core)
   - The actual agent that processes messages
   - Lives in the Hermes agent codebase

Data flow:
----------
Client → Route → Session Store → AIAgent → LLM
                                          ↓
Client ← Route ← Response ← AIAgent ← Tool results


Start:
------
    uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
"""

from fastapi import FastAPI
from app.routes import sessions, messages

app = FastAPI(
    title="Hermes REST API",
    description="REST API for the Hermes AI agent with session management and tool execution.",
    version="0.1.0",
)

# Register routes
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(messages.router, prefix="/api", tags=["Messages"])


@app.get("/")
def root() -> dict:
    """Health check and API info."""
    return {
        "name": "Hermes REST API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "sessions": "/api/sessions",
            "messages": "/api/sessions/{id}/messages",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health() -> dict:
    """Minimal health check for orchestrators."""
    return {"status": "healthy"}
