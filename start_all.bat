@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title PATCHBOUNTY // Launch All Agents and Studio

echo ======================================================================
echo   PATCHBOUNTY // LAUNCHING ALL 6 AGENTS + WEB STUDIO AT ONCE
echo ======================================================================

if exist ".venv\Scripts\python.exe" (
    set "PY_BIN=.venv\Scripts\python.exe"
) else (
    set "PY_BIN=python"
)

echo [1/2] Launching 6-uAgent Swarm in a new coordinated terminal ...
start "PatchBounty 6-Agent Swarm" cmd /k "%PY_BIN% deploy_swarm.py"

echo [2/2] Launching Web Studio on http://127.0.0.1:8002 ...
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8002"
%PY_BIN% -m backend.main

pause
