# Hermes Front Door Architecture — Learning Record

**Date:** 2026-06-29  
**Purpose:** Easy review notes explaining the difference between Termius Hermes, Telegram Hermes, a basic iOS chatbot, and a true Hermes REST API + iOS app.

---

## 1. Bottom Line

You are not comparing different “brains.”

You are comparing different **front doors** into the same backend system.

```text
Same backend brain:
Hermes agent → Qwen governor → Qwen/vLLM model

Different front doors:
1. Termius SSH
2. Telegram bot
3. Basic iOS chatbot
4. REST API + real iOS app
```

The main difference is **how much control the front door gives you**.

---

## 2. The Core Backend Brain

This is the part underneath all interfaces:

```text
Hermes agent
↓
Qwen request governor on port 8003
↓
Qwen/vLLM container on port 8001
↓
Local model inference
```

### Simple explanation

| Component | Plain English Meaning |
|---|---|
| Hermes agent | The reasoning / tool-using worker |
| Governor | Safety and request-control layer |
| Qwen/vLLM | The local AI model engine |
| Docker | The container runtime keeping Qwen/vLLM isolated |
| Systemd services | Linux auto-start / restart management |

This backend can be reached through different interfaces.

---

## 3. Termius Hermes

### Architecture

```text
iPhone Termius app
↓
SSH connection
↓
Linux terminal
↓
Hermes CLI
↓
Hermes agent
↓
Governor
↓
Qwen/vLLM
```

### What it really is

Termius is a **remote keyboard and screen for your Linux machine**.

You are not using a new app backend. You are logging into the Linux PC and running Hermes almost exactly like you would locally.

### Why it feels like the Linux PC version

Because it basically is the Linux PC version, just accessed from your phone.

### Strengths

- Direct access to Linux commands.
- Full terminal control.
- Closest to local Hermes CLI.
- Useful for debugging and admin work.

### Weaknesses

- Not a polished mobile app.
- Harder to read long chats.
- No native chat session UI.
- Requires SSH knowledge.
- Easy to run dangerous commands if not careful.

### Mental model

```text
Termius = remote terminal into the Linux PC
```

---

## 4. Telegram Hermes

### Architecture

```text
Telegram app
↓
Telegram Bot API
↓
hermes-gateway.service
↓
Telegram adapter/plugin
↓
Hermes agent
↓
Governor
↓
Qwen/vLLM
```

### What it really is

Telegram Hermes is a **messaging adapter**.

You send a message inside Telegram. The Hermes gateway receives it, converts it into an internal Hermes request, sends it to the Hermes agent, then replies back through Telegram.

### Why it feels close to Termius

Both are text-based.

In both cases, you type instructions and Hermes responds.

But the difference is:

```text
Termius = direct terminal access
Telegram = message delivery through a bot
```

### Strengths

- Easy to read on phone.
- Chat history is automatically saved inside Telegram.
- Good for quick commands.
- Good for remote status checks.
- Good for cron/job notifications.
- Easier than SSH for normal usage.

### Weaknesses

- Telegram controls the UI.
- Telegram controls message formatting.
- Telegram controls file behavior.
- Telegram controls notification behavior.
- You do not fully own session design.
- Streaming is awkward compared to a real app.
- Auth is mostly tied to Telegram user/chat IDs.

### Mental model

```text
Telegram Hermes = texting Hermes through a bot
```

---

## 5. Basic Harness iOS Chatbot

### Architecture

```text
Harness iOS app
↓
Some backend/message endpoint
↓
Hermes or model backend
```

### What it really is

A basic iOS chatbot is mostly a **custom chat screen**.

It may feel similar to Telegram because the user action is still:

```text
type message → send → get response
```

### Why your harness app felt similar to Telegram

Because if the app only sends messages and displays responses, then it is functionally similar to Telegram.

The UI is custom, but the architecture is still mostly a chatbot wrapper.

### Strengths

- You own the app screen.
- You can control basic layout.
- You can customize buttons and message bubbles.
- Good first step toward a real product.

### Weaknesses

- If there are no real sessions, it is still just a chat wrapper.
- If there is no persistence layer, history is fragile.
- If there is no auth, it is not product-grade.
- If there is no streaming, the experience feels limited.
- If there is no control plane, it does not manage Hermes deeply.

### Mental model

```text
Basic iOS chatbot = my own chat screen, but still mostly a bot UI
```

---

## 6. True Hermes REST API + iOS App

### Architecture

```text
Hermes iOS app
↓
REST API backend
↓
Auth layer
↓
Session manager
↓
Message store
↓
Tool/control routes
↓
Hermes agent adapter
↓
Governor on 8003
↓
Qwen/vLLM on 8001
```

### Concrete tech choices

**Persistence:** SQLite (`aiosqlite`), tables `sessions(id, created_at)` and `messages(id, session_id, role, content, created_at)`.

**Security:** Local-only initial deploy (bound to `127.0.0.1`, no TLS required). Future: API key auth or mTLS.

### What it really is

This is not just a chatbot.

This is a **real product backend plus a native iOS client**.

