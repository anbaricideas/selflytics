# Input variables for secrets module

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "service_account_email" {
  description = "Email of the service account that needs access to secrets"
  type        = string
}

variable "create_openai_secret" {
  description = "Whether to create OpenAI API key secret (set to false for local dev without AI)"
  type        = bool
  default     = true
}
