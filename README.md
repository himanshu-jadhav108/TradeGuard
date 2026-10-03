# TradeGuard

> **Think before you trade.**  
> AI-assisted financial execution layer with live market context, deterministic risk checks, and explicit human control.

Built for the **True Markets “Build the Next Wealth App”** challenge.

---

## 1. What TradeGuard Is

TradeGuard is a wealth-management execution layer designed to eliminate accidental, risky, or hallucinated trades in AI-assisted finance.

When a user provides natural language intent (e.g., *"Buy $500 of BTC"*):
1. **Understands Intent:** Parses structured parameters (`asset`, `side`, `amount`, `amount_type`) and validates against schemas.
2. **Retrieves Market Context:** Pulls quotes with tight spreads, timestamps, and 30-second TTL freshness windows.
3. **Applies Deterministic Risk Controls:** Evaluates balances, asset allowlists, maximum notional ceilings, and portfolio concentration limits server-side.
4. **Presents Explainable Trade Review:** Renders a transparent, human-readable card highlighting before/after portfolio exposure and deterministic check badges (`PASS`, `WARN`, `BLOCK`).
5. **Requires Explicit Human Confirmation:** The LLM cannot execute trades directly. Only user authorization triggers the order lifecycle.
6. **Executes & Audits:** Dispatches order to True Markets Gateway (or deterministic simulator in DEMO mode), updates portfolio balances, and appends an immutable audit event.

---

## 2. Architecture

```text
TradeGuard Architecture
═════════════════════════════════════════════════════════════════════
  [ User Browser ]
        │
        ▼ (HTTP / JSON Domain Models)
  [ Next.js Frontend ] (TypeScript, Tailwind, Recharts, Apple/Linear Polish)
        │
        ▼ (Strict REST Contract: /api/*)
  [ FastAPI Backend ] (Python 3.13 in venv)
        │
        ├── Intent Service (Structured extraction & Pydantic validation)
        ├── Quote Service (Live & deterministic pricing with 30s TTL)
        ├── Deterministic Risk Engine (Authoritative balance & limits)
        ├── Proposal Service (Explainable impact calculation)
        ├── Order Lifecycle Service (State machine & confirmation gate)
        ├── Audit Service (Immutable chronological event log)
        └── Database (SQLite repository / tradeguard.db)
        │
        ▼
  [ True Markets Adapter ] (true_markets_client.py)
        │
        ▼
  [ True Markets Gateway ] (https://api.uat.truemarkets.co/v1/gateway)
        ├── POST /v1/auth/api-key/token
        ├── POST /quotes
        ├── POST /orders
        ├── POST /orders/{id}/execute
        └── GET  /orders/{id}/status
```

---

## 3. Demo Mode (Zero Credentials Required)

TradeGuard is designed to be fully testable and auditable out-of-the-box without requiring live or sandbox API credentials.

- Clearly labeled: `DEMO MODE · Simulated account`.
- Pre-seeded with `$10,000.00 USDC` liquid cash and realistic initial positions (`0.15 BTC`, `1.50 ETH`, `10.0 SOL`).
- Deterministic quote engine with realistic institutional spreads (0.05%) and live TTL expiration bars.
- Full simulated order lifecycle: order ID assignment (`tm-sim-*`), state transitions (`PENDING_CONFIRMATION` → `FILLED`), balance debits, asset credits, and verifiable audit events.
- **1-Click Reset:** A dedicated *"Reset Demo"* button in the header allows reviewers to restore initial seed balances instantly.

---

## 4. True Markets Integration

TradeGuard isolates all external provider communication within `backend/app/services/true_markets_client.py`.

### Documented Endpoints
- **UAT Gateway Base:** `https://api.uat.truemarkets.co/v1/gateway`
- **Production Gateway Base:** `https://api.truemarkets.co/v1/gateway`
- **Auth Endpoint:** `POST /v1/auth/api-key/token`
- **Gateway Endpoints:**
  - `POST /quotes`
  - `POST /orders`
  - `POST /orders/{id}/execute`
  - `GET /orders/{id}/status`
  - `GET /balances`

### Authentication Model
- Organization API key authenticates the server application via bearer token.
- User-scoped calls include `TM-On-Behalf-Of: <user_id>`.
- Unsigned transaction payloads returned during order creation are signed server-side by the dedicated signer key prior to `/orders/{id}/execute`.
- True Markets credentials are strictly backend-only and never reach the client bundle.

---

## 5. UAT Setup

To connect TradeGuard to the live True Markets UAT sandbox:

