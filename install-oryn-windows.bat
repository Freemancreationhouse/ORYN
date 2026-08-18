@echo off
setlocal EnableExtensions
title ORYN - Windows Installer
cd /d "%~dp0"

echo ==============================================
echo   ORYN - Designed to Move
echo   by Studio Kinematics
echo   Windows Installer
echo ==============================================
echo.

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PY=py"
) else (
  where python >nul 2>nul
  if %ERRORLEVEL%==0 (
    set "PY=python"
  ) else (
    echo Python was not found.
    echo Install Python 3.11 or 3.12 and enable "Add Python to PATH".
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PY% -m venv .venv
  if errorlevel 1 goto :fail
)

echo Updating pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail

echo Installing ORYN dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo ORYN Windows installation complete.
echo Run "run-oryn-windows.bat" to start ORYN.
pause
exit /b 0

:fail
echo.
echo ORYN installation failed. Check the error above.
pause
exit /b 1
