import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from app.domain.models import AuditEvent, OrderRecord, OrderSide, OrderStatus, Position, TradeProposal

DB_PATH = Path(__file__).parent.parent.parent / "tradeguard.db"

_db_initialized = False


def get_db():
    global _db_initialized
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    if not _db_initialized:
        _db_initialized = True
        init_db()
    return conn


def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                user_id TEXT PRIMARY KEY,
                cash_usd REAL NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                user_id TEXT NOT NULL,
                asset TEXT NOT NULL,
                quantity REAL NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, asset),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_proposals (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                asset TEXT NOT NULL,
                side TEXT NOT NULL,
                request_amount REAL NOT NULL,
                request_amount_type TEXT NOT NULL,
                estimated_qty REAL NOT NULL,
                estimated_notional_usd REAL NOT NULL,
                quote_snapshot TEXT NOT NULL,
                risk_result TEXT NOT NULL,
                portfolio_impact TEXT NOT NULL,
                explanation TEXT NOT NULL,
                raw_prompt TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                asset TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                notional_usd REAL NOT NULL,
                status TEXT NOT NULL,
                external_order_id TEXT,
                fill_price REAL,
                raw_safe_metadata TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (proposal_id) REFERENCES trade_proposals(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                proposal_id TEXT,
                order_id TEXT,
                summary TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        # Migration: ensure raw_prompt column exists on trade_proposals
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(trade_proposals)")
        cols = [r["name"] for r in cur.fetchall()]
        if "raw_prompt" not in cols:
            conn.execute("ALTER TABLE trade_proposals ADD COLUMN raw_prompt TEXT")

    # Seed baseline default demo account
    seed_session_account(conn, "demo-user-1", "Default Demo Trader")
    conn.close()


def seed_session_account(conn: sqlite3.Connection, session_id: str, name: str = "Demo Trader"):
    """Seeds an isolated demo account for a specific session."""
    with conn:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("INSERT OR IGNORE INTO users (id, name, created_at) VALUES (?, ?, ?)", (session_id, name, now))
        conn.execute("""
            INSERT INTO portfolios (user_id, cash_usd, updated_at) VALUES (?, 10000.0, ?)
            ON CONFLICT(user_id) DO NOTHING
        """, (session_id, now))

        cur = conn.cursor()
        cur.execute("SELECT count(*) as cnt FROM positions WHERE user_id = ?", (session_id,))
        row = cur.fetchone()
        if row and row["cnt"] == 0:
            conn.execute("INSERT INTO positions (user_id, asset, quantity, updated_at) VALUES (?, 'BTC', 0.15, ?)", (session_id, now))
            conn.execute("INSERT INTO positions (user_id, asset, quantity, updated_at) VALUES (?, 'ETH', 1.5, ?)", (session_id, now))
            conn.execute("INSERT INTO positions (user_id, asset, quantity, updated_at) VALUES (?, 'SOL', 10.0, ?)", (session_id, now))

            conn.execute("""
                INSERT OR IGNORE INTO audit_events (id, user_id, event_type, summary, metadata_json, created_at)
                VALUES (?, ?, 'ACCOUNT_SEEDED', 'Demo portfolio initialized with $10,000.00 cash and standard holdings.', ?, ?)
            """, (f"evt-init-{session_id[:8]}", session_id, json.dumps({"cash": 10000.0, "btc": 0.15, "eth": 1.5, "sol": 10.0}), now))


class Storage:
    @staticmethod
    def ensure_session(session_id: str):
        conn = get_db()
        seed_session_account(conn, session_id)
        conn.close()

    @staticmethod
    def get_portfolio(user_id: str = "demo-user-1") -> Dict[str, Any]:
        Storage.ensure_session(user_id)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT cash_usd FROM portfolios WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        cash = row["cash_usd"] if row else 10000.0

        cur.execute("SELECT asset, quantity FROM positions WHERE user_id = ?", (user_id,))
        positions = {r["asset"]: r["quantity"] for r in cur.fetchall()}
        conn.close()
        return {"cash_usd": cash, "positions": positions}

    @staticmethod
    def update_portfolio(user_id: str, cash_usd: float, positions: Dict[str, float]):
        Storage.ensure_session(user_id)
        conn = get_db()
        now = datetime.now(timezone.utc).isoformat()
        with conn:
            conn.execute("UPDATE portfolios SET cash_usd = ?, updated_at = ? WHERE user_id = ?", (cash_usd, now, user_id))
            for asset, qty in positions.items():
                conn.execute("""
                    INSERT INTO positions (user_id, asset, quantity, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, asset) DO UPDATE SET quantity = excluded.quantity, updated_at = excluded.updated_at
                """, (user_id, asset, qty, now))
        conn.close()

    @staticmethod
    def save_proposal(proposal: TradeProposal):
        Storage.ensure_session(proposal.user_id)
        conn = get_db()
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO trade_proposals (
                    id, user_id, asset, side, request_amount, request_amount_type,
                    estimated_qty, estimated_notional_usd, quote_snapshot, risk_result,
                    portfolio_impact, explanation, raw_prompt, status, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal.id,
                proposal.user_id,
                proposal.asset,
                proposal.side.value,
                proposal.request_amount,
                proposal.request_amount_type.value,
                proposal.estimated_qty,
                proposal.estimated_notional_usd,
                proposal.quote.model_dump_json(),
                proposal.risk.model_dump_json(),
                proposal.portfolio_impact.model_dump_json(),
                proposal.explanation,
                proposal.raw_prompt,
                proposal.status,
                proposal.created_at,
                proposal.expires_at,
            ))
        conn.close()

    @staticmethod
    def get_proposal(proposal_id: str, user_id: Optional[str] = None) -> Optional[TradeProposal]:
        conn = get_db()
        cur = conn.cursor()
        if user_id:
            cur.execute("SELECT * FROM trade_proposals WHERE id = ? AND user_id = ?", (proposal_id, user_id))
        else:
            cur.execute("SELECT * FROM trade_proposals WHERE id = ?", (proposal_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        from app.domain.models import QuoteSnapshot, RiskResult, PortfolioImpact, OrderSide, AmountType
        return TradeProposal(
            id=row["id"],
            user_id=row["user_id"],
            asset=row["asset"],
            side=OrderSide(row["side"]),
            request_amount=row["request_amount"],
            request_amount_type=AmountType(row["request_amount_type"]),
            estimated_qty=row["estimated_qty"],
            estimated_notional_usd=row["estimated_notional_usd"],
            quote=QuoteSnapshot.model_validate_json(row["quote_snapshot"]),
            risk=RiskResult.model_validate_json(row["risk_result"]),
            portfolio_impact=PortfolioImpact.model_validate_json(row["portfolio_impact"]),
            explanation=row["explanation"],
            raw_prompt=row["raw_prompt"] if "raw_prompt" in row.keys() else None,
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            status=row["status"],
        )

    @staticmethod
    def claim_proposal_for_confirmation(proposal_id: str, user_id: str) -> bool:
        """
        Atomically claims a proposal for execution, transitioning from PENDING_CONFIRMATION to CONFIRMING.
        Guarantees protection against concurrent double confirmation.
        """
        conn = get_db()
        with conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE trade_proposals
                SET status = 'CONFIRMING'
                WHERE id = ? AND user_id = ? AND status = 'PENDING_CONFIRMATION'
            """, (proposal_id, user_id))
            claimed = cur.rowcount > 0
        conn.close()
        return claimed

    @staticmethod
    def update_proposal_status(proposal_id: str, status: str, user_id: Optional[str] = None):
        conn = get_db()
        with conn:
            if user_id:
                conn.execute("UPDATE trade_proposals SET status = ? WHERE id = ? AND user_id = ?", (status, proposal_id, user_id))
            else:
                conn.execute("UPDATE trade_proposals SET status = ? WHERE id = ?", (status, proposal_id))
        conn.close()

    @staticmethod
    def cancel_proposal(proposal_id: str, user_id: str) -> bool:
        """
        Atomically cancels a proposal if and only if it is in PENDING_CONFIRMATION.
        Also records TRADE_CANCELLED audit event in the same transaction.
        """
        conn = get_db()
        now = datetime.now(timezone.utc).isoformat()
        import uuid
        with conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE trade_proposals
                SET status = 'CANCELLED'
                WHERE id = ? AND user_id = ? AND status = 'PENDING_CONFIRMATION'
            """, (proposal_id, user_id))
            cancelled = cur.rowcount > 0
            if cancelled:
                cur.execute("""
                    INSERT INTO audit_events (
                        id, user_id, event_type, proposal_id, order_id, summary, metadata_json, created_at
                    ) VALUES (?, ?, 'TRADE_CANCELLED', ?, NULL, ?, ?, ?)
                """, (
                    f"evt-{uuid.uuid4().hex[:12]}",
                    user_id,
                    proposal_id,
                    "Proposal cancelled while in PENDING_CONFIRMATION.",
                    json.dumps({"mode": "DEMO"}),
                    now,
                ))
        conn.close()
        return cancelled

    @staticmethod
    def execute_demo_fill_atomic(
        proposal_id: str,
        user_id: str,
        asset: str,
        side: OrderSide,
        estimated_qty: float,
        estimated_notional_usd: float,
        fill_price: float,
        raw_prompt: Optional[str] = None,
    ) -> OrderRecord:
        """
        Executes a demo order fill atomically in a single BEGIN IMMEDIATE transaction:
        1. Verifies proposal is in CONFIRMING state.
        2. Re-checks portfolio balances directly in DB.
        3. Updates cash and asset positions with Decimal-grade precision.
        4. Transitions proposal status to CONFIRMED.
        5. Persists OrderRecord with FILLED status.
        6. Appends TRADE_CONFIRMED and ORDER_FILLED audit events.
        Rolls back entirely on any error.
        """
        Storage.ensure_session(user_id)
        conn = get_db()
        conn.isolation_level = None
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        import uuid

        try:
            cur.execute("BEGIN IMMEDIATE")

            # 1. Verify proposal exists and is in CONFIRMING state
            cur.execute("SELECT status FROM trade_proposals WHERE id = ? AND user_id = ?", (proposal_id, user_id))
            p_row = cur.fetchone()
            if not p_row:
                cur.execute("ROLLBACK")
                raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found.")
            if p_row["status"] != "CONFIRMING":
                cur.execute("ROLLBACK")
                raise HTTPException(
                    status_code=409,
                    detail=f"Proposal cannot be filled (status: {p_row['status']}). Expected CONFIRMING."
                )

            # 2. Re-check user balances inside the transaction
            cur.execute("SELECT cash_usd FROM portfolios WHERE user_id = ?", (user_id,))
            port_row = cur.fetchone()
            cash_val = port_row["cash_usd"] if port_row else 10000.0

            cur.execute("SELECT asset, quantity FROM positions WHERE user_id = ?", (user_id,))
            positions = {r["asset"]: Decimal(str(r["quantity"])) for r in cur.fetchall()}

            d_cash = Decimal(str(cash_val))
            d_notional = Decimal(str(estimated_notional_usd))
            d_qty = Decimal(str(estimated_qty))

            if side == OrderSide.BUY and d_notional > d_cash:
                cur.execute("UPDATE trade_proposals SET status = 'PENDING_CONFIRMATION' WHERE id = ?", (proposal_id,))
                cur.execute("COMMIT")
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient cash balance at confirmation. Needed: ${float(d_notional):,.2f}, Available: ${float(d_cash):,.2f}"
                )
            elif side == OrderSide.SELL and d_qty > positions.get(asset, Decimal("0")):
                cur.execute("UPDATE trade_proposals SET status = 'PENDING_CONFIRMATION' WHERE id = ?", (proposal_id,))
                cur.execute("COMMIT")
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient {asset} balance at confirmation. Needed: {float(d_qty):,.6f}, Owned: {float(positions.get(asset, Decimal('0'))):,.6f}"
                )

            # 3. Update portfolio balances using Decimal arithmetic
            if side == OrderSide.BUY:
                new_cash = (d_cash - d_notional).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                new_asset_qty = (positions.get(asset, Decimal("0")) + d_qty).quantize(
                    Decimal("0.000001"), rounding=ROUND_HALF_UP
                )
            else:
                new_cash = (d_cash + d_notional).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                new_asset_qty = max(Decimal("0"), positions.get(asset, Decimal("0")) - d_qty).quantize(
                    Decimal("0.000001"), rounding=ROUND_HALF_UP
                )

            cur.execute(
                "UPDATE portfolios SET cash_usd = ?, updated_at = ? WHERE user_id = ?",
                (float(new_cash), now, user_id),
            )
            cur.execute("""
                INSERT INTO positions (user_id, asset, quantity, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, asset) DO UPDATE SET quantity = excluded.quantity, updated_at = excluded.updated_at
            """, (user_id, asset, float(new_asset_qty), now))

            # 4. Update proposal status to CONFIRMED
            cur.execute("UPDATE trade_proposals SET status = 'CONFIRMED' WHERE id = ?", (proposal_id,))

            # 5. Insert order record
            order_id = f"ord-{uuid.uuid4().hex[:12]}"
            external_order_id = f"demo-sim-{uuid.uuid4().hex[:8]}"
            order = OrderRecord(
                id=order_id,
                proposal_id=proposal_id,
                user_id=user_id,
                asset=asset,
                side=side,
                quantity=estimated_qty,
                notional_usd=estimated_notional_usd,
                status=OrderStatus.FILLED,
                external_order_id=external_order_id,
                fill_price=fill_price,
                created_at=now,
                updated_at=now,
                mode="DEMO",
                audit_id=f"audit-{order_id}",
                raw_prompt=raw_prompt,
            )

            cur.execute("""
                INSERT INTO orders (
                    id, proposal_id, user_id, asset, side, quantity, notional_usd,
                    status, external_order_id, fill_price, raw_safe_metadata, mode,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order.id,
                order.proposal_id,
                order.user_id,
                order.asset,
                order.side.value,
                order.quantity,
                order.notional_usd,
                order.status.value,
                order.external_order_id,
                order.fill_price,
                json.dumps({"mode": order.mode, "audit_id": order.audit_id, "raw_prompt": order.raw_prompt}),
                order.mode,
                order.created_at,
                order.updated_at,
            ))

            # 6. Audit events (inside same transaction)
            cur.execute("""
                INSERT INTO audit_events (
                    id, user_id, event_type, proposal_id, order_id, summary, metadata_json, created_at
                ) VALUES (?, ?, 'TRADE_CONFIRMED', ?, ?, ?, ?, ?)
            """, (
                f"evt-{uuid.uuid4().hex[:12]}",
                user_id,
                proposal_id,
                order_id,
                f"User explicitly confirmed {side.value} {estimated_qty:,.6f} {asset} (Simulated Demo).",
                json.dumps({"mode": "DEMO", "notional_usd": estimated_notional_usd}),
                now,
            ))

            cur.execute("""
                INSERT INTO audit_events (
                    id, user_id, event_type, proposal_id, order_id, summary, metadata_json, created_at
                ) VALUES (?, ?, 'ORDER_FILLED', ?, ?, ?, ?, ?)
            """, (
                f"evt-{uuid.uuid4().hex[:12]}",
                user_id,
                proposal_id,
                order_id,
                f"Simulated order filled at ${fill_price:,.2f} USDC (External ID: {external_order_id}).",
                json.dumps({
                    "fill_price": fill_price,
                    "quantity": estimated_qty,
                    "cash_after": float(new_cash),
                    "mode": "DEMO",
                }),
                now,
            ))

            cur.execute("COMMIT")
            return order

        except HTTPException:
            raise
        except Exception as e:
            try:
                cur.execute("ROLLBACK")
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=f"Database transaction error during fill: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def save_order(order: OrderRecord):
        Storage.ensure_session(order.user_id)
        conn = get_db()
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO orders (
                    id, proposal_id, user_id, asset, side, quantity, notional_usd,
                    status, external_order_id, fill_price, raw_safe_metadata, mode,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order.id,
                order.proposal_id,
                order.user_id,
                order.asset,
                order.side.value,
                order.quantity,
                order.notional_usd,
                order.status.value,
                order.external_order_id,
                order.fill_price,
                json.dumps({"mode": order.mode, "audit_id": order.audit_id, "raw_prompt": order.raw_prompt}),
                order.mode,
                order.created_at,
                order.updated_at,
            ))
        conn.close()

    @staticmethod
    def get_order(order_id: str, user_id: Optional[str] = None) -> Optional[OrderRecord]:
        conn = get_db()
        cur = conn.cursor()
        if user_id:
            cur.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
        else:
            cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        from app.domain.models import OrderSide, OrderStatus
        meta = json.loads(row["raw_safe_metadata"]) if row["raw_safe_metadata"] else {}
        return OrderRecord(
            id=row["id"],
            proposal_id=row["proposal_id"],
            user_id=row["user_id"],
            asset=row["asset"],
            side=OrderSide(row["side"]),
            quantity=row["quantity"],
            notional_usd=row["notional_usd"],
            status=OrderStatus(row["status"]),
            external_order_id=row["external_order_id"],
            fill_price=row["fill_price"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            mode=row["mode"],
            audit_id=meta.get("audit_id"),
            raw_prompt=meta.get("raw_prompt"),
        )

    @staticmethod
    def save_audit_event(event: AuditEvent):
        Storage.ensure_session(event.user_id)
        conn = get_db()
        with conn:
            conn.execute("""
                INSERT INTO audit_events (
                    id, user_id, event_type, proposal_id, order_id, summary,
                    metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id,
                event.user_id,
                event.event_type,
                event.proposal_id,
                event.order_id,
                event.summary,
                json.dumps(event.metadata),
                event.timestamp,
            ))
        conn.close()

    @staticmethod
    def get_audit_events(user_id: str = "demo-user-1", limit: int = 50) -> List[AuditEvent]:
        Storage.ensure_session(user_id)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM audit_events WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        rows = cur.fetchall()
        conn.close()
        return [
            AuditEvent(
                id=r["id"],
                user_id=r["user_id"],
                event_type=r["event_type"],
                proposal_id=r["proposal_id"],
                order_id=r["order_id"],
                summary=r["summary"],
                metadata=json.loads(r["metadata_json"]) if r["metadata_json"] else {},
                timestamp=r["created_at"],
            )
            for r in rows
        ]

    @staticmethod
    def reset_session(session_id: str):
        """
        Resets ONLY the requesting session's portfolio, proposals, and orders.
        Does NOT impact other visitor sessions.
        """
        conn = get_db()
        now = datetime.now(timezone.utc).isoformat()
        with conn:
            # Delete session proposals and orders
            conn.execute("DELETE FROM orders WHERE user_id = ?", (session_id,))
            conn.execute("DELETE FROM trade_proposals WHERE user_id = ?", (session_id,))
            conn.execute("DELETE FROM audit_events WHERE user_id = ?", (session_id,))

            # Reset portfolio to $10,000 cash and baseline positions
            conn.execute("""
                INSERT INTO portfolios (user_id, cash_usd, updated_at) VALUES (?, 10000.0, ?)
                ON CONFLICT(user_id) DO UPDATE SET cash_usd = 10000.0, updated_at = excluded.updated_at
            """, (session_id, now))

            conn.execute("DELETE FROM positions WHERE user_id = ?", (session_id,))
            conn.execute("INSERT INTO positions (user_id, asset, quantity, updated_at) VALUES (?, 'BTC', 0.15, ?)", (session_id, now))
            conn.execute("INSERT INTO positions (user_id, asset, quantity, updated_at) VALUES (?, 'ETH', 1.5, ?)", (session_id, now))
            conn.execute("INSERT INTO positions (user_id, asset, quantity, updated_at) VALUES (?, 'SOL', 10.0, ?)", (session_id, now))

            import uuid
            conn.execute("""
                INSERT INTO audit_events (id, user_id, event_type, summary, metadata_json, created_at)
                VALUES (?, ?, 'ACCOUNT_RESET', 'Session demo account reset to initial balances ($10,000 USDC, 0.15 BTC, 1.5 ETH, 10 SOL).', ?, ?)
            """, (f"evt-reset-{uuid.uuid4().hex[:12]}", session_id, json.dumps({"cash": 10000.0, "btc": 0.15, "eth": 1.5, "sol": 10.0}), now))
        conn.close()
