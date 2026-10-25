import React, { useEffect, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Award,
  CheckCircle2,
  Copy,
  Cpu,
  ExternalLink,
  FileCode2,
  GitPullRequest,
  KeyRound,
  Layers,
  MessageSquare,
  RefreshCw,
  RotateCcw,
  Send,
  ShieldAlert,
  Sparkles,
  Terminal,
  Users,
  Wallet,
  X,
} from 'lucide-react';
import {
  AgentInfo,
  CandidatePatch,
  ChatItem,
  EnvelopeTrace,
  PaymentState,
  ReproductionReport,
  RuntimeConfig,
  WalletsSnapshot,
} from './types';
import { InteractiveCardRenderer } from './components/InteractiveCardRenderer';

const QUICK_BOUNTIES = [
  {
    label: 'Ledger Float Drift #418 (0.05 FET)',
    prompt: 'Fix fintech-core/ledger-settlement #418 IEEE-754 penny drift and negative refund bug',
  },
  {
    label: 'JWT alg:none Bypass #904 (0.05 FET)',
    prompt: 'Fix auth-gateway/token-guard #904 JWT alg none bypass and expiry off-by-one bug',
  },
  {
    label: 'Sliding Rate Limiter #267 (0.05 FET)',
    prompt: 'Fix api-edge/sliding-limiter #267 ZeroDivisionError and stale window burst leak',
  },
  {
    label: 'Guided Bounty Form Card (card_kind="form")',
    prompt: 'form',
  },
];

