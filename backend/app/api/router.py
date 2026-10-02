from typing import List
from fastapi import APIRouter, HTTPException, Query
from app.core.config import settings
from app.db.store import Storage, init_db
from app.domain.models import (
    AuditEvent,
    IntentParseRequest,
    OrderRecord,
    ParsedIntent,
    PortfolioSummary,
    TradeConfirmRequest,
    TradeProposal,
    TradeProposalCreateRequest,
)
from app.services.intent_service import IntentService
from app.services.order_service import OrderService
from app.services.portfolio_service import PortfolioService
from app.services.proposal_service import ProposalService

api_router = APIRouter(prefix="/api")


@api_router.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "true_markets_mode": settings.TM_ENV,
        "supported_assets": settings.SUPPORTED_ASSETS,
    }


@api_router.post("/intent/parse", response_model=ParsedIntent)
def parse_intent(request: IntentParseRequest):
    return IntentService.parse_natural_language(request.prompt)


@api_router.post("/trades/proposals", response_model=TradeProposal)
def create_proposal(request: TradeProposalCreateRequest):
    return ProposalService.create_proposal(request, user_id="demo-user-1")


@api_router.get("/trades/proposals/{proposal_id}", response_model=TradeProposal)
def get_proposal(proposal_id: str):
    proposal = Storage.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@api_router.post("/trades/{proposal_id}/confirm", response_model=OrderRecord)
async def confirm_trade(proposal_id: str):
    return await OrderService.confirm_proposal(proposal_id=proposal_id, user_id="demo-user-1")


@api_router.post("/trades/{proposal_id}/cancel")
def cancel_trade(proposal_id: str):
    proposal = Storage.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    Storage.update_proposal_status(proposal_id, "CANCELLED")
    return {"status": "CANCELLED", "proposal_id": proposal_id}


@api_router.get("/orders/{order_id}", response_model=OrderRecord)
def get_order(order_id: str):
    order = Storage.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@api_router.get("/portfolio", response_model=PortfolioSummary)
def get_portfolio():
    return PortfolioService.get_summary(user_id="demo-user-1")


@api_router.get("/activity", response_model=List[AuditEvent])
def get_activity(limit: int = Query(50, ge=1, le=100)):
    return Storage.get_audit_events(user_id="demo-user-1", limit=limit)


@api_router.post("/system/reset-demo")
def reset_demo():
    """Resets the demo portfolio and activity to default state for judges."""
    from app.db.store import get_db, init_db, seed_demo_account
    init_db()
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM orders;")
        conn.execute("DELETE FROM trade_proposals;")
        conn.execute("DELETE FROM audit_events;")
        conn.execute("DELETE FROM positions;")
        conn.execute("DELETE FROM portfolios;")
        conn.execute("DELETE FROM users;")
    seed_demo_account(conn)
    conn.close()
    return {"message": "Demo environment reset to initial seed values."}
