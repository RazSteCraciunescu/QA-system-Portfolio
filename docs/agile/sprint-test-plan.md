# Example sprint test plan

**Sprint objective:** Introduce XML interoperability and deterministic partner-rejection handling without regressing JSON delivery.

## Planned scope

- RQ-F-004, RQ-I-002, RQ-I-003, and RQ-R-002;
- XML parsing and partner mapping;
- recursive filtering for XML elements;
- one-attempt handling for partner `4xx`;
- regression of JSON transformation, retry, state history, and status APIs.

## Activities by ceremony

| Activity | QA contribution |
|---|---|
| Refinement | challenge XML examples, define malformed and repeated-element cases, identify secure-parser need |
| Sprint planning | estimate design, data, automation, environment, retest, and regression work |
| Daily execution | report tested build, new risk, blockers, defects, and next evidence target |
| Defect triage | classify parser, contract, worker, and environment failures with impact |
| Sprint review | demonstrate accepted XML, rejected unsafe XML, and one-attempt `400` handling |
| Retrospective | review escaped assumptions, suite runtime, flaky checks, and evidence gaps |

## Test tasks

- update schemas and representative XML data;
- add unit tests for nesting, repeated elements, filtering, depth, and entity rejection;
- add transformer component tests;
- add live XML delivery and partner-`400` scenarios;
- update manual interoperability and security cases;
- update traceability and release regression selection.

## Entry criteria

- examples and error semantics reviewed;
- transformer interface version agreed;
- partner simulator supports deterministic response sequences;
- environment baseline passes.

## Exit criteria

- all new P0 and P1 acceptance criteria have executed evidence;
- no open Critical or High defect in changed flows;
- JSON and XML live delivery pass;
- unsafe XML rejection passes;
- partner `4xx` is not retried;
- documentation and traceability reflect the implemented behaviour.

## Main risks

| Risk | Response |
|---|---|
| Parser accepts dangerous constructs | use defensive parser plus targeted abuse cases |
| XML-to-object rules are ambiguous | agree examples for nesting and repeated elements before coding |
| filtering works only at root | use recursive mixed-depth data and partner inspection |
| `4xx` classification breaks `5xx` retry | use response-sequence matrix and worker unit tests |
