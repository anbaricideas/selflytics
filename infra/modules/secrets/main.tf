# Terraform module for managing secrets in GCP Secret Manager

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# JWT Secret for authentication
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "${var.environment}-jwt-secret"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# OpenAI API Key (optional - only create if provided)
resource "google_secret_manager_secret" "openai_api_key" {
  count     = var.create_openai_secret ? 1 : 0
  secret_id = "${var.environment}-openai-api-key"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# IAM binding to allow Cloud Run service account to access JWT secret
resource "google_secret_manager_secret_iam_member" "jwt_secret_access" {
  secret_id = google_secret_manager_secret.jwt_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

# IAM binding to allow Cloud Run service account to access OpenAI secret
resource "google_secret_manager_secret_iam_member" "openai_secret_access" {
  count     = var.create_openai_secret ? 1 : 0
  secret_id = google_secret_manager_secret.openai_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}
