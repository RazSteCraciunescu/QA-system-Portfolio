# Defect triage and fix-verification guide

## Minimum defect information

A defect should contain the affected build, environment, requirement, preconditions, exact data reference, reproduction, expected and actual result, impact, correlation ID, and available evidence. State whether the failure reproduces after a clean baseline.

## Classification

First decide whether the observation is a product defect, test-code defect, test-data defect, environment/configuration issue, requirement question, or expected limitation. Do not lower severity merely because a workaround exists; record the workaround separately.

### Severity model

| Severity | Typical interpretation |
|---|---|
| Critical | Safety, confidentiality, unrecoverable corruption, or system-wide inability to operate |
| High | Core flow unavailable, incorrect delivery, duplicate processing, or no practical workaround |
| Medium | Material requirement failure with contained impact or viable workaround |
| Low | Limited usability, diagnostics, documentation, or cosmetic problem |

Priority is a delivery decision and may differ from severity. Record who accepted any deferral.

## Triage questions

- Is the build and environment identity reliable?
- Does the same input produce the same failure?
- Which interface first diverges from expected behaviour?
- Is evidence sufficient without including sensitive values?
- Could the symptom be downstream of an earlier service failure?
- What other messages, states, formats, or clients share the changed code path?
- Does the defect invalidate already completed test evidence?

## Fix verification

1. Execute the exact original reproduction on the corrected build.
2. Verify both visible behaviour and stored state.
3. Confirm logs and errors are clear and do not leak payload or credentials.
4. Select adjacent regression from the root cause, not only the symptom.
5. Record build, results, evidence paths, and remaining observations.
6. Reopen when expected behaviour is not fully restored; create a separate issue for a genuinely independent finding.

## Closure wording

A useful closure note states the correction observed, exact retest data, execution result, regression scope, evidence location, and any residual limitation. “Works now” is not sufficient verification evidence.
