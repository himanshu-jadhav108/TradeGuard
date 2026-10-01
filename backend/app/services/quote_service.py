from datetime import datetime, timedelta, timezone
from typing import Dict
from app.core.config import settings
from app.domain.models import QuoteSnapshot

# Baseline seed prices for deterministic demo execution
DEMO_PRICES: Dict[str, float] = {
    "BTC": 86450.00,
    "ETH": 2680.50,
    "SOL": 182.25,
    "USDC": 1.00,
}


class QuoteService:
    @classmethod
    def get_quote(cls, asset: str) -> QuoteSnapshot:
        symbol = asset.upper()
        if symbol not in DEMO_PRICES and symbol not in settings.SUPPORTED_ASSETS:
            raise ValueError(f"Unsupported quote symbol: {asset}")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=settings.QUOTE_TTL_SECONDS)

        # Baseline mid price
        base_price = DEMO_PRICES.get(symbol, 100.0)
        
        # 0.05% realistic institutional spread
        half_spread = base_price * 0.00025
        bid = round(base_price - half_spread, 2)
        ask = round(base_price + half_spread, 2)
        mid = round(base_price, 2)
        spread_pct = round(((ask - bid) / mid) * 100, 3)

        source = "DEMO_SIMULATOR" if settings.TM_ENV == "demo" else "TRUE_MARKETS_UAT"

        return QuoteSnapshot(
            pair=f"{symbol}/USDC",
            base_asset=symbol,
            quote_asset="USDC",
            bid=bid,
            ask=ask,
            mid=mid,
            spread_pct=spread_pct,
            timestamp=now.isoformat(),
            expires_at=expires_at.isoformat(),
            source=source,
        )

    @classmethod
    def is_quote_fresh(cls, quote: QuoteSnapshot) -> bool:
        now = datetime.now(timezone.utc)
        try:
            expires = datetime.fromisoformat(quote.expires_at)
            return now < expires
        except Exception:
            return False
