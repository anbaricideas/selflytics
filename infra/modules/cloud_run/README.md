# Cloud Run Module

Terraform module for deploying containerized applications to GCP Cloud Run.

## Features

- Creates Cloud Run v2 service
- Configures auto-scaling (scale to zero by default)
- Sets up service account with minimal permissions
- Injects environment variables and secrets
- Configures health checks (startup and liveness probes)
- Supports resource limits (CPU, memory)
- Optional public access configuration

## Usage

```hcl
module "cloud_run" {
  source = "../../modules/cloud_run"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  image       = "gcr.io/my-project/clinicraft-webapp:latest"

  # Scaling
  min_instances = 0  # Scale to zero
  max_instances = 10

  # Resources
  cpu_limit    = "1"
  memory_limit = "512Mi"

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
    BASE_URL = "https://clinicraft.anbaricideas.com"
  }
}
```

## Default Configuration

- **Region:** australia-southeast1 (Sydney)
- **Min Instances:** 0 (scale to zero)
- **Max Instances:** 10
- **CPU:** 1 vCPU
- **Memory:** 512Mi
- **Container Port:** 8080
- **Health Check:** /health
- **Public Access:** Enabled

## Inputs

| Name | Description | Type | Required | Default |
|------|-------------|------|----------|---------|
| project_id | GCP project ID | string | yes | - |
| region | GCP region | string | no | australia-southeast1 |
| environment | Environment name | string | yes | - |
| service_name | Service name | string | no | clinicraft-webapp |
| image | Docker image | string | yes | - |
| min_instances | Min instances | number | no | 0 |
| max_instances | Max instances | number | no | 10 |
| cpu_limit | CPU limit | string | no | "1" |
| memory_limit | Memory limit | string | no | "512Mi" |
| container_port | Container port | number | no | 8080 |
| health_check_path | Health check path | string | no | /health |
| debug | Debug mode | bool | no | false |
| env_vars | Environment variables | map(string) | no | {} |
| secrets | Secret Manager secrets | map(object) | no | {} |
| allow_unauthenticated | Public access | bool | no | true |

## Outputs

| Name | Description |
|------|-------------|
| service_name | Cloud Run service name |
| service_url | Public URL of the service |
| service_account_email | Service account email |
| service_id | Full resource ID |
| latest_revision | Latest revision name |

## Health Checks

The module configures two types of probes:

1. **Startup Probe**: Checks if the application has started
   - Initial delay: 10s
   - Period: 10s
   - Failure threshold: 3

2. **Liveness Probe**: Checks if the application is healthy
   - Initial delay: 30s
   - Period: 30s
   - Failure threshold: 3

Both probes use HTTP GET requests to the configured health check path.
