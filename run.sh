#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run.sh  – build the Vue frontend then launch FastAPI (serves API + static files).
#
# Steps:
#   1. Build production bundle (frontend/dist)
#   2. Start FastAPI on BACKEND_PORT (serves /api and frontend SPA)
#   3. Ctrl-C stops the single process
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env file
if [ -f "$ROOT_DIR/.env" ]; then
  set -a  # automatically export all variables
  source "$ROOT_DIR/.env"
  set +a  # stop automatically exporting
fi

# Use environment variable or default
BACKEND_PORT=${BACKEND_PORT:-8080}

# Free the target port if already in use (macOS/Linux)
echo "[run.sh] Ensuring port $BACKEND_PORT is free …"
PORT_PIDS=$(lsof -tiTCP:$BACKEND_PORT -sTCP:LISTEN 2>/dev/null || true)
if [ -n "$PORT_PIDS" ]; then
  echo "[run.sh] Port $BACKEND_PORT in use by PID(s): $PORT_PIDS – terminating…"
  # Best-effort graceful kill
  kill $PORT_PIDS 2>/dev/null || true
  sleep 0.5
  # Force kill if still present
  REMAINING=$(lsof -tiTCP:$BACKEND_PORT -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$REMAINING" ]; then
    echo "[run.sh] Forcing termination of PID(s): $REMAINING"
    kill -9 $REMAINING 2>/dev/null || true
    sleep 0.2
  fi
fi
echo "[run.sh] Port $BACKEND_PORT is available."

# Build frontend ------------------------------------------------------------
echo "[run.sh] Building frontend …"
pushd "$ROOT_DIR/frontend" >/dev/null
# Ensure deps are installed (no-op if already present)
npm install --silent
npm run build --silent
popd >/dev/null

echo "[run.sh] Frontend build completed."

# Start unified backend (serves API + static assets) -----------------------
echo "[run.sh] Starting FastAPI (API + Frontend) on :$BACKEND_PORT …"
python3 main.py run-api --host 0.0.0.0 --port "$BACKEND_PORT"

echo "[run.sh] Server exited." 