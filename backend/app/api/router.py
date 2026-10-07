import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from app.core.config import settings
from app.db.store import Storage
from app.domain.models import (
    AuditEvent,
    IntentParseRequest,
    IntentParseResponse,
    MarketCandlesResponse,
    OHLCBucket,
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
from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError

logger = logging.getLogger("TradeGuard.Router")
api_router = APIRouter(prefix="/api")

_CANDLE_CACHE: Dict[str, Tuple[float, MarketCandlesResponse]] = {}
_CANDLE_CACHE_TTL = 6.0


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


@api_router.get("/market/candles", response_model=MarketCandlesResponse)
async def get_market_candles(
    asset: str = Query(..., description="Asset symbol (BTC, ETH, SOL, USDC)"),
    window: str = Query("1d", description="Lookback window: 1h, 4h, 1d, 7d"),
    resolution: Optional[str] = Query(None, description="Resolution interval: 1m, 5m, 15m, 1h"),
):
    """
    Retrieves real OHLC candles directly from True Markets public market data API.
    Does not invent or simulate fake candles.
    Gracefully returns unavailable status if the upstream service is offline.
    """
    clean_asset = asset.strip().upper()
    if clean_asset not in settings.SUPPORTED_ASSETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset '{clean_asset}' is not supported. Supported: {settings.SUPPORTED_ASSETS}",
        )

    valid_windows = {"1h", "4h", "1d", "7d"}
    clean_window = window.strip().lower()
    if clean_window not in valid_windows:
        clean_window = "1d"

    res_map = {
        "1h": "1m",
        "4h": "5m",
        "1d": "15m",
        "7d": "1h",
    }
    clean_res = (resolution.strip().lower() if resolution else None) or res_map.get(clean_window, "15m")

    cache_key = f"{clean_asset}:{clean_window}:{clean_res}"
    now_ts = datetime.now(timezone.utc).timestamp()
    if cache_key in _CANDLE_CACHE:
        cached_time, cached_resp = _CANDLE_CACHE[cache_key]
        if (now_ts - cached_time) < _CANDLE_CACHE_TTL:
            return cached_resp

    tm_client = TrueMarketsClient()
    try:
        raw_data = await tm_client.get_candles(
            symbol=clean_asset,
            window=clean_window,
            resolution=clean_res,
        )
        raw_candles = raw_data.get("candles", [])
        if not raw_candles:
            resp = MarketCandlesResponse(
                asset=clean_asset,
                window=clean_window,
                resolution=clean_res,
                candles=[],
                is_available=False,
                status_label="Market data unavailable",
                error=f"No candle data returned for {clean_asset}.",
            )
            return resp

        buckets: List[OHLCBucket] = []
        for c in raw_candles:
            try:
                iso_t = c["t"]
                dt = datetime.fromisoformat(iso_t.replace("Z", "+00:00"))
                unix_t = int(dt.timestamp())
                buckets.append(OHLCBucket(
                    time=unix_t,
                    iso_time=iso_t,
                    open=float(c["open"]),
                    high=float(c["high"]),
                    low=float(c["low"]),
                    close=float(c["close"]),
                ))
            except Exception as pe:
                logger.debug("Skipping unparseable candle: %s", pe)

        if not buckets:
            return MarketCandlesResponse(
                asset=clean_asset,
                window=clean_window,
                resolution=clean_res,
                candles=[],
                is_available=False,
                status_label="Market data unavailable",
                error="Could not parse candle series.",
            )

        current_price = buckets[-1].close
        first_open = buckets[0].open
        price_change = round(current_price - first_open, 4)
        price_change_pct = round(((current_price - first_open) / first_open) * 100, 2) if first_open > 0 else 0.0
        high = max(b.high for b in buckets)
        low = min(b.low for b in buckets)
        latest_iso = buckets[-1].iso_time

        latest_dt = datetime.fromisoformat(latest_iso.replace("Z", "+00:00"))
        freshness_secs = max(0, int((datetime.now(timezone.utc) - latest_dt).total_seconds()))

        status_label = "Live market data" if freshness_secs <= 120 else f"Market data updated {freshness_secs}s ago"

        resp = MarketCandlesResponse(
            asset=clean_asset,
            window=clean_window,
            resolution=clean_res,
            current_price=current_price,
            price_change=price_change,
            price_change_pct=price_change_pct,
            high=high,
            low=low,
            latest_timestamp=latest_iso,
            candles=buckets,
            freshness_seconds=freshness_secs,
            is_available=True,
            status_label=status_label,
            error=None,
        )
        _CANDLE_CACHE[cache_key] = (now_ts, resp)
        if current_price and current_price > 0:
            try:
                from app.services.quote_service import DEMO_PRICES
                DEMO_PRICES[clean_asset] = round(float(current_price), 2)
            except Exception:
                pass
        return resp

    except TrueMarketsClientError as tce:
        logger.warning("Candle retrieval failed for %s: %s", clean_asset, tce)
        return MarketCandlesResponse(
            asset=clean_asset,
            window=clean_window,
            resolution=clean_res,
            candles=[],
            is_available=False,
            status_label="Market data temporarily unavailable",
            error=str(tce),
        )
    except Exception as exc:
        logger.error("Unexpected candle retrieval error: %s", exc)
        return MarketCandlesResponse(
            asset=clean_asset,
            window=clean_window,
            resolution=clean_res,
            candles=[],
            is_available=False,
            status_label="Market data temporarily unavailable",
            error="Upstream market data query failed.",
        )


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
