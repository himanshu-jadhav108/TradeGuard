# True Markets Integration

## Current documented endpoints
UAT Gateway base:
`https://api.uat.truemarkets.co/v1/gateway`

Production:
`https://api.truemarkets.co/v1/gateway`

Auth:
`POST /v1/auth/api-key/token`

Gateway:
- `POST /quotes`
- `POST /orders`
- `GET /orders`
- `POST /orders/{id}/execute`
- `GET /orders/{id}`
- `GET /orders/{id}/status`
- balances endpoint
- assets/account endpoints as required

## Authentication model
Gateway clients use:
- organization API key
- signer key

The organization token authenticates the app. User-scoped Gateway requests carry `TM-On-Behalf-Of: <user_id>`.

Order creation can return unsigned wallet transaction payloads. The server signs required payloads with the signer key and posts signatures to `/orders/{id}/execute`. Nothing moves until execution.

## SDK
Prefer the official Python SDK from the FastAPI backend if it supports the required UAT flow. Pin the version after verification.

## Implementation rules
- Create a small adapter with typed request/response models.
- Add timeout, retry/backoff only for safe operations.
- Never blindly retry execute operations.
- Handle `quote_stale`, `insufficient_balance`, `already_submitted`, `401`, `422`, `429`, `503`.
- Log request IDs, not secrets.
- Store external order IDs and statuses.

## Important
UAT is the documented sandbox. Some UAT integrations may require VPN/allowlisting. Do not hard-code an assumption that public-network UAT will work.
