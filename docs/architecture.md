# Architecture and test boundaries

## Component view

| Component | Responsibility | Main risks | Primary test points |
|---|---|---|---|
| Gateway API | Validate, persist, query, and requeue transmissions | invalid acceptance, duplicates, payload exposure, filter errors | HTTP API, OpenAPI, database rows, response headers |
| Delivery worker | Claim queued work, transform, deliver, retry, update state | retry storms, wrong terminal state, stuck work, lost evidence | state sequence, attempt count, outbound calls, worker logs |
| Transformer | Convert JSON/XML to partner contract and remove prohibited fields | semantic data loss, unsafe XML, field leakage | input/output contracts, negative payloads, filtered paths |
| Partner simulator | Provide repeatable external-system behaviour | unrealistic failure tests, hidden retry defects | configured response sequence, observed message, attempt history |
| PostgreSQL | Persist transmission and event state | race conditions, state inconsistency, environment drift | uniqueness constraint, transaction behaviour, status queries |
| QA console | Lightweight diagnostic UI | wrong submission mapping, stale status display | Playwright smoke, API-backed table state |

## Processing sequence

1. A client sends a versioned transmission to the gateway.
2. The gateway validates the envelope and payload type.
3. The gateway writes one transmission row and the initial `QUEUED` event.
4. The worker claims the oldest queued row and records `PROCESSING`.
5. The worker sends the original content to the transformer with the correlation ID.
6. The transformer parses the declared representation, filters prohibited fields, and returns the partner contract.
7. The worker delivers the normalized message to the partner simulator.
8. A `2xx` response produces `DELIVERED`; a `4xx` produces `REJECTED`; transient failures are retried before `FAILED`.
9. API clients can query current state and ordered event history.

## Data and interface boundaries

### Gateway input

The public contract is versioned independently of implementation. JSON Schema in `config/schemas/transmission-v1.schema.json` provides a portable definition for contract tests and external consumers.

### Transformer output

The transformer creates a partner-facing camel-case contract. Its JSON Schema is stored separately in `config/schemas/partner-message-v1.schema.json`. This prevents a gateway model change from silently changing the external interface.

### XML handling

XML is accepted as content inside the JSON envelope. This keeps transport concerns separate from content representation. The transformer uses a defensive XML parser and applies complexity limits before delivery.

### Persistence

The transmission row contains the original content because the worker is a separate process. The public status endpoint deliberately excludes that content. Event rows provide a lightweight audit trail without requiring application-log reconstruction.

## Failure behaviour

| Failure | Expected result | Retry? |
|---|---|---:|
| Gateway validation error | request rejected, no database row | No |
| Duplicate message ID | HTTP `409`, existing row unchanged | No |
| Transformer `422` | `REJECTED` | No |
| Transformer unavailable or `5xx` | `FAILED` | No, current baseline |
| Partner `4xx` | `REJECTED` | No |
| Partner `5xx` | `DELIVERED` if a later attempt succeeds, otherwise `FAILED` | Yes |
| Partner connection error | `DELIVERED` if a later attempt succeeds, otherwise `FAILED` | Yes |
| Worker stops after claiming | stale `PROCESSING` is returned to `QUEUED` on worker restart | Recovery |

## Environment topology

Docker Compose uses one bridge network for the lab. Only the gateway is exposed on all local interfaces. Transformer and partner diagnostic ports bind to `127.0.0.1`; PostgreSQL has no host port.

Application containers:

- run as a non-root user;
- drop Linux capabilities;
- enable `no-new-privileges`;
- receive configuration through environment variables;
- use health checks for startup ordering and CI diagnostics.

## Design tradeoffs

The database doubles as a small work queue. That is not presented as the only architecture for high-scale messaging. It is used here because it makes persistence, claiming, recovery, idempotency, and multi-process testing visible without adding an unrelated broker administration exercise.

For a larger system, the next architecture test increment would compare the current claim model with a broker-backed design and introduce fault injection through Toxiproxy.
