#!/usr/bin/env bash
# Check preview deployment count against configured limit
# Designed for CI/CD pipeline integration to prevent over-provisioning
#
# Features:
#   - Automatically cleans up preview deployments for merged/deleted branches
#   - Checks remaining count against configured limit
#   - Provides detailed reporting of cleanup actions
#
# How it works:
#   1. Counts current preview deployments in Cloud Run
#   2. If AUTO_CLEANUP=true (default):
#      - Fetches list of remote Git branches
#      - Compares preview service labels against active branches
#      - Deletes previews where branch no longer exists
#      - Re-counts deployments
#   3. Verifies remaining count is under limit
#
# Automatic cleanup logic:
#   - Preview services have a "feature" label (e.g., "chat-ui-phase-1")
#   - Script checks if branch "feat/chat-ui-phase-1" still exists remotely
#   - If branch deleted (e.g., after PR merge), preview is deleted
#   - Handles common branch prefixes: feat/, feature/, bugfix/, hotfix/
#
# Usage:
#   check-preview-limit.sh [--quiet] [--no-cleanup]
#
# Options:
#   --quiet, -q       Suppress informational output (errors still shown)
#   --no-cleanup      Disable automatic cleanup (manual cleanup required)
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
#   AUTO_CLEANUP - Enable automatic cleanup (default: true)
#
# Examples:
#   # Normal usage in CI (auto-cleanup enabled)
#   ./check-preview-limit.sh --quiet
#
#   # Manual verification without cleanup
#   ./check-preview-limit.sh --no-cleanup
#
#   # Verbose mode with custom limit
#   PREVIEW_LIMIT=5 ./check-preview-limit.sh

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-australia-southeast1}"
PREVIEW_LIMIT="${PREVIEW_LIMIT:-10}"
SAFETY_MARGIN="${PREVIEW_SAFETY_MARGIN:-2}"
EFFECTIVE_LIMIT=$((PREVIEW_LIMIT - SAFETY_MARGIN))
AUTO_CLEANUP="${AUTO_CLEANUP:-true}"

# Parse arguments
QUIET=false
for arg in "$@"; do
    case $arg in
        --quiet|-q)
            QUIET=true
            ;;
        --no-cleanup)
            AUTO_CLEANUP=false
            ;;
    esac
done

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

# Function to get all remote branch names
get_remote_branches() {
    # Try GitHub CLI first (more reliable in CI, handles auth automatically)
    if command -v gh >/dev/null 2>&1; then
        log_info "Fetching branches via GitHub CLI..."

        # Use GITHUB_REPOSITORY if available (in CI), otherwise infer from git remote
        local repo="${GITHUB_REPOSITORY:-}"
        if [ -z "$repo" ] && command -v git >/dev/null 2>&1; then
            # Extract owner/repo from git remote URL
            repo=$(git remote get-url origin 2>/dev/null | sed -n 's|.*github.com[:/]\(.*\)\.git|\1|p')
        fi

        if [ -n "$repo" ]; then
            if gh api "repos/$repo/branches" --paginate --jq '.[].name' 2>/dev/null; then
                return 0
            fi
        fi

        log_info "GitHub CLI fetch failed, falling back to git ls-remote..."
    fi

    # Fallback to git ls-remote
    if ! command -v git >/dev/null 2>&1; then
        log_error "Neither gh nor git command available - cannot fetch remote branches"
        return 1
    fi

    git ls-remote --heads origin 2>&1 | \
        awk '{print $2}' | \
        sed 's|refs/heads/||' || {
            log_error "Failed to fetch remote branches via git ls-remote"
            return 1
        }
}

