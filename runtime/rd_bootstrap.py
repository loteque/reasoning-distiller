#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

RESULT_CONTRACT = "reasoning-distiller-project-bootstrap-result/1"
LEGACY_PROJECT_CONTRACT = "reasoning-distiller-project/1"
PROJECT_CONTRACT = "reasoning-distiller-project/2"

PROJECT_PATHS = {
    "evidence": "project-knowledge/evidence",
    "invocations": "project-knowledge/invocations",
    "submissions": "project-knowledge/submissions",
}

# Exact v1 bootstrap configuration, retained for backward compatibility.
PROJECT_CONFIG = {
    "contract": LEGACY_PROJECT_CONTRACT,
    "paths": PROJECT_PATHS,
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


def build_project_config(project: dict[str, str]) -> dict[str, Any]:
    if not isinstance(project, dict):
        raise ValueError("project identity must be an object")
    required = {"id", "name", "repository", "summary"}
    if set(project) != required:
        raise ValueError("project identity requires exactly id, name, repository, summary")
    for key in sorted(required):
        value = project[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"project identity {key} must be a non-empty string")
    return {
        "contract": PROJECT_CONTRACT,
        "project": {key: project[key] for key in ("id", "name", "repository", "summary")},
        "paths": dict(PROJECT_PATHS),
    }


def validate_project_config(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"contract", "project", "paths"}:
        return False
    if value.get("contract") != PROJECT_CONTRACT or value.get("paths") != PROJECT_PATHS:
        return False
    project = value.get("project")
    if not isinstance(project, dict) or set(project) != {"id", "name", "repository", "summary"}:
        return False
    return all(isinstance(project.get(key), str) and bool(project[key].strip()) for key in project)


def _load_config(path: Path) -> tuple[dict[str, Any] | None, bytes | None]:
    if not path.exists():
        return None, None
    if not path.is_file() or path.is_symlink():
        raise ValueError("project config path is not a normal file")
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("project config is not valid JSON") from exc
    return value, raw


def bootstrap(target: Path, project: dict[str, str] | None = None) -> tuple[int, dict]:
    install = target / ".reasoning-distiller"
    if not install.exists() or not install.is_dir() or install.is_symlink():
        return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "INSTALLATION_MISSING", "detail": ".reasoning-distiller installation directory is missing or invalid"}

    pk = target / "project-knowledge"
    if pk.exists() and (not pk.is_dir() or pk.is_symlink()):
        return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PATH_CONFLICT", "detail": "project-knowledge exists but is not a normal directory"}

    desired_v2: dict[str, Any] | None = None
    if project is not None:
        try:
            desired_v2 = build_project_config(project)
        except ValueError as exc:
            return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PROJECT_IDENTITY_INVALID", "detail": str(exc)}

    config_path = target / CONFIG_PATH

    # Preflight every existing node before mutation.
    for rel in DIRS:
        path = target / rel
        ensure_beneath(target, path)
        if path.exists() and (not path.is_dir() or path.is_symlink()):
            return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PATH_CONFLICT", "detail": f"{rel} exists but is not a normal directory"}

    ensure_beneath(target, config_path)
    try:
        existing_config, existing_bytes = _load_config(config_path)
    except ValueError as exc:
        return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PROJECT_CONFIG_CONFLICT", "detail": str(exc)}

    legacy_bytes = canonical_json(PROJECT_CONFIG)
    migrate_identity = False
    expected: bytes
    project_contract: str

    if existing_config is None:
        if desired_v2 is None:
            expected = legacy_bytes
            project_contract = LEGACY_PROJECT_CONTRACT
        else:
            expected = canonical_json(desired_v2)
            project_contract = PROJECT_CONTRACT
    elif existing_bytes == legacy_bytes:
        if desired_v2 is None:
            expected = legacy_bytes
            project_contract = LEGACY_PROJECT_CONTRACT
        else:
            expected = canonical_json(desired_v2)
            project_contract = PROJECT_CONTRACT
            migrate_identity = True
    elif validate_project_config(existing_config) and existing_bytes == canonical_json(existing_config):
        if desired_v2 is not None and existing_config != desired_v2:
            return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PROJECT_CONFIG_CONFLICT", "detail": f"{CONFIG_PATH} already contains a different project identity"}
        expected = existing_bytes
        project_contract = PROJECT_CONTRACT
    else:
        return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PROJECT_CONFIG_CONFLICT", "detail": f"{CONFIG_PATH} already exists with unsupported content"}

    existed = {rel: (target / rel).exists() for rel in DIRS}
    config_existed = config_path.exists()

    created: list[str] = []
    updated: list[str] = []
    pk.mkdir(exist_ok=True)
    for rel in DIRS:
        path = target / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=False)
            created.append(rel)

    if not config_existed:
        config_path.write_bytes(expected)
        created.append(CONFIG_PATH)
    elif migrate_identity:
        tmp = config_path.with_name(config_path.name + ".identity.tmp")
        if tmp.exists() or tmp.is_symlink():
            return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "PATH_CONFLICT", "detail": f"{tmp.relative_to(target).as_posix()} already exists"}
        try:
            with open(tmp, "xb") as handle:
                handle.write(expected)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, config_path)
        finally:
            if tmp.exists() and not tmp.is_symlink():
                tmp.unlink()
        updated.append(CONFIG_PATH)

    created.sort()
    updated.sort()
    if updated:
        outcome = "PROJECT_IDENTITY_ESTABLISHED"
    elif not created:
        outcome = "ALREADY_BOOTSTRAPPED"
    elif not any(existed.values()) and not config_existed:
        outcome = "CREATED"
    else:
        outcome = "COMPLETED"

    return 0, {
        "contract": RESULT_CONTRACT,
        "status": "PASS",
        "outcome": outcome,
        "project_contract": project_contract,
        "created": created,
        "updated": updated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically initialize Reasoning Distiller project-owned state")
    parser.add_argument("--target", required=True, help="project repository root")
    parser.add_argument("--project-id")
    parser.add_argument("--project-name")
    parser.add_argument("--repository")
    parser.add_argument("--summary")
    args = parser.parse_args()

    identity_values = [args.project_id, args.project_name, args.repository, args.summary]
    if any(value is not None for value in identity_values) and not all(value is not None for value in identity_values):
        return fail("PROJECT_IDENTITY_INVALID", "--project-id, --project-name, --repository, and --summary must be supplied together")

    project = None
    if all(value is not None for value in identity_values):
        project = {
            "id": args.project_id,
            "name": args.project_name,
            "repository": args.repository,
            "summary": args.summary,
        }

    try:
        target = safe_target(args.target)
        code, result = bootstrap(target, project)
        emit(result)
        return code
    except (OSError, ValueError) as exc:
        return fail("TARGET_INVALID", str(exc))
    except Exception as exc:  # fail closed on unexpected implementation errors
        emit({"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "INTERNAL_ERROR", "detail": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
