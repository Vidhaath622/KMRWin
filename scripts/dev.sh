#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[PollToll] Starting Backend API on http://127.0.0.1:8000 ..."
(
  cd "$ROOT_DIR/backend"
  uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[PollToll] Starting Next.js Control Plane on http://127.0.0.1:3000 ..."
cd "$ROOT_DIR/frontend"
npm run dev
