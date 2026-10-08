from __future__ import annotations

from enum import StrEnum


class TransmissionStatus(StrEnum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


TERMINAL_STATUSES = {
    TransmissionStatus.DELIVERED,
    TransmissionStatus.REJECTED,
    TransmissionStatus.FAILED,
}
