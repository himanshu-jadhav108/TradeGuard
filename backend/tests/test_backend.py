import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.intent_service import IntentService
from app.domain.models import OrderSide, AmountType, RiskLevel
from app.services.quote_service import QuoteService
from app.services.risk_engine import RiskEngine

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "BTC" in data["supported_assets"]


def test_intent_parsing_buy_usd():
    intent = IntentService.parse_natural_language("Buy $500 of BTC")
    assert intent.asset == "BTC"
    assert intent.side == OrderSide.BUY
    assert intent.amount == 500.0
    assert intent.amount_type == AmountType.USD


def test_intent_parsing_sell_asset():
    intent = IntentService.parse_natural_language("Sell 1.5 ETH")
    assert intent.asset == "ETH"
    assert intent.side == OrderSide.SELL
    assert intent.amount == 1.5
    assert intent.amount_type == AmountType.ASSET


def test_intent_parsing_unsupported_asset():
    with pytest.raises(Exception):
        IntentService.parse_natural_language("Buy $200 of DOGE")


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


def test_risk_engine_block_max_notional():
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


def test_e2e_proposal_and_confirm_flow():
    # 1. Reset demo database
    client.post("/api/system/reset-demo")

    # 2. Request proposal for "Buy $500 of BTC"
    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $500 of BTC"})
    assert res_prop.status_code == 200
    prop_data = res_prop.json()
    assert prop_data["asset"] == "BTC"
    assert prop_data["estimated_notional_usd"] == 500.0
    assert prop_data["requires_confirmation"] is True
    proposal_id = prop_data["id"]

    # 3. Explicit human confirmation
    res_confirm = client.post(f"/api/trades/{proposal_id}/confirm")
    assert res_confirm.status_code == 200
    order_data = res_confirm.json()
    assert order_data["status"] == "FILLED"
    assert order_data["proposal_id"] == proposal_id
    assert order_data["mode"] == "DEMO"

    # 4. Check portfolio updated
    res_port = client.get("/api/portfolio")
    assert res_port.status_code == 200
    port_data = res_port.json()
    assert port_data["cash_usd"] == 9500.0  # 10000 - 500

    # 5. Check activity has audit events
    res_act = client.get("/api/activity")
    assert res_act.status_code == 200
    events = res_act.json()
    assert len(events) >= 3
    event_types = [e["event_type"] for e in events]
    assert "PROPOSAL_CREATED" in event_types
    assert "TRADE_CONFIRMED" in event_types
    assert "ORDER_FILLED" in event_types
