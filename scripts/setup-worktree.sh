#!/usr/bin/env bash
#
# setup-worktree.sh - Set up a git worktree with shared configuration files
#
# This script sets up symlinks to gitignored configuration files from the main
# repository, allowing worktrees to share the same .env and terraform.tfvars files.
#
# Usage:
#   ./scripts/setup-worktree.sh [main-repo-path]
#
# Arguments:
#   main-repo-path    Path to main repository (default: auto-detect)
#
# Example:
#   # From within a worktree
#   ./scripts/setup-worktree.sh
#
#   # Specify main repo path explicitly
#   ./scripts/setup-worktree.sh ../clinicraft-wt1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKTREE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ${NC} $*"
}

log_success() {
    echo -e "${GREEN}✅${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC} $*"
}

log_error() {
    echo -e "${RED}❌${NC} $*"
}

# Detect main repository path
detect_main_repo() {
    local main_repo_path="${1:-}"

    if [[ -n "$main_repo_path" ]]; then
        echo "$main_repo_path"
        return
    fi

    # Try to detect main repo from git worktree list
    local git_dir
    git_dir=$(git rev-parse --git-common-dir 2>/dev/null || echo "")

    if [[ -z "$git_dir" ]]; then
        log_error "Not in a git repository"
        exit 1
    fi

    # Get main worktree path from git
    local main_path
    main_path=$(git worktree list --porcelain | grep -m1 "^worktree" | cut -d' ' -f2)

    if [[ -z "$main_path" ]]; then
        log_error "Could not detect main repository path"
        exit 1
    fi

    echo "$main_path"
}

create_symlink() {
    local source=$1
    local target=$2
    local description=$3

    # Create parent directory if needed
    local target_dir
    target_dir=$(dirname "$target")
    mkdir -p "$target_dir"

    # Check if target already exists
    if [[ -L "$target" ]]; then
        log_warning "$description already exists (symlink)"
        return
    elif [[ -f "$target" ]]; then
        log_warning "$description already exists (regular file) - skipping"
        return
    fi

    # Check if source exists
    if [[ ! -f "$source" ]]; then
        log_warning "Source file does not exist: $source - skipping"
        return
    fi

    # Create symlink
    ln -s "$source" "$target"
    log_success "Created symlink: $description"
}

main() {
    echo
    echo "🔗 Git Worktree Configuration Setup"
    echo "===================================="
    echo

    # Detect main repo
    MAIN_REPO=$(detect_main_repo "${1:-}")
    log_info "Main repository: $MAIN_REPO"
    log_info "Worktree: $WORKTREE_ROOT"
    echo

    # Check if we're actually in a worktree
    if [[ "$MAIN_REPO" == "$WORKTREE_ROOT" ]]; then
        log_warning "You appear to be in the main repository, not a worktree"
        log_info "This script is intended for setting up git worktrees"
        echo
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi

    echo "Creating symlinks to configuration files..."
    echo

    # Root .env file
    create_symlink \
        "$MAIN_REPO/.env" \
        "$WORKTREE_ROOT/.env" \
        ".env (root)"

    # Backend .env file
    create_symlink \
        "$MAIN_REPO/backend/.env" \
        "$WORKTREE_ROOT/backend/.env" \
        "backend/.env"

    # Terraform tfvars (dev)
    create_symlink \
        "$MAIN_REPO/infra/environments/dev/terraform.tfvars" \
        "$WORKTREE_ROOT/infra/environments/dev/terraform.tfvars" \
        "infra/environments/dev/terraform.tfvars"

    # Terraform tfvars (staging) - if it exists
    if [[ -f "$MAIN_REPO/infra/environments/staging/terraform.tfvars" ]]; then
        create_symlink \
            "$MAIN_REPO/infra/environments/staging/terraform.tfvars" \
            "$WORKTREE_ROOT/infra/environments/staging/terraform.tfvars" \
            "infra/environments/staging/terraform.tfvars"
    fi

    # Claude Code settings (local)
    create_symlink \
        "$MAIN_REPO/.claude/settings.local.json" \
        "$WORKTREE_ROOT/.claude/settings.local.json" \
        ".claude/settings.local.json"

    echo
    log_info "Checking Python virtual environment..."

    # Install dependencies if needed
    if [[ -d "$WORKTREE_ROOT/backend" ]]; then
        if [[ ! -d "$WORKTREE_ROOT/backend/.venv" ]]; then
            log_warning "Python virtual environment not found"
            echo
            read -p "Install Python dependencies? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Installing dependencies with uv..."
                (cd "$WORKTREE_ROOT/backend" && uv sync --all-extras)
                log_success "Dependencies installed"
            fi
        else
            log_success "Python virtual environment exists"
        fi
    fi

    echo
    log_success "Worktree setup complete!"
    echo
    echo "You can now work in this worktree with the same configuration as the main repo."
    echo "Any changes to .env or terraform.tfvars in the main repo will automatically"
    echo "be reflected here (and vice versa)."
    echo
}

# Run main
main "$@"
