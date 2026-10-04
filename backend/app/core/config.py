import json
from typing import List, Optional, Union
from pydantic import ConfigDict, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "TradeGuard API"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Allowed CORS Origins - accepts comma-separated string, JSON array, or list of strings
    CORS_ORIGINS: Union[List[str], str] = [
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
    SUPPORTED_ASSETS: Union[List[str], str] = ["BTC", "ETH", "SOL", "USDC"]

    @field_validator("CORS_ORIGINS", "SUPPORTED_ASSETS", mode="after")
    @classmethod
    def assemble_list_origins(cls, v):
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(o).strip().strip("'\"") for o in parsed if str(o).strip()]
                except Exception:
                    pass
            return [o.strip().strip("'\"") for o in v_str.split(",") if o.strip()]
        return v

    @model_validator(mode="after")
    def enforce_production_security(self):
        if self.APP_ENV == "production":
            self.DEBUG = False
        return self


settings = Settings()
