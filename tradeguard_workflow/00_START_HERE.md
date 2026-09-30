# TradeGuard — Antigravity Build Workflow

## Mission
Build TradeGuard from scratch as a premium, production-minded fintech demo for the True Markets “Call for Builders: Build the Next Wealth App” challenge.

**Tagline:** Think before you trade.

## Core product
Natural-language trade intent → deterministic validation/risk checks → True Markets quote → explainable trade proposal → explicit human confirmation → True Markets order lifecycle → portfolio/audit.

## Non-negotiables
- Do not build an autonomous trading bot.
- The LLM never directly executes trades.
- Deterministic backend code owns authoritative numbers.
- True Markets credentials never reach the browser.
- Build DEMO mode first, then UAT integration.
- Premium UI is a product requirement, not polish.
- Light/dark theme must both look intentional.
- No generic AI-slop visuals: no purple AI gradients, excessive glassmorphism, cartoon robots, giant chatbot hero, fake metrics, or unverifiable claims.
- Never claim a trade was executed unless the API actually returned the relevant state.
- Never use production funds during development.
