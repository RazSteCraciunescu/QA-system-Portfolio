from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


REDACTED_KEYS = {
    "authorization",
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in REDACTED_KEYS else _sanitize(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("message_id", "correlation_id", "status", "event", "details"):
            if hasattr(record, key):
                payload[key] = _sanitize(getattr(record, key))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(_sanitize(payload), ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    if root.handlers:
        for handler in root.handlers:
            handler.setFormatter(JsonFormatter())
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
