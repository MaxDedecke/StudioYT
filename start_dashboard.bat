@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo        Starte FLYT STUDIO Dashboard...
echo ========================================================
echo.

set "PY_EXE="
if exist "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" (
    set "PY_EXE=C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe"
) else (
    set "PY_EXE=python.exe"
)

:: Browser öffnen
start "" http://localhost:4488

:: Prüfe ob Server bereits auf Port 4488 läuft
netstat -ano | findstr :4488 >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] FLYT Studio Server laeuft bereits auf Port 4488!
    exit /b 0
)

echo [INFO] Starte Server...
"%PY_EXE%" server.py
