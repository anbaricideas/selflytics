# Terraform module for deploying to GCP Cloud Run

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Cloud Run service
resource "google_cloud_run_v2_service" "app" {
  name     = "${var.service_name}-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    # Auto-scaling configuration
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    # Service account (passed from calling module to avoid circular dependency)
    service_account = var.service_account_email

    # Container configuration
    containers {
      image = var.image

      # Resource limits
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        cpu_idle = var.cpu_throttling
      }

      # Port configuration
      ports {
        container_port = var.container_port
      }

      # Environment variables (non-sensitive)
      # Note: PORT env var not explicitly set - Cloud Run automatically sets PORT=8080
      # which matches our Dockerfile EXPOSE directive (backend/Dockerfile:56)
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "DEBUG"
        value = var.debug ? "true" : "false"
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      # Additional environment variables
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      # Secrets from Secret Manager
      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret_name
              version = env.value.version
            }
          }
        }
      }

      # Startup probe (health check)
      startup_probe {
        http_get {
          path = var.health_check_path
          port = var.container_port
        }
        initial_delay_seconds = 10
        timeout_seconds       = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      # Liveness probe
      liveness_probe {
        http_get {
          path = var.health_check_path
          port = var.container_port
        }
        initial_delay_seconds = 30
        timeout_seconds       = 5
        period_seconds        = 30
        failure_threshold     = 3
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Allow unauthenticated access (for public API)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = google_cloud_run_v2_service.app.project
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Grant WIF service account invoker access for CI/CD validation
resource "google_cloud_run_v2_service_iam_member" "wif_invoker" {
  count    = var.grant_wif_invoker_access ? 1 : 0
  project  = google_cloud_run_v2_service.app.project
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.wif_service_account_email}"
}
