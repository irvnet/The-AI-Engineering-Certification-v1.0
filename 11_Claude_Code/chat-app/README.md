# chat-app

A minimal chat web app skeleton: a **FastAPI** backend serving a plain
HTML/CSS/JS chat UI (no frontend framework). The chat endpoint is currently a
**stub that echoes your message** — swap in a real agent later.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (package/venv manager)
- Python 3.12+ (uv can install this for you)

## Install

```bash
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000>.

## API

`POST /api/chat`

```json
// request
{ "message": "hello", "conversation_id": "abc-123" }

// response
{ "reply": "You said: hello" }
```

`GET /` serves the chat UI from `static/index.html`.

## Project layout

```
app/
  main.py     FastAPI app: GET /, POST /api/chat, static mount
  agent.py    generate_reply() — the STUB to replace with a real agent
static/
  index.html  chat UI
  style.css   styling
  app.js      fetch() client that renders both sides of the conversation
```

## Replacing the stub

All chat logic lives in one place: **`app/agent.py:generate_reply`**. Replace
its body with a real implementation (an LLM call, a tool-use agent loop, etc.)
while keeping the function name and signature — no other code needs to change.
