#!/usr/bin/env python3
"""Run fixed validator fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "validators"))
from validate_distillation import validate  # noqa: E402

FIXTURE_DIR = Path(__file__).with_name("fixtures")


def main() -> int:
    failed = False
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        errors = validate(document)
        expected_valid = path.name.startswith("valid-")
        actual_valid = not errors

        if expected_valid == actual_valid:
            print(f"PASS {path.name}")
            continue

        failed = True
        expectation = "valid" if expected_valid else "invalid"
        print(f"FAIL {path.name}: expected {expectation}")
        for error in errors:
            print(f"  - {error}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
