# RelayHub requirements and acceptance criteria

## Purpose

RelayHub accepts a message from one system, normalizes it, and delivers it to an external partner through a separate worker process. The requirements are written to support test design rather than to imitate a full product specification.

## Functional requirements

### RQ-F-001 — Accept a valid transmission

The gateway shall accept a valid version `1.0` transmission and return HTTP `202` with the message ID, correlation ID, initial status, and status URL.

Acceptance criteria:

- mandatory metadata and payload are present;
- the initial status is `QUEUED`;
- the returned correlation ID is also present in the response header;
- the transmission can be retrieved through the status URL.

### RQ-F-002 — Validate message identity and system names

The gateway shall validate the message-ID pattern and normalize source and target system names to uppercase.

Acceptance criteria:

- valid format: `MSG-YYYYMMDD-SUFFIX`, where the suffix is 4–12 uppercase alphanumeric characters;
- leading and trailing whitespace in system names is removed;
- invalid values return HTTP `422` with a stable error code and field-level detail.

### RQ-F-003 — Support JSON payloads

A transmission declaring `payload_format=JSON` shall contain a JSON object. A string, array, or scalar shall be rejected.

### RQ-F-004 — Support XML payloads

A transmission declaring `payload_format=XML` shall contain a string with a `<message>` root element. Malformed XML or an unsupported root shall be rejected during transformation.

### RQ-F-005 — Enforce unique message IDs

Only one transmission may exist for a message ID.

Acceptance criteria:

- the first valid request is accepted;
- a repeated message ID returns HTTP `409` and `DUPLICATE_MESSAGE_ID`;
- concurrent requests cannot create duplicate database rows.

### RQ-F-006 — Expose status without exposing the raw payload

The status endpoint shall return routing metadata, current state, attempt count, acknowledgement, failure information, and timestamps. It shall not return the original payload.

### RQ-F-007 — Filter and paginate status records

The list endpoint shall support source system, target system, priority, status, limit, and offset filters.

Acceptance criteria:

- source and target filters are case-insensitive;
- the limit is between 1 and 200;
- the response contains total count and result items;
- records are ordered newest first.

### RQ-F-008 — Maintain state-transition evidence

The system shall retain an ordered event record for initial queueing, worker claim, terminal outcome, requeue, and stale-worker recovery.

## Interface and interoperability requirements

### RQ-I-001 — Normalize messages to the partner contract

The transformer shall map gateway field names to the partner contract:

- `schema_version` → `schemaVersion`;
- `message_id` → `messageId`;
- `source_system` → `origin`;
- `target_system` → `destination`;
- `data_sensitivity` → `dataSensitivity`.

### RQ-I-002 — Convert XML content to a JSON-compatible structure

XML child elements shall be converted to object properties. Nested elements shall remain nested. Repeated element names shall become a list in source order.

### RQ-I-003 — Filter non-transferable fields

The transformer shall recursively remove these field names, case-insensitively: `api_key`, `debug`, `internal_note`, `password`, `secret`, and `token`.

Acceptance criteria:

- removed fields do not reach the partner;
- the normalized message records the removed field paths in `filteredFields`;
- the input object is not mutated.

### RQ-I-004 — Record partner acknowledgement

A successful partner response shall return HTTP `202` with an acknowledgement ID. RelayHub shall store the acknowledgement and set the transmission to `DELIVERED`.

## Reliability and error-handling requirements

### RQ-R-001 — Retry transient partner failures

The worker shall retry network errors and partner `5xx` responses up to the configured maximum attempt count. The default maximum is three.

### RQ-R-002 — Do not retry deterministic partner rejection

Partner `4xx` responses shall set the transmission to `REJECTED` after one attempt. The worker shall not retry them.

### RQ-R-003 — Fail clearly when the transformer is unavailable

A transformer connection error or `5xx` response shall set the transmission to `FAILED` with a machine-readable failure code.

### RQ-R-004 — Recover stale processing claims

When a worker starts, it shall return transmissions left in `PROCESSING` beyond the configured recovery age to `QUEUED` and record the recovery event.

### RQ-R-005 — Requeue failed delivery

An operator may requeue a `FAILED` transmission. `QUEUED`, `PROCESSING`, `DELIVERED`, and `REJECTED` records shall not be requeueable through this endpoint.

## Security and information-handling requirements

### RQ-S-001 — Limit payload size

The gateway shall reject payloads larger than the configured byte limit with HTTP `413` and `PAYLOAD_TOO_LARGE`.

### RQ-S-002 — Parse XML defensively

The transformer shall reject external entities, DTD-based entity expansion, malformed XML, excessive element counts, and excessive nesting.

### RQ-S-003 — Protect diagnostic controls

Partner-simulator administration endpoints shall require the configured `X-Admin-Token`.

### RQ-S-004 — Redact secrets in structured logs

Known credential field names shall be replaced with `[REDACTED]` before structured log output.

### RQ-S-005 — Add baseline browser security headers

Gateway responses shall include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: no-referrer`.

## Operational requirements

### RQ-O-001 — Provide liveness and readiness endpoints

Each HTTP service shall provide liveness and readiness endpoints. Gateway readiness shall verify database access.

### RQ-O-002 — Run in a repeatable container environment

The gateway, worker, transformer, partner simulator, and PostgreSQL database shall start through one Docker Compose file with dependency health checks.

### RQ-O-003 — Produce machine-readable test evidence

Automated suites shall be able to produce JUnit XML, coverage output, Robot reports, Newman output, browser traces or screenshots on failure, and container logs.
