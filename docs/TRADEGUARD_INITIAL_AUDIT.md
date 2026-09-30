# TradeGuard — Initial Workspace & Architecture Audit

**Date:** 2026-10-03  
**Status:** Audit Complete · Ready for Phase 1 Foundation  
**Branch:** `feat/tradeguard`

---

## 1. Environment & Tooling Audit

- **Operating System:** Windows 10/11 (PowerShell environment)
- **Node.js Version:** `v24.13.1`
- **npm Version:** `11.8.0`
- **Python Version:** `3.13.11` (Virtual environment `venv` explicitly mandated for backend)
- **Git Version:** `2.50.1.windows.1` (Git uninitialized in current workspace; needs initialization and branch `feat/tradeguard`)
- **Docker Version:** `Docker version 29.4.3, build 055a478`
- **Package Managers:** `npm` (primary for frontend), `pip` within dedicated Python `venv` (backend)

---

## 2. Existing Workspace Files & Assets

```text
d:\Projects\TradeGuard\
└── tradeguard_workflow/
    ├── 00_START_HERE.md
    ├── 01_PRODUCT_BRIEF.md
    ├── 02_ARCHITECTURE.md
    ├── 03_TRUE_MARKETS_INTEGRATION.md
    ├── 04_UAT_SETUP.md
    ├── 05_SECURITY.md
    ├── 06_UI_UX_SYSTEM.md
    ├── 07_LANDING_PAGE_SPEC.md
    ├── 08_TRADE_REVIEW_SPEC.md
    ├── 09_DEMO_MODE.md
    ├── 10_DATABASE_SPEC.md
    ├── 11_API_CONTRACTS.md
    ├── 12_TEST_PLAN.md
    ├── 13_DEPLOYMENT.md
    ├── 14_VIDEO_SCRIPT.md
    ├── 15_ACCEPTANCE_CRITERIA.md
    ├── 16_ANTIGRAVITY_RULES.md
    ├── 17_WORKFLOW.md
    ├── 18_FINAL_AUDIT.md
    ├── README.md
    ├── branding/
    │   ├── favicon.png
    │   ├── tradeguard-logo.png
    │   └── tradeguard-logo.svg
    ├── prompts/
    │   ├── 01_AUDIT_ONLY.md ... 10_FINAL_AUDIT.md
    └── reference/
        ├── CURRENT_TRUE_MARKETS_SOURCES.md
        └── UPLOADED_REFERENCE_REPO.md
```

### Branding Assets
- `tradeguard-logo.svg`: Vector shield with modern guard glyph, cleanly styled.
- `tradeguard-logo.png` & `favicon.png`: High-resolution graphic assets ready for Next.js web application integration.
- Brand Name: **TradeGuard**
- Brand Tagline: **Think before you trade.**

---

## 3. Reusable Code vs. Irrelevant Code

### Reusable Concepts (from FinAlly reference notes)
- Domain patterns for market quote caching, time-to-live expiration checks, and seed prices for deterministic simulation.
- Simulation state machines for order lifecycle (`PENDING` → `SUBMITTED` → `FILLED` / `FAILED`).

### Irrelevant / Excluded Functionality (Explicitly Out of Scope)
- No autonomous trading bots or auto-execution loops.
- No price prediction, technical indicators overload, backtesting, or reinforcement learning.
- No copy/social trading or complex multi-agent layers.
- FinAlly's incomplete legacy files are not needed; TradeGuard is built cleanly from scratch using the designated architecture.

---

## 4. Missing Application Layers (To Be Built)

1. **Frontend (`frontend/`):**
   - Next.js (App Router) + TypeScript + Tailwind CSS
   - Curated Theme Design Token System (Light: warm off-white canvas, graphite text, restrained emerald; Dark: near-black graphite canvas, charcoal surfaces, soft-white text, restrained emerald)
   - Landing Page (Hero with live product preview, 4-step workflow: Understand → Check → Confirm → Execute, Security & Control, Demo Video embed, CTA)
   - App Shell & Navigation (Overview, Trade Composer, Portfolio, Activity / Audit Log, Settings, Mode Switch: DEMO vs UAT)
   - The Signature Trade Review Card (live quote, spread/staleness, portfolio impact before/after, deterministic risk checks: PASS / WARN / BLOCK, concise explainable AI justification, explicit Human Confirmation gate)
   - Recharts visual portfolio allocation and exposure cards

