from __future__ import annotations

import json
from collections import deque

import httpx
import pytest

from app.common.config import Settings
from app.common.status import TransmissionStatus
from app.gateway.repository import TransmissionRepository
from app.worker.processor import DeliveryProcessor

pytestmark = pytest.mark.unit


def make_settings(max_attempts: int = 3) -> Settings:
    return Settings(
        app_env="test",
        database_url="sqlite:///:memory:",
        gateway_base_url="http://gateway",
        transformer_url="http://transformer",
        partner_url="http://partner",
        partner_admin_token="test-token",
        worker_poll_seconds=0.01,
        worker_max_attempts=max_attempts,
        worker_retry_delay_seconds=0.0,
        outbound_timeout_seconds=1.0,
        max_payload_bytes=102400,
        log_level="WARNING",
    )


def create_record(session, message_id: str = "MSG-20260902-A17F"):
    return TransmissionRepository().create(
        session,
        {
            "message_id": message_id,
            "correlation_id": "2a11c0fa-3f78-441e-88de-f64604b8aa4f",
            "schema_version": "1.0",
            "source_system": "OPS_A",
            "target_system": "PARTNER_B",
            "priority": "HIGH",
            "data_sensitivity": "CONTROLLED",
            "payload_format": "JSON",
            "payload_json": json.dumps({"event": "update", "internal_note": "remove"}),
        },
    )


def normalized_message(message_id: str) -> dict:
    return {
        "schemaVersion": "1.0",
        "messageId": message_id,
        "origin": "OPS_A",
        "destination": "PARTNER_B",
        "priority": "HIGH",
        "dataSensitivity": "CONTROLLED",
        "content": {"event": "update"},
        "filteredFields": ["payload.internal_note"],
    }


def test_worker_delivers_on_first_attempt(session_factory):
    captured_partner_body = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "transformer":
            return httpx.Response(200, json=normalized_message("MSG-20260902-A17F"))
        captured_partner_body.update(json.loads(request.content))
        return httpx.Response(
            202,
            json={
                "ackId": "ACK-1234567890ABCDEF",
                "messageId": "MSG-20260902-A17F",
                "status": "ACCEPTED",
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    processor = DeliveryProcessor(make_settings(), client=client)
    with session_factory() as session:
        create_record(session)
        result = processor.process_next(session)
        stored = TransmissionRepository().get_by_message_id(session, "MSG-20260902-A17F")

    assert result is not None
    assert result.status == TransmissionStatus.DELIVERED
    assert result.attempts == 1
    assert stored is not None
    assert stored.partner_ack_id == "ACK-1234567890ABCDEF"
    assert captured_partner_body["content"] == {"event": "update"}
    client.close()


def test_worker_retries_server_errors_then_delivers(session_factory):
    statuses = deque([503, 502, 202])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "transformer":
            return httpx.Response(200, json=normalized_message("MSG-20260902-A17F"))
        response_status = statuses.popleft()
        if response_status == 202:
            return httpx.Response(202, json={"ackId": "ACK-1234567890ABCDEF"})
        return httpx.Response(response_status, json={"error": "temporary"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    processor = DeliveryProcessor(make_settings(), client=client)
    with session_factory() as session:
        create_record(session)
        result = processor.process_next(session)

    assert result is not None
    assert result.status == TransmissionStatus.DELIVERED
    assert result.attempts == 3
    client.close()


def test_worker_does_not_retry_partner_client_error(session_factory):
    partner_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal partner_calls
        if request.url.host == "transformer":
            return httpx.Response(200, json=normalized_message("MSG-20260902-A17F"))
        partner_calls += 1
        return httpx.Response(400, json={"error": "bad message"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    processor = DeliveryProcessor(make_settings(), client=client)
    with session_factory() as session:
        create_record(session)
        result = processor.process_next(session)
        stored = TransmissionRepository().get_by_message_id(session, "MSG-20260902-A17F")

    assert result is not None
    assert result.status == TransmissionStatus.REJECTED
    assert partner_calls == 1
    assert stored is not None
    assert stored.failure_code == "PARTNER_400"
    client.close()


def test_worker_stops_when_transformer_rejects_payload(session_factory):
    partner_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal partner_calls
        if request.url.host == "transformer":
            return httpx.Response(422, json={"error": {"code": "INVALID_XML"}})
        partner_calls += 1
        return httpx.Response(202)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    processor = DeliveryProcessor(make_settings(), client=client)
    with session_factory() as session:
        create_record(session)
        result = processor.process_next(session)

    assert result is not None
    assert result.status == TransmissionStatus.REJECTED
    assert result.attempts == 0
    assert partner_calls == 0
    client.close()


def test_worker_marks_failed_after_connection_errors(session_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "transformer":
            return httpx.Response(200, json=normalized_message("MSG-20260902-A17F"))
        raise httpx.ConnectError("partner offline", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    processor = DeliveryProcessor(make_settings(max_attempts=2), client=client)
    with session_factory() as session:
        create_record(session)
        result = processor.process_next(session)
        stored = TransmissionRepository().get_by_message_id(session, "MSG-20260902-A17F")

    assert result is not None
    assert result.status == TransmissionStatus.FAILED
    assert result.attempts == 2
    assert stored is not None
    assert stored.failure_code == "PARTNER_UNAVAILABLE"
    client.close()
