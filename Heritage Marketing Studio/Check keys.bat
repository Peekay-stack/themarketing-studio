@echo off
setlocal
title Heritage - Check keys
set "ROOT=%~dp0"
if not exist "%ROOT%api\.venv\Scripts\python.exe" (
  echo [X] The app environment is missing. Run "Start Heritage Studio.bat" first.
  echo.
  pause
  exit /b 1
)
cd /d "%ROOT%api"
echo ============================================================
echo   Checking api\.env  (your key values are NOT shown)
echo ============================================================
echo.
".venv\Scripts\python.exe" -c "from dotenv import dotenv_values; import os; v=dotenv_values('.env',encoding='utf-8-sig'); a=(v.get('ANTHROPIC_API_KEY') or '').strip(); f=(v.get('FAL_KEY') or '').strip(); print('.env path        :', os.path.abspath('.env')); print('.env exists      :', os.path.exists('.env')); print('ANTHROPIC present:', bool(a), '(length', len(a), ')'); print('starts with sk-  :', a.startswith('sk-')); print('FAL present      :', bool(f))"
echo.
echo If ANTHROPIC present is True, the app will see your key on the next start.
echo.
pause
