from __future__ import annotations

import pytest

from tests.integration.conftest import unique_message_id, wait_for_terminal_status

pytestmark = pytest.mark.integration


def make_json_message(message_id: str) -> dict:
    return {
        "message_id": message_id,
        "schema_version": "1.0",
        "source_system": "OPS_A",
        "target_system": "PARTNER_B",
        "priority": "HIGH",
        "data_sensitivity": "CONTROLLED",
        "payload_format": "JSON",
        "payload": {
            "event": "status-update",
            "unit": "alpha-7",
            "token": "must-not-leave-the-transformer",
            "nested": {"internal_note": "filter this", "safe": True},
        },
    }


def test_json_message_is_normalized_delivered_and_audited(api, integration_config):
    message_id = unique_message_id()
    submitted = api.post(
        f"{integration_config['gateway']}/api/v1/transmissions",
        json=make_json_message(message_id),
    )
    assert submitted.status_code == 202

    final = wait_for_terminal_status(api, integration_config["gateway"], message_id)
    assert final["status"] == "DELIVERED"
    assert final["attempt_count"] == 1
    assert final["partner_ack_id"].startswith("ACK-")

    observed = api.get(
        f"{integration_config['partner']}/__admin/messages/{message_id}",
        headers={"X-Admin-Token": integration_config["admin_token"]},
    )
    assert observed.status_code == 200
    delivered = observed.json()["delivered_message"]
    assert delivered["content"] == {
        "event": "status-update",
        "unit": "alpha-7",
        "nested": {"safe": True},
    }
    assert sorted(delivered["filteredFields"]) == [
        "payload.nested.internal_note",
        "payload.token",
    ]

    events = api.get(
        f"{integration_config['gateway']}/api/v1/transmissions/{message_id}/events"
    ).json()
    assert [event["to_status"] for event in events] == ["QUEUED", "PROCESSING", "DELIVERED"]


def test_xml_message_is_interoperable(api, integration_config):
    message_id = unique_message_id()
    body = make_json_message(message_id)
    body["payload_format"] = "XML"
    body["payload"] = (
        "<message><event>status-update</event><unit>bravo-4</unit>"
        "<location><x>8.2</x><y>4.6</y></location>"
        "<internal_note>remove</internal_note></message>"
    )

    assert api.post(
        f"{integration_config['gateway']}/api/v1/transmissions", json=body
    ).status_code == 202
    final = wait_for_terminal_status(api, integration_config["gateway"], message_id)
    assert final["status"] == "DELIVERED"

    observed = api.get(
        f"{integration_config['partner']}/__admin/messages/{message_id}",
        headers={"X-Admin-Token": integration_config["admin_token"]},
    ).json()
    assert observed["delivered_message"]["content"]["location"] == {"x": "8.2", "y": "4.6"}


def test_transient_partner_errors_are_retried(api, integration_config):
    message_id = unique_message_id()
    configured = api.post(
        f"{integration_config['partner']}/__admin/scenarios",
        headers={"X-Admin-Token": integration_config["admin_token"]},
        json={"message_id": message_id, "response_sequence": [503, 502, 202]},
    )
    assert configured.status_code == 204

    api.post(
        f"{integration_config['gateway']}/api/v1/transmissions",
        json=make_json_message(message_id),
    )
    final = wait_for_terminal_status(api, integration_config["gateway"], message_id)

    assert final["status"] == "DELIVERED"
    assert final["attempt_count"] == 3
    observed = api.get(
        f"{integration_config['partner']}/__admin/messages/{message_id}",
        headers={"X-Admin-Token": integration_config["admin_token"]},
    ).json()
    assert observed["attempt_statuses"] == [503, 502, 202]


def test_partner_400_is_not_retried(api, integration_config):
    message_id = unique_message_id()
    api.post(
        f"{integration_config['partner']}/__admin/scenarios",
        headers={"X-Admin-Token": integration_config["admin_token"]},
        json={"message_id": message_id, "response_sequence": [400, 202]},
    )
    api.post(
        f"{integration_config['gateway']}/api/v1/transmissions",
        json=make_json_message(message_id),
    )

    final = wait_for_terminal_status(api, integration_config["gateway"], message_id)
    assert final["status"] == "REJECTED"
    assert final["attempt_count"] == 1

    observed = api.get(
        f"{integration_config['partner']}/__admin/messages/{message_id}",
        headers={"X-Admin-Token": integration_config["admin_token"]},
    ).json()
    assert observed["attempt_statuses"] == [400]


def test_list_filters_work_across_created_records(api, integration_config):
    message_id = unique_message_id()
    body = make_json_message(message_id)
    body["priority"] = "CRITICAL"
    body["source_system"] = "FIELD_NODE_7"
    api.post(f"{integration_config['gateway']}/api/v1/transmissions", json=body)
    wait_for_terminal_status(api, integration_config["gateway"], message_id)

    response = api.get(
        f"{integration_config['gateway']}/api/v1/transmissions",
        params={"source_system": "field_node_7", "priority": "CRITICAL"},
    )
    assert response.status_code == 200
    assert message_id in [item["message_id"] for item in response.json()["items"]]
