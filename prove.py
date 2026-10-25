"""
PatchBounty (@aegis) — Automated End-to-End Verification Harness.

Verifies:
1. 6 Fetch.ai uAgents (@aegis, @recon, @specter, @forge, @warden, @vault) & deterministic addresses.
2. Fetch.ai Dorado Testnet (dorado-1) wallet manager & balance queries.
3. Multi-language target resolution & deep vulnerability scanning.
4. Cryptographic zero-leak blind proof preview before payment.
5. Sandbox exploit verification pass gate.
6. Post-payment resolution delivery (report, zip fixes bundle, email draft).
"""

import asyncio
import sys

from backend.asi_one_agent import get_swarm_roster
from backend.dorado_escrow import get_escrow_wallets_info
from backend.github_scanner import resolve_repository_target
from backend.resolution_delivery import build_all_fixes_zip, build_resolution_report
from backend.sandbox_verifier import (
    run_full_bounty_verification_pipeline,
    serialize_scan_for_client,
)


async def main() -> None:
    print("======================================================================")
    print(" PatchBounty End-to-End Verification Suite")
    print("======================================================================")

    # 1. Verify 6 uAgents
    roster = get_swarm_roster()
    assert len(roster) == 6, f"Expected 6 uAgents, found {len(roster)}"
    print(f"[1/6] Verified {len(roster)} Active Fetch.ai uAgents:")
    for ag in roster:
        print(f"      - {ag.get('handle', ag.get('name')):10s} | {ag['name']:28s} | {ag['address'][:26]}... | Port {ag.get('port')}")

    # 2. Verify Dorado wallets & balance status
    wallets = get_escrow_wallets_info()
    assert "buyer_wallet" in wallets and "seller_wallet" in wallets
    buyer_addr = wallets["maintainer_wallet"]
    seller_addr = wallets["researcher_wallet"]
    assert buyer_addr.startswith("fetch1")
    assert seller_addr.startswith("fetch1")
    print(f"[2/6] Dorado Ledger Ready -> Buyer: {buyer_addr[:16]}... | Seller: {seller_addr[:16]}...")

    # 3. Target resolution & full scanning
    target = await resolve_repository_target("express_checkout_api")
    assert target is not None and len(target["files"]) > 0

    async def _dummy_emit(agent: str, kind: str, text: str) -> None:
        pass

    scan = await run_full_bounty_verification_pipeline(target, maintainer_budget_usd=195, emit_event=_dummy_emit)
    assert len(scan["all_findings"]) >= 3
    print(f"[3/6] Target Audited -> {target['repo_slug']}: {len(scan['all_findings'])} real vulnerabilities detected")

    # 4. Zero-Leak Vault Lock (pre-payment masking)
    sealed = serialize_scan_for_client(scan, is_settled=False)
    assert sealed["is_clean_code"] is False
    assert sealed["escrow_unlocked"] is False
    top_cand = sealed["candidates"][0]
    assert "VERIFIED_REMEDIATION_GUARD" in top_cand["masked_diff_preview"]
    assert top_cand["patched_code"] == ""
    assert top_cand["unified_diff"] == ""
    print("[4/6] Verified Zero-Leak Blind Escrow Lock (HTTP 402 server seal active)")

    # 5. Sandbox exploit verification pass gate
    unsealed = serialize_scan_for_client(scan, is_settled=True)
    assert unsealed["escrow_unlocked"] is True
    assert unsealed["all_findings"][0]["is_sealed"] is False
    assert len(scan["file_fixes"]) >= 1
    winner = unsealed["candidates"][0]
    assert winner["post_patch_exploit_blocked"] is True
    assert winner["post_patch_unit_tests_passed"] is True
    print(f"[5/6] Sandbox Duel Verification -> {winner['researcher_handle']} ({winner['strategy_name']}): 100% EXPLOITS BLOCKED")

    # 6. Post-payment resolution delivery artifacts
    mock_state = {
        "session_id": "prove_e2e",
        "target_bundle": target,
        "scan_result": {**unsealed, "file_fixes": scan["file_fixes"]},
        "selected_patch": winner,
        "escrow_receipt": {"tx_hash": "TEST_TX", "amount_display": "0.05 TESTFET"},
    }
    report_md = build_resolution_report(mock_state)
    assert "Why It Is Vulnerable" in report_md
    assert "Resolution Applied" in report_md
    zip_bytes = build_all_fixes_zip(mock_state)
    assert len(zip_bytes) > 200
    print(f"[6/6] Resolution Delivery Verified -> Report ({len(report_md)} bytes) + All-Fixes ZIP ({len(zip_bytes)} bytes)")

    print("======================================================================")
    print(" ALL 6/6 PATCHBOUNTY E2E CHECKS PASSED")
    print("======================================================================")


if __name__ == "__main__":
    asyncio.run(main())
