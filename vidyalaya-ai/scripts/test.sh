#!/usr/bin/env bash
# Full test suite: backend journey + units + security, then the frontend checker.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
[ -x "$ROOT/backend/.venv/bin/python" ] && PYTHON="$ROOT/backend/.venv/bin/python"

cd "$ROOT/backend"
echo "=== 1/6  end-to-end journey ==="
"$PYTHON" -m tests.test_journey
echo
echo "=== 2/6  algorithms and AI units ==="
"$PYTHON" -m tests.test_units
echo
echo "=== 3/6  security and access control ==="
"$PYTHON" -m tests.test_security
echo
echo "=== 4/6  local LLM path (stub Ollama server) ==="
"$PYTHON" -m tests.test_ollama
echo
echo "=== 5/6  vector stores (memory / Chroma / Pinecone) ==="
"$PYTHON" -m tests.test_vector_stores
echo
echo "=== 6/6  frontend consistency ==="
SPEC="$(mktemp -t vidyalaya-openapi-XXXX.json)"
"$PYTHON" - <<'PYCODE' "$SPEC"
import json, sys
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    json.dump(client.get("/openapi.json").json(), open(sys.argv[1], "w"))
PYCODE
cd "$ROOT"
"$PYTHON" scripts/verify_frontend.py --openapi "$SPEC"
rm -f "$SPEC"
echo
echo "All suites passed. (Frontend types/build: cd frontend && npm run typecheck && npm run build)"
