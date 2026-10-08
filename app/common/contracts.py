from __future__ import annotations

from enum import StrEnum


class PayloadFormat(StrEnum):
    JSON = "JSON"
    XML = "XML"


class Priority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DataSensitivity(StrEnum):
    PUBLIC = "PUBLIC"
    CONTROLLED = "CONTROLLED"
