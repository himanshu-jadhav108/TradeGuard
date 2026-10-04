# TradeGuard — Competition Hardening & Implementation Status

**Submission Target:** True Markets — Call for Builders: Build the Next Wealth App  
**Status Date:** October 4, 2026  
**Operating Directive:** Think before you trade. AI interprets. Backend validates. User decides.

---

## 1. Verified Existing Functionality

| Layer / Component | Verified Behavior | Integrity Status |
| :--- | :--- | :--- |
| **Separation of Concerns** | Clear boundaries between Intent -> Quote -> Risk -> Proposal -> Order execution. | Retained & Healthy |
| **Server-Side Risk Engine** | Hard pre-trade checks on asset allowlist, quote freshness, max notional, purchasing power, and portfolio concentration. | Deterministic & Enforced |
| **Human Confirmation Gate** | Explicit two-step workflow (`create proposal` -> `review card` -> `confirm order`). No autonomous or unconfirmed execution. | Enforced |
| **Deterministic Demo Mode** | Zero-credential simulation available with local SQLite persistence and predictable test vectors. | Functional |
| **Audit Stream** | Structured `AuditEvent` records generated on proposal creation, trade confirmation, and fills. | Preserved |
| **Frontend Foundation** | Next.js 15 App Router with Tailwind CSS, high-contrast dark/light mode tokens, and reduced-motion support. | Clean & Operational |
| **Test Baseline** | Backend `pytest` suite and frontend TypeScript compilation verified. | Passing |

---

## 2. Identified Audit Vulnerabilities & Problems

### P0-1: Deceptive AI & Confidence Claims
- **Problem:** Rule/regex parser claimed to be an "LLM → Deterministic Gate", hardcoded fake `confidence=0.98`, and displayed "Natural Language Intent (LLM)" in the UI without real LLM grounding.
- **Remedy:** Introduce a clean `InterpreterProvider` abstraction (`RuleBasedInterpreter` + optional strictly grounded LLM provider). Honestly label parser as "Rule-based natural language interpreter". Remove all fake confidence scores.

### P0-2: Intent Parser Ambiguity & Fragility
- **Problem:** Regex fails on edge cases like "Buy 2 bitcoin" (treated as $2 USD), ambiguous multi-leg prompts ("Buy $500 BTC and sell $200 ETH"), negations ("Don't buy BTC"), scientific notation (`1e3`), and missing units.
- **Remedy:** Implement robust token/grammar-based parsing with strict validation, prompt length caps, unit ambiguity detection, and structured clarification requests instead of silent execution.

### P0-3: Fabricated Financial Metrics
- **Problem:** Hardcoded `pnl_24h_pct = 1.85 / -0.42 / 3.12` in `portfolio_service.py`, hardcoded token prices in `risk_engine.py`, and `source = "TRUE_MARKETS_UAT"` badge rendered even when credentials are missing.
- **Remedy:** Eliminate fake 24h P&L. Use a single source of truth for pricing (`QuoteService` / `settings.SUPPORTED_ASSETS`). Truthfully label demo data as "Demo · Simulated". Render "True Markets UAT" only when real credentials authenticate. Explicitly label fees as "Not modelled in demo".

### P0-4: Shared Demo Session & Reset Blast Radius
- **Problem:** Single hardcoded user `demo-user-1` shared by all visitors. Resetting the demo nuked other concurrent reviewers' state. Destructive GET endpoints (`GET /reset`, `GET /system/reset-demo`) allowed accidental resets.
- **Remedy:** Implement per-visitor session isolation via `X-Session-ID` header. Scope portfolios, proposals, orders, and audits by session ID. Deprecate and remove GET reset routes in favor of `POST /api/session/reset`.

### P0-5: Financial Precision & State Machine Concurrency
- **Problem:** Float math used for money arithmetic (`float` instead of `Decimal`). Non-atomic proposal status updates permitted concurrent double-confirmation race conditions.
- **Remedy:** Use `Decimal` precision for balances, notional values, and exposure math. Use atomic SQL transitions (`UPDATE trade_proposals SET status = 'CONFIRMING' WHERE id = ? AND status = 'PENDING_CONFIRMATION'`) and enforce a strict non-reversible order state machine (`PENDING_CONFIRMATION` -> `CONFIRMED` -> `SUBMITTED` -> `PENDING_EXECUTION` -> `FILLED`).

### P0-6: Information Architecture & Redundancy
- **Problem:** Competing `/app` and `/app/trade` routes. Redundant landing page sections.
- **Remedy:** Consolidate `/app` as the single primary Trade Desk and redirect `/app/trade` -> `/app`. Tighten landing page to 5 purposeful sections highlighting the core promise.

### P0-7: True Markets Integration Truthfulness
- **Problem:** Adapter code exists in `true_markets_client.py` but lacked runtime configuration health checks and truthful degradation to Demo Mode when UAT credentials are unset.
- **Remedy:** Keep adapter strictly isolated. Check credentials dynamically. If unconfigured, clearly display "UAT not configured · Demo Mode active" with zero fabricated quotes or orders.

### P0-8: Docker & Tooling Build Readiness
- **Problem:** `next.config.ts` lacked `output: "standalone"` expected by `frontend/Dockerfile`. Missing ESLint config file causing non-interactive linting uncertainty.
- **Remedy:** Configure standalone Next.js build, add `eslint.config.mjs`, and organize development workflow files into `docs/internal/`.

---

## 3. Planned Implementation Phases

1. **Phase 1: Correctness + Honesty**
   - InterpreterProvider architecture with safe rule-based interpreter & clarification responses.
   - Elimination of fake financial data (P&L, fake confidence, fake sources).
   - Session isolation (`X-Session-ID`) & secure atomic `POST /api/session/reset`.
   - Money correctness with `Decimal` and atomic proposal claiming.
2. **Phase 2: Core Trade Flow**
   - Single Trade Desk at `/app` (redirect `/app/trade`).
   - Grounded "You said" -> "We understood" preview.
3. **Phase 3: Trade Review as Hero**
   - Verdict, intent comparison, TTL countdown with active refresh, WARN deliberate acknowledgement ("I understand this warning"), computed BLOCK safe amounts, honest fee labeling, truthful lifecycle steps.
4. **Phase 4: Premium UI/UX & Landing Page**
   - 5-section high-converting landing page.
   - Enhanced typography, responsive layouts (390px, 768px, 1440px), focus states, loading/error states.
5. **Phase 5: True Markets Adapter & Status Verification**
   - Truthful adapter status badge, quote and order handling.
6. **Phase 6: Security, Next.js Hardening & Tooling**
   - ESLint configuration, Next.js standalone build, sanitized logging.
7. **Phase 7: Test Expansion & Browser QA**
   - Comprehensive table-driven backend tests (intent, risk boundaries, atomic double-confirm, session isolation, TM stub).
8. **Phase 8: Final Polish & Documentation**
   - Clean up repo, archive workflow prompts to `docs/internal/`, rewrite production README.md.
