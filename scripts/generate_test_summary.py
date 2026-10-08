from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree


def parse_junit(path: Path) -> dict[str, int | float]:
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    return {
        "tests": sum(int(suite.attrib.get("tests", 0)) for suite in suites),
        "failures": sum(int(suite.attrib.get("failures", 0)) for suite in suites),
        "errors": sum(int(suite.attrib.get("errors", 0)) for suite in suites),
        "skipped": sum(int(suite.attrib.get("skipped", 0)) for suite in suites),
        "time": sum(float(suite.attrib.get("time", 0)) for suite in suites),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a compact Markdown test summary from JUnit XML"
    )
    parser.add_argument("junit", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scope", default="Automated verification")
    args = parser.parse_args()

    totals = parse_junit(args.junit)
    passed = (
        int(totals["tests"])
        - int(totals["failures"])
        - int(totals["errors"])
        - int(totals["skipped"])
    )
    decision = "PASS" if int(totals["failures"]) == 0 and int(totals["errors"]) == 0 else "FAIL"
    content = f"""# Test Execution Summary

- **Scope:** {args.scope}
- **Generated:** {datetime.now(UTC).isoformat()}
- **Decision:** {decision}

| Metric | Result |
|---|---:|
| Tests | {totals['tests']} |
| Passed | {passed} |
| Failed | {totals['failures']} |
| Errors | {totals['errors']} |
| Skipped | {totals['skipped']} |
| Duration | {float(totals['time']):.2f} s |

The JUnit XML remains the source evidence for individual test outcomes.
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
