import React, { useEffect, useRef, useState } from "react";

const DEMO_PRESETS = [
  {
    label: "🛡️ Clean Safe Code ($0 Free)",
    target: "https://github.com/jonschlinkert/is-odd",
    desc: "Clean bug-free repository. 0 bugs, 0 payment required.",
  },
  {
    label: "⚡ E-Commerce Store (3 Bugs)",
    target: "express_checkout_api",
    desc: "Node.js checkout service with SQL injection, RCE, and leaked secrets.",
  },
  {
    label: "💰 FinTech Banking & UPI (SQLi)",
    target: "fintech_ledger_api",
    desc: "Python & SQLite banking ledger with admin vault bypass.",
  },
  {
    label: "🌐 Vulnerable Web App (DSVW)",
    target: "https://github.com/stamparm/DSVW",
    desc: "Damn Simple Vulnerable Web App — multi-bug public repo.",
  },
  {
    label: "💎 DeFi Staking Vault (Web3)",
    target: "defi_staking_vault",
    desc: "Solidity smart contract with reentrancy drain and tx.origin flaw.",
  },
];

export default function App() {
  const [appState, setAppState] = useState(null);
  const [activeStep, setActiveStep] = useState(1); // 1: Scan, 2: Findings, 3: Pricing, 4: Payment, 5: Resolution
  const [targetInput, setTargetInput] = useState("");
  const [customCode, setCustomCode] = useState("");
  const [showCodeInput, setShowCodeInput] = useState(false);
  const [busy, setBusy] = useState(false);

  // Negotiation & Fix Selection
  const [counterOfferInput, setCounterOfferInput] = useState("");
  const [selectedPatchId, setSelectedPatchId] = useState("patch_kestrel");

  // Post-payment delivery
  const [emailInput, setEmailInput] = useState("");
  const [delivering, setDelivering] = useState(false);

  // Modals & Chat
  const [showSettings, setShowSettings] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);
  const [chatMessage, setChatMessage] = useState("");

  // Settings & SMTP
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [ghTokenInput, setGhTokenInput] = useState("");
  const [avKeyInput, setAvKeyInput] = useState("");
  const [smtpHostInput, setSmtpHostInput] = useState("smtp.gmail.com");
  const [smtpPortInput, setSmtpPortInput] = useState("587");
  const [smtpUserInput, setSmtpUserInput] = useState("");
  const [smtpPassInput, setSmtpPassInput] = useState("");
  const [smtpFromInput, setSmtpFromInput] = useState("");
  const [testEmailInput, setTestEmailInput] = useState("");
  const [testingSmtp, setTestingSmtp] = useState(false);
  const [smtpFeedback, setSmtpFeedback] = useState(null);

  const chatEndRef = useRef(null);

  const fetchState = async () => {
    try {
      const res = await fetch("/api/state");
      const data = await res.json();
      setAppState(data);
      if (data?.smtp_status?.host && !smtpUserInput) {
        setSmtpHostInput(data.smtp_status.host);
        setSmtpPortInput(data.smtp_status.port?.toString() || "587");
        if (data.smtp_status.from_addr) setSmtpFromInput(data.smtp_status.from_addr);
      }
      syncStepWithState(data);
    } catch (err) {
      console.error("State fetch error:", err);
    }
  };

  const syncStepWithState = (st) => {
    if (!st) return;
    if (st.phase === "SETTLED") {
      setActiveStep(5);
    } else if (st.solution_verified_pass) {
      setActiveStep(4);
    } else if (st.deal_approved || st.scan_result?.candidates?.length > 0) {
      if (activeStep < 2) setActiveStep(2);
    }
  };

  useEffect(() => {
    fetchState();
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws`);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "state" && msg.state) {
          setAppState(msg.state);
          syncStepWithState(msg.state);
        }
      } catch (e) {
        // ignore malformed
      }
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [appState?.chat_history?.length, showChat]);

  // Actions
  const handleStartScan = async (targetOverride) => {
    const tgt = targetOverride || targetInput.trim();
    if (!tgt && !customCode.trim()) return;
    setBusy(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: tgt.startsWith("http") ? tgt : `Audit ${tgt}`,
          target_hint: tgt.startsWith("http") ? "" : tgt,
          inline_code: customCode,
          force_scan: true,
        }),
      });
      const data = await res.json();
      setAppState(data);
      if (data.scan_result?.is_clean_code) {
        setActiveStep(2);
      } else if (data.scan_result?.total_bugs_found > 0) {
        setActiveStep(2);
      }
    } finally {
      setBusy(false);
    }
  };

  const handleSendCounterOffer = async () => {
    const val = parseInt(counterOfferInput, 10);
    if (!val || val <= 0) return;
    setBusy(true);
    try {
      const res = await fetch("/api/negotiate-bounty", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ counter_offer_usd: val }),
      });
      const data = await res.json();
      setAppState(data);
    } finally {
      setBusy(false);
      setCounterOfferInput("");
    }
  };

  const handleVerifyInSandbox = async (patchId) => {
    setBusy(true);
    try {
      const res = await fetch("/api/approve-solution", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patch_id: patchId || selectedPatchId }),
      });
      const data = await res.json();
      setAppState(data);
      if (data.solution_verified_pass) {
        setActiveStep(4);
      }
    } finally {
      setBusy(false);
    }
  };

  const handlePayEscrow = async () => {
    setBusy(true);
    try {
      const res = await fetch("/api/confirm-bounty", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      setAppState(data);
      if (data.escrow_unlocked) {
        setActiveStep(5);
      }
    } finally {
      setBusy(false);
    }
  };

  const handleResolveAndDeliver = async () => {
    if (!emailInput.trim()) {
      alert("Please enter an email address for your resolution report.");
      return;
    }
    setDelivering(true);
    try {
      const res = await fetch("/api/resolve-and-deliver", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipient_email: emailInput.trim(),
          create_pr: true,
          notify_email: true,
        }),
      });
      const data = await res.json();
      setAppState(data);
    } finally {
      setDelivering(false);
    }
  };

  const handleReset = async () => {
    if (!confirm("Start a new audit session?")) return;
    setBusy(true);
    try {
      const res = await fetch("/api/reset", { method: "POST" });
      const data = await res.json();
      setAppState(data);
      setActiveStep(1);
      setTargetInput("");
      setCustomCode("");
    } finally {
      setBusy(false);
    }
  };

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;
    const msg = chatMessage;
    setChatMessage("");
    setBusy(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      setAppState(data);
    } finally {
      setBusy(false);
    }
  };

  const handleSaveSettings = async (e) => {
    if (e) e.preventDefault();
    await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        asi_one_api_key: apiKeyInput || null,
        github_token: ghTokenInput || null,
        agentverse_api_key: avKeyInput || null,
        smtp_host: smtpHostInput || null,
        smtp_port: smtpPortInput || null,
        smtp_user: smtpUserInput || null,
        smtp_pass: smtpPassInput || null,
        smtp_from: smtpFromInput || null,
      }),
    });
    await fetchState();
    setShowSettings(false);
    alert("Settings & SMTP Configuration saved successfully!");
  };

  const handleTestSmtp = async () => {
    const target = (testEmailInput || emailInput).trim();
    if (!target) {
      alert("Please enter a recipient email address below to receive the test verification email.");
      return;
    }
    setTestingSmtp(true);
    setSmtpFeedback(null);
    try {
      // Auto-save any typed SMTP settings first so the backend has them
      await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          smtp_host: smtpHostInput || null,
          smtp_port: smtpPortInput || null,
          smtp_user: smtpUserInput || null,
          smtp_pass: smtpPassInput || null,
          smtp_from: smtpFromInput || null,
        }),
      });

      const res = await fetch("/api/test-smtp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipient_email: target }),
      });
      const data = await res.json();
      setSmtpFeedback(data);
      if (data.ok) {
        alert(`✅ Test email delivered successfully to ${target}! Please check your inbox/spam folder.`);
      } else {
        alert(`❌ SMTP Test Failed: ${data.reason}\n\nTip: For Gmail, ensure 2-Step Verification is enabled and use a 16-character 'App Password'.`);
      }
    } catch (err) {
      alert(`Error sending test email: ${err.message}`);
    } finally {
      setTestingSmtp(false);
      fetchState();
    }
  };

  const scan = appState?.scan_result;
  const isClean = scan?.is_clean_code;
  const findings = scan?.all_findings || [];
  const candidates = scan?.candidates || [];
  const selectedPatch = appState?.selected_patch;
  const escrow = appState?.escrow_receipt;
  const wallets = appState?.wallets;
  const isSettled = appState?.phase === "SETTLED" && escrow?.verified;

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* 1. TOP NAVBAR */}
      <header className="app-navbar">
        <div className="navbar-inner">
          <div className="brand-group">
            <div className="brand-icon-badge">🛡️</div>
            <div>
              <div className="brand-title">
                PatchBounty <span className="brand-tag">@aegis</span>
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                Autonomous Security Bounty &amp; Zero-Leak Escrow
              </div>
            </div>
          </div>

          <div className="nav-actions">
            <button className="btn-secondary" onClick={() => setShowSettings(true)}>
              ⚙️ Settings
            </button>
            <button className="btn-secondary" onClick={handleReset} disabled={busy}>
              🔄 New Scan
            </button>
          </div>
        </div>
      </header>

      {/* 2. PROGRESS STEPPER (5-STEP SIMPLE JOURNEY) */}
      <div className="stepper-container">
        <nav className="stepper-bar">
          <div
            className={`step-item ${activeStep === 1 ? "active" : ""} ${scan ? "completed" : ""}`}
            onClick={() => setActiveStep(1)}
          >
            <div className="step-number">1</div>
            <div className="step-text">
              <span className="step-title">Scan Repository</span>
              <span className="step-sub">Enter URL or Demo</span>
            </div>
          </div>

          <div
            className={`step-item ${activeStep === 2 ? "active" : ""} ${scan ? "completed" : ""}`}
            onClick={() => scan && setActiveStep(2)}
          >
            <div className="step-number">2</div>
            <div className="step-text">
              <span className="step-title">Security Findings</span>
              <span className="step-sub">{isClean ? "0 Bugs (Clean)" : `${findings.length} Discovered`}</span>
            </div>
          </div>

          <div
            className={`step-item ${activeStep === 3 ? "active" : ""} ${appState?.solution_verified_pass ? "completed" : ""}`}
            onClick={() => scan && !isClean && setActiveStep(3)}
          >
            <div className="step-number">3</div>
            <div className="step-text">
              <span className="step-title">Review &amp; Price</span>
              <span className="step-sub">Fair Benchmark vs AI</span>
            </div>
          </div>

          <div
            className={`step-item ${activeStep === 4 ? "active" : ""} ${isSettled ? "completed" : ""}`}
            onClick={() => appState?.solution_verified_pass && setActiveStep(4)}
          >
            <div className="step-number">4</div>
            <div className="step-text">
              <span className="step-title">Secure Escrow</span>
              <span className="step-sub">0.05 TESTFET</span>
            </div>
          </div>

          <div
            className={`step-item ${activeStep === 5 ? "active" : ""}`}
            onClick={() => isSettled && setActiveStep(5)}
          >
            <div className="step-number">5</div>
            <div className="step-text">
              <span className="step-title">Get Fixes &amp; PR</span>
              <span className="step-sub">Automated Delivery</span>
            </div>
          </div>
        </nav>
      </div>

      {/* 3. MAIN WIZARD CONTENT */}
      <main className="main-content">
        {/* STEP 1: SCAN REPO */}
        {activeStep === 1 && (
          <div className="content-card">
            <div className="card-header">
              <h1 className="card-title">🔍 Scan Any Codebase or GitHub Repository</h1>
              <p className="card-subtitle">
                Our 6 autonomous Fetch.ai security agents inspect every line of source code, verify genuine exploits in
                sandboxes, and prepare verified fixes. Commented code and whitespace are never reported as bugs.
              </p>
            </div>

            <div className="scan-hero-box">
              <div className="scan-input-row">
                <input
                  type="text"
                  className="url-input"
                  placeholder="Paste GitHub Repository URL (e.g. https://github.com/stamparm/DSVW)"
                  value={targetInput}
                  onChange={(e) => setTargetInput(e.target.value)}
                  disabled={busy}
                  onKeyDown={(e) => e.key === "Enter" && handleStartScan()}
                />
                <button
                  className="btn-primary"
                  onClick={() => handleStartScan()}
                  disabled={busy || (!targetInput.trim() && !customCode.trim())}
                  style={{ minWidth: "160px" }}
                >
                  {busy ? "Scanning Entire Codebase..." : "🔍 Scan Entire Project"}
                </button>
              </div>

              <div className="sample-chips-label">Or Pick a 1-Click Demo Repository to Test:</div>
              <div className="sample-chips-row">
                {DEMO_PRESETS.map((p) => (
                  <button
                    key={p.target}
                    className="sample-chip"
                    onClick={() => {
                      setTargetInput(p.target);
                      handleStartScan(p.target);
                    }}
                    disabled={busy}
                    title={p.desc}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Optional Raw Code Accordion */}
            <div style={{ marginTop: "16px" }}>
              <button
                className="btn-secondary"
                onClick={() => setShowCodeInput((v) => !v)}
              >
                {showCodeInput ? "▲ Hide Direct Code Input" : "▼ Or Paste Code Directly / Upload File"}
              </button>

              {showCodeInput && (
                <div style={{ marginTop: "14px", background: "var(--bg-input)", padding: "16px", borderRadius: "var(--radius-md)" }}>
                  <textarea
                    rows={6}
                    className="url-input"
                    style={{ width: "100%", fontFamily: "monospace", fontSize: "13px" }}
                    placeholder="Paste raw Python, JS, Solidity, Java, or Go snippet here..."
                    value={customCode}
                    onChange={(e) => setCustomCode(e.target.value)}
                  />
                  <div style={{ marginTop: "10px", display: "flex", justifyContent: "flex-end" }}>
                    <button
                      className="btn-primary"
                      onClick={() => handleStartScan()}
                      disabled={busy || !customCode.trim()}
                    >
                      Audit Pasted Code
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* STEP 2: FINDINGS REPORT */}
        {activeStep === 2 && (
          <div className="content-card">
            <div className="card-header">
              <h1 className="card-title">
                {isClean ? "🎉 Clean Code Security Clearance" : "⚠️ Security Findings & Vulnerability Audit"}
              </h1>
              <p className="card-subtitle">
                Repository: <strong>{appState?.target_bundle?.repo_slug || "Target Code"}</strong> |{" "}
                Files Inspected: <strong>{scan?.files_scanned_count || 1}</strong> | Coverage:{" "}
                <strong>100% of All Lines Scanned</strong>
              </p>
            </div>

            {isClean ? (
              <div style={{ background: "var(--success-bg)", border: "1px solid var(--border-success)", padding: "28px", borderRadius: "var(--radius-lg)", textAlign: "center" }}>
                <div style={{ fontSize: "48px", marginBottom: "12px" }}>✅</div>
                <h2 style={{ color: "#10B981", fontSize: "22px", fontWeight: 800, marginBottom: "8px" }}>
                  Your Code is 100% Secure &amp; Clean!
                </h2>
                <p style={{ color: "var(--text-main)", maxWidth: "600px", margin: "0 auto 20px", fontSize: "14.5px" }}>
                  All source files passed @recon AST/sink inspection and @specter sandbox checks with{" "}
                  <strong>zero exploitable vulnerabilities</strong>. No payment or code changes are required ($0).
                </p>
                <button className="btn-secondary" onClick={() => setActiveStep(1)}>
                  Scan Another Repository
                </button>
              </div>
            ) : (
              <>
                <div style={{ background: "rgba(2, 132, 199, 0.12)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "var(--radius-md)", padding: "14px 18px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                  <div>
                    <strong style={{ color: "#38BDF8" }}>{findings.length} Real Vulnerabilities Detected</strong>
                    <div style={{ fontSize: "12.5px", color: "var(--text-muted)" }}>
                      Each vulnerability has been confirmed in an isolated sandbox. Solutions are sealed on the server until payment.
                    </div>
                  </div>
                  <button className="btn-primary" onClick={() => setActiveStep(3)}>
                    Review Pricing &amp; Fix Options ➡️
                  </button>
                </div>

                <div className="findings-grid">
                  {findings.map((f, idx) => (
                    <div key={idx} className="finding-card">
                      <div className="finding-header">
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                          <span className="finding-point-badge">Bug #{f.point_number || idx + 1}</span>
                          <span className="finding-title">{f.title || f.blind_category || "Security Vulnerability"}</span>
                        </div>
                        <div style={{ display: "flex", gap: "8px" }}>
                          <span className={`severity-pill severity-${(f.severity || "HIGH").toLowerCase()}`}>
                            {f.severity || "HIGH"}
                          </span>
                          <span style={{ fontSize: "11px", fontWeight: 700, padding: "3px 8px", background: "var(--bg-input)", borderRadius: "6px", color: "var(--text-muted)" }}>
                            {f.cwe_id || "CWE-Security"}
                          </span>
                        </div>
                      </div>

                      <p className="finding-desc">{f.summary || f.blind_impact}</p>

                      {isSettled ? (
                        <div style={{ marginTop: "14px", background: "rgba(16, 185, 129, 0.1)", border: "1px solid var(--border-success)", padding: "12px 16px", borderRadius: "var(--radius-md)" }}>
                          <div style={{ color: "#10B981", fontWeight: 700, fontSize: "13px", marginBottom: "4px" }}>
                            🔓 UNLOCKED EXPLANATION &amp; CODE LOCATION:
                          </div>
                          <div style={{ fontSize: "13px", color: "var(--text-main)", lineHeight: 1.6 }}>
                            <strong>Why It Happens:</strong> {f.why_vulnerable}
                            <br />
                            <strong>Remediation:</strong> {f.how_to_fix}
                          </div>
                        </div>
                      ) : (
                        <div className="locked-solution-banner">
                          <span className="locked-text">
                            🔒 Solution, exact line numbers &amp; fixed code are securely sealed on the server (HTTP 402).
                          </span>
                          <span style={{ fontSize: "11px", color: "var(--text-subtle)", fontFamily: "monospace" }}>
                            SHA-256 Proof: {f.proof_hash ? f.proof_hash.slice(0, 16) + "..." : "SEALED"}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* STEP 3: REVIEW PRICING & CHOOSE FIX */}
        {activeStep === 3 && (
          <div className="content-card">
            <div className="card-header">
              <h1 className="card-title">⚖️ Fair Market Pricing &amp; Fix Selection</h1>
              <p className="card-subtitle">
                Compare traditional human bug-bounty rates (HackerOne / Bugcrowd medians from live NIST NVD data)
                against our autonomous AI researcher rates. No upfront budget required — submit any fair counter-offer!
              </p>
            </div>

            <div className="pricing-comparison-grid">
              <div className="pricing-card">
                <div className="pricing-title">Traditional Human Bug Bounty</div>
                <div className="pricing-amount">${scan?.market_benchmark?.human_market_avg_usd || 2650}</div>
                <div className="pricing-sub">
                  Median market payout on HackerOne &amp; Bugcrowd.
                  <br />
                  ⚠️ <strong>Report ONLY — Does NOT include code fixes!</strong>
                  <br />
                  Turnaround: 7 - 14 Days
                </div>
              </div>

              <div className="pricing-card featured">
                <span className="pricing-card-badge">
                  {scan?.market_benchmark?.savings_vs_market_pct || 90}% SAVINGS
                </span>
                <div className="pricing-title">PatchBounty Autonomous AI Quote</div>
                <div className="pricing-amount" style={{ color: "#38BDF8" }}>
                  ${candidates[0]?.verified_bounty_usd || 185} USD
                </div>
                <div className="pricing-sub">
                  Includes full multi-bug code patches + isolated sandbox exploit verification!
                  <br />
                  Turnaround: Instantaneous (Seconds)
                </div>
              </div>
            </div>

            {/* Counter-Offer Negotiation */}
            <div className="negotiate-box">
              <div style={{ fontWeight: 700, fontSize: "14px", marginBottom: "8px" }}>
                🤝 Negotiate Your Price (Make a Counter-Offer)
              </div>
              <div style={{ fontSize: "12.5px", color: "var(--text-muted)", marginBottom: "12px" }}>
                Our agents automatically accept fair offers down to honest CVSS severity floors ($140 Critical, $90 High, $55 Medium).
              </div>
              <div className="negotiate-row">
                <input
                  type="number"
                  className="url-input"
                  style={{ maxWidth: "220px" }}
                  placeholder="e.g. 160"
                  value={counterOfferInput}
                  onChange={(e) => setCounterOfferInput(e.target.value)}
                  disabled={busy}
                />
                <button
                  className="btn-secondary"
                  onClick={handleSendCounterOffer}
                  disabled={busy || !counterOfferInput.trim()}
                >
                  Send Counter-Offer
                </button>
                {appState?.deal_approved && (
                  <span style={{ color: "#10B981", fontWeight: 700, fontSize: "13px" }}>
                    ✅ Negotiated Deal Approved!
                  </span>
                )}
              </div>
            </div>

            {/* Choose Fix Strategy */}
            <div style={{ marginTop: "24px" }}>
              <div style={{ fontWeight: 700, fontSize: "15px", marginBottom: "12px" }}>
                Select Your Remediation Strategy:
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "12px" }}>
                {candidates.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => setSelectedPatchId(c.id)}
                    style={{
                      background: selectedPatchId === c.id ? "rgba(2, 132, 199, 0.15)" : "var(--bg-subtle)",
                      border: selectedPatchId === c.id ? "2px solid #0284C7" : "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-lg)",
                      padding: "16px",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                      <strong style={{ color: selectedPatchId === c.id ? "#38BDF8" : "#FFFFFF" }}>
                        {c.strategy_name}
                      </strong>
                      <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-muted)" }}>
                        {c.researcher_handle}
                      </span>
                    </div>
                    <div style={{ fontSize: "12.5px", color: "var(--text-muted)", lineHeight: 1.5, marginBottom: "10px" }}>
                      {c.summary}
                    </div>
                    <div style={{ fontSize: "12px", color: "#10B981", fontWeight: 700 }}>
                      Price: ${c.verified_bounty_usd} USD
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ marginTop: "28px", display: "flex", justifyContent: "flex-end" }}>
              <button
                className="btn-success"
                onClick={() => handleVerifyInSandbox(selectedPatchId)}
                disabled={busy}
              >
                {busy ? "Running Sandbox Exploit Duel..." : "🧪 Verify Fix in Sandbox & Proceed to Payment ➡️"}
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: PAYMENT ON DORADO TESTNET */}
        {activeStep === 4 && (
          <div className="content-card">
            <div className="card-header">
              <h1 className="card-title">💳 Secure Escrow Settlement on Fetch.ai Dorado</h1>
              <p className="card-subtitle">
                Payment is held in a trustless smart escrow contract on the Fetch.ai Dorado Testnet (`dorado-1`).
                Settlement cost is only <strong>0.05 TESTFET</strong> (testnet tokens).
              </p>
            </div>

            <div className="escrow-wallet-card">
              <div style={{ fontWeight: 800, fontSize: "15px", color: "#10B981", display: "flex", alignItems: "center", gap: "8px" }}>
                <span>✅ Sandbox Verification Passed</span>
                <span style={{ fontSize: "11px", padding: "2px 8px", background: "rgba(16, 185, 129, 0.2)", borderRadius: "999px" }}>
                  100% EXPLOITS BLOCKED
                </span>
              </div>
              <p style={{ fontSize: "13.5px", color: "var(--text-muted)", marginTop: "6px" }}>
                Agent @warden fired all baseline exploit vectors at the patched code in an isolated subprocess.
                All attacks were stopped with zero code regressions.
              </p>

              <div className="balance-grid">
                <div className="balance-tile">
                  <div className="balance-label">Your Wallet (Maintainer Treasury)</div>
                  <div className="balance-value">
                    {wallets?.maintainer_balance_fet || "10.0000"} <span style={{ fontSize: "13px" }}>TESTFET</span>
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--text-subtle)", fontFamily: "monospace", marginTop: "4px" }}>
                    {wallets?.maintainer_wallet?.slice(0, 16)}...
                  </div>
                </div>

                <div className="balance-tile">
                  <div className="balance-label">Escrow Seller Wallet (@vault)</div>
                  <div className="balance-value" style={{ color: "#38BDF8" }}>
                    {wallets?.researcher_balance_fet || "0.0000"} <span style={{ fontSize: "13px" }}>TESTFET</span>
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--text-subtle)", fontFamily: "monospace", marginTop: "4px" }}>
                    {wallets?.researcher_wallet?.slice(0, 16)}...
                  </div>
                </div>
              </div>
            </div>

            {/* Coordinated Calendar Slot Selection */}
            <div style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)", padding: "20px", borderRadius: "var(--radius-lg)", marginBottom: "24px" }}>
              <div style={{ fontWeight: 700, fontSize: "14px", marginBottom: "6px" }}>
                📅 Choose Coordinated Disclosure Release Window (IST)
              </div>
              <div style={{ fontSize: "12.5px", color: "var(--text-muted)", marginBottom: "12px" }}>
                Ensures zero downtime by aligning the patch rollout with low-traffic staging windows.
              </div>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                {(appState?.disclosure_slots || []).slice(0, 4).map((slot) => (
                  <div
                    key={slot.id}
                    style={{
                      background: "var(--bg-input)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                      padding: "10px 14px",
                      fontSize: "12.5px",
                    }}
                  >
                    <strong>{slot.day_label}</strong>: {slot.time_window}
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
              <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                Cost: <strong style={{ color: "#FFFFFF" }}>0.05 TESTFET</strong> (~$0 USD testnet tokens)
              </div>
              <button
                className="btn-accent"
                onClick={handlePayEscrow}
                disabled={busy}
                style={{ fontSize: "15px", padding: "14px 28px" }}
              >
                {busy ? "Settling On Fetch Dorado Blockchain..." : "💳 Pay 0.05 TESTFET & Unlock Full Fixes"}
              </button>
            </div>
          </div>
        )}

        {/* STEP 5: AUTOMATED RESOLUTION & DELIVERY */}
        {activeStep === 5 && (
          <div className="content-card">
            <div className="card-header">
              <h1 className="card-title">🚀 All Issues Resolved — Automated Delivery</h1>
              <p className="card-subtitle">
                Payment settled on Dorado testnet! TX:{" "}
                <a
                  href={escrow?.explorer_url || `https://companion.fetch.ai/dorado-1/transactions/${escrow?.tx_hash}`}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: "#38BDF8", fontWeight: 700 }}
                >
                  {escrow?.tx_hash || "TX_DORADO_VERIFIED"} ↗
                </a>
              </p>
            </div>

            <div className="resolution-box">
              <h2 style={{ fontSize: "18px", fontWeight: 800, color: "#FFFFFF", marginBottom: "8px" }}>
                1-Click GitHub Pull Request &amp; Email Delivery
              </h2>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", lineHeight: 1.6, marginBottom: "16px" }}>
                Enter your email below. We will push a fix branch (`patchbounty/fix-...`) to your repo, open a Pull Request,
                and send you a comprehensive resolution report. (If you haven't added a write-access GitHub token, you will
                receive a ready All-Fixes.zip bundle instead).
              </p>

              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px", flexWrap: "wrap" }}>
                {appState?.smtp_status?.configured ? (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(16, 185, 129, 0.15)", color: "#10B981", border: "1px solid rgba(16, 185, 129, 0.3)", padding: "4px 12px", borderRadius: "12px", fontSize: "12px", fontWeight: 700 }}>
                    🟢 Live SMTP Mailer Active ({appState.smtp_status.host}:{appState.smtp_status.port})
                  </span>
                ) : (
                  <span
                    onClick={() => setShowSettings(true)}
                    style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(245, 158, 11, 0.15)", color: "#F59E0B", border: "1px solid rgba(245, 158, 11, 0.3)", padding: "4px 12px", borderRadius: "12px", fontSize: "12px", fontWeight: 700, cursor: "pointer" }}
                    title="Click to configure SMTP credentials"
                  >
                    🟡 Live SMTP Not Configured (Click to set up Gmail/SMTP or receive instant .eml draft + downloads)
                  </span>
                )}
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowSettings(true)}
                  style={{ padding: "3px 10px", fontSize: "11px" }}
                >
                  ⚙️ Configure SMTP Settings
                </button>
              </div>

              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
                <input
                  type="email"
                  className="url-input"
                  style={{ maxWidth: "340px" }}
                  placeholder="Your Email (e.g. maintainer@company.com)"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  disabled={delivering}
                />
                <button
                  className="btn-accent"
                  onClick={handleResolveAndDeliver}
                  disabled={delivering || !emailInput.trim()}
                >
                  {delivering ? "Creating PR & Generating Report..." : "🚀 Fix All, Create PR & Email Report"}
                </button>
              </div>

              {appState?.resolution_delivery && (
                <div style={{ marginTop: "16px", background: "var(--bg-input)", padding: "16px", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontWeight: 800, color: "#10B981", fontSize: "14px", marginBottom: "6px" }}>
                    ✅ Delivery Complete — {appState.resolution_delivery.total_bugs_fixed} Vulnerabilities Remediated
                  </div>
                  <div style={{ fontSize: "13px", color: "var(--text-main)", lineHeight: 1.6 }}>
                    {appState.resolution_delivery.pr?.pr_url ? (
                      <div>
                        <strong>GitHub Pull Request:</strong>{" "}
                        <a href={appState.resolution_delivery.pr.pr_url} target="_blank" rel="noreferrer" style={{ color: "#38BDF8", fontWeight: 700 }}>
                          {appState.resolution_delivery.pr.pr_url} ↗
                        </a>
                      </div>
                    ) : (
                      <div>
                        <strong>GitHub PR:</strong> {appState.resolution_delivery.pr?.status} — {appState.resolution_delivery.pr?.reason}
                      </div>
                    )}
                    <div>
                      <strong>Email Status:</strong>{" "}
                      {appState.resolution_delivery.email?.status === "SENT" ? (
                        <span style={{ color: "#10B981", fontWeight: 700 }}>
                          ✅ Delivered via SMTP to {appState.resolution_delivery.email?.recipient} (with HTML advisory &amp; All-Fixes.zip attached)!
                        </span>
                      ) : (
                        <span>
                          {appState.resolution_delivery.email?.status} — {appState.resolution_delivery.email?.reason}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Instant Download Artifacts */}
            <div>
              <div style={{ fontWeight: 700, fontSize: "15px", marginBottom: "10px" }}>
                📦 Instant Deliverables &amp; Downloads:
              </div>
              <div className="download-buttons-grid">
                <a href="/api/artifacts/all-fixes.zip" className="btn-primary" style={{ textDecoration: "none" }}>
                  📦 Download All-Fixes.zip (Code + Patches)
                </a>
                <a href="/api/artifacts/resolution-report.md" className="btn-secondary" style={{ textDecoration: "none" }}>
                  📝 Download Resolution Report (.md)
                </a>
                <a href="/api/artifacts/clearance.pdf" className="btn-secondary" style={{ textDecoration: "none" }}>
                  📄 Executive Security Certificate (.pdf)
                </a>
                {appState?.resolution_eml_ready && (
                  <a href="/api/artifacts/resolution-email.eml" className="btn-secondary" style={{ textDecoration: "none" }}>
                    ✉️ Download Email Draft (.eml)
                  </a>
                )}
                <a href="/api/artifacts/maintainer.ics" className="btn-secondary" style={{ textDecoration: "none" }}>
                  📅 Add Rollout to Calendar (.ics)
                </a>
              </div>
            </div>
          </div>
        )}

        {/* OPTIONAL TECHNICAL TELEMETRY ACCORDION FOR JUDGES & ENGINEERS */}
        <div style={{ marginTop: "32px", textAlign: "center" }}>
          <button
            className="btn-secondary"
            onClick={() => setShowTechDetails((v) => !v)}
            style={{ fontSize: "12px" }}
          >
            {showTechDetails ? "▲ Hide Technical Details & Agent Telemetry" : "▼ Inspect 6-uAgent Mesh & Technical Details (For Judges & Developers)"}
          </button>

          {showTechDetails && (
            <div style={{ marginTop: "16px", textAlign: "left", background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "20px" }}>
              <h3 style={{ fontSize: "15px", fontWeight: 800, marginBottom: "12px", color: "#38BDF8" }}>
                Active Fetch.ai 6-uAgent Mesh Roster:
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "10px" }}>
                {(appState?.agents || []).map((ag) => (
                  <div key={ag.handle} style={{ background: "var(--bg-subtle)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                    <div style={{ fontWeight: 800, color: "#FFFFFF" }}>{ag.handle} ({ag.name})</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>{ag.role}</div>
                    <div style={{ fontSize: "10.5px", color: "var(--text-subtle)", fontFamily: "monospace", marginTop: "4px" }}>
                      Port {ag.port} | {ag.address}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* 4. FLOATING AI ASSISTANT (@aegis CHAT) */}
      <div className="floating-chat-bubble">
        <button className="chat-fab-btn" onClick={() => setShowChat((v) => !v)}>
          💬 {showChat ? "Close Chat" : "Ask @aegis AI"}
        </button>

        {showChat && (
          <div className="chat-drawer">
            <div className="chat-drawer-head">
              <strong style={{ fontSize: "14px", color: "#38BDF8" }}>@aegis AI Security Assistant</strong>
              <button className="close-btn" onClick={() => setShowChat(false)}>✕</button>
            </div>

            <div className="chat-messages-scroll">
              {(appState?.chat_history || []).map((item, idx) => (
                <div key={idx} className={`chat-bubble ${item.role === "user" ? "user" : "assistant"}`}>
                  <div style={{ fontSize: "11px", fontWeight: 700, marginBottom: "3px", opacity: 0.8 }}>
                    {item.agent || (item.role === "user" ? "You" : "@aegis")}
                  </div>
                  <div>{item.text}</div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            <form onSubmit={handleSendChat} className="chat-input-row">
              <input
                type="text"
                className="chat-input-field"
                placeholder="Ask about vulnerabilities, escrow, or code in Eng / Hinglish..."
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                disabled={busy}
              />
              <button type="submit" className="btn-primary" style={{ padding: "6px 14px", fontSize: "13px" }} disabled={busy}>
                Send
              </button>
            </form>
          </div>
        )}
      </div>

      {/* 5. SETTINGS MODAL */}
      {showSettings && (
        <div className="modal-backdrop" onClick={() => setShowSettings(false)}>
          <div className="modal-window" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: "18px", fontWeight: 800 }}>Connect API Keys (Optional)</h3>
              <button className="close-btn" onClick={() => setShowSettings(false)}>✕</button>
            </div>
            <form onSubmit={handleSaveSettings}>
              <div className="form-field">
                <label className="form-label">ASI:ONE API KEY (FOR DUAL LLM REASONING)</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="asi1-..."
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                />
              </div>

              <div className="form-field">
                <label className="form-label">GITHUB TOKEN (FOR WRITE/PR CREATION)</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="ghp_..."
                  value={ghTokenInput}
                  onChange={(e) => setGhTokenInput(e.target.value)}
                />
              </div>

              <div className="form-field">
                <label className="form-label">AGENTVERSE API KEY (FOR CLOUD MAILBOX)</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="eyJ..."
                  value={avKeyInput}
                  onChange={(e) => setAvKeyInput(e.target.value)}
                />
              </div>

              {/* SMTP Settings */}
              <div style={{ marginTop: "24px", paddingTop: "16px", borderTop: "1px solid var(--border-subtle)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <div style={{ fontWeight: 800, fontSize: "14px", color: "#38BDF8" }}>
                    📧 SMTP Email Mailer (Send Real Resolution Reports)
                  </div>
                  {appState?.smtp_status?.configured ? (
                    <span style={{ fontSize: "11px", color: "#10B981", fontWeight: 700 }}>● Active</span>
                  ) : (
                    <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>○ Not Configured</span>
                  )}
                </div>
                <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "14px", lineHeight: 1.5 }}>
                  Deliver the complete vulnerability audit report and <code>All-Fixes.zip</code> directly to maintainers.
                  Works with Gmail (16-char App Password), Outlook, Amazon SES, SendGrid, etc.
                </p>

                <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "10px", marginBottom: "10px" }}>
                  <div className="form-field" style={{ margin: 0 }}>
                    <label className="form-label">SMTP HOST</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="smtp.gmail.com"
                      value={smtpHostInput}
                      onChange={(e) => setSmtpHostInput(e.target.value)}
                    />
                  </div>
                  <div className="form-field" style={{ margin: 0 }}>
                    <label className="form-label">PORT</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="587 (TLS) or 465 (SSL)"
                      value={smtpPortInput}
                      onChange={(e) => setSmtpPortInput(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-field">
                  <label className="form-label">SMTP USERNAME / EMAIL</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="your-email@gmail.com"
                    value={smtpUserInput}
                    onChange={(e) => setSmtpUserInput(e.target.value)}
                  />
                </div>

                <div className="form-field">
                  <label className="form-label">SMTP PASSWORD / APP PASSWORD</label>
                  <input
                    type="password"
                    className="form-input"
                    placeholder="16-character Google App Password (e.g. xxxx yyyy zzzz wwww)"
                    value={smtpPassInput}
                    onChange={(e) => setSmtpPassInput(e.target.value)}
                  />
                </div>

                <div className="form-field">
                  <label className="form-label">SENDER ADDRESS (SMTP_FROM)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="PatchBounty Security <security@yourdomain.com>"
                    value={smtpFromInput}
                    onChange={(e) => setSmtpFromInput(e.target.value)}
                  />
                </div>

                <div style={{ background: "var(--bg-subtle)", padding: "12px", borderRadius: "8px", marginTop: "12px", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "12px", fontWeight: 700, marginBottom: "6px" }}>
                    🧪 Send Test Verification Email
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <input
                      type="email"
                      className="form-input"
                      placeholder="Recipient email to receive test message"
                      value={testEmailInput}
                      onChange={(e) => setTestEmailInput(e.target.value)}
                      style={{ fontSize: "12.5px" }}
                    />
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={handleTestSmtp}
                      disabled={testingSmtp || (!testEmailInput.trim() && !emailInput.trim())}
                      style={{ whiteSpace: "nowrap", fontSize: "12px" }}
                    >
                      {testingSmtp ? "Sending..." : "Send Test Ping"}
                    </button>
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "20px" }}>
                <button type="button" className="btn-secondary" onClick={() => setShowSettings(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save All Settings &amp; SMTP
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
