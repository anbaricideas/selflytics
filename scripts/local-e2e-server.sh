#!/bin/bash
# Start Firestore emulator and dev server for local e2e testing
#
# Usage:
#   ./scripts/local-e2e-server.sh
#
# This script:
# - Starts Firestore emulator in background
# - Waits for emulator to be ready
# - Starts dev server with emulator configuration
# - Cleans up emulator on exit

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting local e2e environment...${NC}"

# Add Java to PATH if homebrew Java is available
if [ -d "/opt/homebrew/opt/openjdk/bin" ]; then
    export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
fi

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo -e "${RED}Error: Firebase CLI not found${NC}"
    echo "Install with: npm install -g firebase-tools"
    exit 1
fi

# Get Firebase CLI path
FIREBASE_CMD=$(command -v firebase)

# Check if .env.local exists
BACKEND_DIR="$(cd "$(dirname "$0")/../backend" && pwd)"
ENV_LOCAL="${BACKEND_DIR}/.env.local"

if [ ! -f "$ENV_LOCAL" ]; then
    echo -e "${YELLOW}Warning: ${ENV_LOCAL} not found${NC}"
    echo "Create it from backend/.env.local.example for local e2e testing"
    exit 1
fi

# Start Firestore emulator in background
echo -e "${GREEN}Starting Firestore emulator...${NC}"
"$FIREBASE_CMD" emulators:start --only firestore --project test-project &
EMULATOR_PID=$!

# Wait for emulator to be ready (check port 8080)
echo -e "${YELLOW}Waiting for Firestore emulator...${NC}"
TIMEOUT=30
ELAPSED=0

while ! curl -s http://localhost:8080 > /dev/null 2>&1; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo -e "${RED}Error: Firestore emulator failed to start within ${TIMEOUT}s${NC}"
        kill $EMULATOR_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

echo -e "${GREEN}Firestore emulator ready!${NC}"

# Set environment variables for dev server
export FIRESTORE_EMULATOR_HOST=localhost:8080
export GOOGLE_CLOUD_PROJECT=test-project

# Load .env.local for additional configuration
set -a
source "$ENV_LOCAL"
set +a

echo -e "${GREEN}Starting dev server...${NC}"
echo -e "${YELLOW}Environment: FIRESTORE_EMULATOR_HOST=${FIRESTORE_EMULATOR_HOST}${NC}"
echo -e "${YELLOW}Base URL: ${BASE_URL:-http://localhost:8000}${NC}"
echo ""
echo -e "${GREEN}Ready for e2e tests!${NC}"
echo -e "Run tests in another terminal:"
echo -e "  ${YELLOW}uv --directory backend run pytest tests/e2e_playwright -v --headed${NC}"
echo ""
echo -e "Press ${RED}Ctrl+C${NC} to stop"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    kill $EMULATOR_PID 2>/dev/null || true
    wait $EMULATOR_PID 2>/dev/null || true
    echo -e "${GREEN}Cleanup complete${NC}"
}

trap cleanup EXIT INT TERM

# Start dev server (using existing script)
cd "$BACKEND_DIR/.."
./scripts/dev-server.sh
