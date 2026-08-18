#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
schema = json.loads((ROOT / "schemas/project-package.schema.json").read_text(encoding="utf-8"))
fixture = json.loads((ROOT / "tests/fixtures/project-package-minimal.json").read_text(encoding="utf-8"))

errors = sorted(Draft202012Validator(schema).iter_errors(fixture), key=lambda e: list(e.path))
if errors:
    for error in errors:
        print(f"FAIL project package: {error.message}")
    raise SystemExit(1)
print("PASS minimal Project Knowledge Package")
