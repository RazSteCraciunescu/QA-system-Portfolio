# Test evidence and information-handling guide

## Principles

Evidence must be attributable, reproducible, proportionate to the risk, and safe to retain. More data is not automatically better evidence.

## Allowed repository data

- fictional system and user names;
- synthetic JSON and XML payloads;
- generated message and correlation IDs;
- local-only test tokens documented as non-production values;
- sanitized logs, reports, screenshots, and configuration;
- checksums and image digests.

## Do not commit

- real credentials, access tokens, certificates, or private keys;
- customer, employee, operational, or classified data;
- internal hostnames, ticket URLs, or unapproved architecture details;
- unredacted production logs or database extracts;
- artifacts whose distribution rights are unclear.

## Evidence bundle

A release evidence bundle should identify:

1. source commit and build or image digest;
2. resolved Compose configuration with secrets removed;
3. environment confidence result;
4. selected scope and requirement coverage;
5. machine-readable test results;
6. human-readable summary and defect posture;
7. deviations, blocked tests, and accepted residual risks;
8. release recommendation and approver.

## Sanitization check

Before sharing an artifact, search for authorization headers, password-like fields, tokens, private keys, full payload markers, internal addresses, and personal data. Redact values while retaining enough context to explain the failure. Record that sanitization occurred; do not silently alter evidence after approval.

## Retention

CI artifacts are retained for 30 days by default. Formal release evidence should follow the governing project retention rule. Temporary local databases and raw logs should be removed when their evidentiary value expires.
