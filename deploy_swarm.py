"""
PatchBounty — 6-uAgent Swarm Coordinated Deployment Runner (deploy_swarm.py).
Deploys and executes all 6 Fetch.ai uAgents (@aegis, @recon, @specter, @forge, @warden, @vault)
concurrently inside a unified Fetch.ai Bureau on dedicated ports 8021-8026.
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import ensure_event_loop
ensure_event_loop()

from backend.asi_one_agent import (
    AEGIS_PORT,
    aegis,
    create_swarm_bureau,
    forge,
    get_agentverse_inspector_url,
    get_swarm_roster,
    recon,
    run_agentverse_bridge,
    specter,
    vault,
    warden,
)


def main():
    print("======================================================================")
    print("  PATCHBOUNTY // 6-uAgent Swarm Coordinated Deployment")
    print("  Running with Fetch.ai uAgents Bureau & Agentverse Coordination")
    print("======================================================================")
    run_agentverse_bridge()


if __name__ == "__main__":
    main()