The REST API becomes the official control layer for Hermes.

### What makes it different

A real REST API app can do more than send one message.

It can manage:

```text
Sessions
Conversation history
Streaming responses
Tool permissions
System status
Logs
File uploads
User settings
Restart controls
Cron jobs
Notifications
Model selection
Health checks
```

### Example API behavior

```text
POST /sessions
Create a new conversation session.

GET /sessions
List saved sessions.

POST /sessions/{id}/messages
Send a message into a specific session.

GET /sessions/{id}/messages
Load previous messages.

GET /sessions/{id}/stream
Stream assistant output.

GET /health
Check if backend is alive.

GET /system/status
Check Docker, 8001, 8003, Hermes services.

POST /system/restart/hermes
Safely restart Hermes gateway.
```

### Strengths

- You own the entire user experience.
- You own session design.
- You own saved history.
- You can build ChatGPT-style conversation management.
- You can build dashboard/control-plane features.
- You can safely expose only approved operations.
- You can support streaming, files, settings, status, logs, and notifications.

### Weaknesses

- More engineering work.
- Requires backend design.
- Requires database design.
- Requires auth/security design.
- Requires iOS networking and state management.
- Requires careful tool permissions.

### Mental model

```text
REST API + iOS app = your own ChatGPT-style Hermes product
```

---

## 7. Clean Comparison Table

| Interface | What It Is | Who Owns the UI? | Best For | Main Limitation |
|---|---|---|---|---|
| Termius Hermes | SSH terminal into Linux | Linux terminal / Termius | Debugging and direct admin | Not a real mobile app |
| Telegram Hermes | Bot through Telegram | Telegram | Messaging, alerts, remote commands | Telegram controls the experience |
| Basic iOS chatbot | Custom chat wrapper | You partially | Simple mobile chat | Still mostly send/receive |
| REST API + iOS app | Full product backend + native app | You fully | Sessions, tools, control, history | More engineering required |

---

## 8. The Most Important Difference

The difference is not the text box.

All of these can let you type a message.

The real difference is whether the system only does this:

```text
send message → get answer
```

or whether it does this:

```text
create session
↓
save history
↓
stream response
↓
control tools
↓
monitor system health
↓
manage files
↓
send notifications
↓
resume work later
```

The second one is the real REST API + iOS app.

---

## 9. Practical Mental Models

### Termius

```text
“I am remotely using my Linux computer.”
```

### Telegram

```text
“I am texting Hermes through a bot.”
```

### Basic iOS chatbot

```text
“I built my own chat screen.”
```

### REST API + iOS app

```text
“I am building my own Hermes product and control plane.”
```

---

## 10. Why Telegram Feels Valuable Right Now

Telegram is valuable because it gives you:

- Phone access.
- Readable messages.
- Saved chat history.
- Notifications.
- Easier command access than SSH.
- Less friction than opening Termius.

That is why it feels like a good improvement over Termius.

But it is still not the final product because Telegram owns the outer shell.

---

## 11. Why REST API + iOS Is the Next Step

A true REST API + iOS app is the next step if the goal is:

```text
Hermes as a real personal AI app
Hermes as a local ChatGPT-style client
Hermes as a control plane for your AI workstation
Hermes as a portfolio-grade engineering repo
```

This is stronger than Telegram because it proves backend architecture, mobile architecture, session design, API design, persistence, and system control.

---

## 12. Recommended Build Order

Build the backend first.

### Phase 1 — Basic Backend

```text
GET  /health
POST /sessions
GET  /sessions
POST /sessions/{session_id}/messages
GET  /sessions/{session_id}/messages
```

Goal:

```text
Create session → send message → save response → reload history
```

### Phase 2 — Streaming

```text
GET /sessions/{session_id}/stream
```

Goal:

```text
Show response as it is generated
```

### Phase 3 — System Status

```text
GET /system/status
```

Show:

```text
Docker status
Qwen container status
8001 status
8003 status
Hermes gateway status
```

### Phase 4 — Safe Controls

```text
POST /system/restart/hermes
POST /system/restart/governor
```

Important rule:

```text
Never restart the model/governor/Hermes blindly.
Always check health first.
```

### Phase 5 — iOS App

Build iOS screens:

```text
Session list
Chat screen
Streaming message view
System status dashboard
Settings screen
Logs screen
```

---

## 13. What This Proves as an Engineering Repo

A REST API + iOS Hermes app proves more than “I made a chatbot.”

It proves:

- Backend API design.
- Session state management.
- Persistent conversation storage.
- Local AI integration.
- Service orchestration.
- Health checking.
- Mobile client integration.
- Streaming response handling.
- Safe control-plane design.
- Real system debugging.

This is stronger portfolio evidence than a simple Telegram bot or one-screen chatbot.

---

## 14. Final One-Sentence Summary

```text
Termius is remote terminal access, Telegram is a messaging adapter, a basic iOS chatbot is a custom chat wrapper, and a real Hermes REST API + iOS app is the product/control layer that owns sessions, history, tools, status, and user experience.
```
