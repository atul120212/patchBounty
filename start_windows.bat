@echo off
title PATCHBOUNTY // @aegis Cyber-Noir Studio (Port 8002)
echo ============================================================================
echo   PATCHBOUNTY // @aegis — STARTING WEB STUDIO ON http://localhost:8002
echo   Also run in a second terminal for live ASI:One + Agentverse Mailbox:
echo     python -m backend.asi_one_agent
echo ============================================================================
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8002
