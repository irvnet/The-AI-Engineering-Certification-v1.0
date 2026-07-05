locals {
  agent_api_host = var.agent_api_domain != "" ? var.agent_api_domain : aws_eip.agent_api.public_ip
}

output "ami_id" {
  description = "AMI used for the agent API host (Ubuntu 24.04 LTS or Packer override)."
  value       = local.agent_ami_id
}

output "ami_name" {
  description = "Resolved AMI name when using the Ubuntu 24.04 LTS lookup (null if ami_id was overridden)."
  value       = var.ami_id != "" ? null : data.aws_ami.ubuntu_2404_lts.name
}

output "project" {
  description = "Project identity for this stack."
  value       = local.project_label
}

output "vpc_id" {
  description = "Isolated VPC hosting Cat Health Agent infrastructure."
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block."
  value       = module.vpc.vpc_cidr_block
}

output "agent_api_public_ip" {
  description = "Elastic IP for the agent API host."
  value       = aws_eip.agent_api.public_ip
}

output "agent_api_url" {
  description = "Set LANGGRAPH_API_URL on Vercel to this base URL once TLS is configured on the host."
  value       = "https://${local.agent_api_host}"
}

output "vercel_env_hint" {
  description = "Suggested Vercel server-side environment variables after deploy."
  value = {
    LANGGRAPH_API_URL     = "https://${local.agent_api_host}"
    NEXT_PUBLIC_API_URL   = "https://<your-vercel-app>.vercel.app/api"
    LANGSMITH_API_KEY     = "<optional-if-using-langsmith-auth>"
  }
}

output "ssh_command" {
  description = "SSH into the agent API host for bootstrap (langgraph dev, nginx, env files)."
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ubuntu@${aws_eip.agent_api.public_ip}  # adjust key path if needed"
}

output "availability_zone" {
  description = "AZ where the agent API host was placed."
  value       = local.availability_zone
}

output "instance_id" {
  description = "EC2 instance ID for the agent API host."
  value       = aws_instance.agent_api.id
}