export const App: React.FC = () => {
  const [config, setConfig] = useState<RuntimeConfig | null>(null);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [wallets, setWallets] = useState<WalletsSnapshot | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatItem[]>([]);
  const [envelopeTrace, setEnvelopeTrace] = useState<EnvelopeTrace[]>([]);
  const [repro, setRepro] = useState<ReproductionReport | null>(null);
  const [rankedPatches, setRankedPatches] = useState<CandidatePatch[]>([]);
  const [paymentState, setPaymentState] = useState<PaymentState>({ stage: 'idle' });

  const [inputText, setInputText] = useState('');
  const [busy, setBusy] = useState(false);
  const [centerTab, setCenterTab] = useState<'patches' | 'repro' | 'envelopes'>('patches');
  const [mobileTab, setMobileTab] = useState<'chat' | 'sandbox' | 'ledger'>('chat');
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showAgentsModal, setShowAgentsModal] = useState(false);

  const [asiKeyInput, setAsiKeyInput] = useState('');
  const [asiModelInput, setAsiModelInput] = useState('asi1-mini');
  const [avKeyInput, setAvKeyInput] = useState('');
  const [customTxHash, setCustomTxHash] = useState('');
  const [showCustomTxBox, setShowCustomTxBox] = useState(false);

  const chatContainerRef = useRef<HTMLDivElement | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      if (data.ok) {
        setConfig(data.config);
        setAsiModelInput(data.config.asi_one_model || 'asi1-mini');
        setAgents(data.agents || []);
        setWallets(data.wallets || null);
        setChatHistory(data.chat_history || []);
        setEnvelopeTrace(data.envelope_trace || []);
        setRepro(data.reproduction_report || null);
        setRankedPatches(data.ranked_patches || []);
        setPaymentState(data.payment_state || { stage: 'idle' });
      }
    } catch (err) {
      console.error('Status fetch error:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/events`);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'chat_message') {
          setChatHistory((prev) => {
            if (prev.some((x) => x.id === msg.payload.id)) return prev;
            return [...prev, msg.payload];
          });
        } else if (msg.type === 'envelope') {
          setEnvelopeTrace((prev) => [...prev, msg.payload]);
        } else if (msg.type === 'reproduction_complete') {
          setRepro(msg.payload);
        } else if (msg.type === 'patches_ready') {
          setRepro(msg.payload.repro);
          setRankedPatches(msg.payload.ranked_patches || []);
        } else if (msg.type === 'payment_state') {
          setPaymentState(msg.payload);
        } else if (msg.type === 'config_updated') {
          setConfig(msg.payload);
        } else if (msg.type === 'session_reset') {
          setChatHistory([]);
          setEnvelopeTrace([]);
          setRepro(null);
          setRankedPatches([]);
          setPaymentState({ stage: 'idle' });
        }
      } catch {
        // ignore parse errors
      }
    };
    const pingTimer = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping');
    }, 15000);
    return () => {
      clearInterval(pingTimer);
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || busy) return;
    setBusy(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText }),
      });
      const data = await res.json();
      if (data.ok) {
        setChatHistory(data.chat_history || []);
        setRepro(data.reproduction_report || null);
        setRankedPatches(data.ranked_patches || []);
        setPaymentState(data.payment_state || { stage: 'idle' });
        setEnvelopeTrace(data.envelope_trace || []);
      }
    } finally {
      setBusy(false);
    }
  };

  const handleSettle = async (explicitHash?: string) => {
    setBusy(true);
    try {
      const res = await fetch('/api/payment/settle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tx_hash: explicitHash || null }),
      });
      const data = await res.json();
      if (data.ok) {
        setPaymentState(data.payment_state);
        if (data.wallets) setWallets(data.wallets);
        if (data.chat_history) setChatHistory(data.chat_history);
      }
    } finally {
      setBusy(false);
    }
  };

  const handleTestCancelGuardrail = async () => {
    setBusy(true);
    try {
      const res = await fetch('/api/payment/test-cancel', { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        setPaymentState(data.payment_state);
        if (data.chat_history) setChatHistory(data.chat_history);
      }
    } finally {
      setBusy(false);
    }
  };

  const handleRefreshWallets = async () => {
    setBusy(true);
    try {
      const res = await fetch('/api/wallets/faucet', { method: 'POST' });
      const data = await res.json();
      setWallets(data);
    } finally {
      setBusy(false);
    }
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asi_one_api_key: asiKeyInput || undefined,
          asi_one_model: asiModelInput,
          agentverse_api_key: avKeyInput || undefined,
        }),
      });
      const data = await res.json();
      if (data.ok) {
        setConfig(data.config);
        setShowConfigModal(false);
      }
    } finally {
      setBusy(false);
    }
  };

  const handleReset = async () => {
    await fetch('/api/reset', { method: 'POST' });
    fetchStatus();
  };

  const bestPatch = rankedPatches[0] || null;
  const canSettle =
    rankedPatches.length > 0 &&
    paymentState.stage !== 'completed' &&
    paymentState.stage !== 'broadcasting';

  return (
    <div className="min-h-screen flex flex-col bg-[#F5F7FB] text-[#0B1221]">
      {/* TOP BAR */}
      <header className="sticky top-0 z-30 bg-white border-b border-[#E2E8F0] px-4 lg:px-6 py-3">
        <div className="max-w-[1440px] mx-auto flex flex-wrap items-center justify-between gap-2.5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#0B1221] flex items-center justify-center shrink-0">
              <GitPullRequest className="w-5 h-5 text-[#60A5FA]" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-base font-extrabold tracking-tight text-[#0B1221]">
                  PatchBounty
                </span>
                <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded-full bg-[#EFF6FF] text-[#1D4ED8] border border-[#BFDBFE]">
                  Fetch.ai Ecosystem
                </span>
              </div>
              <p className="text-xs text-[#64748B]">
                Autonomous Bug Reproduction, Sandboxed Pytest Swarm &amp; On-Chain Dorado Bounty Escrow
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => setShowAgentsModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] hover:bg-[#EFF6FF] text-xs font-semibold text-[#0B1221] cursor-pointer"
            >
              <Cpu className="w-3.5 h-3.5 text-[#1D4ED8]" />
              <span>6 Active uAgents</span>
            </button>

            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#A7F3D0] bg-[#ECFDF5] text-xs font-semibold text-[#065F46]">
              <span className="w-2 h-2 rounded-full bg-[#10B981]" />
              <span>Dorado Testnet Live</span>
            </div>

            <button
              type="button"
              onClick={() => setShowConfigModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#CBD5E1] bg-white hover:bg-[#F8FAFC] text-xs font-semibold text-[#0B1221] cursor-pointer"
            >
              <KeyRound className="w-3.5 h-3.5 text-[#1D4ED8]" />
              <span>API &amp; Mailbox Setup</span>
            </button>

            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-[#E2E8F0] bg-white hover:bg-[#F8FAFC] text-xs font-semibold text-[#475569] cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          </div>
        </div>
      </header>

      {/* QUICK LAUNCH BAR */}
      <div className="bg-white border-b border-[#E2E8F0] px-4 lg:px-6 py-2 overflow-x-auto">
        <div className="max-w-[1440px] mx-auto flex items-center gap-2 whitespace-nowrap">
          <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-[#1D4ED8] mr-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Quick Bounties:</span>
          </span>
          {QUICK_BOUNTIES.map((qb, i) => (
            <button
              key={i}
              type="button"
              disabled={busy}
              onClick={() => sendMessage(qb.prompt)}
              className="px-3 py-1 rounded-full border border-[#CBD5E1] bg-[#F8FAFC] hover:bg-[#1D4ED8] hover:text-white hover:border-[#1D4ED8] text-xs font-medium text-[#0B1221] transition cursor-pointer disabled:opacity-50"
            >
              {qb.label}
            </button>
          ))}
        </div>
      </div>

      {/* MAIN 3-COLUMN STUDIO GRID (RESPONSIVE ON MOBILE & DESKTOP) */}
      <main className="flex-1 max-w-[1440px] w-full mx-auto px-4 lg:px-6 py-4 pb-20 lg:pb-5 grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* LEFT COLUMN (5 cols): ASI:ONE CHAT & INTERACTIVE CARDS */}
        <section
          className={`lg:col-span-5 flex-col ${
            mobileTab === 'chat' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-2xs flex flex-col h-[560px] lg:h-[690px]">
            <div className="px-4 py-3 border-b border-[#E2E8F0] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-[#1D4ED8]" />
                <div>
                  <h2 className="text-xs font-bold uppercase tracking-wider text-[#0B1221]">
                    ASI:One Maintainer Chat &amp; Cards
                  </h2>
                  <p className="text-[11px] text-[#64748B]">
                    AgentChatProtocol v0.3.0 • Handle:{' '}
                    <span className="font-mono text-[#1D4ED8]">@patchbounty_coordinator</span>
                  </p>
                </div>
              </div>
              <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded bg-[#F1F5F9] text-[#334155]">
                card_protocol v1
              </span>
            </div>

            <div
              ref={chatContainerRef}
              className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-[#FAFBFD]"
            >
              {chatHistory.length === 0 ? (
                <div className="my-auto rounded-xl border border-dashed border-[#CBD5E1] bg-white p-6 text-center space-y-2.5">
                  <div className="w-10 h-10 rounded-full bg-[#EFF6FF] text-[#1D4ED8] flex items-center justify-center mx-auto">
                    <Terminal className="w-5 h-5" />
                  </div>
                  <h3 className="text-sm font-bold text-[#0B1221]">
                    Ready to Reproduce &amp; Patch Open-Source Bugs
                  </h3>
                  <p className="text-xs text-[#475569] leading-relaxed max-w-md mx-auto">
                    Click any Quick Bounty above or describe a repository bug below. PatchBounty
                    runs failing pytest suites inside an isolated sandbox, dispatches 3 competing
                    Solver uAgents in parallel, verifies AST safety + 100% test pass, and releases
                    Fetch Dorado TESTFET directly to the winning agent wallet.
                  </p>
                </div>
              ) : (
                chatHistory.map((item) => (
                  <div
                    key={item.id}
                    className={`flex flex-col ${
                      item.role === 'user' ? 'items-end' : 'items-start'
                    }`}
                  >
                    <div
                      className={`max-w-[95%] rounded-xl px-3.5 py-2.5 text-xs leading-relaxed ${
                        item.role === 'user'
                          ? 'bg-[#1D4ED8] text-white'
                          : 'bg-white border border-[#E2E8F0] text-[#0B1221] w-full shadow-2xs'
                      }`}
                    >
                      <div
                        className={`flex items-center justify-between gap-2 text-[10px] font-semibold uppercase tracking-wider mb-1 ${
                          item.role === 'user' ? 'text-[#DBEAFE]' : 'text-[#64748B]'
                        }`}
                      >
                        <span>{item.sender_label}</span>
                        <span>{item.timestamp}</span>
                      </div>
                      <p className="whitespace-pre-wrap break-words">{item.text}</p>
                      {item.card_kind && (
                        <InteractiveCardRenderer
                          cardKind={item.card_kind}
                          cardPayload={item.card_payload}
                          rawAcpWire={item.raw_acp_wire}
                          onCardAction={(act) => sendMessage(act)}
                          disabled={busy}
                        />
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                const msg = inputText;
                setInputText('');
                sendMessage(msg);
              }}
              className="p-3 bg-white border-t border-[#E2E8F0] flex items-center gap-2"
            >
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Describe repo bug or issue (e.g. Fix ledger float penny drift #418)..."
                className="flex-1 rounded-lg border border-[#CBD5E1] bg-[#F8FAFC] px-3 py-2 text-xs text-[#0B1221] focus:bg-white focus:border-[#1D4ED8] focus:outline-none"
              />
              <button
                type="submit"
                disabled={busy || !inputText.trim()}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[#1D4ED8] hover:bg-[#1E40AF] text-white text-xs font-semibold transition cursor-pointer disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send</span>
              </button>
            </form>
          </div>
        </section>

        {/* CENTER COLUMN (4 cols): SANDBOX VERIFICATION, UNIFIED DIFFS & PYTEST LOGS */}
        <section
          className={`lg:col-span-4 flex-col gap-3 ${
            mobileTab === 'sandbox' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {/* 3 KPI Tiles */}
          <div className="grid grid-cols-3 gap-2.5">
            <div className="bg-white rounded-xl border border-[#FECACA] p-3">
              <div className="text-[10.5px] font-semibold uppercase tracking-wide text-[#DC2626]">
                Baseline Bug
              </div>
              <div className="text-base font-bold text-[#DC2626] mt-1 tabular-nums">
                {repro ? `${repro.failed}/${repro.total} FAIL` : '—'}
              </div>
              <div className="text-[10.5px] text-[#64748B] mt-0.5 truncate">
                {repro ? `${repro.duration_ms}ms pytest` : 'Pre-Patch Run'}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-[#BFDBFE] p-3">
              <div className="text-[10.5px] font-semibold uppercase tracking-wide text-[#1D4ED8]">
                Verified Fix
              </div>
              <div className="text-base font-bold text-[#1D4ED8] mt-1 tabular-nums">
                {bestPatch ? `${bestPatch.passed}/${bestPatch.total} PASS` : '—'}
              </div>
              <div className="text-[10.5px] text-[#475569] mt-0.5 truncate">
                {bestPatch ? bestPatch.solver_agent_name : '3x Solver uAgents'}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-[#A7F3D0] p-3">
              <div className="text-[10.5px] font-semibold uppercase tracking-wide text-[#059669]">
                AST Security
              </div>
              <div className="text-base font-bold text-[#059669] mt-1 tabular-nums">
                {bestPatch ? `${bestPatch.score}%` : '—'}
              </div>
              <div className="text-[10.5px] font-semibold text-[#047857] mt-0.5 truncate">
                {bestPatch ? '0 Unsafe Calls' : 'Static Audit'}
              </div>
            </div>
          </div>

          {/* Center Panel */}
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-2xs flex flex-col h-[598px]">
            <div className="px-3.5 py-2.5 border-b border-[#E2E8F0] flex items-center justify-between gap-2">
              <div className="inline-flex rounded-lg bg-[#F1F5F9] p-0.5 shrink-0">
                <button
                  type="button"
                  onClick={() => setCenterTab('patches')}
                  className={`px-2.5 py-1 rounded-md text-xs font-semibold whitespace-nowrap cursor-pointer ${
                    centerTab === 'patches'
                      ? 'bg-white text-[#0B1221] shadow-2xs'
                      : 'text-[#64748B]'
                  }`}
                >
                  Solvers (3x)
                </button>
                <button
                  type="button"
                  onClick={() => setCenterTab('repro')}
                  className={`px-2.5 py-1 rounded-md text-xs font-semibold whitespace-nowrap cursor-pointer ${
                    centerTab === 'repro'
                      ? 'bg-white text-[#0B1221] shadow-2xs'
                      : 'text-[#64748B]'
                  }`}
                >
                  Pytest Log
                </button>
                <button
                  type="button"
                  onClick={() => setCenterTab('envelopes')}
                  className={`px-2.5 py-1 rounded-md text-xs font-semibold whitespace-nowrap cursor-pointer ${
                    centerTab === 'envelopes'
                      ? 'bg-white text-[#0B1221] shadow-2xs'
                      : 'text-[#64748B]'
                  }`}
                >
                  Trace ({envelopeTrace.length})
                </button>
              </div>
              {repro && (
                <span className="text-[10.5px] font-mono text-[#475569] truncate">
                  {repro.repo_slug} {repro.issue_number}
                </span>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-3.5 space-y-3 bg-[#FAFBFD]">
              {centerTab === 'patches' &&
                (rankedPatches.length > 0 ? (
                  rankedPatches.map((p) => (
                    <div
                      key={p.id}
                      className={`rounded-xl bg-white border p-3 space-y-2 ${
                        p.rank === 1 ? 'border-[#93C5FD]' : 'border-[#E2E8F0]'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#EFF6FF] text-[#1D4ED8]">
                            {p.lane} • #{p.rank}
                          </span>
                          <span className="text-xs font-bold text-[#0B1221]">{p.name}</span>
                        </div>
                        <span className="text-[10.5px] font-bold text-[#059669]">
                          {p.passed}/{p.total} PASSED ({p.duration_ms}ms)
                        </span>
                      </div>

                      <p className="text-[11px] text-[#475569]">{p.rationale}</p>

                      <div className="flex items-center justify-between text-[10.5px] text-[#64748B] font-mono bg-[#F8FAFC] px-2.5 py-1 rounded border border-[#F1F5F9]">
                        <span>
                          +{p.lines_added} / -{p.lines_removed} ({p.module_filename})
                        </span>
                        <span className="text-[#059669] font-sans font-semibold">{p.ast_note}</span>
                      </div>

                      <div className="rounded-lg bg-[#0B1221] p-2.5 overflow-x-auto max-h-36">
                        <pre className="text-[10px] font-mono leading-relaxed">
                          {p.unified_diff.split('\n').map((ln, idx) => (
                            <div
                              key={idx}
                              className={
                                ln.startsWith('+')
                                  ? 'text-[#4ADE80]'
                                  : ln.startsWith('-')
                                  ? 'text-[#F87171]'
                                  : ln.startsWith('@@')
                                  ? 'text-[#60A5FA]'
                                  : 'text-[#CBD5E1]'
                              }
                            >
                              {ln}
                            </div>
                          ))}
                        </pre>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 text-[#64748B] space-y-2">
                    <Layers className="w-7 h-7 text-[#94A3B8]" />
                    <div className="text-xs font-bold text-[#334155]">
                      Parallel Solver Sandbox Standby
                    </div>
                    <p className="text-[11px]">
                      Submit a repository issue to reproduce failing pytest assertions and run
                      Solver Alpha, Beta &amp; Gamma in isolated sandboxes.
                    </p>
                  </div>
                ))}

              {centerTab === 'repro' && (
                <div className="space-y-3">
                  {repro ? (
                    <>
                      <div className="rounded-lg border border-[#FECACA] bg-[#FEF2F2] p-3 text-xs text-[#991B1B]">
                        <div className="font-bold flex items-center gap-1.5">
                          <ShieldAlert className="w-4 h-4" />
                          <span>
                            Pre-Patch Failure Confirmed ({repro.failed}/{repro.total} Failed in{' '}
                            {repro.duration_ms}ms)
                          </span>
                        </div>
                        <pre className="mt-2 p-2.5 rounded bg-[#0B1221] text-[#FCA5A5] text-[10px] font-mono overflow-x-auto whitespace-pre-wrap">
                          {repro.output}
                        </pre>
                      </div>
                      {bestPatch && (
                        <div className="rounded-lg border border-[#A7F3D0] bg-[#ECFDF5] p-3 text-xs text-[#065F46]">
                          <div className="font-bold">
                            Post-Patch Regression Suite ({bestPatch.passed}/{bestPatch.total} Passed
                            in {bestPatch.duration_ms}ms)
                          </div>
                          <pre className="mt-2 p-2.5 rounded bg-[#0B1221] text-[#86EFAC] text-[10px] font-mono overflow-x-auto whitespace-pre-wrap">
                            {bestPatch.pytest_output}
                          </pre>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-xs text-[#64748B] text-center py-12">
                      No sandbox pytest logs recorded yet.
                    </div>
                  )}
                </div>
              )}

              {centerTab === 'envelopes' &&
                (envelopeTrace.length > 0 ? (
                  envelopeTrace.map((env) => (
                    <div
                      key={env.id}
                      className="rounded-lg bg-white border border-[#E2E8F0] p-2.5 text-xs space-y-1"
                    >
                      <div className="flex justify-between font-bold text-[#1D4ED8] text-[11px]">
                        <span>{env.protocol}</span>
                        <span className="text-[#64748B] font-normal">{env.timestamp}</span>
                      </div>
                      <div className="text-[10.5px] font-mono text-[#64748B]">
                        {env.sender} -&gt; {env.recipient}
                      </div>
                      <p className="text-[11px] text-[#0B1221]">{env.summary}</p>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-[#64748B] text-center py-12">
                    No uAgent protocol envelopes recorded yet.
                  </div>
                ))}
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN (3 cols): DORADO BOUNTY WALLETS & AGENT PAYMENT PROTOCOL */}
        <section
          className={`lg:col-span-3 flex-col gap-3 ${
            mobileTab === 'ledger' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {/* Dorado Wallets Card */}
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-2xs p-3.5 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Wallet className="w-4 h-4 text-[#1D4ED8]" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-[#0B1221]">
                  Dorado Bounty Wallets
                </h2>
              </div>
              <button
                type="button"
                onClick={handleRefreshWallets}
                className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#1D4ED8] hover:underline cursor-pointer"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Sync / Faucet</span>
              </button>
            </div>

            {wallets ? (
              <div className="space-y-2">
                <div className="rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] p-2.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold text-[#0B1221]">Maintainer Escrow (Buyer)</span>
                    <a
                      href={wallets.coordinator_wallet.explorer_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-0.5 text-[#1D4ED8] font-semibold"
                    >
                      <span>Explorer</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  </div>
                  <div className="text-sm font-extrabold text-[#0B1221] mt-0.5 tabular-nums">
                    {wallets.coordinator_wallet.balance_fet.toFixed(4)}{' '}
                    <span className="text-[10.5px] font-semibold text-[#64748B]">TESTFET</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-[#64748B] mt-1">
                    <span className="truncate">{wallets.coordinator_wallet.address}</span>
                    <button
                      type="button"
                      onClick={() =>
                        navigator.clipboard?.writeText(wallets.coordinator_wallet.address)
                      }
                      className="ml-1 text-[#475569] hover:text-[#0B1221] cursor-pointer"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                  </div>
                </div>

                {Object.values(wallets.solver_wallets).map((sw) => (
                  <div
                    key={sw.agent_key}
                    className="rounded-lg border border-[#E2E8F0] bg-white px-2.5 py-2 flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0">
                      <div className="text-[11px] font-bold text-[#0B1221] truncate">
                        {sw.agent_name}
                      </div>
                      <div className="text-[9.5px] font-mono text-[#64748B] truncate">
                        {sw.address}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-xs font-extrabold text-[#059669] tabular-nums">
                        {sw.balance_fet.toFixed(4)}
                      </div>
                      <a
                        href={sw.explorer_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[9.5px] font-semibold text-[#1D4ED8] hover:underline"
                      >
                        TESTFET -&gt;
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-[#64748B] py-4 text-center">
                Querying Fetch Dorado Ledger...
              </div>
            )}
          </div>

          {/* AgentPaymentProtocol v0.1.0 Card */}
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-2xs p-3.5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-[#1D4ED8]" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-[#0B1221]">
                  Payment Protocol v0.1.0
                </h2>
              </div>
              <span
                className={`text-[10.5px] font-bold uppercase px-2 py-0.5 rounded-full ${
                  paymentState.stage === 'completed'
                    ? 'bg-[#ECFDF5] text-[#047857]'
                    : paymentState.stage === 'cancelled'
                    ? 'bg-[#FEF2F2] text-[#DC2626]'
                    : paymentState.stage === 'idle'
                    ? 'bg-[#F1F5F9] text-[#64748B]'
                    : 'bg-[#FFFBEB] text-[#B45309]'
                }`}
              >
                {paymentState.stage}
              </span>
            </div>

            <ol className="space-y-1.5 text-xs">
              {[
                {
                  label: '1. Solver Emits RequestPayment',
                  done: ['requested', 'broadcasting', 'completed', 'cancelled'].includes(
                    paymentState.stage
                  ),
                },
                {
                  label: '2. Maintainer Dorado Broadcast',
                  done: ['completed', 'cancelled'].includes(paymentState.stage),
                },
                {
                  label: '3. CommitPayment + cosmpy Query',
                  done: ['completed', 'cancelled'].includes(paymentState.stage),
                },
                {
                  label:
                    paymentState.stage === 'cancelled'
                      ? '4. Solver Emitted CancelPayment'
                      : '4. Solver Emits CompletePayment',
                  done: paymentState.stage === 'completed',
                  failed: paymentState.stage === 'cancelled',
                },
              ].map((s, idx) => (
                <li
                  key={idx}
                  className={`flex items-center justify-between px-2.5 py-1.5 rounded border text-[11.5px] ${
                    s.failed
                      ? 'border-[#FECACA] bg-[#FEF2F2] text-[#991B1B] font-semibold'
                      : s.done
                      ? 'border-[#A7F3D0] bg-[#ECFDF5] text-[#065F46] font-semibold'
                      : 'border-[#E2E8F0] bg-[#F8FAFC] text-[#64748B]'
                  }`}
                >
                  <span>{s.label}</span>
                  {s.done && <CheckCircle2 className="w-3.5 h-3.5 text-[#059669] shrink-0" />}
                  {s.failed && <AlertTriangle className="w-3.5 h-3.5 text-[#DC2626] shrink-0" />}
                </li>
              ))}
            </ol>

            {paymentState.stage === 'cancelled' && paymentState.error_reason && (
              <div className="rounded-lg border border-[#FECACA] bg-[#FEF2F2] p-2.5 text-[11px] text-[#991B1B] space-y-1">
                <div className="font-bold">CancelPayment Triggered (Ledger Guardrail):</div>
                <p>{paymentState.error_reason}</p>
              </div>
            )}

            {paymentState.stage === 'completed' && paymentState.bounty_receipt && (
              <div className="rounded-lg border border-[#86EFAC] bg-[#F0FDF4] p-3 space-y-2 text-xs">
                <div className="flex items-center justify-between font-bold text-[#14532D]">
                  <span>Bounty Paid On-Chain</span>
                  <span>Block #{paymentState.bounty_receipt.block_height}</span>
                </div>
                <div className="p-2 rounded bg-white border border-[#BBF7D0] font-mono text-[10px] break-all text-[#166534]">
                  TX: {paymentState.bounty_receipt.tx_hash}
                </div>
                <a
                  href={paymentState.bounty_receipt.explorer_url}
                  target="_blank"
                  rel="noreferrer"
                  className="w-full py-2 px-3 rounded-lg bg-[#059669] hover:bg-[#047857] text-white font-semibold flex items-center justify-center gap-1.5 transition"
                >
                  <span>Verify on Dorado Block Explorer</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
                <a
                  href={paymentState.bounty_receipt.patch_download_url}
                  download
                  className="w-full py-2 px-3 rounded-lg border border-[#16A34A] bg-white hover:bg-[#F0FDF4] text-[#15803D] font-semibold flex items-center justify-center gap-1.5 transition"
                >
                  <FileCode2 className="w-3.5 h-3.5" />
                  <span>Download Signed .patch File</span>
                </a>
              </div>
            )}

            <button
              type="button"
              disabled={!canSettle || busy}
              onClick={() => handleSettle()}
              className="w-full py-2.5 px-3 rounded-lg bg-[#1D4ED8] hover:bg-[#1E40AF] text-white text-xs font-semibold transition cursor-pointer disabled:opacity-50"
            >
              Release 0.05 TESTFET Bounty (Live On-Chain)
            </button>

            <button
              type="button"
              disabled={!canSettle || busy}
              onClick={() => setShowCustomTxBox((v) => !v)}
              className="w-full py-2 px-3 rounded-lg border border-[#CBD5E1] bg-white hover:bg-[#F8FAFC] text-xs font-semibold text-[#0B1221] transition cursor-pointer disabled:opacity-50"
            >
              ASI Browser Wallet / Custom TX Hash
            </button>

            {showCustomTxBox && (
              <div className="space-y-1.5 pt-1">
                <input
                  type="text"
                  value={customTxHash}
                  onChange={(e) => setCustomTxHash(e.target.value)}
                  placeholder="Paste 64-hex Dorado TX hash..."
                  className="w-full rounded border border-[#CBD5E1] px-2.5 py-1.5 text-xs font-mono"
                />
                <button
                  type="button"
                  onClick={() => handleSettle(customTxHash)}
                  className="w-full py-1.5 rounded bg-[#0B1221] text-white text-xs font-semibold cursor-pointer"
                >
                  Submit &amp; Verify TX Hash
                </button>
              </div>
            )}

            <button
              type="button"
              disabled={!canSettle || busy}
              onClick={handleTestCancelGuardrail}
              className="w-full py-2 px-2.5 rounded-lg border border-dashed border-[#CBD5E1] text-[11px] font-medium text-[#64748B] hover:text-[#DC2626] hover:border-[#FCA5A5] transition cursor-pointer disabled:opacity-50"
            >
              Test Invalid Commit -&gt; Verify CancelPayment Guardrail
            </button>
          </div>
        </section>
      </main>

      {/* PERSISTENT TEAM CREDITS FOOTER */}
      <footer className="bg-white border-t border-[#E2E8F0] px-4 lg:px-6 py-3.5 pb-20 lg:pb-3.5 mt-auto">
        <div className="max-w-[1440px] mx-auto flex flex-wrap items-center justify-between gap-2 text-xs text-[#475569]">
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4 text-[#1D4ED8] shrink-0" />
            <span>
              Built with dedication &amp; engineering effort by{' '}
              <strong className="font-bold text-[#1D4ED8]">
                Atul Anand, Jeeya &amp; Vanshika
              </strong>
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-[#64748B]">
            <Users className="w-3.5 h-3.5" />
            <span>
              Fetch-A-Thon 3.0 • Powered by Fetch.ai uAgents, Agentverse, ASI:One &amp; Dorado
              Ledger
            </span>
          </div>
        </div>
      </footer>

      {/* STICKY MOBILE BOTTOM TAB BAR (<1024px) */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-[#CBD5E1] grid grid-cols-3 p-1.5 shadow-lg">
        <button
          type="button"
          onClick={() => setMobileTab('chat')}
          className={`py-1.5 rounded-lg text-xs font-bold flex flex-col items-center cursor-pointer ${
            mobileTab === 'chat' ? 'bg-[#EFF6FF] text-[#1D4ED8]' : 'text-[#64748B]'
          }`}
        >
          <span>Chat &amp; Cards</span>
          <span className="text-[10px]">{chatHistory.length} msgs</span>
        </button>
        <button
          type="button"
          onClick={() => setMobileTab('sandbox')}
          className={`py-1.5 rounded-lg text-xs font-bold flex flex-col items-center cursor-pointer ${
            mobileTab === 'sandbox' ? 'bg-[#EFF6FF] text-[#1D4ED8]' : 'text-[#64748B]'
          }`}
        >
          <span>Solvers &amp; Diff</span>
          <span className="text-[10px]">{rankedPatches.length} verified</span>
        </button>
        <button
          type="button"
          onClick={() => setMobileTab('ledger')}
          className={`py-1.5 rounded-lg text-xs font-bold flex flex-col items-center cursor-pointer ${
            mobileTab === 'ledger' ? 'bg-[#EFF6FF] text-[#1D4ED8]' : 'text-[#64748B]'
          }`}
        >
          <span>Dorado Bounty</span>
          <span className="text-[10px] uppercase">{paymentState.stage}</span>
        </button>
      </nav>

      {/* MODAL 1: API & MAILBOX CONFIGURATION */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 bg-[#0B1221]/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-[#E2E8F0] max-w-md w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#0B1221]">
                ASI:One &amp; Agentverse Runtime Configuration
              </h3>
              <button
                type="button"
                onClick={() => setShowConfigModal(false)}
                className="p-1 text-[#64748B] hover:text-[#0B1221] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-[#475569] leading-relaxed">
              PatchBounty runs 100% free out-of-the-box using real isolated Python sandboxed{' '}
              <code className="bg-[#F1F5F9] px-1 rounded">pytest</code> verification. Redeem promo
              code <strong>FETCHATHONIND</strong> on <strong>asi1.ai</strong> to optionally connect
              your live key below:
            </p>
            <form onSubmit={handleSaveConfig} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold mb-1">ASI_ONE_API_KEY</label>
                <input
                  type="password"
                  value={asiKeyInput}
                  onChange={(e) => setAsiKeyInput(e.target.value)}
                  placeholder={config?.asi_one_key_preview || 'Paste ASI:One API key...'}
                  className="w-full rounded-lg border border-[#CBD5E1] px-3 py-2"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">ASI:One Model</label>
                <select
                  value={asiModelInput}
                  onChange={(e) => setAsiModelInput(e.target.value)}
                  className="w-full rounded-lg border border-[#CBD5E1] px-3 py-2 bg-white"
                >
                  <option value="asi1-mini">asi1-mini (Fastest Solver Reasoning)</option>
                  <option value="asi1">asi1 (Full Flagship Reasoning)</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold mb-1">AGENTVERSE_API_KEY (Optional)</label>
                <input
                  type="password"
                  value={avKeyInput}
                  onChange={(e) => setAvKeyInput(e.target.value)}
                  placeholder={config?.agentverse_key_preview || 'Paste Agentverse key...'}
                  className="w-full rounded-lg border border-[#CBD5E1] px-3 py-2"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 rounded-lg bg-[#1D4ED8] hover:bg-[#1E40AF] text-white font-semibold cursor-pointer"
              >
                Save to .env &amp; Apply Live
              </button>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: 6 ACTIVE UAGENTS ROSTER */}
      {showAgentsModal && (
        <div className="fixed inset-0 z-50 bg-[#0B1221]/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-[#E2E8F0] max-w-2xl w-full max-h-[85vh] overflow-y-auto p-5 space-y-3 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#0B1221]">
                Registered Fetch.ai uAgents Roster (6 Active Agents)
              </h3>
              <button
                type="button"
                onClick={() => setShowAgentsModal(false)}
                className="p-1 text-[#64748B] hover:text-[#0B1221] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2.5">
              {agents.map((ag) => (
                <div
                  key={ag.name}
                  className="rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-3 text-xs space-y-1"
                >
                  <div className="flex flex-wrap items-center justify-between gap-1">
                    <span className="font-bold text-[#0B1221]">{ag.name}</span>
                    <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded bg-[#EFF6FF] text-[#1D4ED8]">
                      {ag.role}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#475569]">{ag.protocols}</div>
                  <div className="font-mono text-[10.5px] text-[#334155] break-all">
                    uAgent: {ag.agent_address}
                  </div>
                  <div className="font-mono text-[10.5px] text-[#059669] break-all">
                    Dorado Wallet: {ag.wallet_address}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
