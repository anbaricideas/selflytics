#!/usr/bin/env bash
# Simplified deployment validation for Phase 1
#
# Usage:
#   ./scripts/validate-deployment.sh [options] [base_url]
#   ./scripts/validate-deployment.sh --preview <feature-name>
#
# Arguments:
#   base_url       Base URL of deployment (default: http://localhost:8000)
#
# Options:
#   -h, --help                Show this help message
#   --preview FEATURE         Validate preview deployment for feature
#   --fail-if-unhealthy       Exit with code 1 if checks fail
#
# Exit codes:
#   0 - Validation passed
#   1 - Validation failed (only with --fail-if-unhealthy)

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${1:-http://localhost:8000}"
FAIL_IF_UNHEALTHY=false
PREVIEW_MODE=false
PREVIEW_FEATURE=""

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            head -15 "$0" | grep "^#" | sed 's/^# \?//'
            exit 0
            ;;
        --preview)
            PREVIEW_MODE=true
            PREVIEW_FEATURE="$2"
            shift 2
            ;;
        --fail-if-unhealthy)
            FAIL_IF_UNHEALTHY=true
            shift
            ;;
        *)
            # Assume it's the base URL
            BASE_URL="$1"
            shift
            ;;
    esac
done

# If in preview mode, construct the URL
if [ "$PREVIEW_MODE" = true ]; then
    GCP_PROJECT_ID="${GCP_PROJECT_ID:-}"
    GCP_REGION="${GCP_REGION:-australia-southeast1}"

    if [ -z "$GCP_PROJECT_ID" ]; then
        echo -e "${RED}✗${NC} GCP_PROJECT_ID environment variable is required for preview mode"
        exit 1
    fi

    # Get the preview service URL
    SERVICE_NAME="selflytics-webapp-preview-${PREVIEW_FEATURE}"
    BASE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$GCP_REGION" \
        --project="$GCP_PROJECT_ID" \
        --format="value(status.url)")

    echo -e "${BLUE}ℹ${NC} Preview URL: $BASE_URL"
fi

# Get auth token if needed (for Cloud Run URLs)
AUTH_HEADER=""
if [[ "$BASE_URL" =~ \.run\.app ]]; then
    # Use ID token from environment if available (CI mode)
    if [[ -n "${ID_TOKEN:-}" ]]; then
        AUTH_HEADER="Authorization: Bearer $ID_TOKEN"
    elif command -v gcloud &> /dev/null; then
        AUTH_TOKEN=$(gcloud auth print-identity-token 2>/dev/null || echo "")
        if [[ -n "$AUTH_TOKEN" ]]; then
            AUTH_HEADER="Authorization: Bearer $AUTH_TOKEN"
        fi
    fi
fi

# Validation function
validate_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    local url="${BASE_URL}${endpoint}"

    echo -n "Checking ${endpoint}... "

    local http_code
    if [[ -n "$AUTH_HEADER" ]]; then
        http_code=$(curl -s -w "%{http_code}" -o /dev/null -H "$AUTH_HEADER" "$url" || echo "000")
    else
        http_code=$(curl -s -w "%{http_code}" -o /dev/null "$url" || echo "000")
    fi

    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗${NC} (HTTP $http_code, expected $expected_status)"
        return 1
    fi
}

# Run validation checks
echo -e "${BLUE}━━━ Deployment Validation${NC}"
echo "Target: $BASE_URL"
echo ""

FAILED=0

# Core health check
validate_endpoint "/health" 200 || FAILED=$((FAILED + 1))

# API root (redirect to /login expected)
validate_endpoint "/" 302 || FAILED=$((FAILED + 1))

# Summary
echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validation checks passed${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILED validation check(s) failed${NC}"

    if [ "$FAIL_IF_UNHEALTHY" = true ]; then
        exit 1
    else
        exit 0
    fi
fi
