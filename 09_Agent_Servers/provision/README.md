# Cat Health Agent — Terraform

Isolated VPC + EC2 + Elastic IP for the LangGraph agent API.

**Full deployment guide:** [DEPLOY.md](../DEPLOY.md)

## Quick start

```bash
cd provision
terraform init
terraform apply
```

Defaults (region, AMI, SSH key, VPC CIDR): see `vars.tf` and `terraform.tfvars.example`.

## Tags

- `Project` = Cat Health Agent
- `ManagedBy` = terraform
- `Environment` = dev
