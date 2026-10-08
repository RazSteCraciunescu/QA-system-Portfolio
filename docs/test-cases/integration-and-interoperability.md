# Integration and interoperability test cases

## TC-INT-001 — Map the gateway envelope to the partner contract

**Requirements:** RQ-I-001  
**Priority:** P0

Submit a valid JSON transmission and inspect the message stored by the partner simulator.

**Expected mapping:**

| Gateway | Partner |
|---|---|
| `schema_version` | `schemaVersion` |
| `message_id` | `messageId` |
| `source_system` | `origin` |
| `target_system` | `destination` |
| `data_sensitivity` | `dataSensitivity` |

Priority and content values remain semantically unchanged. The partner message validates against `partner-message-v1.schema.json`.

## TC-INT-002 — Filter sensitive fields recursively

**Requirements:** RQ-I-003  
**Priority:** P0

Create one JSON payload containing prohibited field names:

- at the root;
- inside nested objects;
- inside objects in an array;
- with mixed letter case.

**Expected:** prohibited fields are absent at the partner; permitted sibling values remain; `filteredFields` identifies every removed path; source test data remains unchanged.

## TC-INT-003 — Deliver an equivalent XML message

**Requirements:** RQ-F-004, RQ-I-002  
**Priority:** P0

1. Submit an XML message containing event, unit, nested location, and an internal note.
2. Wait for terminal state.
3. Inspect the partner message.

**Expected:** final state is `DELIVERED`; nested location is represented as an object; internal note is absent and listed as filtered.

## TC-INT-004 — Reject malformed or unsafe XML

**Requirements:** RQ-F-004, RQ-S-002  
**Priority:** P0

Execute malformed tags, unsupported root, empty message, external entity, DTD expansion, excessive depth, and excessive element count.

**Expected:** transformer returns a controlled `422`; worker sets `REJECTED`; partner receives no delivery attempt; failure information contains a stable transformer code without parser internals.

## TC-INT-005 — Preserve repeated XML element order

**Requirements:** RQ-I-002  
**Priority:** P1

Submit `<message><tag>a</tag><tag>b</tag><tag>c</tag></message>`.

**Expected:** partner content contains `"tag": ["a", "b", "c"]` in source order.

## TC-INT-006 — Store acknowledgement and final delivery state

**Requirements:** RQ-I-004  
**Priority:** P1

1. Configure default successful partner behaviour.
2. Submit a valid message.
3. Poll status and inspect events.

**Expected:** one partner attempt; `DELIVERED`; acknowledgement begins `ACK-`; sequence is `QUEUED → PROCESSING → DELIVERED`.

## TC-INT-007 — Retry transient partner failures

**Requirements:** RQ-R-001  
**Priority:** P0

Configure partner responses `[503, 502, 202]`, submit a valid message, and inspect both systems.

**Expected:** exactly three attempts; final state `DELIVERED`; acknowledgement stored; partner attempt history matches configuration; no duplicate transmission row or duplicate terminal event.

Repeat with three transient failures.

**Expected:** final state `FAILED`, attempt count three, failure code reflects the last response.

## TC-INT-008 — Do not retry partner client rejection

**Requirements:** RQ-R-002  
**Priority:** P0

Configure `[400, 202]` and submit a valid message.

**Expected:** only `400` is consumed; final state `REJECTED`; attempt count one; the configured `202` remains unused.

## TC-INT-009 — Handle transformer unavailability

**Requirements:** RQ-R-003  
**Priority:** P1

1. Stop or misconfigure the transformer.
2. Submit a valid JSON message.
3. Wait for worker processing.
4. Inspect status and partner simulator.

**Expected:** final state `FAILED`; failure code `TRANSFORMER_UNAVAILABLE` or transformer `5xx`; no partner attempt; worker remains alive and can process a later message after service restoration.

## TC-INT-010 — Maintain ordered transition evidence

**Requirements:** RQ-F-008  
**Priority:** P1

Produce one successful, one rejected, one exhausted-retry, and one manually requeued message.

**Expected:** every message has chronologically ordered events; each event carries previous state, new state, attempt count, note, and timestamp; transitions are consistent with the final record.
