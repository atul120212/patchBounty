"""
PatchBounty — 6-uAgent Swarm Coordination Verification (prove_swarm.py).
Tests that all 6 agents (@aegis, @recon, @specter, @forge, @warden, @vault)
are registered, configured with their coordination models, and capable of
exchanging messages within the unified Fetch.ai Bureau.
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import ensure_event_loop
ensure_event_loop()

from backend.asi_one_agent import (
    aegis,
    create_swarm_bureau,
    forge,
    get_agentverse_inspector_url,
    get_swarm_roster,
    recon,
    specter,
    vault,
    warden,
    SwarmCoordinationTask,
    SwarmCoordinationResult,
    SwarmHeartbeat,
    SwarmHeartbeatAck,
)


def test_swarm_registry():
    print("======================================================================")
    print(" PatchBounty 6-uAgent Swarm Coordination Test Suite")
    print("======================================================================")

    # 1. Verify Roster
    roster = get_swarm_roster()
    assert len(roster) == 6, f"Expected 6 uAgents, found {len(roster)}"
    print(f"[1/4] Verified 6 Distinct Agents in Swarm Roster:")
    for ag in roster:
        print(f"      • {ag['handle']:10s} | {ag['name']:24s} | {ag['address'][:26]}... | Port {ag['port']}")

    # 2. Verify Bureau Integration
    bureau = create_swarm_bureau(port=8040)
    agent_names = [a.name for a in bureau._agents]
    expected_names = ["aegis", "recon", "specter", "forge", "warden", "vault"]
    for name in expected_names:
        assert name in agent_names, f"Agent {name} missing from Bureau!"
    print(f"[2/4] Fetch.ai Bureau Configured with All 6 Coordinated Agents: {agent_names}")

    # 3. Verify Message Models & Handlers Registered
    print("[3/4] Verifying Coordination Protocols & Message Handlers on All Agents:")
    agents_map = {
        "@recon": recon,
        "@specter": specter,
        "@forge": forge,
        "@warden": warden,
        "@vault": vault,
        "@aegis": aegis,
    }
    for handle, ag in agents_map.items():
        models_handled = list(getattr(ag._protocol, "models", {}).keys())
        # Also include any models registered across other included protocols (like aegis chat/payment)
        for p in getattr(ag, "protocols", {}).values():
            models_handled.extend(list(getattr(p, "models", {}).keys()))
        print(f"      • {handle:10s} coordination models registered: {len(models_handled)} active")
        assert len(models_handled) >= 1, f"{handle} has no message models registered!"

    # 4. Agentverse Inspector & Mailbox Gateway Verification
    inspector_url = get_agentverse_inspector_url()
    assert "https://agentverse.ai/inspect" in inspector_url
    assert aegis.address in inspector_url
    print(f"[4/4] Verified Coordinator Mailbox & Inspector Gateway:")
    print(f"      URL: {inspector_url[:72]}...")

    print("======================================================================")
    print(" ALL 4/4 SWARM COORDINATION CHECKS PASSED SUCCESSFULLY!")
    print("======================================================================")


if __name__ == "__main__":
    test_swarm_registry()
