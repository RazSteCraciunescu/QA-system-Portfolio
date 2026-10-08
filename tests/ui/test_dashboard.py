from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from playwright.sync_api import expect, sync_playwright

pytestmark = pytest.mark.ui


def test_user_can_queue_message_from_dashboard():
    if os.getenv("RUN_UI") != "1":
        pytest.skip("Set RUN_UI=1 to run browser tests against a live environment")

    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8080")
    message_id = f"MSG-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:8].upper()}"
    output_dir = Path("artifacts/live/ui")
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        try:
            page.goto(base_url)
            expect(page).to_have_title("RelayHub QA Console")
            expect(page.locator("#health")).to_have_text("Gateway ready")

            page.locator("#message-id").fill(message_id)
            page.locator("#source-system").fill("UI_CLIENT")
            page.locator("#target-system").fill("PARTNER_B")
            page.locator("#payload").fill('{"event":"ui-smoke","internal_note":"remove"}')
            page.get_by_role("button", name="Queue transmission").click()

            expect(page.locator("#form-result")).to_contain_text("accepted")
            expect(page.locator(f'tr[data-message-id="{message_id}"]')).to_be_visible(
                timeout=10000
            )
        except Exception:
            page.screenshot(path=output_dir / "failure.png", full_page=True)
            raise
        finally:
            context.tracing.stop(path=output_dir / "trace.zip")
            browser.close()
