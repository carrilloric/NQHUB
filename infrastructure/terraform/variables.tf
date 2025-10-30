# NQHUB Infrastructure Variables

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "nqhub"
}

# Cloud provider variables (uncomment based on provider)

# GCP
# variable "project_id" {
#   description = "GCP Project ID"
#   type        = string
# }

# variable "region" {
#   description = "GCP Region"
#   type        = string
#   default     = "us-central1"
# }

# variable "zone" {
#   description = "GCP Zone"
#   type        = string
#   default     = "us-central1-a"
# }

# AWS
# variable "region" {
#   description = "AWS Region"
#   type        = string
#   default     = "us-east-1"
# }

# VM Configuration
variable "machine_type" {
  description = "VM machine type"
  type        = string
  default     = "n1-standard-4"  # GCP example
}

variable "gpu_type" {
  description = "GPU type"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 100
}

# Network Configuration
variable "allowed_ips" {
  description = "List of allowed IP addresses"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Change in production
}
