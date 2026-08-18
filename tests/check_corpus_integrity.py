#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "docs/extraction/copied-artifacts.json").read_text(encoding="utf-8"))

failed = False
for item in manifest["artifacts"]:
    if not item.get("bytes_must_match_during_parity"):
        continue
    path = ROOT / item["destination"]
    if not path.is_file():
        print(f"FAIL missing {item['destination']}")
        failed = True
        continue
    actual = subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()
    expected = item["source_blob_sha"]
    if actual != expected:
        print(f"FAIL {item['destination']}: expected blob {expected}, got {actual}")
        failed = True
    else:
        print(f"PASS {item['destination']} {actual}")

raise SystemExit(1 if failed else 0)
