from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.models import Transmission, TransmissionEvent
from app.common.status import TransmissionStatus


class DuplicateMessageError(RuntimeError):
    pass


class TransmissionRepository:
    def create(self, session: Session, values: dict[str, Any]) -> Transmission:
        record = Transmission(**values, status=TransmissionStatus.QUEUED.value)
        session.add(record)
        try:
            session.flush()
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateMessageError(values["message_id"]) from exc

        session.add(
            TransmissionEvent(
                transmission_id=record.id,
                from_status=None,
                to_status=TransmissionStatus.QUEUED.value,
                attempt=0,
                note="Request accepted for processing",
            )
        )
        session.commit()
        session.refresh(record)
        return record

    def get_by_message_id(self, session: Session, message_id: str) -> Transmission | None:
        return session.scalar(select(Transmission).where(Transmission.message_id == message_id))

    def list(
        self,
        session: Session,
        *,
        source_system: str | None = None,
        target_system: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[Transmission]]:
        filters = []
        if source_system:
            filters.append(func.upper(Transmission.source_system) == source_system.upper())
        if target_system:
            filters.append(func.upper(Transmission.target_system) == target_system.upper())
        if priority:
            filters.append(Transmission.priority == priority)
        if status:
            filters.append(Transmission.status == status)

        count_statement = select(func.count()).select_from(Transmission).where(*filters)
        data_statement: Select[tuple[Transmission]] = (
            select(Transmission)
            .where(*filters)
            .order_by(Transmission.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        total = int(session.scalar(count_statement) or 0)
        return total, list(session.scalars(data_statement).all())

    def events(self, session: Session, transmission_id: int) -> list[TransmissionEvent]:
        statement = (
            select(TransmissionEvent)
            .where(TransmissionEvent.transmission_id == transmission_id)
            .order_by(TransmissionEvent.created_at.asc(), TransmissionEvent.id.asc())
        )
        return list(session.scalars(statement).all())

    def claim_next(self, session: Session) -> Transmission | None:
        statement = (
            select(Transmission)
            .where(Transmission.status == TransmissionStatus.QUEUED.value)
            .order_by(Transmission.created_at.asc())
            .limit(1)
        )
        if session.bind and session.bind.dialect.name == "postgresql":
            statement = statement.with_for_update(skip_locked=True)

        record = session.scalar(statement)
        if record is None:
            session.rollback()
            return None

        previous = record.status
        record.status = TransmissionStatus.PROCESSING.value
        record.processing_started_at = datetime.now(UTC)
        record.failure_code = None
        record.failure_detail = None
        session.add(
            TransmissionEvent(
                transmission_id=record.id,
                from_status=previous,
                to_status=record.status,
                attempt=record.attempt_count,
                note="Worker claimed queued transmission",
            )
        )
        session.commit()
        session.refresh(record)
        return record

    def recover_stale_processing(self, session: Session, max_age_seconds: int = 60) -> int:
        cutoff = datetime.now(UTC) - timedelta(seconds=max_age_seconds)
        statement = select(Transmission).where(
            Transmission.status == TransmissionStatus.PROCESSING.value,
            Transmission.processing_started_at.is_not(None),
            Transmission.processing_started_at < cutoff,
        )
        records = list(session.scalars(statement).all())
        for record in records:
            previous = record.status
            record.status = TransmissionStatus.QUEUED.value
            record.processing_started_at = None
            session.add(
                TransmissionEvent(
                    transmission_id=record.id,
                    from_status=previous,
                    to_status=record.status,
                    attempt=record.attempt_count,
                    note="Recovered after stale worker claim",
                )
            )
        if records:
            session.commit()
        else:
            session.rollback()
        return len(records)

    def update_attempt(self, session: Session, record: Transmission, attempt: int) -> None:
        record.attempt_count = attempt
        session.commit()
        session.refresh(record)

    def transition(
        self,
        session: Session,
        record: Transmission,
        new_status: TransmissionStatus,
        *,
        note: str,
        partner_ack_id: str | None = None,
        failure_code: str | None = None,
        failure_detail: str | None = None,
    ) -> Transmission:
        previous = record.status
        record.status = new_status.value
        record.partner_ack_id = partner_ack_id
        record.failure_code = failure_code
        record.failure_detail = failure_detail[:500] if failure_detail else None
        session.add(
            TransmissionEvent(
                transmission_id=record.id,
                from_status=previous,
                to_status=record.status,
                attempt=record.attempt_count,
                note=note[:250],
            )
        )
        session.commit()
        session.refresh(record)
        return record

    def requeue(self, session: Session, record: Transmission) -> Transmission:
        previous = record.status
        record.status = TransmissionStatus.QUEUED.value
        record.attempt_count = 0
        record.partner_ack_id = None
        record.failure_code = None
        record.failure_detail = None
        record.processing_started_at = None
        session.add(
            TransmissionEvent(
                transmission_id=record.id,
                from_status=previous,
                to_status=record.status,
                attempt=0,
                note="Manual requeue requested",
            )
        )
        session.commit()
        session.refresh(record)
        return record
