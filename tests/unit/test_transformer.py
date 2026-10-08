from __future__ import annotations

import pytest

from app.transformer.transform import (
    TransformationError,
    normalize_json,
    normalize_xml,
)

pytestmark = pytest.mark.unit


def test_json_filter_removes_sensitive_fields_at_multiple_levels():
    payload = {
        "event": "update",
        "token": "do-not-forward",
        "nested": {"password": "hidden", "safe": 7},
        "items": [{"internal_note": "hidden", "value": "ok"}],
    }

    normalized, removed = normalize_json(payload)

    assert normalized == {"event": "update", "nested": {"safe": 7}, "items": [{"value": "ok"}]}
    assert removed == [
        "payload.token",
        "payload.nested.password",
        "payload.items[0].internal_note",
    ]


def test_json_normalization_does_not_mutate_input():
    payload = {"event": "update", "secret": "x"}
    normalize_json(payload)
    assert payload == {"event": "update", "secret": "x"}


def test_json_excessive_nesting_is_rejected():
    payload: dict = {"value": "end"}
    for _ in range(22):
        payload = {"child": payload}

    with pytest.raises(TransformationError, match="nesting") as exc:
        normalize_json(payload)

    assert exc.value.code == "PAYLOAD_TOO_DEEP"


def test_xml_is_converted_to_dictionary_and_filtered():
    payload = (
        "<message><event>update</event><unit>alpha</unit>"
        "<location><x>2.1</x><y>3.4</y></location>"
        "<internal_note>remove</internal_note></message>"
    )

    normalized, removed = normalize_xml(payload)

    assert normalized == {
        "event": "update",
        "unit": "alpha",
        "location": {"x": "2.1", "y": "3.4"},
    }
    assert removed == ["message.internal_note"]


def test_xml_repeated_elements_become_a_list():
    normalized, _ = normalize_xml("<message><tag>a</tag><tag>b</tag></message>")
    assert normalized == {"tag": ["a", "b"]}


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ("<message><event>broken</message>", "INVALID_XML"),
        ("<envelope><event>ok</event></envelope>", "INVALID_XML_ROOT"),
        ("<message />", "EMPTY_XML_MESSAGE"),
    ],
)
def test_invalid_xml_variants_are_rejected(payload: str, code: str):
    with pytest.raises(TransformationError) as exc:
        normalize_xml(payload)
    assert exc.value.code == code


def test_xml_external_entity_is_rejected():
    payload = (
        '<!DOCTYPE message [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        "<message><event>&xxe;</event></message>"
    )
    with pytest.raises(TransformationError) as exc:
        normalize_xml(payload)
    assert exc.value.code == "INVALID_XML"
