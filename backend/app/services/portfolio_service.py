from datetime import datetime, timezone
from typing import List
from app.core.config import settings
from app.db.store import Storage
from app.domain.models import Position, PortfolioSummary
from app.services.quote_service import QuoteService


class PortfolioService:
    @classmethod
    def get_summary(cls, user_id: str = "demo-user-1") -> PortfolioSummary:
        data = Storage.get_portfolio(user_id)
        cash_usd = data["cash_usd"]
        positions_map = data["positions"]

        positions: List[Position] = []
        total_assets_val = 0.0

        for asset, qty in positions_map.items():
            if qty <= 0:
                continue
            quote = QuoteService.get_quote(asset)
            val = round(qty * quote.mid, 2)
            total_assets_val += val
            
            pnl_24h = 1.85 if asset == "BTC" else (-0.42 if asset == "ETH" else 3.12)
            positions.append(
                Position(
                    asset=asset,
                    quantity=qty,
                    price_usd=quote.mid,
                    value_usd=val,
                    allocation_pct=0.0,  # calculated below
                    pnl_24h_pct=pnl_24h,
                )
            )

        total_value = round(cash_usd + total_assets_val, 2)

        # Calculate exact percentages
        for p in positions:
            p.allocation_pct = round((p.value_usd / total_value) * 100, 1) if total_value > 0 else 0.0

        return PortfolioSummary(
            user_id=user_id,
            cash_usd=cash_usd,
            total_value_usd=total_value,
            positions=positions,
            mode=settings.TM_ENV.upper(),
            as_of=datetime.now(timezone.utc).isoformat(),
        )
