#!/usr/bin/env bash
# Check preview deployment count against configured limit
# Designed for CI/CD pipeline integration to prevent over-provisioning
#
# Usage:
#   check-preview-limit.sh [--quiet]
#
# Exit codes:
#   0 - Under limit (OK to deploy)
#   1 - Over limit or error
#
# Environment variables:
#   GCP_PROJECT_ID - GCP project ID (required)
#   GCP_REGION - GCP region (default: australia-southeast1)
#   PREVIEW_LIMIT - Maximum preview deployments (default: 10)
#   PREVIEW_SAFETY_MARGIN - Reserved slots for concurrent deploys (default: 2)

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-australia-southeast1}"
PREVIEW_LIMIT="${PREVIEW_LIMIT:-10}"
SAFETY_MARGIN="${PREVIEW_SAFETY_MARGIN:-2}"
EFFECTIVE_LIMIT=$((PREVIEW_LIMIT - SAFETY_MARGIN))

# Parse arguments
QUIET=false
if [[ "${1:-}" == "--quiet" ]] || [[ "${1:-}" == "-q" ]]; then
    QUIET=true
fi

# Logging functions
log_info() {
    if [ "$QUIET" = false ]; then
        echo "$1"
    fi
}

log_error() {
    echo "ERROR: $1" >&2
}

# Validate required environment variables
if [ -z "$PROJECT_ID" ]; then
    log_error "GCP_PROJECT_ID environment variable is required"
    exit 1
fi

# Function to count active preview services
count_preview_services() {
    local count
    count=$(gcloud run services list \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --filter="metadata.name:selflytics-webapp-preview" \
        --format="value(name)" 2>/dev/null | wc -l | tr -d ' ')

    echo "$count"
}

# Initial count
log_info "Checking preview deployments in project: $PROJECT_ID, region: $REGION"

count=$(count_preview_services)

if [ $? -ne 0 ]; then
    log_error "Failed to query GCP Cloud Run services"
    log_error "Ensure you are authenticated: gcloud auth login"
    log_error "Verify project: gcloud config get-value project"
    exit 1
fi

log_info "Active previews: $count / $PREVIEW_LIMIT (effective limit: $EFFECTIVE_LIMIT with safety margin of $SAFETY_MARGIN)"

# Check against effective limit
if [ "$count" -ge "$EFFECTIVE_LIMIT" ]; then
    # Retry once to ensure accuracy (mitigate transient gcloud issues)
    log_info "Limit check: retrying count to ensure accuracy..."
    sleep 2

    count=$(count_preview_services)
    log_info "Recount: $count / $PREVIEW_LIMIT"

    if [ "$count" -ge "$EFFECTIVE_LIMIT" ]; then
        log_error "Preview limit exceeded ($count >= $EFFECTIVE_LIMIT)"
        echo ""
        log_error "Please clean up old previews before creating new ones:"
        log_error "  gcloud run services list --region=$REGION --filter='metadata.name:selflytics-webapp-preview'"
        log_error ""
        log_error "To delete a preview service:"
        log_error "  gcloud run services delete SERVICE_NAME --region=$REGION"
        exit 1
    fi
fi

log_info "✓ Preview limit OK ($count < $EFFECTIVE_LIMIT)"
exit 0
