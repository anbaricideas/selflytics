# Outputs for development environment

output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = module.cloud_run.service_url
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = module.cloud_run.service_name
}

output "service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = module.cloud_run.service_account_email
}

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP region"
  value       = var.region
}

output "jwt_secret_id" {
  description = "ID of the JWT secret in Secret Manager"
  value       = module.secrets.jwt_secret_id
}

output "openai_secret_id" {
  description = "ID of the OpenAI secret in Secret Manager"
  value       = module.secrets.openai_secret_id
}
