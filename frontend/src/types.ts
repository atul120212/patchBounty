export interface RuntimeConfig {
  asi_one_configured: boolean;
  asi_one_key_preview: string;
  asi_one_model: string;
  agentverse_configured: boolean;
  agentverse_key_preview: string;
  escrow_amount_fet: string;
  llm_engine_label: string;
}

export interface AgentInfo {
  name: string;
  role: string;
  protocols: string;
  agent_address: string;
  wallet_address: string;
  explorer_url: string;
}

export interface SolverWalletEntry {
  agent_key: string;
  agent_name: string;
  address: string;
  balance_fet: number;
  explorer_url: string;
}

export interface WalletsSnapshot {
  network: string;
  denom: string;
  coordinator_wallet: {
    label: string;
    address: string;
    balance_fet: number;
    explorer_url: string;
  };
  solver_wallets: Record<string, SolverWalletEntry>;
}

export interface ReproductionReport {
  scenario_id: string;
  repo_slug: string;
  issue_number: string;
  title: string;
  severity: string;
  bounty_fet: string;
  bounty_inr_equiv: number;
  reproduced: boolean;
  exit_code: number;
  passed: number;
  failed: number;
  total: number;
  duration_ms: number;
  output: string;
}

export interface CandidatePatch {
  id: string;
  lane: string;
  solver_agent_key: string;
  solver_agent_name: string;
  solver_wallet: string;
  name: string;
  strategy: string;
  rationale: string;
  module_filename: string;
  unified_diff: string;
  lines_added: number;
  lines_removed: number;
  ast_ok: boolean;
  ast_note: string;
  all_tests_passed: boolean;
  passed: number;
  failed: number;
  total: number;
  duration_ms: number;
  pytest_output: string;
  score: number;
  rank: number;
}

export interface ChatItem {
  id: string;
  timestamp: string;
  role: 'user' | 'agent';
  sender_label: string;
  text: string;
  card_kind?: 'form' | 'carousel' | 'detail' | 'review' | null;
  card_payload?: any;
  raw_acp_wire?: any;
}

export interface EnvelopeTrace {
  id: string;
  timestamp: string;
  protocol: string;
  sender: string;
  recipient: string;
  summary: string;
  wire: Record<string, any>;
}

export interface PaymentState {
  stage: 'idle' | 'requested' | 'broadcasting' | 'completed' | 'cancelled';
  reference?: string;
  winning_solver?: string;
  recipient_wallet?: string;
  request_model?: any;
  commit_model?: any;
  resolution_model?: any;
  verification?: {
    tx_hash: string;
    block_height: number;
    recipient: string;
    paid_fet: string;
    explorer_url: string;
  };
  error_reason?: string | null;
  bounty_receipt?: {
    reference: string;
    repo: string;
    solver: string;
    recipient_wallet: string;
    merge_mode: string;
    tx_hash: string;
    block_height: number;
    explorer_url: string;
    patch_download_url: string;
  };
}
