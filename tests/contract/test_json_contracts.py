from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, ValidationError, validate

from app.gateway.main import app as gateway_app
from app.transformer.main import app as transformer_app

pytestmark = pytest.mark.contract
ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_transmission_schema_is_valid_draft_2020_12():
    schema = load_json(ROOT / "config/schemas/transmission-v1.schema.json")
    Draft202012Validator.check_schema(schema)


def test_valid_sample_matches_transmission_schema():
    schema = load_json(ROOT / "config/schemas/transmission-v1.schema.json")
    sample = load_json(ROOT / "test-data/valid/transmission-json.json")
    validate(sample, schema)


def test_unsupported_version_sample_fails_contract_validation():
    schema = load_json(ROOT / "config/schemas/transmission-v1.schema.json")
    sample = load_json(ROOT / "test-data/invalid/unsupported-version.json")
    with pytest.raises(ValidationError):
        validate(sample, schema)


def test_transformer_output_matches_partner_contract(sample_transmission: dict):
    response = TestClient(transformer_app).post(
        "/internal/v1/normalize", json=sample_transmission
    )
    assert response.status_code == 200

    schema = load_json(ROOT / "config/schemas/partner-message-v1.schema.json")
    validate(response.json(), schema)


def test_gateway_openapi_exposes_versioned_operational_endpoints():
    openapi = gateway_app.openapi()
    paths = openapi["paths"]

    assert "/api/v1/transmissions" in paths
    assert "/api/v1/transmissions/{message_id}" in paths
    assert "/api/v1/transmissions/{message_id}/events" in paths
    assert "/health/live" in paths
    assert "202" in paths["/api/v1/transmissions"]["post"]["responses"]


def test_gateway_request_contract_rejects_unspecified_properties():
    schema = gateway_app.openapi()["components"]["schemas"]["TransmissionCreate"]
    assert schema["additionalProperties"] is False
