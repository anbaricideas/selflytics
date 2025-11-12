# Input variables for Cloud Run module

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run deployment"
  type        = string
  default     = "australia-southeast1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "service_name" {
  description = "Base name for the Cloud Run service"
  type        = string
  default     = "selflytics-webapp"
}

variable "image" {
  description = "Docker image to deploy (e.g., gcr.io/project/image:tag)"
  type        = string
}

variable "service_account_email" {
  description = "Email of the service account to use for Cloud Run (passed from calling module)"
  type        = string
}

# Scaling configuration
variable "min_instances" {
  description = "Minimum number of instances (0 for scale to zero)"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

# Resource limits
variable "cpu_limit" {
  description = "CPU limit (e.g., '1' for 1 vCPU)"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory limit (e.g., '512Mi', '1Gi')"
  type        = string
  default     = "512Mi"
}

variable "cpu_throttling" {
  description = "CPU throttling when idle"
  type        = bool
  default     = true
}

# Container configuration
variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8080
}

variable "health_check_path" {
  description = "Path for health check endpoint"
  type        = string
  default     = "/health"
}

# Environment variables
variable "debug" {
  description = "Enable debug mode"
  type        = bool
  default     = false
}

variable "env_vars" {
  description = "Additional environment variables (non-sensitive)"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets from Secret Manager to inject as environment variables"
  type = map(object({
    secret_name = string
    version     = string
  }))
  default = {}
}

# Access control
variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service"
  type        = bool
  default     = true
}

# CI/CD access control
variable "grant_wif_invoker_access" {
  description = "Grant WIF service account invoker access for CI/CD validation"
  type        = bool
  default     = false
}

variable "wif_service_account_email" {
  description = "WIF service account email for CI/CD (e.g., github-actions-sa@project.iam.gserviceaccount.com)"
  type        = string
  default     = ""
}
