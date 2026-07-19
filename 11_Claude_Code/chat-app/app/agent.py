"""The chat "brain".

This module is the single seam where the real agent plugs in. It runs a
read-only **codebase concierge**: given a user question, it uses the Claude
Agent SDK to read/glob/grep a target repository and answer concisely.

The target repo is configured out-of-band via the ``CONCIERGE_REPO_DIR``
environment variable (required) — the agent answers questions about *that*
repo, not this app.

``generate_reply`` keeps its synchronous name and signature so ``app.main``
needs no changes; the async SDK ``query()`` is driven internally via
``asyncio.run()``.
"""

import asyncio
import logging
import os
from pathlib import Path
import subprocess

from collections.abc import AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

REPO_DIR_ENV = "CONCIERGE_REPO_DIR"

# Hard cap so no single request can loop forever on a headless server.
MAX_TURNS = 25

# Read-only allowlist. This is the safety story for running headless: the agent
# can inspect the repo but cannot modify anything or run arbitrary commands.
ALLOWED_TOOLS = ["Read", "Glob", "Grep", "mcp__concierge__count_lines", "mcp__concierge__git_log"]

_sessions: dict[str, str] = {}

SYSTEM_PROMPT = (
    "You are a concierge for the code repository at the current working "
    "directory. Answer questions about this codebase concisely and accurately. "
    "Cite specific file paths (and line numbers when useful).\n\n"
    "You are sandboxed: the ONLY tools available to you are Read, Glob, count_lines, git_log and "
    "Grep. You have NO ability to write, edit, create, or delete files, and NO "
    "ability to run shell commands — those tools are not available in this "
    "configuration. Never claim or imply that you can modify files or run "
    "commands. If asked to do so, briefly explain that you are read-only. "
    "If a question cannot be answered from the repo, say so plainly."
)


@tool("count_lines", "Count lines of code in a file", {"file_path": str})
async def count_lines(args):
    logger.info("count_lines called: %s", args["file_path"])
    with open(args["file_path"]) as f:
        n = sum(1 for _ in f)
    return {"content": [{"type": "text", "text": f"{args['file_path']}: {n} lines"}]}

@tool("git_log", "recent git commits in the repository", {"limit": int})
async def git_log(args):
    logger.info("git_log called: limit=%s", args.get("limit", 10))
    output = subprocess.check_output(
      ["git", "log", "-n", str(args.get("limit", 10)), "--oneline"],
      cwd=_resolve_repo_dir(),
      text=True,
    )

    logger.info("git_log output: %s", output)
    return {"content": [{"type": "text", "text": output}]}

server = create_sdk_mcp_server(name="concierge", version="1.0.0", tools=[count_lines, git_log])








class ConciergeConfigError(Exception):
    """The concierge is not configured correctly (e.g. missing target repo)."""


def _resolve_repo_dir() -> str:
    """Return the absolute path of the target repo, or raise ConciergeConfigError."""
    raw = os.environ.get(REPO_DIR_ENV)
    if not raw:
        raise ConciergeConfigError(
            f"{REPO_DIR_ENV} is not set; no repository to answer questions about."
        )
    path = Path(raw).expanduser()
    if not path.is_dir():
        raise ConciergeConfigError(
            f"{REPO_DIR_ENV}={raw!r} is not an existing directory."
        )

    logger.info("Resolved repo dir: %s", path.resolve())
    return str(path.resolve())


_CONFIG_HELP = (
    "I'm not configured yet — set the `CONCIERGE_REPO_DIR` environment "
    "variable to the repository you'd like me to answer questions about."
)
_GENERIC_ERROR = (
    "Sorry — I ran into a problem answering that. Please try again in a moment."
)


def _summarize_tool(name: str, tool_input: dict | None) -> str:
    """Turn a tool call into a short, human-readable progress line."""
    ti = tool_input or {}
    short = name.split("__")[-1]  # strip the mcp__concierge__ prefix
    if short == "Grep":
        where = ti.get("path") or ti.get("glob")
        return f'Grep "{ti.get("pattern", "")}"' + (f" in {where}" if where else "")
    if short == "Glob":
        return f'Glob {ti.get("pattern", "")}'
    if short == "Read":
        return f"Read {Path(ti.get('file_path', '')).name}"
    if short == "count_lines":
        return f"count_lines {Path(ti.get('file_path', '')).name}"
    if short == "git_log":
        return f"git_log (last {ti.get('limit', 10)} commits)"
    return short


async def stream_reply(
    message: str, conversation_id: str | None = None
) -> AsyncIterator[dict]:
    """Run the concierge and yield progress events as it works.

    Yields dicts: ``{"type": "status"|"tool"|"done"|"error", ...}`` (see the SSE
    contract in ``app.main``). Tool events are emitted live from the assistant's
    ``ToolUseBlock``s as the query loop surfaces them, before the final answer.

    Session resume keys off ``conversation_id`` (see the contract in CLAUDE.md);
    every failure is turned into a polite ``error`` event, never raised, so the
    endpoint never 500s mid-stream.
    """
    try:
        cwd = _resolve_repo_dir()

        resume_id = _sessions.get(conversation_id) if conversation_id else None

        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=ALLOWED_TOOLS,
            cwd=cwd,
            max_turns=MAX_TURNS,
            resume=resume_id,
            mcp_servers={"concierge": server},
        )

        yield {"type": "status", "summary": "Analyzing the repository…"}

        result: ResultMessage | None = None
        async for msg in query(prompt=message, options=options):
            if isinstance(msg, SystemMessage) and msg.subtype == "init":
                if conversation_id:
                    _sessions[conversation_id] = msg.data["session_id"]
            elif isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        yield {
                            "type": "tool",
                            "name": block.name,
                            "summary": _summarize_tool(block.name, block.input),
                        }
            elif isinstance(msg, ResultMessage):
                result = msg

        if result is None:
            raise RuntimeError("Agent produced no result message.")
        if result.is_error:
            raise RuntimeError(f"Agent finished with an error: {result.result!r}")
        yield {"type": "done", "reply": result.result}
    except ConciergeConfigError as exc:
        logger.warning("Concierge not configured: %s", exc)
        yield {"type": "error", "message": _CONFIG_HELP}
    except Exception:  # noqa: BLE001 — never let the endpoint 500 on the user
        logger.exception("Concierge failed to answer a message")
        yield {"type": "error", "message": _GENERIC_ERROR}


async def _collect_reply(message: str, conversation_id: str | None) -> str:
    """Drain :func:`stream_reply`, returning just the final reply text."""
    reply = _GENERIC_ERROR
    async for event in stream_reply(message, conversation_id):
        if event["type"] == "done":
            reply = event["reply"]
        elif event["type"] == "error":
            reply = event["message"]
    return reply


def generate_reply(message: str, conversation_id: str | None = None) -> str:
    """Produce an assistant reply synchronously (non-streaming fallback).

    Drives the same concierge as :func:`stream_reply` but collapses it to a
    single string, so the plain ``POST /api/chat`` endpoint keeps working
    unchanged. Failures already surface as polite ``error`` events, so this
    never raises.
    """
    return asyncio.run(_collect_reply(message, conversation_id))
