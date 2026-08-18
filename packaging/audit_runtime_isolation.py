#!/usr/bin/env python3
"""Audit an installed Reasoning Distiller tree for runtime isolation violations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

AUDIT_CONTRACT = "reasoning-distiller-runtime-isolation-audit/1"
TEXT_SUFFIXES = {".py", ".json", ".md", ".yaml", ".yml", ".toml", ".txt", ".sh"}
FORBIDDEN_RUNTIME_TOKENS = (
    "github.com/loteque/reasoning-distiller",
    "raw.githubusercontent.com/loteque/reasoning-distiller",
    "api.github.com/repos/loteque/reasoning-distiller",
    "git@github.com:loteque/reasoning-distiller",
    "docs/distiller/",
    "docs/handoff/rgp/",
)
PROVENANCE_ROOT = ".installation"


def audit(installed_root: Path) -> dict:
    root = installed_root.resolve()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("installed root must be a regular directory")

    violations: list[dict[str, str]] = []
    scanned = 0
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            violations.append({"path": rel, "reason": "symlink-forbidden"})
            continue
        if path.is_dir():
            continue
        if rel == PROVENANCE_ROOT or rel.startswith(PROVENANCE_ROOT + "/"):
            continue
        scanned += 1
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lower = text.lower()
        for token in FORBIDDEN_RUNTIME_TOKENS:
            if token.lower() in lower:
                violations.append({"path": rel, "reason": f"forbidden-runtime-reference:{token}"})

    result = {
        "contract": AUDIT_CONTRACT,
        "status": "PASS" if not violations else "FAIL",
        "scanned_files": scanned,
        "violations": violations,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a local Reasoning Distiller install for runtime isolation")
    parser.add_argument("installed_root", type=Path)
    args = parser.parse_args()
    result = audit(args.installed_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
