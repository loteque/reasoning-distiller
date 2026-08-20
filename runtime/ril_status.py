#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rd_bootstrap import PROJECT_CONFIG, canonical_json, validate_project_config
from ril_mutation import ContractError, projection_status, replay
from ril_operators import EMPTY_OPERATOR_STATE, operator_paths
from ril_roles import DEFAULT_ROLE_STATE, role_paths
from ril_steward_authorization import EMPTY_AUTH_STATE, authorization_paths

STATUS_CONTRACT = "reasoning-distiller-status/1"


def _installation(project_root: Path) -> str:
    path = project_root / ".reasoning-distiller"
    if not path.exists():
        return "MISSING"
    if path.is_symlink() or not path.is_dir():
        return "INCOMPATIBLE"
    return "VALID"


def _project_bootstrap(project_root: Path) -> str:
    pk = project_root / "project-knowledge"
    config = pk / "project.json"
    if not pk.exists() and not config.exists():
        return "MISSING"
    if not pk.exists() or pk.is_symlink() or not pk.is_dir():
        return "CONFLICT"
    if not config.exists():
        return "MISSING"
    if config.is_symlink() or not config.is_file():
        return "CONFLICT"
    try:
        raw = config.read_bytes()
        if raw == canonical_json(PROJECT_CONFIG):
            return "VALID"
        value = json.loads(raw.decode("utf-8"))
        return "VALID" if validate_project_config(value) and raw == canonical_json(value) else "CONFLICT"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "CONFLICT"


def _inspect_domain(events_dir: Path, projection_path: Path, initial_state: Any) -> dict[str, Any]:
    try:
        state, events = replay(events_dir, initial_state)
    except ContractError as exc:
        return {
            "history": "INVALID",
            "projection": "CONFLICT",
            "state": None,
            "event_count": None,
            "reason_code": exc.code,
        }
    pstatus = projection_status(events_dir, projection_path, initial_state)
    projection = pstatus["status"]
    result: dict[str, Any] = {
        "history": "VALID",
        "projection": projection,
        "state": state,
        "event_count": len(events),
    }
    if projection == "CONFLICT":
        result["reason_code"] = pstatus.get("reason_code", "PROJECTION_CONFLICT")
    return result


def _has_normal_file(path: Path) -> bool:
    if not path.exists() or path.is_symlink() or not path.is_dir():
        return False
    try:
        for item in path.rglob("*"):
            if item.is_file() and not item.is_symlink():
                return True
    except OSError:
        return False
    return False


def _authority_state(auth_state: dict[str, Any] | None, role_state: dict[str, Any] | None, scope: str) -> str:
    if auth_state is None or role_state is None:
        return "CONFLICT"
    role_id = auth_state.get("assignments", {}).get(scope)
    if role_id is None:
        return "UNASSIGNED"
    entry = role_state.get("roles", {}).get(role_id)
    if entry is None or entry.get("status") != "available":
        return "TARGET_UNAVAILABLE"
    return "AVAILABLE"


def _aggregate_projection(domains: dict[str, dict[str, Any]]) -> str:
    states = [info["projection"] for info in domains.values() if info["history"] == "VALID"]
    if any(state == "CONFLICT" for state in states):
        return "CONFLICT"
    if any(state == "REBUILDABLE" for state in states):
        return "REBUILDABLE"
    return "VALID"


def _blocker(precedence: int, code: str, dimension: str) -> dict[str, Any]:
    return {"precedence": precedence, "code": code, "dimension": dimension}


