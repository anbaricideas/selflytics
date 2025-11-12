#!/usr/bin/env bash
#
# validate-gcp-setup.sh - Validate GCP Infrastructure Setup for Selflytics
#
# This script validates that all required GCP service accounts, IAM permissions,
# Workload Identity Federation, and infrastructure components are properly configured.
#
# Usage:
#   ./scripts/validate-gcp-setup.sh [--project PROJECT_ID] [--verbose]
#
# Exit codes:
#   0 - All validations passed
#   1 - One or more validations failed
#   2 - Configuration error
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-selflytics-infra}"
PROJECT_NUMBER="174666459313"
REGION="australia-southeast1"
VERBOSE=false

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      head -n 20 "$0" | grep "^#" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage information"
      exit 2
      ;;
  esac
done

# Helper functions
log_info() {
  echo -e "${BLUE}ℹ${NC} $*"
}

log_success() {
  echo -e "${GREEN}✓${NC} $*"
  ((++PASSED))
}

log_error() {
  echo -e "${RED}✗${NC} $*"
  ((++FAILED))
}

log_warning() {
  echo -e "${YELLOW}⚠${NC} $*"
  ((++WARNINGS))
}

log_section() {
  echo ""
  echo -e "${BLUE}═══ $* ═══${NC}"
}

check_command() {
  if ! command -v "$1" &> /dev/null; then
    log_error "Required command '$1' not found. Please install it first."
    exit 2
  fi
}

# Check prerequisites
log_section "Prerequisites"
check_command gcloud
check_command jq
log_success "All required commands are available"

# Verify project access
log_section "Project Access"
log_info "Checking access to project: $PROJECT_ID"

if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
  log_error "Cannot access project '$PROJECT_ID'. Check authentication and permissions."
  exit 2
fi
log_success "Project '$PROJECT_ID' is accessible"

# Get current project configuration
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [[ "$CURRENT_PROJECT" != "$PROJECT_ID" ]]; then
  log_warning "Current gcloud project is '$CURRENT_PROJECT', expected '$PROJECT_ID'"
  log_info "Run: gcloud config set project $PROJECT_ID"
fi

#
# Service Accounts Validation
#
log_section "Service Accounts"

# Define expected service accounts
declare -A SERVICE_ACCOUNTS=(
  ["dev-cloud-run-sa"]="Cloud Run service account for dev environment"
  ["github-actions-sa"]="GitHub Actions CI/CD service account"
)

for sa_name in "${!SERVICE_ACCOUNTS[@]}"; do
  sa_email="${sa_name}@${PROJECT_ID}.iam.gserviceaccount.com"
  description="${SERVICE_ACCOUNTS[$sa_name]}"

  if gcloud iam service-accounts describe "$sa_email" --project="$PROJECT_ID" &> /dev/null; then
    log_success "Service account exists: $sa_email"
    if [[ "$VERBOSE" == "true" ]]; then
      log_info "  Purpose: $description"
    fi
  else
    log_error "Service account missing: $sa_email ($description)"
  fi
done

#
# IAM Permissions Validation
#
log_section "IAM Permissions"

# Define expected IAM bindings
# Format: "member|role"
declare -a IAM_BINDINGS=(
  # Cloud Run service account permissions
  "serviceAccount:dev-cloud-run-sa@${PROJECT_ID}.iam.gserviceaccount.com|roles/logging.logWriter"
  "serviceAccount:dev-cloud-run-sa@${PROJECT_ID}.iam.gserviceaccount.com|roles/datastore.user"

  # GitHub Actions service account permissions
  "serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com|roles/run.admin"
  "serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com|roles/iam.serviceAccountUser"
  "serviceAccount:github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com|roles/artifactregistry.writer"

  # Compute service account permissions (for preview deployments)
  "serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com|roles/datastore.user"
  "serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com|roles/logging.logWriter"
  "serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com|roles/secretmanager.secretAccessor"
)

# Get current IAM policy
IAM_POLICY=$(gcloud projects get-iam-policy "$PROJECT_ID" --format=json 2>/dev/null)

for binding in "${IAM_BINDINGS[@]}"; do
  IFS='|' read -r member role <<< "$binding"

  if echo "$IAM_POLICY" | jq -e ".bindings[] | select(.role==\"$role\") | .members[] | select(. == \"$member\")" &> /dev/null; then
    if [[ "$VERBOSE" == "true" ]]; then
      log_success "IAM binding: $member → $role"
    fi
  else
    log_error "Missing IAM binding: $member → $role"
  fi
