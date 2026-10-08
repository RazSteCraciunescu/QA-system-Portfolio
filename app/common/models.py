from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.common.database import Base
from app.common.status import TransmissionStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class Transmission(Base):
    __tablename__ = "transmissions"
    __table_args__ = (UniqueConstraint("message_id", name="uq_transmission_message_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    schema_version: Mapped[str] = mapped_column(String(10), nullable=False)
    source_system: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    target_system: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    data_sensitivity: Mapped[str] = mapped_column(String(12), nullable=False)
    payload_format: Mapped[str] = mapped_column(String(8), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=TransmissionStatus.QUEUED.value, index=True
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partner_ack_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class TransmissionEvent(Base):
    __tablename__ = "transmission_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transmission_id: Mapped[int] = mapped_column(
        ForeignKey("transmissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    to_status: Mapped[str] = mapped_column(String(16), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    note: Mapped[str | None] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
