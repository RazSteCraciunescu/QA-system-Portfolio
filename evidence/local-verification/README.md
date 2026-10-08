# Local Verification Evidence

This snapshot records the checks executed against the committed RelayHub baseline on 2 September 2026.

| Executed scope | Result | Evidence |
|---|---:|---|
| Unit, component, contract, and security automation | 52 passed | `fast-junit.xml`, `fast-test-summary.md` |
| Live multi-process integration | 5 passed | `integration-junit.xml`, `integration-test-summary.md`, `logs/` |
| Branch-aware application coverage | 88.47% | `coverage.xml`, `coverage-summary.md` |
| Repository and source validation | Pass | `verification-checks.txt` |
| Evidence integrity | SHA-256 manifest | `manifest.sha256` |

The live integration run used separate gateway, worker, transformer, and partner-simulator processes with a shared temporary SQLite database. The production-like PostgreSQL Compose pack and tool-specific Robot, Newman, browser, Bandit, pip-audit, Trivy, k6, and ZAP jobs remain CI-controlled because their runtimes were not available on the local verification host.

This evidence is intentionally separate from `artifacts/`, which is reserved for disposable output from later local and CI runs.
