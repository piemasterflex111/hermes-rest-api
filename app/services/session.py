"""Session manager for Hermes REST API."""
import os
import uuid
from datetime import datetime
from typing import Dict, Optional
from app.config import SESSION_DIR, MAX_SESSIONS

class SessionManager:
    """Manage agent sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        os.makedirs(SESSION_DIR, exist_ok=True)
    
    def create_session(self) -> str:
        """Create a new session and return session ID."""
        if len(self.sessions) >= MAX_SESSIONS:
            raise ValueError(f"Maximum sessions ({MAX_SESSIONS}) reached")
        
        session_id = uuid.uuid4().hex[:16]
        self.sessions[session_id] = {
            "id": session_id,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "pid": None,
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session information."""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> list:
        """List all active sessions."""
        return list(self.sessions.values())
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """Update session information."""
        if session_id in self.sessions:
            self.sessions[session_id].update(kwargs)
            return True
        return False
