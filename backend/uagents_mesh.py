"""
PatchBounty 6-uAgent Swarm & Live Agentverse Mailbox Runner (`python -m backend.uagents_mesh`).
Works identically to DealSetu: run `python -m backend.uagents_mesh` in a second terminal to connect
`@aegis` directly to Fetch.ai Agentverse Mailbox & ASI:One while syncing live to `http://127.0.0.1:8002`!
"""
from backend.asi_one_agent import (
    aegis,
    chat_proto,
    create_swarm_bureau,
    forge,
    get_agentverse_inspector_url,
    get_swarm_roster,
    payment_proto,
    recon,
    run_agentverse_bridge,
    specter,
    vault,
    warden,
    SUBAGENTS,
    SUBAGENT_REGISTRY,
    dispatch_subagent_task,
    run_sequential_master_workflow,
    SwarmCoordinationTask,
    SwarmCoordinationResult,
)

__all__ = [
    "aegis",
    "recon",
    "specter",
    "forge",
    "warden",
    "vault",
    "chat_proto",
    "payment_proto",
    "get_swarm_roster",
    "get_agentverse_inspector_url",
    "create_swarm_bureau",
    "run_agentverse_bridge",
    "SUBAGENTS",
    "SUBAGENT_REGISTRY",
    "dispatch_subagent_task",
    "run_sequential_master_workflow",
    "SwarmCoordinationTask",
    "SwarmCoordinationResult",
]

if __name__ == "__main__":
    run_agentverse_bridge()
