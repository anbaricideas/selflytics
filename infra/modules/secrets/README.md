# Secrets Module

Terraform module for managing application secrets in GCP Secret Manager.

## Features

- Creates secrets in GCP Secret Manager
- Configures IAM permissions for Cloud Run service account access
- Supports optional secrets (e.g., OpenAI API key for local dev)
- Environment-specific secret naming

## Usage

```hcl
module "secrets" {
  source = "../../modules/secrets"

  project_id            = var.project_id
  environment           = var.environment
  service_account_email = google_service_account.cloud_run_sa.email
  create_openai_secret  = true
}
```

## Secrets Created

1. **JWT Secret** (`{environment}-jwt-secret`)
   - Required for authentication
   - Must be manually populated after creation

2. **OpenAI API Key** (`{environment}-openai-api-key`) - Optional
   - Only created if `create_openai_secret = true`
   - Must be manually populated after creation

## Manual Secret Population

After Terraform creates the secrets, populate them manually:

```bash
# JWT Secret
echo -n "your-secure-jwt-secret" | gcloud secrets versions add dev-jwt-secret --data-file=-

# OpenAI API Key
echo -n "sk-..." | gcloud secrets versions add dev-openai-api-key --data-file=-
```

## Inputs

| Name | Description | Type | Required | Default |
|------|-------------|------|----------|---------|
| project_id | GCP project ID | string | yes | - |
| environment | Environment name | string | yes | - |
| service_account_email | Service account email | string | yes | - |
| create_openai_secret | Create OpenAI secret | bool | no | true |

## Outputs

| Name | Description |
|------|-------------|
| jwt_secret_id | Secret Manager secret ID for JWT |
| jwt_secret_name | Full resource name of JWT secret |
| openai_secret_id | Secret Manager secret ID for OpenAI (if created) |
| openai_secret_name | Full resource name of OpenAI secret (if created) |
