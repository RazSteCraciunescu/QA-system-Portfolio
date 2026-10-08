# Known limitations and follow-up work

These are explicit test-lab boundaries, not hidden defects.

1. **One worker profile is exercised by default.** PostgreSQL row locking supports multiple workers, but a long-running parallel-worker soak test is not part of the normal pipeline.
2. **The dashboard is diagnostic.** It does not preserve user filters or provide role-based access control.
3. **The XML contract is intentionally narrow.** Namespaces, attributes, mixed content, and very large documents are outside the current baseline.
4. **Network partition testing is simulated.** Response codes, timeouts, and unavailable endpoints are covered; packet loss and latency distribution would need a proxy such as Toxiproxy.
5. **Performance testing is a smoke profile.** Results should not be interpreted as capacity or sizing data.
6. **Disaster recovery is not automated.** Database backup and restore steps are documented as a future environment exercise.
7. **Browser coverage is Chromium-only in CI.** Firefox and WebKit are reasonable additions if the dashboard becomes a supported user interface.

Suggested next increment: add Toxiproxy, a second worker, and a 30-minute recovery soak while preserving the fast pull-request path.
