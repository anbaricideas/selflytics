# Output values from Cloud Run module

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.app.name
}

output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.app.uri
}

output "service_account_email" {
  description = "Email of the Cloud Run service account (passed through from input)"
  value       = var.service_account_email
}

output "service_id" {
  description = "Full resource ID of the Cloud Run service"
  value       = google_cloud_run_v2_service.app.id
}

output "latest_revision" {
  description = "Name of the latest revision"
  value       = google_cloud_run_v2_service.app.latest_ready_revision
}
