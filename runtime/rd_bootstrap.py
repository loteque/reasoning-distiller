#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

RESULT_CONTRACT = "reasoning-distiller-project-bootstrap-result/1"
PROJECT_CONTRACT = "reasoning-distiller-project/1"

PROJECT_CONFIG = {
    "contract": PROJECT_CONTRACT,
    "paths": {
        "evidence": "project-knowledge/evidence",
        "invocations": "project-knowledge/invocations",
        "submissions": "project-knowledge/submissions",
    },
}

DIRS = [
    "project-knowledge/evidence",
    "project-knowledge/invocations",
    "project-knowledge/submissions",
]
CONFIG_PATH = "project-knowledge/project.json"


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def emit(value: dict) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def fail(code: str, detail: str) -> int:
    emit({"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": code, "detail": detail})
    return 2


def safe_target(raw: str) -> Path:
    target = Path(raw).expanduser().resolve(strict=True)
    if not target.is_dir():
        raise ValueError("target is not a directory")
    return target


def ensure_beneath(target: Path, path: Path) -> None:
    resolved_parent = path.parent.resolve(strict=False)
    try:
        resolved_parent.relative_to(target)
    except ValueError as exc:
        raise ValueError(f"path escapes target: {path}") from exc


def bootstrap(target: Path) -> tuple[int, dict]:
    install = target / ".reasoning-distiller"
    if not install.exists() or not install.is_dir() or install.is_symlink():
        return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "INSTALLATION_MISSING", "detail": ".reasoning-distiller installation directory is missing or invalid"}

    pk = target / "project-knowledge"
    if pk.exists() and (not pk.is_dir() or pk.is_symlink()):
        return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PATH_CONFLICT", "detail": "project-knowledge exists but is not a normal directory"}

    config_path = target / CONFIG_PATH
    expected = canonical_json(PROJECT_CONFIG)

    # Preflight every existing node before mutation.
    for rel in DIRS:
        path = target / rel
        ensure_beneath(target, path)
        if path.exists() and (not path.is_dir() or path.is_symlink()):
            return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PATH_CONFLICT", "detail": f"{rel} exists but is not a normal directory"}

    ensure_beneath(target, config_path)
    if config_path.exists():
        if not config_path.is_file() or config_path.is_symlink():
            return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PATH_CONFLICT", "detail": f"{CONFIG_PATH} exists but is not a normal file"}
        if config_path.read_bytes() != expected:
            return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PROJECT_CONFIG_CONFLICT", "detail": f"{CONFIG_PATH} already exists with different content"}

    existed = {rel: (target / rel).exists() for rel in DIRS}
    config_existed = config_path.exists()

    created: list[str] = []
    pk.mkdir(exist_ok=True)
    for rel in DIRS:
        path = target / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=False)
            created.append(rel)
    if not config_existed:
        config_path.write_bytes(expected)
        created.append(CONFIG_PATH)

    created.sort()
    if not created:
        outcome = "ALREADY_BOOTSTRAPPED"
    elif not any(existed.values()) and not config_existed:
        outcome = "CREATED"
    else:
        outcome = "COMPLETED"

    return 0, {
        "contract": RESULT_CONTRACT,
        "status": "PASS",
        "outcome": outcome,
        "project_contract": PROJECT_CONTRACT,
        "created": created,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically initialize Reasoning Distiller project-owned state")
    parser.add_argument("--target", required=True, help="project repository root")
    args = parser.parse_args()
    try:
        target = safe_target(args.target)
        code, result = bootstrap(target)
        emit(result)
        return code
    except (OSError, ValueError) as exc:
        return fail("TARGET_INVALID", str(exc))
    except Exception as exc:  # fail closed on unexpected implementation errors
        emit({"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "INTERNAL_ERROR", "detail": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
