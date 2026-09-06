@echo off
REM One-command local run (Windows). Needs Python 3.10+ and Node 18+.
cd /d "%~dp0api"
if not exist .venv ( python -m venv .venv )
call .venv\Scripts\activate
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt
if not exist brief_assets\node_modules ( pushd brief_assets & npm install --no-audit --no-fund & popd )
echo.
echo   Heritage Marketing Studio -^> http://localhost:8000   (API docs: /docs)
echo.
uvicorn main:app --reload --port 8000
