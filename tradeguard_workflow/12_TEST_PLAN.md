# Test Plan

## Unit
- intent schema validation
- risk thresholds
- portfolio calculations
- quote staleness
- asset allowlist
- order state transitions

## Integration
- True Markets adapter mocked
- UAT quote
- UAT balance
- UAT order creation
- UAT status

## E2E
1. Open landing page.
2. Enter buy request.
3. See proposal.
4. See risk checks.
5. Confirm.
6. See resulting order status.
7. See audit activity.

## Security tests
- no secret in client bundle
- no secret in logs
- unauthorized confirm rejected
- malformed LLM output rejected
- unsupported asset rejected

All existing tests must continue to pass.
