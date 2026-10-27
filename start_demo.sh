#!/usr/bin/env zsh
# 1-Command Judge Stage Launcher for PollToll (Backend :8000 + Frontend :3000)
set -e
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting PollToll Audit & Quota Shield API on http://127.0.0.1:8000 ..."
(cd "$ROOT_DIR/backend" && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000) &
BACK_PID=$!

trap "kill $BACK_PID 2>/dev/null || true" EXIT INT TERM
sleep 2

echo "⚡ Pre-warming DuckDB AI cache for instant (<2ms) stage demo clicks..."
python3 "$ROOT_DIR/scripts/prewarm_demo_cache.py" || true

echo "🌐 Starting PollToll 4-Plane Control Console on http://localhost:3000 ..."
cd "$ROOT_DIR/frontend" && npm run dev
