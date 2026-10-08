from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.common.config import Settings
from app.common.models import Transmission
from app.common.status import TransmissionStatus
from app.gateway.repository import TransmissionRepository

LOGGER = logging.getLogger("relayhub.worker")


@dataclass
class ProcessingResult:
    message_id: str
    status: TransmissionStatus
    attempts: int


class DeliveryProcessor:
    def __init__(
        self,
        settings: Settings,
        repository: TransmissionRepository | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository or TransmissionRepository()
        self.client = client or httpx.Client(timeout=settings.outbound_timeout_seconds)

    def close(self) -> None:
        self.client.close()

    def process_next(self, session: Session) -> ProcessingResult | None:
        record = self.repository.claim_next(session)
        if record is None:
            return None
        return self.process_claimed(session, record)

    def process_claimed(self, session: Session, record: Transmission) -> ProcessingResult:
        try:
            original_payload = json.loads(record.payload_json)
        except json.JSONDecodeError as exc:
            self.repository.transition(
                session,
                record,
                TransmissionStatus.REJECTED,
                note="Stored payload was not valid JSON",
                failure_code="STORED_PAYLOAD_INVALID",
                failure_detail=str(exc),
            )
            return ProcessingResult(record.message_id, TransmissionStatus.REJECTED, 0)

        normalize_request: dict[str, Any] = {
            "message_id": record.message_id,
            "schema_version": record.schema_version,
            "source_system": record.source_system,
            "target_system": record.target_system,
            "priority": record.priority,
            "data_sensitivity": record.data_sensitivity,
            "payload_format": record.payload_format,
            "payload": original_payload,
        }
        headers = {"X-Correlation-ID": record.correlation_id}

        try:
            transform_response = self.client.post(
                f"{self.settings.transformer_url}/internal/v1/normalize",
                json=normalize_request,
                headers=headers,
            )
        except httpx.RequestError as exc:
            self.repository.transition(
                session,
                record,
                TransmissionStatus.FAILED,
                note="Transformer could not be reached",
                failure_code="TRANSFORMER_UNAVAILABLE",
                failure_detail=str(exc),
            )
            return ProcessingResult(record.message_id, TransmissionStatus.FAILED, 0)

        if 400 <= transform_response.status_code < 500:
            self.repository.transition(
                session,
                record,
                TransmissionStatus.REJECTED,
                note="Transformer rejected the payload",
                failure_code=f"TRANSFORMER_{transform_response.status_code}",
                failure_detail=transform_response.text,
            )
            return ProcessingResult(record.message_id, TransmissionStatus.REJECTED, 0)
        if transform_response.status_code >= 500:
            self.repository.transition(
                session,
                record,
                TransmissionStatus.FAILED,
                note="Transformer returned a server error",
                failure_code=f"TRANSFORMER_{transform_response.status_code}",
                failure_detail=transform_response.text,
            )
            return ProcessingResult(record.message_id, TransmissionStatus.FAILED, 0)

        try:
            normalized_message = transform_response.json()
        except ValueError as exc:
            self.repository.transition(
                session,
                record,
                TransmissionStatus.FAILED,
                note="Transformer response was not JSON",
                failure_code="TRANSFORMER_INVALID_RESPONSE",
                failure_detail=str(exc),
            )
            return ProcessingResult(record.message_id, TransmissionStatus.FAILED, 0)

        last_failure_code = "PARTNER_UNAVAILABLE"
        last_failure_detail = "No partner attempt completed"
        for attempt in range(1, self.settings.worker_max_attempts + 1):
            self.repository.update_attempt(session, record, attempt)
            try:
                partner_response = self.client.post(
                    f"{self.settings.partner_url}/partner/v1/messages",
                    json=normalized_message,
                    headers=headers,
                )
            except httpx.RequestError as exc:
                last_failure_code = "PARTNER_UNAVAILABLE"
                last_failure_detail = str(exc)
            else:
                if 200 <= partner_response.status_code < 300:
                    ack_id = None
                    try:
                        ack_id = partner_response.json().get("ackId")
                    except ValueError:
                        pass
                    self.repository.transition(
                        session,
                        record,
                        TransmissionStatus.DELIVERED,
                        note="Partner accepted normalized message",
                        partner_ack_id=ack_id,
                    )
                    LOGGER.info(
                        "transmission_delivered",
                        extra={
                            "event": "transmission_delivered",
                            "message_id": record.message_id,
                            "correlation_id": record.correlation_id,
                            "status": TransmissionStatus.DELIVERED.value,
                            "details": {"attempts": attempt},
                        },
                    )
                    return ProcessingResult(
                        record.message_id, TransmissionStatus.DELIVERED, attempt
                    )

                if 400 <= partner_response.status_code < 500:
                    self.repository.transition(
                        session,
                        record,
                        TransmissionStatus.REJECTED,
                        note="Partner rejected normalized message without retry",
                        failure_code=f"PARTNER_{partner_response.status_code}",
                        failure_detail=partner_response.text,
                    )
                    return ProcessingResult(record.message_id, TransmissionStatus.REJECTED, attempt)

                last_failure_code = f"PARTNER_{partner_response.status_code}"
                last_failure_detail = partner_response.text

            if attempt < self.settings.worker_max_attempts:
                time.sleep(self.settings.worker_retry_delay_seconds * attempt)

        self.repository.transition(
            session,
            record,
            TransmissionStatus.FAILED,
            note="Partner delivery attempts exhausted",
            failure_code=last_failure_code,
            failure_detail=last_failure_detail,
        )
        LOGGER.error(
            "transmission_failed",
            extra={
                "event": "transmission_failed",
                "message_id": record.message_id,
                "correlation_id": record.correlation_id,
                "status": TransmissionStatus.FAILED.value,
                "details": {"attempts": record.attempt_count, "code": last_failure_code},
            },
        )
        return ProcessingResult(
            record.message_id, TransmissionStatus.FAILED, record.attempt_count
        )
