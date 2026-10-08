from __future__ import annotations

from urllib.error import URLError

import pytest

from scripts import wait_for_service

pytestmark = pytest.mark.unit


class Response:
    def __init__(self, status: int):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_: object) -> None:
        return None


def test_wait_returns_true_for_successful_response(monkeypatch):
    monkeypatch.setattr(wait_for_service, "urlopen", lambda *_args, **_kwargs: Response(204))
    assert wait_for_service.wait("http://127.0.0.1/health", 0.1) is True


def test_wait_retries_transient_connection_failure(monkeypatch):
    calls = iter([URLError("not ready"), Response(200)])

    def fake_open(*_args, **_kwargs):
        result = next(calls)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(wait_for_service, "urlopen", fake_open)
    monkeypatch.setattr(wait_for_service.time, "sleep", lambda _seconds: None)
    assert wait_for_service.wait("http://127.0.0.1/health", 0.1) is True


def test_named_timeout_is_supported(monkeypatch):
    monkeypatch.setattr(
        wait_for_service,
        "parse_args",
        lambda: type(
            "Arguments",
            (),
            {"url": "http://127.0.0.1/health", "named_timeout": 4.0, "legacy_timeout": 9.0},
        )(),
    )
    observed: dict[str, object] = {}

    def fake_wait(url: str, timeout: float) -> bool:
        observed.update(url=url, timeout=timeout)
        return True

    monkeypatch.setattr(wait_for_service, "wait", fake_wait)
    assert wait_for_service.main() == 0
    assert observed == {"url": "http://127.0.0.1/health", "timeout": 4.0}
