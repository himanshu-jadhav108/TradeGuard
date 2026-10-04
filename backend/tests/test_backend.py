import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.intent_service import IntentService
from app.domain.models import OrderSide, AmountType, RiskLevel, TradeConfirmRequest
from app.services.quote_service import QuoteService
from app.services.risk_engine import RiskEngine
from app.db.store import Storage

client = TestClient(app)


# ==========================================
# 1. Intent Parsing & Adversarial Tests
# ==========================================

def test_intent_parsing_buy_usd():
    intent = IntentService.parse_natural_language("Buy $500 of BTC")
    assert intent.asset == "BTC"
    assert intent.side == OrderSide.BUY
    assert intent.amount == 500.0
    assert intent.amount_type == AmountType.USD
    assert intent.interpreter_type == "RULE_BASED"


def test_intent_parsing_buy_asset_quantity():
    # Tests "Buy 2 bitcoin" which was previously misparsed as $2 USD
    intent = IntentService.parse_natural_language("Buy 2 bitcoin")
    assert intent.asset == "BTC"
    assert intent.side == OrderSide.BUY
    assert intent.amount == 2.0
    assert intent.amount_type == AmountType.ASSET


def test_intent_parsing_fractional_asset():
    intent = IntentService.parse_natural_language("Buy 0.5 of BTC")
    assert intent.asset == "BTC"
    assert intent.side == OrderSide.BUY
    assert intent.amount == 0.5
    assert intent.amount_type == AmountType.ASSET


def test_intent_parsing_sell_asset():
    intent = IntentService.parse_natural_language("Sell 1.5 ETH")
    assert intent.asset == "ETH"
    assert intent.side == OrderSide.SELL
    assert intent.amount == 1.5
    assert intent.amount_type == AmountType.ASSET


def test_intent_rejection_negation():
    # Rejects "Don't buy BTC, sell $100 of ETH"
    res = IntentService.parse_with_clarification("Don't buy BTC, sell $100 of ETH")
    assert res.success is False
    assert "Negation" in (res.error or "")


def test_intent_rejection_multi_leg():
    # Rejects compound/alternative intents
    res = IntentService.parse_with_clarification("Buy $500 BTC and sell $200 ETH")
    assert res.success is False
    assert "Multi-leg" in (res.error or "")

    res2 = IntentService.parse_with_clarification("Buy $500 of ETH or BTC")
    assert res2.success is False


def test_intent_rejection_scientific_notation():
    # Rejects "Buy $1e3 of BTC"
    res = IntentService.parse_with_clarification("Buy $1e3 of BTC")
    assert res.success is False
    assert "Scientific notation" in (res.error or "")


def test_intent_rejection_unsupported_asset():
    res = IntentService.parse_with_clarification("Buy $200 of DOGE")
    assert res.success is False
    assert "DOGE" in (res.error or "")


def test_intent_ambiguous_bare_number_clarification():
    # Bare number like "Buy 500 BTC" or "Buy 500"
    res = IntentService.parse_with_clarification("Buy 500")
    assert res.success is False
    assert res.clarification is not None or res.error is not None


def test_intent_oversized_prompt_rejection():
    oversized = "Buy $500 of BTC " + ("extra text " * 50)
    res = IntentService.parse_with_clarification(oversized)
    assert res.success is False
    assert "maximum length" in (res.error or "")


# ==========================================
# 2. Risk Engine Deterministic Boundary Tests
# ==========================================

def test_risk_engine_pass():
    quote = QuoteService.get_quote("BTC")
    risk_result, impact, qty, notional = RiskEngine.evaluate_trade(
        asset="BTC",
        side=OrderSide.BUY,
        request_amount=500.0,
        request_amount_type=AmountType.USD,
        quote=quote,
        cash_usd=10000.0,
        current_positions={"BTC": 0.05},
    )
    assert risk_result.can_execute is True
    assert risk_result.overall_status == RiskLevel.PASS
    assert notional == 500.0
    assert qty > 0


