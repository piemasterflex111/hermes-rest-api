# Hermes REST API

## What This Is

A REST API that wraps the Hermes AI agent. Each session has its own agent instance with persistent conversation history. The API manages agent lifecycle, tool execution, and session state.

## Architecture

```
Client (mobile/web)
    ↓
HTTP Request
    ↓
FastAPI Routes (input validation)
    ↓
Session Store (agent lifecycle)
    ↓
AIAgent (Hermes core)
    ↓
LLM + Tools
```

## Setup

```bash
cd ~/Work/projects/hermes-rest-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn hermes_api.app.main:app --host 0.0.0.0 --port 8003 --reload
```

## API

### Sessions
- `POST /api/sessions` — Create a new agent session
- `GET /api/sessions` — List all sessions
- `GET /api/sessions/{id}` — Get session info
- `DELETE /api/sessions/{id}` — Delete a session

### Messages
- `POST /api/sessions/{id}/messages` — Send a message
- `GET /api/sessions/{id}/messages` — Get message history

## Example

```bash
# Create a session
curl -X POST http://localhost:8003/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3.6-27b"}'

# Send a message
curl -X POST http://localhost:8003/api/sessions/<id>/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?"}'

# Get response history
curl http://localhost:8003/api/sessions/<id>/messages
```
