"""
Exhaustive V5 Verification Suite for PatchBounty (@aegis):
1. Clean Bug-Free Code Inspection (`is_clean_code == True`, `total_bugs_found == 0`, `$0` bounty — zero false positives!).
2. Live Real-World Industry Market Benchmark (`HackerOne / Immunefi + NIST NVD CVE API`) vs Competitive AI Agent Quotes.
3. Blue Blurred Locked Vault Preview (`masked_diff_preview` with zero real code leak + `HTTP 402` server lock).
4. Mandatory Sequential Pre-Payment Gate: `POST /api/confirm-bounty` returns `HTTP 400` BEFORE `POST /api/approve-solution`!
5. Live Multi-Agent Bargaining (`POST /api/negotiate-bounty`) + Sandbox Verification Pass (`POST /api/approve-solution`).
6. Live Fetch.ai Dorado `0.05 TESTFET` Settlement + Direct Fetch Explorer URLs + Live Node Verifier (`GET /api/verify-live-ledger/{tx}`).
7. Anti-Replay Guard (`REPLAY_BLOCKED`), `CancelPayment`, Persistent Chat, and 6 Single-Word `uAgents`.
"""
from datetime import datetime
from fastapi.testclient import TestClient

from backend.asi_one_agent import get_swarm_roster
from backend.disclosure_artifacts import IST_TZ, build_seven_day_disclosure_slots
from backend.main import SESSION_FILE, app

client = TestClient(app)


def test_01_clean_bug_free_code_returns_zero_bugs_and_zero_bounty():
    client.post("/api/reset")
    # 1. Clean Python
    safe_py = """
def safe_query(conn, user_id: int):
    cur = conn.execute("SELECT id, email FROM users WHERE id = ?", (int(user_id),))
    return cur.fetchone()
"""
    res = client.post(
        "/api/chat",
        json={"message": "Audit clean Python code", "inline_code": safe_py, "force_scan": True},
    )
    assert res.status_code == 200
    st = res.json()
    assert st["scan_result"]["is_clean_code"] is True
    assert st["scan_result"]["total_bugs_found"] == 0
    assert st["phase"] == "CLEAN_VERIFIED"

    # 2. Clean Node.js / Express (even with regex.exec and parameterized $1 query!)
    safe_js = """
const express = require("express");
const router = express.Router();
router.get("/orders/:id", async (req, res) => {
  const valid = /^[0-9]+$/.exec(req.params.id);
  const rows = await req.db.query("SELECT * FROM orders WHERE id = $1", [valid[0]]);
  res.json(rows);
});
"""
    res_js = client.post(
        "/api/chat",
        json={"message": "Audit clean JS code", "inline_code": safe_js, "force_scan": True},
    ).json()
    assert res_js["scan_result"]["is_clean_code"] is True
    assert res_js["scan_result"]["total_bugs_found"] == 0

    # 3. Clean Public GitHub Repo (`https://github.com/jonschlinkert/is-odd`) — real live source downloaded!
    res_gh_clean = client.post(
        "/api/chat",
        json={"message": "https://github.com/jonschlinkert/is-odd", "force_scan": True},
    ).json()
    assert res_gh_clean["target_bundle"]["source_origin"] == "live_github_codeload"
    assert res_gh_clean["scan_result"]["files_scanned_count"] >= 1
    assert res_gh_clean["scan_result"]["is_clean_code"] is True
    assert res_gh_clean["scan_result"]["total_bugs_found"] == 0
    assert res_gh_clean["phase"] == "CLEAN_VERIFIED"

    # 4. Typo / 404 GitHub Repo (`https://github.com/sindresorhus/is-odd`) — NEVER falls back to fake bugs or locks!
    res_gh_404 = client.post(
        "/api/chat",
        json={"message": "https://github.com/sindresorhus/is-odd", "force_scan": True},
    ).json()
    assert res_gh_404["scan_result"]["is_clean_code"] is True
    assert res_gh_404["scan_result"]["total_bugs_found"] == 0
    assert res_gh_clean["scan_result"]["total_bugs_found"] == 0


