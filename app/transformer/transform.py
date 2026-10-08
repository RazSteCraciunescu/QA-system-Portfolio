from __future__ import annotations

from collections import Counter
from typing import Any

from defusedxml import ElementTree as SafeElementTree
from defusedxml.common import DefusedXmlException

SENSITIVE_FIELDS = {
    "api_key",
    "debug",
    "internal_note",
    "password",
    "secret",
    "token",
}
MAX_XML_ELEMENTS = 500
MAX_NESTING_DEPTH = 20


class TransformationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _clean_json(value: Any, path: str = "payload", depth: int = 0) -> tuple[Any, list[str]]:
    if depth > MAX_NESTING_DEPTH:
        raise TransformationError("PAYLOAD_TOO_DEEP", "Payload nesting exceeds the supported depth")

    removed: list[str] = []
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            field_path = f"{path}.{key}"
            if key.lower() in SENSITIVE_FIELDS:
                removed.append(field_path)
                continue
            clean_value, clean_removed = _clean_json(item, field_path, depth + 1)
            clean[key] = clean_value
            removed.extend(clean_removed)
        return clean, removed
    if isinstance(value, list):
        clean_list = []
        for index, item in enumerate(value):
            clean_value, clean_removed = _clean_json(item, f"{path}[{index}]", depth + 1)
            clean_list.append(clean_value)
            removed.extend(clean_removed)
        return clean_list, removed
    return value, removed


def normalize_json(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    clean, removed = _clean_json(payload)
    return clean, removed


def _element_to_value(element, path: str, depth: int = 0) -> tuple[Any, list[str], int]:
    if depth > MAX_NESTING_DEPTH:
        raise TransformationError("PAYLOAD_TOO_DEEP", "XML nesting exceeds the supported depth")

    current_path = f"{path}.{element.tag}" if path else element.tag
    if element.tag.lower() in SENSITIVE_FIELDS:
        return None, [current_path], 1

    children = list(element)
    if not children:
        return (element.text or "").strip(), [], 1

    counts = Counter(child.tag for child in children)
    result: dict[str, Any] = {}
    removed: list[str] = []
    elements_seen = 1
    for child in children:
        child_value, child_removed, child_count = _element_to_value(child, current_path, depth + 1)
        elements_seen += child_count
        if elements_seen > MAX_XML_ELEMENTS:
            raise TransformationError("XML_TOO_COMPLEX", "XML payload contains too many elements")
        removed.extend(child_removed)
        if child.tag.lower() in SENSITIVE_FIELDS:
            continue
        if counts[child.tag] > 1:
            result.setdefault(child.tag, []).append(child_value)
        else:
            result[child.tag] = child_value
    return result, removed, elements_seen


def normalize_xml(payload: str) -> tuple[dict[str, Any], list[str]]:
    try:
        root = SafeElementTree.fromstring(payload)
    except (SafeElementTree.ParseError, DefusedXmlException) as exc:
        raise TransformationError("INVALID_XML", "XML payload could not be parsed safely") from exc

    if root.tag != "message":
        raise TransformationError("INVALID_XML_ROOT", "XML root element must be <message>")

    value, removed, _ = _element_to_value(root, "")
    if not isinstance(value, dict):
        raise TransformationError("EMPTY_XML_MESSAGE", "XML message must contain child elements")
    return value, removed
