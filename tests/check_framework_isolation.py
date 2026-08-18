#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_DIRS = ["agents", "protocols", "schemas", "validators", "admission", "backends", "orchestration"]
FORBIDDEN = ["loteque/gdscript-voxel-engine", "project-chat-handoff", "docs/project-chat-handoff"]

failed = False
for dirname in FRAMEWORK_DIRS:
    root = ROOT / dirname
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in FORBIDDEN:
            if token in text:
                print(f"FAIL {path.relative_to(ROOT)} contains consuming-project coupling: {token}")
                failed = True

role_checks = {
    "agents/distiller/DIRECTIVE.md": ["does not itself grant admission"],
    "agents/steward/DIRECTIVE.md": ["Authority is granted by the project knowledge package", "Distiller is a candidate producer only"],
    "agents/architect/DIRECTIVE.md": ["does not admit project knowledge"],
    "agents/engineer/DIRECTIVE.md": ["does not acquire project Steward authority"]
}
for relative, needles in role_checks.items():
    path = ROOT / relative
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    for needle in needles:
        if needle not in text:
            print(f"FAIL {relative} missing authority invariant: {needle}")
            failed = True

if not failed:
    print("PASS framework isolation and role authority boundaries")
raise SystemExit(1 if failed else 0)
