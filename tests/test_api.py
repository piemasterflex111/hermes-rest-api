"""Tests for Hermes REST API."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_health(client):
    """Test health endpoint."""
    response = await client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_sessions" in data

@pytest.mark.asyncio
async def test_create_session(client):
    """Test session creation."""
    response = await client.post("/v1/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "running"

@pytest.mark.asyncio
async def test_list_sessions(client):
    """Test listing sessions."""
    response = await client.get("/v1/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_delete_session(client):
    """Test session deletion."""
    # Create a session
    create = await client.post("/v1/sessions")
    session_id = create.json()["id"]
    
    # Delete it
    response = await client.delete(f"/v1/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    
    # Verify it's gone
    get = await client.get(f"/v1/sessions/{session_id}")
    assert get.status_code == 404
