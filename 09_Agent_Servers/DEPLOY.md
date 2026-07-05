# Cat Health Agent — Deployment Guide

Production layout for this project:

```text
Browser → Vercel (Next.js + /api proxy) → EC2 Elastic IP :8123 → langgraph up (Docker)
```

| Component | Where |
|-----------|--------|
| Agent API | EC2 (custom AMI + Terraform) |
| Frontend | Vercel (Hobby) |
| Traces | LangSmith |

---

## Creating the AMI

Packer bakes a **Cat Health Agent v1.0.0** image: Ubuntu 24.04 LTS, Docker, pre-pulled LangGraph stack images, the agent project at `~/agent`, and a `cat-health-agent` systemd unit (not auto-started).

**Prerequisites:** [Packer](https://developer.hashicorp.com/packer/install) 1.14+, AWS credentials, EC2 key pair `asamples` in `us-east-1`.

```bash
cd ami
packer init cat-health-agent-v1.0.0.pkr.hcl
packer build cat-health-agent-v1.0.0.pkr.hcl
```

On success, note the AMI ID (example):

```text
us-east-1: ami-044bbd7c73595a0e1
```

Set it as the Terraform default in `provision/vars.tf` (`ami_id`) so `terraform apply` uses the custom image without passing `-var` each time. Rebuild and update that value whenever you cut a new AMI version.

### What is on the image

| Path / component | Purpose |
|------------------|---------|
| `~/agent/` | `app/`, `data/`, `langgraph.json`, `pyproject.toml`, `uv.lock`, `.dockerignore` |
| `~/agent/.env` | Copied from `.env.example` — **empty keys**; fill on first boot |
| Docker + images | `langchain/langgraph-api:3.13`, `redis:6`, `pgvector/pgvector:pg16` |
| `uv` | Runs `langgraph up` from `~/agent` |
| `cat-health-agent.service` | Installed, **not enabled** until you start it |

**Not baked:** real API keys, assistant UUIDs (created in Postgres on first `langgraph up`).

Terraform-specific defaults and tags: see [`provision/README.md`](provision/README.md).

---

## Deploying the Agent Server on EC2

Terraform provisions an isolated VPC and a single EC2 host with an Elastic IP. The baked AMI already contains the project; you only add secrets and start the service.

```bash
cd provision
terraform init
terraform apply
```

Useful outputs:

```bash
terraform output agent_api_public_ip
terraform output ssh_command
terraform output ami_id
```

### 1. Open port 8123 (temporary demo)

The default security group allows **443/80/22** only. `langgraph up` listens on **8123**, so add an inbound rule on the `cat-health-agent-agent-api` security group:

- **TCP 8123** from `0.0.0.0/0` (temporary; tear down when done)

For a longer-lived setup, proxy **443 → localhost:8123** with Caddy/nginx instead of exposing 8123 publicly.

### 2. SSH bootstrap

```bash
# use terraform output ssh_command, e.g.:
ssh -i ~/.ssh/asamples.pem ubuntu@<elastic-ip>

nano ~/agent/.env    # OPENAI_API_KEY, TAVILY_API_KEY, LANGSMITH_API_KEY, LANGSMITH_TRACING=true

sudo systemctl enable --now cat-health-agent
curl http://localhost:8123/ok    # expect {"ok":true}
```

Check service logs if needed:

```bash
journalctl -u cat-health-agent -f
```

### 3. Get the production assistant UUID

With `langgraph up`, the frontend needs a **UUID** (not the graph name):

```bash
curl -s -X POST http://localhost:8123/assistants/search \
  -H 'Content-Type: application/json' \
  -d '{"graph_id":"agent_with_helpfulness"}' | python3 -m json.tool
```

Copy `assistant_id` for the Vercel frontend. UUIDs change if Postgres data is wiped.

### 4. Verify from your laptop

```bash
curl http://<elastic-ip>:8123/ok
```

---

## Deploying the Frontend on Vercel

The Next.js app runs on **Vercel (Hobby)**; it proxies to the EC2 agent API via a server-side route — API keys never go to the browser.

### 1. Deploy to Vercel

```bash
cd frontend
npm install          # first time only
npx vercel           # link project, preview deploy
npx vercel --prod    # production
```

Set **Root Directory** to `frontend` if importing via the Vercel dashboard.

### 2. Environment variables (Vercel → Settings → Environment Variables)

| Variable | Where | Example |
|----------|--------|---------|
| `LANGGRAPH_API_URL` | Server only | `http://<elastic-ip>:8123` |
| `LANGSMITH_API_KEY` | Server only | `lsv2_pt_...` |
| `NEXT_PUBLIC_API_URL` | Public | `https://<your-app>.vercel.app/api` |

After the first deploy, set `NEXT_PUBLIC_API_URL` to your real Vercel URL, then run `vercel --prod` again.

### 3. Assistant ID

In `frontend/app/page.tsx`, set `ASSISTANT_ID` to the **UUID** from the EC2 `assistants/search` call (graph `agent_with_helpfulness`). Redeploy after changing.

| Backend | Port | `ASSISTANT_ID` |
|---------|------|----------------|
| `langgraph dev` (local) | 2024 | `"agent_with_helpfulness"` |
| `langgraph up` (EC2) | 8123 | UUID from search |

### 4. Smoke test

1. Open your Vercel URL.
2. Send a cat-health question.
3. Confirm streaming reply and tool use.
4. Check [LangSmith](https://smith.langchain.com) for traces.

### Local vs production env

| | Local `.env.local` | Vercel |
|--|-------------------|--------|
| `LANGGRAPH_API_URL` | `http://localhost:8123` | `http://<elastic-ip>:8123` |
| `NEXT_PUBLIC_API_URL` | `http://localhost:3000/api` | `https://<app>.vercel.app/api` |

---

## Teardown

```bash
cd provision
terraform destroy
```

Remove the temporary **8123** security group rule if you added it manually.
