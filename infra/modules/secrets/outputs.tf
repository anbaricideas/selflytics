# Output values from secrets module

output "jwt_secret_id" {
  description = "ID of the JWT secret in Secret Manager"
  value       = google_secret_manager_secret.jwt_secret.secret_id
}

output "jwt_secret_name" {
  description = "Full resource name of the JWT secret"
  value       = google_secret_manager_secret.jwt_secret.name
}

output "openai_secret_id" {
  description = "ID of the OpenAI API key secret in Secret Manager (if created)"
  value       = var.create_openai_secret ? google_secret_manager_secret.openai_api_key[0].secret_id : null
}

output "openai_secret_name" {
  description = "Full resource name of the OpenAI secret (if created)"
  value       = var.create_openai_secret ? google_secret_manager_secret.openai_api_key[0].name : null
}
