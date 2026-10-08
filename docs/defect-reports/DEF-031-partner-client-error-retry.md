# DEF-031 — Worker retries deterministic partner rejection

**Type:** Product defect sample  
**Component:** Delivery worker  
**Severity:** High  
**Priority:** P0  
**Requirements:** RQ-R-001, RQ-R-002  
**Detected in:** Baseline 0.9.0  
**Resolved in:** Baseline 0.9.1  
**Status:** Closed after retest

## Summary

A partner `400` response was handled by the generic non-success branch and retried until the maximum attempt count. The requirement states that client-side rejection is deterministic and must not be retried.

## Reproduction

1. Configure the partner simulator response sequence to `400, 202`.
2. Submit a valid message.
3. Poll the message status and partner attempt history.

## Expected

The worker makes one delivery attempt, stores failure classification `PARTNER_400`, and sets the final state to `REJECTED`.

## Actual in 0.9.0

The worker made a second attempt and marked the message `DELIVERED` after the simulator returned `202`. This concealed the original contract rejection.

## Impact

Unnecessary traffic and misleading final status could mask invalid transformed data. A real partner might also apply rate limits or treat repeated invalid messages as an operational incident.

## Root cause and correction

The retry decision used a broad `status >= 400` condition. Handling was separated into network/`5xx` transient failure, `4xx` deterministic rejection, and accepted response branches.

## Retest and regression

- `400, 202`: one attempt, `REJECTED`.
- `422, 202`: one attempt, `REJECTED`.
- `503, 202`: two attempts, `DELIVERED`.
- Three `503` responses: three attempts, `FAILED`.
- Connection timeout followed by success: retry and delivery.
- Re-ran TC-INT-007, TC-INT-008, TC-REG-003, TC-REG-004, worker unit tests, and live failure-recovery tests.
