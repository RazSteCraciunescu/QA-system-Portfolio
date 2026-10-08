# Quality risk register

Scoring uses probability and impact from 1 to 5. Exposure is their product and guides test depth; it is not a substitute for engineering judgement.

| ID | Risk | P | I | Exposure | Primary controls | Residual position |
|---|---|---:|---:|---:|---|---|
| QR-01 | Accepted message is lost before delivery | 3 | 5 | 15 | persistent queue state, worker recovery, end-to-end status checks | Medium |
| QR-02 | Duplicate business message is processed twice | 3 | 5 | 15 | database uniqueness, conflict response, concurrency test | Low |
| QR-03 | JSON or XML is mapped incorrectly at partner boundary | 3 | 5 | 15 | independent schemas, unit mapping matrix, live partner inspection | Medium |
| QR-04 | Prohibited fields leave the controlled boundary | 2 | 5 | 10 | recursive filtering, synthetic markers, log-redaction tests | Low |
| QR-05 | Unsafe XML consumes resources or reads local content | 2 | 5 | 10 | defensive parser, depth/element limits, abuse-case regression | Low |
| QR-06 | Transient partner failure causes permanent loss | 3 | 4 | 12 | bounded retry, deterministic simulator, attempt-history checks | Medium |
| QR-07 | Deterministic rejection is retried and concealed | 3 | 4 | 12 | explicit `4xx` branch, response-sequence tests | Low |
| QR-08 | Environment fault is reported as product defect | 4 | 3 | 12 | readiness checks, confidence test, runbook, container logs | Medium |
| QR-09 | Public status API exposes message content | 2 | 5 | 10 | summary response model, unique payload-marker security check | Low |
| QR-10 | Automated suite passes while a service never participated | 2 | 4 | 8 | partner attempt inspection, event history, health and logs | Low |
| QR-11 | PostgreSQL behaviour differs from SQLite fast tests | 3 | 3 | 9 | Compose integration gate and explicit fallback limitation | Medium |
| QR-12 | Test evidence cannot be tied to a build | 2 | 4 | 8 | commit/image identity, machine-readable reports, artifact naming | Low |

Risks are reviewed when requirements, interfaces, retry policy, data classification, or deployment topology change.
