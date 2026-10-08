from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest


@pytest.fixture(scope="session")
def integration_config():
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Set RUN_INTEGRATION=1 to run against a live RelayHub environment")
    return {
        "gateway": os.getenv("BASE_URL", "http://127.0.0.1:8080").rstrip("/"),
        "partner": os.getenv("PARTNER_BASE_URL", "http://127.0.0.1:8083").rstrip("/"),
        "admin_token": os.getenv("PARTNER_ADMIN_TOKEN", "local-test-token"),
    }


@pytest.fixture
def api(integration_config):
    with httpx.Client(timeout=5.0) as client:
        yield client


@pytest.fixture(autouse=True)
def reset_partner_state(api, integration_config):
    response = api.delete(
        f"{integration_config['partner']}/__admin/state",
        headers={"X-Admin-Token": integration_config["admin_token"]},
    )
    assert response.status_code == 204


def unique_message_id() -> str:
    date = datetime.now(UTC).strftime("%Y%m%d")
    return f"MSG-{date}-{uuid4().hex[:8].upper()}"


def wait_for_terminal_status(client: httpx.Client, gateway: str, message_id: str) -> dict:
    deadline = time.monotonic() + 15
    last_body = None
    while time.monotonic() < deadline:
        response = client.get(f"{gateway}/api/v1/transmissions/{message_id}")
        assert response.status_code == 200
        last_body = response.json()
        if last_body["status"] in {"DELIVERED", "REJECTED", "FAILED"}:
            return last_body
        time.sleep(0.2)
    pytest.fail(f"Transmission did not reach a terminal status. Last response: {last_body}")
