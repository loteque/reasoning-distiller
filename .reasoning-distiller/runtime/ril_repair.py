#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ril_mutation import ContractError, canonical_json_bytes, digest, replay
from ril_operators import EMPTY_OPERATOR_STATE, operator_paths
from ril_roles import DEFAULT_ROLE_STATE, role_paths
from ril_steward_authorization import EMPTY_AUTH_STATE, authorization_paths

RESULT_CONTRACT = "reasoning-distiller-ordinary-repair-result/1"

DOMAIN_ORDER = (
    "operator_registry",
    "role_registry",
    "steward_authorization",
)


def _domain_spec(project_root: Path, domain: str) -> tuple[Path, Path, Any]:
    if domain == "operator_registry":
        events_dir, projection_path = operator_paths(project_root)
        return events_dir, projection_path, EMPTY_OPERATOR_STATE
    if domain == "role_registry":
        events_dir, projection_path = role_paths(project_root)
        return events_dir, projection_path, DEFAULT_ROLE_STATE
    if domain == "steward_authorization":
        events_dir, projection_path = authorization_paths(project_root)
        return events_dir, projection_path, EMPTY_AUTH_STATE
    raise ContractError("UNKNOWN_REPAIR_DOMAIN", domain)


def _result(status: str, outcome: str, domain: str, detail: str | None = None, **extra: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "status": status,
        "outcome": outcome,
        "domain": domain,
    }
    if detail:
        value["detail"] = detail
    value.update(extra)
    return value


def _validate_history(project_root: Path, domain: str) -> tuple[Any, int] | dict[str, Any]:
    events_dir, _, initial_state = _domain_spec(project_root, domain)
    try:
        state, events = replay(events_dir, initial_state)
        return state, len(events)
    except ContractError as exc:
        return _result(
            "FAIL",
            "EXCEPTIONAL_RECOVERY_REQUIRED",
            domain,
            exc.detail,
            reason_code=exc.code,
        )


def _projection_path_safe(path: Path) -> bool:
    if path.exists():
        return path.is_file() and not path.is_symlink()
    parent = path.parent
    if parent.exists() and (not parent.is_dir() or parent.is_symlink()):
        return False
    return True


def _replace_projection(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise ContractError("PROJECTION_PATH_CONFLICT", "projection parent must be a normal directory")
    temp = path.with_name(path.name + ".repair.tmp")
    if temp.exists() or temp.is_symlink():
        raise ContractError("PROJECTION_PATH_CONFLICT", f"temporary repair path already exists: {temp}")
    try:
        with open(temp, "xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists() and not temp.is_symlink():
            temp.unlink()


def _apply_validated_repair(project_root: Path, domain: str, state: Any, event_count: int) -> dict[str, Any]:
    _, projection_path, _ = _domain_spec(project_root, domain)
    if not _projection_path_safe(projection_path):
        return _result("FAIL", "PROJECTION_PATH_CONFLICT", domain)

    expected = canonical_json_bytes(state)
    expected_digest = digest(state)
    if projection_path.exists():
        try:
            current = projection_path.read_bytes()
        except OSError as exc:
            return _result("FAIL", "PROJECTION_PATH_CONFLICT", domain, str(exc))
        if current == expected:
            return _result(
                "PASS",
                "NO_CHANGE",
                domain,
                projection_digest=expected_digest,
                event_count=event_count,
            )
        outcome = "REPAIRED"
    else:
        outcome = "REBUILT"

    try:
        _replace_projection(projection_path, expected)
    except (ContractError, OSError) as exc:
        detail = exc.detail if isinstance(exc, ContractError) else str(exc)
        return _result("FAIL", "PROJECTION_PATH_CONFLICT", domain, detail)

    return _result(
        "PASS",
        outcome,
        domain,
        projection_digest=expected_digest,
        event_count=event_count,
    )


def repair_domain(project_root: Path, domain: str) -> dict[str, Any]:
    try:
        validated = _validate_history(project_root, domain)
    except ContractError as exc:
        return _result("FAIL", exc.code, domain, exc.detail)
    if isinstance(validated, dict):
        return validated
    state, event_count = validated
    return _apply_validated_repair(project_root, domain, state, event_count)


def repair_all(project_root: Path) -> dict[str, Any]:
    validated: dict[str, tuple[Any, int]] = {}

    # Preflight every authoritative history before changing any projection.
    for domain in DOMAIN_ORDER:
        try:
            result = _validate_history(project_root, domain)
        except ContractError as exc:
            return _result("FAIL", exc.code, "all", exc.detail, failed_domain=domain)
        if isinstance(result, dict):
            return _result(
                "FAIL",
                "EXCEPTIONAL_RECOVERY_REQUIRED",
                "all",
                result.get("detail"),
                failed_domain=domain,
                reason_code=result.get("reason_code"),
            )
        validated[domain] = result

    # Preflight projection paths globally to avoid partial repair on known conflicts.
    for domain in DOMAIN_ORDER:
        _, projection_path, _ = _domain_spec(project_root, domain)
        if not _projection_path_safe(projection_path):
            return _result(
                "FAIL",
                "PROJECTION_PATH_CONFLICT",
                "all",
                failed_domain=domain,
            )

    repairs: dict[str, dict[str, Any]] = {}
    for domain in DOMAIN_ORDER:
        state, event_count = validated[domain]
        result = _apply_validated_repair(project_root, domain, state, event_count)
        if result["status"] != "PASS":
            return _result(
                "FAIL",
                result["outcome"],
                "all",
                result.get("detail"),
                failed_domain=domain,
                repairs=repairs,
            )
        repairs[domain] = {
            "outcome": result["outcome"],
            "projection_digest": result["projection_digest"],
            "event_count": result["event_count"],
        }

    outcomes = {item["outcome"] for item in repairs.values()}
    if outcomes == {"NO_CHANGE"}:
        outcome = "NO_CHANGE"
    elif "REPAIRED" in outcomes:
        outcome = "REPAIRED"
    else:
        outcome = "REBUILT"
    return _result("PASS", outcome, "all", repairs=repairs)


if __name__ == "__main__":
    import json
    import sys

    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    domain = sys.argv[2] if len(sys.argv) > 2 else "all"
    value = repair_all(root) if domain == "all" else repair_domain(root, domain)
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
