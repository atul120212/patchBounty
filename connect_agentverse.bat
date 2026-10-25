@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo [0/2] Clearing any previous instances on Swarm Ports 8021-8026 ...
for %%p in (8021 8022 8023 8024 8025 8026) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%p " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo [1/2] Launching PatchBounty 6-uAgent Swarm in Coordinated Bureau ...
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -u deploy_swarm.py
) else (
    python -u deploy_swarm.py
)
pause
