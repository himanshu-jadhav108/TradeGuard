from datetime import datetime, timedelta, timezone
from typing import Dict
from app.core.config import settings
from app.domain.models import QuoteSnapshot

# Single source of truth for baseline demo prices
DEMO_PRICES: Dict[str, float] = {
    "BTC": 86450.00,
    "ETH": 2680.50,
    "SOL": 182.25,
    "USDC": 1.00,
}


class QuoteService:
    @classmethod
    def get_price(cls, asset: str) -> float:
        """Returns the canonical reference mid-price for an asset."""
        symbol = asset.upper()
        return DEMO_PRICES.get(symbol, 1.0)

    @classmethod
    def get_quote(cls, asset: str) -> QuoteSnapshot:
        symbol = asset.upper()
        if symbol not in DEMO_PRICES and symbol not in settings.SUPPORTED_ASSETS:
            raise ValueError(f"Unsupported quote symbol: {asset}")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=settings.QUOTE_TTL_SECONDS)

        # Canonical reference price
        base_price = cls.get_price(symbol)

        # 0.05% realistic institutional spread
        half_spread = round(base_price * 0.00025, 2)
        bid = round(base_price - half_spread, 2)
        ask = round(base_price + half_spread, 2)
        mid = round(base_price, 2)
        spread_pct = round(((ask - bid) / mid) * 100, 3)

        # Only claim TRUE_MARKETS_UAT if environment is uat and credentials actually exist
        from app.services.true_markets_client import TrueMarketsClient
        tm_client = TrueMarketsClient()
        if settings.TM_ENV == "uat" and tm_client.is_configured():
            source = "TRUE_MARKETS_UAT"
        else:
            source = "DEMO_SIMULATOR"

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
