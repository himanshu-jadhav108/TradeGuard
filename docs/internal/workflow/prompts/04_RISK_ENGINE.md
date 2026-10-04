# Antigravity Prompt 04 — Risk Engine

Implement deterministic risk checks.

Minimum:
- valid asset
- positive quantity
- max notional
- balance sufficiency
- concentration threshold
- portfolio impact
- quote staleness

Return machine-readable checks with severity:
PASS / WARN / BLOCK.

The LLM cannot override a BLOCK.
