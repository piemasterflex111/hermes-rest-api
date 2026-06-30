"""Tests for Hermes REST API."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from app.main import app


class MockSessionStore:
    def __init__(self):
        self.sessions = {}

    def create(self, **kwargs):
        import uuid
        sid = str(uuid.uuid4())
        self.sessions[sid] = {
            "session_id": sid,
            "model": kwargs.get("model", "default"),
            "max_turns": kwargs.get("max_turns", 10),
            "status": "running",
            "message_count": 0,
        }
        return self.sessions[sid]

    def get_session(self, sid):
        return self.sessions.get(sid)

    def list_sessions(self):
        return list(self.sessions.values())

    def get_agent(self, sid):
        mock = MagicMock()
        mock.run = MagicMock(return_value="Mock response")
        return mock

    def increment_message_count(self, sid):
        if sid in self.sessions:
            self.sessions[sid]["message_count"] += 1

    def delete(self, sid):
        if sid in self.sessions:
            del self.sessions[sid]
            return True
        return False


@pytest.fixture(autouse=True)
def patch_session_store():
    with patch("app.sessions.session_store", MockSessionStore()) as mock_store:
        with patch("app.routes.sessions.session_store", mock_store):
            with patch("app.routes.messages.session_store", mock_store):
                yield mock_store


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post("/v1/sessions", json={
        "model": "gpt-4",
        "max_turns": 5,
    })
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["session_id"]


@pytest.mark.asyncio
async def test_list_sessions(client):
    # Create a session first
    create_resp = await client.post("/v1/sessions", json={"model": "gpt-4"})
    assert create_resp.status_code == 200

    list_resp = await client.get("/v1/sessions")
    assert list_resp.status_code == 200
    # The mock will return data for this session
    data = list_resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_session_lifecycle(client):
    # Create
    create = await client.post("/v1/sessions", json={"model": "gpt-4"})
    assert create.status_code == 200
    session_id = create.json()["session_id"]

    # Get
    get = await client.get(f"/v1/sessions/{session_id}")
    assert get.status_code == 200
    assert get.json()["session_id"] == session_id

    # Message
    send = await client.post(f"/v1/sessions/{session_id}/messages", json={"content": "hello"})
    assert send.status_code == 200
    assert "reply" in send.json()

    # Delete
    delete = await client.delete(f"/v1/sessions/{session_id}")
    assert delete.status_code == 200
    assert delete.json()["status"] == "deleted"

    # Verify it's gone
    fetch = await client.get(f"/v1/sessions/{session_id}")
    assert fetch.status_code == 404
