<p align = "center" draggable="false" ><img src="https://github.com/AI-Maker-Space/LLM-Dev-101/assets/37101144/d1343317-fa2f-41e1-8af1-1dbb18399719"
     width="200px"
     height="auto"/>
</p>

<h1 align="center" id="heading">Session 11: Claude Code & the Claude Agent SDK</h1>

| 📰 Session Sheet | ⏺️ Recording | 🖼️ Slides | 👨‍💻 Repo | 📝 Homework | 📁 Feedback |
|:-----------------|:-------------|:----------|:----------|:------------|:------------|
| [Session 11: Claude Code & Claude Agent SDK ](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Modules/11_Claude_Code) |[Recording!](https://us02web.zoom.us/rec/share/2I5HA6DwVFgmtyjPaq1SJDgkaVEuYZoWYyMCK8DOAZ99Zm6f7dTi0IGONXj6mRel.YHFzKF03mI5v6JAM) <br> passcode: `&Qhi!cf0`| [Session 11 Slides](https://canva.link/uw1cl42x84tm6zh) |You are here! <br><br> [Certification Challenge](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Certification%20Challenge) | [Optional Session 11 Assignment](https://forms.gle/sAyr5BgBLTfgJV8EA) <br><br>  [Cert Challenge Submission Form](https://forms.gle/xtM9F38nfRKcdjH97)| [Feedback 7/7](https://forms.gle/oDrguLDNvva65mtM8) |

## Useful Resources

**Claude Code**
- [Claude Code Documentation](https://code.claude.com/docs) — official docs: setup, workflows, settings
- [Claude Code Quickstart](https://code.claude.com/docs/en/quickstart) — from install to first session
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) — Anthropic engineering guide

**Claude Agent SDK**
- [Agent SDK Overview](https://docs.anthropic.com/en/api/agent-sdk/overview) — what the SDK is and when to use it
- [Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) — Anthropic engineering deep dive

## Main Assignment

**Build a chat web app powered by the Claude Agent SDK** — and build it *with* Claude Code.

This session is markdown-only on purpose. There is no starter code and no notebook: every line of code in your final app will be written in collaboration with Claude Code. The session has one build arc across a single breakout room:

```text
you → Claude Code → chat app skeleton → wire in Agent SDK query()
      (FastAPI + chat UI, echo stub)      ├─ tools: Read / Glob / Grep
                                           └─ your custom tool
```

The finished product: a **codebase concierge** — a chat interface in the browser where an agent (with real tools) answers questions about any repository you point it at. In Session 10 you served models behind endpoints; today you serve an *agent* behind one.

Work through the three guides in order:

```text
01_Installing_Claude_Code.md   # install, authenticate, verify
02_Using_Claude_Code.md        # drive Claude Code; scaffold the chat app skeleton
03_Claude_Agent_SDK.md         # add the agent and connect it to your website
```

## Outline

### Breakout Room #1: Claude Code, the Agent SDK, and the Connection

- Task 1: Install Claude Code and authenticate ([guide](./01_Installing_Claude_Code.md))
- Task 2: Learn the loop — explore a repo you didn't write ([guide](./02_Using_Claude_Code.md))
- Task 3: Scaffold the chat app skeleton with Claude Code (plan → implement → verify)
- Task 4: Write the project's `CLAUDE.md`
- Question #1 and Question #2
- Task 5: Install the Agent SDK and run your first `query()` ([guide](./03_Claude_Agent_SDK.md))
- Task 6: Wire the agent into `/api/chat` — replace the echo stub
- Task 7: Conversation memory — resume sessions across messages
- Task 8: Give the agent a custom tool
- Question #3 and Question #4
- Activity #1: Level Up the Chat App

## Questions

### ❓ Question #1

While scaffolding in Task 3 you used **plan mode** before letting Claude Code write anything. Why does an agent that can execute shell commands need a permission system at all, and why is plan mode particularly valuable when starting a project from an empty directory?

#### ✅ Answer

- An agent that can execute shell commands needs a permission system to limit the blast radius of any mistakes or "misunderstandings" between operator and agent. 
- Plan mode is valuable partly because it front-loads the design process and gives the operator opportunities to make corrections until the plan is satisfactory, but also because it gives the operator an opportunity to see how the agent will respond and provide additional guidance before allowing the agent to run any commands that could be destructive. 

### ❓ Question #2

`CLAUDE.md` is loaded into context at the start of every session. What belongs in it — and what *doesn't*? How does this relate to what you learned about context management and memory in Session 3?

#### ✅ Answer

What belongs in CLAUDE.md 
-  lightweight, high-leverage info the agent shouldn’t have to rediscover every session 
- depending on location, can be personal preferences (~/.claude/CLAUDE.md) or project-specific (./CLAUDE.md in chat-app/) 
- For this app includes things like application architecture (to support future code/design changes), how to run, test (uv run uvicorn…, the curl to /api/chat, and that CONCIERGE_REPO_DIR must be set).

What doesn’t belong 
- facts non-critical or easily readable from the code, the full build spec, long documents or details that go stale quickly 
- CLAUDE.md is loaded at the start of every session, extra lines permanently consume context and contribute to context rot — the same finite-window problem Session 3 addressed with summarization and /compact, but here we prevent rot up front by managing what’s injected and when more carefully
- That’s different from conversation memory (Task 7’s conversation_id → SDK session_id): CLAUDE.md is static project memory across Claude Code sessions; session resume is thread memory within a chat. Both manage limited context, but in different areas of the application.

### ❓ Question #3

The Agent SDK gives you the same agent loop that powers Claude Code. Compare this to the agent loops you hand-built with LangGraph in Sessions 2–4: what does the SDK give you for free, and what control do you give up?

#### ✅ Answer

What you get for free:
- loops and retries, tools, permissions, MCP, session persistence, compaction

What you give up: 
- per-iteration control, arbitrary graphs

Observation: 
- claude sdk gives less visibility and control over the loop steps.. which speeds outcomes but its harder to enforce rigid routing
- LangGraph lets you directly define nodes, edges, state which gives a more predictable flow. 


### ❓ Question #4

Your chat app could have called a chat completions API directly, the way you did early in the course. What do you gain by routing every message through the Agent SDK's `query()` instead — and what new risks does an agent with tools introduce that a plain chat completion doesn't have? How did your tool allowlist and permission mode address them?

#### ✅ Answer

What you get: 
- A chat returns text from the model’s training context, it can’t explore the target repo's tree. 
- Routing through query() gives you the same tool-using loop as Claude Code: Read, Glob, Grep, plus custom tools like count_lines. 
- You also get session resume, streaming from the message loop, and governance knobs (allowlist, max_turns) as part of an opinionated harness — less hand-wiring than assembling loops in LangGraph, and the right shape for a codebase concierge behind an HTTP endpoint.

New risks:
- An agent with tools can read files you didn’t intend, trigger a runaway loop taht burns cost or follow a malicious user prompt if Bash were allowed. 
- On a headless server there’s no operator approving each tool call

How you addressed it:
- restricted the agent to a read-only allowlist (Read, Glob, Grep, and explicitly named MCP tools). max_turns=25 caps runaway loops. 
- didn't give the agent Bash — git_log runs a fixed subprocess I control. 
- In Claude Code, plan mode was the gate while building; in production the allowlist is the permission model.

## Activity 1: Level Up the Chat App

Extend your working chat app with **at least one** of the following (built with Claude Code, of course):

1. **Live progress streaming** — stream the agent's activity to the browser (e.g. via Server-Sent Events) so users see tool calls ("reading `app.py`…") while the agent works, instead of a spinner
2. **Multi-conversation support** — a sidebar of separate conversations, each mapped to its own SDK session
3. **A second custom tool** — something genuinely useful for your target repo (e.g. `git_log` for recent changes, or a test-runner summary tool)

Whichever you pick, demo it in your Loom video and explain the design decision in one paragraph.

## Advanced Activity: The Cat Shop Concierge

Connect your Session 8 cat shop MCP server to your chat app's agent via the SDK's `mcp_servers` option. Your chat app becomes a shopping concierge: users can browse the catalog, fill a cart, and check out — in natural language, through the UI you built, hitting the OAuth-protected server you wrote in Session 8.

Include your findings and a demo in your Loom video.

## Ship 🚢

The working chat app!

### Deliverables

- A short Loom showing:
  - Claude Code scaffolding or extending the app (plan → implement → verify — show the plan!); and
  - the chat app answering real questions about a repository, including at least one visible custom-tool use

## Share 🚀

Make a social media post about your final application!

### Deliverables

- Make a post on any social media platform about what you built!

Here's a template to get you started:

```
🚀 Exciting News! 🚀

I am thrilled to announce that I have just built and shipped a chat app powered by the Claude Agent SDK — scaffolded entirely with Claude Code! 🎉🤖

🔍 Three Key Takeaways:
1️⃣
2️⃣
3️⃣

Let's continue pushing the boundaries of what's possible in the world of AI agents. Here's to many more innovations! 🚀
Shout out to @AIMakerspace !

#ClaudeCode #AgentSDK #AIAgents #Innovation #AI #TechMilestone

Feel free to reach out if you're curious or would like to collaborate on similar projects! 🤝🔥
```

## Submitting Your Homework (Optional For Extra Mark)

Follow these steps to prepare and submit your homework:

1. Pull the latest updates from upstream into the main branch of your repo:

```bash
git checkout main
git pull upstream main
git push origin main
```

2. Work through `01_Installing_Claude_Code.md`, `02_Using_Claude_Code.md`, and `03_Claude_Agent_SDK.md` in order.
3. Build your chat app in a new `chat-app/` folder inside this session directory (include its `CLAUDE.md` — we want to see it!).
4. Fill in your answers to Questions #1–#4 in this README.
5. Complete Activity #1 and record your Loom video.
6. Add, commit, and push your work to your origin repository. Remove `.env` files and API keys before committing.

When submitting your homework, provide the GitHub URL to your repo.
