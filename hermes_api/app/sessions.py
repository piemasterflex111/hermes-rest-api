"""Session store — in-memory for now; swap to Redis or DB in production."""

import uuid
from typing import Dict, Optional


class InMemorySessionStore:
    def __init__(self):
        self._sessions: Dict[str, dict] = {}

    def create(self, **kwargs):
        sid = str(uuid.uuid4())
        self._sessions[sid] = {
            "session_id": sid,
            "model": kwargs.get("model", "default"),
            "max_turns": kwargs.get("max_turns", 10),
            "status": "running",
            "message_count": 0,
            "_agent": None,
        }
        return self._sessions[sid]

    def get_session(self, sid: str) -> Optional[dict]:
        return self._sessions.get(sid)

    def list_sessions(self) -> list:
        return [
            {k: v for k, v in s.items() if not k.startswith("_")}
            for s in self._sessions.values()
        ]

    def get_agent(self, sid: str):
        if sid not in self._sessions:
            return None
        return self._sessions[sid].get("_agent")

    def increment_message_count(self, sid: str):
        if sid in self._sessions:
            self._sessions[sid]["message_count"] += 1

    def delete(self, sid: str) -> bool:
        if sid in self._sessions:
            del self._sessions[sid]
            return True
        return False


session_store = InMemorySessionStore()
