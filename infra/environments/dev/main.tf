# Development environment Terraform configuration for Selflytics

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Backend configuration for storing Terraform state in GCS
  # Run: terraform init -backend-config="bucket=selflytics-infra-terraform-state"
  backend "gcs" {
    prefix = "env/dev"
  }
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable Firestore API
resource "google_project_service" "firestore" {
  project = var.project_id
  service = "firestore.googleapis.com"

  disable_on_destroy = false
}

# Create Firestore database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region # australia-southeast1
  type        = "FIRESTORE_NATIVE"

  # Recommended settings
  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"

  depends_on = [google_project_service.firestore]
}

# Service account for Cloud Run (created independently to break circular dependency)
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.environment}-cloud-run-sa"
  display_name = "Cloud Run Service Account (${var.environment})"
  project      = var.project_id
}

# Grant Cloud Run service account permission to write logs to Cloud Logging
resource "google_project_iam_member" "cloud_run_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Run service account access to Firestore
resource "google_project_iam_member" "cloud_run_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"

  depends_on = [google_firestore_database.database]
}

# Grant default Compute Engine service account access to Firestore
# (used by preview deployments until they're migrated to use dedicated SAs)
resource "google_project_iam_member" "compute_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"

  depends_on = [google_firestore_database.database]
}

# Grant default Compute Engine service account access to Cloud Logging
# (used by preview deployments for telemetry)
resource "google_project_iam_member" "compute_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Grant default Compute Engine service account access to Secret Manager
# (used by preview deployments to access JWT_SECRET and OPENAI_API_KEY)
resource "google_project_iam_member" "compute_secretmanager" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"

  depends_on = [module.secrets]
}

# Data source to get project number
data "google_project" "project" {
  project_id = var.project_id
}

# Secrets module (depends on service account)
module "secrets" {
  source = "../../modules/secrets"

  project_id            = var.project_id
  environment           = var.environment
  service_account_email = google_service_account.cloud_run_sa.email
  create_openai_secret  = true
}

# Cloud Run service (depends on secrets)
module "cloud_run" {
  source = "../../modules/cloud_run"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  image       = var.image

  # Pass the pre-created service account
  service_account_email = google_service_account.cloud_run_sa.email

  # Development scaling (scale to zero for cost savings)
  min_instances = 0
  max_instances = 5

  # Development resources (minimal for cost)
  cpu_limit    = "1"
  memory_limit = "512Mi"

  # Development configuration
  debug = true

  # Secrets from Secret Manager
  secrets = {
    JWT_SECRET = {
      secret_name = module.secrets.jwt_secret_name
      version     = "latest"
    }
    OPENAI_API_KEY = {
      secret_name = module.secrets.openai_secret_name
      version     = "latest"
    }
  }

  # Additional environment variables
  env_vars = {
    BASE_URL       = var.base_url
    TELEMETRY      = "cloudlogging"
    GCP_PROJECT_ID = var.project_id
  }

  # IAM-based access only (org policy prevents public access)
  allow_unauthenticated = false

  # Grant WIF service account invoker access for CI/CD validation
  # TODO: Enable this after creating github-actions-sa service account for CI/CD
  grant_wif_invoker_access  = false
  wif_service_account_email = "github-actions-sa@${var.project_id}.iam.gserviceaccount.com"

  depends_on = [module.secrets]
}
