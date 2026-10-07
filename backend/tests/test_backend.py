import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.services.intent_service import IntentService
from app.domain.models import OrderSide, AmountType, RiskLevel, TradeConfirmRequest, TradeProposalCreateRequest
from app.services.quote_service import QuoteService
from app.services.risk_engine import RiskEngine
from app.services.proposal_service import ProposalService
from app.services.order_service import OrderService
from app.db.store import Storage, get_db

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


# ---------------------------------------------------------------------------
# P1-1 Audit Completeness and Safety Signals Tests
# ---------------------------------------------------------------------------


def test_audit_intent_parsed_and_rejected():
    user_id = f"test-audit-intent-{uuid.uuid4().hex[:6]}"

    # 1. Valid intent
    res_valid = client.post("/api/intent/parse", json={"prompt": "Buy $200 of BTC"}, headers={"X-Session-ID": user_id})
    assert res_valid.status_code == 200
    assert res_valid.json()["success"] is True

    # 2. Rejected intent (negation)
    res_neg = client.post("/api/intent/parse", json={"prompt": "Don't buy ETH"}, headers={"X-Session-ID": user_id})
    assert res_neg.status_code == 200
    assert res_neg.json()["success"] is False

    # Check activity
    events = client.get("/api/activity", headers={"X-Session-ID": user_id}).json()
    event_types = [e["event_type"] for e in events]
    assert "INTENT_PARSED" in event_types
    assert "INTENT_REJECTED" in event_types

    # Verify monotonic seq and is_recorded
    seqs = [e["seq"] for e in events if e.get("seq") is not None]
    assert len(seqs) >= 2
    # Since events are returned ORDER BY seq DESC:
    assert seqs[0] > seqs[1]
    assert all(e.get("is_recorded") is True for e in events)


@pytest.mark.asyncio
async def test_audit_risk_evaluated_warning_ack_and_rejections():
    user_id = f"test-audit-lifecycle-{uuid.uuid4().hex[:6]}"

    # 1. Staged proposal produces RISK_EVALUATED
    prop = await ProposalService.create_proposal(
        TradeProposalCreateRequest(asset="SOL", side=OrderSide.BUY, amount=100.0, amount_type=AmountType.USD),
        user_id=user_id,
    )
    events = client.get("/api/activity", headers={"X-Session-ID": user_id}).json()
    risk_event = next(e for e in events if e["event_type"] == "RISK_EVALUATED")
    assert risk_event["proposal_id"] == prop.id
    assert "checks" in risk_event["metadata"]
    assert "thresholds" in risk_event["metadata"]

    # 2. Test cancel produces TRADE_CANCELLED
    client.post(f"/api/trades/{prop.id}/cancel", headers={"X-Session-ID": user_id})
    events = client.get("/api/activity", headers={"X-Session-ID": user_id}).json()
    assert any(e["event_type"] == "TRADE_CANCELLED" and e["proposal_id"] == prop.id for e in events)

    # 3. Test blocked proposal confirmation produces CONFIRM_REJECTED
    prop_blocked = await ProposalService.create_proposal(
        TradeProposalCreateRequest(asset="BTC", side=OrderSide.BUY, amount=30000.0, amount_type=AmountType.USD),
        user_id=user_id,
    )
    with pytest.raises(Exception):
        await OrderService.confirm_proposal(prop_blocked.id, TradeConfirmRequest(proposal_id=prop_blocked.id), user_id=user_id)

    events = client.get("/api/activity", headers={"X-Session-ID": user_id}).json()
    reject_event = next(e for e in events if e["event_type"] == "CONFIRM_REJECTED" and e["proposal_id"] == prop_blocked.id)
    assert reject_event["metadata"]["reason"] == "RISK_BLOCKED"

    # 4. Test expired quote confirmation produces PROPOSAL_EXPIRED
    prop_stale = await ProposalService.create_proposal(
        TradeProposalCreateRequest(asset="ETH", side=OrderSide.BUY, amount=100.0, amount_type=AmountType.USD),
        user_id=user_id,
    )
    # Force quote timestamp to past
    with get_db() as conn:
        conn.execute("UPDATE trade_proposals SET quote_snapshot = json_set(quote_snapshot, '$.timestamp', '2020-01-01T00:00:00Z', '$.expires_at', '2020-01-01T00:00:30Z') WHERE id = ?", (prop_stale.id,))

    with pytest.raises(Exception):
        await OrderService.confirm_proposal(prop_stale.id, TradeConfirmRequest(proposal_id=prop_stale.id), user_id=user_id)

    events = client.get("/api/activity", headers={"X-Session-ID": user_id}).json()
    assert any(e["event_type"] == "PROPOSAL_EXPIRED" and e["proposal_id"] == prop_stale.id for e in events)


