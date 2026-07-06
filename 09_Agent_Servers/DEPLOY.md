# Cat Health Agent — Deployment Guide

Production layout for this project (self-hosted path):

```text
Browser → Vercel (Next.js + /api proxy) → EC2 Elastic IP → langgraph up (Docker)
```

| Component | Where |
|-----------|--------|
| Agent API | EC2 (custom AMI + Terraform) |
| Frontend | Vercel (Hobby) |
| Traces | LangSmith |

Secrets never go to the browser. The Next.js `/api` route proxies server-side using `LANGGRAPH_API_URL` and `LANGSMITH_API_KEY`.

---

## Deployment checklist (in order)

Use this sequence to avoid common mistakes (empty `.env`, wrong Vercel URLs, build failures).

1. **Build AMI** → note AMI ID → set `ami_id` in `provision/vars.tf`
2. **`terraform apply`** → note Elastic IP and `ssh_command`
3. **Security group** → ensure the agent API port is reachable (see [Network access](#network-access))
4. **SSH bootstrap** → fill `~/agent/.env` → start `cat-health-agent` service
5. **Verify agent** on the host, then from your laptop (see [Verify the agent](#verify-the-agent))
6. **Assistant UUID** → `assistants/search` on the host → update `frontend/app/page.tsx`
7. **First Vercel deploy** → note the **Aliased** production URL (not the deployment-specific URL)
8. **Vercel env vars** → set all three → `npx vercel --prod`
9. **Smoke test** → cat-health question on Vercel → check LangSmith traces
10. **Teardown** when done → `terraform destroy` + remove any temporary SG rules

---

## Creating the AMI

Packer bakes a **Cat Health Agent v1.0.0** image: Ubuntu 24.04 LTS, Docker, pre-pulled LangGraph stack images, the agent project at `~/agent`, and a `cat-health-agent` systemd unit (not auto-started).

**Prerequisites:** [Packer](https://developer.hashicorp.com/packer/install) 1.14+, AWS credentials, EC2 key pair in `us-east-1`.

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

See [`ami/README.md`](ami/README.md) for image contents and build notes.

### What is on the image

| Path / component | Purpose |
|------------------|---------|
| `~/agent/` | `app/`, `data/`, `langgraph.json`, `pyproject.toml`, `uv.lock`, `.dockerignore` |
| `~/agent/.env` | Copied from `.env.example` — **empty keys**; fill on first boot |
| Docker + images | `langchain/langgraph-api:3.13`, `redis:6`, `pgvector/pgvector:pg16` |
| `uv` | Runs `langgraph up` from `~/agent` |
| `cat-health-agent.service` | Installed, **not enabled** until you start it |

**Not baked:** real API keys, assistant UUIDs (created in Postgres on first `langgraph up`).

The API listen port is defined in the AMI bootstrap (`ami/install.sh`) and the systemd unit on the host — not in Terraform.

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

> **Note:** `terraform output agent_api_url` shows `https://<ip>` for a future TLS front-end. For the demo proxy path, `LANGGRAPH_API_URL` on Vercel must be **`http://`** and include the agent API port from the systemd unit (see below).

### Network access

The default security group allows **443 / 80 / 22** only. `langgraph up` binds to a separate port (see `ExecStart` in `/etc/systemd/system/cat-health-agent.service` on the host).

For a **short-lived demo**, add an inbound rule on the `cat-health-agent-agent-api` security group for that port (TCP, from your chosen CIDR).

For anything longer-lived, put **Caddy or nginx on 443** and reverse-proxy to `localhost:<agent-port>` instead of exposing the app port publicly.

### SSH bootstrap

```bash
# use terraform output ssh_command, e.g.:
ssh -i ~/.ssh/asamples.pem ubuntu@<elastic-ip>
```

Edit secrets (plain `KEY=value` lines — **no** `export` prefix; systemd `EnvironmentFile` does not accept `export`):

```bash
nano ~/agent/.env
chmod 600 ~/agent/.env
```

Required keys:

```text
OPENAI_API_KEY=
TAVILY_API_KEY=
LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
```

Sanity check without printing secrets:

```bash
awk -F= '/^[A-Z]/ { if (length($2)==0) print $1 "=EMPTY"; else print $1 "=set" }' ~/agent/.env
```

Start the service:

```bash
sudo systemctl enable --now cat-health-agent
journalctl -u cat-health-agent -f   # wait for "Ready!" — first boot can take several minutes
```

If you edit `.env` after the service is already running, restart to pick up keys:

```bash
sudo systemctl restart cat-health-agent
```

### Get the production assistant UUID

With `langgraph up`, the frontend needs a **UUID** (not the graph name):

```bash
curl -s -X POST http://localhost:<agent-port>/assistants/search \
  -H 'Content-Type: application/json' \
  -d '{"graph_id":"agent_with_helpfulness"}' | python3 -m json.tool
```

Use the port shown in the service log (`API: http://localhost:…`) or in `cat-health-agent.service`. Copy `assistant_id` into `frontend/app/page.tsx`. UUIDs change if Postgres data is wiped.

### Verify the agent

On the instance:

```bash
curl http://localhost:<agent-port>/ok    # expect {"ok":true}
```

From your laptop (after SG allows the agent API port):

```bash
curl http://<elastic-ip>:<agent-port>/ok
```

---

## Deploying the Frontend on Vercel

The Next.js app runs on **Vercel (Hobby)**; it proxies to the EC2 agent API via a server-side route.

### 1. Deploy to Vercel

```bash
cd frontend
npm install          # first time only
npx vercel           # link project, preview deploy — note the **Aliased** URL when available
npx vercel --prod    # production
```

Set **Root Directory** to `frontend` if importing via the Vercel dashboard.

Use the **Aliased** production URL (e.g. `https://cat-health-agent-two.vercel.app`), not the deployment-specific hostname (`…-xxxxx-….vercel.app`).

### 2. Environment variables

Set in **Vercel → Settings → Environment Variables** for **Production** (and Preview if needed). **`.env.local` on your laptop is not uploaded to Vercel.**

| Variable | Scope | Value |
|----------|--------|--------|
| `LANGGRAPH_API_URL` | Server only | `http://<elastic-ip>:<agent-port>` — port from systemd unit on EC2 |
| `LANGSMITH_API_KEY` | Server only | `lsv2_pt_…` |
| `NEXT_PUBLIC_API_URL` | Baked into client JS | `https://<your-aliased-app>.vercel.app/api` |

**`LANGGRAPH_API_URL` rules**

- Use **`http://`**, not `https://`, for the demo (no TLS on the agent host yet)
- Include the **agent API port** from the EC2 systemd unit
- Do **not** use `terraform output agent_api_url` as-is (wrong scheme and no app port)

**`NEXT_PUBLIC_API_URL` rules**

- Must be a **full absolute URL** ending in `/api` — the LangGraph browser SDK calls `new URL()` and rejects relative paths like `/api`
- Use your **stable Aliased** Vercel domain, not a one-off deployment URL
- **Redeploy** (`npx vercel --prod`) after any change — `NEXT_PUBLIC_*` is embedded at build time

Or via CLI from `frontend/`:

```bash
npx vercel env add LANGGRAPH_API_URL production
npx vercel env add LANGSMITH_API_KEY production
npx vercel env add NEXT_PUBLIC_API_URL production
```

### 3. Assistant ID

In `frontend/app/page.tsx`, set `ASSISTANT_ID` to the **UUID** from the EC2 `assistants/search` call (graph `agent_with_helpfulness`). Redeploy after changing.

| Backend | `ASSISTANT_ID` |
|---------|----------------|
| `langgraph dev` (local) | `"agent_with_helpfulness"` (graph name) |
| `langgraph up` (EC2) | UUID from `assistants/search` |

### 4. Smoke test

1. Open your **Aliased** Vercel URL.
2. Ask a cat-health question (not just “hi” — see [Known UI behavior](#known-ui-behavior)).
3. Confirm streaming reply and tool use.
4. Check [LangSmith](https://smith.langchain.com) for traces.

Verify the proxy from your machine:

```bash
curl https://<your-aliased-app>.vercel.app/api/ok
```

### Local vs production env

| | Local `frontend/.env.local` | Vercel |
|--|---------------------------|--------|
| `LANGGRAPH_API_URL` | `http://localhost:<local-agent-port>` | `http://<elastic-ip>:<agent-port>` |
| `NEXT_PUBLIC_API_URL` | `http://localhost:3000/api` | `https://<aliased-app>.vercel.app/api` |

Local agent port depends on how you run LangGraph (`langgraph dev` vs `langgraph up`).

---

## Known UI behavior

The `agent_with_helpfulness` graph appends internal messages like `HELPFULNESS:Y`, `HELPFULNESS:N`, or `HELPFULNESS:END` during its evaluation loop. The chat UI renders all AI messages, so you may see these alongside normal replies.

Vague greetings often get `HELPFULNESS:N` and a retry. A substantive cat-health question should show tool use and eventually pass the loop.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Vercel build: `API URL is required` | `LANGGRAPH_API_URL` not set on Vercel | Add it in project settings, redeploy |
| `Failed to construct 'URL': Invalid URL` | `NEXT_PUBLIC_API_URL` missing, empty, or relative `/api` | Set full `https://…/api` URL, redeploy |
| `Failed to fetch` / can’t reach LangGraph | Wrong `NEXT_PUBLIC_API_URL` (old deployment hostname, `localhost`, or EC2 IP in the browser) | Use **Aliased** `https://…vercel.app/api`, redeploy |
| Vercel `/api/ok` works but browser chat fails | Stale client bundle | Hard refresh; confirm env var + `--prod` redeploy |
| Agent OK on EC2, fails from Vercel | SG blocks agent API port from the internet | Add inbound rule for the port in `cat-health-agent-agent-api` SG |
| Chat errors / empty replies | Empty or stale EC2 `.env` | Fill keys, `sudo systemctl restart cat-health-agent` |
| Wrong or missing assistant | Graph name in `page.tsx` instead of UUID | Run `assistants/search` on EC2, update `ASSISTANT_ID`, redeploy |
| Service stuck on `Building…` | Normal on first boot | Wait; watch `journalctl -u cat-health-agent -f` |

**Debug tips**

- Browser **Network** tab: requests should go to `https://<your-app>.vercel.app/api/…`, not EC2 or `localhost`
- Vercel **Deployments → Logs / Functions** for proxy errors
- EC2: `journalctl -u cat-health-agent -f` and `curl http://localhost:<agent-port>/ok`

---

## Teardown

```bash
cd provision
terraform destroy
```

Remove any temporary security group rule you added for the agent API port.

---

## Future hardening (optional)

- Reverse proxy on **443 → localhost:<agent-port>**; drop public exposure of the app port
- Codify the extra SG rule in `provision/sg.tf` only if you accept the security tradeoff
- Vercel deployment protection or a simple auth gate on the frontend
- Commit `uv.lock` for reproducible AMI builds
