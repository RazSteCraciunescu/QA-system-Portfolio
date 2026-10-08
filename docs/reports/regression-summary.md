# Regression selection summary

## Core release pack

| Area | Selected evidence | Reason |
|---|---|---|
| Submission and validation | gateway component, Robot, Postman, TC-FUN-001–005 | protects the public entry point |
| Persistence and status | repository, component, live event history, TC-FUN-006–010 | protects auditability and supportability |
| JSON/XML interoperability | transformer unit/component, contracts, live XML, TC-INT-001–006 | highest interface risk |
| Retry and rejection | worker unit, live response sequences, TC-INT-007–009 | protects reliability and avoids harmful repeats |
| Secure handling | security suite, schema checks, TC-SEC-001–009 | protects boundary and diagnostics |
| Environment and release | health tests, Compose checks, Robot, TC-REL pack | protects repeatability and readiness |

## Selection rules

- Always execute P0 requirement coverage for a release candidate.
- Add tests for every changed component and its direct callers/consumers.
- For a fixed defect, select the original reproduction plus root-cause neighbours.
- For schema changes, execute old and new compatible examples and explicit unsupported-version checks.
- For configuration changes, use a clean Compose baseline and retain resolved configuration.
- Treat flaky tests as defects in test assets; do not normalize reruns without investigation.

## Result categories

Report passed, failed, blocked, skipped, and not selected separately. A passing rerun does not erase the first failure; the investigation and disposition remain part of the cycle record.