def test_risk_engine_block_insufficient_cash():
    quote = QuoteService.get_quote("BTC")
    risk_result, impact, qty, notional = RiskEngine.evaluate_trade(
        asset="BTC",
        side=OrderSide.BUY,
        request_amount=15000.0,
        request_amount_type=AmountType.USD,
        quote=quote,
        cash_usd=1000.0,
        current_positions={"BTC": 0.05},
    )
    assert risk_result.can_execute is False
    assert risk_result.overall_status == RiskLevel.BLOCK
    balance_check = next(c for c in risk_result.checks if c.name == "Balance Sufficiency")
    assert balance_check.status == RiskLevel.BLOCK
    assert risk_result.suggested_safe_amount_usd == 1000.0


def test_risk_engine_block_max_notional_ceiling():
    quote = QuoteService.get_quote("BTC")
    risk_result, _, _, _ = RiskEngine.evaluate_trade(
        asset="BTC",
        side=OrderSide.BUY,
        request_amount=30000.0,
        request_amount_type=AmountType.USD,
        quote=quote,
        cash_usd=50000.0,
        current_positions={},
    )
    assert risk_result.can_execute is False
    assert risk_result.overall_status == RiskLevel.BLOCK
    limit_check = next(c for c in risk_result.checks if c.name == "Maximum Notional Limit")
    assert limit_check.status == RiskLevel.BLOCK
    assert risk_result.suggested_safe_amount_usd == 25000.0


def test_risk_engine_concentration_warning():
    quote = QuoteService.get_quote("BTC")
    # Portfolio: cash $10,000, 0.15 BTC ($12,967). Buying $5,000 BTC raises BTC to ~58% (>40%)
    risk_result, impact, _, _ = RiskEngine.evaluate_trade(
        asset="BTC",
        side=OrderSide.BUY,
        request_amount=5000.0,
        request_amount_type=AmountType.USD,
        quote=quote,
        cash_usd=10000.0,
        current_positions={"BTC": 0.15},
    )
    assert risk_result.can_execute is True
    assert risk_result.overall_status == RiskLevel.WARN
    assert risk_result.warn_requires_ack is True
    conc_check = next(c for c in risk_result.checks if c.name == "Portfolio Concentration")
    assert conc_check.status == RiskLevel.WARN


# ==========================================
# 3. Two-Phase Execution & State Machine
# ==========================================

def test_e2e_proposal_confirm_and_double_confirm_prevention():
    session = "test-session-atomic-1"
    headers = {"X-Session-ID": session}

    # 1. Reset demo database for session
    res_reset = client.post("/api/session/reset", headers=headers)
    assert res_reset.status_code == 200

    # 2. Request proposal for "Buy $500 of SOL" (clean PASS within 40% limit)
    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $500 of SOL"}, headers=headers)
    assert res_prop.status_code == 200
    prop_data = res_prop.json()
    assert prop_data["asset"] == "SOL"
    assert prop_data["risk"]["overall_status"] == "PASS"
    assert prop_data["estimated_notional_usd"] == 500.0
    assert prop_data["requires_confirmation"] is True
    assert prop_data["raw_prompt"] == "Buy $500 of SOL"
    proposal_id = prop_data["id"]

    # 3. Explicit human confirmation
    res_confirm = client.post(
        f"/api/trades/{proposal_id}/confirm",
        json={"proposal_id": proposal_id, "acknowledged_warnings": False},
        headers=headers,
    )
    assert res_confirm.status_code == 200
    order_data = res_confirm.json()
    assert order_data["status"] == "FILLED"
    assert order_data["proposal_id"] == proposal_id
    assert order_data["mode"] == "DEMO"

    # 4. Immediate Double Confirmation Attempt must be rejected with 409 Conflict
    res_double = client.post(
        f"/api/trades/{proposal_id}/confirm",
        json={"proposal_id": proposal_id, "acknowledged_warnings": False},
        headers=headers,
    )
    assert res_double.status_code == 409
    assert "already been processed" in res_double.json()["detail"]


