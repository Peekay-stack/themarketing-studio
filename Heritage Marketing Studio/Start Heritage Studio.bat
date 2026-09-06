@echo off
setlocal enabledelayedexpansion
title Heritage Marketing Studio
set "ROOT=%~dp0"
set "LOG=%ROOT%heritage-log.txt"

echo ============================================================
echo   Heritage Marketing Studio - launcher
echo ============================================================
echo.

if not exist "%ROOT%api\main.py" (
  echo [X] Could not find the "api" folder next to this file.
  echo     Right-click the .zip -^> "Extract All..." then run this from the
  echo     extracted folder ^(the one that contains the "api" folder^).
  echo.
  pause
  exit /b 1
)
cd /d "%ROOT%api"
> "%LOG%" echo Heritage Marketing Studio startup log
>>"%LOG%" echo =====================================

REM --- find Python (py launcher is preferred; the Store stub can't shadow it) ---
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
  echo [X] Python was not found.
  echo     Install Python 3.10+ from https://www.python.org/downloads/
  echo     During install, TICK "Add python.exe to PATH", then run this again.
  echo.
  pause
  exit /b 1
)
echo [ok] Python: %PY%

if not exist ".venv\Scripts\python.exe" (
  echo [..] Creating environment ^(first run only^)...
  %PY% -m venv .venv >>"%LOG%" 2>&1
  if errorlevel 1 ( echo [X] Environment creation failed. & start "" notepad "%LOG%" & pause & exit /b 1 )
)
set "VPY=.venv\Scripts\python.exe"

if not exist ".deps-installed" (
  echo [..] Installing dependencies. First time can take a few minutes...
  "%VPY%" -m pip install --upgrade pip >>"%LOG%" 2>&1
  "%VPY%" -m pip install -r requirements.txt >>"%LOG%" 2>&1
  if errorlevel 1 (
    echo [X] Core install failed - opening the log, please send it to me.
    start "" notepad "%LOG%"
    pause
    exit /b 1
  )
  echo [..] Installing optional extras ^(figures/media - fine if these fail^)...
  "%VPY%" -m pip install -r requirements-optional.txt >>"%LOG%" 2>&1
  if errorlevel 1 ( echo [!] Optional extras skipped - the IMC brief renders without embedded figures. )
  echo done > ".deps-installed"
) else (
  echo [ok] Dependencies already installed.  ^(To reinstall: delete api\.deps-installed and api\.venv, then run again.^)
)

REM --- make sure a .env exists ------------------------------------------
if not exist ".env" (
  if exist ".env.example" ( copy ".env.example" ".env" >nul ) else ( echo ANTHROPIC_API_KEY=> ".env" )
)

REM --- loop until the Anthropic key is actually detected (BOM-tolerant) --
:checkkey
"%VPY%" -c "from dotenv import dotenv_values;v=dotenv_values('.env',encoding='utf-8-sig');import sys;sys.exit(0 if (v.get('ANTHROPIC_API_KEY') or '').strip() else 1)"
if errorlevel 1 (
  echo.
  echo [action] Your ANTHROPIC_API_KEY is not set yet.
  echo          In the Notepad window, type your key right after  ANTHROPIC_API_KEY=
  echo          so the line reads  ANTHROPIC_API_KEY=sk-ant-...   then SAVE and CLOSE Notepad.
  echo.
  start /wait notepad ".env"
  goto checkkey
)
echo [ok] Anthropic key detected.

where node >nul 2>nul || echo [!] Node.js not found - IMC brief .docx renders without embedded figures.

echo.
echo   Server -^> http://127.0.0.1:8000   (opens automatically in a moment)
echo   Check keys any time at http://127.0.0.1:8000/health
echo   Keep THIS window open. Press Ctrl+C to stop.
echo.
start "" cmd /c "timeout /t 6 /nobreak >nul & start http://127.0.0.1:8000"
"%VPY%" -m uvicorn main:app --host 127.0.0.1 --port 8000 2>>"%LOG%"

echo.
echo ============================================================
echo  Server stopped. If it did not open, the reason is in:
echo    %LOG%
echo  (opening it now - please send me its contents).
echo ============================================================
start "" notepad "%LOG%"
pause
