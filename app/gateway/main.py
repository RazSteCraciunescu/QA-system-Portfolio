from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.config import get_settings
from app.common.contracts import Priority
from app.common.database import get_db_session, init_database
from app.common.logging_utils import configure_logging
from app.common.status import TransmissionStatus
from app.gateway.repository import DuplicateMessageError, TransmissionRepository
from app.gateway.schemas import (
    ProblemBody,
    ProblemResponse,
    TransmissionAccepted,
    TransmissionCreate,
    TransmissionEventView,
    TransmissionList,
    TransmissionSummary,
)

LOGGER = logging.getLogger("relayhub.gateway")
REPOSITORY = TransmissionRepository()
STATIC_DIR = Path(__file__).resolve().parent / "static"


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", str(uuid4()))


def _problem(
    request: Request,
    http_status: int,
    code: str,
    message: str,
    details: list[dict[str, object]] | None = None,
) -> JSONResponse:
    body = ProblemResponse(
        error=ProblemBody(
            code=code,
            message=message,
            correlation_id=_correlation_id(request),
            details=details,
        )
    )
    return JSONResponse(status_code=http_status, content=body.model_dump(mode="json"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    init_database()
    LOGGER.info("gateway_started", extra={"event": "gateway_started"})
    yield


app = FastAPI(
    title="RelayHub Message Gateway",
    version="1.0.0",
    description="Synthetic distributed-system API used by the quality engineering portfolio.",
    lifespan=lifespan,
)
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.middleware("http")
async def request_context(request: Request, call_next):
    supplied = request.headers.get("X-Correlation-ID", "")
    try:
        correlation_id = str(UUID(supplied)) if supplied else str(uuid4())
    except ValueError:
        correlation_id = str(uuid4())
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [
        {
            "location": ".".join(str(item) for item in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return _problem(
        request,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "VALIDATION_ERROR",
        "Request validation failed",
        details,
    )


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health/live", tags=["health"])
def live() -> dict[str, str]:
    return {"status": "UP", "service": "gateway"}


@app.get("/health/ready", tags=["health"])
def ready(request: Request, session: Session = Depends(get_db_session)):
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - depends on environment failure
        LOGGER.warning("database_not_ready", exc_info=exc)
        return _problem(
            request,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "DATABASE_UNAVAILABLE",
            "Gateway database is not ready",
        )
    return {"status": "READY", "dependencies": {"database": "UP"}}


@app.get("/api/v1/version", tags=["metadata"])
def version() -> dict[str, str]:
    return {"service": "relayhub-gateway", "version": app.version, "api": "v1"}


@app.post(
    "/api/v1/transmissions",
    response_model=TransmissionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    responses={409: {"model": ProblemResponse}, 413: {"model": ProblemResponse}},
    tags=["transmissions"],
)
def create_transmission(
    request: Request,
    body: TransmissionCreate,
    session: Session = Depends(get_db_session),
):
    payload_json = json.dumps(body.payload, ensure_ascii=False, separators=(",", ":"))
    if len(payload_json.encode("utf-8")) > get_settings().max_payload_bytes:
        return _problem(
            request,
            status.HTTP_413_CONTENT_TOO_LARGE,
            "PAYLOAD_TOO_LARGE",
            "Payload exceeds the configured size limit",
        )

    values = {
        "message_id": body.message_id,
        "correlation_id": _correlation_id(request),
        "schema_version": body.schema_version,
        "source_system": body.source_system,
        "target_system": body.target_system,
        "priority": body.priority.value,
        "data_sensitivity": body.data_sensitivity.value,
        "payload_format": body.payload_format.value,
        "payload_json": payload_json,
    }
    try:
        record = REPOSITORY.create(session, values)
    except DuplicateMessageError:
        return _problem(
            request,
            status.HTTP_409_CONFLICT,
            "DUPLICATE_MESSAGE_ID",
            f"Transmission {body.message_id} already exists",
        )

    LOGGER.info(
        "transmission_queued",
        extra={
            "event": "transmission_queued",
            "message_id": record.message_id,
            "correlation_id": record.correlation_id,
            "status": record.status,
        },
    )
    return TransmissionAccepted(
        message_id=record.message_id,
        correlation_id=record.correlation_id,
        status=record.status,
        status_url=str(request.url_for("get_transmission", message_id=record.message_id)),
    )


@app.get(
    "/api/v1/transmissions/{message_id}",
    response_model=TransmissionSummary,
    responses={404: {"model": ProblemResponse}},
    tags=["transmissions"],
)
def get_transmission(
    request: Request,
    message_id: str,
    session: Session = Depends(get_db_session),
):
    record = REPOSITORY.get_by_message_id(session, message_id)
    if record is None:
        return _problem(
            request,
            status.HTTP_404_NOT_FOUND,
            "TRANSMISSION_NOT_FOUND",
            f"Transmission {message_id} was not found",
        )
    return record


@app.get(
    "/api/v1/transmissions/{message_id}/events",
    response_model=list[TransmissionEventView],
    responses={404: {"model": ProblemResponse}},
    tags=["transmissions"],
)
def get_transmission_events(
    request: Request,
    message_id: str,
    session: Session = Depends(get_db_session),
):
    record = REPOSITORY.get_by_message_id(session, message_id)
    if record is None:
        return _problem(
            request,
            status.HTTP_404_NOT_FOUND,
            "TRANSMISSION_NOT_FOUND",
            f"Transmission {message_id} was not found",
        )
    return REPOSITORY.events(session, record.id)


@app.get(
    "/api/v1/transmissions",
    response_model=TransmissionList,
    tags=["transmissions"],
)
def list_transmissions(
    source_system: str | None = None,
    target_system: str | None = None,
    priority: Priority | None = None,
    status_filter: TransmissionStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db_session),
):
    total, records = REPOSITORY.list(
        session,
        source_system=source_system,
        target_system=target_system,
        priority=priority.value if priority else None,
        status=status_filter.value if status_filter else None,
        limit=limit,
        offset=offset,
    )
    return TransmissionList(total=total, items=records)


@app.post(
    "/api/v1/transmissions/{message_id}/requeue",
    response_model=TransmissionSummary,
    responses={404: {"model": ProblemResponse}, 409: {"model": ProblemResponse}},
    tags=["transmissions"],
)
def requeue_transmission(
    request: Request,
    message_id: str,
    session: Session = Depends(get_db_session),
):
    record = REPOSITORY.get_by_message_id(session, message_id)
    if record is None:
        return _problem(
            request,
            status.HTTP_404_NOT_FOUND,
            "TRANSMISSION_NOT_FOUND",
            f"Transmission {message_id} was not found",
        )
    if record.status != TransmissionStatus.FAILED.value:
        return _problem(
            request,
            status.HTTP_409_CONFLICT,
            "STATUS_NOT_REQUEUEABLE",
            "Only FAILED transmissions can be requeued",
        )
    return REPOSITORY.requeue(session, record)