@pytest.mark.asyncio
async def test_safety_signals_computation_and_endpoint():
    user_id = f"test-safety-signals-{uuid.uuid4().hex[:6]}"

    # Create two duplicate proposals in short window
    prop1 = await ProposalService.create_proposal(
        TradeProposalCreateRequest(asset="ETH", side=OrderSide.BUY, amount=50.0, amount_type=AmountType.USD),
        user_id=user_id,
    )
    prop2 = await ProposalService.create_proposal(
        TradeProposalCreateRequest(asset="ETH", side=OrderSide.BUY, amount=50.0, amount_type=AmountType.USD),
        user_id=user_id,
    )

    # Call /api/safety-signals
    res = client.get("/api/safety-signals", headers={"X-Session-ID": user_id})
    assert res.status_code == 200
    data = res.json()
    assert data["label"] == "rule-based safety signals"
    assert data["session_id"] == user_id

    signals_by_id = {s["id"]: s for s in data["signals"]}
    assert "sig-duplicates" in signals_by_id
    assert "sig-rate" in signals_by_id
    assert "sig-rejected-confirms" in signals_by_id
    assert "sig-expired-quotes" in signals_by_id

    # The 2nd proposal should be detected as a duplicate of the 1st
    assert signals_by_id["sig-duplicates"]["count"] >= 1
    # Both proposals staged in the last 60s
    assert signals_by_id["sig-rate"]["count"] >= 2


def test_intent_zero_and_negative_rejection():
    # 1. $0 rejected
    res_zero_usd = IntentService.parse_with_clarification("Buy $0 of BTC")
    assert res_zero_usd.success is False
    assert "greater than zero" in (res_zero_usd.error or "")

    res_zero_asset = IntentService.parse_with_clarification("Sell 0 ETH")
    assert res_zero_asset.success is False
    assert "greater than zero" in (res_zero_asset.error or "")

    # 2. Negative numbers rejected
    res_neg_usd = IntentService.parse_with_clarification("Buy -$50 of BTC")
    assert res_neg_usd.success is False
    assert "cannot be negative" in (res_neg_usd.error or "")

    res_neg_usd2 = IntentService.parse_with_clarification("Buy $-50 of BTC")
    assert res_neg_usd2.success is False
    assert "cannot be negative" in (res_neg_usd2.error or "")

    res_neg_asset = IntentService.parse_with_clarification("Sell -1.5 SOL")
    assert res_neg_asset.success is False
    assert "cannot be negative" in (res_neg_asset.error or "")


def test_trade_proposal_validators_and_valueerror_mapping_to_422():
    headers = {"X-Session-ID": "test-val-422"}

    # 1. Negative amount via structured endpoint returns 422
    res_neg = client.post(
        "/api/trades/proposals",
        json={"asset": "BTC", "side": "BUY", "amount": -100.0, "amount_type": "USD"},
        headers=headers,
    )
    assert res_neg.status_code == 422

    # 2. Zero amount via structured endpoint returns 422
    res_zero = client.post(
        "/api/trades/proposals",
        json={"asset": "BTC", "side": "BUY", "amount": 0.0, "amount_type": "USD"},
        headers=headers,
    )
    assert res_zero.status_code == 422

    # 3. Unsupported asset via structured endpoint returns 422
    res_unsupported = client.post(
        "/api/trades/proposals",
        json={"asset": "XRP", "side": "BUY", "amount": 100.0, "amount_type": "USD"},
        headers=headers,
    )
    assert res_unsupported.status_code == 422

    # 4. Extreme amount exceeding cap returns 422
    res_cap = client.post(
        "/api/trades/proposals",
        json={"asset": "BTC", "side": "BUY", "amount": 99_000_000.0, "amount_type": "USD"},
        headers=headers,
    )
    assert res_cap.status_code == 422

    # 5. Missing both prompt and structured fields raises ValueError mapped to 422
    res_empty = client.post(
        "/api/trades/proposals",
        json={},
        headers=headers,
    )
    assert res_empty.status_code == 422


