# Hermes REST API

A production-grade REST service that exposes the Hermes AI agent as HTTP endpoints. Mobile and web clients get full agent capabilities — tool use, terminal, filesystem, skills, memory, cron — without SSH or Tailscale.

## Architecture

```
Client (mobile, web, script)
    ↓  HTTPS + API key
REST API Server (:8090)
    ├── Authentication (API keys, rate limiting)
    ├── Session Management (create, list, kill agent sessions)
    ├── Streaming (SSE for real-time agent output)
    ├── Tool Capture (log every tool the agent uses)
    └── Sandboxing (limit what mobile clients can access)
        ↓  spawns
Hermes Agent CLI (hermes --cli)
    ↓  tool use
Linux filesystem, terminal, skills, memory, cron...
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/sessions` | Create new agent session |
| GET | `/v1/sessions` | List active sessions |
| GET | `/v1/sessions/:id` | Get session status |
| DELETE | `/v1/sessions/:id` | Kill session |
| POST | `/v1/sessions/:id/message` | Send message to agent |
| GET | `/v1/sessions/:id/stream` | SSE stream of agent output |
| POST | `/v1/files` | Read file on server |
| POST | `/v1/files/write` | Write file on server (sandboxed) |
| POST | `/v1/terminal` | Run terminal command (sandboxed) |
| GET | `/v1/health` | Health check |

## Design Decisions

1. **Sessions are real processes** — each session spawns a Hermes CLI child process. Session ID maps to process ID.
2. **Streaming via SSE** — agent output flows in real-time. No polling.
3. **Tool capture is automatic** — we parse agent stdout to extract tool calls and results.
4. **API key auth** — clients present a bearer token. Keys are stored in `~/.hermes-rest-api/keys.json`.
5. **Sandboxing** — mobile clients get restricted access (no `rm -rf`, no root commands).

## Tech Stack

- Python 3.11
- FastAPI (async web framework)
- Uvicorn (ASGI server)
- aiohttp (for async subprocess management)
- SQLite (session metadata storage)
- Server-Sent Events (streaming)
