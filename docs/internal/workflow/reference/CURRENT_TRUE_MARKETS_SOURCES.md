# Current True Markets sources verified during workflow creation

- Gateway: https://docs.truemarkets.co/gateway/
- Gateway API: https://docs.truemarkets.co/apis/retail/true-markets-gateway-api/
- API reference: https://docs.truemarkets.co/api/
- SDK quickstart: https://docs.truemarkets.co/sdks/quickstart/
- API keys: https://docs.truemarkets.co/developer-resources/api-keys/
- Authentication: https://docs.truemarkets.co/developer-resources/authentication/
- Errors: https://docs.truemarkets.co/developer-resources/errors/
- Public market-data WebSocket: https://docs.truemarkets.co/api/websocket/market-data/

Verified points:
- UAT Gateway base is https://api.uat.truemarkets.co/v1/gateway
- Production Gateway base is https://api.truemarkets.co/v1/gateway
- Gateway uses organization API key + signer key.
- Gateway user-scoped requests use TM-On-Behalf-Of.
- Quotes are separate from order execution.
- Gateway order lifecycle includes create → sign payloads when required → execute → status.
- UAT may require VPN/allowlisting for some integrations.
- Private keys must remain out of source control/chat.
