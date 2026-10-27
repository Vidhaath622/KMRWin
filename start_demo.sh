#!/usr/bin/env zsh
# 1-Command Judge Stage Launcher for PollToll (Backend :8000 + Frontend :3000)
set -e
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---- Prerequisite checks -------------------------------------------------
for tool in uv node npm; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "❌ '$tool' is not installed or not on PATH."
    case "$tool" in
      uv) echo "   Install: curl -LsSf https://astral.sh/uv/install.sh | sh   (or: brew install uv)" ;;
      node|npm) echo "   Install Node.js 18+ from https://nodejs.org (or: brew install node)" ;;
    esac
    exit 1
  fi
done

# ---- Make sure the ports are free (stale dev servers are a common cause) ----
free_port() {
  local port="$1" pids
  pids="$(lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null || true)"
  [ -z "$pids" ] && return 0
  echo "⚠️  Port $port is already in use by:"
  lsof -i :"$port" -sTCP:LISTEN 2>/dev/null | sed 's/^/     /'
  if [ -t 0 ]; then
    read "?   Kill it and continue? [y/N] " ans
    if [[ "$ans" == [yY]* ]]; then
      echo "$pids" | xargs kill 2>/dev/null || true
      sleep 1
      pids="$(lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null || true)"
      [ -n "$pids" ] && echo "$pids" | xargs kill -9 2>/dev/null || true
      return 0
    fi
  fi
  echo "❌ Free port $port first (e.g. 'lsof -ti :$port | xargs kill') and re-run."
  exit 1
}
free_port 8000
free_port 3000

# ---- Install dependencies on first run (node_modules/.venv are not in git) --
echo "📦 Syncing backend dependencies (uv sync) ..."
(cd "$ROOT_DIR/backend" && uv sync)

if [ ! -x "$ROOT_DIR/frontend/node_modules/.bin/next" ]; then
  echo "📦 Installing frontend dependencies (npm install) ..."
  (cd "$ROOT_DIR/frontend" && npm install)
fi

# ---- Backend -------------------------------------------------------------
echo "🚀 Starting PollToll Audit & Quota Shield API on http://127.0.0.1:8000 ..."
(cd "$ROOT_DIR/backend" && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000) &
BACK_PID=$!

trap "kill $BACK_PID 2>/dev/null || true" EXIT INT TERM

# Wait up to ~60s for the backend to become healthy (instead of a fixed sleep)
echo "⏳ Waiting for backend to be ready ..."
READY=0
for i in {1..60}; do
  if ! kill -0 "$BACK_PID" 2>/dev/null; then
    echo "❌ Backend process exited early — see the error above."
    exit 1
  fi
  if curl -sf http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done
if [ "$READY" -ne 1 ]; then
  echo "❌ Backend did not become healthy within 60s."
  exit 1
fi

echo "⚡ Pre-warming DuckDB AI cache for instant (<2ms) stage demo clicks..."
python3 "$ROOT_DIR/scripts/prewarm_demo_cache.py" || true

echo "🌐 Starting PollToll 4-Plane Control Console on http://localhost:3000 ..."
cd "$ROOT_DIR/frontend" && npm run dev
