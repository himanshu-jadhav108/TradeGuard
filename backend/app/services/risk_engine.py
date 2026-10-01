from typing import Dict, List, Tuple
from app.core.config import settings
from app.domain.models import (
    AmountType,
    OrderSide,
    PortfolioImpact,
    QuoteSnapshot,
    RiskCheckItem,
    RiskLevel,
    RiskResult,
)
from app.services.quote_service import QuoteService


class RiskEngine:
    @classmethod
    def evaluate_trade(
        cls,
        asset: str,
        side: OrderSide,
        request_amount: float,
        request_amount_type: AmountType,
        quote: QuoteSnapshot,
        cash_usd: float,
        current_positions: Dict[str, float],
    ) -> Tuple[RiskResult, PortfolioImpact, float, float]:
        """
        Runs authoritative, deterministic risk checks.
        Returns:
          - RiskResult (overall_status, can_execute, checks)
          - PortfolioImpact
          - estimated_qty
          - estimated_notional_usd
        """
        checks: List[RiskCheckItem] = []
        symbol = asset.upper()

        # 1. Asset Support Check
        if symbol not in settings.SUPPORTED_ASSETS:
            checks.append(RiskCheckItem(
                name="Asset Support",
                status=RiskLevel.BLOCK,
                message=f"Asset '{symbol}' is not on the supported trading allowlist.",
                details={"asset": symbol, "allowed": settings.SUPPORTED_ASSETS}
            ))
        else:
            checks.append(RiskCheckItem(
                name="Asset Support",
                status=RiskLevel.PASS,
                message=f"Asset '{symbol}' is verified on the supported allowlist.",
            ))

        # 2. Quote Freshness Check
        if not QuoteService.is_quote_fresh(quote):
            checks.append(RiskCheckItem(
                name="Quote Freshness",
                status=RiskLevel.BLOCK,
                message="Quote has expired or exceeded maximum time-to-live. A new quote is required.",
                details={"quote_timestamp": quote.timestamp, "expires_at": quote.expires_at}
            ))
        else:
            checks.append(RiskCheckItem(
                name="Quote Freshness",
                status=RiskLevel.PASS,
                message="Live market quote is fresh and within the 30-second TTL window.",
            ))

        # Quantity and Notional Calculations
        price = quote.ask if side == OrderSide.BUY else quote.bid
        if request_amount_type == AmountType.USD:
            notional_usd = request_amount
            qty = round(request_amount / price, 6)
        else:
            qty = request_amount
            notional_usd = round(qty * price, 2)

        # 3. Positive Quantity / Notional Check
        if qty <= 0 or notional_usd <= 0:
            checks.append(RiskCheckItem(
                name="Valid Amount",
                status=RiskLevel.BLOCK,
                message="Trade quantity and notional amount must be strictly greater than zero.",
            ))
        else:
            checks.append(RiskCheckItem(
                name="Valid Amount",
                status=RiskLevel.PASS,
                message=f"Calculated {qty:,.6f} {symbol} (${notional_usd:,.2f} USD).",
            ))

        # 4. Maximum Order Notional Limit Check
        if notional_usd > settings.MAX_NOTIONAL_USD:
            checks.append(RiskCheckItem(
                name="Maximum Notional Limit",
                status=RiskLevel.BLOCK,
                message=f"Order size of ${notional_usd:,.2f} exceeds strict system ceiling of ${settings.MAX_NOTIONAL_USD:,.2f}.",
                details={"max_allowed_usd": settings.MAX_NOTIONAL_USD, "requested_usd": notional_usd}
            ))
        else:
            checks.append(RiskCheckItem(
                name="Maximum Notional Limit",
                status=RiskLevel.PASS,
                message=f"Order notional (${notional_usd:,.2f}) is within maximum threshold of ${settings.MAX_NOTIONAL_USD:,.2f}.",
            ))

        # 5. Balance Sufficiency Check
        if side == OrderSide.BUY:
            if notional_usd > cash_usd:
                shortfall = notional_usd - cash_usd
                checks.append(RiskCheckItem(
                    name="Balance Sufficiency",
                    status=RiskLevel.BLOCK,
                    message=f"Insufficient cash balance. Available: ${cash_usd:,.2f}, required: ${notional_usd:,.2f} (shortfall: ${shortfall:,.2f}).",
                    details={"available_cash": cash_usd, "required_cash": notional_usd}
                ))
            else:
                checks.append(RiskCheckItem(
                    name="Balance Sufficiency",
                    status=RiskLevel.PASS,
                    message=f"Cash balance of ${cash_usd:,.2f} is sufficient for ${notional_usd:,.2f} purchase.",
                ))
        elif side == OrderSide.SELL:
            current_asset_qty = current_positions.get(symbol, 0.0)
            if qty > current_asset_qty:
                checks.append(RiskCheckItem(
                    name="Position Sufficiency",
                    status=RiskLevel.BLOCK,
                    message=f"Insufficient asset balance. Owned: {current_asset_qty:,.6f} {symbol}, requested sell: {qty:,.6f} {symbol}.",
                    details={"available_qty": current_asset_qty, "requested_qty": qty}
                ))
            else:
                checks.append(RiskCheckItem(
                    name="Position Sufficiency",
                    status=RiskLevel.PASS,
                    message=f"Holding of {current_asset_qty:,.6f} {symbol} is sufficient for sale.",
                ))

        # Calculate Portfolio Impact & Concentration
        current_asset_qty = current_positions.get(symbol, 0.0)
        current_asset_val = current_asset_qty * quote.mid
        
        # Calculate total portfolio value before
        total_val_before = cash_usd
        for a, q in current_positions.items():
            if a == symbol:
                total_val_before += current_asset_val
            else:
                # Estimate other values
                p = 2680.5 if a == "ETH" else (182.25 if a == "SOL" else 1.0)
                total_val_before += q * p

        curr_alloc_pct = (current_asset_val / total_val_before) if total_val_before > 0 else 0.0

        if side == OrderSide.BUY:
            projected_qty = round(current_asset_qty + qty, 6)
            cash_after = round(cash_usd - notional_usd, 2)
        else:
            projected_qty = round(max(0.0, current_asset_qty - qty), 6)
            cash_after = round(cash_usd + notional_usd, 2)

        projected_asset_val = projected_qty * quote.mid
        total_val_after = cash_after + (total_val_before - cash_usd - current_asset_val) + projected_asset_val
        proj_alloc_pct = (projected_asset_val / total_val_after) if total_val_after > 0 else 0.0

        # 6. Concentration Warning Check
        if side == OrderSide.BUY and proj_alloc_pct > settings.CONCENTRATION_THRESHOLD_PCT:
            checks.append(RiskCheckItem(
                name="Portfolio Concentration",
                status=RiskLevel.WARN,
                message=f"Order raises {symbol} concentration to {proj_alloc_pct * 100:.1f}%, exceeding guideline threshold of {settings.CONCENTRATION_THRESHOLD_PCT * 100:.0f}%.",
                details={
                    "current_pct": round(curr_alloc_pct * 100, 1),
                    "projected_pct": round(proj_alloc_pct * 100, 1),
                    "threshold_pct": round(settings.CONCENTRATION_THRESHOLD_PCT * 100, 1)
                }
            ))
        else:
            checks.append(RiskCheckItem(
                name="Portfolio Concentration",
                status=RiskLevel.PASS,
                message=f"Projected {symbol} allocation is {proj_alloc_pct * 100:.1f}%, within balanced diversification limits.",
            ))

        # Overall Status Determination
        has_block = any(c.status == RiskLevel.BLOCK for c in checks)
        has_warn = any(c.status == RiskLevel.WARN for c in checks)
        overall_status = RiskLevel.BLOCK if has_block else (RiskLevel.WARN if has_warn else RiskLevel.PASS)
        can_execute = not has_block

        impact = PortfolioImpact(
            asset=symbol,
            current_qty=current_asset_qty,
            current_value_usd=round(current_asset_val, 2),
            current_allocation_pct=round(curr_alloc_pct * 100, 1),
            projected_qty=projected_qty,
            projected_value_usd=round(projected_asset_val, 2),
            projected_allocation_pct=round(proj_alloc_pct * 100, 1),
            cash_before_usd=round(cash_usd, 2),
            cash_after_usd=round(cash_after, 2),
            total_portfolio_value_before=round(total_val_before, 2),
            total_portfolio_value_after=round(total_val_after, 2),
        )

        risk_result = RiskResult(
            overall_status=overall_status,
            can_execute=can_execute,
            checks=checks,
        )

        return risk_result, impact, qty, notional_usd
