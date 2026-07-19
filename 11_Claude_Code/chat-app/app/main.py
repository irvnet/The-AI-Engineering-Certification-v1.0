"""FastAPI app: serves the chat UI and the concierge chat endpoints."""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent import generate_reply, stream_reply

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="chat-app")


class NoCacheStaticFiles(StaticFiles):
    """Serve static assets with no-cache headers.

    The chat UI's JS/CSS change often during development; browsers otherwise
    reuse a cached ``app.js`` and silently run stale client code (e.g. hitting
    the old non-streaming endpoint). Force revalidation on every request.
    """

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def index() -> FileResponse:
    """Serve the chat UI."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Return an assistant reply for the given message.

    Delegates to ``generate_reply`` (currently a stub) — that is the one place
    to swap in a real agent.
    """
    reply = generate_reply(req.message, req.conversation_id)
    return ChatResponse(reply=reply)


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """Stream the concierge's progress and final answer as Server-Sent Events.

    Each event is one SSE frame: ``data: <json>\\n\\n``, where the JSON is one of
    the ``status`` / ``tool`` / ``done`` / ``error`` events yielded by
    :func:`app.agent.stream_reply`. The client shows ``tool`` lines live while
    the agent works, then renders the ``done`` reply.
    """

    async def event_source():
        async for event in stream_reply(req.message, req.conversation_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Serve css/js. Mounted after routes so it doesn't shadow "/".
# NoCacheStaticFiles ensures the browser always runs the current client code.
app.mount("/static", NoCacheStaticFiles(directory=STATIC_DIR), name="static")
