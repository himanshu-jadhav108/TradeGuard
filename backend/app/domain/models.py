from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class AmountType(str, Enum):
    USD = "USD"
    ASSET = "ASSET"


class RiskLevel(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"


class OrderStatus(str, Enum):
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMING = "CONFIRMING"
    SUBMITTED = "SUBMITTED"
    PENDING_EXECUTION = "PENDING_EXECUTION"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ParsedIntent(BaseModel):
    asset: str
    side: OrderSide
    amount: float = Field(gt=0, description="Amount must be positive")
    amount_type: AmountType
    raw_prompt: str
    interpreter_type: str = "RULE_BASED"


class IntentParseRequest(BaseModel):
    prompt: str


class IntentParseResponse(BaseModel):
    success: bool
    intent: Optional[ParsedIntent] = None
    clarification: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class QuoteSnapshot(BaseModel):
    pair: str
    base_asset: str
    quote_asset: str
    bid: float
    ask: float
    mid: float
    spread_pct: float
    timestamp: str
    expires_at: str
    source: str  # "DEMO_SIMULATOR" | "TRUE_MARKETS_UAT"
    quote_id: Optional[str] = None
    age_seconds: Optional[float] = None


class RiskCheckItem(BaseModel):
    name: str
    status: RiskLevel
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    suggested_action: Optional[str] = None


class RiskResult(BaseModel):
    overall_status: RiskLevel
    can_execute: bool
    checks: List[RiskCheckItem]
    warn_requires_ack: bool = False
    block_reason: Optional[str] = None
    suggested_safe_amount_usd: Optional[float] = None


class PortfolioImpact(BaseModel):
    asset: str
    current_qty: float
    current_value_usd: float
    current_allocation_pct: float
    projected_qty: float
    projected_value_usd: float
    projected_allocation_pct: float
    cash_before_usd: float
    cash_after_usd: float
    total_portfolio_value_before: float
    total_portfolio_value_after: float


class TradeProposalCreateRequest(BaseModel):
    prompt: Optional[str] = None
    asset: Optional[str] = None
    side: Optional[OrderSide] = None
    amount: Optional[float] = None
    amount_type: Optional[AmountType] = None


class TradeProposal(BaseModel):
    id: str
    user_id: str  # Scoped session_id
    asset: str
    side: OrderSide
    request_amount: float
    request_amount_type: AmountType
    estimated_qty: float
    estimated_notional_usd: float
    quote: QuoteSnapshot
    risk: RiskResult
    portfolio_impact: PortfolioImpact
    explanation: str
    raw_prompt: Optional[str] = None
    created_at: str
    expires_at: str
    status: str  # "PENDING_CONFIRMATION" | "CONFIRMING" | "CONFIRMED" | "CANCELLED" | "EXPIRED"
    requires_confirmation: bool = True
    fee_estimate_usd: Optional[float] = None
    fee_label: str = "Not modelled in demo"


class TradeConfirmRequest(BaseModel):
    proposal_id: str
    acknowledged_warnings: bool = False


class OrderRecord(BaseModel):
    id: str
    proposal_id: str
    user_id: str
    asset: str
    side: OrderSide
    quantity: float
    notional_usd: float
    status: OrderStatus
    external_order_id: Optional[str] = None
    fill_price: Optional[float] = None
    created_at: str
    updated_at: str
    mode: str  # "DEMO" | "UAT"
    audit_id: Optional[str] = None
    raw_prompt: Optional[str] = None


class AuditEvent(BaseModel):
    id: str
    user_id: str
    event_type: str
    proposal_id: Optional[str] = None
    order_id: Optional[str] = None
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str
    seq: Optional[int] = None
    is_recorded: bool = True


class SafetySignal(BaseModel):
    id: str
    name: str
    description: str
    count: int
    severity: str  # "INFO", "WARN", "CRITICAL"
    details: Dict[str, Any] = Field(default_factory=dict)


class SafetySignalsReport(BaseModel):
    session_id: str
    signals: List[SafetySignal]
    total_stored_events: int
    computed_at: str
    label: str = "rule-based safety signals"



class Position(BaseModel):
    asset: str
    quantity: float
    price_usd: float
    value_usd: float
    allocation_pct: float


class PortfolioSummary(BaseModel):
    user_id: str
    cash_usd: float
    total_value_usd: float
    positions: List[Position]
    mode: str
    as_of: str


class SessionResetResponse(BaseModel):
    status: str = "ok"
    session_id: str
    message: str