def test_session_hardening_missing_and_invalid_rejected_400():
    # 1. Missing X-Session-ID header rejected with 400
    res_missing = client.get("/api/portfolio")
    assert res_missing.status_code == 400
    assert "Missing required X-Session-ID" in res_missing.json()["detail"]

    # 2. Empty / whitespace X-Session-ID rejected with 400
    res_whitespace = client.get("/api/portfolio", headers={"X-Session-ID": "   "})
    assert res_whitespace.status_code == 400
    assert "Missing required X-Session-ID" in res_whitespace.json()["detail"]

    # 3. Too short X-Session-ID (< 4 chars) rejected with 400
    res_short = client.get("/api/portfolio", headers={"X-Session-ID": "abc"})
    assert res_short.status_code == 400
    assert "Invalid X-Session-ID" in res_short.json()["detail"]

    # 4. Invalid characters rejected with 400
    res_invalid_chars = client.get("/api/portfolio", headers={"X-Session-ID": "session!@#$%^"})
    assert res_invalid_chars.status_code == 400
    assert "Invalid X-Session-ID" in res_invalid_chars.json()["detail"]

    # 5. Valid session ID accepted with 200
    res_valid = client.get("/api/portfolio", headers={"X-Session-ID": "valid-session-1234"})
    assert res_valid.status_code == 200


# ==========================================
# 8. P1-8 Comprehensive Verification Tests
# ==========================================

def test_stale_quote_at_confirm_via_api():
    """Verify that confirming a proposal with an expired quote returns 409 and marks proposal EXPIRED."""
    session = f"test-stale-confirm-{uuid.uuid4().hex[:6]}"
    headers = {"X-Session-ID": session}
    client.post("/api/session/reset", headers=headers)

    # 1. Create valid proposal
    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $100 of SOL"}, headers=headers)
    assert res_prop.status_code == 200
    prop_id = res_prop.json()["id"]

    # 2. Force quote to expired state in SQLite DB
    with get_db() as conn:
        conn.execute(
            "UPDATE trade_proposals SET quote_snapshot = json_set(quote_snapshot, '$.timestamp', '2020-01-01T00:00:00Z', '$.expires_at', '2020-01-01T00:00:30Z') WHERE id = ?",
            (prop_id,)
        )

    # 3. Attempt confirmation: must be rejected with 409 Conflict
    res_confirm = client.post(f"/api/trades/{prop_id}/confirm", json={"proposal_id": prop_id}, headers=headers)
    assert res_confirm.status_code == 409
    assert "expired" in res_confirm.json()["detail"].lower()

    # 4. Verify proposal is marked EXPIRED and audit stream has PROPOSAL_EXPIRED
    prop_record = Storage.get_proposal(prop_id, user_id=session)
    assert prop_record.status == "EXPIRED"

    events = client.get("/api/activity", headers=headers).json()
    assert any(e["event_type"] == "PROPOSAL_EXPIRED" and e["proposal_id"] == prop_id for e in events)


def test_warning_acknowledgement_required_and_recorded_in_audit():
    """Verify that a WARN trade requires acknowledgement, rejects without it, and records WARNING_ACKNOWLEDGED."""
    session = f"test-warn-ack-{uuid.uuid4().hex[:6]}"
    headers = {"X-Session-ID": session}
    client.post("/api/session/reset", headers=headers)

    # 1. Create a proposal that triggers concentration warning (> 40% BTC guideline)
    # Portfolio starts with 0.15 BTC ($12.9k) out of $28.8k (~45%). An extra $1000 BTC triggers WARN.
    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $1000 of BTC"}, headers=headers)
    assert res_prop.status_code == 200
    prop_data = res_prop.json()
    prop_id = prop_data["id"]
    assert prop_data["risk"]["overall_status"] == "WARN"

    # 2. Confirming WITHOUT acknowledgement must return HTTP 400
    res_unack = client.post(
        f"/api/trades/{prop_id}/confirm",
        json={"proposal_id": prop_id, "acknowledged_warnings": False},
        headers=headers,
    )
    assert res_unack.status_code == 400
    assert "acknowledgement" in res_unack.json()["detail"].lower()

    # Verify CONFIRM_REJECTED event recorded
    events_unack = client.get("/api/activity", headers=headers).json()
    assert any(e["event_type"] == "CONFIRM_REJECTED" and e["proposal_id"] == prop_id for e in events_unack)

    # 3. Confirming WITH acknowledgement succeeds with HTTP 200
    res_ack = client.post(
        f"/api/trades/{prop_id}/confirm",
        json={"proposal_id": prop_id, "acknowledged_warnings": True},
        headers=headers,
    )
    assert res_ack.status_code == 200
    assert res_ack.json()["status"] == "FILLED"

    # 4. Verify WARNING_ACKNOWLEDGED event is in the audit stream
    events_filled = client.get("/api/activity", headers=headers).json()
    ack_event = next(e for e in events_filled if e["event_type"] == "WARNING_ACKNOWLEDGED" and e["proposal_id"] == prop_id)
    assert ack_event is not None
    assert ack_event["is_recorded"] is True
    assert ack_event["seq"] is not None


