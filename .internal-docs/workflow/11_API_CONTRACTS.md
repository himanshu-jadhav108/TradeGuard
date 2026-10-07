# Backend API Contract

POST /api/intent/parse
Input: natural language
Output: validated intent

POST /api/trades/proposals
Input: intent
Output: trade proposal with quote/risk data

POST /api/trades/{proposal_id}/confirm
Output: order lifecycle state

GET /api/orders/{order_id}
GET /api/portfolio
GET /api/activity
GET /api/health

Keep external provider schema out of the frontend. Frontend consumes TradeGuard domain models.
