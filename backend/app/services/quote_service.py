from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, Optional
from app.core.config import settings
from app.domain.models import QuoteSnapshot

logger = logging.getLogger("TradeGuard.QuoteService")

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
    def get_demo_quote(cls, asset: str) -> QuoteSnapshot:
        """Generates a deterministic simulated quote strictly tagged as DEMO_SIMULATOR."""
        symbol = asset.upper()
        if symbol not in DEMO_PRICES and symbol not in settings.SUPPORTED_ASSETS:
            raise ValueError(f"Unsupported quote symbol: {asset}")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=settings.QUOTE_TTL_SECONDS)

        base_price = cls.get_price(symbol)
        half_spread = round(base_price * 0.00025, 2)
        bid = round(base_price - half_spread, 2)
        ask = round(base_price + half_spread, 2)
        mid = round(base_price, 2)
        spread_pct = round(((ask - bid) / mid) * 100, 3)

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
            source="DEMO_SIMULATOR",
            quote_id=None,
        )

    @classmethod
    async def get_quote(cls, asset: str, user_id: str = "demo-user-1") -> QuoteSnapshot:
        """
        Obtains a quote.
        In UAT mode with configured credentials, calls TrueMarketsClient.get_quote
        and tags the quote as TRUE_MARKETS_UAT only when gateway-sourced.
        In DEMO mode or unconfigured UAT, returns deterministic DEMO_SIMULATOR quote.
        Static prices are never tagged as UAT.
        """
        symbol = asset.upper()
        if symbol not in DEMO_PRICES and symbol not in settings.SUPPORTED_ASSETS:
            raise ValueError(f"Unsupported quote symbol: {asset}")

        from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError

        if settings.TM_ENV == "uat":
            tm_client = TrueMarketsClient()
            if tm_client.is_configured():
                try:
                    gw_data = await tm_client.get_quote(
                        pair=f"{symbol}/USDC",
                        side="BUY",
                        amount=1.0,
                        user_id=user_id,
                    )
                    now = datetime.now(timezone.utc)
                    expires_at = gw_data.get("expires_at") or (
                        now + timedelta(seconds=settings.QUOTE_TTL_SECONDS)
                    ).isoformat()
                    bid = float(gw_data["bid"])
                    ask = float(gw_data["ask"])
                    mid = float(gw_data.get("mid", (bid + ask) / 2))
                    spread_pct = (
                        round(((ask - bid) / mid) * 100, 3) if mid > 0 else 0.0
                    )
                    quote_id = str(gw_data.get("quote_id") or gw_data.get("id") or "")

                    return QuoteSnapshot(
                        pair=gw_data.get("pair", f"{symbol}/USDC"),
                        base_asset=symbol,
                        quote_asset="USDC",
                        bid=bid,
                        ask=ask,
                        mid=mid,
                        spread_pct=spread_pct,
                        timestamp=gw_data.get("timestamp") or now.isoformat(),
                        expires_at=expires_at,
                        source="TRUE_MARKETS_UAT",
                        quote_id=quote_id or None,
                    )
                except TrueMarketsClientError:
                    raise
                except Exception as e:
                    logger.error("Unexpected error fetching True Markets quote: %s", e)
                    raise TrueMarketsClientError(
                        f"Gateway quote failed: {str(e)}",
                        status_code=503,
                        error_code="GATEWAY_UNAVAILABLE",
                    )

        # In DEMO mode or if UAT credentials are unconfigured:
        # Return deterministic DEMO_SIMULATOR quote. No static price is ever tagged UAT.
        return cls.get_demo_quote(symbol)

    @classmethod
    def is_quote_fresh(cls, quote: QuoteSnapshot) -> bool:
        now = datetime.now(timezone.utc)
        try:
            expires = datetime.fromisoformat(quote.expires_at)
            return now < expires
        except Exception:
            return False
