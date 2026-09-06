#!/usr/bin/env bash
# One-command local run (mac/Linux). Needs Python 3.10+ and Node 18+.
set -e
cd "$(dirname "$0")/api"
python3 -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
[ -d brief_assets/node_modules ] || (cd brief_assets && npm install --no-audit --no-fund && cd ..)
echo ""
echo "  Heritage Marketing Studio -> http://localhost:8000   (API docs: /docs)"
echo ""
uvicorn main:app --reload --port 8000
