@echo off
REM Runs the EXACT production image locally (mirrors permanent hosting). Needs Docker Desktop.
cd /d "%~dp0"
docker build -t heritage-studio .
echo   -^> http://localhost:8000
docker run --rm -p 8000:8000 --env-file api/.env heritage-studio
