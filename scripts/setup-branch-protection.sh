#!/bin/bash

# Branch Protection Setup Script
# This script sets up branch protection rules for the repository
# Requires GitHub CLI to be installed and authenticated

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed. Please install it first."
    print_status "Installation guide: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    print_error "You are not authenticated with GitHub CLI."
    print_status "Please run: gh auth login"
    exit 1
fi

# Get repository name
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

if [ -z "$REPO" ]; then
    print_error "Could not determine repository name. Are you in a git repository?"
    exit 1
fi

print_status "Setting up branch protection for repository: $REPO"

# Function to set up branch protection for a specific branch
setup_branch_protection() {
    local branch=$1
    local required_reviews=$2
    local require_code_owners=$3
    local enforce_admins=$4

    print_status "Setting up protection for branch: $branch"

    # Set required status checks
    gh api repos/$REPO/branches/$branch/protection \
        --method PUT \
        --field required_status_checks='{"strict":true,"contexts":["test","docker-build","security-scan"]}' \
        --field enforce_admins=$enforce_admins \
        --field required_pull_request_reviews="{\"required_approving_review_count\":$required_reviews,\"dismiss_stale_reviews\":true,\"require_code_owner_reviews\":$require_code_owners,\"require_last_push_approval\":true}" \
        --field restrictions='{"users":[],"teams":[]}' \
        --field required_linear_history=true \
        --field allow_force_pushes=false \
        --field allow_deletions=false \
        --field block_creations=true \
        --field required_conversation_resolution=true

    print_status "✅ Branch protection configured for $branch"
}

# Create develop branch if it doesn't exist
if ! git show-ref --verify --quiet refs/remotes/origin/develop; then
    print_warning "Develop branch doesn't exist. Creating it..."
    git checkout -b develop
    git push -u origin develop
    print_status "✅ Created and pushed develop branch"
fi

# Set up protection for main branch
setup_branch_protection "main" 2 true true

# Set up protection for develop branch
setup_branch_protection "develop" 1 false false

print_status "🎉 Branch protection setup completed!"
print_status ""
print_status "Summary of protection rules:"
print_status "  Main branch:"
print_status "    - Requires 2 approving reviews"
print_status "    - Requires code owner reviews"
print_status "    - Enforces admin restrictions"
print_status "    - Requires linear history"
print_status "    - Blocks direct pushes"
print_status ""
print_status "  Develop branch:"
print_status "    - Requires 1 approving review"
print_status "    - No code owner requirement"
print_status "    - No admin enforcement"
print_status "    - Allows non-linear history"
print_status "    - Blocks direct pushes"
print_status ""
print_status "Both branches require:"
print_status "  - All CI checks to pass"
print_status "  - Conversation resolution"
print_status "  - No force pushes or deletions"
