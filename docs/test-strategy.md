# Test strategy

## Objective

Provide timely, reproducible evidence that RelayHub accepts supported messages, preserves interface semantics, handles failures predictably, protects controlled fields, and is ready to run in its agreed container environment.

The strategy follows a risk-based approach. Test count is secondary to coverage of the failure modes that would damage interoperability or operational trust.

## Quality risks

| Risk | Impact | Likelihood | Priority | Main controls |
|---|---:|---:|---:|---|
| Prohibited data reaches an external system | Critical | Medium | P0 | recursive filtering tests, partner inspection, log-redaction tests |
| Duplicate submissions create duplicate work | High | Medium | P0 | database constraint, API conflict checks, concurrency follow-up |
| Worker retries a deterministic rejection | High | Medium | P0 | `4xx` no-retry unit and end-to-end tests |
| XML and JSON produce different business meaning | High | Medium | P0 | representation-pair tests, schema checks, partner comparison |
| A transient outage loses a valid message | High | Medium | P1 | retry sequence tests, terminal-state and attempt evidence |
| Message remains stuck after worker interruption | High | Low | P1 | stale-claim recovery test and restart scenario |
| Status filtering hides or misreports records | Medium | Medium | P1 | component, integration, and regression filters |
| Environment starts with an unavailable dependency | Medium | Medium | P1 | readiness checks, Compose dependency health, startup logs |
| Diagnostic UI submits a malformed envelope | Low | Medium | P2 | one Playwright smoke path; API remains the primary control |

## Test levels

### Static checks

- Python compilation;
- Ruff lint and formatting;
- Mypy analysis;
- JSON and YAML parsing;
- OpenAPI and JSON Schema structure checks;
- dependency and source security scans.

### Unit tests

Isolate payload conversion, validation, repository state logic, retry decisions, recovery, and redaction. External services use `httpx.MockTransport`, so failures are deterministic and fast.

### Component tests

Exercise each FastAPI service through an in-process HTTP client. These tests verify status codes, response shapes, middleware, endpoint authorization, and service-specific behaviour without Docker.

### Contract tests

Validate committed examples against JSON Schema and compare the live transformer output with the partner contract. OpenAPI checks protect the expected versioned routes and response codes.

### Integration and interoperability tests

Run gateway, worker, transformer, partner simulator, and shared persistence as separate processes. Verify complete state sequences, JSON/XML conversion, filtering, retry behaviour, no-retry behaviour, acknowledgement storage, and query filters.

### System and UI tests

Use the diagnostic console as a thin end-user path. Only one high-value browser smoke test is kept because most behaviour is safer and faster to verify at the API boundary.

### Non-functional checks

- k6 service-level acceptance smoke;
- OWASP ZAP baseline scan;
- payload size and complexity limits;
- container and dependency scans;
- health, startup, and recovery observations.

## Automation framework allocation

| Framework | Purpose | Reason for selection |
|---|---|---|
| Pytest | unit, component, contract, security, integration | flexible fixtures, Python service access, concise diagnostics |
| Robot Framework | readable release smoke | accessible keyword layer for mixed technical audiences |
| Postman/Newman | portable API regression | easy manual exploration and CI execution |
| Playwright | browser smoke | reliable locator and browser automation model |
| k6 | small load profile | versionable script and clear threshold output |
| Docker Compose | environment orchestration | repeatable service and dependency topology |

Using several frameworks is deliberate only where they serve different audiences or feedback loops. The same behaviour is not repeated everywhere.

## Test data strategy

- Use synthetic system identifiers and payloads only.
- Keep stable valid and invalid examples under version control.
- Generate message IDs at runtime to avoid test coupling.
- Include prohibited fields specifically to prove filtering.
- Reset the partner simulator before each integration test.
- Do not use production exports, customer names, credentials, or operational content.

## Environment strategy

| Environment | Persistence | Use |
|---|---|---|
| In-process fast tests | SQLite memory database | pull-request feedback and local development |
| Local multi-process runner | temporary SQLite file | end-to-end verification without Docker |
| Docker Compose | PostgreSQL container | primary integration, Robot, Newman, UI, and security environment |
| CI scheduled run | fresh Compose environment | performance smoke and extended security baseline |

Configuration differences are explicit. A test passing only on SQLite is not accepted as database-integration evidence.

## Entry criteria

- requirements and acceptance criteria are reviewable;
- interface schemas are versioned;
- the target build is identifiable;
- the selected environment is healthy;
- required test data and simulator controls are available;
- blocking defects from the previous cycle have an agreed disposition.

## Exit criteria

For release readiness:

- all P0 and P1 requirement paths have executed;
- fast, integration, Robot, and agreed security gates pass;
- no open Critical or High defect remains without formal acceptance;
- failed tests are explained by defects or environment incidents;
- regression evidence and container logs are retained;
- known limitations are reviewed against release scope;
- rollback or containment notes exist for residual operational risk.

## Defect management

Severity reflects impact; priority reflects scheduling.

- **Critical:** data exposure, unrecoverable loss, or system-wide unavailability.
- **High:** core interoperability or state flow fails without a safe workaround.
- **Medium:** supported behaviour is incorrect but contained.
- **Low:** cosmetic, diagnostic, or low-risk usability issue.

A defect is ready for verification when the changed build, root cause, affected interfaces, and suggested regression scope are known. Verification includes the original reproduction and a focused adjacent regression check.

## Reporting and metrics

Useful cycle indicators:

- planned, executed, passed, failed, blocked, and not-run tests;
- requirement coverage by risk priority;
- open defects by severity and age;
- fix verification pass rate;
- automation pass rate excluding confirmed environment incidents;
- flaky-test count and quarantine age;
- average partner delivery attempts;
- release criteria met, at risk, or not met.

A green percentage without requirement and defect context is not a release decision.
