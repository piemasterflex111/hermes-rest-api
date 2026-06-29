"""
Session store — in-memory storage for agent sessions.

In production, replace this with Redis or a database.

Each session maps to one AIAgent instance. The store keeps both:
- Metadata (session_id, created_at, config)
- The live agent reference
"""

import uuid
from datetime import datetime
from typing import Optional, Any

from app.agent_factory import create_agent


class SessionStore:
    """
    Thread-local session store.

    In a production server, this would be:
    - Redis for distributed state
    - Or a DB-backed ORM
    """
    _sessions: dict[str, dict] = {}
    _agents: dict[str, Any] = {}

    def create(
        self,
        model: str = "",
        base_url: str = "",
        max_turns: int = 10,
        enabled_toolsets: Optional[list] = None,
        disabled_toolsets: Optional[list] = None,
        save_trajectories: bool = False,
        verbose: bool = False,
    ) -> dict:
        """
        Create a new session and instantiate its agent.

        Returns the session metadata dict.
        """
        session_id = str(uuid.uuid4())

        # Create the agent instance
        agent = create_agent(
            model=model,
            base_url=base_url,
            max_turns=max_turns,
            enabled_toolsets=enabled_toolsets,
            disabled_toolsets=disabled_toolsets,
            save_trajectories=save_trajectories,
            verbose=verbose,
        )

        # Store metadata
        self._sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "model": model,
            "max_turns": max_turns,
            "enabled_toolsets": enabled_toolsets,
            "disabled_toolsets": disabled_toolsets,
            "message_count": 0,
            "status": "active",
        }

        # Store the agent reference
        self._agents[session_id] = agent

        return self._sessions[session_id]

    def get_agent(self, session_id: str) -> Optional[Any]:
        """Get the AIAgent instance for a session."""
        return self._agents.get(session_id)

    def increment_message_count(self, session_id: str) -> None:
        """Increment the message counter for a session."""
        if session_id in self._sessions:
            self._sessions[session_id]["message_count"] += 1

    def get_messages(self, session_id: str) -> Optional[list]:
        """Get the message history for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        agent = self._agents.get(session_id)
        if agent and hasattr(agent, "messages"):
            return agent.messages
        return session.get("messages", [])

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session metadata."""
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """Delete a session and clean up its agent."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            # Clean up agent
            if session_id in self._agents:
                del self._agents[session_id]
            return True
        return False

    def list_sessions(self) -> list[dict]:
        """List all active sessions (without agent objects)."""
        return list(self._sessions.values())


# Global singleton — one store per server process
session_store = SessionStore()