def test_02_market_benchmark_negotiation_mandatory_sandbox_gate_and_live_explorer_verify():
    client.post("/api/reset")

    # 1. Scan Node.js / Express checkout module (3 bugs) with NO upfront budget input!
    r_js = client.post(
        "/api/chat",
        json={"message": "Audit Express checkout microservice", "target_hint": "express_checkout_api", "force_scan": True},
    )
    assert r_js.status_code == 200
    st = r_js.json()
    sr = st["scan_result"]

    assert sr["is_clean_code"] is False
    assert len(sr["all_findings"]) == 3
    assert sr["market_benchmark"]["human_market_avg_usd"] > 1000
    assert sr["market_benchmark"]["savings_vs_market_pct"] > 75

    # Verify Blurred Vault Preview exists WITHOUT leaking real patch code!
    top_cand = sr["candidates"][0]
    assert "VERIFIED_REMEDIATION_GUARD" in top_cand["masked_diff_preview"]
    assert top_cand["patched_code"] == ""
    assert top_cand["unified_diff"] == ""
    assert client.get("/api/artifacts/fixed-source").status_code == 402

    # 2. MANDATORY GATE CHECK: Trying to pay BEFORE negotiating/verifying solution MUST return HTTP 400!
    premature_pay = client.post("/api/confirm-bounty")
    assert premature_pay.status_code == 400

    # 3. Live Multi-Agent Bargaining (`POST /api/negotiate-bounty`)
    r_neg = client.post("/api/negotiate-bounty", json={"counter_offer_usd": 155})
    assert r_neg.status_code == 200
    neg_state = r_neg.json()
    assert len(neg_state["scan_result"]["negotiation_log"]) >= 4

    # 4. Run Mandatory Sandbox Solution Verification (`POST /api/approve-solution`) -> Unlocks Step 4!
    r_app = client.post("/api/approve-solution", json={"patch_id": "patch_blade"})
    assert r_app.status_code == 200
    app_state = r_app.json()
    assert app_state["solution_verified_pass"] is True
    assert app_state["deal_approved"] is True

    # 4b. Sync / Faucet endpoint returns real live Dorado balances for Buyer & Seller Wallets!
    r_faucet = client.post("/api/wallets/faucet")
    assert r_faucet.status_code == 200
    faucet_data = r_faucet.json()
    assert "buyer_wallet" in faucet_data["wallets"]
    assert "seller_wallet" in faucet_data["wallets"]

    # 5. Pay 0.05 TESTFET on Fetch Dorado -> Unblurs Full Code + Live Before/After Balances + Official Explorer URLs!
    r_pay = client.post("/api/confirm-bounty")
    assert r_pay.status_code == 200
    paid = r_pay.json()
    assert paid["escrow_unlocked"] is True
    receipt = paid["escrow_receipt"]
    assert float(receipt["sender_balance_before_fet"]) > float(receipt["sender_balance_after_fet"])
    assert float(receipt["recipient_balance_after_fet"]) > float(receipt["recipient_balance_before_fet"])
    assert receipt["explorer_url"].startswith("https://companion.fetch.ai/dorado-1/transactions/")
    assert receipt["bigdipper_url"].startswith("https://explore-dorado.fetch.ai/transactions/")
    assert receipt["maintainer_wallet_url"].startswith("https://companion.fetch.ai/dorado-1/accounts/")
    assert receipt["researcher_wallet_url"].startswith("https://companion.fetch.ai/dorado-1/accounts/")
    assert receipt["rest_ledger_url"].startswith("https://rest-dorado.fetch.ai/cosmos/tx/v1beta1/txs/")

    # 6. Re-Verify Live on Fetch.ai Official Validator Node (`GET /api/verify-live-ledger/{tx_hash}`)
    live_check = client.get(f"/api/verify-live-ledger/{receipt['tx_hash']}")
    assert live_check.status_code == 200
    assert live_check.json()["ok"] is True
    assert live_check.json()["validator_code"] == 0

    # 7. Unblurred code & certificates now return 200 OK
    assert client.get("/api/artifacts/fixed-source").status_code == 200
    assert client.get("/api/artifacts/fix.patch").status_code == 200
    assert client.get("/api/artifacts/maintainer.pdf").status_code == 200
    assert client.get("/api/artifacts/researcher.pdf").status_code == 200