2. **Backend (`backend/` with Python `venv`):**
   - FastAPI application with CORS restricted to frontend origin
   - Pydantic models for structured intent, quote snapshots, risk evaluations, trade proposals, orders, and audit events
   - **Intent Service:** Structured parsing with deterministic fallback parsing + LLM extraction adapter with strict schema enforcement
   - **Deterministic Risk Engine:** Authoritative checks (asset allowlist, valid side/positive quantity, balance sufficiency, max order notional limit, portfolio concentration threshold, quote freshness/staleness)
   - **Quote Service:** Deterministic simulated quotes for DEMO mode; True Markets Gateway quotes for UAT
   - **Trade Proposal Service:** Coordinates intent, quote, and risk engine to generate an immutable, explainable proposal
   - **True Markets Client Adapter (`true_markets_client.py`):** Strict boundary wrapper for UAT gateway endpoints (`/v1/auth/api-key/token`, `/quotes`, `/orders`, `/orders/{id}/execute`, `/orders/{id}/status`, balances) with signing payload handling, error normalization, and credential isolation
   - **Order Lifecycle & Audit Service:** Manages states (`PENDING_CONFIRMATION`, `SUBMITTED`, `PENDING_EXECUTION`, `FILLED`, `CANCELLED`, `REJECTED`), updates portfolio positions, and appends immutable audit events
   - **Database Storage:** SQLite repository interface (`sqlite3` / SQLAlchemy) for local/demo persistence (users, portfolios, positions, proposals, orders, audit_events)

---

## 5. Proposed Architecture

```text
TradeGuard
│
├── frontend/                     # Next.js (App Router) + TypeScript + Tailwind CSS
│   ├── public/branding/          # TradeGuard logos and favicons
│   ├── src/
│   │   ├── app/                  # Next.js App Router (Landing, /app routes: overview, trade, portfolio, activity)
│   │   ├── components/           # UI Primitives, Navigation, TradeReviewCard, PortfolioCharts, AuditTimeline
│   │   ├── lib/                  # API client, domain types, theme utilities
│   │   └── styles/               # Design tokens, CSS variables (light & dark)
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/                      # FastAPI + Python 3.13 (in backend/.venv)
│   ├── app/
│   │   ├── api/                  # FastAPI routers: /api/intent, /api/trades, /api/orders, /api/portfolio, /api/activity, /api/health
│   │   ├── core/                 # Config, security, database session, logging
│   │   ├── domain/               # Domain models, enums, schemas (Pydantic)
│   │   ├── services/
│   │   │   ├── intent_service.py # NL intent extraction & Pydantic validation
│   │   │   ├── quote_service.py  # Live & simulated quote feeder
│   │   │   ├── risk_engine.py    # Deterministic checks (PASS/WARN/BLOCK)
│   │   │   ├── proposal_service.py # Trade proposal compilation & explanation
│   │   │   ├── order_service.py  # Order state machine & execution flow
│   │   │   ├── portfolio_service.py # Holdings, exposure, cash calculations
│   │   │   ├── audit_service.py  # Immutable event stream recorder
│   │   │   └── true_markets_client.py # Isolated UAT gateway adapter
│   │   ├── db/                   # SQLite schema, migrations, repository patterns
│   │   └── main.py               # FastAPI entrypoint, middleware, lifespan
│   ├── tests/                    # pytest suite (unit, integration, security, e2e smoke)
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docs/                         # Specifications, audits, deployment guide, video script
├── .gitignore                    # Secrets, .venv, node_modules, sqlite db, logs excluded
└── README.md                     # Comprehensive setup, architecture, demo, and deployment guide
```

---

## 6. Dependency Choices

- **Frontend:**
  - `next`: ^15 / ^14 React framework
  - `react`, `react-dom`
  - `lucide-react`: Clean, restrained fintech iconography
  - `clsx`, `tailwind-merge`: Class composition
  - `recharts`: Crisp, restrained financial charts
  - `tailwindcss`, `postcss`, `autoprefixer`
  - `typescript`, `@types/react`, `@types/node`

