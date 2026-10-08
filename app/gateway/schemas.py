from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.contracts import DataSensitivity, PayloadFormat, Priority


class TransmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message_id: str = Field(
        pattern=r"^MSG-[0-9]{8}-[A-Z0-9]{4,12}$",
        examples=["MSG-20260902-A17F"],
    )
    schema_version: str = Field(pattern=r"^1\.0$")
    source_system: str = Field(min_length=2, max_length=30, pattern=r"^[A-Z][A-Z0-9_-]+$")
    target_system: str = Field(min_length=2, max_length=30, pattern=r"^[A-Z][A-Z0-9_-]+$")
    priority: Priority = Priority.NORMAL
    data_sensitivity: DataSensitivity = DataSensitivity.PUBLIC
    payload_format: PayloadFormat
    payload: dict[str, Any] | str

    @field_validator("source_system", "target_system", mode="before")
    @classmethod
    def normalize_system_name(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def payload_matches_declared_format(self) -> "TransmissionCreate":
        if self.payload_format == PayloadFormat.JSON and not isinstance(self.payload, dict):
            raise ValueError("JSON payload_format requires payload to be an object")
        if self.payload_format == PayloadFormat.XML and not isinstance(self.payload, str):
            raise ValueError("XML payload_format requires payload to be a string")
        return self


class TransmissionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    correlation_id: str
    schema_version: str
    source_system: str
    target_system: str
    priority: str
    data_sensitivity: str
    payload_format: str
    status: str
    attempt_count: int
    partner_ack_id: str | None
    failure_code: str | None
    failure_detail: str | None
    created_at: datetime
    updated_at: datetime


class TransmissionAccepted(BaseModel):
    message_id: str
    correlation_id: str
    status: str
    status_url: str


class TransmissionList(BaseModel):
    total: int
    items: list[TransmissionSummary]


class TransmissionEventView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: str | None
    to_status: str
    attempt: int
    note: str | None
    created_at: datetime


class ProblemBody(BaseModel):
    code: str
    message: str
    correlation_id: str
    details: list[dict[str, Any]] | None = None


class ProblemResponse(BaseModel):
    error: ProblemBody
