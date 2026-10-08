# DEF-017 — Concurrent duplicate submissions create more than one accepted response

**Type:** Product defect sample  
**Component:** Gateway persistence  
**Severity:** High  
**Priority:** P0  
**Requirement:** RQ-F-005  
**Detected in:** Baseline 0.7.0  
**Resolved in:** Baseline 0.7.1  
**Status:** Closed after retest

## Summary

When multiple clients submitted the same new message ID at nearly the same time, duplicate detection based only on a read-before-write check allowed more than one request to return `202`.

## Preconditions

- Clean database.
- Gateway connected to PostgreSQL.
- Twenty clients prepared with identical valid bodies and a shared message ID.

## Reproduction

1. Release all twenty POST requests to `/api/v1/transmissions` through one synchronization barrier.
2. Record each response and correlation ID.
3. Query the database by message ID.
4. Repeat ten times with a clean row between runs.

## Expected

Exactly one request returns `202`. Every other request returns `409` with `DUPLICATE_MESSAGE_ID`. One transmission row exists.

## Actual in 0.7.0

Two to four requests returned `202` in 6 of 10 runs. The final row count varied by database timing.

## Impact

Callers could receive conflicting acceptance evidence for one business identifier. Downstream processing might run more than once, so the issue blocks release.

## Root cause and correction

The first implementation checked for an existing row before insert but had no database uniqueness constraint. The correction added a unique constraint on `message_id` and mapped insertion conflicts to the standard `409` response.

## Retest and regression

- Repeated the synchronized twenty-client test 100 times: one `202`, nineteen `409`, one row in every run.
- Verified normal unique submissions remained accepted.
- Verified duplicate detection after service restart.
- Re-ran TC-FUN-001, TC-FUN-005, TC-REG-001, repository tests, gateway component tests, and live integration.

## Retained evidence

Request/result matrix, gateway log extract, database count query, and JUnit output are expected in the cycle evidence bundle. No payload values or credentials are required for this defect.
