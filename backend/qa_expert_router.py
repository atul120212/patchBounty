"""
Context-Aware Conversational Assistant & Agentverse 15/15 Semantic Router for PatchBounty (@aegis).
1. Remembers full multi-turn chat history (`chat_history[-8:]`) and active repository audit state.
2. Replies naturally in Roman Hinglish if the user asks in Hindi/Hinglish, or crisp English if in English.
3. Enforces strict Escrow Anti-Leak Rules: Before `0.05 TESTFET` settlement, never reveals exact line numbers
   or fixed source code even if asked directly in chat! Once paid (`SETTLED`), explains every exact fix line!
"""
import re
from backend.config_store import runtime_config

PATCHBOUNTY_SYSTEM_FACTS = (
    "PatchBounty Official Architecture & Blind Escrow Bounty Rules:\n"
    "1. 6 Fetch.ai Single-Word uAgents: @aegis (Master Coordinator & Escrow Orchestrator on AgentChatProtocol v0.3.0 + "
    "AgentPaymentProtocol v0.1.0), @recon (Multi-Language GitHub & Codebase Scanner supporting Python, JavaScript/TypeScript, "
    "Solidity, Java, Go, PHP, C/C++, C#, Ruby, Rust, SQL), @specter (Isolated Sandbox Exploit Verifier), @forge (3-Tier Full-File "
    "Patch Architect: @blade, @kestrel, @titan), @warden (Post-Patch Exploit-Block & Regression Gate), and @vault (Live Fetch.ai "
    "Dorado Testnet `0.05 TESTFET` Escrow Treasury & Anti-Replay Verifier).\n"
    "2. Why Businesses Cannot Steal Code Without Paying (Zero-Knowledge Blind Escrow Lock): Before payment, PatchBounty scans "
    "100% of the code across any programming language, proves the bugs are genuinely exploitable in an isolated sandbox, and "
    "lists ALL bugs in numbered points showing business risk & cryptographic SHA-256 proof hashes — while keeping exact line numbers, "
    "exploit payloads, and fixed code strictly SEALED on the server (`HTTP 402 Payment Required`). The instant `0.05 TESTFET` "
    "confirms on Fetch Dorado Testnet, @vault unlocks exact file/line locations, full fixed code, git `.patch`, PDFs, and `.ics` invites.\n"
    "3. Sealed Maintainer Budget Privacy & Honest CVSS Severity Floors: Maintainer's private max budget is 100% hidden from "
    "researchers and Researcher Payout PDFs. Over-budget quotes negotiate down toward honest CVSS floors ($140 Critical, $90 High, "
    "$55 Medium). If a budget is below the floor, PatchBounty alerts 'Not Available Within Your Bounty Budget'.\n"
    "4. Dual 50/50 ASI:One Load Balancer: Single `ASI_ONE_API_KEY` alternates 50/50 across `asi1` and `asi1-mini`."
)

HINGLISH_MARKERS = {
    "kya", "kaise", "kyu", "kyun", "hai", "hain", "mein", "me", "kitne", "kaha", "kahan",
    "batao", "bataiye", "samjhao", "paisa", "paise", "mera", "mere", "code", "sahi", "nahi",
    "nhi", "kar", "karega", "hoga", "dikhao", "chलेगा", "chalega", "bhai", "aur",
}


def _looks_hinglish(text: str) -> bool:
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    return len(words.intersection(HINGLISH_MARKERS)) >= 2


def parse_maintainer_budget_usd(text: str) -> int | None:
    patterns = [
        r"(?:budget|ceiling|under|below|within|max|upto|up to|bounty(?:\s+is|\s+of)?)\s*(?:is|=|:)?\s*(?:\$|usd\s*)?(\d{1,6})\b",
        r"\$\s*(\d{1,6})\b",
        r"\b(\d{1,6})\s*(?:usd|dollars)\b",
    ]
    low = text.lower()
    for pat in patterns:
        m = re.search(pat, low)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 500000:
                return val
    return None


