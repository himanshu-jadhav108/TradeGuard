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

        # 6. Route Execution based on Environment
        tm_client = TrueMarketsClient()
        is_real_uat = settings.TM_ENV == "uat" and tm_client.is_configured()

        if not is_real_uat:
            # DETERMINISTIC DEMO SIMULATION (Atomic single transaction BEGIN IMMEDIATE)
            fill_price = proposal.quote.ask if proposal.side == OrderSide.BUY else proposal.quote.bid
            return Storage.execute_demo_fill_atomic(
                proposal_id=proposal_id,
                user_id=user_id,
                asset=proposal.asset,
                side=proposal.side,
                estimated_qty=proposal.estimated_qty,
                estimated_notional_usd=proposal.estimated_notional_usd,
                fill_price=fill_price,
                raw_prompt=proposal.raw_prompt,
            )

        else:
            # REAL TRUE MARKETS UAT GATEWAY EXECUTION
            # Pre-execution balance check
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

            # Dispatch to gateway
            try:
                gw_order = await tm_client.create_order(
                    pair=proposal.quote.pair,
                    side=proposal.side.value,
                    quantity=proposal.estimated_qty,
                    quote_id=proposal.quote.quote_id,
                    user_id=user_id,
                )
            except TrueMarketsClientError as e:
                # Creation failed before gateway order existed: safe to release claim
                Storage.update_proposal_status(proposal_id, "PENDING_CONFIRMATION", user_id=user_id)
                raise HTTPException(status_code=e.status_code or 502, detail=str(e))

            ext_id = gw_order.get("id") or gw_order.get("order_id")

            # Persist order immediately with external ID
            # CRITICAL: Never release proposal claim once gateway order exists!
            order = OrderRecord(
                id=order_id,
                proposal_id=proposal.id,
                user_id=user_id,
                asset=proposal.asset,
                side=proposal.side,
                quantity=proposal.estimated_qty,
                notional_usd=proposal.estimated_notional_usd,
                status=OrderStatus.SUBMITTED,
                external_order_id=ext_id,
                fill_price=None,  # Never use quote mid
                created_at=now,
                updated_at=now,
                mode="UAT",
                audit_id=f"audit-{order_id}",
                raw_prompt=proposal.raw_prompt,
            )
            Storage.save_order(order)

            Storage.save_audit_event(AuditEvent(
                id=f"evt-{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                event_type="UAT_ORDER_SUBMITTED",
                proposal_id=proposal_id,
                order_id=order_id,
                summary=f"Submitted to True Markets UAT Gateway: Order ID {ext_id}.",
                metadata={"external_id": ext_id, "mode": "UAT"},
                timestamp=now,
            ))

            # Execute order (Never blindly retry execute)
            try:
                exec_res = await tm_client.execute_order(order_id=ext_id, user_id=user_id)
                status_str = exec_res.get("status", "SUBMITTED").upper()
                order_status = OrderStatus.FILLED if status_str in ("FILLED", "COMPLETED") else OrderStatus.SUBMITTED

                gateway_fill_price = None
                if order_status == OrderStatus.FILLED:
                    raw_fill = exec_res.get("fill_price") or exec_res.get("price") or gw_order.get("fill_price")
                    if raw_fill is not None:
                        try:
                            gateway_fill_price = float(raw_fill)
                        except (ValueError, TypeError):
                            gateway_fill_price = None

                now_up = datetime.now(timezone.utc).isoformat()
                order.status = order_status
                order.fill_price = gateway_fill_price
                order.updated_at = now_up
                Storage.save_order(order)
                Storage.update_proposal_status(proposal_id, "CONFIRMED", user_id=user_id)

                Storage.save_audit_event(AuditEvent(
                    id=f"evt-{uuid.uuid4().hex[:12]}",
                    user_id=user_id,
                    event_type="ORDER_FILLED" if order_status == OrderStatus.FILLED else "ORDER_EXECUTED",
                    proposal_id=proposal_id,
                    order_id=order_id,
                    summary=f"True Markets Gateway executed order {ext_id} (Status: {order_status.value}).",
                    metadata={"external_id": ext_id, "status": order_status.value, "fill_price": gateway_fill_price, "mode": "UAT"},
                    timestamp=now_up,
                ))

                return order

            except Exception as exec_err:
                # On execute failure: mark order FAILED, mark proposal FAILED, require a new proposal
                now_err = datetime.now(timezone.utc).isoformat()
                order.status = OrderStatus.FAILED
                order.updated_at = now_err
                Storage.save_order(order)
                Storage.update_proposal_status(proposal_id, "FAILED", user_id=user_id)

                Storage.save_audit_event(AuditEvent(
                    id=f"evt-{uuid.uuid4().hex[:12]}",
                    user_id=user_id,
                    event_type="ORDER_FAILED",
                    proposal_id=proposal_id,
                    order_id=order_id,
                    summary=f"True Markets execution failed for Order ID {ext_id}: {str(exec_err)}.",
                    metadata={"external_id": ext_id, "error": str(exec_err), "mode": "UAT"},
                    timestamp=now_err,
                ))

                status_code = getattr(exec_err, "status_code", 502) or 502
                raise HTTPException(
                    status_code=status_code,
                    detail=f"Gateway execution failed for external order '{ext_id}'. Order marked FAILED. Please request a new proposal."
                )
