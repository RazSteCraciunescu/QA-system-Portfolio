# Requirements traceability matrix

The matrix links requirements to automated checks and manual cases. Automated names are deliberately specific so a reviewer can locate the evidence without guessing.

| Requirement | Risk | Automated evidence | Manual evidence |
|---|---:|---|---|
| RQ-F-001 | P0 | `test_create_get_list_and_event_history`; Robot `Valid Message Reaches Partner` | TC-FUN-001, TC-REL-002 |
| RQ-F-002 | P1 | `test_system_names_are_trimmed_and_normalized`; `test_validation_errors_use_standard_problem_shape` | TC-FUN-002, TC-FUN-003 |
| RQ-F-003 | P0 | `test_payload_type_must_match_json_format`; JSON end-to-end test | TC-FUN-004 |
| RQ-F-004 | P0 | `test_payload_type_must_match_xml_format`; `test_xml_message_is_interoperable` | TC-INT-003, TC-INT-004 |
| RQ-F-005 | P0 | `test_duplicate_message_id_is_blocked_by_database_constraint`; API duplicate test; Robot duplicate test | TC-FUN-005, TC-REG-001 |
| RQ-F-006 | P0 | gateway retrieve test; Postman `Read submitted message` | TC-SEC-006 |
| RQ-F-007 | P1 | repository case-insensitive filter; live list-filter test | TC-FUN-006 through TC-FUN-009 |
| RQ-F-008 | P1 | repository event tests; JSON end-to-end event assertion | TC-INT-010 |
| RQ-I-001 | P0 | transformer component test; partner JSON Schema test | TC-INT-001 |
| RQ-I-002 | P0 | XML dictionary and repeated-element unit tests | TC-INT-003, TC-INT-005 |
| RQ-I-003 | P0 | JSON/XML filtering unit tests; live partner inspection | TC-SEC-001, TC-SEC-002 |
| RQ-I-004 | P1 | worker success test; JSON end-to-end acknowledgement assertion | TC-INT-006 |
| RQ-R-001 | P0 | worker retry unit test; live transient-error test | TC-INT-007, TC-REG-003 |
| RQ-R-002 | P0 | worker no-retry unit test; live partner-400 test | TC-INT-008, TC-REG-004 |
| RQ-R-003 | P1 | worker transformer rejection and unavailable branches | TC-INT-009 |
| RQ-R-004 | P1 | `test_stale_processing_record_is_recovered` | TC-REL-006 |
| RQ-R-005 | P1 | repository requeue flow; API requeue conflict test | TC-FUN-010, TC-REG-005 |
| RQ-S-001 | P0 | gateway payload-size component test | TC-SEC-003 |
| RQ-S-002 | P0 | external-entity, malformed, root, depth, and complexity tests | TC-SEC-004, TC-SEC-005 |
| RQ-S-003 | P1 | partner admin unauthorized tests | TC-SEC-007 |
| RQ-S-004 | P0 | structured-log redaction test | TC-SEC-008 |
| RQ-S-005 | P2 | gateway security-header component test | TC-SEC-009 |
| RQ-O-001 | P1 | health component tests; Robot `Gateway Is Ready` | TC-REL-001 |
| RQ-O-002 | P1 | CI Compose integration job and environment runbook | TC-REL-003, TC-REL-004 |
| RQ-O-003 | P1 | CI artifact jobs and report-generation script | TC-REL-007, TC-REL-008 |

## Coverage interpretation

- **P0** requirements require both automated evidence and a reviewable manual scenario.
- **P1** requirements require automated or operational evidence plus traceable acceptance criteria.
- **P2** requirements may use focused smoke evidence.

A mapped test that was not executed does not count as covered for a release cycle. The cycle report must distinguish designed coverage from executed coverage.
