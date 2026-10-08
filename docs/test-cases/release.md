# Release and operational-readiness test cases

## TC-REL-001 — Verify service health model

**Requirements:** RQ-O-001  
**Priority:** P1

Check liveness and readiness for gateway, transformer, and partner. Repeat gateway readiness with database available and unavailable.

**Expected:** liveness identifies a running process; readiness reflects dependency access; unavailable dependency returns `503` with controlled detail.

## TC-REL-002 — Execute release smoke path

**Requirements:** RQ-F-001, RQ-I-004  
**Priority:** P0

Run the Robot suite against the release-candidate environment.

**Expected:** health, valid delivery, and duplicate rejection pass; Robot output, log, and report files are retained.

## TC-REL-003 — Start from a clean container state

**Requirements:** RQ-O-002  
**Priority:** P1

1. Run `docker compose down -v`.
2. Build and start the environment.
3. Wait for all health checks.
4. Submit a valid message.

**Expected:** no manual database preparation is required; all services become healthy; message is delivered.

## TC-REL-004 — Restart application services with persisted database

**Requirements:** RQ-O-002  
**Priority:** P1

Create a delivered record, restart gateway and worker without deleting the volume, and query the record.

**Expected:** state and events persist; services return healthy; new work is processed.

## TC-REL-005 — Verify clean shutdown and repeatable start

**Priority:** P2

Start and stop the environment three times. Review exit codes, orphan containers, local ports, and logs.

**Expected:** no orphaned application container or unexpected port remains; each start reaches readiness.

## TC-REL-006 — Recover stale worker claim

**Requirements:** RQ-R-004  
**Priority:** P1

Interrupt the worker after claim and restart after the recovery threshold.

**Expected:** one recovery event, work returns to queue, and later processing completes without duplicate rows.

## TC-REL-007 — Produce and retain test evidence

**Requirements:** RQ-O-003  
**Priority:** P1

Run fast and integration workflows with evidence output enabled.

**Expected:** JUnit XML, coverage XML, Robot files, Newman output, browser failure evidence when applicable, and Compose logs are present and readable. Summary numbers reconcile with source files.

## TC-REL-008 — Review release criteria and residual risk

**Requirements:** all P0/P1  
**Priority:** P0

Review requirement execution, open defects, failed and blocked tests, environment incidents, security findings, known limitations, and rollback notes.

**Expected:** a documented recommendation of Ready, Ready with accepted risk, Not ready, or No recommendation; every exception has an owner and rationale.
