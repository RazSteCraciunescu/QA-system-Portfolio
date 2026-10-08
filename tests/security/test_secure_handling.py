from __future__ import annotations

import json
import logging
from io import StringIO

import pytest
from fastapi.testclient import TestClient

from app.common.logging_utils import JsonFormatter
from app.partner_mock.main import app as partner_app
from app.transformer.main import app as transformer_app

pytestmark = pytest.mark.security


def test_structured_logger_redacts_common_secret_fields():
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("security-test")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    logger.info(
        "request_received",
        extra={"details": {"token": "secret-value", "nested": {"password": "hidden"}}},
    )
    record = json.loads(output.getvalue())

    assert "secret-value" not in output.getvalue()
    assert "hidden" not in output.getvalue()
    assert record["details"]["token"] == "[REDACTED]"
    assert record["details"]["nested"]["password"] == "[REDACTED]"


def test_transformer_blocks_xml_external_entity(sample_xml_transmission: dict):
    sample_xml_transmission["payload"] = (
        '<!DOCTYPE message [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        "<message><event>&xxe;</event></message>"
    )
    response = TestClient(transformer_app).post(
        "/internal/v1/normalize", json=sample_xml_transmission
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_XML"
    assert "root:" not in response.text


def test_partner_admin_data_is_not_available_without_token():
    response = TestClient(partner_app).get("/__admin/messages/MSG-20260902-A17F")
    assert response.status_code == 401
