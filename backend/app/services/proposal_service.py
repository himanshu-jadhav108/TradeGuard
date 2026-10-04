import uuid
from datetime import datetime, timezone
from app.db.store import Storage
from app.domain.models import (
    AmountType,
    AuditEvent,
    OrderSide,
    TradeProposal,
    TradeProposalCreateRequest,
)
from app.services.intent_service import IntentService
from app.services.quote_service import QuoteService
from app.services.risk_engine import RiskEngine


class ProposalService:
    @classmethod
    def create_proposal(
        cls, request: TradeProposalCreateRequest, user_id: str = "demo-user-1"
    ) -> TradeProposal:
        raw_prompt = request.prompt

        # 1. Resolve structured intent from prompt or explicit payload
        if request.prompt:
            intent = IntentService.parse_natural_language(request.prompt)
            asset = intent.asset
            side = intent.side
            amount = intent.amount
            amount_type = intent.amount_type
        else:
            if not request.asset or not request.side or not request.amount:
                raise ValueError("Must provide either a prompt or structured (asset, side, amount).")
            asset = request.asset.upper()
            side = request.side
            amount = request.amount
            amount_type = request.amount_type or AmountType.USD

        # 2. Retrieve quote
        quote = QuoteService.get_quote(asset)

        # 3. Retrieve user balances
        portfolio_data = Storage.get_portfolio(user_id)
        cash_usd = portfolio_data["cash_usd"]
        positions = portfolio_data["positions"]

        # 4. Run deterministic risk engine
        risk_result, impact, est_qty, est_notional = RiskEngine.evaluate_trade(
            asset=asset,
            side=side,
            request_amount=amount,
            request_amount_type=amount_type,
            quote=quote,
            cash_usd=cash_usd,
            current_positions=positions,
        )

        # 5. Generate concise, grounded factual explanation based on deterministic values
        verb = "Acquiring" if side == OrderSide.BUY else "Liquidating"
        price = quote.ask if side == OrderSide.BUY else quote.bid
        explanation = (
            f"{verb} {est_qty:,.6f} {asset} at ${price:,.2f} {quote.quote_asset}. "
            f"Cash balance shifts from ${impact.cash_before_usd:,.2f} to ${impact.cash_after_usd:,.2f}, "
            f"moving {asset} exposure from {impact.current_allocation_pct:.1f}% to {impact.projected_allocation_pct:.1f}%."
        )

        now = datetime.now(timezone.utc).isoformat()
        proposal_id = f"prop-{uuid.uuid4().hex[:12]}"

        proposal = TradeProposal(
            id=proposal_id,
            user_id=user_id,
            asset=asset,
            side=side,
            request_amount=amount,
            request_amount_type=amount_type,
            estimated_qty=est_qty,
            estimated_notional_usd=est_notional,
            quote=quote,
            risk=risk_result,
            portfolio_impact=impact,
            explanation=explanation,
            raw_prompt=raw_prompt,
            created_at=now,
            expires_at=quote.expires_at,
            status="PENDING_CONFIRMATION",
            requires_confirmation=True,
            fee_label="Not modelled in demo",
        )

        # 6. Save to storage
        Storage.save_proposal(proposal)

        # 7. Record audit event
        audit_event = AuditEvent(
            id=f"evt-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            event_type="PROPOSAL_CREATED",
            proposal_id=proposal_id,
            summary=f"Created {side.value} proposal for {est_qty:,.6f} {asset} (${est_notional:,.2f} USD). Risk status: {risk_result.overall_status.value}.",
            metadata={
                "asset": asset,
                "side": side.value,
                "amount": amount,
                "amount_type": amount_type.value,
                "raw_prompt": raw_prompt,
                "risk_status": risk_result.overall_status.value,
            },
            timestamp=now,
        )
        Storage.save_audit_event(audit_event)

        return proposal
