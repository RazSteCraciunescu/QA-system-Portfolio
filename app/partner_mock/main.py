from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.config import get_settings
from app.common.contracts import DataSensitivity, Priority
from app.common.logging_utils import configure_logging
from app.partner_mock.state import PartnerState

LOGGER = logging.getLogger("relayhub.partner_mock")
STATE = PartnerState()
ALLOWED_SCENARIO_STATUSES = {202, 400, 409, 422, 429, 500, 502, 503, 504}


class PartnerMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    schema_version: str = Field(alias="schemaVersion")
    message_id: str = Field(alias="messageId")
    origin: str
    destination: str
    priority: Priority
    data_sensitivity: DataSensitivity = Field(alias="dataSensitivity")
    content: dict[str, Any]
    filtered_fields: list[str] = Field(alias="filteredFields")


class PartnerAck(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ack_id: str = Field(alias="ackId")
    message_id: str = Field(alias="messageId")
    status: str


class ScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str
    response_sequence: list[int] = Field(min_length=1, max_length=10)
    delay_ms: int = Field(default=0, ge=0, le=5000)

    @field_validator("response_sequence")
    @classmethod
    def allowed_status_codes(cls, values: list[int]) -> list[int]:
        invalid = [value for value in values if value not in ALLOWED_SCENARIO_STATUSES]
        if invalid:
            raise ValueError(f"Unsupported simulated status codes: {invalid}")
        return values


def require_admin_token(x_admin_token: str = Header(default="", alias="X-Admin-Token")) -> None:
    if x_admin_token != get_settings().partner_admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(get_settings().log_level)
    STATE.reset()
    yield


app = FastAPI(
    title="RelayHub Partner Simulator",
    version="1.0.0",
    description="Stateful external-system simulator used for interoperability and recovery tests.",
    lifespan=lifespan,
)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "UP", "service": "partner-mock"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "READY", "service": "partner-mock"}


@app.post("/partner/v1/messages", response_model=PartnerAck, status_code=202)
def receive_message(body: PartnerMessage):
    response_status, delay_ms = STATE.next_response(body.message_id)
    if delay_ms:
        time.sleep(delay_ms / 1000)

    if response_status != status.HTTP_202_ACCEPTED:
        LOGGER.warning(
            "partner_simulated_failure",
            extra={
                "event": "partner_simulated_failure",
                "message_id": body.message_id,
                "status": str(response_status),
            },
        )
        return JSONResponse(
            status_code=response_status,
            content={
                "error": {
                    "code": f"SIMULATED_{response_status}",
                    "message": "Configured partner response",
                }
            },
        )

    ack_id = f"ACK-{uuid4().hex[:16].upper()}"
    STATE.store_success(body.message_id, body.model_dump(mode="json", by_alias=True), ack_id)
    LOGGER.info(
        "partner_message_accepted",
        extra={"event": "partner_message_accepted", "message_id": body.message_id},
    )
    return PartnerAck(ackId=ack_id, messageId=body.message_id, status="ACCEPTED")


@app.post("/__admin/scenarios", dependencies=[Depends(require_admin_token)], status_code=204)
def configure_scenario(body: ScenarioRequest):
    STATE.configure(body.message_id, body.response_sequence, body.delay_ms)


@app.get("/__admin/messages/{message_id}", dependencies=[Depends(require_admin_token)])
def inspect_message(message_id: str):
    record = STATE.inspect(message_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not observed")
    return record


@app.delete("/__admin/state", dependencies=[Depends(require_admin_token)], status_code=204)
def reset_state():
    STATE.reset()
