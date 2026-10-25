import json
from datetime import datetime, timezone
from uuid import uuid4
from uagents_core.contrib.protocols.chat import ChatMessage, MetadataContent, TextContent


def make_acp_card_message(text: str, card_kind: str, payload: dict) -> tuple[ChatMessage, dict]:
    serialized = json.dumps(payload, separators=(",", ":"))
    meta_dict = {
        "card_protocol_version": "1",
        "card_kind": card_kind,
        "requires_card_interaction": "true",
        "card_payload": serialized,
    }
    msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=text),
            MetadataContent(type="metadata", metadata=meta_dict),
        ],
    )
    return msg, meta_dict


def build_bounty_form_card() -> tuple[ChatMessage, dict, dict]:
    payload = {
        "title": "Submit Open-Source Bug Bounty Issue",
        "subtitle": "PatchBounty reproduces failing tests in a clean Python sandbox, runs 3 parallel solver uAgents, and escrows TESTFET on Dorado.",
        "submit_label": "Reproduce Bug & Launch 3 Solver uAgents",
        "fields": [
            {
                "name": "target_repo",
                "label": "Target Repository / Bounty Issue",
                "type": "select",
                "required": True,
                "options": [
                    {
                        "label": "fintech-core/ledger-settlement #418 (Float Drift & Refund Exploit)",
                        "value": "payment-ledger-rounding",
                    },
                    {
                        "label": "auth-gateway/token-guard #904 (JWT alg:none & Expiry Bypass)",
                        "value": "jwt-session-validator",
                    },
                    {
                        "label": "api-edge/sliding-limiter #267 (ZeroDivision & Burst Leak)",
                        "value": "rate-limiter-window",
                    },
                ],
            },
            {
                "name": "verification_policy",
                "label": "Sandbox Verification Gate",
                "type": "text",
                "required": True,
                "default": "100% pytest pass + Clean AST Security Audit",
            },
            {
                "name": "bounty_fet",
                "label": "On-Chain Bounty Reward (TESTFET)",
                "type": "number",
                "required": True,
                "default": "0.05",
            },
        ],
    }
    msg, raw = make_acp_card_message(
        "Complete the structured ASI:One Bug Bounty Form Card below to run real sandboxed reproduction and parallel solver synthesis:",
        "form",
        payload,
    )
    return msg, payload, raw


def build_patches_carousel_card(repro: dict, patches: list[dict]) -> tuple[ChatMessage, dict, dict]:
    payload = {
        "title": f"Verified Candidate Patches — {repro['repo_slug']} {repro['issue_number']}",
        "subtitle": f"Baseline: {repro['failed']}/{repro['total']} FAILED -> All {len(patches)} Solver Patches Verified 100% Passing",
        "items": [
            {
                "id": p["id"],
                "lane": p["lane"],
                "title": p["name"],
                "solver_agent": p["solver_agent_name"],
                "solver_wallet": p["solver_wallet"],
                "badge_pass": f"{p['passed']}/{p['total']} Pytest Passed ({p['duration_ms']}ms)",
                "badge_rank": "Recommended #1" if p["rank"] == 1 else f"Rank #{p['rank']} • Score {p['score']}",
                "diff_stats": f"+{p['lines_added']} / -{p['lines_removed']} lines • {p['ast_note']}",
                "rationale": p["rationale"],
                "cta_label": "Inspect Unified Diff ->",
                "action_payload": {"action": "select_patch", "patch_id": p["id"]},
            }
            for p in patches
        ],
    }
    best = patches[0]
    summary = (
        f"Reproduced {repro['failed']}/{repro['total']} failing pytest assertions on {repro['repo_slug']} {repro['issue_number']}, "
        f"then verified 3 parallel solver uAgent patches in isolated sandboxes. Top candidate: {best['name']} "
        f"({best['passed']}/{best['total']} tests passed in {best['duration_ms']}ms, {best['ast_note']}). Select a candidate card below:"
    )
    msg, raw = make_acp_card_message(summary, "carousel", payload)
    return msg, payload, raw