def test_warn_requires_explicit_acknowledgement():
    session = "test-session-warn-ack"
    headers = {"X-Session-ID": session}
    client.post("/api/session/reset", headers=headers)

    # Create proposal that triggers concentration warning
    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $5,000 of BTC"}, headers=headers)
    assert res_prop.status_code == 200
    prop = res_prop.json()
    assert prop["risk"]["overall_status"] == "WARN"

    # Attempt confirm without acknowledging warning
    res_fail = client.post(
        f"/api/trades/{prop['id']}/confirm",
        json={"proposal_id": prop["id"], "acknowledged_warnings": False},
        headers=headers,
    )
    assert res_fail.status_code == 400
    assert "requires explicit acknowledgement" in res_fail.json()["detail"]

    # Attempt confirm WITH acknowledgement
    res_ok = client.post(
        f"/api/trades/{prop['id']}/confirm",
        json={"proposal_id": prop["id"], "acknowledged_warnings": True},
        headers=headers,
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "FILLED"


def test_block_cannot_execute():
    session = "test-session-block-deny"
    headers = {"X-Session-ID": session}
    client.post("/api/session/reset", headers=headers)

    # Buy $30,000 exceeds ceiling of $25,000 -> BLOCK
    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $30,000 of BTC"}, headers=headers)
    assert res_prop.status_code == 200
    prop = res_prop.json()
    assert prop["risk"]["overall_status"] == "BLOCK"

    res_confirm = client.post(
        f"/api/trades/{prop['id']}/confirm",
        json={"proposal_id": prop["id"], "acknowledged_warnings": True},
        headers=headers,
    )
    assert res_confirm.status_code == 400
    assert "Execution blocked" in res_confirm.json()["detail"]


# ==========================================
# 4. Per-Visitor Session Isolation Tests
# ==========================================

def test_session_isolation_and_scoped_reset():
    session_a = "user-alice-1234"
    session_b = "user-bob-5678"

    # Reset both
    client.post("/api/session/reset", headers={"X-Session-ID": session_a})
    client.post("/api/session/reset", headers={"X-Session-ID": session_b})

    # Alice buys $1,000 of SOL
    res_a = client.post("/api/trades/proposals", json={"prompt": "Buy $1,000 of SOL"}, headers={"X-Session-ID": session_a})
    prop_a = res_a.json()
    client.post(f"/api/trades/{prop_a['id']}/confirm", json={"proposal_id": prop_a["id"]}, headers={"X-Session-ID": session_a})

    # Verify Alice cash decreased to $9,000
    port_a = client.get("/api/portfolio", headers={"X-Session-ID": session_a}).json()
    assert port_a["cash_usd"] == 9000.0

    # Verify Bob cash is UNTOUCHED at $10,000
    port_b = client.get("/api/portfolio", headers={"X-Session-ID": session_b}).json()
    assert port_b["cash_usd"] == 10000.0

    # Alice resets her session
    client.post("/api/session/reset", headers={"X-Session-ID": session_a})
    port_a_reset = client.get("/api/portfolio", headers={"X-Session-ID": session_a}).json()
    assert port_a_reset["cash_usd"] == 10000.0

    # Bob is still intact
    port_b_check = client.get("/api/portfolio", headers={"X-Session-ID": session_b}).json()
    assert port_b_check["cash_usd"] == 10000.0


# ==========================================
# 5. Security: Destructive GET Reset Disabled
# ==========================================

def test_get_reset_disallowed():
    # GET reset must return 405 Method Not Allowed
    res = client.get("/api/session/reset")
    assert res.status_code == 405


# ==========================================
# 6. True Markets Adapter Isolation Tests
# ==========================================

def test_true_markets_client_unconfigured_safety():
    from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError
    tm = TrueMarketsClient(api_key=None, org_user_id=None)
    assert tm.is_configured() is False

    # Calling quote without credentials raises expected TrueMarketsClientError
    with pytest.raises(TrueMarketsClientError) as exc_info:
        import asyncio
        asyncio.run(tm.get_quote("BTC/USDC", "BUY", 500.0))
    assert "credentials not configured" in str(exc_info.value)
