#!/bin/bash

# ==============================================================================
# Git Hooks Setup Script
# ==============================================================================
# This script installs git hooks to prevent accidental .env file commits
#
# Usage:
#   bash scripts/setup_git_hooks.sh
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "=================================================="
echo "Git Hooks Setup for Player Identification"
echo "=================================================="
echo ""

# Check if we're in a git repository
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "   Run this script from the project root"
    exit 1
fi

echo "✓ Git repository detected"
echo "✓ Installing pre-commit hook..."

# Create pre-commit hook
cat > "$GIT_HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# ==============================================================================
# Pre-commit Hook: Prevent .env file commits
# ==============================================================================

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for .env files in staged changes
ENV_FILES=$(git diff --cached --name-only | grep -E '^\.env$|^\.env\..*$' | grep -v '\.env\.example$' || true)

if [ -n "$ENV_FILES" ]; then
    echo -e "${RED}=================================================="
    echo -e "ERROR: Attempting to commit .env file(s)!"
    echo -e "==================================================${NC}"
    echo ""
    echo "The following file(s) contain secrets and should NOT be committed:"
    echo ""
    echo -e "${YELLOW}$ENV_FILES${NC}"
    echo ""
    echo "These files are blocked for security reasons."
    echo ""
    echo "To fix:"
    echo "  1. Unstage the file(s): git reset HEAD .env"
    echo "  2. Ensure .env is in .gitignore"
    echo "  3. Only commit .env.example (template)"
    echo ""
    echo -e "${RED}Commit aborted.${NC}"
    exit 1
fi

# Check for hardcoded secrets in code
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts|jsx|tsx)$' || true)

if [ -n "$STAGED_FILES" ]; then
    # Look for potential hardcoded secrets
    SECRETS_FOUND=$(git diff --cached $STAGED_FILES | grep -E '(SERP_API_KEY|AWS_SECRET|SECRET_KEY|PASSWORD|API_KEY)\s*=\s*["\047][^"\047]{10,}["\047]' || true)
    
    if [ -n "$SECRETS_FOUND" ]; then
        echo -e "${YELLOW}=================================================="
        echo -e "WARNING: Potential hardcoded secrets detected!"
        echo -e "==================================================${NC}"
        echo ""
        echo "Found potential secrets in staged changes:"
        echo "$SECRETS_FOUND"
        echo ""
        echo "Please verify these are not real secrets before committing."
        echo ""
        read -p "Do you want to continue with the commit? (y/N) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Commit aborted.${NC}"
            exit 1
        fi
    fi
fi

echo "✓ Pre-commit checks passed"
exit 0
EOF

# Make hook executable
chmod +x "$GIT_HOOKS_DIR/pre-commit"

echo "✓ Pre-commit hook installed"
echo ""
echo "=================================================="
echo "Installation Complete!"
echo "=================================================="
echo ""
echo "The following protections are now active:"
echo "  ✓ Prevents committing .env files"
echo "  ✓ Warns about potential hardcoded secrets"
echo ""
echo "Test the hook:"
echo "  1. Try to stage .env: git add .env"
echo "  2. Try to commit: git commit -m 'test'"
echo "  3. Hook should block the commit"
echo ""
echo "To bypass the hook (not recommended):"
echo "  git commit --no-verify"
echo ""
