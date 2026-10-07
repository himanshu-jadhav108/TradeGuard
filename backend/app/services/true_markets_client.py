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
        signer_key: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.TM_API_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.TM_API_KEY
        self.org_user_id = org_user_id or settings.TM_ORGANIZATION_USER_ID
        self.signer_key_path = signer_key_path or settings.TM_SIGNER_KEY_PATH
        self.signer_key = signer_key
        self._auth_token: Optional[str] = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.org_user_id)

    def get_signer_key(self) -> Optional[str]:
        if self.signer_key:
            return self.signer_key
        if self.signer_key_path:
            try:
                import os
                if os.path.exists(self.signer_key_path):
                    with open(self.signer_key_path, "r", encoding="utf-8") as f:
                        return f.read().strip()
            except Exception as e:
                logger.warning("Could not read signer key from %s: %s", self.signer_key_path, e)
        return None

    def _get_auth_url(self) -> str:
        """
        Derives auth URL without doubling /v1 or leaking /gateway into the auth endpoint.
        Per .internal-docs/workflow/03_TRUE_MARKETS_INTEGRATION.md: POST /v1/auth/api-key/token
        """
        url = self.base_url
        if url.endswith("/gateway"):
            url = url[:-len("/gateway")]
        if url.endswith("/v1"):
            return f"{url}/auth/api-key/token"
        return f"{url}/v1/auth/api-key/token"

    async def authenticate(self) -> str:
        """
        Retrieves auth token using organization API key via POST /v1/auth/api-key/token
        """
        if not self.api_key:
            raise TrueMarketsClientError("TM_API_KEY is not configured.", status_code=401, error_code="MISSING_API_KEY")

        url = self._get_auth_url()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json={"api_key": self.api_key})
                if res.status_code == 200:
                    data = res.json()
                    self._auth_token = data.get("token") or data.get("access_token")
                    return self._auth_token or ""
                else:
                    logger.warning("True Markets auth failed: HTTP %s", res.status_code)
                    raise TrueMarketsClientError(
                        f"Authentication failed: HTTP {res.status_code}",
                        status_code=res.status_code,
                        error_code="AUTH_FAILED",
                    )
        except httpx.TimeoutException as exc:
            logger.error("Timeout during True Markets authentication")
            raise TrueMarketsClientError("Gateway authentication timeout", status_code=504, error_code="GATEWAY_TIMEOUT")
        except httpx.RequestError as exc:
            logger.error("Network error during True Markets authentication: %s", type(exc).__name__)
            raise TrueMarketsClientError("Gateway connection error", status_code=503, error_code="GATEWAY_UNAVAILABLE")

    async def _ensure_authenticated(self) -> None:
        """Ensures auth token is present before dispatching gateway requests."""
        if not self._auth_token and self.api_key:
            await self.authenticate()

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

        await self._ensure_authenticated()

        url = f"{self.base_url}/quotes"
        payload = {
            "pair": pair,
            "side": side.upper(),
            "amount": amount,
        }
        headers = self._get_headers(user_id)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    logger.warning("True Markets quote failed: HTTP %s", res.status_code)
                    raise TrueMarketsClientError(f"Upstream quote request failed: HTTP {res.status_code}", status_code=res.status_code)
                return res.json()
        except httpx.TimeoutException:
            logger.error("Gateway quote timeout")
            raise TrueMarketsClientError("Gateway quote timeout", status_code=504, error_code="GATEWAY_TIMEOUT")
        except httpx.RequestError as exc:
            logger.error("Network error during True Markets quote request: %s", type(exc).__name__)
            raise TrueMarketsClientError("Gateway connection error", status_code=503, error_code="GATEWAY_UNAVAILABLE")

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

        await self._ensure_authenticated()

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
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code not in (200, 201):
                    logger.warning("True Markets order creation failed: HTTP %s", res.status_code)
                    raise TrueMarketsClientError(f"Upstream order creation failed: HTTP {res.status_code}", status_code=res.status_code)
                return res.json()
        except httpx.TimeoutException:
            logger.error("Gateway order creation timeout")
            raise TrueMarketsClientError("Gateway order creation timeout", status_code=504, error_code="GATEWAY_TIMEOUT")
        except httpx.RequestError as exc:
            logger.error("Network error during True Markets order creation: %s", type(exc).__name__)
            raise TrueMarketsClientError("Gateway connection error", status_code=503, error_code="GATEWAY_UNAVAILABLE")

    async def execute_order(self, order_id: str, signature: Optional[str] = None, user_id: str = "demo-user-1") -> Dict[str, Any]:
        """
        POST /orders/{id}/execute
        Never blindly retry this operation.
        """
        if not self.is_configured():
            raise TrueMarketsClientError("True Markets credentials not configured.", status_code=400)

        await self._ensure_authenticated()

        url = f"{self.base_url}/orders/{order_id}/execute"
        payload = {}
        sig = signature or self.get_signer_key()
        if sig:
            payload["signature"] = sig

        headers = self._get_headers(user_id)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code not in (200, 202):
                    logger.warning("True Markets order execution failed: HTTP %s", res.status_code)
                    raise TrueMarketsClientError(f"Upstream order execution failed: HTTP {res.status_code}", status_code=res.status_code)
                return res.json()
        except httpx.TimeoutException:
            logger.error("Gateway execute timeout")
            raise TrueMarketsClientError("Gateway execute timeout", status_code=504, error_code="GATEWAY_TIMEOUT")
        except httpx.RequestError as exc:
            logger.error("Network error during True Markets order execution: %s", type(exc).__name__)
            raise TrueMarketsClientError("Gateway connection error", status_code=503, error_code="GATEWAY_UNAVAILABLE")

    async def get_order_status(self, order_id: str, user_id: str = "demo-user-1") -> Dict[str, Any]:
        """
        GET /orders/{id}/status
        """
        if not self.is_configured():
            raise TrueMarketsClientError("True Markets credentials not configured.", status_code=400)

        await self._ensure_authenticated()

        url = f"{self.base_url}/orders/{order_id}/status"
        headers = self._get_headers(user_id)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code != 200:
                    logger.warning("True Markets status inquiry failed: HTTP %s", res.status_code)
                    raise TrueMarketsClientError(f"Upstream status check failed: HTTP {res.status_code}", status_code=res.status_code)
                return res.json()
        except httpx.TimeoutException as exc:
            logger.error("Gateway status inquiry timeout: %s", str(exc))
            raise TrueMarketsClientError("Gateway status inquiry timeout", status_code=504, error_code="GATEWAY_TIMEOUT")
        except httpx.RequestError as exc:
            logger.error("Network error during True Markets status inquiry: %s", str(exc))
            raise TrueMarketsClientError(f"Gateway connection error: {str(exc)}", status_code=503, error_code="GATEWAY_UNAVAILABLE")
