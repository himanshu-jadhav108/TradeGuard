# Architecture

Browser → Next.js → FastAPI → services → True Markets.

## Frontend
- Next.js + TypeScript
- Tailwind CSS
- Accessible component primitives
- Recharts or equivalent for financial charts
- Server-safe API client
- Theme tokens for light/dark

## Backend
FastAPI
- intent service
- portfolio service
- deterministic risk engine
- quote service
- trade proposal service
- True Markets adapter
- order lifecycle service
- audit service

## Storage
SQLite for local/demo persistence. Keep persistence behind repository interfaces so a managed DB can replace it later.

## True Markets boundary
`true_markets_client.py` is the ONLY module allowed to know True Markets authentication/base URLs/headers/SDK details.

No frontend True Markets calls.
No secrets in Git.
