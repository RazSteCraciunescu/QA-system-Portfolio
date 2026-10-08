# Contributing

Changes should preserve traceability between requirements, tests, defects, and release evidence.

## Expected workflow

1. Describe the risk or requirement being addressed.
2. Add or update the smallest useful test at the lowest sensible layer.
3. Run the fast suite before opening a pull request.
4. Run integration tests for interface, persistence, retry, or configuration changes.
5. Update documentation when behaviour or evidence expectations change.

## Test naming

Use behaviour-focused names. Prefer `test_partner_400_is_not_retried` over `test_error_case_2`.

Manual case IDs use these prefixes:

- `TC-FUN` — functional;
- `TC-INT` — integration and interoperability;
- `TC-REG` — regression;
- `TC-SEC` — security and information handling;
- `TC-REL` — release and operational readiness.

## Pull-request evidence

Include the commands run, outcome, affected requirement IDs, and any remaining risk. A screenshot without the underlying log or result file is supporting evidence, not the only evidence.
