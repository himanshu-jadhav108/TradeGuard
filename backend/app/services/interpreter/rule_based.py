import math
import re
from typing import List, Optional, Tuple
from app.core.config import settings
from app.domain.models import AmountType, OrderSide, ParsedIntent
from app.services.interpreter.base import BaseInterpreter, InterpretationResult

MAX_PROMPT_LENGTH = 280
MAX_SAFE_AMOUNT = 10_000_000.0

# Canonical asset name mappings
ASSET_ALIASES = {
    "BTC": ["btc", "bitcoin"],
    "ETH": ["eth", "ether", "ethereum"],
    "SOL": ["sol", "solana"],
    "USDC": ["usdc", "usd coin"],
}

# Negation keywords indicating conflicting commands or cancellations
NEGATION_WORDS = ["don't", "dont", "do not", "never", "stop", "cancel", "abort", "not"]

# Multi-leg or alternative conjunctions
MULTI_LEG_PATTERNS = [
    r"\band\s+(?:then\s+)?(?:buy|sell|long|short)\b",
    r"\bor\s+(?:buy|sell|long|short)\b",
    r"\bor\b",
    r";",
    r"&&",
]


class RuleBasedInterpreter(BaseInterpreter):
    """
    Authoritative, deterministic natural-language intent parser.
    Identifies single-leg trades with explicit side, asset, and unit detection.
    Rejects negation, multi-leg requests, scientific notation, and ambiguous units with structured clarifications.
    """

    def parse(self, prompt: str) -> InterpretationResult:
        if not prompt or not prompt.strip():
            return InterpretationResult(
                success=False,
                error="Trade prompt cannot be empty.",
                suggestions=["Buy $500 of BTC", "Sell 0.5 ETH", "Buy $1,000 of SOL"],
            )

        clean = prompt.strip()
        if len(clean) > MAX_PROMPT_LENGTH:
            return InterpretationResult(
                success=False,
                error=f"Trade prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters.",
            )

        lower = clean.lower()

        # 1. Detect Negation
        for neg in NEGATION_WORDS:
            # Word boundary check
            if re.search(rf"\b{re.escape(neg)}\b", lower):
                return InterpretationResult(
                    success=False,
                    error="Negation or conditional cancellation detected. TradeGuard only executes explicit affirmative trade intents.",
                    suggestions=["State only the trade you want to execute (e.g., 'Sell $100 of ETH')."],
                )

        # 2. Detect Multi-Leg or Ambiguous Disjunctions
        for ml_pat in MULTI_LEG_PATTERNS:
            if re.search(ml_pat, lower):
                return InterpretationResult(
                    success=False,
                    error="Multi-leg, compound, or alternative trade requests cannot be safely processed in a single order.",
                    clarification="TradeGuard requires one single, unambiguous trade intent at a time for safety validation.",
                    suggestions=[
                        "Submit one trade first (e.g. 'Buy $500 of BTC'), then submit subsequent orders separately."
                    ],
                )

        # 3. Detect Side (BUY vs SELL)
        buy_matches = len(re.findall(r"\b(buy|purchase|acquire|long)\b", lower))
        sell_matches = len(re.findall(r"\b(sell|liquidate|short|dump)\b", lower))

        if buy_matches > 0 and sell_matches > 0:
            return InterpretationResult(
                success=False,
                error="Conflicting trade directions detected (both BUY and SELL found in prompt).",
                clarification="Please specify either a BUY or a SELL order, not both.",
                suggestions=["Buy $500 of BTC", "Sell 0.5 ETH"],
            )
        elif buy_matches > 0:
            side = OrderSide.BUY
        elif sell_matches > 0:
            side = OrderSide.SELL
        else:
            return InterpretationResult(
                success=False,
                error="Could not determine trade direction (BUY/SELL) from prompt.",
                clarification="Start with 'Buy' or 'Sell' to specify trade action.",
                suggestions=["Buy $500 of BTC", "Sell 0.5 ETH"],
            )

        # 4. Detect Target Asset from supported allowlist
        detected_assets: List[str] = []
        for symbol, aliases in ASSET_ALIASES.items():
            for alias in aliases:
                if re.search(rf"\b{re.escape(alias)}\b", lower):
                    if symbol not in detected_assets:
                        detected_assets.append(symbol)
                    break

        # Check for commonly known unsupported assets (e.g., DOGE, ADA, XRP)
        unsupported_mention = re.search(r"\b(doge|dogecoin|ada|cardano|xrp|ripple|pepe|shib|bnb)\b", lower)
        if unsupported_mention:
            unsupported_name = unsupported_mention.group(1).upper()
            return InterpretationResult(
                success=False,
                error=f"Asset '{unsupported_name}' is not supported. Supported assets are: {', '.join(settings.SUPPORTED_ASSETS)}.",
                suggestions=[f"Buy $500 of {s}" for s in settings.SUPPORTED_ASSETS if s != "USDC"],
            )

        if len(detected_assets) == 0:
            return InterpretationResult(
                success=False,
                error=f"No supported asset recognized in prompt. Supported assets: {', '.join(settings.SUPPORTED_ASSETS)}.",
                suggestions=["Buy $500 of BTC", "Buy $200 of ETH", "Buy $100 of SOL"],
            )
        elif len(detected_assets) > 1:
            return InterpretationResult(
                success=False,
                error=f"Multiple assets detected ({', '.join(detected_assets)}).",
                clarification="TradeGuard evaluates risk on one single asset per proposal.",
                suggestions=[f"{side.value.title()} $500 of {a}" for a in detected_assets],
            )

        asset = detected_assets[0]

        # 5. Scientific Notation / Extreme values rejection
        if re.search(r"[0-9]+[eE][+-]?[0-9]+", clean):
            return InterpretationResult(
                success=False,
                error="Scientific notation (e.g. 1e3) is not supported for trade quantities.",
                suggestions=["Use standard numeric notation like $1,000 or 0.05 BTC"],
            )

        # 6. Parse Amount and Currency/Asset Unit
        amount_res = self._extract_amount_and_type(clean, lower, asset)
        if not amount_res[0]:
            return InterpretationResult(
                success=False,
                error=amount_res[1],
                clarification=amount_res[2],
                suggestions=amount_res[3],
            )

        amount, amount_type = amount_res[0], amount_res[1]

        # Validation: finite positive number
        if math.isnan(amount) or math.isinf(amount) or amount <= 0:
            return InterpretationResult(
                success=False,
                error="Trade amount must be a finite positive number greater than zero.",
            )

        if amount > MAX_SAFE_AMOUNT:
            return InterpretationResult(
                success=False,
                error=f"Trade amount (${amount:,.2f}) exceeds maximum safety input ceiling of ${MAX_SAFE_AMOUNT:,.2f}.",
            )

        parsed_intent = ParsedIntent(
            asset=asset,
            side=side,
            amount=amount,
            amount_type=amount_type,
            raw_prompt=clean,
            interpreter_type="RULE_BASED",
        )

        return InterpretationResult(success=True, intent=parsed_intent)

    def _extract_amount_and_type(
        self, original: str, lower: str, asset: str
    ) -> Tuple[Optional[float], Optional[AmountType], Optional[str], List[str]]:
        """
        Carefully disambiguates:
          - Explicit USD: "$500", "$ 500.50", "500 usd", "500 usdc", "500 dollars"
          - Explicit Asset: "2 btc", "2 bitcoin", "0.5 of btc", "0.5 eth", "10 sol"
          - Ambiguous bare number: "buy 500 btc" vs "buy $500 of btc"
        Returns (amount, amount_type, error_or_clarification, suggestions)
        """
        asset_aliases = ASSET_ALIASES.get(asset, [asset.lower()])
        alias_pattern = "|".join(re.escape(a) for a in asset_aliases)

        # 1. Explicit USD match: "$500", "$ 1,200.50", "500 usd", "500 dollars", "500 usdc"
        usd_prefix = re.search(r"\$\s*([0-9,]+(?:\.[0-9]+)?)", original)
        usd_suffix = re.search(r"([0-9,]+(?:\.[0-9]+)?)\s*(?:usd|usdc|dollars|bucks)\b", lower)

        if usd_prefix:
            raw_val = usd_prefix.group(1).replace(",", "")
            try:
                val = float(raw_val)
                return val, AmountType.USD, None, []
            except ValueError:
                pass

        if usd_suffix:
            raw_val = usd_suffix.group(1).replace(",", "")
            try:
                val = float(raw_val)
                return val, AmountType.USD, None, []
            except ValueError:
                pass

        # 2. Explicit Asset Quantity match:
        # e.g., "2 bitcoin", "2 btc", "0.5 of btc", "0.5 of bitcoin", "1.5 eth", "10 solana"
        asset_qty_match = re.search(
            rf"([0-9,]+(?:\.[0-9]+)?)\s*(?:of\s+)?(?:{alias_pattern}|tokens|coins|shares)\b",
            lower,
        )
        if asset_qty_match:
            raw_val = asset_qty_match.group(1).replace(",", "")
            try:
                val = float(raw_val)
                return val, AmountType.ASSET, None, []
            except ValueError:
                pass

        # 3. Check for bare number before or after asset without explicit currency symbol
        # e.g., "buy btc 500" or "buy 500 btc" (where the alias was matched)
        # If user wrote "buy 500 btc", step 2 should match if alias was right after number.
        # But if user wrote "buy $500 of btc", step 1 matched.
        # What if user wrote "buy 500 of btc" or "buy btc for 500"?
        bare_of_match = re.search(rf"([0-9,]+(?:\.[0-9]+)?)\s*(?:worth\s+of|worth|of)\s*(?:{alias_pattern})\b", lower)
        if bare_of_match:
            # "500 worth of btc" implies currency value
            raw_val = bare_of_match.group(1).replace(",", "")
            try:
                val = float(raw_val)
                return val, AmountType.USD, None, []
            except ValueError:
                pass

        # Any standalone number in the prompt
        all_numbers = re.findall(r"([0-9,]+(?:\.[0-9]+)?)", clean_str := re.sub(r"\b(?:btc|eth|sol|usdc)\b", "", lower))
        if len(all_numbers) == 1:
            raw_val = all_numbers[0].replace(",", "")
            try:
                val = float(raw_val)
                # If the value is a whole number >= 50 for BTC or ETH, likely intended USD, but ambiguous!
                # If ambiguous, return clarification rather than guessing!
                if val >= 100:
                    clarification = f"I understood you want to trade {asset}, but the unit is ambiguous. Did you mean ${val:,.0f} USD or {val:,.4f} {asset}?"
                    suggestions = [f"Buy ${val:,.0f} of {asset}", f"Buy {val:g} {asset}"]
                    return None, None, clarification, suggestions
                else:
                    # Smaller numbers like 0.5, 2, 10 could be tokens
                    clarification = f"Specify whether {val:g} is a USD notional amount (${val:g}) or asset quantity ({val:g} {asset})."
                    suggestions = [f"Buy ${val:g} of {asset}", f"Buy {val:g} {asset}"]
                    return None, None, clarification, suggestions
            except ValueError:
                pass

        return None, None, "Could not extract a valid trade amount and unit from your request.", [
            f"Buy $500 of {asset}",
            f"Buy 0.1 {asset}",
        ]
