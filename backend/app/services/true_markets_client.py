import logging
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("TradeGuard.TrueMarkets")


class TrueMarketsClientError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class TrueMarketsClient:
    """
    Isolated True Markets Gateway API Client Adapter.
    Adheres strictly to documented True Markets retail gateway contracts:
      - POST /v1/auth/api-key/token
      - POST /quotes
      - POST /orders
      - POST /orders/{id}/execute
      - GET  /orders/{id}/status
      - GET  /balances
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        org_user_id: Optional[str] = None,
        signer_key_path: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.TM_API_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.TM_API_KEY
        self.org_user_id = org_user_id or settings.TM_ORGANIZATION_USER_ID
        self.signer_key_path = signer_key_path or settings.TM_SIGNER_KEY_PATH
        self._auth_token: Optional[str] = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.org_user_id)

    async def authenticate(self) -> str:
        """
        Retrieves auth token using organization API key via POST /v1/auth/api-key/token
        """
        if not self.api_key:
            raise TrueMarketsClientError("TM_API_KEY is not configured.", status_code=401, error_code="MISSING_API_KEY")

        url = f"{self.base_url}/v1/auth/api-key/token"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json={"api_key": self.api_key})
                if res.status_code == 200:
                    data = res.json()
                    self._auth_token = data.get("token") or data.get("access_token")
                    return self._auth_token or ""
                else:
                    logger.warning("True Markets auth failed: %s %s", res.status_code, res.text)
                    raise TrueMarketsClientError(
                        f"Authentication failed: {res.status_code}",
                        status_code=res.status_code,
                        error_code="AUTH_FAILED"
                    )
        except httpx.RequestError as exc:
            logger.error("Network error during True Markets authentication: %s", str(exc))
            raise TrueMarketsClientError(f"Gateway connection error: {str(exc)}", status_code=503, error_code="GATEWAY_UNAVAILABLE")

    def _get_headers(self, user_id: str) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "TM-On-Behalf-Of": user_id,
        }
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def get_quote(self, pair: str, side: str, amount: float, user_id: str = "demo-user-1") -> Dict[str, Any]:
        """
        POST /quotes
        """
        if not self.is_configured():
            raise TrueMarketsClientError("True Markets credentials not configured. Please use DEMO mode.", status_code=400)

        url = f"{self.base_url}/quotes"
        payload = {
            "pair": pair,
            "side": side.upper(),
            "amount": amount,
        }
        headers = self._get_headers(user_id)

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code != 200:
                raise TrueMarketsClientError(f"Quote error: {res.text}", status_code=res.status_code)
            return res.json()

    async def create_order(
        self,
        pair: str,
        side: str,
        quantity: float,
        quote_id: Optional[str] = None,
        user_id: str = "demo-user-1",
    ) -> Dict[str, Any]:
        """
        POST /orders
        """
        if not self.is_configured():
            raise TrueMarketsClientError("True Markets credentials not configured.", status_code=400)

        url = f"{self.base_url}/orders"
        payload = {
            "pair": pair,
            "side": side.upper(),
            "quantity": quantity,
            "type": "MARKET",
        }
        if quote_id:
            payload["quote_id"] = quote_id

        headers = self._get_headers(user_id)
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code not in (200, 201):
                raise TrueMarketsClientError(f"Order creation failed: {res.text}", status_code=res.status_code)
            return res.json()

    async def execute_order(self, order_id: str, signature: Optional[str] = None, user_id: str = "demo-user-1") -> Dict[str, Any]:
        """
        POST /orders/{id}/execute
        Never blindly retry this operation.
        """
        if not self.is_configured():
            raise TrueMarketsClientError("True Markets credentials not configured.", status_code=400)

        url = f"{self.base_url}/orders/{order_id}/execute"
        payload = {}
        if signature:
            payload["signature"] = signature

        headers = self._get_headers(user_id)
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code not in (200, 202):
                raise TrueMarketsClientError(f"Execution failed: {res.text}", status_code=res.status_code)
            return res.json()

    async def get_order_status(self, order_id: str, user_id: str = "demo-user-1") -> Dict[str, Any]:
        """
        GET /orders/{id}/status
        """
        if not self.is_configured():
            raise TrueMarketsClientError("True Markets credentials not configured.", status_code=400)

        url = f"{self.base_url}/orders/{order_id}/status"
        headers = self._get_headers(user_id)
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                raise TrueMarketsClientError(f"Status inquiry failed: {res.text}", status_code=res.status_code)
            return res.json()
