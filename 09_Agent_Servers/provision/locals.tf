locals {
  project_name  = "cat-health-agent"
  project_label = "Cat Health Agent"

  availability_zone = var.availability_zone != "" ? var.availability_zone : data.aws_availability_zones.available.names[0]

  # Empty ami_id → latest official Ubuntu 24.04 LTS; set ami_id after Packer bake
  agent_ami_id = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu_2404_lts.id

  common_tags = {
    Project     = local.project_label
    ManagedBy   = "terraform"
    Environment = var.environment
  }
}
