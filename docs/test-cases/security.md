# Security and controlled-information test cases

These checks are defensive verification for the lab. They are not a substitute for a formal penetration test or accreditation activity.

## TC-SEC-001 — Remove prohibited JSON fields

**Requirements:** RQ-I-003  
**Priority:** P0

Use prohibited names at multiple depths and in arrays. Include case variants such as `Token` and `PASSWORD`.

**Expected:** no prohibited value reaches the partner; all safe siblings remain; removed paths are listed.

## TC-SEC-002 — Remove prohibited XML elements

**Requirements:** RQ-I-003  
**Priority:** P0

Place prohibited elements at the root and inside nested structures.

**Expected:** the partner receives neither element nor value; safe XML content remains intact.

## TC-SEC-003 — Enforce payload byte limit

**Requirements:** RQ-S-001  
**Priority:** P0

Test one byte below, exactly at, and one byte above the configured limit using UTF-8 ASCII and multibyte characters.

**Expected:** below and exact boundary are accepted; above boundary returns `413` and `PAYLOAD_TOO_LARGE`; no partial row is created.

## TC-SEC-004 — Reject XML external entity

**Requirements:** RQ-S-002  
**Priority:** P0

Submit an XML document that defines an external entity referencing a harmless local path.

**Expected:** controlled `422`; local file content is never returned, logged, or delivered; partner sees no request.

## TC-SEC-005 — Reject XML resource-exhaustion patterns

**Requirements:** RQ-S-002  
**Priority:** P0

Exercise entity expansion, more than 500 elements, and more than 20 levels of nesting.

**Expected:** request is rejected within an acceptable short duration; service remains responsive to a valid message immediately afterwards.

## TC-SEC-006 — Do not expose raw payload in status APIs

**Requirements:** RQ-F-006  
**Priority:** P0

Submit a unique marker in the payload, then search status, list, event, health, version, and validation responses.

**Expected:** marker is absent from public responses. Failure detail is bounded and does not echo original content unnecessarily.

## TC-SEC-007 — Protect partner administration endpoints

**Requirements:** RQ-S-003  
**Priority:** P1

Call scenario, inspection, and reset endpoints with no token, wrong token, and correct token.

**Expected:** no/wrong token returns `401`; correct token permits the operation; token value is not echoed.

## TC-SEC-008 — Redact known credential fields in logs

**Requirements:** RQ-S-004  
**Priority:** P0

Log nested structures containing `authorization`, `password`, `secret`, `token`, `api_key`, and safe controls.

**Expected:** secret values become `[REDACTED]`; safe fields remain; JSON log remains parseable.

## TC-SEC-009 — Return baseline browser security headers

**Requirements:** RQ-S-005  
**Priority:** P2

Inspect successful and error responses from API and dashboard routes.

**Expected:** `nosniff`, frame denial, and no-referrer policy are present consistently.
