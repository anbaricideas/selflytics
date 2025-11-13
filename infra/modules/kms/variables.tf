variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "region" {
  description = "GCP region for KMS resources"
  type        = string
}

variable "cloud_run_service_account" {
  description = "Email of the Cloud Run service account that needs encrypt/decrypt permissions"
  type        = string
}
