# Functional test cases

## TC-FUN-001 — Accept a valid JSON transmission

**Requirements:** RQ-F-001, RQ-F-003  
**Priority:** P0  
**Preconditions:** Gateway and database are ready; message ID does not exist.

**Data:** `test-data/valid/transmission-json.json`

**Steps:**

1. POST the transmission to `/api/v1/transmissions`.
2. Record HTTP status, response body, and `X-Correlation-ID`.
3. Follow the returned `status_url`.

**Expected:**

- submission returns `202`;
- body contains the submitted message ID, a UUID correlation ID, `QUEUED`, and a usable status URL;
- response header correlation ID matches the body;
- status URL returns the same routing metadata;
- original payload is not returned by the status endpoint.

**Evidence:** request/response capture, status response, database or event record when available.

## TC-FUN-002 — Normalize source and target names

**Requirements:** RQ-F-002  
**Priority:** P1

**Steps:**

1. Submit a valid request with `source_system="  ops_a "` and `target_system="partner_b"`.
2. Retrieve the stored transmission.

**Expected:** request is accepted and stored as `OPS_A` to `PARTNER_B`.

## TC-FUN-003 — Reject invalid identity and schema version

**Requirements:** RQ-F-002  
**Priority:** P0

Execute each data row independently:

| Variant | Change | Expected field detail |
|---|---|---|
| A | message ID has no `MSG-` prefix | `body.message_id` |
| B | date section contains letters | `body.message_id` |
| C | suffix has fewer than four characters | `body.message_id` |
| D | `schema_version=2.0` | `body.schema_version` |
| E | unknown top-level property | unexpected field location |

**Expected:** HTTP `422`, `VALIDATION_ERROR`, correlation ID, and field-level details; no transmission row is created.

## TC-FUN-004 — Enforce declared payload representation

**Requirements:** RQ-F-003, RQ-F-004  
**Priority:** P0

| Declared format | Payload | Expected |
|---|---|---|
| JSON | object | accepted |
| JSON | string | `422` |
| XML | string | accepted by gateway |
| XML | object | `422` |

For the accepted XML variant, final transformation validity is verified by the integration pack.

## TC-FUN-005 — Reject duplicate message ID

**Requirements:** RQ-F-005  
**Priority:** P0

1. Submit a valid message.
2. Repeat the same request.
3. Repeat again with changed payload but the same message ID.
4. Query the list endpoint for that ID's source and inspect the database when available.

**Expected:** first request returns `202`; later requests return `409` and `DUPLICATE_MESSAGE_ID`; only one transmission and one initial queue event exist.

## TC-FUN-006 — Filter by source and target system

**Requirements:** RQ-F-007  
**Priority:** P1

1. Create messages from `OPS_A`, `OPS_B`, and `FIELD_NODE_7` to two targets.
2. Query by each source using uppercase and lowercase filter values.
3. Query by target.
4. Query by source and target together.

**Expected:** matching is case-insensitive for system names; combined filters use logical AND; total count matches returned data before pagination.

## TC-FUN-007 — Filter by priority and status

**Requirements:** RQ-F-007  
**Priority:** P1

1. Create messages at all supported priorities.
2. Produce at least one `DELIVERED`, `REJECTED`, and `FAILED` record through controlled partner behaviour.
3. Query each priority and state independently and in combination.

**Expected:** every returned item matches all requested filters; unsupported enumeration values return `422`.

## TC-FUN-008 — Paginate and order results

**Requirements:** RQ-F-007  
**Priority:** P2

1. Create at least six records with observable creation order.
2. Query with `limit=2, offset=0`, then offsets 2 and 4.
3. Try limits 0, 1, 200, and 201; try offset `-1`.

**Expected:** valid pages do not overlap and are newest first; total remains six; invalid bounds return `422`.

## TC-FUN-009 — Handle unknown message ID

**Requirements:** RQ-F-006  
**Priority:** P1

Query status, events, and requeue endpoints for a syntactically valid ID that does not exist.

**Expected:** each endpoint returns `404`, `TRANSMISSION_NOT_FOUND`, and a correlation ID; no stack trace or database detail is exposed.

## TC-FUN-010 — Requeue only failed delivery

**Requirements:** RQ-R-005, RQ-F-008  
**Priority:** P1

1. Produce a `FAILED` record by exhausting partner retries.
2. POST its requeue endpoint.
3. Inspect status and event history.
4. Attempt requeue on `QUEUED`, `PROCESSING`, `DELIVERED`, and `REJECTED` records.

**Expected:** failed record returns to `QUEUED`, attempt count and failure fields are cleared, and a requeue event is appended. Other states return `409` and remain unchanged.
