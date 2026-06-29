# Hermes REST API — Project Plan

**Author:** Payam Adloo
**Started:** 2026-06-29
**Status:** Planning
**Repo:** `github.com/piemasterflex111/hermes-rest-api`

---

## 1. What This Is

Hermes REST API is a **local AI gateway** that sits between a client (web, mobile, CLI) and the local Qwen model running behind the Governor.

It is NOT a re-implementation of Hermes Desktop. It is a **thin REST control plane** that:

- Routes requests through the Governor (port 8003) to vLLM (port 8001)
- Tracks sessions and message history in SQLite
- Detects when a user revisits a prior conversation and recalls the context
- Logs every request for audit and debugging

## 2. Why We Are Building This

### Real Problem

Hermes Desktop and Hermes CLI work great on this workstation. But there is no standard REST interface to call the local AI from:

- A mobile app running on iOS/Android
- A web dashboard on another machine
- An automated script on a CI server
- A custom tool that needs local AI without Docker or Kubernetes

Every time someone wants to use the local Qwen model from outside Hermes, they have to write their own HTTP client against the Governor or vLLM directly. That is error-prone and requires understanding the internal stack.

### What This Solves

Hermes REST API is the **standard interface** to the local AI stack. It provides:

1. **A clean REST API** with standard OpenAI-compatible endpoints
2. **Session management** so conversations persist and can be resumed
3. **Continuity detection** so repeated questions from prior conversations are recalled
4. **Audit logs** for debugging and quality tracking
5. **A reference implementation** of how to call the Governor correctly

This is not theoretical. The Governor is already running on port 8003. The vLLM model is already running on port 8001. Hermes REST API connects them with a proper control plane.

## 3. Architecture

### Data Flow

```
Client (curl, web, mobile, CLI)
    ↓ HTTPS
Hermes REST API — port 8010
    ↓ HTTP (localhost only)
Governor — port 8003
    ↓ HTTP (localhost only)
vLLM — port 8001
    ↓
Qwen3.6-27B on GPU
```

### Storage

| Component | Technology | Purpose |
|-----------|------------|---------|
| Session metadata | SQLite `sessions` table | Session ID, title, created/updated timestamps |
| Messages | SQLite `messages` table | Role, content, timestamps |
| Session capsules | SQLite `session_capsules` table | Title, summary, entities, decisions, next actions |
| Entity index | SQLite FTS5 virtual table | Full-text search over entities for continuity detection |
| Audit log | File-based `logs/hermes-api.log` | Request/response pairs with timing |

### Port Assignment (CRITICAL)

| Service | Port | Purpose |
|---------|------|---------|
| **Hermes REST API** | **8010** | THIS service — the control plane |
| Governor | 8003 | Request governance, rate limiting, scheduling |
| vLLM | 8001 | GPU inference engine |

**Never let Hermes REST API call its own port as the Governor.** That creates an infinite loop. Governor calls vLLM. Hermes calls Governor. Client calls Hermes.

## 4. Implementation Plan

### Phase 1: Foundation (2 hours)

**Goal:** A working FastAPI app with health check that calls Governor correctly.

**Deliverables:**
- Clean project structure (no duplicate directories)
- `config.py` with proper settings
- `schemas.py` with request/response models
- `main.py` with `/health` endpoint
- `requirements.txt` with correct dependencies
- `uvicorn` runs on port 8010, calls Governor on 8003

**Success criteria:**
```bash
uvicorn hermes_api.app.main:app --host 127.0.0.1 --port 8010
curl http://127.0.0.1:8010/health
# Returns: {"status": "ok", "governor_reachable": true, ...}
```

### Phase 2: Session Management (3 hours)

**Goal:** Create sessions, send messages, store in SQLite.

**Deliverables:**
- `models.py` with database schema
- `database.py` with connection pooling and WAL mode
- `POST /sessions` — create session
- `GET /sessions` — list sessions
- `GET /sessions/{id}` — get session details
- `POST /sessions/{id}/messages` — send message
- `GET /sessions/{id}/messages` — get message history

**Success criteria:**
```bash
# Create session
curl -X POST http://127.0.0.1:8010/sessions
# Returns: {"id": "uuid", "title": null, "created_at": "..."}

# Send message
curl -X POST http://127.0.0.1:8010/sessions/{id}/messages \
  -d '{"content": "Hello World", "role": "user"}'
# Returns: {"id": "uuid", "response": "...", "created_at": "..."}

# Get history
curl http://127.0.0.1:8010/sessions/{id}/messages
# Returns: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
```

### Phase 3: Continuity Engine (4 hours)

**Goal:** Detect when a new session overlaps with prior conversations.

**Deliverables:**
- `continuity.py` with entity extraction and FTS5 search
- `POST /sessions/{id}/continuity-check` — check for prior context
- Session capsule generation after conversations
- Entity extraction (technical terms, file paths, tool names, concepts)
- FTS5 scoring with entity overlap baseline
- Recall card returned BEFORE model call

**Success criteria:**
```bash
# After completing a conversation about "blueprints evaluator"
# Start a new session asking the same thing
curl -X POST http://127.0.0.1:8010/sessions/{new_id}/continuity-check \
  -d '{"content": "Evaluate my project blueprints against job requirements"}'

# Returns:
{
  "is_repeat": true,
  "confidence": 0.88,
  "matched_session_id": "uuid-of-prior-session",
  "matched_session_title": "Blueprints Evaluator Architecture",
  "already_established": [
    "Project uses FastAPI + SQLite + SQLAlchemy",
    "Targets JobOps skill-mapping integration",
    "Requires SOLID principles implementation"
  ],
  "recommended_next_step": "Continue implementation instead of re-explaining"
}
```

