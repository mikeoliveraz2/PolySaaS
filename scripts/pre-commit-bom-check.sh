#!/bin/bash
# Pre-commit hook: Verify BOM before allowing commit
#
# Installation:
#   cp scripts/pre-commit-bom-check.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# This hook will run automatically before each `git commit`.
# It warns if the commit appears incomplete based on the Mattermost Passthrough BOM.

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check if verify_bom.py exists
if [ ! -f "scripts/verify_bom.py" ]; then
    echo -e "${YELLOW}⚠️  Warning: BOM verification script not found. Skipping BOM check.${NC}"
    exit 0
fi

# Run BOM verification
echo -e "${YELLOW}🔍 Running BOM verification...${NC}"

# Get staged files
STAGED_FILES=$(git diff --cached --name-only)

# Check if this is a Mattermost passthrough commit
if echo "$STAGED_FILES" | grep -q -E "mattermost_handler|passthrough_shim|mattermost_shim"; then
    echo -e "${YELLOW}📋 Mattermost passthrough files detected. Checking BOM...${NC}"
    
    if ! python scripts/verify_bom.py --check-staged; then
        echo ""
        echo -e "${RED}❌ BOM verification failed.${NC}"
        echo ""
        echo "Your commit may be incomplete. Review the BOM checklist:"
        echo "   Documentation: documentation/BOM_MATTERMOST_PASSTHROUGH_SSO.md"
        echo ""
        echo "To bypass this check (NOT RECOMMENDED):"
        echo "   git commit --no-verify"
        echo ""
        exit 1
    fi
    
    echo -e "${GREEN}✅ BOM verification passed!${NC}"
fi

exit 0
