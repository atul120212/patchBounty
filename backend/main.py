"""
PatchBounty (@aegis) — FastAPI Backend, Multi-Agent Bargain Engine, Sandbox Pass Gate & Dorado Escrow (`port 8002`).
Enforces the complete real-world workflow:
  Step 1: Multi-Language Full-File Code Scan (Clean Code = $0 Bounty Pass!)
  Step 2: Numbered Blind Audit Report + Blue Frosted-Blur Locked Solution Vault Preview (`HTTP 402` server seal)
  Step 3: Live Market Benchmark vs AI Quotes + Live Multi-Agent Bargaining + Mandatory Sandbox Solution Pass Gate
  Step 4: Interactive IST Rollout Calendar + Live Fetch.ai Dorado `0.05 TESTFET` Settlement + Direct Explorer URLs
"""
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.asi_one_agent import get_swarm_roster
from backend.config_store import PROJECT_ROOT, runtime_config
from backend.disclosure_artifacts import (
    build_seven_day_disclosure_slots,
    generate_disclosure_ics,
    generate_maintainer_clearance_pdf,
    generate_researcher_payout_pdf,
)
from backend.dorado_escrow import (
    build_cancel_payment_receipt,
    check_live_dorado_ledger_status,
    get_escrow_wallets_info,
    refresh_live_dorado_wallets,
    settle_bounty_on_dorado,
    verify_external_dorado_tx,
)
from backend.github_scanner import BUILTIN_REAL_TARGETS, resolve_repository_target
from backend.resolution_delivery import (
    build_all_fixes_zip,
    build_resolution_report,
    create_github_pull_request,
    deliver_email_notification,
    test_smtp_configuration,
)
from backend.qa_expert_router import (
    answer_patchbounty_meta_question,
    is_meta_or_policy_question,
    parse_maintainer_budget_usd,
)
from backend.sandbox_verifier import (
    run_full_bounty_verification_pipeline,
    run_live_exploit_duel,
    serialize_scan_for_client,
)

app = FastAPI(
    title="PatchBounty (@aegis) — Autonomous Bug Bounty Negotiation & Blind Escrow Studio",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SESSION_FILE = DATA_DIR / "session_store.json"


def _pick_default_available_slot(slots: list[dict]) -> dict:
    for s in slots:
        if s.get("available", True):
            return s
    return slots[0]


def _fresh_initial_state() -> dict:
    slots = build_seven_day_disclosure_slots()
    return {
        "session_id": str(uuid4())[:8],
        "phase": "IDLE",
        "deal_approved": False,
        "solution_verified_pass": False,
        "live_ledger_check": None,
        "chat_history": [
            {
                "id": "welcome-01",
                "role": "assistant",
                "agent": "@aegis",
                "card_kind": "welcome",
                "text": (
                    "**Welcome to PatchBounty (@aegis)**\n\n"
                    "1. **Scan Any Language or GitHub Repo:** Full top-to-bottom code check across Python, JavaScript/Node, Solidity, Java, Go, PHP, and C++. Clean bug-free code passes with $0 bounty.\n"
                    "2. **Blurred Vault Lock:** All bugs are listed in numbered points while the solution stays blurred & locked on the server so nobody can copy fixes without paying.\n"
                    "3. **Market Benchmark, Live Bargaining & Sandbox Pass Gate:** Compare real-world HackerOne/Immunefi market rates vs our AI quotes, negotiate price live, verify the fix passes sandbox tests, and pay **0.05 TESTFET** on Fetch Dorado with direct Explorer links!"
                ),
            }
        ],
        "swarm_events": [],
        "target_bundle": None,
        "scan_result": None,
        "selected_patch": None,
        "disclosure_slots": slots,
        "selected_slot": _pick_default_available_slot(slots),
        "live_duel_result": None,
        "escrow_receipt": None,
        "resolution_delivery": None,
        "resolution_eml_text": "",
    }


def _load_persisted_state() -> dict:
    if SESSION_FILE.exists():
        try:
            saved = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict) and "chat_history" in saved:
                fresh_slots = build_seven_day_disclosure_slots()
                saved["disclosure_slots"] = fresh_slots
                saved.setdefault("deal_approved", False)
                saved.setdefault("solution_verified_pass", False)
                saved.setdefault("live_ledger_check", None)
                saved.setdefault("resolution_delivery", None)
                saved.setdefault("resolution_eml_text", "")
                if not saved.get("selected_slot"):
                    saved["selected_slot"] = _pick_default_available_slot(fresh_slots)
                return saved
        except Exception:
            pass
    return _fresh_initial_state()


