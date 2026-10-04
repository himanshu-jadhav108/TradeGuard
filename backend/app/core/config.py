from typing import List, Optional
from pydantic import ConfigDict, model_validator
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

    @model_validator(mode="before")
    @classmethod
    def parse_cors_origins(cls, data):
        if isinstance(data, dict):
            cors = data.get("CORS_ORIGINS")
            if isinstance(cors, str):
                cors_str = cors.strip()
                if cors_str.startswith("[") and cors_str.endswith("]"):
                    try:
                        import json
                        data["CORS_ORIGINS"] = json.loads(cors_str)
                    except Exception:
                        data["CORS_ORIGINS"] = [o.strip().strip("'\"") for o in cors_str.strip("[]").split(",") if o.strip()]
                else:
                    data["CORS_ORIGINS"] = [o.strip().strip("'\"") for o in cors_str.split(",") if o.strip()]
        return data

    @model_validator(mode="after")
    def enforce_production_security(self):
        if self.APP_ENV == "production":
            self.DEBUG = False
        return self


settings = Settings()
