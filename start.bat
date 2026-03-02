@echo off
setlocal

set API_PORT=8000
set STREAMLIT_PORT=8501

REM Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3 is required. Install it from https://python.org
    exit /b 1
)

for /f "tokens=*" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VERSION=%%i
echo Using Python %PY_VERSION%

REM Create venv if needed
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM Install deps
echo Installing dependencies...
pip install -q -e ".[dev]"

REM Create data directories
if not exist "data" mkdir data

REM Start API
echo Starting API on port %API_PORT%...
start /b uvicorn app.main:app --host 0.0.0.0 --port %API_PORT%

REM Wait for API
echo Waiting for API...
timeout /t 5 /nobreak >nul

REM Start Streamlit
echo Starting Streamlit on port %STREAMLIT_PORT%...
start /b streamlit run frontend/app.py --server.port %STREAMLIT_PORT% --server.headless true

timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo   Contract Template Manager is running!
echo   API:      http://localhost:%API_PORT%/docs
echo   Frontend: http://localhost:%STREAMLIT_PORT%
echo   Close this window to stop
echo ============================================
echo.

start http://localhost:%STREAMLIT_PORT%

REM Keep window open
pause