### Phase 4: Governor Integration (2 hours)

**Goal:** Robust communication with the Governor layer.

**Deliverables:**
- `GovernorClient` class with retry logic
- Timeout handling (504 Gateway Timeout)
- Request ID tracking
- Graceful degradation when Governor is down
- Rate limit detection and queuing

**Success criteria:**
- Governor up: requests flow through correctly
- Governor down: returns 503 with clear error
- Timeout: returns 504 after configured timeout
- Rate limit: returns 429 with retry-after

### Phase 5: Tests (3 hours)

**Goal:** Prove the system works and handles failures.

**Deliverables:**
- `test_health.py` — health check endpoint
- `test_sessions.py` — CRUD operations
- `test_messages.py` — message storage and retrieval
- `test_continuity.py` — repeat detection, confidence scoring
- `test_governor_client.py` — timeout, retry, error cases
- Integration test: end-to-end request flow

**Success criteria:**
```bash
pytest tests/ -v
# All tests pass
# Governor mock tests pass with Governor offline
```

### Phase 6: Documentation (2 hours)

**Goal:** A developer can spin this up and use it.

**Deliverables:**
- `README.md` setup instructions
- `OPENAPI.yaml` generated from FastAPI
- curl examples for every endpoint
- Architecture diagram
- Troubleshooting guide

---

## 5. Code Quality Standards

### Rules

1. **No hardcoded credentials in code.** Use environment variables or config files.
2. **No secret keys in Git.** `.gitignore` covers `.env`, `*.secret`, `*.key`.
3. **Every function has a docstring** explaining what it does and why.
4. **Every endpoint has validation** via Pydantic schemas.
5. **SQLite uses WAL mode** for concurrent reads/writes.
6. **Governor calls use retries** with exponential backoff.
7. **Test coverage ≥ 70%** for core logic.
8. **Type hints on all functions** — no `Any` unless unavoidable.

### File Structure

```
hermes-rest-api/
├── PLAN.md                        ← This file
├── README.md                       ← Setup, architecture, examples
├── requirements.txt               ← Pinned dependencies
├── hermes_api/
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py              ← Settings
│   │   ├── models.py               ← SQLAlchemy ORM
│   │   ├── schemas.py              ← Pydantic request/response
│   │   ├── main.py                   ← FastAPI app, middleware, lifespan
│   │   ├── services/                   ← Business logic
│   │   │   ├── __init__.py
│   │   │   ├── governor_client.py   ← Governor HTTP client
│   │   │   └── continuity.py        ← Continuity engine, FTS5 search
│   │   └── routes/                   ← API endpoints
│   │       ├── __init__.py
│   │       ├── health.py              ← Health check
│   │       ├── sessions.py            ← Session CRUD
│   │       └── messages.py            ← Message history
└── tests/                           ← Pytest suite
    ├── __init__.py
    ├── test_health.py
    ├── test_sessions.py
    ├── test_messages.py
    ├── test_continuity.py
    └── conftest.py                  ← Shared fixtures
```

---

## 6. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-29 | Port 8010 for Hermes REST API | Governor owns 8003; Hermes must not conflict |
| 2026-06-29 | SQLite over PostgreSQL | Local-first, no external dependencies, WAL handles concurrency |
| 2026-06-29 | FastAPI over Flask | Async support, Pydantic validation, OpenAPI generation |
| 2026-06-29 | Pydantic v2 | Active development, better performance than v1 |
| 2026-06-29 | SQLAlchemy async | Async I/O for concurrent requests, better than raw SQL |
| 2026-06-29 | FTS5 over app-level search | SQLite built-in, no external search engine needed |
| 2026-06-29 | Session capsules | Encapsulate prior context without full transcript injection |
| 2026-06-29 | Governor client retry logic | Governor can be slow under load; retries handle transient failures |

---

## 7. How This Is Built (Engineering Process)

### Step-by-step

1. **Write the plan** (this document) — What we are building and why
2. **Commit the plan** — `git commit -m "Add PLAN.md with project architecture"`
3. **Build Phase 1** — Health check, config, schemas, Governor client
4. **Verify Phase 1** — `curl http://127.0.0.1:8010/health` returns `{"status": "ok"}`
5. **Commit Phase 1** — `git commit -m "Phase 1: Foundation with health check"`
6. **Build Phase 2** — Session management, SQLite, message history
7. **Verify Phase 2** — Create session, send message, get history
8. **Commit Phase 2** — `git commit -m "Phase 2: Session management"`
9. **Continue through Phases 3-6** — Same pattern: build, verify, commit

### Why This Order

- **Health first** because it proves the stack is wired correctly
- **Sessions next** because continuity detection depends on session history
- **Governor integration early** because it is the core networking layer
- **Continuity engine last** because it builds on everything else
- **Tests and docs last** because they verify the final system works

### What Makes This Tangible

At every step, there is a **command to run** and **output to see**:

- `curl` to hit endpoints
- `pytest` to run tests
- `git log` to see progress
- `sqlite3 hermes.db .tables` to inspect the database
- `cat logs/hermes-api.log` to see audit trails

This is not a research document. It is a build plan with verification at every step.

---

## 8. Success Criteria

The project is done when:

1. `curl http://127.0.0.1:8010/health` returns `{"status": "ok"}`
2. Creating a session, sending a message, and getting the response works
3. Continuing a prior session recalls the context correctly
4. Governor being down returns a clear 503 error
5. All pytest pass
6. README explains how to set up and use the system

## 9. What We Are NOT Building

- A re-implementation of Hermes Desktop or CLI
- Authentication or multi-tenant support
- Stripe billing or paid access
- Complex deployment (Docker, Kubernetes, cloud pipelines)

This is a local-first tool for a single user calling their local AI stack.

