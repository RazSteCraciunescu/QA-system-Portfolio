from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.config import get_settings
from app.common.contracts import DataSensitivity, PayloadFormat, Priority
from app.common.logging_utils import configure_logging
from app.transformer.transform import TransformationError, normalize_json, normalize_xml

LOGGER = logging.getLogger("relayhub.transformer")


class NormalizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str
    schema_version: str
    source_system: str
    target_system: str
    priority: Priority
    data_sensitivity: DataSensitivity
    payload_format: PayloadFormat
    payload: dict[str, Any] | str

    @model_validator(mode="after")
    def payload_matches_format(self) -> "NormalizeRequest":
        if self.payload_format == PayloadFormat.JSON and not isinstance(self.payload, dict):
            raise ValueError("JSON payload must be an object")
        if self.payload_format == PayloadFormat.XML and not isinstance(self.payload, str):
            raise ValueError("XML payload must be a string")
        return self


class NormalizedMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: str = Field(alias="schemaVersion")
    message_id: str = Field(alias="messageId")
    origin: str
    destination: str
    priority: Priority
    data_sensitivity: DataSensitivity = Field(alias="dataSensitivity")
    content: dict[str, Any]
    filtered_fields: list[str] = Field(alias="filteredFields")


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(get_settings().log_level)
    yield


app = FastAPI(
    title="RelayHub Transformer",
    version="1.0.0",
    description="Normalizes JSON and XML messages into the partner contract.",
    lifespan=lifespan,
)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "UP", "service": "transformer"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "READY", "service": "transformer"}


@app.post("/internal/v1/normalize", response_model=NormalizedMessage)
def normalize(body: NormalizeRequest, request: Request):
    try:
        if body.payload_format == PayloadFormat.JSON:
            content, removed = normalize_json(body.payload)  # type: ignore[arg-type]
        else:
            content, removed = normalize_xml(body.payload)  # type: ignore[arg-type]
    except TransformationError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "correlation_id": request.headers.get("X-Correlation-ID", "unknown"),
                }
            },
        )

    LOGGER.info(
        "message_normalized",
        extra={
            "event": "message_normalized",
            "message_id": body.message_id,
            "details": {"filtered_field_count": len(removed)},
        },
    )
    return NormalizedMessage(
        schemaVersion=body.schema_version,
        messageId=body.message_id,
        origin=body.source_system,
        destination=body.target_system,
        priority=body.priority,
        dataSensitivity=body.data_sensitivity,
        content=content,
        filteredFields=removed,
    )
