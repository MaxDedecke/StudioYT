@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo        Starte FLYT STUDIO PLATFORM 2.0...
echo ========================================================
echo.

set "PY_EXE=python.exe"

:: Browser oeffnen
start "" http://localhost:4488

:: Pruefe ob Server bereits auf Port 4488 laeuft
netstat -ano | findstr :4488 >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] FLYT Studio Platform laeuft bereits auf Port 4488!
    exit /b 0
)

echo [INFO] Starte Plattform (FastAPI + React Studio)...
"%PY_EXE%" run_platform.py