done

if [[ "$VERBOSE" != "true" && "$FAILED" == "0" ]]; then
  log_success "All IAM permissions configured correctly"
fi

#
# Workload Identity Federation Validation
#
log_section "Workload Identity Federation"

WIF_POOL="github-pool"
WIF_PROVIDER="github-provider"
WIF_LOCATION="global"

# Check WIF pool
if gcloud iam workload-identity-pools describe "$WIF_POOL" --location="$WIF_LOCATION" --project="$PROJECT_ID" &> /dev/null; then
  log_success "WIF pool exists: $WIF_POOL"
else
  log_error "WIF pool missing: $WIF_POOL"
fi

# Check WIF provider
if gcloud iam workload-identity-pools providers describe "$WIF_PROVIDER" \
    --workload-identity-pool="$WIF_POOL" \
    --location="$WIF_LOCATION" \
    --project="$PROJECT_ID" &> /dev/null; then
  log_success "WIF provider exists: $WIF_PROVIDER"

  if [[ "$VERBOSE" == "true" ]]; then
    PROVIDER_INFO=$(gcloud iam workload-identity-pools providers describe "$WIF_PROVIDER" \
      --workload-identity-pool="$WIF_POOL" \
      --location="$WIF_LOCATION" \
      --project="$PROJECT_ID" \
      --format=json)

    ISSUER=$(echo "$PROVIDER_INFO" | jq -r '.oidc.issuerUri')
    log_info "  Issuer: $ISSUER"
  fi
else
  log_error "WIF provider missing: $WIF_PROVIDER"
fi

# Check WIF service account binding
WIF_SA="github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com"
WIF_BINDING_MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${WIF_POOL}/attribute.repository/anbaricideas/selflytics"

SA_POLICY=$(gcloud iam service-accounts get-iam-policy "$WIF_SA" --project="$PROJECT_ID" --format=json 2>/dev/null || echo "{}")

if echo "$SA_POLICY" | jq -e ".bindings[] | select(.role==\"roles/iam.workloadIdentityUser\") | .members[] | select(. == \"$WIF_BINDING_MEMBER\")" &> /dev/null; then
  log_success "WIF service account binding configured"
else
  log_error "WIF service account binding missing for anbaricideas/selflytics"
fi

#
# Cloud Run Services Validation
#
log_section "Cloud Run Services"

# Check dev service
DEV_SERVICE="selflytics-webapp-dev"
if gcloud run services describe "$DEV_SERVICE" --region="$REGION" --project="$PROJECT_ID" &> /dev/null; then
  log_success "Cloud Run service exists: $DEV_SERVICE"

  if [[ "$VERBOSE" == "true" ]]; then
    SERVICE_URL=$(gcloud run services describe "$DEV_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")
    SERVICE_ACCOUNT=$(gcloud run services describe "$DEV_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(spec.template.spec.serviceAccountName)")
    log_info "  URL: $SERVICE_URL"
    log_info "  Service Account: $SERVICE_ACCOUNT"
  fi
else
  log_error "Cloud Run service missing: $DEV_SERVICE"
fi

