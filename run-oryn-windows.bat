@echo off
setlocal
title ORYN - Designed to Move
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ORYN is not installed yet.
  echo Run install-oryn-windows.bat first.
  pause
  exit /b 1
)

echo Starting ORYN...
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8080"
".venv\Scripts\python.exe" main.py

echo.
echo ORYN stopped.
pause
