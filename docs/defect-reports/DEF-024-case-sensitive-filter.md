# DEF-024 — Source-system filter is unexpectedly case-sensitive

**Type:** Product defect sample  
**Component:** Gateway list API  
**Severity:** Medium  
**Priority:** P1  
**Requirement:** RQ-F-007  
**Detected in:** Baseline 0.8.2  
**Resolved in:** Baseline 0.8.3  
**Status:** Closed after retest

## Summary

`GET /api/v1/transmissions?source_system=alpha_client` returned no records even though submissions from `ALPHA_CLIENT` existed. The requirement defined source and target filters as case-insensitive.

## Reproduction

1. Submit messages from `ALPHA_CLIENT` and `BRAVO_CLIENT`.
2. Query with `source_system=ALPHA_CLIENT` and record the result.
3. Repeat with `alpha_client`, `Alpha_Client`, leading/trailing spaces, and a non-existent source.

## Expected

All case variants select the `ALPHA_CLIENT` records. Surrounding query whitespace is rejected or normalized consistently. The unrelated and non-existent sources are not returned.

## Actual in 0.8.2

Only the exact uppercase value returned records. The API returned `200` with an empty result for lower and mixed case, giving no indication that the filter semantics were wrong.

## Correction

The repository comparison now normalizes both filter and stored value for source and target systems. Request-schema normalization remains responsible for values created through the gateway.

## Retest and adjacent regression

- Verified source and target filters with upper, lower, and mixed case.
- Combined source filter with priority, status, limit, and offset.
- Checked total count and newest-first ordering.
- Re-ran TC-FUN-006 through TC-FUN-009 and the live filtering scenario.

## Notes

This defect is useful in triage because the endpoint was available and technically successful; the failure was semantic rather than transport-level.
