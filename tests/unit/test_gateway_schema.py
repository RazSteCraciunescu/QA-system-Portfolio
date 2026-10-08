from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.gateway.schemas import TransmissionCreate

pytestmark = pytest.mark.unit


def test_system_names_are_trimmed_and_normalized(sample_transmission: dict):
    sample_transmission["source_system"] = "  ops_a "
    sample_transmission["target_system"] = "partner_b"

    model = TransmissionCreate.model_validate(sample_transmission)

    assert model.source_system == "OPS_A"
    assert model.target_system == "PARTNER_B"


def test_unsupported_schema_version_is_rejected(sample_transmission: dict):
    sample_transmission["schema_version"] = "2.0"
    with pytest.raises(ValidationError):
        TransmissionCreate.model_validate(sample_transmission)


def test_payload_type_must_match_json_format(sample_transmission: dict):
    sample_transmission["payload"] = "not-an-object"
    with pytest.raises(ValidationError, match="JSON payload_format"):
        TransmissionCreate.model_validate(sample_transmission)


def test_payload_type_must_match_xml_format(sample_transmission: dict):
    sample_transmission["payload_format"] = "XML"
    with pytest.raises(ValidationError, match="XML payload_format"):
        TransmissionCreate.model_validate(sample_transmission)


def test_unknown_fields_are_rejected(sample_transmission: dict):
    sample_transmission["unexpected"] = "value"
    with pytest.raises(ValidationError):
        TransmissionCreate.model_validate(sample_transmission)
