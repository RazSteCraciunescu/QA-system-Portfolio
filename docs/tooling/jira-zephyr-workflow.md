# Example Jira and test-management workflow

The repository is tool-neutral, but the following mapping shows how its assets fit a Jira plus Zephyr-style process.

| Repository concept | Issue or test-management item |
|---|---|
| Requirement ID | Story acceptance criterion or linked requirement |
| Manual case ID | Versioned test case |
| Automated test name | Test case automation key or execution link |
| Sprint test plan | Test plan or sprint QA task |
| Execution evidence | Test cycle execution with report attachment |
| Defect sample | Bug linked to failed execution and requirement |
| Release-readiness report | Release test cycle summary and go/no-go input |

## Suggested workflow

1. Create or refine the requirement with testable acceptance criteria.
2. Link manual and automated cases before execution begins.
3. Group the selected cases into a build-specific test cycle.
4. Record environment, data, result, evidence, and defect link for each execution.
5. Keep blocked and not-run separate from failed.
6. Link each defect to the requirement, failed execution, and correction build.
7. Retest on the changed build and execute adjacent regression.
8. Close the cycle with coverage, defect posture, deviations, and recommendation.

## Configuration-management notes

- Store executable assets, schemas, and documentation in Git.
- Store execution status and approval in the designated test-management system.
- Reference immutable commit SHAs or image digests rather than a moving branch name.
- Avoid copying full payloads or secrets into tickets; link sanitized evidence instead.
- Do not edit passed evidence to match a later build. Create a new execution.