@pytest.mark.asyncio
async def test_stubbed_uat_timeout_handling(monkeypatch):
    """Verify that when UAT gateway times out during order execution, order is marked FAILED and proposal is locked."""
    from app.core.config import settings
    from app.domain.models import QuoteSnapshot, RiskResult, PortfolioImpact, OrderSide, AmountType, TradeProposal, TradeConfirmRequest
    from app.services.order_service import OrderService
    from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError
    from app.db.store import Storage
    from fastapi import HTTPException

    monkeypatch.setattr(settings, "TM_ENV", "uat")
    monkeypatch.setattr(settings, "TM_API_KEY", "mock-key")
    monkeypatch.setattr(settings, "TM_ORGANIZATION_USER_ID", "mock-org-user")

    async def mock_create_order(self, pair, side, quantity, quote_id=None, user_id="demo-user-1"):
        return {"id": "gw-order-timeout-test", "status": "PENDING"}

    async def mock_execute_order(self, order_id, signature=None, user_id="demo-user-1"):
        raise TrueMarketsClientError("Gateway execution timed out", status_code=504, error_code="GATEWAY_TIMEOUT")

    monkeypatch.setattr(TrueMarketsClient, "create_order", mock_create_order)
    monkeypatch.setattr(TrueMarketsClient, "execute_order", mock_execute_order)

    user_id = f"test-uat-timeout-{uuid.uuid4().hex[:6]}"
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
        quote_id="gw-q-timeout",
    )

    prop = TradeProposal(
        id=f"prop-uat-timeout-{uuid.uuid4().hex[:6]}",
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
        explanation="Testing UAT timeout",
        created_at="2026-10-11T12:00:00Z",
        expires_at="2026-10-11T12:05:00Z",
        status="PENDING_CONFIRMATION",
    )
    Storage.save_proposal(prop)

    with pytest.raises(HTTPException) as exc_info:
        await OrderService.confirm_proposal(
            proposal_id=prop.id,
            confirm_req=TradeConfirmRequest(proposal_id=prop.id),
            user_id=user_id,
        )
    assert exc_info.value.status_code == 504
    assert "Order marked FAILED" in exc_info.value.detail

    # Verify proposal status is FAILED and cannot be released or confirmed again
    p_check = Storage.get_proposal(prop.id, user_id=user_id)
    assert p_check.status == "FAILED"


