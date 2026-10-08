# Master test plan

## 1. Scope

This plan covers RelayHub version 1.0: gateway submission and query APIs, worker processing, JSON/XML transformation, partner delivery, retry and recovery, diagnostic UI, persistence, container startup, and release evidence.

### In scope

- functional and negative API testing;
- database-backed state flow;
- JSON and XML interoperability;
- external partner acknowledgement and controlled failure behaviour;
- regression of fixed defects;
- container and configuration verification;
- baseline security and information-handling checks;
- small service-performance smoke;
- release-readiness evidence.

### Out of scope

- production capacity sizing;
- high-availability database failover;
- full accessibility certification of the diagnostic UI;
- penetration testing;
- third-party identity management;
- long-duration disaster recovery.

## 2. Test items

| Item | Versioning source | Build evidence |
|---|---|---|
| Python application image | Git tag and container digest | CI release workflow |
| Gateway API | OpenAPI `1.0.0` | `/api/v1/version` response |
| Input contract | transmission JSON Schema | committed schema checksum |
| Partner contract | partner message and acknowledgement schemas | contract test output |
| Compose environment | `compose.yaml` in target commit | `docker compose config` and logs |
| Test automation | target Git commit | JUnit, Robot, Newman, Playwright output |

## 3. Test approach

The execution order is designed to stop cheaply:

1. repository validation and static analysis;
2. unit and component tests;
3. contract and security fast tests;
4. Docker image build and environment readiness;
5. live integration and interoperability tests;
6. Robot and Newman release smoke;
7. Playwright UI smoke;
8. scheduled k6 and ZAP checks.

A failure at an earlier layer does not automatically prevent diagnostic execution at a later layer, but it prevents release approval until understood.

## 4. Environments

### Developer fast environment

- Python 3.11–3.14;
- SQLite in memory;
- no external services;
- mocked outbound HTTP.

### Integration environment

- Docker Engine with Compose;
- PostgreSQL 17 container;
- one gateway, one worker, one transformer, one partner simulator;
- local-only diagnostic ports;
- clean database for CI; persistent volume permitted locally.

### Local fallback

The `scripts/run_local_e2e.py` runner starts all Python components as separate processes using a temporary SQLite file. This proves process-to-process HTTP behaviour but does not replace PostgreSQL integration evidence.

## 5. Roles

| Role | Responsibilities |
|---|---|
| QA owner | analysis, risk selection, test design, automation, execution, triage, release recommendation |
| Developer | technical clarification, implementation, unit evidence, defect correction, impact analysis |
| Product or system representative | acceptance criteria, operational priority, residual-risk decision |
| Release coordinator | build identification, environment readiness, deployment and rollback coordination |

A small project may assign several roles to one person. Decisions should still be recorded by role rather than assumed.

## 6. Test deliverables

- requirements and acceptance criteria;
- risk-based strategy and this plan;
- manual cases and automated suites;
- committed test data and interface schemas;
- defect reports and fix-verification evidence;
- JUnit XML, coverage, Robot, Newman, Playwright, k6, and ZAP output as applicable;
- container logs and environment configuration;
- regression summary and release-readiness assessment.

## 7. Schedule model

| Activity | Timing |
|---|---|
| Requirement and risk review | before implementation or at sprint planning |
| Test design and data preparation | during refinement and early implementation |
| Fast automation | alongside code change |
| Integration execution | when component interfaces stabilize |
| Defect triage and retest | daily during active cycle |
| Regression selection | before release candidate deployment |
| Release-readiness review | after agreed gates and defect disposition |
| Post-release evidence review | after deployment or operational validation |

## 8. Suspension and resumption

Testing may be suspended when:

- the environment cannot start or has an unidentified data state;
- the build does not match the declared version;
- more than 20% of selected tests are blocked by one infrastructure issue;
- a Critical issue makes continued execution unsafe or misleading.

Testing resumes when the blocking condition has an owner, documented correction or workaround, and a quick environment-confidence check passes.

## 9. Defect workflow

1. Capture build, environment, requirement, data, reproduction, expected, actual, and evidence.
2. Separate product failure from test, data, and environment failure.
3. Assign severity and proposed priority.
4. Triage with development and system representatives.
5. Retest the exact reproduction on the changed build.
6. Run adjacent regression based on root cause and changed components.
7. Close, reopen, defer, or accept with documented rationale.

## 10. Risks to this plan

| Plan risk | Mitigation |
|---|---|
| Over-reliance on the simulator | keep contract schemas independent and include negative client behaviour |
| Automation duplicated across tools | assign each framework a distinct purpose and review overlap |
| CI-only failures | provide local Compose and local multi-process runners with retained logs |
| False confidence from small load test | label k6 output as smoke, not capacity evidence |
| Unreviewed generated artefacts | keep JUnit and logs as source evidence; summarize without replacing them |

## 11. Approval recommendation format

The QA recommendation is one of:

- **Ready:** exit criteria met; remaining limitations do not conflict with release scope.
- **Ready with accepted risk:** named residual risk has owner, containment, and approval.
- **Not ready:** exit criteria or defect posture is unacceptable.
- **No recommendation:** evidence is incomplete or environment confidence is insufficient.
