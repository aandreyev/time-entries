#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run.sh  – single-command helper to build the Vue frontend and launch both
#           FastAPI backend and static frontend server.
#
# 1. Builds the production bundle with Vite ( ./frontend/dist )
# 2. Starts the FastAPI server on port 8080
# 3. Serves the static bundle on port 3000 using `npx serve`
# 4. Cleans up child processes on exit (Ctrl-C)
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT=8080
FRONTEND_PORT=3000

# Build frontend ------------------------------------------------------------
echo "[run.sh] Building frontend …"
pushd "$ROOT_DIR/frontend" >/dev/null
# Ensure deps are installed (no-op if already present)
npm install --silent
npm run build --silent
popd >/dev/null

echo "[run.sh] Frontend build completed."

# Start backend -------------------------------------------------------------
echo "[run.sh] Starting FastAPI backend on :$BACKEND_PORT …"
python3 main.py run-api --host 0.0.0.0 --port "$BACKEND_PORT" &
API_PID=$!

# Start static server for frontend -----------------------------------------
echo "[run.sh] Serving frontend dist on :$FRONTEND_PORT …"
npx serve -s "$ROOT_DIR/frontend/dist" -l "$FRONTEND_PORT" &
FE_PID=$!

echo "[run.sh] ------------------------------------------------------------"
echo "Frontend 👉 http://localhost:$FRONTEND_PORT"
echo "Backend  👉 http://localhost:$BACKEND_PORT/docs"  # FastAPI docs
echo "Press Ctrl+C to stop both."
echo "[run.sh] ------------------------------------------------------------"

# Cleanup on exit -----------------------------------------------------------
cleanup() {
  echo "\n[run.sh] Shutting down …"
  kill "$API_PID" "$FE_PID" 2>/dev/null || true
  wait "$API_PID" "$FE_PID" 2>/dev/null || true
  echo "[run.sh] Done."
}
trap cleanup SIGINT SIGTERM

# Wait forever (until Ctrl+C)
wait 