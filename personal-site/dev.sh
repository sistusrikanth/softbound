#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "→ Installing frontend dependencies..."
cd "$ROOT/frontend"
npm install

echo "→ Building frontend..."
npm run build

echo "→ Setting up Python backend..."
cd "$ROOT/backend"
PYTHON="${PYTHON:-python3.12}"
if [ ! -d .venv ] || ! .venv/bin/python -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  rm -rf .venv
  "$PYTHON" -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

echo "→ Starting server on http://localhost:8080"
echo "  Admin: http://localhost:8080/admin (password: admin123)"
cd "$ROOT/backend"
DATA_DIR="$ROOT/data" uvicorn main:app --reload --port 8080
