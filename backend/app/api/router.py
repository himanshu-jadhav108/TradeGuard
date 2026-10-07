import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from app.core.config import settings
from app.db.store import Storage
from app.domain.models import (
    AuditEvent,
    IntentParseRequest,
    IntentParseResponse,
    OrderRecord,
    PortfolioSummary,
    SafetySignalsReport,
    SessionResetResponse,
    TradeConfirmRequest,
    TradeProposal,
    TradeProposalCreateRequest,
)
from app.services.intent_service import IntentService
from app.services.order_service import OrderService
from app.services.portfolio_service import PortfolioService
from app.services.proposal_service import ProposalService
from app.services.safety_signal_service import SafetySignalService
from app.services.true_markets_client import TrueMarketsClient

api_router = APIRouter(prefix="/api")


def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """
    Extracts and validates visitor session ID for per-session demo isolation.
    Rejects missing or invalid X-Session-ID with HTTP 400 Bad Request.
    """
    if not x_session_id or not x_session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required X-Session-ID header. A valid session ID is required for demo isolation.",
        )
    clean = x_session_id.strip()
    if not re.match(r"^[a-zA-Z0-9_-]{4,64}$", clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Session-ID header. Must be 4-64 characters matching [a-zA-Z0-9_-].",
        )
    return clean


@api_router.get("/health")
def health_check():
    tm_client = TrueMarketsClient()
    uat_configured = tm_client.is_configured()
    active_mode = "uat" if (settings.TM_ENV == "uat" and uat_configured) else "demo"
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "mode": active_mode,
        "true_markets_mode": settings.TM_ENV,
        "true_markets_configured": uat_configured,
        "true_markets_available": (settings.TM_ENV == "uat" and uat_configured),
        "supported_assets": settings.SUPPORTED_ASSETS,
        "max_notional_usd": settings.MAX_NOTIONAL_USD,
        "concentration_threshold_pct": settings.CONCENTRATION_THRESHOLD_PCT,
    }


@api_router.post("/intent/parse", response_model=IntentParseResponse)
def parse_intent(
    request: IntentParseRequest,
    session_id: str = Depends(get_session_id),
):
    result = IntentService.parse_with_clarification(request.prompt)
    now = datetime.now(timezone.utc).isoformat()
    if result.success and result.intent:
        Storage.save_audit_event(AuditEvent(
            id=f"evt-{uuid.uuid4().hex[:12]}",
            user_id=session_id,
            event_type="INTENT_PARSED",
            summary=f"Parsed intent: {result.intent.side.value} {result.intent.amount} {result.intent.asset} ({result.intent.amount_type.value}).",
            metadata={
                "prompt": request.prompt,
                "asset": result.intent.asset,
                "side": result.intent.side.value,
                "amount": result.intent.amount,
                "amount_type": result.intent.amount_type.value,
            },
            timestamp=now,
            is_recorded=True,
        ))
    else:
        Storage.save_audit_event(AuditEvent(
            id=f"evt-{uuid.uuid4().hex[:12]}",
            user_id=session_id,
            event_type="INTENT_REJECTED",
            summary=f"Intent rejected or requires clarification: {result.error or result.clarification or 'Unrecognized intent'}.",
            metadata={
                "prompt": request.prompt,
                "error": result.error,
                "clarification": result.clarification,
            },
            timestamp=now,
            is_recorded=True,
        ))
    return IntentParseResponse(
        success=result.success,
        intent=result.intent,
        clarification=result.clarification,
        suggestions=result.suggestions,
        error=result.error,
    )



@api_router.post("/trades/proposals", response_model=TradeProposal)
async def create_proposal(
    request: TradeProposalCreateRequest,
    session_id: str = Depends(get_session_id),
):
    return await ProposalService.create_proposal(request, user_id=session_id)


@api_router.get("/trades/proposals/{proposal_id}", response_model=TradeProposal)
def get_proposal(
    proposal_id: str,
    session_id: str = Depends(get_session_id),
):
    proposal = Storage.get_proposal(proposal_id, user_id=session_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@api_router.post("/trades/{proposal_id}/confirm", response_model=OrderRecord)
async def confirm_trade(
    proposal_id: str,
    confirm_req: Optional[TradeConfirmRequest] = None,
    session_id: str = Depends(get_session_id),
):
    req = confirm_req or TradeConfirmRequest(proposal_id=proposal_id)
    return await OrderService.confirm_proposal(proposal_id=proposal_id, confirm_req=req, user_id=session_id)


@api_router.post("/trades/{proposal_id}/cancel")
def cancel_trade(
    proposal_id: str,
    session_id: str = Depends(get_session_id),
):
    proposal = Storage.get_proposal(proposal_id, user_id=session_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != "PENDING_CONFIRMATION":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel trade in status '{proposal.status}'. Cancellation is only allowed when PENDING_CONFIRMATION.",
        )
    cancelled = Storage.cancel_proposal(proposal_id, user_id=session_id)
    if not cancelled:
        p_check = Storage.get_proposal(proposal_id, user_id=session_id)
        curr = p_check.status if p_check else "UNKNOWN"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel trade in status '{curr}'. Cancellation is only allowed when PENDING_CONFIRMATION.",
        )
    return {"status": "CANCELLED", "proposal_id": proposal_id}


@api_router.get("/orders/{order_id}", response_model=OrderRecord)
def get_order(
    order_id: str,
    session_id: str = Depends(get_session_id),
):
    order = Storage.get_order(order_id, user_id=session_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@api_router.get("/portfolio", response_model=PortfolioSummary)
def get_portfolio(session_id: str = Depends(get_session_id)):
    return PortfolioService.get_summary(user_id=session_id)


@api_router.get("/activity", response_model=List[AuditEvent])
def get_activity(
    limit: int = Query(50, ge=1, le=100),
    session_id: str = Depends(get_session_id),
):
    return Storage.get_audit_events(user_id=session_id, limit=limit)


@api_router.get("/safety-signals", response_model=SafetySignalsReport)
def get_safety_signals(session_id: str = Depends(get_session_id)):
    """
    Computes rule-based safety signals strictly and deterministically from stored session audit events.
    """
    events = Storage.get_audit_events(user_id=session_id, limit=200)
    return SafetySignalService.compute_signals(session_id=session_id, events=events)



@api_router.post("/session/reset", response_model=SessionResetResponse)
@api_router.post("/system/reset-demo", response_model=SessionResetResponse)
def reset_session_demo(session_id: str = Depends(get_session_id)):
    """
    Scoped, non-destructive to other users: Resets only the calling visitor session.
    """
    Storage.reset_session(session_id)
    return SessionResetResponse(
        status="ok",
        session_id=session_id,
        message=f"Session demo account '{session_id}' successfully reset to default state ($10,000 cash, 0.15 BTC, 1.5 ETH, 10 SOL).",
    )


# Explicitly disallow destructive GET resets with informative HTTP 405 Method Not Allowed
@api_router.get("/session/reset", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
@api_router.get("/system/reset-demo", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
def disallow_get_reset():
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="GET reset operations are disabled for security. Use POST /api/session/reset with X-Session-ID.",
    )
