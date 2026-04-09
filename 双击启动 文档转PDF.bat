@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo    Doc2PDF Tool Starting...
echo ========================================
echo.

set "PROJECT_DIR=%~dp0"
set "VENV_PYTHON=%PROJECT_DIR%venv\Scripts\python.exe"
set "MAIN_PY=%PROJECT_DIR%backend\main.py"

if not exist "%VENV_PYTHON%" (
    echo Error: Python not found
    echo Please make sure the folder is extracted completely.
    pause
    exit /b 1
)

if not exist "%MAIN_PY%" (
    echo Error: main.py not found
    pause
    exit /b 1
)

echo Starting server on http://localhost:8503
echo.

cmd /c "title Doc2PDF Server && cd /d "%PROJECT_DIR%" && venv\Scripts\python backend\main.py"

pause