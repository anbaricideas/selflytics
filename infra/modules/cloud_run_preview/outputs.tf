# Output values from Cloud Run Preview module

output "service_name" {
  description = "Name of the preview Cloud Run service"
  value       = google_cloud_run_v2_service.preview.name
}

output "service_url" {
  description = "URL of the deployed preview Cloud Run service"
  value       = google_cloud_run_v2_service.preview.uri
}

output "service_id" {
  description = "Full resource ID of the preview Cloud Run service"
  value       = google_cloud_run_v2_service.preview.id
}

output "latest_revision" {
  description = "Name of the latest revision"
  value       = google_cloud_run_v2_service.preview.latest_ready_revision
}

output "feature_name" {
  description = "Feature name used in service name"
  value       = var.feature_name
}
