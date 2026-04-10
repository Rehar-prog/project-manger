@echo off
echo ===========================================
echo   Project Control Dashboard
echo ===========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Checking dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies may not have installed correctly
)

echo.
echo Starting Project Control Dashboard...
echo Access the dashboard at: http://localhost:8787
echo Press Ctrl+C to stop
echo.

python app.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    pause
)
