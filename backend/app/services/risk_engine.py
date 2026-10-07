from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
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


def to_d(val: float | str | int | Decimal) -> Decimal:
    return Decimal(str(val))


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
        Runs authoritative, deterministic risk checks using Decimal arithmetic.
        Evaluates:
          1. Supported Asset Allowlist
          2. Quote Freshness (TTL)
          3. Positive Quantity & Sane Value
          4. Maximum Order Notional Ceiling ($25,000)
          5. Cash or Position Sufficiency
          6. Portfolio Concentration Threshold (40%)
        """
        checks: List[RiskCheckItem] = []
        symbol = asset.upper()

        d_cash = to_d(cash_usd)
        d_price = to_d(quote.ask if side == OrderSide.BUY else quote.bid)
        d_req_amount = to_d(request_amount)
        d_max_notional = to_d(settings.MAX_NOTIONAL_USD)
        d_concentration_threshold = to_d(settings.CONCENTRATION_THRESHOLD_PCT)

        # 1. Asset Support Check
        if symbol not in settings.SUPPORTED_ASSETS:
            checks.append(RiskCheckItem(
                name="Asset Support",
                status=RiskLevel.BLOCK,
                message=f"Asset '{symbol}' is not on the supported institutional allowlist.",
                details={"observed": symbol, "threshold": "Supported Allowlist", "asset": symbol, "allowed": settings.SUPPORTED_ASSETS},
                suggested_action=f"Select a supported asset: {', '.join(settings.SUPPORTED_ASSETS)}",
                why_it_matters="Execution is restricted to verified, liquid institutional pairs on the allowlist.",
                what_you_can_do=f"Select a supported asset: {', '.join(settings.SUPPORTED_ASSETS)}.",
            ))
        else:
            checks.append(RiskCheckItem(
                name="Asset Support",
                status=RiskLevel.PASS,
                message=f"Asset '{symbol}' is verified on the supported allowlist.",
                details={"observed": symbol, "threshold": "Supported Allowlist", "asset": symbol, "allowed": settings.SUPPORTED_ASSETS},
                why_it_matters="Asset is verified on the institutional allowlist.",
                what_you_can_do="Proceed with order review.",
            ))

        # 2. Quote Freshness Check
        quote_age: float = 0.0
        if quote.age_seconds is not None:
            quote_age = quote.age_seconds
        else:
            try:
                q_ts = datetime.fromisoformat(quote.timestamp.replace("Z", "+00:00"))
                quote_age = max(0.0, (datetime.now(timezone.utc) - q_ts).total_seconds())
            except Exception:
                quote_age = 0.0

        ttl_str = f"{settings.QUOTE_TTL_SECONDS:.1f}s TTL"
        if not QuoteService.is_quote_fresh(quote):
            checks.append(RiskCheckItem(
                name="Quote Freshness",
                status=RiskLevel.BLOCK,
                message="Quote has expired or exceeded maximum time-to-live. A new quote must be requested.",
                details={"observed": f"{quote_age:.1f}s age", "threshold": ttl_str, "quote_timestamp": quote.timestamp, "expires_at": quote.expires_at},
                suggested_action="Refresh quote to retrieve fresh pricing.",
                why_it_matters="Quotes older than 30 seconds risk adverse execution slippage in volatile market conditions.",
                what_you_can_do="Click 'Refresh Expired Quote' to fetch a fresh market snapshot.",
            ))
        else:
            checks.append(RiskCheckItem(
                name="Quote Freshness",
                status=RiskLevel.PASS,
                message="Market quote is fresh and within the 30-second TTL window.",
                details={"observed": f"{quote_age:.1f}s age", "threshold": ttl_str, "quote_timestamp": quote.timestamp, "expires_at": quote.expires_at},
                why_it_matters="Quote freshness guarantees pricing within the strict 30-second execution window.",
                what_you_can_do="Proceed with order review.",
            ))

        # 3. Calculate Quantity and Notional in Decimal
        if request_amount_type == AmountType.USD:
            d_notional = d_req_amount
            d_qty = (d_notional / d_price).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        else:
            d_qty = d_req_amount.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            d_notional = (d_qty * d_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        qty = float(d_qty)
        notional_usd = float(d_notional)

        # Valid Amount Check
        if d_qty <= Decimal("0") or d_notional <= Decimal("0"):
            checks.append(RiskCheckItem(
                name="Valid Amount",
                status=RiskLevel.BLOCK,
                message="Trade quantity and notional amount must be strictly greater than zero.",
                details={"observed": f"${notional_usd:,.2f} ({qty:,.6f} {symbol})", "threshold": "> $0.00"},
                why_it_matters="Zero or negative trade values cannot be routed to exchange order books.",
                what_you_can_do="Specify a positive dollar or token amount.",
            ))
        else:
            checks.append(RiskCheckItem(
                name="Valid Amount",
                status=RiskLevel.PASS,
                message=f"Calculated {qty:,.6f} {symbol} (${notional_usd:,.2f} USD).",
                details={"observed": f"${notional_usd:,.2f} ({qty:,.6f} {symbol})", "threshold": "> $0.00"},
                why_it_matters="Order amount and derived quantities are strictly positive.",
                what_you_can_do="Proceed with order review.",
            ))

        # 4. Maximum Order Notional Limit Check ($25,000)
        suggested_safe_amount: Optional[float] = None
        if d_notional > d_max_notional:
            suggested_safe_amount = float(d_max_notional)
            checks.append(RiskCheckItem(
                name="Maximum Notional Limit",
                status=RiskLevel.BLOCK,
                message=f"Order size of ${notional_usd:,.2f} exceeds strict system ceiling of ${float(d_max_notional):,.2f}.",
                details={"observed": f"${notional_usd:,.2f}", "threshold": f"${float(d_max_notional):,.2f}", "max_allowed_usd": float(d_max_notional), "requested_usd": notional_usd},
                suggested_action=f"Reduce order size to ${float(d_max_notional):,.2f} or less.",
                why_it_matters=f"Strict order ceiling (${float(d_max_notional):,.2f}) prevents catastrophic fat-finger entries and runaway exposures.",
                what_you_can_do=f"Reduce order size to ${float(d_max_notional):,.2f} or use the suggested safe amount.",
            ))
        else:
            checks.append(RiskCheckItem(
                name="Maximum Notional Limit",
                status=RiskLevel.PASS,
                message=f"Order notional (${notional_usd:,.2f}) is within maximum threshold of ${float(d_max_notional):,.2f}.",
                details={"observed": f"${notional_usd:,.2f}", "threshold": f"${float(d_max_notional):,.2f}", "max_allowed_usd": float(d_max_notional), "requested_usd": notional_usd},
                why_it_matters=f"Order notional remains strictly under the safety ceiling (${float(d_max_notional):,.2f}).",
                what_you_can_do="Proceed with order review.",
            ))

        # 5. Balance Sufficiency Check
        if side == OrderSide.BUY:
            if d_notional > d_cash:
                d_shortfall = d_notional - d_cash
                if suggested_safe_amount is None or float(d_cash) < suggested_safe_amount:
                    suggested_safe_amount = float(d_cash)
                checks.append(RiskCheckItem(
                    name="Balance Sufficiency",
                    status=RiskLevel.BLOCK,
                    message=f"Insufficient cash balance. Available: ${float(d_cash):,.2f}, required: ${notional_usd:,.2f} (shortfall: ${float(d_shortfall):,.2f}).",
                    details={"observed": f"${notional_usd:,.2f} required", "threshold": f"${float(d_cash):,.2f} available", "available_cash": float(d_cash), "required_cash": notional_usd},
                    suggested_action=f"Reduce buy amount to your available cash of ${float(d_cash):,.2f}.",
                    why_it_matters="Orders requiring more cash than available in your settled balance cannot be executed.",
                    what_you_can_do=f"Reduce buy amount to your available cash of ${float(d_cash):,.2f} or deposit additional USDC.",
                ))
            else:
                checks.append(RiskCheckItem(
                    name="Balance Sufficiency",
                    status=RiskLevel.PASS,
                    message=f"Cash balance of ${float(d_cash):,.2f} is sufficient for ${notional_usd:,.2f} purchase.",
                    details={"observed": f"${notional_usd:,.2f} required", "threshold": f"${float(d_cash):,.2f} available", "available_cash": float(d_cash), "required_cash": notional_usd},
                    why_it_matters="Liquid purchasing power is verified sufficient for full settlement.",
                    what_you_can_do="Proceed with order review.",
                ))
        elif side == OrderSide.SELL:
            d_current_qty = to_d(current_positions.get(symbol, 0.0))
            if d_qty > d_current_qty:
                checks.append(RiskCheckItem(
                    name="Position Sufficiency",
                    status=RiskLevel.BLOCK,
                    message=f"Insufficient asset balance. Owned: {float(d_current_qty):,.6f} {symbol}, requested sell: {qty:,.6f} {symbol}.",
                    details={"observed": f"{qty:,.6f} {symbol} requested", "threshold": f"{float(d_current_qty):,.6f} {symbol} owned", "available_qty": float(d_current_qty), "requested_qty": qty},
                    suggested_action=f"Adjust sell quantity to your owned balance of {float(d_current_qty):,.6f} {symbol}.",
                    why_it_matters="Short selling is disabled; orders cannot exceed owned token holdings.",
                    what_you_can_do=f"Adjust sell quantity to your owned balance of {float(d_current_qty):,.6f} {symbol}.",
                ))
            else:
                checks.append(RiskCheckItem(
                    name="Position Sufficiency",
                    status=RiskLevel.PASS,
                    message=f"Holding of {float(d_current_qty):,.6f} {symbol} is sufficient for sale.",
                    details={"observed": f"{qty:,.6f} {symbol} requested", "threshold": f"{float(d_current_qty):,.6f} {symbol} owned", "available_qty": float(d_current_qty), "requested_qty": qty},
                    why_it_matters="Sufficient asset inventory is verified in your portfolio.",
                    what_you_can_do="Proceed with order review.",
                ))

        # 6. Portfolio Impact & Single Source of Truth Valuation
        d_curr_asset_qty = to_d(current_positions.get(symbol, 0.0))
        d_mid_price = to_d(quote.mid)
        d_current_asset_val = (d_curr_asset_qty * d_mid_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Calculate total portfolio value before from single source of truth (QuoteService.get_price)
        d_total_val_before = d_cash
        for a, q in current_positions.items():
            if a == symbol:
                d_total_val_before += d_current_asset_val
            else:
                p = to_d(QuoteService.get_price(a))
                d_total_val_before += (to_d(q) * p).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        d_curr_alloc_pct = (
            (d_current_asset_val / d_total_val_before * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            if d_total_val_before > Decimal("0")
            else Decimal("0.0")
        )

        if side == OrderSide.BUY:
            d_proj_qty = (d_curr_asset_qty + d_qty).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            d_cash_after = (d_cash - d_notional).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            d_proj_qty = max(Decimal("0"), d_curr_asset_qty - d_qty).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            d_cash_after = (d_cash + d_notional).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        d_proj_asset_val = (d_proj_qty * d_mid_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        d_total_val_after = d_cash_after + (d_total_val_before - d_cash - d_current_asset_val) + d_proj_asset_val

        d_proj_alloc_pct = (
            (d_proj_asset_val / d_total_val_after * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            if d_total_val_after > Decimal("0")
            else Decimal("0.0")
        )

        # 7. Concentration Warning Check (Guideline)
        warn_requires_ack = False
        concentration_threshold_display = float(d_concentration_threshold * Decimal("100"))

        if side == OrderSide.BUY and (d_proj_alloc_pct / Decimal("100")) > d_concentration_threshold:
            warn_requires_ack = True
            checks.append(RiskCheckItem(
                name="Portfolio Concentration",
                status=RiskLevel.WARN,
                message=f"Order increases {symbol} concentration to {float(d_proj_alloc_pct):.1f}%, exceeding your {concentration_threshold_display:.0f}% guideline threshold.",
                details={
                    "observed": f"{float(d_proj_alloc_pct):.1f}%",
                    "threshold": f"{concentration_threshold_display:.0f}%",
                    "current_pct": float(d_curr_alloc_pct),
                    "projected_pct": float(d_proj_alloc_pct),
                    "threshold_pct": concentration_threshold_display,
                },
                suggested_action=f"Acknowledging this warning allows confirmation, or reduce order size to maintain <{concentration_threshold_display:.0f}% allocation.",
                why_it_matters=f"The proposed trade increases portfolio concentration in {symbol} beyond the configured {concentration_threshold_display:.0f}% guideline.",
                what_you_can_do=f"Reduce order size to stay under {concentration_threshold_display:.0f}%, or acknowledge this risk to proceed with confirmation.",
            ))
        else:
            checks.append(RiskCheckItem(
                name="Portfolio Concentration",
                status=RiskLevel.PASS,
                message=f"Projected {symbol} allocation is {float(d_proj_alloc_pct):.1f}%, within balanced diversification limits.",
                details={
                    "observed": f"{float(d_proj_alloc_pct):.1f}%",
                    "threshold": f"{concentration_threshold_display:.0f}%",
                    "current_pct": float(d_curr_alloc_pct),
                    "projected_pct": float(d_proj_alloc_pct),
                    "threshold_pct": concentration_threshold_display,
                },
                why_it_matters=f"Projected portfolio allocation remains diversified within the {concentration_threshold_display:.0f}% guideline threshold.",
                what_you_can_do="Proceed with order review.",
            ))

        # Overall Status Determination
        has_block = any(c.status == RiskLevel.BLOCK for c in checks)
        has_warn = any(c.status == RiskLevel.WARN for c in checks)
        overall_status = RiskLevel.BLOCK if has_block else (RiskLevel.WARN if has_warn else RiskLevel.PASS)
        can_execute = not has_block

        block_reason = None
        if has_block:
            first_block = next(c for c in checks if c.status == RiskLevel.BLOCK)
            block_reason = first_block.message

        impact = PortfolioImpact(
            asset=symbol,
            current_qty=float(d_curr_asset_qty),
            current_value_usd=float(d_current_asset_val),
            current_allocation_pct=float(d_curr_alloc_pct),
            projected_qty=float(d_proj_qty),
            projected_value_usd=float(d_proj_asset_val),
            projected_allocation_pct=float(d_proj_alloc_pct),
            cash_before_usd=float(d_cash),
            cash_after_usd=float(d_cash_after),
            total_portfolio_value_before=float(d_total_val_before),
            total_portfolio_value_after=float(d_total_val_after),
        )

        risk_result = RiskResult(
            overall_status=overall_status,
            can_execute=can_execute,
            checks=checks,
            warn_requires_ack=warn_requires_ack,
            block_reason=block_reason,
            suggested_safe_amount_usd=suggested_safe_amount,
        )

        return risk_result, impact, qty, notional_usd
