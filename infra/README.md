# Selflytics Infrastructure

Terraform modules and environments for deploying Selflytics to GCP.

## Structure

```
infra/
├── modules/           # Reusable Terraform modules
│   ├── cloud_run/     # Cloud Run service
│   ├── firestore/     # Firestore database
│   ├── secrets/       # Secret Manager
│   └── storage/       # GCS buckets
└── environments/      # Environment configurations
    └── dev/           # Development environment
```

## Usage

See project root README.md for deployment instructions.
