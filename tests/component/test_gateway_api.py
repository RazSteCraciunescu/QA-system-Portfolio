from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.common.config import reset_settings_cache
from app.common.database import get_db_session
from app.gateway.main import app

pytestmark = pytest.mark.component


@pytest.fixture
def gateway_client(session_factory, monkeypatch):
    monkeypatch.setenv("MAX_PAYLOAD_BYTES", "102400")
    reset_settings_cache()

    def override_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_session
    client = TestClient(app)
    yield client
    client.close()
    app.dependency_overrides.clear()
    reset_settings_cache()


def test_live_and_ready_health_endpoints(gateway_client: TestClient):
    assert gateway_client.get("/health/live").json()["status"] == "UP"
    ready = gateway_client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "READY", "dependencies": {"database": "UP"}}


def test_create_get_list_and_event_history(gateway_client: TestClient, sample_transmission: dict):
    created = gateway_client.post("/api/v1/transmissions", json=sample_transmission)

    assert created.status_code == 202
    assert created.json()["message_id"] == sample_transmission["message_id"]
    assert created.json()["status"] == "QUEUED"
    UUID(created.headers["X-Correlation-ID"])

    retrieved = gateway_client.get(f"/api/v1/transmissions/{sample_transmission['message_id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["source_system"] == "OPS_A"
    assert "payload" not in retrieved.json()

    listed = gateway_client.get("/api/v1/transmissions", params={"source_system": "ops_a"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    events = gateway_client.get(
        f"/api/v1/transmissions/{sample_transmission['message_id']}/events"
    )
    assert events.status_code == 200
    assert [event["to_status"] for event in events.json()] == ["QUEUED"]


def test_duplicate_message_returns_clear_conflict(
    gateway_client: TestClient, sample_transmission: dict
):
    assert gateway_client.post("/api/v1/transmissions", json=sample_transmission).status_code == 202
    duplicate = gateway_client.post("/api/v1/transmissions", json=sample_transmission)

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_MESSAGE_ID"


def test_validation_errors_use_standard_problem_shape(
    gateway_client: TestClient, sample_transmission: dict
):
    sample_transmission["schema_version"] = "2.0"
    response = gateway_client.post("/api/v1/transmissions", json=sample_transmission)

    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "VALIDATION_ERROR"
    assert body["correlation_id"] == response.headers["X-Correlation-ID"]
    assert any(detail["location"] == "body.schema_version" for detail in body["details"])


def test_missing_transmission_returns_404_problem(gateway_client: TestClient):
    response = gateway_client.get("/api/v1/transmissions/MSG-20260902-NONE")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TRANSMISSION_NOT_FOUND"


def test_only_failed_transmissions_can_be_requeued(
    gateway_client: TestClient, sample_transmission: dict
):
    gateway_client.post("/api/v1/transmissions", json=sample_transmission)
    response = gateway_client.post(
        f"/api/v1/transmissions/{sample_transmission['message_id']}/requeue"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "STATUS_NOT_REQUEUEABLE"


def test_supplied_valid_correlation_id_is_preserved(
    gateway_client: TestClient, sample_transmission: dict
):
    correlation_id = "5d2b4051-8bc5-4b7e-8a2d-df12c73fe3fb"
    response = gateway_client.post(
        "/api/v1/transmissions",
        json=sample_transmission,
        headers={"X-Correlation-ID": correlation_id},
    )
    assert response.headers["X-Correlation-ID"] == correlation_id
    assert response.json()["correlation_id"] == correlation_id


def test_invalid_correlation_id_is_replaced(gateway_client: TestClient):
    response = gateway_client.get(
        "/health/live", headers={"X-Correlation-ID": "not-a-uuid"}
    )
    assert response.headers["X-Correlation-ID"] != "not-a-uuid"
    UUID(response.headers["X-Correlation-ID"])


def test_security_headers_are_added(gateway_client: TestClient):
    response = gateway_client.get("/")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "RelayHub QA Console" in response.text


def test_payload_size_limit_is_enforced(
    gateway_client: TestClient, sample_transmission: dict, monkeypatch
):
    monkeypatch.setenv("MAX_PAYLOAD_BYTES", "20")
    reset_settings_cache()
    sample_transmission["payload"] = {"value": "this is deliberately larger than twenty bytes"}

    response = gateway_client.post("/api/v1/transmissions", json=sample_transmission)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