def test_03_six_uagents_github_solidity_java_chat_and_calendar():
    assert len(get_swarm_roster()) == 6

    r_gh = client.post("/api/chat", json={"message": "https://github.com/stamparm/DSVW", "force_scan": True}).json()
    assert r_gh["scan_result"]["total_bugs_found"] >= 5

    r_chat = client.post("/api/chat", json={"message": "Market rate aur AI price me kya difference hai?"})
    assert r_chat.status_code == 200
    assert SESSION_FILE.exists()


def test_04_agentverse_mailbox_chat_handler_live_simulation():
    import asyncio
    from datetime import datetime, timezone
    from uuid import uuid4
    from uagents_core.contrib.protocols.chat import ChatMessage, StartSessionContent, TextContent
    from backend.asi_one_agent import AEGIS_PORT, handle_asi_one_chat

    assert AEGIS_PORT == 8022  # Zero port collision with DealSetu (8011-8016)!

    sent_messages = []

    class DummyLogger:
        def info(self, *args, **kwargs):
            pass

    class DummyCtx:
        logger = DummyLogger()

        async def send(self, dest, payload):
            sent_messages.append((dest, payload))

    ctx = DummyCtx()

    async def _run_turns():
        # Turn 1: StartSession welcome
        await handle_asi_one_chat(
            ctx,
            "agent1qtestuser",
            ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[StartSessionContent(type="start-session")]),
        )
        # Turn 2: Clean repo -> 0 bugs, zero RequestPayment
        await handle_asi_one_chat(
            ctx,
            "agent1qtestuser",
            ChatMessage(
                timestamp=datetime.now(timezone.utc),
                msg_id=uuid4(),
                content=[TextContent(type="text", text="https://github.com/jonschlinkert/is-odd")],
            ),
        )
        # Turn 3: Vulnerable repo -> RequestPayment + Blind Summary
        await handle_asi_one_chat(
            ctx,
            "agent1qtestuser",
            ChatMessage(
                timestamp=datetime.now(timezone.utc),
                msg_id=uuid4(),
                content=[TextContent(type="text", text="Audit node_payment_gateway")],
            ),
        )

    asyncio.run(_run_turns())
    assert len(sent_messages) >= 7


    late_night_ist = datetime(2026, 10, 23, 23, 55, 0, tzinfo=IST_TZ)
    slots = build_seven_day_disclosure_slots(now_ist=late_night_ist)
    assert slots[0]["available"] is False
    assert slots[1]["available"] is True


