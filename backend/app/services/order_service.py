import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException
from app.core.config import settings
from app.db.store import Storage
from app.domain.models import (
    AuditEvent,
    OrderRecord,
    OrderSide,
    OrderStatus,
    RiskLevel,
    TradeConfirmRequest,
)
from app.services.quote_service import QuoteService
from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError


class OrderService:
    @classmethod
    async def confirm_proposal(
        cls, proposal_id: str, confirm_req: TradeConfirmRequest, user_id: str = "demo-user-1"
    ) -> OrderRecord:
        # 1. Fetch proposal to inspect pre-conditions
        proposal = Storage.get_proposal(proposal_id, user_id=user_id)
        if not proposal:
            raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found.")

        # 2. Strict Risk Gate Verification
        if proposal.risk.overall_status == RiskLevel.BLOCK:
            raise HTTPException(
                status_code=400,
                detail=f"Execution blocked by deterministic risk engine: {proposal.risk.block_reason or 'Blocked trades cannot be executed.'}",
            )

        # 3. WARN Acknowledgement Verification
        if proposal.risk.overall_status == RiskLevel.WARN and proposal.risk.warn_requires_ack:
            if not confirm_req.acknowledged_warnings:
                raise HTTPException(
                    status_code=400,
                    detail="Confirmation requires explicit acknowledgement of the portfolio concentration warning.",
                )

        # 4. Verify Quote Freshness (30s TTL)
        if not QuoteService.is_quote_fresh(proposal.quote):
            Storage.update_proposal_status(proposal_id, "EXPIRED", user_id=user_id)
            raise HTTPException(
                status_code=409,
                detail="Market quote expired before confirmation was received. Please refresh the quote.",
            )

        # 5. Atomic Claim to prevent concurrent double confirmation
        claimed = Storage.claim_proposal_for_confirmation(proposal_id, user_id=user_id)
        if not claimed:
            # Re-fetch proposal to provide exact status
            p_check = Storage.get_proposal(proposal_id, user_id=user_id)
            status_desc = p_check.status if p_check else "PROCESSED"
            raise HTTPException(
                status_code=409,
                detail=f"Proposal has already been processed or is currently executing (status: {status_desc}). Double confirmation is prevented.",
            )

        try:
            # 6. Re-verify user balance at moment of execution
            portfolio_data = Storage.get_portfolio(user_id)
            d_cash = Decimal(str(portfolio_data["cash_usd"]))
            positions = {k: Decimal(str(v)) for k, v in portfolio_data["positions"].items()}
            d_notional = Decimal(str(proposal.estimated_notional_usd))
            d_qty = Decimal(str(proposal.estimated_qty))

            if proposal.side == OrderSide.BUY and d_notional > d_cash:
                Storage.update_proposal_status(proposal_id, "PENDING_CONFIRMATION", user_id=user_id)
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient cash balance at confirmation. Needed: ${float(d_notional):,.2f}, Available: ${float(d_cash):,.2f}",
                )
            elif proposal.side == OrderSide.SELL and d_qty > positions.get(proposal.asset, Decimal("0")):
                Storage.update_proposal_status(proposal_id, "PENDING_CONFIRMATION", user_id=user_id)
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient {proposal.asset} balance at confirmation. Needed: {float(d_qty):,.6f}, Owned: {float(positions.get(proposal.asset, Decimal('0'))):,.6f}",
                )

            now = datetime.now(timezone.utc).isoformat()
            order_id = f"ord-{uuid.uuid4().hex[:12]}"

            # 7. Route Execution based on Environment
            tm_client = TrueMarketsClient()
            is_real_uat = settings.TM_ENV == "uat" and tm_client.is_configured()

            if not is_real_uat:
                # DETERMINISTIC DEMO SIMULATION
                external_order_id = f"demo-sim-{uuid.uuid4().hex[:8]}"
                fill_price = proposal.quote.ask if proposal.side == OrderSide.BUY else proposal.quote.bid

                # Update portfolio balances using Decimal arithmetic
                if proposal.side == OrderSide.BUY:
                    new_cash = (d_cash - d_notional).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    positions[proposal.asset] = (positions.get(proposal.asset, Decimal("0")) + d_qty).quantize(
                        Decimal("0.000001"), rounding=ROUND_HALF_UP
                    )
                else:
                    new_cash = (d_cash + d_notional).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    positions[proposal.asset] = max(
                        Decimal("0"), positions.get(proposal.asset, Decimal("0")) - d_qty
                    ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

                # Persist state
                float_positions = {k: float(v) for k, v in positions.items()}
                Storage.update_portfolio(user_id, float(new_cash), float_positions)
                Storage.update_proposal_status(proposal_id, "CONFIRMED", user_id=user_id)

                order = OrderRecord(
                    id=order_id,
                    proposal_id=proposal.id,
                    user_id=user_id,
                    asset=proposal.asset,
                    side=proposal.side,
                    quantity=proposal.estimated_qty,
                    notional_usd=proposal.estimated_notional_usd,
                    status=OrderStatus.FILLED,
                    external_order_id=external_order_id,
                    fill_price=fill_price,
                    created_at=now,
                    updated_at=now,
                    mode="DEMO",
                    audit_id=f"audit-{order_id}",
                    raw_prompt=proposal.raw_prompt,
                )
                Storage.save_order(order)

                # Structured Audit Trail
                Storage.save_audit_event(AuditEvent(
                    id=f"evt-{uuid.uuid4().hex[:12]}",
                    user_id=user_id,
                    event_type="TRADE_CONFIRMED",
                    proposal_id=proposal_id,
                    order_id=order_id,
                    summary=f"User explicitly confirmed {proposal.side.value} {proposal.estimated_qty:,.6f} {proposal.asset} (Simulated Demo).",
                    metadata={"mode": "DEMO", "notional_usd": proposal.estimated_notional_usd},
                    timestamp=now,
                ))

                Storage.save_audit_event(AuditEvent(
                    id=f"evt-{uuid.uuid4().hex[:12]}",
                    user_id=user_id,
                    event_type="ORDER_FILLED",
                    proposal_id=proposal_id,
                    order_id=order_id,
                    summary=f"Simulated order filled at ${fill_price:,.2f} USDC (External ID: {external_order_id}).",
                    metadata={
                        "fill_price": fill_price,
                        "quantity": proposal.estimated_qty,
                        "cash_after": float(new_cash),
                        "mode": "DEMO",
                    },
                    timestamp=now,
                ))

                return order

            else:
                # REAL TRUE MARKETS UAT GATEWAY EXECUTION
                try:
                    gw_order = await tm_client.create_order(
                        pair=proposal.quote.pair,
                        side=proposal.side.value,
                        quantity=proposal.estimated_qty,
                        quote_id=proposal.quote.quote_id,
                        user_id=user_id,
                    )
                    ext_id = gw_order.get("id") or gw_order.get("order_id")

                    exec_res = await tm_client.execute_order(order_id=ext_id, user_id=user_id)
                    status_str = exec_res.get("status", "SUBMITTED").upper()

                    order_status = OrderStatus.FILLED if status_str in ("FILLED", "COMPLETED") else OrderStatus.SUBMITTED

                    # Never use quote mid as a fill price
                    gateway_fill_price = None
                    if order_status == OrderStatus.FILLED:
                        raw_fill = exec_res.get("fill_price") or exec_res.get("price") or gw_order.get("fill_price")
                        if raw_fill is not None:
                            try:
                                gateway_fill_price = float(raw_fill)
                            except (ValueError, TypeError):
                                gateway_fill_price = None

                    order = OrderRecord(
                        id=order_id,
                        proposal_id=proposal.id,
                        user_id=user_id,
                        asset=proposal.asset,
                        side=proposal.side,
                        quantity=proposal.estimated_qty,
                        notional_usd=proposal.estimated_notional_usd,
                        status=order_status,
                        external_order_id=ext_id,
                        fill_price=gateway_fill_price,
                        created_at=now,
                        updated_at=now,
                        mode="UAT",
                        audit_id=f"audit-{order_id}",
                        raw_prompt=proposal.raw_prompt,
                    )

                    Storage.update_proposal_status(proposal_id, "CONFIRMED", user_id=user_id)
                    Storage.save_order(order)

                    Storage.save_audit_event(AuditEvent(
                        id=f"evt-{uuid.uuid4().hex[:12]}",
                        user_id=user_id,
                        event_type="UAT_ORDER_SUBMITTED",
                        proposal_id=proposal_id,
                        order_id=order_id,
                        summary=f"Submitted to True Markets UAT Gateway: Order ID {ext_id}, Status: {status_str}.",
                        metadata={"external_id": ext_id, "status": status_str, "mode": "UAT"},
                        timestamp=now,
                    ))

                    return order

                except TrueMarketsClientError as e:
                    Storage.update_proposal_status(proposal_id, "PENDING_CONFIRMATION", user_id=user_id)
                    raise HTTPException(status_code=e.status_code or 500, detail=str(e))

        except Exception:
            # If unexpected error occurred during execution, release lock if safe
            Storage.update_proposal_status(proposal_id, "PENDING_CONFIRMATION", user_id=user_id)
            raise
