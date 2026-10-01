import re
from typing import Optional
from fastapi import HTTPException
from app.core.config import settings
from app.domain.models import AmountType, OrderSide, ParsedIntent


class IntentService:
    @classmethod
    def parse_natural_language(cls, prompt: str) -> ParsedIntent:
        clean_text = prompt.strip()
        if not clean_text:
            raise HTTPException(status_code=400, detail="Trade prompt cannot be empty.")

        # Match BUY or SELL keywords
        lower = clean_text.lower()
        side: OrderSide
        if any(w in lower for w in ["buy", "purchase", "acquire", "long", "get"]):
            side = OrderSide.BUY
        elif any(w in lower for w in ["sell", "liquidate", "short", "dump", "close"]):
            side = OrderSide.SELL
        else:
            raise HTTPException(
                status_code=422,
                detail="Unable to determine trade direction (BUY/SELL) from input."
            )

        # Match Asset from allowlist
        asset: Optional[str] = None
        for supp in settings.SUPPORTED_ASSETS:
            # Check symbol or common names
            patterns = [
                rf"\b{supp}\b",
                rf"\bbitcoin\b" if supp == "BTC" else None,
                rf"\bethereum\b" if supp == "ETH" else None,
                rf"\bsolana\b" if supp == "SOL" else None,
                rf"\busdc\b" if supp == "USDC" else None,
            ]
            for pat in patterns:
                if pat and re.search(pat, lower, re.IGNORECASE):
                    asset = supp
                    break
            if asset:
                break

        if not asset:
            raise HTTPException(
                status_code=422,
                detail=f"Asset not recognized or unsupported. Supported assets: {', '.join(settings.SUPPORTED_ASSETS)}"
            )

        # Match Amount and Amount Type ($500 vs 0.5 BTC)
        # Check USD amount pattern first: e.g. $500, $ 500.50, 500 usd, 500 usdc, 500 dollars
        usd_pattern = re.search(r"\$\s*([0-9,]+(?:\.[0-9]+)?)|([0-9,]+(?:\.[0-9]+)?)\s*(?:usd|usdc|dollars)", lower)
        amount: Optional[float] = None
        amount_type: AmountType = AmountType.USD

        if usd_pattern:
            val_str = usd_pattern.group(1) or usd_pattern.group(2)
            amount = float(val_str.replace(",", ""))
            amount_type = AmountType.USD
        else:
            # Check asset qty pattern: e.g. 0.05 btc, 2 eth, 10 sol
            asset_pattern = re.search(
                rf"([0-9,]+(?:\.[0-9]+)?)\s*(?:{asset.lower()}|tokens|shares|coins)", lower
            )
            if asset_pattern:
                amount = float(asset_pattern.group(1).replace(",", ""))
                amount_type = AmountType.ASSET
            else:
                # Generic fallback number
                num_match = re.search(r"([0-9,]+(?:\.[0-9]+)?)", clean_text)
                if num_match:
                    amount = float(num_match.group(1).replace(",", ""))
                    amount_type = AmountType.USD
                else:
                    raise HTTPException(
                        status_code=422,
                        detail="Could not extract a valid trade amount from request."
                    )

        if amount <= 0:
            raise HTTPException(
                status_code=422,
                detail="Trade amount must be strictly greater than zero."
            )

        return ParsedIntent(
            asset=asset,
            side=side,
            amount=amount,
            amount_type=amount_type,
            raw_prompt=clean_text,
            confidence=0.98,
        )
