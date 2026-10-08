from __future__ import annotations

import json
import py_compile
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".sh", ".bat"}
TRACKING_QUERY_KEYS = {
    "ref",
    "source",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}
URL_PATTERN = re.compile(r"https?://[^\s<>()\[\]{}\"']+")


def tracking_keys_in(text: str) -> set[str]:
    found: set[str] = set()
    for match in URL_PATTERN.findall(text):
        query = urlsplit(match.rstrip(".,;:")).query
        query_items = parse_qsl(query, keep_blank_values=True)
        found.update(key.lower() for key, _ in query_items if key.lower() in TRACKING_QUERY_KEYS)
    return found


def main() -> int:
    errors: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", ".venv"} for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in {"Dockerfile", "Makefile"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            tracking_keys = tracking_keys_in(text)
            if tracking_keys:
                joined = ", ".join(sorted(tracking_keys))
                errors.append(
                    f"Tracking query parameter(s) in {path.relative_to(ROOT)}: {joined}"
                )
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON {path.relative_to(ROOT)}: {exc}")
        if path.suffix in {".yaml", ".yml"} or path.name == "compose.yaml":
            try:
                yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                errors.append(f"Invalid YAML {path.relative_to(ROOT)}: {exc}")
        if path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"Python compile error {path.relative_to(ROOT)}: {exc.msg}")

    required = [
        "README.md",
        "compose.yaml",
        "Dockerfile",
        "docs/test-strategy.md",
        "docs/traceability.md",
        ".github/workflows/quality-gate.yml",
    ]
    for relative in required:
        if not (ROOT / relative).exists():
            errors.append(f"Missing required repository file: {relative}")

    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Repository validation passed: Python, JSON, YAML, required files, and URL hygiene.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
