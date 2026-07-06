# Cat Health Agent — Packer AMI

Builds **Cat Health Agent v1.0.0**: Ubuntu 24.04 LTS, Docker, pre-pulled LangGraph images, project at `~/agent`, and a `cat-health-agent` systemd unit (installed, not enabled).

Full deployment flow: [`DEPLOY.md`](../DEPLOY.md)

## Prerequisites

- [Packer](https://developer.hashicorp.com/packer/install) 1.14+
- AWS credentials with permission to launch/build AMIs
- EC2 key pair in your target region (default stack uses `us-east-1`)

## Build

```bash
cd ami
packer init cat-health-agent-v1.0.0.pkr.hcl
packer build cat-health-agent-v1.0.0.pkr.hcl
```

Note the output AMI ID and set `ami_id` in `provision/vars.tf`.

## What `install.sh` does

1. Docker Engine + Compose plugin
2. Pre-pulls LangGraph stack images (`langchain/langgraph-api`, Redis, pgvector)
3. Installs `uv` for the `ubuntu` user
4. Runs `uv sync` in `~/agent` (after Packer copies the project)
5. Writes `/etc/systemd/system/cat-health-agent.service` — **`langgraph up`** with port defined in the script
6. Does **not** enable the service or fill secrets

## On the running instance

After `terraform apply`:

1. SSH in (see `terraform output ssh_command`)
2. Edit `~/agent/.env` from `.env.example` — API keys, no `export` prefix
3. `chmod 600 ~/agent/.env`
4. `sudo systemctl enable --now cat-health-agent`
5. Confirm health via the port shown in `journalctl` or the systemd unit

## Files

| File | Role |
|------|------|
| `cat-health-agent-v1.0.0.pkr.hcl` | Packer template (Ubuntu noble, tags, file provisioners) |
| `install.sh` | Host bootstrap run during AMI build |

## Tags (aligned with Terraform)

- `Project` = Cat Health Agent
- `ManagedBy` = packer
- `Version` = v1.0.0
