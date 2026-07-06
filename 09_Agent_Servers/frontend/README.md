# Cat Health Agent — Frontend

Next.js chat UI that streams from your LangGraph deployment via a secure `/api` proxy (`langgraph-nextjs-api-passthrough`).

Production deployment: [`DEPLOY.md`](../DEPLOY.md)

## Local development

The chat UI needs a **running LangGraph agent** (Python backend). Start that first from the **repo root** — see the main [`README.md`](../README.md) (*Run locally*). Backend setup uses `uv sync` and `uv run langgraph dev` or `langgraph up`; this folder is Node/Next.js only.

From **`frontend/`**:

```bash
npm install
```

Create `.env.local` in this directory:

```text
LANGGRAPH_API_URL=http://localhost:<local-agent-port>
LANGSMITH_API_KEY=lsv2_pt_...
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

```bash
npm run dev
```

Open `http://localhost:3000`. For `langgraph dev`, set `ASSISTANT_ID` to the graph name in `app/page.tsx`. For `langgraph up`, use the UUID from `assistants/search`.

## Deploy to Vercel

```bash
npx vercel           # first link — note Aliased URL
npx vercel --prod
```

Set **Root Directory** to `frontend` if importing via dashboard.

### Environment variables (Vercel only)

| Variable | Example |
|----------|---------|
| `LANGGRAPH_API_URL` | `http://<elastic-ip>:<agent-port>` |
| `LANGSMITH_API_KEY` | `lsv2_pt_…` |
| `NEXT_PUBLIC_API_URL` | `https://<aliased-app>.vercel.app/api` |

See [`DEPLOY.md`](../DEPLOY.md) for rules (absolute URL, Aliased domain, redeploy after changes). **Do not copy `.env.local` to Vercel verbatim** — values differ for production.

## Key files

| File | Role |
|------|------|
| `app/page.tsx` | `ASSISTANT_ID` |
| `app/api/[...path]/route.ts` | Server proxy to LangGraph |
| `components/chat.tsx` | `useStream` + UI |
