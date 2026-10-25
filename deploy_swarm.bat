@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title PATCHBOUNTY // 6-uAgent Swarm Coordinated Deployment

echo ======================================================================
echo   PATCHBOUNTY // 6-uAGENT SWARM COORDINATED DEPLOYMENT
echo   Deploying: @aegis @recon @specter @forge @warden @vault
echo ======================================================================

echo [1/3] Clearing any previous instances holding Swarm Ports 8021-8026 ...
for %%p in (8021 8022 8023 8024 8025 8026) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%p " ^| findstr "LISTENING"') do (
        echo       Freeing port %%p (PID %%a) ...
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo [2/3] Verifying Python environment ...
if exist ".venv\Scripts\python.exe" (
    set "PY_BIN=.venv\Scripts\python.exe"
) else (
    set "PY_BIN=python"
)

echo [3/3] Starting Fetch.ai Bureau with all 6 Agents in full coordination ...
echo       Studio API Mirror: http://127.0.0.1:8002
echo       Press Ctrl+C to terminate cleanly.
echo ======================================================================

%PY_BIN% -u deploy_swarm.py
pause
