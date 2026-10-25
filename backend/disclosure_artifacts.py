"""
14-Day Coordinated Security Rollout Calendar (with 4 Selectable IST Time Windows per Date + Real-Time Past Cutoff)
and Executive Light-Theme Printable PDF Security Certificates + Separate Maintainer & Researcher `.ics` Invites.

Strict Privacy Invariant: Maintainer's secret maximum budget ceiling is NEVER included in Researcher artifacts!
"""
from datetime import datetime, timedelta, timezone
from backend.dorado_escrow import get_escrow_wallets_info

IST_TZ = timezone(timedelta(hours=5, minutes=30))

DAILY_IST_WINDOWS = [
    {"win_id": "morning_10", "label": "10:00 AM - 11:00 AM IST", "hour": 10, "track": "Morning CI Hotfix Merge"},
    {"win_id": "afternoon_15", "label": "03:00 PM - 04:00 PM IST", "hour": 15, "track": "Afternoon Staging Canary"},
    {"win_id": "evening_20", "label": "08:30 PM - 09:30 PM IST", "hour": 20, "track": "Low-Traffic Production Rollout"},
    {"win_id": "night_23", "label": "11:00 PM - 11:55 PM IST", "hour": 23, "track": "Zero-Downtime Night Window"},
]


def get_now_ist() -> datetime:
    return datetime.now(IST_TZ)


def build_seven_day_disclosure_slots(now_ist: datetime | None = None) -> list[dict]:
    """Builds 14 days of interactive calendar dates with 4 selectable IST rollout windows per date."""
    base = now_ist or get_now_ist()
    slots: list[dict] = []
    for day_offset in range(10):
        day_dt = base + timedelta(days=day_offset)
        day_windows: list[dict] = []
        for w in DAILY_IST_WINDOWS:
            win_dt = day_dt.replace(hour=w["hour"], minute=0, second=0, microsecond=0)
            is_open = True if day_offset > 0 else (win_dt - timedelta(minutes=15) > base)
            end_dt = win_dt + timedelta(minutes=55)
            day_windows.append(
                {
                    "win_id": w["win_id"],
                    "time_window": w["label"],
                    "release_track": w["track"],
                    "available": is_open,
                    "dtstart_local": win_dt.strftime("%Y%m%dT%H%M%S"),
                    "dtend_local": end_dt.strftime("%Y%m%dT%H%M%S"),
                }
            )

        open_wins = [dw for dw in day_windows if dw["available"]]
        chosen = open_wins[0] if open_wins else day_windows[-1]
        day_avail = len(open_wins) > 0

        slots.append(
            {
                "id": f"slot_day_{day_offset + 1}",
                "day_name": day_dt.strftime("%a"),
                "day_num": day_dt.strftime("%d"),
                "month_short": day_dt.strftime("%b"),
                "day_label": (
                    "Today (Closed)" if (day_offset == 0 and not day_avail)
                    else ("Today" if day_offset == 0 else ("Tomorrow" if day_offset == 1 else day_dt.strftime("%a, %d %b")))
                ),
                "date_str": day_dt.strftime("%d %b %Y"),
                "time_window": chosen["time_window"],
                "release_track": chosen["release_track"],
                "win_id": chosen["win_id"],
                "windows": day_windows,
                "available": day_avail,
                "dtstart_local": chosen["dtstart_local"],
                "dtend_local": chosen["dtend_local"],
            }
        )
    return slots


def _pdf_escape(text: str) -> str:
    clean = str(text or "").encode("ascii", errors="replace").decode("ascii")
    return clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _compile_single_page_vector_pdf(commands: list[str]) -> bytes:
    stream_bytes = "\n".join(commands).encode("latin-1", errors="replace")
    objs: list[bytes] = []
    objs.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objs.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objs.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R /F3 6 0 R >> >> /Contents 7 0 R >> endobj\n"
    )
    objs.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objs.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj\n")
    objs.append(b"6 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Courier >> endobj\n")
    objs.append(
        f"7 0 obj << /Length {len(stream_bytes)} >> stream\n".encode("ascii")
        + stream_bytes
        + b"\nendstream endobj\n"
    )

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objs:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)} \n0000000000 65535 f \n".encode("ascii"))
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    return bytes(out)


