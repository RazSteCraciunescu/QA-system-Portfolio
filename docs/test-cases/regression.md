# Regression test pack

The regression pack is selected around prior failure modes and high-risk boundaries. It is not a copy of every functional test.

## TC-REG-001 — Duplicate-request race protection

**Related defect:** DEF-017  
**Priority:** P0

Send 20 parallel requests using the same message ID and identical valid content.

**Expected:** one `202`, nineteen `409` responses, one database row, and one initial event. No `500` response is acceptable.

## TC-REG-002 — Case-insensitive system filtering

**Related defect:** DEF-024  
**Priority:** P1

Create `FIELD_NODE_7`, then filter using `FIELD_NODE_7`, `field_node_7`, and mixed case.

**Expected:** every query returns the same record and total.

## TC-REG-003 — Transient failure retry boundary

**Related defect:** DEF-031 adjacent risk  
**Priority:** P0

Execute partner sequences `[503,202]`, `[503,502,202]`, and `[503,502,504]`.

**Expected:** attempts are 2, 3, and 3 respectively; first two deliver; final sequence fails once attempts are exhausted.

## TC-REG-004 — Client rejection is not retried

**Related defect:** DEF-031  
**Priority:** P0

Execute partner response codes `400`, `409`, and `429` individually with a later `202` queued behind each.

**Expected:** each message is `REJECTED` after one attempt. The current baseline treats all partner `4xx` responses as deterministic rejection.

## TC-REG-005 — Requeue clears stale failure state

**Priority:** P1

Fail a message, requeue it after partner recovery, and allow redelivery.

**Expected:** requeue clears attempts, acknowledgement, failure code, and failure detail; second processing cycle can reach `DELIVERED`; event history preserves both cycles.

## TC-REG-006 — JSON/XML filtering parity

**Priority:** P0

Send equivalent JSON and XML content containing `token`, `internal_note`, and safe fields.

**Expected:** partner business content is equivalent after representation conversion; prohibited data is absent in both; filtered paths reflect the source representation.

## TC-REG-007 — Status endpoint does not regress into payload exposure

**Priority:** P0

Submit a payload containing an obvious marker and inspect list, status, event, error, and version endpoints.

**Expected:** the marker appears nowhere in public API responses. It may appear only in controlled test input and internal persistence.

## TC-REG-008 — Worker restart recovers stale processing

**Priority:** P1

Stop the worker after a record reaches `PROCESSING`, wait beyond the recovery age, and restart it.

**Expected:** worker records a recovery event, returns the record to `QUEUED`, and completes it once dependencies are available. No second transmission row is created.
