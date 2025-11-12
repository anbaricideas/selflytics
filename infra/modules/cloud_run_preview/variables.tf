# Input variables for Cloud Run Preview module
# Simplified version of cloud_run module for preview deployments

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run deployment"
  type        = string
  default     = "australia-southeast1"
}

variable "feature_name" {
  description = "Sanitized feature name (from branch name, e.g., 'telemetry')"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.feature_name)) && length(var.feature_name) <= 40
    error_message = "Feature name must be lowercase alphanumeric with hyphens, start/end with alphanumeric, max 40 chars."
  }
}

variable "image" {
  description = "Docker image to deploy (e.g., region-docker.pkg.dev/project/repo/image:tag)"
  type        = string
}

variable "service_account_email" {
  description = "Email of the service account to use for Cloud Run (optional, uses default if not provided)"
  type        = string
  default     = null
}

variable "secrets" {
  description = "Map of environment variable names to Secret Manager secret references"
  type = map(object({
    secret_name = string
    version     = string
  }))
  default = {}
}