def build_patch_detail_card(repro: dict, patch: dict) -> tuple[ChatMessage, dict, dict]:
    payload = {
        "patch_id": patch["id"],
        "title": f"{patch['name']} ({patch['solver_agent_name']})",
        "subtitle": f"{repro['repo_slug']} {repro['issue_number']} • {patch['passed']}/{patch['total']} Passed • +{patch['lines_added']}/-{patch['lines_removed']} lines",
        "unified_diff": patch["unified_diff"],
        "rows": [
            {"label": "Winning Solver uAgent", "value": patch["solver_agent_name"]},
            {"label": "Recipient Dorado Wallet", "value": f"{patch['solver_wallet'][:14]}...{patch['solver_wallet'][-8:]}"},
            {"label": "Sandbox Pytest Verdict", "value": f"{patch['passed']}/{patch['total']} Passed ({patch['duration_ms']} ms)"},
            {"label": "Static Security Check", "value": patch["ast_note"]},
        ],
        "sub_options": {
            "name": "merge_mode",
            "label": "Select Repository Merge Target",
            "choices": [
                {"label": "Squash & Merge to main + Export .patch", "value": "Squash & Merge (main)"},
                {"label": "Open Signed PR Branch fix/patchbounty", "value": "Signed PR Branch"},
                {"label": "Hotfix Release Tag v1.0.1-security", "value": "Hotfix Release Tag"},
            ],
        },
        "cta_label": "Proceed to Bounty Payout Review ->",
    }
    msg, raw = make_acp_card_message(
        f"Inspecting verified unified git diff from {patch['solver_agent_name']}. Choose your merge target below to review on-chain bounty release:",
        "detail",
        payload,
    )
    return msg, payload, raw


def build_bounty_review_card(
    repro: dict, patch: dict, merge_mode: str, amount_fet: str
) -> tuple[ChatMessage, dict, dict]:
    w = patch["solver_wallet"]
    payload = {
        "patch_id": patch["id"],
        "merge_mode": merge_mode,
        "title": "Human Maintainer Bounty Payout Sign-Off",
        "subtitle": "Authorizes real Fetch Dorado TESTFET payout directly to the winning Solver uAgent's fetch1... wallet.",
        "summary_rows": [
            {"label": "Repository & Issue", "value": f"{repro['repo_slug']} {repro['issue_number']}"},
            {"label": "Verified Solver Winner", "value": f"{patch['name']} ({patch['solver_agent_name']})"},
            {"label": "Merge Strategy", "value": merge_mode},
            {"label": "Bounty Escrow Release", "value": f"{amount_fet} TESTFET (fet_direct)"},
            {"label": "Solver Dorado Wallet", "value": f"{w[:14]}...{w[-8:]}"},
        ],
        "approve_label": f"Approve & Pay {amount_fet} FET Bounty",
        "cancel_label": "Cancel Payout",
    }
    msg, raw = make_acp_card_message(
        f"Ready to release {amount_fet} TESTFET bounty directly to {patch['solver_agent_name']} ({w[:14]}...{w[-8:]}). Confirm human sign-off below:",
        "review",
        payload,
    )
    return msg, payload, raw


def parse_card_or_text_response(raw_input: str) -> dict:
    cleaned = raw_input.strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "action" in parsed:
            return parsed
    except Exception:
        pass

    lower = cleaned.lower()
    if lower in {"form", "bounty form", "guided form"}:
        return {"action": "open_form"}

    for solver_id in ("solver_alpha", "solver_beta", "solver_gamma"):
        if solver_id in lower:
            if "approve" in lower or "payout" in lower or "escrow" in lower:
                return {
                    "action": "approve_bounty",
                    "patch_id": solver_id,
                    "merge_mode": "Squash & Merge (main)",
                }
            if "confirm" in lower or "merge" in lower:
                return {
                    "action": "confirm_merge_mode",
                    "patch_id": solver_id,
                    "merge_mode": "Squash & Merge (main)",
                }
            return {"action": "select_patch", "patch_id": solver_id}

    if lower in {"cancel", "cancel payout"}:
        return {"action": "cancel_bounty"}

    return {"action": "new_bug_report", "raw_text": cleaned}


def build_git_patch_artifact(
    reference: str, repro: dict, patch: dict, tx_hash: str, block_height: int
) -> str:
    header = [
        f"From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001",
        f"From: {patch['solver_agent_name']} <{patch['solver_agent_name']}@fetch.ai>",
        f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')}",
        f"Subject: [PATCH] Fix {repro['repo_slug']} {repro['issue_number']} — {repro['title']}",
        "",
        f"PatchBounty Reference: {reference}",
        f"Sandbox Verification: {patch['passed']}/{patch['total']} pytest passed in {patch['duration_ms']}ms ({patch['ast_note']})",
        f"Solver Fetch Dorado Wallet: {patch['solver_wallet']}",
        f"Verified Fetch Dorado TX Hash: {tx_hash} (Block #{block_height})",
        "---",
        patch["unified_diff"],
    ]
    return "\n".join(header)
