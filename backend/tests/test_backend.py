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
    quote = QuoteService.get_demo_quote("BTC")
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
    quote = QuoteService.get_demo_quote("BTC")
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
    quote = QuoteService.get_demo_quote("BTC")
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
    quote = QuoteService.get_demo_quote("BTC")
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


def test_true_markets_client_auth_url_normalization():
    from app.services.true_markets_client import TrueMarketsClient

    # With standard gateway URL containing /v1/gateway
    tm1 = TrueMarketsClient(base_url="https://api.uat.truemarkets.co/v1/gateway")
    assert tm1._get_auth_url() == "https://api.uat.truemarkets.co/v1/auth/api-key/token"

    # With base domain without trailing segment
    tm2 = TrueMarketsClient(base_url="https://api.uat.truemarkets.co")
    assert tm2._get_auth_url() == "https://api.uat.truemarkets.co/v1/auth/api-key/token"

    # With /gateway base
    tm3 = TrueMarketsClient(base_url="https://api.uat.truemarkets.co/gateway")
    assert tm3._get_auth_url() == "https://api.uat.truemarkets.co/v1/auth/api-key/token"


def test_true_markets_client_signer_key_resolution(tmp_path):
    from app.services.true_markets_client import TrueMarketsClient

    # Direct signer key
    tm_direct = TrueMarketsClient(signer_key="secret-key-123")
    assert tm_direct.get_signer_key() == "secret-key-123"

    # File path signer key
    key_file = tmp_path / "signer.key"
    key_file.write_text("file-secret-key-456")
    tm_file = TrueMarketsClient(signer_key_path=str(key_file))
    assert tm_file.get_signer_key() == "file-secret-key-456"

    # Non-existent file path
    tm_none = TrueMarketsClient(signer_key_path=str(tmp_path / "missing.key"))
    assert tm_none.get_signer_key() is None


async def test_uat_quote_success_gateway_tagged(monkeypatch):
    from app.core.config import settings
    from app.services.quote_service import QuoteService
    from app.services.true_markets_client import TrueMarketsClient

    monkeypatch.setattr(settings, "TM_ENV", "uat")
    monkeypatch.setattr(settings, "TM_API_KEY", "mock-key")
    monkeypatch.setattr(settings, "TM_ORGANIZATION_USER_ID", "mock-org-user")

    async def mock_get_quote(self, pair, side, amount, user_id="demo-user-1"):
        return {
            "pair": "BTC/USDC",
            "bid": 86100.0,
            "ask": 86200.0,
            "mid": 86150.0,
            "quote_id": "gw-quote-789",
            "expires_at": "2026-10-11T12:00:00Z",
            "timestamp": "2026-10-11T11:59:30Z",
        }

    monkeypatch.setattr(TrueMarketsClient, "get_quote", mock_get_quote)

    quote = await QuoteService.get_quote("BTC")
    assert quote.source == "TRUE_MARKETS_UAT"
    assert quote.quote_id == "gw-quote-789"
    assert quote.bid == 86100.0
    assert quote.ask == 86200.0
    assert quote.mid == 86150.0


async def test_uat_quote_error_raises_and_never_tags_static_price_as_uat(monkeypatch):
    from app.core.config import settings
    from app.services.quote_service import QuoteService
    from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError

    monkeypatch.setattr(settings, "TM_ENV", "uat")
    monkeypatch.setattr(settings, "TM_API_KEY", "mock-key")
    monkeypatch.setattr(settings, "TM_ORGANIZATION_USER_ID", "mock-org-user")

    async def mock_get_quote_error(self, pair, side, amount, user_id="demo-user-1"):
        raise TrueMarketsClientError("Upstream gateway 500 error", status_code=500, error_code="GATEWAY_ERROR")

    monkeypatch.setattr(TrueMarketsClient, "get_quote", mock_get_quote_error)

    with pytest.raises(TrueMarketsClientError):
        await QuoteService.get_quote("BTC")