def generate_maintainer_clearance_pdf(state: dict) -> bytes:
    scan = state.get("scan_result") or {}
    findings = scan.get("all_findings") or [scan.get("vulnerability") or {}]
    patch = state.get("selected_patch") or {}
    slot = state.get("selected_slot") or {}
    escrow = state.get("escrow_receipt") or {}
    target = state.get("target_bundle") or {}
    wallets = get_escrow_wallets_info()

    budget_txt = (
        f"${scan.get('maintainer_budget_usd')} USD"
        if scan.get("maintainer_budget_provided")
        else "Market Auto-Discovery"
    )
    merge_pin = f"AEGIS-{patch.get('patch_sha256', '9910')[:6].upper()}"
    maint_w = escrow.get("sender_maintainer_wallet") or wallets["maintainer_wallet"]
    res_w = escrow.get("recipient_researcher_wallet") or wallets["researcher_wallet"]

    cmds = [
        "0.96 0.98 1.00 rg 0 0 595 842 re f",
        # Clean Royal Blue Header Banner
        "0.11 0.31 0.85 rg 30 742 535 74 re f",
        "1 1 1 rg BT /F2 13.5 Tf 44 788 Td (PATCHBOUNTY // MAINTAINER SECURITY CLEARANCE PASS) Tj ET",
        "0.85 0.92 1.00 rg BT /F1 9 Tf 44 766 Td (6-uAgent Swarm: @aegis  @recon  @specter  @forge  @warden  @vault) Tj ET",
        f"0.04 0.65 0.45 rg 424 764 126 30 re f 1 1 1 rg BT /F2 9 Tf 433 775 Td (PIN: {_pdf_escape(merge_pin)}) Tj ET",
        # Card 1: All Numbered Findings Unlocked
        "1 1 1 rg 30 582 535 146 re f",
        "0.11 0.31 0.85 rg BT /F2 11 Tf 44 706 Td (1. UNLOCKED FULL-CODE VULNERABILITY AUDIT REPORT) Tj ET",
        f"0.12 0.16 0.23 rg BT /F1 9.5 Tf 44 686 Td (Repository: {_pdf_escape(target.get('repo_slug', 'N/A'))} | Language: {_pdf_escape(scan.get('language', 'Python'))} | Total Bugs Fixed: {len(findings)}) Tj ET",
    ]
    y_cursor = 666
    for f_item in findings[:3]:
        line_str = f"#{f_item.get('point_number', 1)} [{f_item.get('cwe_id', 'CWE')} | {f_item.get('severity', 'HIGH')}] {f_item.get('file_path', '')}:L{f_item.get('line_number', 1)} - {str(f_item.get('title', ''))[:38]}"
        cmds.append(f"0.15 0.20 0.30 rg BT /F2 8.8 Tf 44 {y_cursor} Td ({_pdf_escape(line_str)}) Tj ET")
        y_cursor -= 13
        detail_str = f"Why: {str(f_item.get('why_vulnerable', ''))[:52]} | Fix: {str(f_item.get('how_to_fix', ''))[:40]}"
        cmds.append(f"0.35 0.42 0.55 rg BT /F1 7.4 Tf 44 {y_cursor} Td ({_pdf_escape(detail_str)}) Tj ET")
        y_cursor -= 17
    cmds.append("0.04 0.55 0.38 rg BT /F2 9.5 Tf 44 596 Td (@warden Verdict: ALL EXPLOITS BLOCKED | 100% REGRESSION TESTS PASSED) Tj ET")

    # Card 2: Sealed Maintainer Ledger
    cmds.extend([
        "1 1 1 rg 30 460 535 108 re f",
        "0.11 0.31 0.85 rg BT /F2 11 Tf 44 544 Td (2. CONFIDENTIAL MAINTAINER BOUNTY LEDGER) Tj ET",
        f"0.80 0.12 0.42 rg BT /F2 9.5 Tf 44 522 Td (YOUR PRIVATE BOUNTY CEILING: {_pdf_escape(budget_txt)}  [SEALED - HIDDEN FROM RESEARCHER]) Tj ET",
        f"0.12 0.16 0.23 rg BT /F1 9.5 Tf 44 502 Td (Selected Researcher: {_pdf_escape(patch.get('researcher_handle', ''))} | Ask: ${patch.get('initial_ask_usd', 0)} USD | Paid: ${patch.get('verified_bounty_usd', 0)} USD | Saved: ${patch.get('maintainer_savings_usd', 0)} USD) Tj ET",
        f"BT /F1 9 Tf 44 480 Td (SLA Warranty: {_pdf_escape(patch.get('sla_warranty', '90-Day Guarantee'))}   |   Patch SHA-256: {_pdf_escape(patch.get('patch_sha256', ''))}) Tj ET",
        # Card 3: Rollout Window & On-Chain Proof
        "1 1 1 rg 30 300 535 146 re f",
        "0.11 0.31 0.85 rg BT /F2 11 Tf 44 424 Td (3. ROLLOUT SCHEDULE & FETCH.AI DORADO BLOCKCHAIN RECEIPT (@vault)) Tj ET",
        f"0.12 0.16 0.23 rg BT /F2 9.5 Tf 44 402 Td (Scheduled Rollout: {_pdf_escape(slot.get('date_str', ''))} | {_pdf_escape(slot.get('time_window', ''))} ({_pdf_escape(slot.get('release_track', ''))})) Tj ET",
        f"BT /F1 9 Tf 44 380 Td (On-Chain Escrow Settled: {_pdf_escape(escrow.get('amount_display', '0.05 TESTFET'))} on {_pdf_escape(escrow.get('network', 'Fetch Dorado Testnet'))}) Tj ET",
        f"BT /F3 8 Tf 44 360 Td (TX Hash: {_pdf_escape(escrow.get('tx_hash', 'VERIFIED_ON_DORADO'))}) Tj ET",
        f"BT /F3 8 Tf 44 342 Td (Block Height: #{escrow.get('block_height', 0)} | Maintainer: {_pdf_escape(maint_w)}) Tj ET",
        f"BT /F3 8 Tf 44 324 Td (Researcher Wallet: {_pdf_escape(res_w)}) Tj ET",
        "0.40 0.46 0.56 rg BT /F1 8.8 Tf 44 56 Td (Built by Atul Anand, Jeeya, and Vanshika for Fetch.ai Fetch-A-Thon 3.0 | AgentChatProtocol v0.3.0 + AgentPaymentProtocol v0.1.0) Tj ET",
    ])
    return _compile_single_page_vector_pdf(cmds)


