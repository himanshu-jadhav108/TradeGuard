# Security

- Secrets backend-only.
- Never expose API keys, signer private keys, JWTs, or raw credential files to Next.js.
- Never store secrets in SQLite.
- Never send secrets to the LLM.
- Validate all LLM output with Pydantic.
- Never allow arbitrary tool names/URLs from the model.
- Use allowlisted assets and order types.
- Enforce server-side maximum notional.
- Require explicit user confirmation.
- Use an idempotency/order-state strategy.
- Treat execute as non-idempotent from our perspective: if uncertain, query status before retry.
- Redact secrets from logs.