def is_meta_or_policy_question(text: str) -> bool:
    t = text.strip().lower()
    if not t:
        return True

    explicit_non_scan = (
        "not scanning", "do not scan", "don't scan", "do not select", "don't select",
        "do not lock", "text answer", "just asking", "only asking", "question:", "without scanning",
    )
    if any(ns in t for ns in explicit_non_scan):
        return True

    scan_triggers = (
        "github.com/", "```", "targets/", "fintech_ledger_api", "express_checkout_api",
        "defi_staking_vault", "banking_dao_java", "cloud_deploy_runner",
        "doc_vault_storage", "config_sync_engine", "token_ssrf_gateway",
        "scan ", "audit ", "remediate ", "can you scan", "can you audit",
        "please scan", "please audit", "find sql injection", "find vulnerabilities in",
    )
    if any(st in t for st in scan_triggers):
        return False

    return True


def _build_safe_live_context(session_state: dict | None) -> str:
    if not session_state or not session_state.get("scan_result"):
        return "Current Session Status: No repository has been scanned yet in this session."

    sr = session_state["scan_result"]
    is_paid = session_state.get("phase") == "SETTLED" and bool((session_state.get("escrow_receipt") or {}).get("verified"))
    findings = sr.get("all_findings") or []
    sel_patch = session_state.get("selected_patch") or {}
    slot = session_state.get("selected_slot") or {}

    if not is_paid:
        pts = "; ".join(
            f"#{f['point_number']} {f['severity']} (CVSS {f['cvss_score']}): {f['blind_category']}"
            for f in findings
        )
        return (
            f"Current Session Status (ESCROW LOCKED — NOT PAID YET):\n"
            f"- Scanned Language: {sr.get('language')} ({sr.get('lines_scanned_count')} lines inspected)\n"
            f"- Total Vulnerabilities Found: {len(findings)} -> [{pts}]\n"
            f"- Selected Researcher Tier: {sel_patch.get('researcher_handle')} ({sel_patch.get('strategy_name')}) at ${sel_patch.get('verified_bounty_usd')} USD\n"
            f"- Scheduled Rollout Window: {slot.get('date_str')} ({slot.get('time_window')})\n"
            f"- STRICT SECURITY RULE: Because 0.05 TESTFET has NOT been paid yet, DO NOT reveal exact line numbers or fixed code; invite the user to complete Step 4 payment to unlock everything."
        )

    pts_paid = "; ".join(
        f"#{f['point_number']} {f['cwe_id']} at {f['file_path']}:L{f['line_number']} ({f['title']})"
        for f in findings
    )
    escrow = session_state.get("escrow_receipt") or {}
    return (
        f"Current Session Status (ESCROW UNLOCKED — PAID ON DORADO BLOCK #{escrow.get('block_height')}):\n"
        f"- Scanned Language: {sr.get('language')}\n"
        f"- All Unlocked Findings ({len(findings)}): {pts_paid}\n"
        f"- Approved Patch: {sel_patch.get('researcher_handle')} at ${sel_patch.get('verified_bounty_usd')} USD | TX: {escrow.get('tx_hash')}"
    )


