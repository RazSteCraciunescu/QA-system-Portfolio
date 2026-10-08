from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    gateway_base_url: str
    transformer_url: str
    partner_url: str
    partner_admin_token: str
    worker_poll_seconds: float
    worker_max_attempts: int
    worker_retry_delay_seconds: float
    outbound_timeout_seconds: float
    max_payload_bytes: int
    log_level: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./relayhub.db"),
        gateway_base_url=os.getenv("GATEWAY_BASE_URL", "http://127.0.0.1:8080"),
        transformer_url=os.getenv("TRANSFORMER_URL", "http://127.0.0.1:8082"),
        partner_url=os.getenv("PARTNER_URL", "http://127.0.0.1:8083"),
        partner_admin_token=os.getenv("PARTNER_ADMIN_TOKEN", "local-test-token"),
        worker_poll_seconds=float(os.getenv("WORKER_POLL_SECONDS", "0.25")),
        worker_max_attempts=int(os.getenv("WORKER_MAX_ATTEMPTS", "3")),
        worker_retry_delay_seconds=float(os.getenv("WORKER_RETRY_DELAY_SECONDS", "0.35")),
        outbound_timeout_seconds=float(os.getenv("OUTBOUND_TIMEOUT_SECONDS", "3.0")),
        max_payload_bytes=int(os.getenv("MAX_PAYLOAD_BYTES", "102400")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


def reset_settings_cache() -> None:
    """Used by tests after changing environment variables."""
    get_settings.cache_clear()
