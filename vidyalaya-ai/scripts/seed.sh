#!/usr/bin/env bash
# Reset the database, seed the whole Class 12 curriculum and build the AI index.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"
PYTHON="${PYTHON:-python3}"
[ -x .venv/bin/python ] && PYTHON=.venv/bin/python
"$PYTHON" -m app.seed.seed --reset --index