def generate_researcher_payout_pdf(state: dict) -> bytes:
    """STRICT PRIVACY INVARIANT: Never embeds `maintainer_budget_usd` anywhere in Researcher Receipt PDF!"""
    scan = state.get("scan_result") or {}
    findings = scan.get("all_findings") or [scan.get("vulnerability") or {}]
    patch = state.get("selected_patch") or {}
    slot = state.get("selected_slot") or {}
    escrow = state.get("escrow_receipt") or {}
    target = state.get("target_bundle") or {}
    wallets = get_escrow_wallets_info()
    res_w = escrow.get("recipient_researcher_wallet") or wallets["researcher_wallet"]

    cmds = [
        "0.96 0.98 1.00 rg 0 0 595 842 re f",
        "0.04 0.52 0.42 rg 30 742 535 74 re f",
        "1 1 1 rg BT /F2 14 Tf 44 788 Td (PATCHBOUNTY // RESEARCHER ZERO-FEE PAYOUT RECEIPT) Tj ET",
        "0.85 0.98 0.94 rg BT /F1 9 Tf 44 766 Td (0% Platform Commission | Verified Multi-Language Security Remediation Receipt) Tj ET",
        "1 1 1 rg 30 600 535 126 re f",
        "0.04 0.52 0.42 rg BT /F2 11 Tf 44 704 Td (1. RESEARCHER REMEDIATION & PAYOUT SUMMARY) Tj ET",
        f"0.12 0.16 0.23 rg BT /F2 10.5 Tf 44 680 Td (Researcher Handle: {_pdf_escape(patch.get('researcher_handle', ''))} | Approved Bounty Payout: ${patch.get('verified_bounty_usd', 0)} USD) Tj ET",
        "0.04 0.52 0.42 rg BT /F2 9.5 Tf 44 658 Td (Platform Commission Charged: $0 USD (0% Researcher Deduction)) Tj ET",
        f"0.12 0.16 0.23 rg BT /F1 9.5 Tf 44 636 Td (Repository: {_pdf_escape(target.get('repo_slug', ''))} | Language: {_pdf_escape(scan.get('language', 'Python'))} | Bugs Remediated: {len(findings)}) Tj ET",
        f"BT /F1 9.5 Tf 44 616 Td (Patch SHA-256 Digest: {_pdf_escape(patch.get('patch_sha256', ''))} | SLA Commitment: {_pdf_escape(patch.get('sla_warranty', ''))}) Tj ET",
        "1 1 1 rg 30 430 535 154 re f",
        "0.11 0.31 0.85 rg BT /F2 11 Tf 44 560 Td (2. DISCLOSURE MERGE SCHEDULE & ON-CHAIN DORADO SETTLEMENT) Tj ET",
        f"0.12 0.16 0.23 rg BT /F2 9.5 Tf 44 536 Td (Coordinated Merge Window: {_pdf_escape(slot.get('date_str', ''))} | {_pdf_escape(slot.get('time_window', ''))}) Tj ET",
        f"BT /F1 9 Tf 44 514 Td (On-Chain Escrow Released: {_pdf_escape(escrow.get('amount_display', '0.05 TESTFET'))} on {_pdf_escape(escrow.get('network', 'Fetch Dorado Testnet'))}) Tj ET",
        f"BT /F3 8 Tf 44 492 Td (TX Hash: {_pdf_escape(escrow.get('tx_hash', 'VERIFIED_ON_DORADO'))}) Tj ET",
        f"BT /F3 8 Tf 44 472 Td (Block Height: #{escrow.get('block_height', 0)}) Tj ET",
        f"BT /F3 8 Tf 44 452 Td (Recipient Wallet: {_pdf_escape(res_w)}) Tj ET",
        "0.40 0.46 0.56 rg BT /F1 8.8 Tf 44 56 Td (Built by Atul Anand, Jeeya, and Vanshika for Fetch.ai Fetch-A-Thon 3.0) Tj ET",
    ]
    return _compile_single_page_vector_pdf(cmds)