async def test_uat_quote_timeout_raises_and_never_tags_static_price_as_uat(monkeypatch):
    from app.core.config import settings
    from app.services.quote_service import QuoteService
    from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError

    monkeypatch.setattr(settings, "TM_ENV", "uat")
    monkeypatch.setattr(settings, "TM_API_KEY", "mock-key")
    monkeypatch.setattr(settings, "TM_ORGANIZATION_USER_ID", "mock-org-user")

    async def mock_get_quote_timeout(self, pair, side, amount, user_id="demo-user-1"):
        raise TrueMarketsClientError("Gateway quote timeout", status_code=504, error_code="GATEWAY_TIMEOUT")

    monkeypatch.setattr(TrueMarketsClient, "get_quote", mock_get_quote_timeout)

    with pytest.raises(TrueMarketsClientError) as exc_info:
        await QuoteService.get_quote("BTC")
    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "GATEWAY_TIMEOUT"


def test_demo_mode_never_tags_static_price_as_uat(monkeypatch):
    from app.core.config import settings
    from app.services.quote_service import QuoteService

    # Even if TM_ENV is uat, without credentials it must return DEMO_SIMULATOR
    monkeypatch.setattr(settings, "TM_ENV", "uat")
    monkeypatch.setattr(settings, "TM_API_KEY", None)
    monkeypatch.setattr(settings, "TM_ORGANIZATION_USER_ID", None)

    import asyncio
    quote = asyncio.run(QuoteService.get_quote("BTC"))
    assert quote.source == "DEMO_SIMULATOR"
    assert quote.quote_id is None

    # In DEMO mode, strictly DEMO_SIMULATOR
    monkeypatch.setattr(settings, "TM_ENV", "demo")
    quote_demo = asyncio.run(QuoteService.get_quote("ETH"))
    assert quote_demo.source == "DEMO_SIMULATOR"
    assert quote_demo.quote_id is None


async def test_uat_order_passes_quote_id_and_never_uses_mid_as_fill_price(monkeypatch):
    from app.core.config import settings
    from app.domain.models import QuoteSnapshot, RiskResult, PortfolioImpact, OrderSide, AmountType, TradeProposal, TradeConfirmRequest
    from app.services.order_service import OrderService
    from app.services.true_markets_client import TrueMarketsClient
    from app.db.store import Storage

    monkeypatch.setattr(settings, "TM_ENV", "uat")
    monkeypatch.setattr(settings, "TM_API_KEY", "mock-key")
    monkeypatch.setattr(settings, "TM_ORGANIZATION_USER_ID", "mock-org-user")

    captured_create = {}

    async def mock_create_order(self, pair, side, quantity, quote_id=None, user_id="demo-user-1"):
        captured_create["pair"] = pair
        captured_create["quote_id"] = quote_id
        return {"id": "gw-order-999", "status": "PENDING"}

    async def mock_execute_order(self, order_id, signature=None, user_id="demo-user-1"):
        # Returns SUBMITTED status without fill price
        return {"id": order_id, "status": "SUBMITTED"}

    monkeypatch.setattr(TrueMarketsClient, "create_order", mock_create_order)
    monkeypatch.setattr(TrueMarketsClient, "execute_order", mock_execute_order)

    user_id = "test-uat-quote-id-user"
    Storage.reset_session(user_id)

    quote = QuoteSnapshot(
        pair="BTC/USDC",
        base_asset="BTC",
        quote_asset="USDC",
        bid=86000.0,
        ask=86100.0,
        mid=86050.0,
        spread_pct=0.116,
        timestamp="2026-10-11T12:00:00Z",
        expires_at="2026-10-11T12:05:00Z",
        source="TRUE_MARKETS_UAT",
        quote_id="gw-quote-captured-123",
    )

    prop = TradeProposal(
        id="prop-test-uat-1",
        user_id=user_id,
        asset="BTC",
        side=OrderSide.BUY,
        request_amount=100.0,
        request_amount_type=AmountType.USD,
        estimated_qty=0.00116,
        estimated_notional_usd=100.0,
        quote=quote,
        risk=RiskResult(overall_status="PASS", can_execute=True, checks=[]),
        portfolio_impact=PortfolioImpact(
            asset="BTC", current_qty=0.0, current_value_usd=0.0, current_allocation_pct=0.0,
            projected_qty=0.00116, projected_value_usd=100.0, projected_allocation_pct=1.0,
            cash_before_usd=10000.0, cash_after_usd=9900.0,
            total_portfolio_value_before=10000.0, total_portfolio_value_after=10000.0,
        ),
        explanation="Testing UAT quote id forwarding",
        created_at="2026-10-11T12:00:00Z",
        expires_at="2026-10-11T12:05:00Z",
        status="PENDING_CONFIRMATION",
    )
    Storage.save_proposal(prop)

    order = await OrderService.confirm_proposal(
        proposal_id=prop.id,
        confirm_req=TradeConfirmRequest(proposal_id=prop.id),
        user_id=user_id,
    )

    # 1. quote_id was passed to create_order
    assert captured_create["quote_id"] == "gw-quote-captured-123"
    # 2. Never use quote mid as a fill price: SUBMITTED status must have fill_price None
    assert order.status.value == "SUBMITTED"
    assert order.fill_price is None
    assert order.fill_price != quote.mid


