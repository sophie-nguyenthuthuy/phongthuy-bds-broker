"""Cấu hình ứng dụng — đọc từ env, validate bằng pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Env ──────────────────────────────────────────────────────
    env: Literal["dev", "staging", "prod", "test"] = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: SecretStr = Field(min_length=32)
    api_cors_origins: str = "http://localhost:3000"

    # ─── DB / Redis ──────────────────────────────────────────────
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    # ─── Storage ─────────────────────────────────────────────────
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_path: str = "./storage"
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_access_key: SecretStr | None = None
    s3_secret_key: SecretStr | None = None

    # ─── DLCN (NĐ 13/2023/NĐ-CP) ─────────────────────────────────
    dlcn_retention_days: int = 90
    dlcn_encryption_key: SecretStr = Field(
        description="Fernet key (32-byte base64). Required in prod.",
    )

    # ─── JWT ─────────────────────────────────────────────────────
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 60
    jwt_refresh_ttl_days: int = 14

    # ─── Billing ─────────────────────────────────────────────────
    vnpay_tmn_code: str = ""
    vnpay_hash_secret: SecretStr = SecretStr("")
    vnpay_api_url: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    vnpay_return_url: str = "http://localhost:3000/billing/vnpay-return"
    momo_partner_code: str = ""
    momo_access_key: str = ""
    momo_secret_key: SecretStr = SecretStr("")

    # ─── OCR ─────────────────────────────────────────────────────
    ocr_backend: Literal["paddleocr", "google_vision", "mock"] = "mock"
    paddleocr_lang: str = "vi"
    google_application_credentials: str | None = None

    # ─── Observability ───────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"
    sentry_dsn: str | None = None

    @field_validator("api_cors_origins")
    @classmethod
    def split_cors(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lấy settings (singleton, cache cho process)."""
    return Settings()  # type: ignore[call-arg]
