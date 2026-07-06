# Cat Health Agent — Terraform

Isolated VPC + single EC2 + Elastic IP for the self-hosted LangGraph agent API.

**Full deployment guide:** [`DEPLOY.md`](../DEPLOY.md)  
**AMI build:** [`ami/README.md`](../ami/README.md)

## What this stack creates

| Resource | Purpose |
|----------|---------|
| VPC `10.42.0.0/26` | Isolated network |
| Public subnet `10.42.0.0/28` | Agent host |
| EC2 + Elastic IP | Runs `langgraph up` via systemd |
| Security group | **443 / 80 / 22** inbound by default |

The agent API listens on a **separate port** (configured in the AMI/systemd unit). Terraform does not open that port by default — see [`DEPLOY.md` — Network access](../DEPLOY.md#network-access).

## Quick start

```bash
cd provision
terraform init
terraform apply
```

Defaults (region, AMI, SSH key, VPC CIDR): see `vars.tf` and `terraform.tfvars.example`.

Optional overrides:

```bash
cp terraform.tfvars.example terraform.tfvars
# e.g. allowed_ssh_cidr = "203.0.113.10/32"
```

## Outputs

```bash
terraform output agent_api_public_ip   # Elastic IP — use in LANGGRAPH_API_URL (with agent port)
terraform output ssh_command           # SSH bootstrap
terraform output ami_id
terraform output instance_id
```

| Output | Use |
|--------|-----|
| `agent_api_public_ip` | EC2 public address |
| `agent_api_url` | **Not** for Vercel as-is — HTTPS without app port; for future TLS front-end |
| `vercel_env_hint` | Starting point only — fix scheme/port per `DEPLOY.md` |
| `ssh_command` | Fill `~/agent/.env`, start service |

After apply, continue at **DEPLOY.md → SSH bootstrap**.

## Tags

- `Project` = Cat Health Agent
- `ManagedBy` = terraform
- `Environment` = dev (default)

## Teardown

```bash
terraform destroy
```

Remove any manual security group rules added for the agent API port.
