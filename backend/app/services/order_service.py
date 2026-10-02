import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from app.core.config import settings
from app.db.store import Storage
from app.domain.models import (
    AuditEvent,
    OrderRecord,
    OrderSide,
    OrderStatus,
    RiskLevel,
)
from app.services.quote_service import QuoteService
from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError


class OrderService:
    @classmethod
    async def confirm_proposal(
        cls, proposal_id: str, user_id: str = "demo-user-1"
    ) -> OrderRecord:
        # 1. Fetch proposal
        proposal = Storage.get_proposal(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found.")

        if proposal.status != "PENDING_CONFIRMATION":
            raise HTTPException(
                status_code=400,
                detail=f"Proposal is already in status '{proposal.status}' and cannot be executed.",
            )

        # 2. Strict Re-Verification of Risk Gate
        if proposal.risk.overall_status == RiskLevel.BLOCK:
            raise HTTPException(
                status_code=400,
                detail="Execution blocked by deterministic risk engine. Blocked trades cannot be overridden.",
            )

        # Verify quote freshness
        if not QuoteService.is_quote_fresh(proposal.quote):
            Storage.update_proposal_status(proposal_id, "EXPIRED")
            raise HTTPException(
                status_code=409,
                detail="Market quote expired before confirmation was received. Please request a new quote.",
            )

        # 3. Verify user balance again
        portfolio_data = Storage.get_portfolio(user_id)
        cash_usd = portfolio_data["cash_usd"]
        positions = portfolio_data["positions"]

        if proposal.side == OrderSide.BUY and proposal.estimated_notional_usd > cash_usd:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient cash balance at confirmation. Needed: ${proposal.estimated_notional_usd:,.2f}, Available: ${cash_usd:,.2f}",
            )
        elif proposal.side == OrderSide.SELL and proposal.estimated_qty > positions.get(proposal.asset, 0.0):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient {proposal.asset} balance at confirmation. Needed: {proposal.estimated_qty:,.6f}, Owned: {positions.get(proposal.asset, 0.0):,.6f}",
            )

        now = datetime.now(timezone.utc).isoformat()
        order_id = f"ord-{uuid.uuid4().hex[:12]}"

        # 4. Route Execution based on Environment
        is_demo = settings.TM_ENV == "demo"
        tm_client = TrueMarketsClient()

        if is_demo or not tm_client.is_configured():
            # DETERMINISTIC DEMO SIMULATION
            external_order_id = f"tm-sim-{uuid.uuid4().hex[:8]}"
            fill_price = proposal.quote.ask if proposal.side == OrderSide.BUY else proposal.quote.bid

            # Create Order Record in FILLED state
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
            )

            # Update portfolio balances deterministically
            if proposal.side == OrderSide.BUY:
                new_cash = round(cash_usd - proposal.estimated_notional_usd, 2)
                positions[proposal.asset] = round(positions.get(proposal.asset, 0.0) + proposal.estimated_qty, 6)
            else:
                new_cash = round(cash_usd + proposal.estimated_notional_usd, 2)
                positions[proposal.asset] = round(max(0.0, positions.get(proposal.asset, 0.0) - proposal.estimated_qty), 6)

            Storage.update_portfolio(user_id, new_cash, positions)
            Storage.update_proposal_status(proposal_id, "CONFIRMED")
            Storage.save_order(order)

            # Audit Trail
            confirm_audit = AuditEvent(
                id=f"evt-{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                event_type="TRADE_CONFIRMED",
                proposal_id=proposal_id,
                order_id=order_id,
                summary=f"User explicitly confirmed {proposal.side.value} {proposal.estimated_qty:,.6f} {proposal.asset}.",
                metadata={"mode": "DEMO", "notional_usd": proposal.estimated_notional_usd},
                timestamp=now,
            )
            Storage.save_audit_event(confirm_audit)

            fill_audit = AuditEvent(
                id=f"evt-{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                event_type="ORDER_FILLED",
                proposal_id=proposal_id,
                order_id=order_id,
                summary=f"Simulated order filled at ${fill_price:,.2f} USDC (External ID: {external_order_id}).",
                metadata={
                    "fill_price": fill_price,
                    "quantity": proposal.estimated_qty,
                    "cash_after": new_cash,
                    "mode": "DEMO",
                },
                timestamp=now,
            )
            Storage.save_audit_event(fill_audit)

            return order

        else:
            # LIVE / UAT GATEWAY EXECUTION
            try:
                # 1. Create order on Gateway
                gw_order = await tm_client.create_order(
                    pair=proposal.quote.pair,
                    side=proposal.side.value,
                    quantity=proposal.estimated_qty,
                    user_id=user_id,
                )
                ext_id = gw_order.get("id") or gw_order.get("order_id")

                # 2. Execute order on Gateway
                exec_res = await tm_client.execute_order(order_id=ext_id, user_id=user_id)
                status_str = exec_res.get("status", "FILLED").upper()

                order_status = OrderStatus.FILLED if status_str in ("FILLED", "COMPLETED") else OrderStatus.SUBMITTED

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
                    fill_price=proposal.quote.mid,
                    created_at=now,
                    updated_at=now,
                    mode="UAT",
                    audit_id=f"audit-{order_id}",
                )

                Storage.update_proposal_status(proposal_id, "CONFIRMED")
                Storage.save_order(order)

                uat_audit = AuditEvent(
                    id=f"evt-{uuid.uuid4().hex[:12]}",
                    user_id=user_id,
                    event_type="UAT_ORDER_SUBMITTED",
                    proposal_id=proposal_id,
                    order_id=order_id,
                    summary=f"Submitted to True Markets UAT Gateway: Order ID {ext_id}, Status: {status_str}.",
                    metadata={"external_id": ext_id, "status": status_str, "mode": "UAT"},
                    timestamp=now,
                )
                Storage.save_audit_event(uat_audit)

                return order

            except TrueMarketsClientError as e:
                raise HTTPException(status_code=e.status_code or 500, detail=str(e))