- **Backend (Python 3.13 in `venv`):**
  - `fastapi`: Modern async API framework
  - `uvicorn`: ASGI server
  - `pydantic`: Strict schema validation and data parsing
  - `pydantic-settings`: Environment configuration
  - `httpx`: Async HTTP client for external True Markets Gateway calls
  - `pytest`, `pytest-asyncio`: Automated test suites
  - `sqlite3` (built-in standard library) for fast, zero-external-dependency persistence

---

## 7. Implementation Risks & Mitigations

1. **Risk:** True Markets UAT credentials not present in local environment during evaluation.  
   **Mitigation:** Complete, robust DEMO mode runs deterministically without any credentials. True Markets client adapter is fully implemented with realistic mocked UAT contracts and end-to-end unit/integration coverage, ready to connect seamlessly when credentials are provided in `.env`.
2. **Risk:** Non-deterministic LLM behavior breaking trade execution.  
   **Mitigation:** Strict separation of concerns. LLM only extracts structured intent `{ asset, side, amount, amount_type }`. Authoritative numbers (quotes, balances, quantities, risk assessments) are computed strictly by deterministic Python backend services. A `BLOCK` risk result physically cannot be overridden.
3. **Risk:** Accidental credential leak to client or git.  
   **Mitigation:** True Markets credentials reside exclusively in backend environment variables. Frontend only communicates with `/api/*` endpoints consuming TradeGuard domain models. Robust `.gitignore` initialized immediately.

---

## 8. Implementation Sequence

1. **Phase 1 — Foundation:**
   - Initialize git repo and create `feat/tradeguard`
   - Setup Python virtual environment (`backend/.venv`) and install FastAPI dependencies
   - Setup Next.js frontend with Tailwind CSS and theme design tokens
   - Implement backend health check and baseline tests
   - Commit: `chore: initialize TradeGuard foundation`

2. **Phase 2 — Design System & Premium UI:**
   - Install TradeGuard branding assets (logo SVG, PNG, favicon)
   - Build design token system (light + dark mode, high contrast, Apple/Linear aesthetic)
   - Build Landing Page with interactive preview, 4-step workflow, demo video container
   - Build App Shell (Navigation, Overview, Trade, Portfolio, Activity, Settings)
   - Commit: `feat: add premium design system`

3. **Phase 3 — Deterministic Demo Engine & Risk Engine:**
   - Seeded deterministic portfolio, quote simulator (BTC/USDC, ETH/USDC, SOL/USDC)
   - Intent parsing service with structured validation
   - Deterministic risk engine (allowlist, balance, max size, concentration, quote staleness) returning PASS / WARN / BLOCK
   - Commit: `feat: add TradeGuard demo engine` & `feat: add deterministic risk engine`

4. **Phase 4 — Trade Review & Execution Flow:**
   - Signature Trade Review Card with live quote, projected exposure, risk check badges, and explicit human confirmation
   - Simulated order lifecycle and portfolio balance updates
   - Audit trail activity logging
   - Commit: `feat: add trade proposal flow` & `feat: add audit activity`

5. **Phase 5 — True Markets Adapter (UAT Gateway):**
   - Implement `true_markets_client.py` adhering to documented endpoints (`/v1/auth/api-key/token`, `/quotes`, `/orders`, `/orders/{id}/execute`, `/orders/{id}/status`, balances)
   - Safe error handling, backoff, signing payload handling, and status verification
   - Commit: `feat: add True Markets adapter` & `feat: add UAT order lifecycle`

6. **Phase 6 — Testing & Hardening:**
   - Unit tests, integration tests with mocked True Markets, security scans
   - Responsive and visual QA across light and dark modes
   - Commit: `test: add TradeGuard end-to-end coverage`

7. **Phase 7 — Deployment Preparation & Final Audit:**
   - Production builds, Dockerfile / Vercel / Render configs, README documentation
   - Commit: `chore: prepare deployment` & `fix: final audit issues`
   - Produce Final Engineering Report
