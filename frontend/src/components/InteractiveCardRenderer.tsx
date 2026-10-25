import React, { useState } from 'react';
import { ChevronRight, Code2, ShieldCheck } from 'lucide-react';

interface Props {
  cardKind?: 'form' | 'carousel' | 'detail' | 'review' | null;
  cardPayload?: any;
  rawAcpWire?: any;
  onCardAction: (serializedAction: string) => void;
  disabled?: boolean;
}

export const InteractiveCardRenderer: React.FC<Props> = ({
  cardKind,
  cardPayload,
  rawAcpWire,
  onCardAction,
  disabled,
}) => {
  const [showRawJson, setShowRawJson] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, string>>({
    target_repo: 'payment-ledger-rounding',
    verification_policy: '100% pytest pass + Clean AST Security Audit',
    bounty_fet: '0.05',
  });
  const defaultMerge =
    cardPayload?.sub_options?.choices?.[0]?.value || 'Squash & Merge (main)';
  const [mergeMode, setMergeMode] = useState<string>(defaultMerge);

  if (!cardKind || !cardPayload) return null;

  return (
    <div className="mt-2.5 rounded-lg border border-[#CBD5E1] bg-[#F8FAFC] overflow-hidden shadow-2xs">
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#EFF6FF] border-b border-[#DBEAFE]">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-[#1D4ED8]" />
          <span className="text-[11px] font-semibold tracking-wide uppercase text-[#1E40AF]">
            ASI:One Interactive Card • {cardKind}
          </span>
        </div>
        <button
          type="button"
          onClick={() => setShowRawJson((v) => !v)}
          className="inline-flex items-center gap-1 text-[11px] font-medium text-[#1D4ED8] hover:text-[#1E3A8A] cursor-pointer"
        >
          <Code2 className="w-3 h-3" />
          {showRawJson ? 'Hide ACP Wire JSON' : 'Raw ACP JSON'}
        </button>
      </div>

      {showRawJson && (
        <pre className="p-2.5 bg-[#0F172A] text-[#E2E8F0] text-[10.5px] leading-relaxed overflow-x-auto max-h-48 border-b border-[#334155]">
          {JSON.stringify(rawAcpWire, null, 2)}
        </pre>
      )}

      {/* 1. FORM CARD */}
      {cardKind === 'form' && (
        <div className="p-3.5 space-y-3 bg-white">
          <div>
            <h4 className="text-sm font-bold text-[#0B1221]">{cardPayload.title}</h4>
            <p className="text-xs text-[#475569] mt-0.5">{cardPayload.subtitle}</p>
          </div>
          {(cardPayload.fields || []).map((f: any) => (
            <div key={f.name} className="space-y-1">
              <label className="block text-xs font-semibold text-[#1E293B]">{f.label}</label>
              {f.type === 'select' ? (
                <select
                  value={formValues[f.name] || f.options?.[0]?.value || ''}
                  onChange={(e) => setFormValues({ ...formValues, [f.name]: e.target.value })}
                  className="w-full rounded-md border border-[#CBD5E1] bg-[#F8FAFC] px-2.5 py-1.5 text-xs text-[#0B1221] focus:border-[#1D4ED8] focus:outline-none"
                >
                  {(f.options || []).map((opt: any) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={f.type === 'number' ? 'number' : 'text'}
                  value={formValues[f.name] ?? f.default ?? ''}
                  onChange={(e) => setFormValues({ ...formValues, [f.name]: e.target.value })}
                  className="w-full rounded-md border border-[#CBD5E1] bg-[#F8FAFC] px-2.5 py-1.5 text-xs text-[#0B1221] focus:border-[#1D4ED8] focus:outline-none"
                />
              )}
            </div>
          ))}
          <button
            type="button"
            disabled={disabled}
            onClick={() =>
              onCardAction(
                JSON.stringify({
                  action: 'submit_intake',
                  ...formValues,
                })
              )
            }
            className="w-full py-2 px-3 rounded-lg bg-[#1D4ED8] hover:bg-[#1E40AF] text-white text-xs font-semibold transition cursor-pointer disabled:opacity-50"
          >
            {cardPayload.submit_label || 'Launch Swarm'}
          </button>
        </div>
      )}

      {/* 2. CAROUSEL CARD */}
      {cardKind === 'carousel' && (
        <div className="p-3 space-y-2.5 bg-white">
          <div>
            <h4 className="text-xs font-bold text-[#0B1221]">{cardPayload.title}</h4>
            <p className="text-[11px] text-[#64748B]">{cardPayload.subtitle}</p>
          </div>
          <div className="space-y-2">
            {(cardPayload.items || []).map((item: any, idx: number) => (
              <div
                key={item.id}
                className={`rounded-lg border p-2.5 transition ${
                  idx === 0
                    ? 'border-[#60A5FA] bg-[#F8FAFC]'
                    : 'border-[#E2E8F0] bg-white'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-1.5">
                  <span className="text-xs font-bold text-[#0B1221]">{item.title}</span>
                  <div className="flex flex-wrap items-center gap-1">
                    <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded-full bg-[#ECFDF5] text-[#047857] border border-[#A7F3D0]">
                      {item.badge_pass}
                    </span>
                    <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded-full bg-[#EFF6FF] text-[#1D4ED8] border border-[#BFDBFE]">
                      {item.badge_rank}
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-[#475569] mt-1">{item.diff_stats}</p>
                <p className="text-[11px] text-[#334155] mt-1 line-clamp-2">{item.rationale}</p>
                <div className="mt-2.5 flex items-center justify-between gap-2">
                  <span className="text-[10.5px] font-mono text-[#64748B]">
                    {item.solver_agent}
                  </span>
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => onCardAction(JSON.stringify(item.action_payload))}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md bg-[#1D4ED8] hover:bg-[#1E40AF] text-white text-[11px] font-semibold transition cursor-pointer disabled:opacity-50"
                  >
                    <span>Inspect Unified Diff</span>
                    <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. DETAIL CARD */}
      {cardKind === 'detail' && (
        <div className="p-3.5 space-y-3 bg-white">
          <div>
            <h4 className="text-xs font-bold text-[#0B1221]">{cardPayload.title}</h4>
            <p className="text-[11px] text-[#64748B]">{cardPayload.subtitle}</p>
          </div>

          <div className="rounded-md border border-[#E2E8F0] divide-y divide-[#F1F5F9] text-xs">
            {(cardPayload.rows || []).map((r: any, idx: number) => (
              <div key={idx} className="flex justify-between px-2.5 py-1.5 gap-2">
                <span className="text-[#64748B]">{r.label}</span>
                <span className="font-semibold text-[#0B1221] text-right">{r.value}</span>
              </div>
            ))}
          </div>

          {cardPayload.unified_diff && (
            <div className="rounded-md bg-[#0B1221] p-2.5 overflow-x-auto max-h-40 border border-[#1E293B]">
              <pre className="text-[10.5px] font-mono leading-relaxed">
                {String(cardPayload.unified_diff)
                  .split('\n')
                  .map((line: string, i: number) => {
                    const color = line.startsWith('+')
                      ? 'text-[#4ADE80]'
                      : line.startsWith('-')
                      ? 'text-[#F87171]'
                      : line.startsWith('@@')
                      ? 'text-[#60A5FA]'
                      : 'text-[#CBD5E1]';
                    return (
                      <div key={i} className={color}>
                        {line}
                      </div>
                    );
                  })}
              </pre>
            </div>
          )}

          {cardPayload.sub_options && (
            <div className="space-y-1.5">
              <div className="text-xs font-semibold text-[#1E293B]">
                {cardPayload.sub_options.label}
              </div>
              {(cardPayload.sub_options.choices || []).map((c: any) => (
                <label
                  key={c.value}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-[#E2E8F0] hover:bg-[#F8FAFC] text-xs cursor-pointer"
                >
                  <input
                    type="radio"
                    name={`merge_${cardPayload.patch_id}`}
                    value={c.value}
                    checked={mergeMode === c.value}
                    onChange={() => setMergeMode(c.value)}
                  />
                  <span>{c.label}</span>
                </label>
              ))}
            </div>
          )}

          <button
            type="button"
            disabled={disabled}
            onClick={() =>
              onCardAction(
                JSON.stringify({
                  action: 'confirm_merge_mode',
                  patch_id: cardPayload.patch_id,
                  merge_mode: mergeMode,
                })
              )
            }
            className="w-full py-2 px-3 rounded-lg bg-[#1D4ED8] hover:bg-[#1E40AF] text-white text-xs font-semibold transition cursor-pointer disabled:opacity-50"
          >
            Proceed to Bounty Payout Review
          </button>
        </div>
      )}

      {/* 4. REVIEW CARD */}
      {cardKind === 'review' && (
        <div className="p-3.5 space-y-3 bg-white">
          <div>
            <h4 className="text-xs font-bold text-[#0B1221]">{cardPayload.title}</h4>
            <p className="text-[11px] text-[#64748B]">{cardPayload.subtitle}</p>
          </div>
          <div className="rounded-md border border-[#E2E8F0] divide-y divide-[#F1F5F9] text-xs">
            {(cardPayload.summary_rows || []).map((r: any, idx: number) => (
              <div key={idx} className="flex justify-between px-2.5 py-1.5 gap-2">
                <span className="text-[#64748B]">{r.label}</span>
                <span className="font-semibold text-[#0B1221] text-right">{r.value}</span>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={disabled}
              onClick={() =>
                onCardAction(
                  JSON.stringify({
                    action: 'approve_bounty',
                    patch_id: cardPayload.patch_id,
                    merge_mode: cardPayload.merge_mode,
                  })
                )
              }
              className="flex-1 py-2 px-3 rounded-lg bg-[#059669] hover:bg-[#047857] text-white text-xs font-semibold transition cursor-pointer disabled:opacity-50"
            >
              {cardPayload.approve_label || 'Approve & Pay Bounty'}
            </button>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onCardAction(JSON.stringify({ action: 'cancel_bounty' }))}
              className="py-2 px-3 rounded-lg border border-[#CBD5E1] bg-white hover:bg-[#F8FAFC] text-[#334155] text-xs font-semibold transition cursor-pointer"
            >
              {cardPayload.cancel_label || 'Cancel'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