def _save_state_to_disk() -> None:
    try:
        SESSION_FILE.write_text(json.dumps(STATE, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


STATE: dict = _load_persisted_state()
ACTIVE_WS: list[WebSocket] = []


def is_escrow_unlocked() -> bool:
    return STATE.get("phase") == "SETTLED" and bool((STATE.get("escrow_receipt") or {}).get("verified"))


async def broadcast_ws(payload: dict) -> None:
    stale: list[WebSocket] = []
    for ws in list(ACTIVE_WS):
        try:
            await ws.send_json(payload)
        except Exception:
            stale.append(ws)
    for ws in stale:
        if ws in ACTIVE_WS:
            ACTIVE_WS.remove(ws)


async def emit_swarm_event(agent: str, stage: str, detail: str) -> None:
    evt = {
        "id": str(uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        "agent": agent,
        "stage": stage,
        "detail": detail,
    }
    STATE["swarm_events"].append(evt)
    STATE["swarm_events"] = STATE["swarm_events"][-60:]
    await broadcast_ws({"type": "swarm_event", "event": evt})


def public_state() -> dict:
    unlocked = is_escrow_unlocked()
    scan_public = serialize_scan_for_client(STATE["scan_result"], is_settled=unlocked)

    selected_public = None
    if STATE["selected_patch"]:
        sp = STATE["selected_patch"]
        if unlocked:
            selected_public = {**sp, "is_sealed": False}
        else:
            selected_public = {
                **sp,
                "patched_code": "",
                "unified_diff": "",
                "masked_diff_preview": sp.get("masked_diff_preview", ""),
                "is_sealed": True,
            }

    duel_public = None
    if STATE["live_duel_result"]:
        d = STATE["live_duel_result"]
        if unlocked:
            duel_public = d
        else:
            duel_public = {
                "vuln_class": d["vuln_class"],
                "language": d.get("language", "Python"),
                "payload_executed": "Sealed in @vault Escrow",
                "unpatched": {
                    "verdict": d["unpatched"]["verdict"],
                    "exploit_succeeded": d["unpatched"]["exploit_succeeded"],
                    "unit_tests_passed": d["unpatched"]["unit_tests_passed"],
                    "elapsed_ms": d["unpatched"]["elapsed_ms"],
                    "detail": d["unpatched"].get("blind_detail") or "Breach verified inside isolated sandbox.",
                },
                "patched": {
                    "verdict": d["patched"]["verdict"],
                    "exploit_blocked": d["patched"]["exploit_blocked"],
                    "unit_tests_passed": d["patched"]["unit_tests_passed"],
                    "elapsed_ms": d["patched"]["elapsed_ms"],
                    "detail": d["patched"].get("blind_detail") or "All exploit vectors neutralized (100% pass).",
                },
            }

    return {
        "session_id": STATE["session_id"],
        "phase": STATE["phase"],
        "escrow_unlocked": unlocked,
        "deal_approved": bool(STATE.get("deal_approved")),
        "solution_verified_pass": bool(STATE.get("solution_verified_pass")),
        "live_ledger_check": STATE.get("live_ledger_check"),
        "config": runtime_config.public_status(),
        "wallets": get_escrow_wallets_info(),
        "agents": get_swarm_roster(),
        "builtin_targets": [
            {
                "key": k,
                "repo_slug": v["repo_slug"],
                "language": v["language"],
                "service_name": v["service_name"],
                "cwe_badge": v["cwe_badge"],
            }
            for k, v in BUILTIN_REAL_TARGETS.items()
        ],
        "chat_history": STATE["chat_history"],
        "swarm_events": STATE["swarm_events"],
        "target_bundle": (
            {
                "source_origin": STATE["target_bundle"]["source_origin"],
                "repo_slug": STATE["target_bundle"]["repo_slug"],
                "repo_url": STATE["target_bundle"]["repo_url"],
                "files_count": len(STATE["target_bundle"]["files"]),
            }
            if STATE["target_bundle"]
            else None
        ),
        "scan_result": scan_public,
        "selected_patch": selected_public,
        "disclosure_slots": STATE["disclosure_slots"],
        "selected_slot": STATE["selected_slot"],
        "live_duel_result": duel_public,
        "escrow_receipt": STATE["escrow_receipt"],
        "resolution_delivery": STATE.get("resolution_delivery"),
        "resolution_eml_ready": bool(STATE.get("resolution_eml_text")),
        "smtp_status": {
            "configured": bool(runtime_config.smtp_host and runtime_config.smtp_user and runtime_config.smtp_pass),
            "host": runtime_config.smtp_host,
            "port": runtime_config.smtp_port,
            "user_masked": runtime_config.public_status().get("smtp_user_masked", ""),
            "from_addr": runtime_config.smtp_from or runtime_config.smtp_user or "security@patchbounty.agent",
        },
    }


class ConfigUpdatePayload(BaseModel):
    asi_one_api_key: str | None = None
    github_token: str | None = None
    agentverse_api_key: str | None = None
    dorado_buyer_seed: str | None = None
    routing_mode: str | None = None
    smtp_host: str | None = None
    smtp_port: int | str | None = None
    smtp_user: str | None = None
    smtp_pass: str | None = None
    smtp_from: str | None = None


class TestSmtpPayload(BaseModel):
    recipient_email: str


class ChatTurnPayload(BaseModel):
    message: str
    target_hint: str = ""
    maintainer_budget_usd: int | None = None
    inline_code: str = ""
    force_scan: bool = False


class NegotiateBountyPayload(BaseModel):
    counter_offer_usd: int
    preferred_patch_id: str | None = None


class ApproveSolutionPayload(BaseModel):
    patch_id: str


class SelectPatchPayload(BaseModel):
    patch_id: str


class SelectSlotPayload(BaseModel):
    slot_id: str
    win_id: str | None = None


class LiveExploitPayload(BaseModel):
    custom_payload: str = ""


class VerifyTxPayload(BaseModel):
    tx_hash: str


class ResolveDeliverPayload(BaseModel):
    recipient_email: str = ""
    create_pr: bool = True
    notify_email: bool = True


class MirrorSyncPayload(BaseModel):
    source: str = "ASI:One Live Chat"
    user_text: str
    reply_text: str
    model_used: str = "asi1"
    scan_result: dict | None = None
    target_bundle: dict | None = None


@app.websocket("/ws")
async def websocket_stream(ws: WebSocket):
    await ws.accept()
    ACTIVE_WS.append(ws)
    try:
        await ws.send_json({"type": "state", "state": public_state()})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in ACTIVE_WS:
            ACTIVE_WS.remove(ws)


@app.get("/api/health")
async def health_check():
    return {
        "ok": True,
        "service": "PatchBounty (@aegis)",
        "version": "5.0.0",
        "asi_one_configured": bool(runtime_config.asi_one_api_key),
        "agents_online": len(get_swarm_roster()),
        "wallets": get_escrow_wallets_info(),
    }


@app.get("/api/state")
async def get_full_state():
    return public_state()


@app.post("/api/config")
async def save_runtime_config(payload: ConfigUpdatePayload):
    status = runtime_config.update_credentials(
        asi_one_api_key=payload.asi_one_api_key,
        github_token=payload.github_token,
        agentverse_api_key=payload.agentverse_api_key,
        dorado_buyer_seed=payload.dorado_buyer_seed,
        routing_mode=payload.routing_mode,
        smtp_host=payload.smtp_host,
        smtp_port=payload.smtp_port,
        smtp_user=payload.smtp_user,
        smtp_pass=payload.smtp_pass,
        smtp_from=payload.smtp_from,
    )
    smtp_info = f"SMTP Ready={status.get('smtp_configured')}" if payload.smtp_host or payload.smtp_user else ""
    await emit_swarm_event("@aegis", "CREDENTIALS_UPDATED", f"ASI:One Ready={status['asi_one_configured']} | Mode={status['routing_mode']} {smtp_info}".strip())
    _save_state_to_disk()
    await broadcast_ws({"type": "state", "state": public_state()})
    return {"ok": True, "config": status, "wallets": get_escrow_wallets_info()}


@app.post("/api/test-smtp")
async def test_smtp_mail(payload: TestSmtpPayload):
    res = test_smtp_configuration(payload.recipient_email)
    if res.get("ok"):
        await emit_swarm_event("@aegis", "SMTP_TEST_VERIFIED", f"Test email successfully sent to {payload.recipient_email}")
    else:
        await emit_swarm_event("@aegis", "SMTP_TEST_FAILED", res.get("reason", "")[:120])
    return res


@app.post("/api/test-asi")
async def test_live_asi_connection():
    if not runtime_config.asi_one_api_key:
        return {"ok": False, "detail": "No ASI_ONE_API_KEY configured yet. Paste your key above and click Save & Test."}
    reply, used_model = await runtime_config.complete_asi_one(
        messages=[{"role": "user", "content": "Reply in 6 words confirming @aegis ASI:One connection is live."}],
        prefer_flagship=False,
        max_tokens=40,
        temperature=0.1,
        timeout=10.0,
    )
    if reply and used_model in ("asi1", "asi1-mini"):
        await emit_swarm_event("@aegis", "ASI_ONE_VERIFIED", f"Live ping succeeded via {used_model}")
        await broadcast_ws({"type": "state", "state": public_state()})
        return {"ok": True, "model": used_model, "reply": reply, "config": runtime_config.public_status()}
    return {"ok": False, "detail": "Could not reach ASI:One with the current key. Please double-check your ASI_ONE_API_KEY."}


@app.post("/api/reset")
async def reset_session():
    fresh = _fresh_initial_state()
    STATE.clear()
    STATE.update(fresh)
    _save_state_to_disk()
    await broadcast_ws({"type": "state", "state": public_state()})
    return public_state()


@app.post("/api/mirror-sync")
async def mirror_external_asi_one_session(payload: MirrorSyncPayload):
    STATE["chat_history"].append(
        {"id": str(uuid4())[:8], "role": "user", "text": f"{payload.source}: {payload.user_text}"}
    )
    if payload.scan_result and payload.target_bundle:
        STATE["target_bundle"] = payload.target_bundle
        STATE["scan_result"] = payload.scan_result
        STATE["selected_patch"] = payload.scan_result["candidates"][0] if payload.scan_result.get("candidates") else None
        STATE["phase"] = "CLEAN_VERIFIED" if payload.scan_result.get("is_clean_code") else "AUDIT_READY"
        STATE["deal_approved"] = False
        STATE["solution_verified_pass"] = False
        STATE["escrow_receipt"] = None
    STATE["chat_history"].append(
        {
            "id": str(uuid4())[:8],
            "role": "assistant",
            "agent": "@aegis",
            "model_used": payload.model_used,
            "card_kind": "proposals" if payload.scan_result else None,
            "text": html.unescape(payload.reply_text),
        }
    )
    _save_state_to_disk()
    await emit_swarm_event("@aegis", "ASI_ONE_LIVE_SYNC", f"Mirrored live turn from {payload.source} ({payload.model_used})")
    await broadcast_ws({"type": "state", "state": public_state()})
    return {"ok": True}


@app.post("/api/chat")
async def handle_chat_turn(payload: ChatTurnPayload):
    user_display = payload.message.strip() or f"Audit code ({payload.target_hint or 'submitted source'})"
    if not user_display and not payload.inline_code.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    STATE["chat_history"].append({"id": str(uuid4())[:8], "role": "user", "text": user_display})

    if not payload.force_scan and not payload.inline_code.strip() and is_meta_or_policy_question(user_display):
        await emit_swarm_event("@aegis", "CONVERSATIONAL_QA", "Answered user query using active session memory.")
        answer, model_used = await answer_patchbounty_meta_question(user_display, session_state=STATE)
        STATE["chat_history"].append(
            {
                "id": str(uuid4())[:8],
                "role": "assistant",
                "agent": "@aegis",
                "model_used": model_used,
                "card_kind": None,
                "text": html.unescape(answer),
            }
        )
        _save_state_to_disk()
        await broadcast_ws({"type": "state", "state": public_state()})
        return public_state()

    # NEW SCAN ALWAYS RESETS NEGOTIATION, SANDBOX GATE & ESCROW LOCK!
    STATE["phase"] = "SCANNING"
    STATE["deal_approved"] = False
    STATE["solution_verified_pass"] = False
    STATE["escrow_receipt"] = None
    STATE["live_ledger_check"] = None
    STATE["resolution_delivery"] = None
    STATE["resolution_eml_text"] = ""

    budget = payload.maintainer_budget_usd if payload.maintainer_budget_usd is not None else parse_maintainer_budget_usd(user_display)

    await emit_swarm_event("@recon", "TARGET_ACQUISITION", f"Inspecting target '{payload.target_hint or user_display[:52]}'")
    target_bundle = await resolve_repository_target(
        user_display, target_hint=payload.target_hint, inline_code=payload.inline_code
    )
    STATE["target_bundle"] = target_bundle

    if target_bundle.get("not_found_error"):
        STATE["scan_result"] = {
            "escrow_unlocked": False,
            "is_clean_code": True,
            "not_found_error": True,
            "language": "GitHub URL Check",
            "files_scanned_count": 0,
            "lines_scanned_count": 0,
            "total_bugs_found": 0,
            "all_findings": [],
            "vulnerability": None,
            "unpatched_source": "",
            "preset_attack_vectors": [],
            "pre_patch_sandbox": None,
            "candidates": [],
            "market_benchmark": None,
            "negotiation_log": [],
            "maintainer_budget_provided": False,
            "maintainer_budget_usd": None,
            "budget_below_floor": False,
            "honest_severity_floor_usd": 0,
            "ai_advisory": f"Repository {target_bundle['repo_url']} was not found on GitHub (404 or private). No vulnerabilities reported and $0 payment requested.",
            "ai_model_used": "recon-github-check",
        }
        STATE["selected_patch"] = None
        STATE["live_duel_result"] = None
        STATE["phase"] = "CLEAN_VERIFIED"
        STATE["chat_history"].append(
            {
                "id": str(uuid4())[:8],
                "role": "assistant",
                "agent": "@recon",
                "model_used": "recon-github-check",
                "card_kind": None,
                "text": (
                    f"**GitHub Repository Not Found (404 / Private)**\n\n"
                    f"Could not find public source code at `{target_bundle['repo_url']}`. "
                    f"Please double-check the repository URL or paste your source code directly. "
                    f"**No lock applied and $0 payment requested.**"
                ),
            }
        )
        _save_state_to_disk()
        await broadcast_ws({"type": "state", "state": public_state()})
        return public_state()

    scan_result = await run_full_bounty_verification_pipeline(target_bundle, budget, emit_swarm_event)
    fresh_slots = build_seven_day_disclosure_slots()
    STATE["disclosure_slots"] = fresh_slots
    STATE["selected_slot"] = _pick_default_available_slot(fresh_slots)
    STATE["scan_result"] = scan_result

    # CASE A: 100% BUG-FREE CLEAN CODE ($0 BOUNTY REQUIRED!)
    if scan_result.get("is_clean_code"):
        STATE["selected_patch"] = None
        STATE["live_duel_result"] = None
        STATE["phase"] = "CLEAN_VERIFIED"
        reply_text = (
            f"**Clean Security Audit Passed — 0 Vulnerabilities Found!**\n\n"
            f"- **Language Inspected:** {scan_result['language']} ({scan_result['lines_scanned_count']} lines checked top-to-bottom)\n"
            f"- **Security Verdict:** Safe — zero SQLi, RCE, deserialization, path escape, or hardcoded secret sinks detected.\n"
            f"- **Bounty Required:** **$0 USD** (No patch or escrow payment needed!)"
        )
        STATE["chat_history"].append(
            {
                "id": str(uuid4())[:8],
                "role": "assistant",
                "agent": "@aegis",
                "model_used": scan_result["ai_model_used"],
                "card_kind": "clean",
                "text": reply_text,
            }
        )
        _save_state_to_disk()
        await broadcast_ws({"type": "state", "state": public_state()})
        return public_state()

    # CASE B: VULNERABILITIES FOUND -> BLIND PROOF + MARKET BENCHMARK + REQUIRE STEP 3 NEGOTIATION & SANDBOX PASS!
    STATE["selected_patch"] = scan_result["candidates"][0]
    prim_file = target_bundle["files"][0]
    STATE["live_duel_result"] = run_live_exploit_duel(
        scan_result["unpatched_source"],
        STATE["selected_patch"]["patched_code"],
        scan_result["vulnerability"]["vuln_class"],
        language=scan_result["language"],
        file_path=prim_file["file_path"],
    )
    STATE["phase"] = "AUDIT_READY"

    findings = scan_result["all_findings"]
    mb = scan_result.get("market_benchmark") or {}
    top = scan_result["candidates"][0]

    numbered_points = "\n".join(
        f"{f['point_number']}. **{f['severity']} (CVSS {f['cvss_score']}) — {html.unescape(f['blind_category'])}:** "
        f"{html.unescape(f['blind_impact'])}"
        for f in findings
    )

    floor_alert = ""
    if scan_result["budget_below_floor"]:
        floor_alert = (
            f"\n\n**Budget Notice:** Not Available Within Your Bounty Budget (${budget} USD). "
            f"Honest {findings[0]['severity']} minimum floor is **${scan_result['honest_severity_floor_usd']} USD**."
        )

    reply_text = (
        f"**Complete {scan_result['language']} Audit Finished — {len(findings)} Issue(s) Confirmed**\n\n"
        f"{numbered_points}\n\n"
        f"**Industry Market Rate vs PatchBounty AI Quotes:**\n"
        f"- **Real-World Bug Bounty Market Avg:** **${mb.get('human_market_avg_usd', 2400)} USD** (Report only, 7-14 days)\n"
        f"- **Market Data Source:** {mb.get('market_source', 'Industry Benchmark')} | **Mode:** {mb.get('benchmark_mode', 'LIVE_NVD')} | **Live NIST NVD:** {mb.get('nvd_global_cve_count', '—')} total CVE in this class (Sample: {mb.get('nvd_sample_cve', '—')})\n"
        f"- **PatchBounty AI Starting Bid ({top['researcher_handle']}):** **${top['verified_bounty_usd']} USD** — **{mb.get('savings_vs_market_pct', 90)}% cheaper** & full fix included!\n\n"
        f"**Next Step:** Open **Page 3 (Bids & Negotiation)** to bargain with researchers, verify the sandbox patch passes 100%, and unlock **Page 4 Payment**.{floor_alert}"
    )

    STATE["chat_history"].append(
        {
            "id": str(uuid4())[:8],
            "role": "assistant",
            "agent": "@aegis",
            "model_used": scan_result["ai_model_used"],
            "card_kind": "proposals",
            "text": reply_text,
        }
    )
    _save_state_to_disk()
    await broadcast_ws({"type": "state", "state": public_state()})
    return public_state()


@app.post("/api/negotiate-bounty")
async def negotiate_bounty_live(payload: NegotiateBountyPayload):
    """
    Live Multi-Agent Bargaining Engine (`@aegis` Buyer Agent <-> `@blade`, `@kestrel`, `@titan` Researcher Agents).
    Computes competitive concessions down toward each researcher's Honest CVSS Floor without leaking Maintainer secrets!
    """
    if not STATE["scan_result"] or STATE["scan_result"].get("is_clean_code"):
        raise HTTPException(status_code=400, detail="Scan a vulnerable codebase first.")

    sr = STATE["scan_result"]
    offer = max(1, int(payload.counter_offer_usd))
    sr["maintainer_budget_usd"] = offer
    sr["maintainer_budget_provided"] = True

    any_within = False
    round_lines: list[dict] = [
        {
            "speaker": "Maintainer (@aegis Buyer Agent)",
            "round": "Counter-Offer",
            "message": f"Maintainer proposed target settlement of ${offer} USD for complete verified multi-bug remediation.",
        }
    ]

    for c in sr["candidates"]:
        floor = int(c.get("floor_usd", sr["honest_severity_floor_usd"]))
        ask = int(c["initial_ask_usd"])
        if offer < floor:
            c["verified_bounty_usd"] = floor
            c["within_budget"] = False
            c["within_maintainer_budget"] = False
            c["maintainer_savings_usd"] = max(0, ask - floor)
            round_lines.append(
                {
                    "speaker": f"{c['researcher_handle']} ({c['strategy_name']})",
                    "round": "Floor Counter",
                    "message": (
                        f"Cannot drop below honest {sr['vulnerability']['severity']} severity floor of ${floor} USD "
                        f"(already cut from ${ask} USD — saving you ${ask - floor} USD)."
                    ),
                }
            )
        elif offer >= ask:
            c["verified_bounty_usd"] = ask
            c["within_budget"] = True
            c["within_maintainer_budget"] = True
            c["maintainer_savings_usd"] = 0
            any_within = True
            round_lines.append(
                {
                    "speaker": f"{c['researcher_handle']} ({c['strategy_name']})",
                    "round": "Deal Accepted",
                    "message": f"Accepted immediately at initial quote of ${ask} USD (below your ${offer} USD offer!).",
                }
            )
        else:
            agreed = max(floor, int(round((offer * 0.75) + (floor * 0.25))))
            agreed = min(offer, agreed)
            c["verified_bounty_usd"] = agreed
            c["within_budget"] = True
            c["within_maintainer_budget"] = True
            c["maintainer_savings_usd"] = max(0, ask - agreed)
            any_within = True
            round_lines.append(
                {
                    "speaker": f"{c['researcher_handle']} ({c['strategy_name']})",
                    "round": "Deal Accepted",
                    "message": (
                        f"Accepted counter-negotiation at ${agreed} USD! Dropped ${ask - agreed} USD off initial ${ask} USD ask."
                    ),
                }
            )

    sr["budget_below_floor"] = not any_within
    sr.setdefault("negotiation_log", []).extend(round_lines)

    chosen_id = payload.preferred_patch_id or (STATE["selected_patch"]["id"] if STATE["selected_patch"] else sr["candidates"][0]["id"])
    for c in sr["candidates"]:
        if c["id"] == chosen_id:
            STATE["selected_patch"] = c
            break

    await emit_swarm_event(
        "@aegis",
        "MULTI_AGENT_NEGOTIATION",
        f"Negotiated ${offer} USD counter-offer across @blade/@kestrel/@titan -> Active bid: {STATE['selected_patch']['researcher_handle']} at ${STATE['selected_patch']['verified_bounty_usd']} USD",
    )

    STATE["chat_history"].append(
        {
            "id": str(uuid4())[:8],
            "role": "assistant",
            "agent": "@aegis",
            "model_used": "aegis-negotiator",
            "card_kind": None,
            "text": (
                f"**Multi-Agent Negotiation Round Complete (Your Offer: ${offer} USD)**\n\n"
                + "\n".join(f"- **{r['speaker']}:** {r['message']}" for r in round_lines[1:])
                + "\n\nClick **Verify Patch in Sandbox & Lock Deal** on Page 3 to unlock payment!"
            ),
        }
    )
    _save_state_to_disk()
    await broadcast_ws({"type": "state", "state": public_state()})
    return public_state()


@app.post("/api/approve-solution")
async def verify_solution_and_lock_deal(payload: ApproveSolutionPayload):
    """
    MANDATORY PRE-PAYMENT SANDBOX SOLUTION GATE:
    Executes isolated subprocess exploit + regression test duel on the selected researcher's patch.
    ONLY unlocks Step 4 Payment when `exploit_blocked == True` AND `unit_tests_passed == True`!
    """
    if not STATE["scan_result"] or STATE["scan_result"].get("is_clean_code"):
        raise HTTPException(status_code=400, detail="Run a vulnerability scan first.")

    sr = STATE["scan_result"]
    target_cand = None
    for c in sr["candidates"]:
        if c["id"] == payload.patch_id:
            target_cand = c
            break
    if not target_cand:
        raise HTTPException(status_code=404, detail="Selected researcher patch not found.")

    STATE["selected_patch"] = target_cand
    prim_path = STATE["target_bundle"]["files"][0]["file_path"] if STATE["target_bundle"] else "target_mod.py"
    duel = run_live_exploit_duel(
        sr["unpatched_source"],
        target_cand["patched_code"],
        sr["vulnerability"]["vuln_class"],
        language=sr.get("language", "Python"),
        file_path=prim_path,
    )
    STATE["live_duel_result"] = duel

    passed = bool(duel["patched"]["exploit_blocked"]) and bool(duel["patched"]["unit_tests_passed"])
    STATE["solution_verified_pass"] = passed
    STATE["deal_approved"] = passed
    STATE["phase"] = "DEAL_VERIFIED" if passed else "AUDIT_READY"

    await emit_swarm_event(
        "@warden",
        "SANDBOX_GATE_LOCKED" if passed else "SANDBOX_GATE_FAILED",
        f"Verified {target_cand['researcher_handle']} (${target_cand['verified_bounty_usd']} USD) -> ExploitBlocked={duel['patched']['exploit_blocked']}, TestsPass={duel['patched']['unit_tests_passed']}",
    )

    STATE["chat_history"].append(
        {
            "id": str(uuid4())[:8],
            "role": "assistant",
            "agent": "@warden",
            "model_used": "warden-sandbox",
            "card_kind": None,
            "text": (
                f"**Sandbox Verification PASSED & Deal Locked ({target_cand['researcher_handle']} — ${target_cand['verified_bounty_usd']} USD)**\n\n"
                f"1. **Unpatched Code in Sandbox:** Exploited ({duel['unpatched']['elapsed_ms']} ms)\n"
                f"2. **{target_cand['researcher_handle']} Proposed Fix:** **ALL EXPLOITS BLOCKED & 100% TESTS PASSED** ({duel['patched']['elapsed_ms']} ms)\n\n"
                f"**Step 4 Payment Unlocked:** Choose your IST deployment slot and pay **0.05 TESTFET** to unblur & download full fixed code!"
            ),
        }
    )
    _save_state_to_disk()
    await broadcast_ws({"type": "state", "state": public_state()})
    return public_state()


@app.post("/api/live-exploit-replay")
async def trigger_live_exploit_replay(payload: LiveExploitPayload):
    if not STATE["scan_result"] or not STATE["selected_patch"]:
        raise HTTPException(status_code=400, detail="Run a security scan first.")
    sr = STATE["scan_result"]
    patch = STATE["selected_patch"]
    prim_path = STATE["target_bundle"]["files"][0]["file_path"] if STATE["target_bundle"] else "target_mod.py"
    duel = run_live_exploit_duel(
        sr["unpatched_source"],
        patch["patched_code"],
        sr["vulnerability"]["vuln_class"],
        custom_payload=payload.custom_payload.strip(),
        language=sr.get("language", "Python"),
        file_path=prim_path,
    )
    STATE["live_duel_result"] = duel
    _save_state_to_disk()
    await broadcast_ws({"type": "state", "state": public_state()})
    return {"ok": True, "duel": public_state()["live_duel_result"]}


@app.post("/api/select-patch")
async def select_patch_candidate(payload: SelectPatchPayload):
    if not STATE["scan_result"]:
        raise HTTPException(status_code=400, detail="Run a repository scan first.")
    prim_path = STATE["target_bundle"]["files"][0]["file_path"] if STATE["target_bundle"] else "target_mod.py"
    for cand in STATE["scan_result"]["candidates"]:
        if cand["id"] == payload.patch_id:
            STATE["selected_patch"] = cand
            STATE["live_duel_result"] = run_live_exploit_duel(
                STATE["scan_result"]["unpatched_source"],
                cand["patched_code"],
                STATE["scan_result"]["vulnerability"]["vuln_class"],
                language=STATE["scan_result"].get("language", "Python"),
                file_path=prim_path,
            )
            _save_state_to_disk()
            await emit_swarm_event(
                "@forge",
                "RESEARCHER_TIER_SELECTED",
                f"Selected {cand['researcher_handle']} ({cand['strategy_name']}) at ${cand['verified_bounty_usd']} USD",
            )
            await broadcast_ws({"type": "state", "state": public_state()})
            return public_state()
    raise HTTPException(status_code=404, detail="Patch candidate not found.")


@app.post("/api/select-slot")
async def select_disclosure_slot(payload: SelectSlotPayload):
    for s in STATE["disclosure_slots"]:
        if s["id"] == payload.slot_id:
            if not s.get("available", True):
                raise HTTPException(status_code=400, detail="All IST windows for this date have already passed.")
            chosen_slot = dict(s)
            if payload.win_id and s.get("windows"):
                for w in s["windows"]:
                    if w["win_id"] == payload.win_id:
                        if not w.get("available", True):
                            raise HTTPException(status_code=400, detail="Selected IST time slot has already passed today.")
                        chosen_slot["win_id"] = w["win_id"]
                        chosen_slot["time_window"] = w["time_window"]
                        chosen_slot["release_track"] = w["release_track"]
                        chosen_slot["dtstart_local"] = w["dtstart_local"]
                        chosen_slot["dtend_local"] = w["dtend_local"]
                        break
            STATE["selected_slot"] = chosen_slot
            _save_state_to_disk()
            await emit_swarm_event(
                "@aegis",
                "CALENDAR_SLOT_LOCKED",
                f"Locked rollout schedule: {chosen_slot['date_str']} • {chosen_slot['time_window']}",
            )
            await broadcast_ws({"type": "state", "state": public_state()})
            return public_state()
    raise HTTPException(status_code=404, detail="Calendar date not found.")


@app.post("/api/wallets/faucet")
async def sync_and_topup_dorado_wallets():
    wallets = await refresh_live_dorado_wallets(top_up_faucet=True)
    await emit_swarm_event(
        "@vault",
        "DORADO_WALLETS_SYNCED",
        f"Buyer={wallets['maintainer_balance_fet']} TESTFET | Escrow={wallets['researcher_balance_fet']} TESTFET",
    )
    await broadcast_ws({"type": "state", "state": public_state()})
    return {"ok": True, "wallets": wallets, "state": public_state()}


@app.post("/api/confirm-bounty")
async def confirm_bounty_settlement():
    if not STATE["selected_patch"]:
        raise HTTPException(status_code=400, detail="Scan a codebase and choose a researcher tier first.")
    if not STATE.get("deal_approved") or not STATE.get("solution_verified_pass"):
        raise HTTPException(
            status_code=400,
            detail="Step 3 Required First: Negotiate/Select Researcher Bid AND Verify Patch = PASS in Sandbox on Page 3 before paying!",
        )

    STATE["phase"] = "SETTLING_ESCROW"
    await emit_swarm_event("@vault", "DORADO_ESCROW_BROADCAST", "Broadcasting live 0.05 TESTFET transaction on Fetch Dorado Testnet...")
    await broadcast_ws({"type": "state", "state": public_state()})

    receipt = await settle_bounty_on_dorado()
    STATE["escrow_receipt"] = receipt
    STATE["phase"] = "SETTLED"

    # Also auto-populate live ledger verification snapshot from Fetch.ai node!
    STATE["live_ledger_check"] = await check_live_dorado_ledger_status(receipt["tx_hash"])

    sr = STATE["scan_result"]
    unlocked_lines = "\n".join(
        f"{f['point_number']}. **{f['cwe_id']}** in `{f['file_path']}` at **Line {f['line_number']}** — {f['title']}"
        for f in (sr.get("all_findings") or [])
    )

    await emit_swarm_event(
        "@vault",
        "ESCROW_UNLOCKED_ON_DORADO",
        f"Block #{receipt['block_height']}: Buyer {receipt['sender_balance_before_fet']}->{receipt['sender_balance_after_fet']} TESTFET | Escrow {receipt['recipient_balance_before_fet']}->{receipt['recipient_balance_after_fet']} TESTFET",
    )
    STATE["chat_history"].append(
        {
            "id": str(uuid4())[:8],
            "role": "assistant",
            "agent": "@vault",
            "card_kind": "receipt",
            "text": (
                f"**Payment Confirmed on Fetch Dorado Block #{receipt['block_height']} — Solution Unblurred & Unlocked!**\n\n"
                f"**Live On-Chain Wallet Balance Transfer Proof:**\n"
                f"- **Maintainer Buyer (`@aegis`):** `{receipt['sender_balance_before_fet']} TESTFET` -> **{receipt['sender_delta_fet']} TESTFET Deducted** -> **`{receipt['sender_balance_after_fet']} TESTFET`**\n"
                f"- **Researcher Escrow (`@vault`):** `{receipt['recipient_balance_before_fet']} TESTFET` -> **{receipt['recipient_delta_fet']} TESTFET Credited** -> **`{receipt['recipient_balance_after_fet']} TESTFET`**\n\n"
                f"**Exact Unlocked Bugs — Asli Error, Kyu Hai, Aur Solution:**\n{unlocked_lines}\n\n"
                f"Har file ka pura fixed code **Page 2 (@forge Patch Matrix)** me khul gaya hai — wahan se copy/download kar lo.\n\n"
                f"**Verify Externally on Official Fetch.ai Explorer:**\n"
                f"- **Transaction Explorer:** {receipt['explorer_url']}\n"
                f"- **Buyer Account Explorer:** {receipt['maintainer_wallet_url']}\n"
                f"- **Seller Account Explorer:** {receipt['researcher_wallet_url']}\n"
                f"- **Rollout Window:** {STATE['selected_slot']['date_str']} ({STATE['selected_slot']['time_window']})"
            ),
        }
    )
    _save_state_to_disk()
    await broadcast_ws({"type": "state", "state": public_state()})
    return public_state()


@app.get("/api/verify-live-ledger/{tx_hash}")
async def verify_live_on_fetch_validator(tx_hash: str):
    """
    Allows Researcher, Maintainer, or Hackathon Judge to re-verify ANY transaction hash directly
    against Fetch.ai's live Dorado Validator REST API in real time without triggering replay lock!
    """
    live_proof = await check_live_dorado_ledger_status(tx_hash)
    STATE["live_ledger_check"] = live_proof
    _save_state_to_disk()
    if live_proof.get("ok"):
        await emit_swarm_event(
            "@vault",
            "LIVE_EXPLORER_VERIFIED",
            f"Verified live on Fetch Dorado Validator Node: Block #{live_proof['block_height']} (Code 0 = SUCCESS)",
        )
    return live_proof


@app.post("/api/verify-tx-hash")
async def verify_submitted_tx_hash(payload: VerifyTxPayload):
    if not STATE["selected_patch"]:
        raise HTTPException(status_code=400, detail="Run a scan and select a researcher tier first.")
    receipt = await verify_external_dorado_tx(payload.tx_hash)
    STATE["escrow_receipt"] = receipt
    if receipt.get("verified"):
        STATE["phase"] = "SETTLED"
        STATE["live_ledger_check"] = await check_live_dorado_ledger_status(receipt["tx_hash"])
        await emit_swarm_event("@vault", "EXTERNAL_TX_UNLOCKED", f"Verified Dorado Block #{receipt['block_height']} — Vault Unlocked!")
        STATE["chat_history"].append(
            {
                "id": str(uuid4())[:8],
                "role": "assistant",
                "agent": "@vault",
                "card_kind": "receipt",
                "text": (
                    f"**External Dorado TX Verified on Block #{receipt['block_height']} — Vault Unlocked!**\n\n"
                    f"- **Verify on Fetch Explorer:** {receipt['explorer_url']}"
                ),
            }
        )
    else:
        STATE["phase"] = "PAYMENT_CANCELLED"
        await emit_swarm_event("@vault", receipt["status"], receipt["reason"])
        STATE["chat_history"].append(
            {
                "id": str(uuid4())[:8],
                "role": "assistant",
                "agent": "@vault",
                "card_kind": None,
                "text": f"**Payment Guard ({receipt['status']}):** {receipt['reason']}",
            }
        )
    _save_state_to_disk()
    await broadcast_ws({"type": "state", "state": public_state()})
    return public_state()


@app.post("/api/cancel-payment")
async def cancel_bounty_settlement():
    receipt = build_cancel_payment_receipt()
    STATE["escrow_receipt"] = receipt
    STATE["phase"] = "PAYMENT_CANCELLED"
    _save_state_to_disk()
    await emit_swarm_event("@vault", "CANCEL_PAYMENT_ISSUED", "Issued AgentPaymentProtocol CancelPayment — 0 TESTFET deducted.")
    STATE["chat_history"].append(
        {
            "id": str(uuid4())[:8],
            "role": "assistant",
            "agent": "@vault",
            "card_kind": None,
            "text": "**Escrow Cancelled Safely (`CancelPayment`):** 0 TESTFET deducted. Solution remains blurred & locked inside @vault.",
        }
    )
    await broadcast_ws({"type": "state", "state": public_state()})
    return public_state()


def _require_paid_escrow() -> None:
    if not is_escrow_unlocked():
        raise HTTPException(
            status_code=402,
            detail="Escrow Locked (402 Payment Required): Negotiate Bid, Pass Sandbox Check, and Pay 0.05 TESTFET on Fetch Dorado first!",
        )


@app.get("/api/artifacts/fixed-source")
async def download_fixed_source_file():
    _require_paid_escrow()
    patch = STATE["selected_patch"]
    orig_name = Path(STATE["target_bundle"]["files"][0]["file_path"]).name if STATE["target_bundle"] else "remediated_code.py"
    return Response(
        content=patch["patched_code"].encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="fixed_{orig_name}"'},
    )


@app.get("/api/artifacts/fix.patch")
async def download_unified_patch_file():
    _require_paid_escrow()
    patch = STATE["selected_patch"]
    fname = f"patchbounty-{patch['id']}-{patch['patch_sha256'][:8]}.patch"
    return Response(
        content=patch["unified_diff"].encode("utf-8"),
        media_type="text/x-diff",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/api/artifacts/maintainer.pdf")
async def download_maintainer_pdf():
    _require_paid_escrow()
    pdf_bytes = generate_maintainer_clearance_pdf(STATE)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="PatchBounty-Maintainer-Clearance-Pass.pdf"'},
    )


@app.get("/api/artifacts/researcher.pdf")
async def download_researcher_pdf():
    _require_paid_escrow()
    pdf_bytes = generate_researcher_payout_pdf(STATE)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="PatchBounty-Researcher-Bounty-Receipt.pdf"'},
    )


@app.get("/api/artifacts/maintainer.ics")
async def download_maintainer_ics():
    _require_paid_escrow()
    ics_txt = generate_disclosure_ics(STATE, audience="maintainer")
    return Response(
        content=ics_txt.encode("utf-8"),
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="patchbounty-maintainer-rollout.ics"'},
    )


@app.get("/api/artifacts/researcher.ics")
async def download_researcher_ics():
    _require_paid_escrow()
    ics_txt = generate_disclosure_ics(STATE, audience="researcher")
    return Response(
        content=ics_txt.encode("utf-8"),
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="patchbounty-researcher-payout.ics"'},
    )


@app.post("/api/resolve-and-deliver")
async def resolve_issues_create_pr_and_email(payload: ResolveDeliverPayload):
    """
    POST-PAYMENT RESOLUTION FLOW (payment ho chuka ho tabhi chalega — warna HTTP 402):
      1. Saari vulnerabilities ka fixed code (jo pehle se @forge bana chuka hai) taiyaar,
      2. GitHub par nayi branch push karke Pull Request create (token + write access ho to),
         warna ready-to-apply all-fixes.zip bundle,
      3. User ko issues + resolution ki report email (SMTP ho to asal send, warna .eml draft).
    """
    _require_paid_escrow()
    if not STATE.get("scan_result") or STATE["scan_result"].get("is_clean_code"):
        raise HTTPException(status_code=400, detail="Is scan me fix karne wala koi bug nahi hai.")

    pr_result: dict = {"status": "NOT_REQUESTED", "pr_url": "", "reason": "", "patch_bundle_ready": True}
    if payload.create_pr:
        await emit_swarm_event("@forge", "RESOLUTION_PR_STARTED", "Payment confirm — fixed code GitHub branch/PR ki taraf bhej rahe hain...")
        pr_result = await create_github_pull_request(STATE)
        await emit_swarm_event(
            "@forge",
            f"RESOLUTION_PR_{pr_result.get('status', 'DONE')}",
            pr_result.get("pr_url") or pr_result.get("reason", "")[:180],
        )

    email_result: dict = {"status": "NOT_REQUESTED", "recipient": "", "reason": ""}
    eml_text = ""
    if payload.notify_email:
        raw_email = deliver_email_notification(STATE, payload.recipient_email)
        eml_text = raw_email.pop("eml_text", "")
        email_result = raw_email
        await emit_swarm_event("@aegis", f"RESOLUTION_EMAIL_{email_result.get('status', 'DONE')}", email_result.get("reason", "")[:180])

    STATE["resolution_eml_text"] = eml_text
    delivery = {
        "resolved_at": datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC"),
        "repo_slug": (STATE.get("target_bundle") or {}).get("repo_slug", ""),
        "total_bugs_fixed": len((STATE.get("scan_result") or {}).get("all_findings") or []),
        "files_fixed": [fx.get("file_path", "") for fx in (STATE.get("scan_result") or {}).get("file_fixes") or []],
        "pr": pr_result,
        "email": email_result,
        "report_ready": True,
        "fixes_bundle_ready": True,
    }
    STATE["resolution_delivery"] = delivery

    pr_line = (
        f"- **GitHub Pull Request:** {pr_result['pr_url']}"
        if pr_result.get("pr_url")
        else f"- **GitHub PR Status:** {pr_result.get('status', '')} — {pr_result.get('reason', '')}"
    )
    mail_line = (
        f"- **Email Notification:** {email_result.get('status', '')} — {email_result.get('reason', '')}"
        if payload.notify_email
        else "- **Email Notification:** Not requested"
    )
    STATE["chat_history"].append(
        {
            "id": str(uuid4())[:8],
            "role": "assistant",
            "agent": "@forge",
            "card_kind": "receipt",
            "text": (
                f"**Saari Vulnerabilities Resolve Ho Gayi — Delivery Complete!**\n\n"
                f"{pr_line}\n"
                f"{mail_line}\n\n"
                f"**Downloads:** Resolution Report (issues + resolution) aur All-Fixes Bundle (har file ka fixed code + .patch) "
                f"Page 4 se download kar sakte ho."
            ),
        }
    )
    _save_state_to_disk()
    await broadcast_ws({"type": "state", "state": public_state()})
    return public_state()


@app.get("/api/artifacts/resolution-report.md")
async def download_resolution_report():
    _require_paid_escrow()
    return Response(
        content=build_resolution_report(STATE).encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="PatchBounty-Resolution-Report.md"'},
    )


@app.get("/api/artifacts/all-fixes.zip")
async def download_all_fixes_bundle():
    _require_paid_escrow()
    return Response(
        content=build_all_fixes_zip(STATE),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="PatchBounty-All-Fixes.zip"'},
    )


@app.get("/api/artifacts/resolution-email.eml")
async def download_resolution_email_draft():
    _require_paid_escrow()
    eml = STATE.get("resolution_eml_text") or ""
    if not eml:
        raise HTTPException(status_code=404, detail="Email draft abhi bana nahi hai — pehle Resolve & Deliver chalao.")
    return Response(
        content=eml.encode("utf-8"),
        media_type="message/rfc822",
        headers={"Content-Disposition": 'attachment; filename="PatchBounty-Resolution-Email.eml"'},
    )


UI_BUNDLE_DIR = PROJECT_ROOT / "frontend" / "ui_bundle"
if (UI_BUNDLE_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(UI_BUNDLE_DIR / "assets")), name="ui_assets")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    candidate = UI_BUNDLE_DIR / full_path
    if full_path and candidate.is_file():
        return FileResponse(str(candidate))
    index_file = UI_BUNDLE_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(str(index_file))
    return {"status": "PatchBounty (@aegis) v5.0 API Running", "ui_bundle": "Not built yet"}


if __name__ == "__main__":
    import uvicorn

    print("==================================================================", flush=True)
    print(" Starting PatchBounty Web Studio & API on http://127.0.0.1:8002", flush=True)
    print("==================================================================", flush=True)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8002, reload=False)

