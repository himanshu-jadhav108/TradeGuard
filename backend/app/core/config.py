from typing import List, Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "TradeGuard API"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Allowed CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    # True Markets Integration
    # "demo" = internal deterministic simulator; "uat" = True Markets UAT Gateway
    TM_ENV: str = "demo"
    TM_API_BASE_URL: str = "https://api.uat.truemarkets.co/v1/gateway"
    TM_ORGANIZATION_USER_ID: Optional[str] = None
    TM_API_KEY: Optional[str] = None
    TM_SIGNER_KEY_PATH: Optional[str] = None

    # Risk Controls
    MAX_NOTIONAL_USD: float = 25000.0
    CONCENTRATION_THRESHOLD_PCT: float = 0.40  # 40% portfolio warning
    QUOTE_TTL_SECONDS: int = 30

    # Supported Assets Allowlist
    SUPPORTED_ASSETS: List[str] = ["BTC", "ETH", "SOL", "USDC"]


settings = Settings()
