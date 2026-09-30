# UAT Setup

Antigravity must not ask the developer to paste secrets into source files or chat.

Use environment variables / deployment secrets.

Suggested variables:
- TM_ENV=uat
- TM_KEY_FILE=/run/secrets/...
- TM_API_BASE_URL=https://api.uat.truemarkets.co/v1/gateway
- TM_ORGANIZATION_USER_ID=...
- TM_SIGNER_KEY_PATH=...

Do not commit any key file.

Before implementation:
1. Confirm the hackathon account has Gateway/UAT access.
2. Confirm whether a test user can be created.
3. Confirm wallet/account IDs.
4. Confirm at least one supported asset.
5. Test quote only.
6. Test balance.
7. Only then test order creation.
8. Execute only in UAT with a test user.
