# PatchBounty (@aegis) — Autonomous Multi-Agent Security Bounty & Zero-Leak Escrow Studio

**Built by Atul Anand, Jeeya, and Vanshika for Fetch-A-Thon 3.0**

---

## NEW in v5.1 — Full-Repo Scan, Comment-Safe Scanner, Dynamic Findings (Judge Notes)

1. **Pura GitHub Repo Scan (Ek File Nahi!):** Jab koi `github.com/owner/repo` URL deta hai, to
   @recon poora repository archive download karke **repo ki HAR supported source file** —
   kitne bhi folder/page/file ho — line-by-line check karta hai. Pehle wali top-8 file shortlist
   hata di gayi hai. Sirf `node_modules/ vendor/ dist/ build/ .git/` jaise dependency/generated
   folder skip hote hain (woh repo ka apna code nahi hota). UI me `repo_scan` coverage dikhta hai:
   kitni files mili, kitni scan hui, kitni skip hui.
2. **Comment Kabhi Bug Nahi:** Ek comment-stripper (strings ka pura dhyan rakh ke, line number
   badle bina) pehle saare `//`, `/* */`, `#`, `--` comment hata deta hai. Comment me likha
   purana vulnerable example, TODO, ya documentation snippet **kabhi finding nahi banta**.
   Sirf asli executable code hi scan hota hai.
3. **Dynamic Findings (Static Copy-Paste Khatm):** Har bug ka title, blind impact, aur payment
   ke baad wala `Kyu Hai Ye Bug` explanation usi file ki **asli line, asli sink-API, asli
   variable aur asli function** se banta hai. Code badlo ya GitHub URL badlo — har scan ki
   report alag aur usi code ke hisaab se banti hai, same keywords repeat nahi hote.
4. **Payment Ke Baad Asli Error + Kyu + Solution:** Payment se pehle sirf numbered blind
   points + blue blurred vault dikhta hai (file/line/code/why — sab sealed, `HTTP 402`).
   `0.05 TESTFET` Dorado payment ke baad Page 2 par har bug ke liye khulta hai:
   **asli file + line + asli vulnerable code + "Kyu Hai Ye Bug" + "Solution"**, saath me
   **har file ka alag fixed code** (`file_fixes`) aur unified diff.
5. **Agent Seed = V3 (Original):** `@aegis` ka seed wapas original
   `patchbounty-aegis-command-coordinator-v3` hai (address
   `agent1qv8eua2vnj3znmggn66hjr3j2zgzqe5nusc6z2e35whglfx3c3yjgeftf4x`, Port `8022`).

---

## NEW in v6 — Payment Ke Baad Auto-Resolution: GitHub PR + Email Report

Pura flow ab end-to-end hai:

```text
GitHub Link -> Full-Repo Scan -> Numbered List -> Bargain -> Sandbox PASS
-> 0.05 TESTFET Payment -> FIX ALL + GitHub PR + Email Report
```

Payment confirm hone ke baad **Page 4** par naya panel aata hai —
**"RESOLVE ALL ISSUES — GITHUB PR + EMAIL REPORT"**:

1. Email address do (report wahi jayegi) aur ek click: **FIX ALL, CREATE PR & EMAIL REPORT**.
2. **GitHub PR:** Agar `Connect API Keys` me us repo par **WRITE access wala GitHub token** hai,
   to system nayi branch `patchbounty/fix-...` push karke asal **Pull Request** bana deta hai —
   har fixed file usme commit hoti hai, PR body me poori report (issue + kyu + resolution) hoti hai.
3. **Token/Access na ho to fail nahi hota:** ready **All-Fixes.zip** ban jata hai (har file ka
   fixed code + `.patch` + report) — `git apply` karke khud PR bana sakte ho. Wajah screen par saaf likhi milti hai.
4. **Email:** `.env` me SMTP (`SMTP_HOST/SMTP_USER/SMTP_PASS`, Gmail App Password chalega) ho to
   report **asal me send** hoti hai. SMTP na ho to jhootha "sent" nahi bola jata — ready **.eml draft**
   download banta hai, kisi bhi mail app se bhej sakte ho.
5. Downloads (sirf payment ke baad, warna HTTP 402): `RESOLUTION_REPORT.md` (har issue + resolution),
   `All-Fixes.zip`, aur email draft `.eml`.

## Quick Start on Windows PowerShell (Exact 2 Terminals — Same as DealSetu!)

### Terminal 1 — Start PatchBounty Web Studio + API (`http://127.0.0.1:8002`)
```powershell
cd C:\Users\HP\Desktop\hackethon\project-2-patchbounty
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002
```
Open **`http://127.0.0.1:8002`** -> Click **`Connect API Keys`** in top-right header -> Paste your `ASI_ONE_API_KEY`!

---

### Terminal 2 — Deploy All 6 Fetch.ai uAgents in Coordinated Bureau & Agentverse Mailbox
Open a **second PowerShell window** in the same folder (`project-2-patchbounty`) and run:
```powershell
cd C:\Users\HP\Desktop\hackethon\project-2-patchbounty
.venv\Scripts\activate
python deploy_swarm.py
```
*(Or simply double-click **`deploy_swarm.bat`** or **`connect_agentverse.bat`**!)*

1. Terminal 2 launches the **Fetch.ai Bureau** hosting all 6 agents (`@aegis`, `@recon`, `@specter`, `@forge`, `@warden`, `@vault`) running concurrently with inter-agent coordination protocols.
2. It prints clickable Inspector URLs:
   `https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8022&address=agent1q...`
   *(You can also click **`Open @aegis in Agentverse Inspector ↗`** directly inside the Web UI!)*
3. In your browser on `agentverse.ai`, click **`Connect`** -> choose **`Mailbox`** -> Done!
4. Copy `@aegis`'s `agent1q...` address into **`https://asi1.ai`** chat — every live chat on `asi1.ai` triggers the full coordinated multi-agent pipeline and syncs straight onto your local `http://127.0.0.1:8002` dashboard!

---

## Live Stage Demo Cheat-Sheet (Test Both Clean & Buggy Code in 30 Seconds!)

1. **Clean / Bug-Free Safe Repo (`0 Bugs -> Green Safe Card -> NO LOCK -> $0 Payment`):**
   - Paste GitHub URL: `https://github.com/jonschlinkert/is-odd` (or click **`Clean Safe Code ($0 Test)`** chip on Page 1).
2. **Vulnerable Multi-Bug GitHub Repo (`7 Real Bugs -> Blue Blurred Vault Lock -> Bargain -> Sandbox PASS -> Pay 0.05 TESTFET`):**
   - Paste GitHub URL: `https://github.com/stamparm/DSVW`
   - Go to **Page 2 (`Audit Report`)** -> Show numbered blind bugs + **Blue Blurred Locked Solution Vault**
   - Go to **Page 3 (`Negotiate`)** -> Compare **Live Industry Market Benchmark vs AI Quotes**, send counter-offer (e.g. `160`), and click **`Verify Solution in Sandbox & Lock Bid`** (`PASS`)
   - Go to **Page 4 (`Calendar & Pay`)** -> Pick IST slot -> Click **`Pay 0.05 TESTFET & Unblur Full Solution`** -> Watch **Buyer Wallet `-0.0500 TESTFET` Deducted** & **Escrow Seller Wallet `+0.0500 TESTFET` Credited** LIVE on screen + click **`Verify on Dorado Block Explorer ↗`**!
# patchBounty
