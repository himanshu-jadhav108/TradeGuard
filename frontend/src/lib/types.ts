export type OrderSide = "BUY" | "SELL";
export type AmountType = "USD" | "ASSET";
export type RiskLevel = "PASS" | "WARN" | "BLOCK";
export type OrderStatus =
  | "PENDING_CONFIRMATION"
  | "CONFIRMING"
  | "SUBMITTED"
  | "PENDING_EXECUTION"
  | "FILLED"
  | "CANCELLED"
  | "REJECTED"
  | "FAILED";

export interface ParsedIntent {
  asset: string;
  side: OrderSide;
  amount: number;
  amount_type: AmountType;
  raw_prompt: string;
  interpreter_type?: string;
}

export interface IntentParseResponse {
  success: boolean;
  intent?: ParsedIntent;
  clarification?: string;
  suggestions: string[];
  error?: string;
}

export interface QuoteSnapshot {
  pair: string;
  base_asset: string;
  quote_asset: string;
  bid: number;
  ask: number;
  mid: number;
  spread_pct: number;
  timestamp: string;
  expires_at: string;
  source: string;
}

export interface RiskCheckItem {
  name: string;
  status: RiskLevel;
  message: string;
  details?: Record<string, any>;
  suggested_action?: string;
}

export interface RiskResult {
  overall_status: RiskLevel;
  can_execute: boolean;
  checks: RiskCheckItem[];
  warn_requires_ack?: boolean;
  block_reason?: string;
  suggested_safe_amount_usd?: number;
}

export interface PortfolioImpact {
  asset: string;
  current_qty: number;
  current_value_usd: number;
  current_allocation_pct: number;
  projected_qty: number;
  projected_value_usd: number;
  projected_allocation_pct: number;
  cash_before_usd: number;
  cash_after_usd: number;
  total_portfolio_value_before: number;
  total_portfolio_value_after: number;
}

export interface TradeProposal {
  id: string;
  user_id: string;
  asset: string;
  side: OrderSide;
  request_amount: number;
  request_amount_type: AmountType;
  estimated_qty: number;
  estimated_notional_usd: number;
  quote: QuoteSnapshot;
  risk: RiskResult;
  portfolio_impact: PortfolioImpact;
  explanation: string;
  raw_prompt?: string;
  created_at: string;
  expires_at: string;
  status: string;
  requires_confirmation: boolean;
  fee_label?: string;
}

export interface OrderRecord {
  id: string;
  proposal_id: string;
  user_id: string;
  asset: string;
  side: OrderSide;
  quantity: number;
  notional_usd: number;
  status: OrderStatus;
  external_order_id?: string;
  fill_price?: number;
  created_at: string;
  updated_at: string;
  mode: "DEMO" | "UAT";
  audit_id?: string;
  raw_prompt?: string;
}

export interface AuditEvent {
  id: string;
  user_id: string;
  event_type: string;
  proposal_id?: string;
  order_id?: string;
  summary: string;
  metadata: Record<string, any>;
  timestamp: string;
  seq?: number;
  is_recorded?: boolean;
}

export interface SafetySignal {
  id: string;
  name: string;
  description: string;
  count: number;
  severity: "INFO" | "WARN" | "CRITICAL";
  details?: Record<string, any>;
}

export interface SafetySignalsReport {
  session_id: string;
  signals: SafetySignal[];
  total_stored_events: number;
  computed_at: string;
  label: string;
}


export interface Position {
  asset: string;
  quantity: number;
  price_usd: number;
  value_usd: number;
  allocation_pct: number;
}

export interface PortfolioSummary {
  user_id: string;
  cash_usd: number;
  total_value_usd: number;
  positions: Position[];
  mode: string;
  as_of: string;
}

export interface SessionResetResponse {
  status: string;
  session_id: string;
  message: string;
}
