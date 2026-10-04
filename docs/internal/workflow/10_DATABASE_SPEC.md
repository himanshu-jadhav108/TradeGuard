# Database

Tables/entities:
- users
- portfolios
- positions
- trade_proposals
- orders
- audit_events

Important fields:
trade_proposals:
id, user_id, asset, side, qty, qty_unit, quote_snapshot, risk_result, explanation, status, created_at

orders:
id, proposal_id, external_order_id, status, raw_safe_metadata, created_at, updated_at

audit_events:
id, user_id, event_type, proposal_id, order_id, metadata_json, created_at

Do not store private keys or bearer tokens.
