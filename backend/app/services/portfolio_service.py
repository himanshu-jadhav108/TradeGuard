from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List
from app.core.config import settings
from app.db.store import Storage
from app.domain.models import Position, PortfolioSummary
from app.services.quote_service import QuoteService


class PortfolioService:
    @classmethod
    def get_summary(cls, user_id: str = "demo-user-1") -> PortfolioSummary:
        data = Storage.get_portfolio(user_id)
        d_cash = Decimal(str(data["cash_usd"]))
        positions_map = data["positions"]

        positions: List[Position] = []
        d_total_assets_val = Decimal("0.00")

        for asset, qty in positions_map.items():
            d_qty = Decimal(str(qty))
            if d_qty <= Decimal("0"):
                continue
            price = QuoteService.get_price(asset)
            d_price = Decimal(str(price))
            d_val = (d_qty * d_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            d_total_assets_val += d_val

            positions.append(
                Position(
                    asset=asset,
                    quantity=float(d_qty),
                    price_usd=price,
                    value_usd=float(d_val),
                    allocation_pct=0.0,
                )
            )

        d_total_value = (d_cash + d_total_assets_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Calculate exact percentages
        for p in positions:
            d_val = Decimal(str(p.value_usd))
            p.allocation_pct = (
                float((d_val / d_total_value * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
                if d_total_value > Decimal("0")
                else 0.0
            )

        from app.services.true_markets_client import TrueMarketsClient
        is_real_uat = settings.TM_ENV == "uat" and TrueMarketsClient().is_configured()
        mode = "UAT" if is_real_uat else "DEMO"

        return PortfolioSummary(
            user_id=user_id,
            cash_usd=float(d_cash),
            total_value_usd=float(d_total_value),
            positions=positions,
            mode=mode,
            as_of=datetime.now(timezone.utc).isoformat(),
        )
