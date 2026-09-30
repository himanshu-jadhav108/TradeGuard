# Product Brief

TradeGuard is an AI-assisted financial execution interface.

### Core sentence
> TradeGuard turns a natural-language trade request into an explainable, risk-checked proposal and executes through True Markets only after explicit user confirmation.

### Primary demo
User enters: `Buy $500 of BTC`

System:
1. Extracts structured intent.
2. Retrieves account/balance and quote data.
3. Runs deterministic risk checks.
4. Shows a trade review card.
5. User explicitly confirms.
6. Creates/signs/executes the True Markets order when UAT is configured.
7. Polls status.
8. Records an audit event and updates the portfolio view.

### Modes
- DEMO: deterministic seeded account/quote/order simulation. No external credentials.
- UAT: real True Markets sandbox integration.
- PRODUCTION: feature-flagged and disabled by default for the hackathon.

### Success
A judge can understand the value within 60 seconds and complete the core flow within 2 minutes.
