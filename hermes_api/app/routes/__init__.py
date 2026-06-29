"""
FastAPI route registration.
"""
from app.routes.sessions import router as sessions_router
from app.routes.messages import router as messages_router

def register_routes(app):
    """Register all API routes with the FastAPI app."""
    app.include_router(sessions_router, prefix="/api", tags=["sessions"])
    app.include_router(messages_router, prefix="/api", tags=["messages"])