# ==========================================
# 7. Atomic Execution & State Integrity (P0-4)
# ==========================================

def test_forced_failure_after_fill_cannot_double_fill():
    session = "test-atomic-fill-double"
    headers = {"X-Session-ID": session}
    client.post("/api/session/reset", headers=headers)

    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $500 of SOL"}, headers=headers)
    assert res_prop.status_code == 200
    prop_id = res_prop.json()["id"]

    # Initial confirmation: succeeds
    res_first = client.post(f"/api/trades/{prop_id}/confirm", json={"proposal_id": prop_id}, headers=headers)
    assert res_first.status_code == 200
    assert res_first.json()["status"] == "FILLED"

    port_after_first = client.get("/api/portfolio", headers=headers).json()
    assert port_after_first["cash_usd"] == 9500.0

    # Forced double fill attempt: must return 409
    res_second = client.post(f"/api/trades/{prop_id}/confirm", json={"proposal_id": prop_id}, headers=headers)
    assert res_second.status_code == 409
    assert "Double confirmation is prevented" in res_second.json()["detail"] or "already been processed" in res_second.json()["detail"]

    # Balances must be strictly unchanged (only filled once)
    port_after_second = client.get("/api/portfolio", headers=headers).json()
    assert port_after_second["cash_usd"] == 9500.0


def test_cancel_during_confirming_returns_409():
    session = "test-cancel-race"
    headers = {"X-Session-ID": session}
    client.post("/api/session/reset", headers=headers)

    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $500 of SOL"}, headers=headers)
    assert res_prop.status_code == 200
    prop_id = res_prop.json()["id"]

    # Transition to CONFIRMING directly in store
    claimed = Storage.claim_proposal_for_confirmation(prop_id, user_id=session)
    assert claimed is True

    # Cancel while CONFIRMING must return 409 Conflict
    res_cancel = client.post(f"/api/trades/{prop_id}/cancel", headers=headers)
    assert res_cancel.status_code == 409
    assert "CONFIRMING" in res_cancel.json()["detail"]
    assert "PENDING_CONFIRMATION" in res_cancel.json()["detail"]


def test_cancel_only_allowed_from_pending_confirmation():
    session = "test-cancel-state-rules"
    headers = {"X-Session-ID": session}
    client.post("/api/session/reset", headers=headers)

    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $500 of SOL"}, headers=headers)
    assert res_prop.status_code == 200
    prop_id = res_prop.json()["id"]

    # First cancel from PENDING_CONFIRMATION: succeeds with 200
    res_cancel_1 = client.post(f"/api/trades/{prop_id}/cancel", headers=headers)
    assert res_cancel_1.status_code == 200
    assert res_cancel_1.json()["status"] == "CANCELLED"

    # Second cancel from CANCELLED: must return 409 Conflict
    res_cancel_2 = client.post(f"/api/trades/{prop_id}/cancel", headers=headers)
    assert res_cancel_2.status_code == 409
    assert "CANCELLED" in res_cancel_2.json()["detail"]


