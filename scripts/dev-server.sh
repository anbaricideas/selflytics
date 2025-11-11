#!/bin/bash
# Start the development server with environment variables from backend/.env
#
# Usage: ./scripts/dev-server.sh

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Load environment variables from backend/.env if it exists
if [ -f "$BACKEND_DIR/.env" ]; then
    echo "Loading environment from backend/.env..."
    set -a  # automatically export all variables
    # shellcheck disable=SC1091
    source "$BACKEND_DIR/.env"
    set +a
else
    echo "Warning: backend/.env not found, using defaults"
fi

# Use PORT from environment, default to 8000
PORT="${PORT:-8000}"

echo "Starting development server on http://127.0.0.1:$PORT"
echo "Press Ctrl+C to stop"

# Start uvicorn with reload and proper settings
uv --directory "$BACKEND_DIR" run uvicorn app.main:app \
    --reload \
    --host 127.0.0.1 \
    --port "$PORT"
