import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.domain.models import AuditEvent, OrderRecord, OrderStatus, Position, TradeProposal

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

    # Seed default demo account if empty
    seed_demo_account(conn)
    conn.close()


def seed_demo_account(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = 'demo-user-1'")
    if not cur.fetchone():
        now = datetime.now(timezone.utc).isoformat()
        cur.execute("INSERT INTO users (id, name, created_at) VALUES (?, ?, ?)", ("demo-user-1", "Demo Trader", now))
        cur.execute("INSERT INTO portfolios (user_id, cash_usd, updated_at) VALUES (?, ?, ?)", ("demo-user-1", 10000.0, now))
        
        # Initial holdings: 0.15 BTC ($12,000 approx) and 1.5 ETH ($4,500 approx)
        cur.execute("INSERT INTO positions (user_id, asset, quantity, updated_at) VALUES (?, ?, ?, ?)",
                    ("demo-user-1", "BTC", 0.15, now))
        cur.execute("INSERT INTO positions (user_id, asset, quantity, updated_at) VALUES (?, ?, ?, ?)",
                    ("demo-user-1", "ETH", 1.5, now))
        cur.execute("INSERT INTO positions (user_id, asset, quantity, updated_at) VALUES (?, ?, ?, ?)",
                    ("demo-user-1", "SOL", 10.0, now))

        # Initial audit event
        cur.execute("""
            INSERT INTO audit_events (id, user_id, event_type, summary, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "evt-init-001",
            "demo-user-1",
            "ACCOUNT_SEEDED",
            "Demo portfolio initialized with $10,000.00 cash and initial positions.",
            json.dumps({"cash": 10000.0, "btc": 0.15, "eth": 1.5, "sol": 10.0}),
            now
        ))
        conn.commit()


# Repository operations
class Storage:
    @staticmethod
    def get_portfolio(user_id: str = "demo-user-1") -> Dict[str, Any]:
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
        conn = get_db()
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO trade_proposals (
                    id, user_id, asset, side, request_amount, request_amount_type,
                    estimated_qty, estimated_notional_usd, quote_snapshot, risk_result,
                    portfolio_impact, explanation, status, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                proposal.status,
                proposal.created_at,
                proposal.expires_at,
            ))
        conn.close()

    @staticmethod
    def get_proposal(proposal_id: str) -> Optional[TradeProposal]:
        conn = get_db()
        cur = conn.cursor()
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
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            status=row["status"],
        )

    @staticmethod
    def update_proposal_status(proposal_id: str, status: str):
        conn = get_db()
        with conn:
            conn.execute("UPDATE trade_proposals SET status = ? WHERE id = ?", (status, proposal_id))
        conn.close()

    @staticmethod
    def save_order(order: OrderRecord):
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
                json.dumps({"mode": order.mode, "audit_id": order.audit_id}),
                order.mode,
                order.created_at,
                order.updated_at,
            ))
        conn.close()

    @staticmethod
    def get_order(order_id: str) -> Optional[OrderRecord]:
        conn = get_db()
        cur = conn.cursor()
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
        )

    @staticmethod
    def save_audit_event(event: AuditEvent):
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
