from __future__ import annotations

import logging
import os
import signal
import tempfile
import time
from pathlib import Path

from app.common.config import get_settings
from app.common.database import get_session_factory, init_database
from app.common.logging_utils import configure_logging
from app.gateway.repository import TransmissionRepository
from app.worker.processor import DeliveryProcessor

LOGGER = logging.getLogger("relayhub.worker")
HEARTBEAT = Path(
    os.getenv(
        "WORKER_HEARTBEAT_FILE",
        str(Path(tempfile.gettempdir()) / "relayhub-worker-heartbeat"),
    )
)
RUNNING = True


def stop_worker(*_: object) -> None:
    global RUNNING
    RUNNING = False


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_database()
    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)

    repository = TransmissionRepository()
    processor = DeliveryProcessor(settings, repository=repository)
    session_factory = get_session_factory()

    with session_factory() as session:
        recovered = repository.recover_stale_processing(session, max_age_seconds=60)
        if recovered:
            LOGGER.warning(
                "stale_transmissions_recovered",
                extra={"event": "stale_transmissions_recovered", "details": {"count": recovered}},
            )

    LOGGER.info("worker_started", extra={"event": "worker_started"})
    try:
        while RUNNING:
            HEARTBEAT.write_text(str(time.time()), encoding="utf-8")
            with session_factory() as session:
                try:
                    result = processor.process_next(session)
                except Exception:
                    session.rollback()
                    LOGGER.exception("unhandled_processing_error")
                    result = None
            if result is None:
                time.sleep(settings.worker_poll_seconds)
    finally:
        processor.close()
        HEARTBEAT.unlink(missing_ok=True)
        LOGGER.info("worker_stopped", extra={"event": "worker_stopped"})


if __name__ == "__main__":
    run()
