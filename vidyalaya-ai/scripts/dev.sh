#!/usr/bin/env bash
# Start the backend (port 8000) and the frontend (port 5173) for development.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Backend"
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install -q --upgrade pip
  ./.venv/bin/pip install -q -r requirements.txt
fi
./.venv/bin/python -m app.seed.seed --index >/dev/null 2>&1 || true
./.venv/bin/uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "==> Frontend"
cd "$ROOT/frontend"
[ -d node_modules ] || npm install
npm run dev &
FRONTEND_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT
echo ""
echo "Vidyalaya AI is starting:"
echo "  frontend  http://localhost:5173"
echo "  API docs  http://localhost:8000/docs"
echo "  demo      abhinav@student.vidyalaya.ai / Student@123"
wait
