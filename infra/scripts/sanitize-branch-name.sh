#!/usr/bin/env bash
# Sanitize branch name for Cloud Run service naming
#
# Usage: ./sanitize-branch-name.sh <branch-name>
#
# Rules:
# - Remove common branch prefixes (feat/, fix/, chore/, etc.)
# - Convert to lowercase
# - Replace invalid characters with hyphen
# - Collapse consecutive hyphens
# - Remove leading/trailing hyphens
# - Truncate to 40 characters max
# - Fail if result is empty
#
# Input:  feat/phase-1-infrastructure
# Output: phase-1-infrastructure
#
# Cloud Run service name limit: 63 chars
# Our prefix: selflytics-webapp-preview- (27 chars)
# Max feature name: 40 chars (leaves 36 char margin for safety)

# Check bash version (requires 4.0+ for lowercase syntax)
if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    echo "Error: This script requires bash 4.0 or later (found: $BASH_VERSION)" >&2
    echo "Current syntax uses bash 4.0+ lowercase conversion (\${var,,})" >&2
    exit 1
fi

set -euo pipefail

BRANCH_NAME="${1:-}"

if [ -z "$BRANCH_NAME" ]; then
    echo "Usage: $0 <branch-name>" >&2
    exit 1
fi

# Remove common branch prefixes (feat/, fix/, chore/, etc.)
# Match everything up to and including the first slash
FEATURE_NAME=$(echo "$BRANCH_NAME" | sed 's|^[^/]*/||')

# Convert to lowercase
FEATURE_NAME="${FEATURE_NAME,,}"

# Replace invalid characters (anything not ASCII alphanumeric or hyphen) with hyphen
# Use [:alnum:] and ASCII mode to handle only ASCII chars
# LC_ALL=C forces ASCII-only interpretation
FEATURE_NAME=$(echo "$FEATURE_NAME" | LC_ALL=C tr -cs '[:alnum:]-' '-')

# Collapse consecutive hyphens to single hyphen
FEATURE_NAME=$(echo "$FEATURE_NAME" | tr -s '-')

# Remove leading/trailing hyphens - use while loop for multiple iterations
while [[ "$FEATURE_NAME" =~ ^- || "$FEATURE_NAME" =~ -$ ]]; do
    FEATURE_NAME="${FEATURE_NAME#-}"  # Remove leading hyphen
    FEATURE_NAME="${FEATURE_NAME%-}"  # Remove trailing hyphen
done

# Fail if result is empty
if [ -z "$FEATURE_NAME" ]; then
    echo "Error: Branch name sanitization resulted in empty string" >&2
    echo "Input was: $BRANCH_NAME" >&2
    exit 1
fi

# Truncate to 40 chars (leaving room for selflytics-webapp-preview- prefix = 27 chars)
# Cloud Run service name limit: 63 chars total
FEATURE_NAME="${FEATURE_NAME:0:40}"

# Remove trailing hyphens if truncation created any
while [[ "$FEATURE_NAME" =~ -$ ]]; do
    FEATURE_NAME="${FEATURE_NAME%-}"
done

echo "$FEATURE_NAME"