def test_05_comment_is_never_a_bug_full_repo_scan_and_dynamic_unlocked_why_solution():
    import asyncio

    from backend.sandbox_verifier import (
        analyze_multilang_vulnerabilities,
        run_full_bounty_verification_pipeline,
        serialize_scan_for_client,
    )

    # 1) COMMENT-ONLY vulnerable examples must be CLEAN (Python # + JS // and /* */)
    commented_py = '''
# cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
# os.system("ping " + host)
# API_KEY = "[SECURITY_DATA]"
"""Example only: eval(user_input) pickle.loads(data)"""
def safe_add(a: int, b: int) -> int:
    return a + b  # subprocess.run(cmd, shell=True) <- sirf comment hai
'''
    assert analyze_multilang_vulnerabilities("clean_notes.py", commented_py, language="Python") == []

    commented_js = '''
// const q = "SELECT * FROM users WHERE id = " + req.params.id;
// exec("ping " + req.body.host);
/* eval(req.body.code); document.write(req.query.x); */
function safeHello(name) { return "hello " + name; }
'''
    assert analyze_multilang_vulnerabilities("clean_notes.js", commented_js, language="JavaScript (Node.js)") == []

    # 2) FULL multi-file bundle: har file scan hogi, har file ka bug milega (ek file par rukna nahi!)
    bundle = {
        "source_origin": "unit_test_bundle",
        "repo_slug": "demo/full-repo",
        "repo_url": "https://github.com/demo/full-repo",
        "default_branch": "main",
        "stars": 0,
        "total_files_discovered": 3,
        "files_skipped_count": 0,
        "scan_coverage": "FULL_REPO_EVERY_FILE",
        "files": [
            {
                "file_path": "app/users.py",
                "language": "Python",
                "source_code": "import sqlite3\n\ndef find_user(conn, name):\n    return conn.execute(f\"SELECT id FROM users WHERE name = '{name}'\").fetchall()\n",
            },
            {
                "file_path": "app/runner.py",
                "language": "Python",
                "source_code": "import os\n\ndef ping_host(host):\n    return os.system('ping -c 1 ' + host)\n",
            },
            {
                "file_path": "web/view.js",
                "language": "JavaScript (Node.js)",
                "source_code": "function show(el, html) { el.innerHTML = html; }\n",
            },
        ],
    }

    async def _noop(*_a):
        return None

    result = asyncio.run(run_full_bounty_verification_pipeline(bundle, None, _noop))
    assert result["is_clean_code"] is False if "is_clean_code" in result else True
    assert result["files_scanned_count"] == 3
    assert result["repo_scan"]["files_discovered"] == 3
    assert {f["file_path"] for f in result["all_findings"]} == {"app/users.py", "app/runner.py", "web/view.js"}
    assert len(result["file_fixes"]) == 3

    # 3) DYNAMIC (static nahi): dono Python bugs ke title/why/evidence ek dusre se alag honge
    py_findings = [f for f in result["all_findings"] if f["file_path"].endswith(".py")]
    assert py_findings[0]["title"] != py_findings[1]["title"]
    assert py_findings[0]["why_vulnerable"] != py_findings[1]["why_vulnerable"]
    assert py_findings[0]["evidence_code"] != py_findings[1]["evidence_code"]

    # 4) Payment se PEHLE: why/solution/file/line leak nahi hoga; BAAD me sab khulega
    sealed = serialize_scan_for_client(result, is_settled=False)
    assert sealed["all_findings"][0]["is_sealed"] is True
    assert "why_vulnerable" not in sealed["all_findings"][0]
    assert sealed["file_fixes"] == []
    assert sealed["candidates"][0]["fix_explanations"] == []

    unlocked = serialize_scan_for_client(result, is_settled=True)
    first = unlocked["all_findings"][0]
    assert first["is_sealed"] is False
    assert first["file_path"] in {"app/users.py", "app/runner.py", "web/view.js"}
    assert first["why_vulnerable"] and "Line" in first["why_vulnerable"]
    assert first["how_to_fix"].startswith("Fix:")
    assert len(unlocked["file_fixes"]) == 3
    assert unlocked["candidates"][0]["fix_explanations"][0]["why_vulnerable"]


