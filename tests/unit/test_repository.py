from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from app.common.status import TransmissionStatus
from app.gateway.repository import DuplicateMessageError, TransmissionRepository

pytestmark = pytest.mark.unit


def values(message_id: str = "MSG-20260902-A17F") -> dict:
    return {
        "message_id": message_id,
        "correlation_id": "2a11c0fa-3f78-441e-88de-f64604b8aa4f",
        "schema_version": "1.0",
        "source_system": "OPS_A",
        "target_system": "PARTNER_B",
        "priority": "HIGH",
        "data_sensitivity": "CONTROLLED",
        "payload_format": "JSON",
        "payload_json": json.dumps({"event": "update"}),
    }


def test_create_adds_initial_audit_event(session_factory):
    repository = TransmissionRepository()
    with session_factory() as session:
        record = repository.create(session, values())
        events = repository.events(session, record.id)

    assert record.status == TransmissionStatus.QUEUED.value
    assert len(events) == 1
    assert events[0].from_status is None
    assert events[0].to_status == TransmissionStatus.QUEUED.value


def test_duplicate_message_id_is_blocked_by_database_constraint(session_factory):
    repository = TransmissionRepository()
    with session_factory() as session:
        repository.create(session, values())
        duplicate = values()
        duplicate["correlation_id"] = "30e838a9-27a0-44c8-bab0-7db8a35ac0e7"
        with pytest.raises(DuplicateMessageError):
            repository.create(session, duplicate)


def test_filters_are_case_insensitive_for_system_names(session_factory):
    repository = TransmissionRepository()
    with session_factory() as session:
        repository.create(session, values())
        total, records = repository.list(session, source_system="ops_a", target_system="partner_b")

    assert total == 1
    assert [record.message_id for record in records] == ["MSG-20260902-A17F"]


def test_claim_transition_and_requeue_flow(session_factory):
    repository = TransmissionRepository()
    with session_factory() as session:
        repository.create(session, values())
        record = repository.claim_next(session)
        assert record is not None
        assert record.status == TransmissionStatus.PROCESSING.value

        repository.update_attempt(session, record, 3)
        repository.transition(
            session,
            record,
            TransmissionStatus.FAILED,
            note="partner unavailable",
            failure_code="PARTNER_503",
            failure_detail="temporary outage",
        )
        assert record.status == TransmissionStatus.FAILED.value

        repository.requeue(session, record)
        assert record.status == TransmissionStatus.QUEUED.value
        assert record.attempt_count == 0
        assert record.failure_code is None
        assert [event.to_status for event in repository.events(session, record.id)] == [
            "QUEUED",
            "PROCESSING",
            "FAILED",
            "QUEUED",
        ]


def test_stale_processing_record_is_recovered(session_factory):
    repository = TransmissionRepository()
    with session_factory() as session:
        repository.create(session, values())
        record = repository.claim_next(session)
        assert record is not None
        record.processing_started_at = datetime.now(UTC) - timedelta(minutes=5)
        session.commit()

        recovered = repository.recover_stale_processing(session, max_age_seconds=60)

        assert recovered == 1
        assert record.status == TransmissionStatus.QUEUED.value