async def test_uat_execute_failure_marks_order_failed_and_locks_proposal(monkeypatch):
    from app.core.config import settings
    from app.domain.models import QuoteSnapshot, RiskResult, PortfolioImpact, OrderSide, AmountType, TradeProposal, TradeConfirmRequest, OrderStatus
    from app.services.order_service import OrderService
    from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError
    from app.db.store import Storage

    monkeypatch.setattr(settings, "TM_ENV", "uat")
    monkeypatch.setattr(settings, "TM_API_KEY", "mock-key")
    monkeypatch.setattr(settings, "TM_ORGANIZATION_USER_ID", "mock-org-user")

    async def mock_create_order(self, pair, side, quantity, quote_id=None, user_id="demo-user-1"):
        return {"id": "gw-order-fail-test", "status": "PENDING"}

    async def mock_execute_order(self, order_id, signature=None, user_id="demo-user-1"):
        raise TrueMarketsClientError("Execution gateway rejection", status_code=500)

    monkeypatch.setattr(TrueMarketsClient, "create_order", mock_create_order)
    monkeypatch.setattr(TrueMarketsClient, "execute_order", mock_execute_order)

    user_id = "test-uat-fail-lock-user"
    Storage.reset_session(user_id)

    quote = QuoteSnapshot(
        pair="BTC/USDC",
        base_asset="BTC",
        quote_asset="USDC",
        bid=86000.0,
        ask=86100.0,
        mid=86050.0,
        spread_pct=0.116,
        timestamp="2026-10-11T12:00:00Z",
        expires_at="2026-10-11T12:05:00Z",
        source="TRUE_MARKETS_UAT",
        quote_id="gw-q-1",
    )

    prop = TradeProposal(
        id="prop-test-uat-fail-1",
        user_id=user_id,
        asset="BTC",
        side=OrderSide.BUY,
        request_amount=100.0,
        request_amount_type=AmountType.USD,
        estimated_qty=0.00116,
        estimated_notional_usd=100.0,
        quote=quote,
        risk=RiskResult(overall_status="PASS", can_execute=True, checks=[]),
        portfolio_impact=PortfolioImpact(
            asset="BTC", current_qty=0.0, current_value_usd=0.0, current_allocation_pct=0.0,
            projected_qty=0.00116, projected_value_usd=100.0, projected_allocation_pct=1.0,
            cash_before_usd=10000.0, cash_after_usd=9900.0,
            total_portfolio_value_before=10000.0, total_portfolio_value_after=10000.0,
        ),
        explanation="Testing UAT failure",
        created_at="2026-10-11T12:00:00Z",
        expires_at="2026-10-11T12:05:00Z",
        status="PENDING_CONFIRMATION",
    )
    Storage.save_proposal(prop)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await OrderService.confirm_proposal(
            proposal_id=prop.id,
            confirm_req=TradeConfirmRequest(proposal_id=prop.id),
            user_id=user_id,
        )
    assert exc_info.value.status_code == 500 or exc_info.value.status_code == 502
    assert "Order marked FAILED" in exc_info.value.detail

    # Verify proposal status is FAILED and cannot be released or confirmed again
    p_check = Storage.get_proposal(prop.id, user_id=user_id)
    assert p_check.status == "FAILED"

    # Verify order was persisted and marked FAILED
    orders = client.get("/api/activity", headers={"X-Session-ID": user_id}).json()
    order_fail_event = next(e for e in orders if e["event_type"] == "ORDER_FAILED")
    assert order_fail_event["metadata"]["external_id"] == "gw-order-fail-test"
