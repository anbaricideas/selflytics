# Terraform Deployment Steps for Phase 1

**Project**: Selflytics
**Environment**: Dev
**GCP Project**: selflytics-infra (174666459313)
**Region**: australia-southeast1

---

## Prerequisites ✅

- [x] GCP project created: `selflytics-infra`
- [x] Billing enabled
- [x] GCS bucket for Terraform state: `gs://selflytics-infra-terraform-state/`
- [x] gcloud configuration created: `selflytics`
- [x] direnv configured (`.envrc` sets `CLOUDSDK_ACTIVE_CONFIG_NAME=selflytics`)

---

## Manual Steps Required

### 1. Authenticate with GCP 🔐

**Current Issue**: OAuth authentication expired (`invalid_rapt` error)

**Commands to run**:
```bash
# Ensure you're in the selflytics project directory (direnv will activate config)
cd /Users/bryn/repos/selflytics

# Re-authenticate for gcloud CLI
gcloud auth login

# Re-authenticate for Application Default Credentials (used by Terraform)
gcloud auth application-default login

# Verify authentication
gcloud auth list
gcloud config get-value project  # Should show: selflytics-infra
```

### 2. Initialize Terraform Backend

Once authenticated, run:
```bash
terraform -chdir=infra/environments/dev init \
  -backend-config="bucket=selflytics-infra-terraform-state"
```

**Expected output**:
- Terraform modules initialized
- Backend configured successfully
- Lock file created

### 3. Review Terraform Plan

```bash
terraform -chdir=infra/environments/dev plan
```

**What to review**:
- Cloud Run service configuration
- Firestore database setup
- Secret Manager secrets (placeholders - values added later)
- IAM permissions
- No unexpected resource deletions

### 4. Apply Terraform Configuration

```bash
terraform -chdir=infra/environments/dev apply
```

**Resources to be created**:
- Cloud Run service: `selflytics-dev`
- Firestore database (if not exists)
- Secret Manager secrets (empty placeholders):
  - `jwt-secret-key`
  - `openai-api-key`
  - `garmin-client-secret` (Phase 2)
- IAM service accounts and permissions

### 5. Populate Secrets in GCP Secret Manager

After Terraform apply, manually add secret values:

#### 5a. Generate JWT Secret

```bash
# Generate a secure random key (32 bytes, base64 encoded)
JWT_SECRET=$(openssl rand -base64 32)
echo "Generated JWT_SECRET: $JWT_SECRET"

# Add to Secret Manager
echo -n "$JWT_SECRET" | gcloud secrets versions add jwt-secret-key \
  --project=selflytics-infra \
  --data-file=-
```

#### 5b. Add OpenAI API Key

```bash
# Get your OpenAI API key from: https://platform.openai.com/api-keys
# Then add to Secret Manager:
echo -n "sk-proj-YOUR_OPENAI_KEY_HERE" | gcloud secrets versions add openai-api-key \
  --project=selflytics-infra \
  --data-file=-
```

#### 5c. Verify Secrets

```bash
gcloud secrets list --project=selflytics-infra

# Should show:
# - jwt-secret-key (1 version)
# - openai-api-key (1 version)
# - garmin-client-secret (placeholder, will be used in Phase 2)
```

### 6. Update Cloud Run Service with Secrets

The Terraform configuration should automatically mount secrets as environment variables. Verify:

```bash
gcloud run services describe selflytics-dev \
  --region=australia-southeast1 \
  --project=selflytics-infra \
  --format="value(spec.template.spec.containers[0].env)"
```

### 7. Validate Deployment

```bash
# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe selflytics-dev \
  --region=australia-southeast1 \
  --project=selflytics-infra \
  --format="value(status.url)")

echo "Service URL: $SERVICE_URL"

# Test health endpoint
curl -s "$SERVICE_URL/health" | python3 -m json.tool

# Expected output:
# {
#     "status": "healthy",
#     "service": "selflytics"
# }
```

### 8. Test Authentication Flow

```bash
# Test registration (should work with real Firestore)
curl -X POST "$SERVICE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","display_name":"Test User"}' \
  | python3 -m json.tool

# Test login
curl -X POST "$SERVICE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123" \
  | python3 -m json.tool

# Should return:
# {
#     "access_token": "eyJ...",
#     "token_type": "bearer"
# }
```

---

## Troubleshooting

### Authentication Errors

If you see `invalid_rapt` or OAuth errors:
```bash
gcloud auth application-default revoke
gcloud auth application-default login
```

### Terraform State Lock

If Terraform is locked:
```bash
terraform -chdir=infra/environments/dev force-unlock <LOCK_ID>
```

### Secret Access Denied

Ensure the Cloud Run service account has access:
```bash
gcloud secrets add-iam-policy-binding jwt-secret-key \
  --member="serviceAccount:github-actions@selflytics-infra.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=selflytics-infra
```

---

## Success Criteria

- [ ] Terraform apply completes successfully
- [ ] Cloud Run service is deployed and accessible
- [ ] Health endpoint returns 200 OK
- [ ] Firestore database is created
- [ ] Secrets are populated in Secret Manager
- [ ] Login page renders correctly at service URL
- [ ] User registration works (creates document in Firestore)
- [ ] User login works (returns JWT token)
- [ ] Protected endpoints require authentication

---

## Next Steps After Deployment

1. Mark Phase 1 complete in `ROADMAP.md`
2. Update Phase 1 plan with deployment results
3. Submit PR: `feat/phase-1-infrastructure` → `main`
4. Begin Phase 2: Garmin Integration

---

*Created: 2025-11-12*
*Status: Awaiting manual authentication*