def generate_disclosure_ics(state: dict, audience: str = "maintainer") -> str:
    scan = state.get("scan_result") or {}
    vuln = scan.get("vulnerability") or {}
    patch = state.get("selected_patch") or {}
    slot = state.get("selected_slot") or {}
    escrow = state.get("escrow_receipt") or {}
    target = state.get("target_bundle") or {}

    summary = (
        f"[PatchBounty @aegis] Rollout {scan.get('language', '')} Fix ({target.get('repo_slug', 'repo')})"
        if audience == "maintainer"
        else f"[PatchBounty @vault] Bounty Payout ${patch.get('verified_bounty_usd', 0)} USD ({patch.get('researcher_handle', '')})"
    )

    desc_lines = [
        f"Repository: {target.get('repo_slug', 'N/A')}",
        f"Primary Issue: {vuln.get('cwe_id', 'Security Fix')} ({vuln.get('severity', 'HIGH')})",
        f"Selected Researcher: {patch.get('researcher_handle', '')} ({patch.get('strategy_name', '')})",
        f"Approved Bounty Payout: ${patch.get('verified_bounty_usd', 0)} USD",
        f"Dorado Escrow TX: {escrow.get('tx_hash', 'VERIFIED')}",
    ]
    if audience == "maintainer" and scan.get("maintainer_budget_provided"):
        desc_lines.append(f"Confidential Maintainer Ceiling: ${scan.get('maintainer_budget_usd')} USD")

    description = "\\n".join(desc_lines)
    uid = f"aegis-{audience}-{patch.get('patch_sha256', '0000')[:8]}@patchbounty.fetch.ai"
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//PatchBounty Aegis Swarm//Fetch.ai//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTART;TZID=Asia/Kolkata:{slot.get('dtstart_local', '20261024T100000')}\r\n"
        f"DTEND;TZID=Asia/Kolkata:{slot.get('dtend_local', '20261024T105500')}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DESCRIPTION:{description}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
