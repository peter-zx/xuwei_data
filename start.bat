@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo    Doc2PDF Tool Starting...
echo ========================================
echo.

cd /d "%~dp0"

if not exist "venv" (
    echo First run, creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo.
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
    echo Done!
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Starting service...
echo Browser will open http://localhost:8501
echo Press Ctrl+C to stop
echo.

python backend\main.py

pause
