# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                                      # install/refresh dependencies
export CONCIERGE_REPO_DIR=/abs/path/to/repo  # REQUIRED: the repo the concierge answers about
uv run uvicorn app.main:app --reload         # run dev server at http://127.0.0.1:8000
```

There is no test suite or linter configured yet. To smoke-test the API without the browser (with `CONCIERGE_REPO_DIR` set):

```bash
curl -s -X POST localhost:8000/api/chat \
  -H 'content-type: application/json' \
  -d '{"message":"What does this project do? Cite file paths.","conversation_id":"t1"}'
# -> {"reply":"<a concise, path-citing answer about CONCIERGE_REPO_DIR's repo>"}
```

With `CONCIERGE_REPO_DIR` unset, the agent replies politely asking you to set it (it never 500s).

## Architecture

A minimal FastAPI chat app with a vanilla HTML/CSS/JS frontend (no framework, no build step). The chat "brain" is a **read-only codebase concierge**: it answers questions about a target repository (set via `CONCIERGE_REPO_DIR`) using the Claude Agent SDK. The brain is isolated behind a single function so it can be replaced without touching anything else.

- **`app/main.py`** — the FastAPI app. Defines the Pydantic request/response contract (`ChatRequest` / `ChatResponse`), serves `static/index.html` at `GET /`, mounts `static/` at `/static`, and handles `POST /api/chat`. This layer does no chat logic itself — it only validates input and delegates.
- **`app/agent.py`** — `generate_reply(message, conversation_id) -> str` is the **one seam** where chat logic lives. It runs the Claude Agent SDK `query()` against the repo in `CONCIERGE_REPO_DIR`, restricted to read-only tools (`["Read", "Glob", "Grep"]`) with a `max_turns=25` cap and a concierge `system_prompt`, and returns `ResultMessage.result`. The async `query()` is driven synchronously via `asyncio.run()` so the name and signature stay stable and `main.py` needs no changes. Every failure — missing/invalid `CONCIERGE_REPO_DIR` or an agent error — is caught and returned as a polite reply, so `/api/chat` never 500s. The read-only allowlist is the safety story for running headless. (`scratch_query.py` at the repo root is a standalone reference for the `query()` loop shape.)
- **`static/app.js`** — the client. Generates one `conversation_id` per page load (`crypto.randomUUID()`), POSTs to `/api/chat`, and renders both user and assistant bubbles. Handles pending/error states and disables input while a request is in flight.

### Key detail: the conversation_id contract

The frontend already threads a `conversation_id` through every request, but the concierge does not yet use it — each SDK call is stateless (no per-conversation history). That id is the intended key for memory: wire session resume / a `session_store` in `agent.py` (inside `_ask_concierge`), not in `main.py`.

### Static mount ordering

In `main.py`, `app.mount("/static", ...)` is intentionally placed **after** the route definitions so it does not shadow `GET /`. Preserve this ordering if adding routes.
