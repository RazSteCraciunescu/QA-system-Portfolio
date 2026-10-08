from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.partner_mock.main import STATE, app

pytestmark = pytest.mark.component
CLIENT = TestClient(app)
ADMIN_HEADERS = {"X-Admin-Token": "local-test-token"}


@pytest.fixture(autouse=True)
def clean_state():
    STATE.reset()
    yield
    STATE.reset()


def partner_message(message_id: str = "MSG-20260902-A17F") -> dict:
    return {
        "schemaVersion": "1.0",
        "messageId": message_id,
        "origin": "OPS_A",
        "destination": "PARTNER_B",
        "priority": "HIGH",
        "dataSensitivity": "CONTROLLED",
        "content": {"event": "update"},
        "filteredFields": [],
    }


def test_admin_endpoints_require_token():
    response = CLIENT.delete("/__admin/state")
    assert response.status_code == 401


def test_configured_response_sequence_is_consumed_in_order():
    configured = CLIENT.post(
        "/__admin/scenarios",
        headers=ADMIN_HEADERS,
        json={
            "message_id": "MSG-20260902-A17F",
            "response_sequence": [422, 202],
            "delay_ms": 0,
        },
    )
    assert configured.status_code == 204

    first = CLIENT.post("/partner/v1/messages", json=partner_message())
    second = CLIENT.post("/partner/v1/messages", json=partner_message())

    assert first.status_code == 422
    assert second.status_code == 202
    assert second.json()["ackId"].startswith("ACK-")

    inspected = CLIENT.get(
        "/__admin/messages/MSG-20260902-A17F", headers=ADMIN_HEADERS
    )
    assert inspected.json()["attempt_statuses"] == [422, 202]
    assert inspected.json()["delivered_message"]["content"] == {"event": "update"}


def test_unsupported_simulation_status_is_rejected():
    response = CLIENT.post(
        "/__admin/scenarios",
        headers=ADMIN_HEADERS,
        json={
            "message_id": "MSG-20260902-A17F",
            "response_sequence": [418],
        },
    )
    assert response.status_code == 422