def test_crash_after_fill_transaction_atomicity(monkeypatch):
    """Verify that if an error occurs within execute_demo_fill_atomic, the entire transaction rolls back."""
    import sqlite3
    from decimal import Decimal
    from app.domain.models import QuoteSnapshot, RiskResult, PortfolioImpact, OrderSide, AmountType, TradeProposal

    session = f"test-crash-atomic-{uuid.uuid4().hex[:6]}"
    Storage.reset_session(session)

    init_portfolio = Storage.get_portfolio(session)
    init_cash = init_portfolio["cash_usd"]

    quote = QuoteSnapshot(
        pair="BTC/USDC", base_asset="BTC", quote_asset="USDC",
        bid=86000.0, ask=86100.0, mid=86050.0, spread_pct=0.116,
        timestamp="2026-10-11T12:00:00Z", expires_at="2026-10-11T12:05:00Z",
        source="DEMO_SIMULATOR",
    )
    prop = TradeProposal(
        id=f"prop-crash-{uuid.uuid4().hex[:6]}",
        user_id=session,
        asset="BTC",
        side=OrderSide.BUY,
        request_amount=500.0,
        request_amount_type=AmountType.USD,
        estimated_qty=0.0058,
        estimated_notional_usd=500.0,
        quote=quote,
        risk=RiskResult(overall_status="PASS", can_execute=True, checks=[]),
        portfolio_impact=PortfolioImpact(
            asset="BTC", current_qty=0.0, current_value_usd=0.0, current_allocation_pct=0.0,
            projected_qty=0.0058, projected_value_usd=500.0, projected_allocation_pct=1.0,
            cash_before_usd=init_cash, cash_after_usd=init_cash - 500.0,
            total_portfolio_value_before=init_cash, total_portfolio_value_after=init_cash,
        ),
        explanation="Testing crash rollback",
        created_at="2026-10-11T12:00:00Z",
        expires_at="2026-10-11T12:05:00Z",
        status="CONFIRMING",
    )
    Storage.save_proposal(prop)

    # Intentionally trigger an error by attempting to fill with a notional exceeding cash balance
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        Storage.execute_demo_fill_atomic(
            proposal_id=prop.id,
            user_id=session,
            asset="BTC",
            side=OrderSide.BUY,
            estimated_qty=0.0058,
            estimated_notional_usd=99999999.0,  # Far exceeds cash balance ($10,000)!
            fill_price=86100.0,
            acknowledged_warnings=False,
        )
    assert exc_info.value.status_code == 400

    # Verify that portfolio cash was NOT touched
    after_portfolio = Storage.get_portfolio(session)
    assert after_portfolio["cash_usd"] == init_cash

    # Verify that proposal status was safely restored to PENDING_CONFIRMATION (cannot fill without balance)
    p_check = Storage.get_proposal(prop.id, user_id=session)
    assert p_check.status == "PENDING_CONFIRMATION"

    # Verify that no order was persisted in the database
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM orders WHERE proposal_id = ?", (prop.id,)).fetchone()
        assert row["cnt"] == 0

    # 2. Test mid-transaction crash rollback
    # Claim proposal to CONFIRMING again
    Storage.update_proposal_status(prop.id, "CONFIRMING", user_id=session)

    # Force a database exception during execution by wrapping connection
    class CrashCursor:
        def __init__(self, cur):
            self._cur = cur
        def __getattr__(self, name):
            return getattr(self._cur, name)
        def execute(self, sql, *args, **kwargs):
            if "INSERT INTO orders" in sql:
                raise sqlite3.OperationalError("Simulated disk I/O crash during order insertion")
            return self._cur.execute(sql, *args, **kwargs)

    class MockConnectionWrapper:
        def __init__(self, conn):
            self._conn = conn
        def __getattr__(self, name):
            return getattr(self._conn, name)
        def __enter__(self):
            self._conn.__enter__()
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            return self._conn.__exit__(exc_type, exc_val, exc_tb)
        def cursor(self):
            return CrashCursor(self._conn.cursor())

    orig_get_db = get_db
    monkeypatch.setattr("app.db.store.get_db", lambda: MockConnectionWrapper(orig_get_db()))

    with pytest.raises(HTTPException) as exc_crash:
        Storage.execute_demo_fill_atomic(
            proposal_id=prop.id,
            user_id=session,
            asset="BTC",
            side=OrderSide.BUY,
            estimated_qty=0.0058,
            estimated_notional_usd=500.0,
            fill_price=86100.0,
            acknowledged_warnings=False,
        )
    assert exc_crash.value.status_code == 500
    assert "Simulated disk I/O crash" in exc_crash.value.detail

    # Cash must still be unchanged after rollback
    crash_portfolio = Storage.get_portfolio(session)
    assert crash_portfolio["cash_usd"] == init_cash

    # No order persisted
    with orig_get_db() as conn_check:
        row_check = conn_check.execute("SELECT COUNT(*) as cnt FROM orders WHERE proposal_id = ?", (prop.id,)).fetchone()
        assert row_check["cnt"] == 0


