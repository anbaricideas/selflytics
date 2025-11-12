# Variables for development environment

variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "selflytics-infra"
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "australia-southeast1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "image" {
  description = "Docker image to deploy"
  type        = string
  # Default to latest tag, but should be overridden in CI/CD
  default = "australia-southeast1-docker.pkg.dev/selflytics-infra/selflytics/backend:latest"
}

variable "base_url" {
  description = "Base URL for the application"
  type        = string
  default     = "https://selflytics-dev.run.app"
}