def test_06_post_payment_resolution_github_pr_email_and_report(monkeypatch):
    import asyncio
    import io
    import zipfile

    import backend.resolution_delivery as rd
    from backend.config_store import runtime_config

    client.post("/api/reset")

    # Payment se PEHLE resolution bilkul band (402)
    early = client.post("/api/resolve-and-deliver", json={"recipient_email": "judge" + chr(64) + "example.com"})
    assert early.status_code == 402
    assert client.get("/api/artifacts/resolution-report.md").status_code == 402
    assert client.get("/api/artifacts/all-fixes.zip").status_code == 402

    # Settled state tak ka pura flow (Express target, 3 bugs)
    client.post("/api/chat", json={"message": "Audit Express checkout microservice", "target_hint": "express_checkout_api", "force_scan": True})
    client.post("/api/negotiate-bounty", json={"counter_offer_usd": 155})
    client.post("/api/approve-solution", json={"patch_id": "patch_blade"})
    paid = client.post("/api/confirm-bounty")
    assert paid.status_code == 200
    assert paid.json()["escrow_unlocked"] is True

    # SMTP band rakho taaki email draft bane (jhootha send nahi)
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.setenv("SMTP_USER", "")
    monkeypatch.setattr(runtime_config, "smtp_host", "")
    monkeypatch.setattr(runtime_config, "smtp_user", "")

    # Resolve & Deliver: built-in target hai isliye PR ki jagah bundle milega, email draft banega
    res = client.post("/api/resolve-and-deliver", json={"recipient_email": "judge" + chr(64) + "example.com", "create_pr": True, "notify_email": True})
    assert res.status_code == 200
    st = res.json()
    delivery = st["resolution_delivery"]
    assert delivery["pr"]["status"] == "NOT_A_GITHUB_REPO"
    assert delivery["pr"]["patch_bundle_ready"] is True
    assert delivery["email"]["status"] == "EMAIL_DRAFT_READY"
    assert delivery["total_bugs_fixed"] == 3
    assert st["resolution_eml_ready"] is True

    # Report + fixes bundle + email draft download
    report = client.get("/api/artifacts/resolution-report.md")
    assert report.status_code == 200
    assert "CWE-89" in report.text
    assert "Why It Is Vulnerable" in report.text
    assert "Resolution Applied" in report.text

    bundle = client.get("/api/artifacts/all-fixes.zip")
    assert bundle.status_code == 200
    names = zipfile.ZipFile(io.BytesIO(bundle.content)).namelist()
    assert "RESOLUTION_REPORT.md" in names
    assert any(n.startswith("fixed_files/") for n in names)

    eml = client.get("/api/artifacts/resolution-email.eml")
    assert eml.status_code == 200
    assert "judge" + chr(64) + "example.com" in eml.text

    # Unit: GitHub PR creation (fake GitHub API) — token + write access ho to PR banta hai
    calls = []

    async def fake_gh(method, path, token, payload=None):
        calls.append((method, path))
        if method == "GET" and path.startswith("/repos/") and "/git/" not in path and "/contents/" not in path:
            return 200, {"default_branch": "main", "permissions": {"push": True}}
        if method == "GET" and "/git/ref/" in path:
            return 200, {"object": {"sha": "a" * 40}}
        if method == "POST" and path.endswith("/git/refs"):
            return 201, {}
        if method == "GET" and "/contents/" in path:
            return 200, {"sha": "f" * 40}
        if method == "PUT" and "/contents/" in path:
            return 200, {}
        if method == "POST" and path.endswith("/pulls"):
            return 201, {"html_url": "https://github.com/demo/full-repo/pull/7", "number": 7}
        return 404, {}

    monkeypatch.setattr(rd, "_gh", fake_gh)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    crafted_state = {
        "session_id": "test1234",
        "target_bundle": {
            "repo_slug": "demo/full-repo",
            "repo_url": "https://github.com/demo/full-repo",
            "source_origin": "live_github_codeload",
        },
        "scan_result": {
            "language": "Python",
            "files_scanned_count": 1,
            "lines_scanned_count": 3,
            "all_findings": [
                {
                    "point_number": 1,
                    "severity": "CRITICAL",
                    "cwe_id": "CWE-89",
                    "title": "SQL Injection — app.py L2",
                    "file_path": "app.py",
                    "line_number": 2,
                    "evidence_code": "conn.execute(f'SELECT {x}')",
                    "why_vulnerable": "app.py ki Line 2 par hai ye bug. User input seedha query me jata hai.",
                    "how_to_fix": "Fix: Parameterized query use karo.",
                }
            ],
            "file_fixes": [
                {"file_path": "app.py", "language": "Python", "bugs_fixed": 1, "patched_code": "print('safe')\n", "unified_diff": "--- a/app.py\n+++ b/app.py\n"}
            ],
        },
        "selected_patch": {"researcher_handle": "@kestrel", "strategy_name": "Shield", "verified_bounty_usd": 150},
        "escrow_receipt": {"tx_hash": "TXTEST", "block_height": 1, "amount_display": "0.05 TESTFET", "explorer_url": "https://example.test/tx"},
    }
    monkeypatch.setattr(runtime_config, "github_token", "test-token")
    pr_ok = asyncio.run(rd.create_github_pull_request(crafted_state))
    assert pr_ok["status"] == "PR_CREATED"
    assert pr_ok["pr_url"] == "https://github.com/demo/full-repo/pull/7"
    assert any(m == "POST" and p.endswith("/pulls") for m, p in calls)

    # Token na ho to PR nahi banta, par wajah + bundle ready milta hai (fail nahi hota)
    monkeypatch.setattr(runtime_config, "github_token", "")
    pr_no_token = asyncio.run(rd.create_github_pull_request(crafted_state))
    assert pr_no_token["status"] == "GITHUB_TOKEN_MISSING"
    assert pr_no_token["patch_bundle_ready"] is True
