#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "======================================================================"
echo " PatchBounty (Project 2) — Fetch.ai One-Command Turnkey Launcher"
echo " Developed by Atul Anand, Jeeya & Vanshika"
echo "======================================================================"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "[Setup] Created .env from .env.example (zero keys needed to start)."
fi

if [ ! -d ".venv" ]; then
  echo "[1/4] Creating Python virtual environment (.venv)..."
  python3 -m venv .venv
fi

echo "[2/4] Verifying Python uAgents, cosmpy, pytest & FastAPI dependencies..."
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt

if [ ! -d "frontend/node_modules" ]; then
  echo "[3/4] Installing React + Vite Fetch.ai Studio UI dependencies..."
  (cd frontend && npm install --no-fund --no-audit && npm run build)
else
  echo "[3/4] Frontend dependencies ready."
fi

echo "======================================================================"
echo " Starting Unified PatchBounty Full-Stack Studio -> http://localhost:8002"
echo " Press Ctrl+C anytime to stop."
echo "======================================================================"

./.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8002
