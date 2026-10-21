@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo        Starte FLYT STUDIO PLATFORM 2.0...
echo ========================================================
echo.

set "PY_EXE=python.exe"

:: Beende alte Instanzen auf Port 4488, damit immer die aktuelle Version laeuft
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :4488 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: Browser oeffnen
start "" http://localhost:4488

echo [INFO] Starte Plattform (FastAPI + React Studio)...
"%PY_EXE%" run_platform.py
