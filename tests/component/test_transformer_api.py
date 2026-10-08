from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.transformer.main import app

pytestmark = pytest.mark.component
CLIENT = TestClient(app)


def test_json_contract_is_normalized_with_camel_case_fields(sample_transmission: dict):
    response = CLIENT.post("/internal/v1/normalize", json=sample_transmission)

    assert response.status_code == 200
    body = response.json()
    assert body["messageId"] == sample_transmission["message_id"]
    assert body["schemaVersion"] == "1.0"
    assert "internal_note" not in body["content"]
    assert body["filteredFields"] == ["payload.internal_note"]


def test_xml_contract_is_normalized(sample_xml_transmission: dict):
    response = CLIENT.post("/internal/v1/normalize", json=sample_xml_transmission)

    assert response.status_code == 200
    assert response.json()["content"]["location"] == {"x": "12.4", "y": "8.1"}


def test_malformed_xml_returns_domain_error(sample_xml_transmission: dict):
    sample_xml_transmission["payload"] = "<message><event>broken</message>"
    response = CLIENT.post("/internal/v1/normalize", json=sample_xml_transmission)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_XML"