1. Obtain your Organization API key and Signer Key from the True Markets developer portal.
2. In `backend/.env`, set:
   ```env
   TM_ENV=uat
   TM_API_BASE_URL=https://api.uat.truemarkets.co/v1/gateway
   TM_API_KEY=<your-organization-api-key>
   TM_ORGANIZATION_USER_ID=<your-test-user-id>
   TM_SIGNER_KEY_PATH=/path/to/signer_key.pem
   ```
3. Restart the backend service. TradeGuard will automatically route quoting and execution through the True Markets Gateway.

---

## 6. Environment Variables

### Backend (`backend/.env`)
| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment (`development`, `production`, `test`) |
| `DEBUG` | `True` | FastAPI debug mode |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |
| `TM_ENV` | `demo` | Execution mode: `demo` (simulated) or `uat` (True Markets) |
| `TM_API_BASE_URL` | `https://api.uat.truemarkets.co/v1/gateway` | Gateway base URL |
| `TM_API_KEY` | `""` | True Markets organization API key |
| `TM_ORGANIZATION_USER_ID` | `""` | User context for `TM-On-Behalf-Of` |
| `TM_SIGNER_KEY_PATH` | `""` | Local path to private signer key |
| `MAX_NOTIONAL_USD` | `25000.0` | Server-enforced order ceiling (BLOCK trigger) |
| `CONCENTRATION_THRESHOLD_PCT` | `0.40` | Concentration warning limit (WARN trigger) |
| `QUOTE_TTL_SECONDS` | `30` | Quote freshness time-to-live |

### Frontend (`frontend/.env.local`)
| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000/api` | TradeGuard backend API base URL |

---

## 7. Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+ & npm

### Backend Setup (using Python virtual environment `venv`)
```bash
# Navigate to backend directory
cd backend

# Create dedicated virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server on port 8000
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Next.js development server on port 3000
npm run dev
```

Visit `http://localhost:3000` to interact with TradeGuard.

---

## 8. Automated Testing

All tests run deterministically without external dependencies.

```bash
# Run backend pytest suite (in backend/.venv)
cd backend
.venv\Scripts\pytest -v

# Run frontend type checking
cd ../frontend
npm run typecheck

# Run frontend production build
npm run build
```

---

## 9. Deployment

### Docker Compose (All-in-One)
```bash
docker compose up --build
```

### Cloud Split Deployment
- **Frontend:** Vercel (Set `NEXT_PUBLIC_API_URL` to backend domain).
- **Backend:** Render / Railway / Fly.io (Deploy `backend/Dockerfile` with environment variables).

---

## 10. Security & Execution Boundaries

- **Zero Autonomous Execution:** The LLM only parses natural language strings. It has zero authority to submit orders.
- **Deterministic Server-Side Controls:** The Python backend calculates authoritative numbers. If a risk check results in `BLOCK`, the execution API rejects the transaction with code `400`.
- **Quote Freshness Guarantee:** Quotes expire after 30 seconds. Stale quotes cannot be confirmed.
- **Secrets Isolation:** No credentials, private keys, or API tokens are ever delivered to the browser or stored in Git.

---

## 11. Limitations & Hackathon Boundaries

- Production funds are strictly disabled by default.
- Assets are restricted to the allowlist (`BTC`, `ETH`, `SOL`, `USDC`).
- Speculative features (autonomous trading bots, price forecasting, copy trading) are intentionally excluded to maintain fintech-grade reliability.

---

## 12. Demo Script & Judge Instructions

1. Open `http://localhost:3000`.
2. Observe the premium landing page, design tokens, and value proposition (*"Think before you trade"*).
3. Under **Live Interactive Preview**, click the **“Buy $500 of BTC”** 1-click test button.
4. Review the generated **Trade Review Card**:
   - Verify the calculated quantity: `~0.005784 BTC`
   - Inspect the live quote snapshot and spread
   - Observe the projected portfolio allocation change
   - Review the 5 deterministic risk checks (`PASS` / `WARN`)
   - Read the explainable factual summary
5. Click **[ Confirm Trade ]**.
6. Observe the immediate transition to `FILLED` state with an assigned order reference.
7. Click **Launch App** or navigate to **Overview** / **Portfolio** to verify that cash decreased from `$10,000.00` to `$9,500.00` and BTC holdings increased.
8. Navigate to **Activity** to review the cryptographic chronological audit stream.
9. Test the risk engine guardrails: Try typing `Buy $35,000 of BTC` or `Buy $18,000 of SOL` to observe the system physically block execution with clear visual feedback.