def test_strict_monotonic_event_ordering_across_lifecycle():
    """Verify that all events recorded across a trade lifecycle have strictly monotonic seq numbers."""
    session = f"test-event-seq-{uuid.uuid4().hex[:6]}"
    headers = {"X-Session-ID": session}
    client.post("/api/session/reset", headers=headers)

    # 1. Parse intent
    res_parse = client.post("/api/intent/parse", json={"prompt": "Buy $150 of SOL"}, headers=headers)
    assert res_parse.status_code == 200

    # 2. Create proposal
    res_prop = client.post("/api/trades/proposals", json={"prompt": "Buy $150 of SOL"}, headers=headers)
    assert res_prop.status_code == 200
    prop_id = res_prop.json()["id"]

    # 3. Confirm trade
    res_confirm = client.post(f"/api/trades/{prop_id}/confirm", json={"proposal_id": prop_id}, headers=headers)
    assert res_confirm.status_code == 200

    # 4. Fetch activity events
    events = client.get("/api/activity", headers=headers).json()
    assert len(events) >= 3

    # Activity endpoint returns ORDER BY seq DESC
    seqs_desc = [e["seq"] for e in events]
    assert all(isinstance(s, int) for s in seqs_desc)
    for i in range(len(seqs_desc) - 1):
        assert seqs_desc[i] > seqs_desc[i + 1], f"Expected seq {seqs_desc[i]} > {seqs_desc[i+1]}"

    # Verify timestamps are ISO 8601 formatted
    from datetime import datetime
    for e in events:
        ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
        assert ts is not None
        assert e["is_recorded"] is True


def test_market_candles_endpoint_success_and_error(monkeypatch):
    """Test /api/market/candles endpoint returns real candle schema and handles errors."""
    from app.services.true_markets_client import TrueMarketsClient, TrueMarketsClientError

    # 1. Success mock
    async def mock_get_candles(self, symbol, window="1d", resolution="15m", asset_class="spot"):
        return {
            "symbol": symbol,
            "window": window,
            "resolution": resolution,
            "candles": [
                {"t": "2026-10-07T12:00:00Z", "open": "83000.0", "high": "83500.0", "low": "82900.0", "close": "83200.0"},
                {"t": "2026-10-07T12:15:00Z", "open": "83200.0", "high": "83800.0", "low": "83100.0", "close": "83600.0"},
            ],
        }

    monkeypatch.setattr(TrueMarketsClient, "get_candles", mock_get_candles)

    res = client.get("/api/market/candles?asset=BTC&window=1d")
    assert res.status_code == 200
    data = res.json()
    assert data["asset"] == "BTC"
    assert data["is_available"] is True
    assert len(data["candles"]) == 2
    assert data["current_price"] == 83600.0
    assert data["price_change"] == 600.0
    assert data["high"] == 83800.0
    assert data["low"] == 82900.0
    assert isinstance(data["candles"][0]["time"], int)

    # 2. Unsupported asset validation (400)
    res_bad = client.get("/api/market/candles?asset=FAKEASSET")
    assert res_bad.status_code == 400
    assert "not supported" in res_bad.json()["detail"]

    # 3. Graceful upstream error handling (is_available=False, no crash)
    async def mock_failing_candles(self, symbol, window="1d", resolution="15m", asset_class="spot"):
        raise TrueMarketsClientError("Upstream timeout", status_code=504)

    monkeypatch.setattr(TrueMarketsClient, "get_candles", mock_failing_candles)
    # Use different window to bypass cache
    res_err = client.get("/api/market/candles?asset=SOL&window=4h")
    assert res_err.status_code == 200
    data_err = res_err.json()
    assert data_err["is_available"] is False
    assert data_err["status_label"] == "Market data temporarily unavailable"
    assert len(data_err["candles"]) == 0


def test_risk_engine_why_it_matters_and_what_you_can_do_populated():
    """Verify that RiskEngine enriches checks with explainable 'why_it_matters' and 'what_you_can_do'."""
    from app.services.risk_engine import RiskEngine
    from app.domain.models import QuoteSnapshot, OrderSide, AmountType

    quote = QuoteSnapshot(
        pair="BTC/USDC",
        base_asset="BTC",
        quote_asset="USDC",
        bid=80000.0,
        ask=80100.0,
        mid=80050.0,
        spread_pct=0.12,
        timestamp="2026-10-07T12:00:00Z",
        expires_at="2026-10-07T12:05:00Z",
        source="DEMO_SIMULATOR",
        age_seconds=5.0,
    )

    risk_result, _, _, _ = RiskEngine.evaluate_trade(
        asset="BTC",
        side=OrderSide.BUY,
        request_amount=1000.0,
        request_amount_type=AmountType.USD,
        quote=quote,
        cash_usd=10000.0,
        current_positions={"BTC": 0.05},
    )

    for check in risk_result.checks:
        assert check.why_it_matters is not None and len(check.why_it_matters) > 5
        assert check.what_you_can_do is not None and len(check.what_you_can_do) > 5