# Check Cloud Run IAM for WIF invoker
CR_IAM=$(gcloud run services get-iam-policy "$DEV_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format=json 2>/dev/null || echo "{}")

if echo "$CR_IAM" | jq -e ".bindings[] | select(.role==\"roles/run.invoker\") | .members[] | select(. == \"serviceAccount:${WIF_SA}\")" &> /dev/null; then
  log_success "WIF service account has Cloud Run invoker access"
else
  log_warning "WIF service account missing Cloud Run invoker access (required for deployment validation)"
fi

#
# Firestore Validation
#
log_section "Firestore Database"

if gcloud firestore databases describe --database="(default)" --project="$PROJECT_ID" &> /dev/null; then
  log_success "Firestore database exists: (default)"

  if [[ "$VERBOSE" == "true" ]]; then
    DB_LOCATION=$(gcloud firestore databases describe --database="(default)" --project="$PROJECT_ID" --format="value(locationId)")
    log_info "  Location: $DB_LOCATION"
  fi
else
  log_error "Firestore database missing: (default)"
fi

#
# Secret Manager Validation
#
log_section "Secret Manager"

# Define expected secrets
declare -A SECRETS=(
  ["dev-jwt-secret"]="JWT signing secret for dev environment"
  ["dev-openai-api-key"]="OpenAI API key for dev environment"
)

for secret_name in "${!SECRETS[@]}"; do
  description="${SECRETS[$secret_name]}"

  if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &> /dev/null; then
    # Check if secret has at least one version
    VERSION_COUNT=$(gcloud secrets versions list "$secret_name" --project="$PROJECT_ID" --format="value(name)" | wc -l)

    if [[ "$VERSION_COUNT" -gt 0 ]]; then
      log_success "Secret exists with versions: $secret_name"
      if [[ "$VERBOSE" == "true" ]]; then
        log_info "  Purpose: $description"
        log_info "  Versions: $VERSION_COUNT"
      fi
    else
      log_warning "Secret exists but has no versions: $secret_name"
    fi
  else
    log_error "Secret missing: $secret_name ($description)"
  fi
done

# Check secret access permissions
for secret_name in "${!SECRETS[@]}"; do
  SECRET_IAM=$(gcloud secrets get-iam-policy "$secret_name" --project="$PROJECT_ID" --format=json 2>/dev/null || echo "{}")

  DEV_SA_MEMBER="serviceAccount:dev-cloud-run-sa@${PROJECT_ID}.iam.gserviceaccount.com"
  if echo "$SECRET_IAM" | jq -e ".bindings[] | select(.role==\"roles/secretmanager.secretAccessor\") | .members[] | select(. == \"$DEV_SA_MEMBER\")" &> /dev/null; then
    if [[ "$VERBOSE" == "true" ]]; then
      log_success "Secret access granted to dev-cloud-run-sa: $secret_name"
    fi
  else
    log_error "Secret access missing for dev-cloud-run-sa: $secret_name"
  fi
done

#
# Artifact Registry Validation
#
log_section "Artifact Registry"

REPO_NAME="selflytics"
if gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" --project="$PROJECT_ID" &> /dev/null; then
  log_success "Artifact Registry repository exists: $REPO_NAME"

  if [[ "$VERBOSE" == "true" ]]; then
    REPO_FORMAT=$(gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" --project="$PROJECT_ID" --format="value(format)")
    log_info "  Format: $REPO_FORMAT"
    log_info "  Location: $REGION"
  fi
else
  log_error "Artifact Registry repository missing: $REPO_NAME"
fi

#
# Enabled APIs Validation
#
log_section "Enabled APIs"

# Define required APIs
declare -A REQUIRED_APIS=(
  ["run.googleapis.com"]="Cloud Run"
  ["firestore.googleapis.com"]="Firestore"
  ["secretmanager.googleapis.com"]="Secret Manager"
  ["artifactregistry.googleapis.com"]="Artifact Registry"
  ["iam.googleapis.com"]="IAM"
  ["iamcredentials.googleapis.com"]="IAM Credentials (WIF)"
  ["cloudresourcemanager.googleapis.com"]="Cloud Resource Manager"
  ["logging.googleapis.com"]="Cloud Logging"
)

ENABLED_APIS=$(gcloud services list --enabled --project="$PROJECT_ID" --format="value(config.name)" 2>/dev/null)

for api in "${!REQUIRED_APIS[@]}"; do
  service_name="${REQUIRED_APIS[$api]}"

  if echo "$ENABLED_APIS" | grep -q "^$api$"; then
    if [[ "$VERBOSE" == "true" ]]; then
      log_success "API enabled: $service_name ($api)"
    fi
  else
    log_error "API not enabled: $service_name ($api)"
  fi
done

if [[ "$VERBOSE" != "true" && "$FAILED" == "0" ]]; then
  log_success "All required APIs are enabled"
fi

#
# Summary
#
log_section "Validation Summary"

echo ""
echo "Results:"
echo "  ${GREEN}✓${NC} Passed:   $PASSED"
echo "  ${RED}✗${NC} Failed:   $FAILED"
echo "  ${YELLOW}⚠${NC} Warnings: $WARNINGS"
echo ""

if [[ "$FAILED" -gt 0 ]]; then
  echo -e "${RED}Validation failed. Please fix the errors above.${NC}"
  exit 1
else
  if [[ "$WARNINGS" -gt 0 ]]; then
    echo -e "${YELLOW}Validation passed with warnings. Review warnings above.${NC}"
  else
    echo -e "${GREEN}All validations passed successfully!${NC}"
  fi
  exit 0
fi