# Function to clean up stale preview deployments
cleanup_stale_previews() {
    log_info "Checking for stale preview deployments..."

    # Get list of remote branches
    local remote_branches
    if ! remote_branches=$(get_remote_branches); then
        log_error "Could not fetch remote branches. Skipping automatic cleanup."
        log_error "This may be due to git not being available or network issues."
        return 1
    fi

    if [ -z "$remote_branches" ]; then
        log_error "No remote branches found. This is unexpected - skipping cleanup."
        return 1
    fi

    # Debug: log number of branches found (always show, even in quiet mode)
    local branch_count
    branch_count=$(echo "$remote_branches" | wc -l | tr -d ' ')
    log_error "DEBUG: Found $branch_count remote branches"

    # Get all preview services with their feature labels
    local services
    services=$(gcloud run services list \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --filter="metadata.name:selflytics-webapp-preview" \
        --format="table[no-heading](metadata.name,metadata.labels.feature)" 2>/dev/null)

    if [ -z "$services" ]; then
        log_info "No preview deployments found."
        return 0
    fi

    local deleted_count=0

    # Process each service
    while IFS=$'\t' read -r service_name feature_label; do
        # Skip if no feature label (shouldn't happen, but be safe)
        if [ -z "$feature_label" ]; then
            log_info "⚠ Service $service_name has no feature label, skipping"
            continue
        fi

        # Convert feature label back to branch name format
        # Feature labels are sanitized (e.g., "chat-ui-phase-1" from "feat/chat-ui-phase-1")
        # We need to check if any branch ends with this pattern
        local branch_exists=false
        while IFS= read -r branch; do
            # Check if branch matches the feature label pattern
            # Handles: feat/chat-ui-phase-1 -> chat-ui-phase-1
            local sanitized_branch
            sanitized_branch=$(echo "$branch" | sed 's|^feat/||; s|^feature/||; s|^bugfix/||; s|^hotfix/||')

            if [ "$sanitized_branch" = "$feature_label" ]; then
                branch_exists=true
                break
            fi
        done <<< "$remote_branches"

        if [ "$branch_exists" = false ]; then
            log_error "DEBUG: Deleting stale preview: $service_name (feature=$feature_label, branch no longer exists)"

            if gcloud run services delete "$service_name" \
                --region="$REGION" \
                --project="$PROJECT_ID" \
                --quiet 2>/dev/null; then

                deleted_count=$((deleted_count + 1))
                log_error "DEBUG: Deleted $service_name successfully"
            else
                log_error "DEBUG: Failed to delete $service_name"
            fi
        else
            log_error "DEBUG: Keeping $service_name (feature=$feature_label, branch exists)"
        fi
    done <<< "$services"

    if [ $deleted_count -gt 0 ]; then
        log_info "✓ Cleaned up $deleted_count stale preview(s)"
    else
        log_info "✓ No stale previews found"
    fi

    return 0
}

# Initial count
log_info "Checking preview deployments in project: $PROJECT_ID, region: $REGION"

if ! count=$(count_preview_services); then
    log_error "Failed to query GCP Cloud Run services"
    log_error "Ensure you are authenticated: gcloud auth login"
    log_error "Verify project: gcloud config get-value project"
    exit 1
fi

log_info "Active previews: $count / $PREVIEW_LIMIT (effective limit: $EFFECTIVE_LIMIT with safety margin of $SAFETY_MARGIN)"

# Run automatic cleanup if enabled
if [ "$AUTO_CLEANUP" = "true" ]; then
    log_info ""
    log_info "Running automatic cleanup of stale previews..."

    if cleanup_stale_previews; then
        # Recount after cleanup
        count=$(count_preview_services)
        log_info "Previews after cleanup: $count / $PREVIEW_LIMIT"
    else
        log_error "Automatic cleanup failed or was skipped. Proceeding with limit check."
    fi
fi

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
        log_error "Automatic cleanup did not free enough space."
        log_error ""
        log_error "To view all previews:"
        log_error "  gcloud run services list --region=$REGION --filter='metadata.name:selflytics-webapp-preview'"
        log_error ""
        log_error "To delete a preview service:"
        log_error "  gcloud run services delete SERVICE_NAME --region=$REGION"
        log_error ""
        log_error "To disable automatic cleanup:"
        log_error "  AUTO_CLEANUP=false $0"
        exit 1
    fi
fi

log_info "✓ Preview limit OK ($count < $EFFECTIVE_LIMIT)"
exit 0
