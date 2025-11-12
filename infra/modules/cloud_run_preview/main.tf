# Terraform module for preview deployments to GCP Cloud Run
# Simplified, fixed configuration for feature branch previews

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Preview Cloud Run service
resource "google_cloud_run_v2_service" "preview" {
  name     = "clinicraft-webapp-preview-${var.feature_name}"
  location = var.region
  project  = var.project_id

  template {
    # Auto-scaling: scale to zero for cost savings, max 1 instance for preview testing
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    # Use provided service account or default Cloud Run SA
    service_account = var.service_account_email

    # Container configuration
    containers {
      image = var.image

      # Resource limits: same as dev environment
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      # Port configuration
      ports {
        container_port = 8080
      }

      # Environment variables
      env {
        name  = "ENVIRONMENT"
        value = "preview-${var.feature_name}"
      }

      env {
        name  = "DEBUG"
        value = "true"
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
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
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 10
        timeout_seconds       = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      # Liveness probe
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
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
    environment = "preview"
    feature     = var.feature_name
    managed_by  = "terraform"
  }
}

# No public access for preview environments
# Users access via gcloud proxy (./infra/scripts/proxy.sh preview-<feature>)
# This complies with organization policy requiring authenticated access
