@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo ======================================================================
echo  PatchBounty v5 - Fetch.ai One-Click Auto-Installer and Live Launcher
echo  Developed by Atul Anand, Jeeya and Vanshika
echo ======================================================================

echo [0/4] Stopping any previous old server instance on Port 8002 ...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002 " ^| findstr "LISTENING"') do (
    echo       Terminating stale PID %%a holding Port 8002 ...
    taskkill /F /PID %%a >nul 2>&1
)

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not added to PATH.
    pause
    exit /b 1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [Setup] Created .env automatically from .env.example.
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating isolated Python virtual environment in .venv ...
    python -m venv .venv
) else (
    echo [1/4] Verified existing Python virtual environment in .venv ...
)

.venv\Scripts\python.exe -c "import uagents, cosmpy, fastapi, openai, httpx" >nul 2>&1
if errorlevel 1 (
    echo [2/4] Downloading and installing all required Python dependencies...
    call .venv\Scripts\python.exe -m pip install --upgrade pip
    call .venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo [2/4] All Python packages verified ready in .venv.
)

echo [3/4] Opening PatchBounty Web Studio on http://localhost:8002 ...
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8002"

echo ======================================================================
echo  PatchBounty Studio URL     : http://localhost:8002
echo  Agentverse Mailbox Command : .venv\Scripts\python.exe -m backend.asi_one_agent
echo    (or simply double-click  : connect_agentverse.bat)
echo  Press Ctrl+C anytime to stop the server cleanly.
echo ======================================================================

.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8002
pause