def classify_status(project_root: Path) -> dict[str, Any]:
    installation = _installation(project_root)
    bootstrap = _project_bootstrap(project_root)

    # Lower-level state is inspected only when project-owned paths can be meaningful.
    operator_info = _inspect_domain(*operator_paths(project_root), EMPTY_OPERATOR_STATE)
    role_info = _inspect_domain(*role_paths(project_root), DEFAULT_ROLE_STATE)
    auth_info = _inspect_domain(*authorization_paths(project_root), EMPTY_AUTH_STATE)
    domains = {
        "operator": operator_info,
        "role_registry": role_info,
        "steward_authorization": auth_info,
    }

    history_health = "INVALID" if any(v["history"] == "INVALID" for v in domains.values()) else "VALID"
    projection_health = _aggregate_projection(domains)

    operator_state = operator_info["state"]
    if operator_info["history"] == "INVALID" or operator_info["projection"] == "CONFLICT":
        operator = "CONFLICT"
    elif operator_state == EMPTY_OPERATOR_STATE:
        operator = "MISSING"
    else:
        operator = "VALID"

    if role_info["history"] == "INVALID" or role_info["projection"] == "CONFLICT":
        role_registry = "CONFLICT"
    elif role_info["projection"] == "REBUILDABLE":
        role_registry = "REBUILDABLE"
    else:
        role_registry = "VALID"

    reconciliation_authority = _authority_state(auth_info["state"], role_info["state"], "semantic_reconciliation")
    admission_authority = _authority_state(auth_info["state"], role_info["state"], "admission")

    evidence = "AVAILABLE" if _has_normal_file(project_root / "project-knowledge" / "evidence") else "NONE"
    candidate = "PENDING" if _has_normal_file(project_root / "project-knowledge" / "submissions") else "NONE"

    if candidate == "NONE":
        reconciliation = "NOT_REQUIRED"
    elif reconciliation_authority == "AVAILABLE":
        reconciliation = "REQUIRED"
    else:
        reconciliation = "BLOCKED"
    admission = "NOT_READY"

    dimensions = {
        "installation": installation,
        "project_bootstrap": bootstrap,
        "operator": operator,
        "role_registry": role_registry,
        "reconciliation_authority": reconciliation_authority,
        "admission_authority": admission_authority,
        "projection_health": projection_health,
        "history_health": history_health,
        "evidence": evidence,
        "candidate": candidate,
        "reconciliation": reconciliation,
        "admission": admission,
    }

    blocker: dict[str, Any] | None = None
    next_action = "READY"

    if installation == "MISSING":
        blocker = _blocker(1, "INSTALLATION_MISSING", "installation")
        next_action = "INSTALL"
    elif installation == "INCOMPATIBLE":
        blocker = _blocker(1, "INSTALLATION_INCOMPATIBLE", "installation")
        next_action = "INSTALL"
    elif bootstrap == "MISSING":
        blocker = _blocker(1, "PROJECT_BOOTSTRAP_MISSING", "project_bootstrap")
        next_action = "BOOTSTRAP_PROJECT"
    elif bootstrap == "CONFLICT":
        blocker = _blocker(1, "PROJECT_BOOTSTRAP_CONFLICT", "project_bootstrap")
        next_action = "BOOTSTRAP_PROJECT"
    elif history_health == "INVALID":
        blocker = _blocker(2, "AUTHORITATIVE_HISTORY_INVALID", "history_health")
        next_action = "REPAIR_HISTORY"
    elif projection_health == "CONFLICT":
        blocker = _blocker(3, "PROJECTION_CONFLICT", "projection_health")
        next_action = "REPAIR_PROJECTION"
    elif operator == "MISSING":
        blocker = _blocker(4, "INITIAL_OPERATOR_REQUIRED", "operator")
        next_action = "ESTABLISH_INITIAL_OPERATOR"
    elif candidate == "PENDING" and reconciliation_authority == "UNASSIGNED":
        blocker = _blocker(5, "RECONCILIATION_AUTHORITY_UNASSIGNED", "reconciliation_authority")
        next_action = "AUTHORIZE_RECONCILIATION_STEWARD"
    elif candidate == "PENDING" and reconciliation_authority == "TARGET_UNAVAILABLE":
        blocker = _blocker(5, "RECONCILIATION_TARGET_UNAVAILABLE", "reconciliation_authority")
        next_action = "RESTORE_RECONCILIATION_ROLE"
    elif candidate == "PENDING" and reconciliation_authority == "CONFLICT":
        blocker = _blocker(5, "RECONCILIATION_AUTHORITY_CONFLICT", "reconciliation_authority")
        next_action = "REPAIR_PROJECTION"
    elif candidate == "PENDING" and reconciliation_authority == "AVAILABLE":
        blocker = _blocker(6, "ACTIVATION_EVIDENCE_REQUIRED", "reconciliation")
        next_action = "PROVIDE_ACTIVATION_EVIDENCE"
    elif evidence == "NONE":
        blocker = _blocker(7, "EVIDENCE_REQUIRED", "evidence")
        next_action = "ADD_EVIDENCE"
    elif candidate == "NONE":
        next_action = "RUN_DISTILLER"

    if installation != "VALID":
        lifecycle = "UNINSTALLED"
    elif bootstrap != "VALID":
        lifecycle = "INSTALLED"
    elif candidate == "PENDING" and reconciliation_authority == "AVAILABLE":
        lifecycle = "RECONCILIATION_REQUIRED"
    elif candidate == "PENDING":
        lifecycle = "CANDIDATE_READY"
    elif evidence == "AVAILABLE":
        lifecycle = "EVIDENCE_READY"
    else:
        lifecycle = "INITIALIZED"

    return {
        "contract": STATUS_CONTRACT,
        "status": "PASS",
        "dimensions": dimensions,
        "blocker": blocker,
        "next_action": next_action,
        "lifecycle": lifecycle,
        "domain_health": {
            name: {
                "history": info["history"],
                "projection": info["projection"],
                "event_count": info["event_count"],
                **({"reason_code": info["reason_code"]} if "reason_code" in info else {}),
            }
            for name, info in domains.items()
        },
    }


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    print(json.dumps(classify_status(root), sort_keys=True, separators=(",", ":"), ensure_ascii=False))
