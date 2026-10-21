@echo off
setlocal enabledelayedexpansion

:: Navigate to script directory
cd /d "%~dp0"

echo =====================================================================
echo  Smart EV Battery Management System
echo  ANFIS-Based Battery State of Health Estimation
echo =====================================================================
echo.

:: 1. Verify Python Installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python is available:
python --version
echo.

:: 2. Manage Virtual Environment (Optional / Recommended)
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (.venv)...
    call .venv\Scripts\activate.bat
)

:: 3. Launch Application
echo [INFO] Starting Smart EV Battery Management System (ANFIS V5)...
echo Note: Pass --web to launch in browser mode if desired.
echo.
python app.py %*

if errorlevel 1 (
    echo.
    echo [ERROR] Application terminated with an error code.
    pause
)

endlocal