async def answer_patchbounty_meta_question(
    user_text: str,
    session_state: dict | None = None,
) -> tuple[str, str]:
    use_hinglish = _looks_hinglish(user_text)
    lang_rule = (
        "Reply clearly in friendly, easy-to-understand Roman Hinglish (using numbered points where helpful, strictly zero emojis)."
        if use_hinglish
        else "Reply clearly in crisp, direct English (using numbered points where helpful, strictly zero emojis)."
    )

    history_msgs: list[dict] = []
    if session_state and session_state.get("chat_history"):
        for item in session_state["chat_history"][-6:]:
            role = "user" if item.get("role") == "user" else "assistant"
            txt = str(item.get("text", "")).strip()
            if txt and txt != user_text.strip():
                history_msgs.append({"role": role, "content": txt[:500]})

    live_ctx = _build_safe_live_context(session_state)

    messages = [
        {
            "role": "system",
            "content": (
                "You are @aegis, the intelligent security & bounty assistant of PatchBounty built by "
                "Atul Anand, Jeeya, and Vanshika on Fetch.ai.\n"
                f"{lang_rule}\n"
                "Always directly answer what the user actually asked in 70 to 170 words and finish every sentence cleanly.\n\n"
                f"{PATCHBOUNTY_SYSTEM_FACTS}\n\n{live_ctx}"
            ),
        },
        *history_msgs,
        {"role": "user", "content": user_text},
    ]

    live_ans, used_model = await runtime_config.complete_asi_one(
        messages=messages,
        prefer_flagship=True,
        max_tokens=650,
        temperature=0.25,
        timeout=14.0,
    )
    if live_ans:
        return live_ans.strip(), used_model

    # Clean deterministic fallback (supports both Hinglish & English + session awareness!)
    sr = (session_state or {}).get("scan_result")
    is_paid = (session_state or {}).get("phase") == "SETTLED"
    if use_hinglish:
        if sr:
            n_bugs = len(sr.get("all_findings") or [])
            status_line = (
                "Aapka 0.05 TESTFET payment confirm ho chuka hai — exact line numbers aur poora fixed code unlock hai!"
                if is_paid
                else f"Abhi code mein total {n_bugs} security bugs confirm hue hain, lekin exact line numbers aur fixed code @vault escrow mein LOCKED hain taaki bina payment researcher ka fix leak na ho. Page 4 par 0.05 TESTFET pay karte hi poora fix unlock ho jayega."
            )
            return (
                f"PatchBounty (@aegis) Update:\n"
                f"1. Language Scanned: {sr.get('language')} ({n_bugs} bugs found across full scan)\n"
                f"2. Escrow Lock Status: {status_line}\n"
                f"3. Multi-Language Support: Python, JavaScript/Node.js, TypeScript, Solidity, Java, Go, PHP, aur C/C++ sabhi languages support hoti hain.",
                "aegis-smart-guard",
            )
        return (
            "Namaste! Main @aegis hoon — PatchBounty ka AI Security Coordinator.\n"
            "1. Aap kisi bhi language (Python, JavaScript, Solidity, Java, Go, PHP, C++) ka code ya GitHub repo link scan kar sakte hain.\n"
            "2. Main poore code ko check karke saare bugs numbered points mein dikhata hoon, lekin exact line aur fixed code tab tak @vault escrow mein lock rakhta hoon jab tak 0.05 TESTFET payment confirm na ho jaye.\n"
            "3. Aapka private max budget researcher se 100% secret rehta hai.",
            "aegis-smart-guard",
        )

    low = user_text.lower()
    if any(k in low for k in ["budget", "floor", "quote", "negotiate", "researcher see", "private"]):
        return (
            "Over-Budget Quotes, Severity Floor & Sealed Maintainer Privacy:\n"
            "When initial asks exceed your private ceiling, @aegis negotiates across all 3 verified tiers (@blade, @kestrel, @titan) "
            "down toward the honest CVSS severity floor ($140 USD Critical, $90 USD High, $55 USD Medium) while keeping your private "
            "maximum budget 100% hidden from researchers and omitted from Researcher Payout PDFs. If a budget is below the floor, "
            "@aegis flags 'Not Available Within Your Bounty Budget' instead of offering unverified low-cost fixes.",
            "expert-deterministic",
        )
    if any(k in low for k in ["receipt", "certificate", "pdf", "printable", "calendar", "slot", "confirm", "ics", "steal", "lock"]):
        return (
            "Blind Escrow Code Lock, Calendar Rollout & Post-Payment Certificates:\n"
            "Before payment, PatchBounty proves exploitability in an isolated sandbox and lists all findings as numbered impact points "
            "while sealing exact line numbers and fixed code on the server (HTTP 402). Once 0.05 TESTFET confirms on Fetch Dorado Testnet, "
            "@vault immediately unlocks exact line locations, full multi-language fixed code, unified .patch diff, IST rollout .ics invites, "
            "Maintainer Clearance Pass PDF, and Researcher Zero-Fee Payout Receipt PDF.",
            "expert-deterministic",
        )
    return (
        "PatchBounty (@aegis) coordinates 6 single-word Fetch.ai uAgents (@aegis, @recon, @specter, @forge, @warden, @vault) "
        "to inspect complete repositories across Python, JavaScript/TypeScript, Solidity, Java, Go, PHP, and C/C++, prove "
        "vulnerabilities inside isolated sandboxes without leaking unpaid fixes, schedule IST rollout windows (.ics), "
        "and settle 0.05 TESTFET bounties on Fetch Dorado Testnet.",
        "expert-deterministic",
    )
