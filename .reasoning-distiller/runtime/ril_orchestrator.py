#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from ril_admission import admit
from ril_operator_management import (
    apply_operator_change,
    apply_root_transfer,
    approve_operator_change,
    approve_root_transfer,
    plan_operator_change,
    plan_root_transfer,
)
from ril_operators import apply_initial_operator, approve_initial_operator, plan_initial_operator
from ril_reconciliation import reconcile_candidate
from ril_repair import repair_all, repair_domain
from ril_roles import apply_role_submission, approve_role_submission, plan_role_submission
from ril_status import classify_status
from ril_steward_authorization import (
    apply_authorization_change,
    approve_authorization_change,
    plan_authorization_change,
)
from ril_storage_verification import verify_storage

REQUEST_CONTRACT = "reasoning-distiller-orchestrator-request/1"
RESULT_CONTRACT = "reasoning-distiller-orchestrator-result/1"


def _fail(action: str | None, outcome: str, detail: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"contract": RESULT_CONTRACT, "status": "FAIL", "outcome": outcome}
    if action is not None:
        out["action"] = action
    if detail:
        out["detail"] = detail
    return out


def _ok(action: str, primitive: str, result: Any) -> dict[str, Any]:
    return {
        "contract": RESULT_CONTRACT,
        "status": "PASS",
        "action": action,
        "primitive": primitive,
        "result": result,
    }


def _exact(arguments: Any, required: set[str], optional: set[str] | None = None) -> dict[str, Any]:
    optional = optional or set()
    if not isinstance(arguments, dict):
        raise ValueError("arguments must be an object")
    keys = set(arguments)
    if not required.issubset(keys):
        raise ValueError(f"missing arguments: {','.join(sorted(required - keys))}")
    extra = keys - required - optional
    if extra:
        raise ValueError(f"unexpected arguments: {','.join(sorted(extra))}")
    return arguments


def _route(project_root: Path, package_root: Path, action: str, args: dict[str, Any]) -> tuple[str, Any]:
    if action == "STATUS":
        _exact(args, set())
        return "ril_status.classify_status", classify_status(project_root)
    if action == "VERIFY_STORAGE":
        _exact(args, set())
        return "ril_storage_verification.verify_storage", verify_storage(project_root, package_root)
    if action == "REPAIR_ALL":
        _exact(args, set())
        return "ril_repair.repair_all", repair_all(project_root)
    if action == "REPAIR_DOMAIN":
        a = _exact(args, {"domain"})
        return "ril_repair.repair_domain", repair_domain(project_root, a["domain"])
    if action == "RECONCILE":
        a = _exact(args, {"candidate_path", "activation", "assessment"})
        return "ril_reconciliation.reconcile_candidate", reconcile_candidate(project_root, Path(a["candidate_path"]), a["activation"], a["assessment"])
    if action == "ADMIT":
        a = _exact(args, {"disposition_path", "activation", "plan"})
        return "ril_admission.admit", admit(project_root, Path(a["disposition_path"]), a["activation"], a["plan"])
    if action == "INITIAL_OPERATOR_PLAN":
        a = _exact(args, {"operator_id"})
        return "ril_operators.plan_initial_operator", plan_initial_operator(project_root, a["operator_id"])
    if action == "INITIAL_OPERATOR_APPROVE":
        a = _exact(args, {"proposal", "operator_id"}, {"authentication_evidence"})
        return "ril_operators.approve_initial_operator", approve_initial_operator(a["proposal"], a["operator_id"], a.get("authentication_evidence"))
    if action == "INITIAL_OPERATOR_APPLY":
        a = _exact(args, {"proposal", "approval"})
        return "ril_operators.apply_initial_operator", apply_initial_operator(project_root, a["proposal"], a["approval"])
    if action == "OPERATOR_PLAN":
        a = _exact(args, {"operation", "target_operator_id"}, {"capabilities"})
        return "ril_operator_management.plan_operator_change", plan_operator_change(project_root, a["operation"], a["target_operator_id"], a.get("capabilities"))
    if action == "OPERATOR_APPROVE":
        a = _exact(args, {"proposal", "operator_id"}, {"authentication_evidence"})
        return "ril_operator_management.approve_operator_change", approve_operator_change(a["proposal"], a["operator_id"], a.get("authentication_evidence"))
    if action == "OPERATOR_APPLY":
        a = _exact(args, {"proposal", "approval"})
        return "ril_operator_management.apply_operator_change", apply_operator_change(project_root, a["proposal"], a["approval"])
    if action == "ROOT_TRANSFER_PLAN":
        a = _exact(args, {"to_operator_id"})
        return "ril_operator_management.plan_root_transfer", plan_root_transfer(project_root, a["to_operator_id"])
    if action == "ROOT_TRANSFER_APPROVE":
        a = _exact(args, {"proposal", "operator_id"}, {"authentication_evidence"})
        return "ril_operator_management.approve_root_transfer", approve_root_transfer(a["proposal"], a["operator_id"], a.get("authentication_evidence"))
    if action == "ROOT_TRANSFER_APPLY":
        a = _exact(args, {"proposal", "approval"})
        return "ril_operator_management.apply_root_transfer", apply_root_transfer(project_root, a["proposal"], a["approval"])
    if action == "ROLE_SUBMISSION_PLAN":
        a = _exact(args, {"submission"})
        return "ril_roles.plan_role_submission", plan_role_submission(project_root, a["submission"])
    if action == "ROLE_SUBMISSION_APPROVE":
        a = _exact(args, {"proposal", "operator_id"}, {"authentication_evidence"})
        return "ril_roles.approve_role_submission", approve_role_submission(a["proposal"], a["operator_id"], a.get("authentication_evidence"))
    if action == "ROLE_SUBMISSION_APPLY":
        a = _exact(args, {"proposal", "approval"})
        return "ril_roles.apply_role_submission", apply_role_submission(project_root, a["proposal"], a["approval"])
    if action == "STEWARD_AUTH_PLAN":
        a = _exact(args, {"operation", "scope"}, {"role_id"})
        return "ril_steward_authorization.plan_authorization_change", plan_authorization_change(project_root, a["operation"], a["scope"], a.get("role_id"))
    if action == "STEWARD_AUTH_APPROVE":
        a = _exact(args, {"proposal", "operator_id"}, {"authentication_evidence"})
        return "ril_steward_authorization.approve_authorization_change", approve_authorization_change(a["proposal"], a["operator_id"], a.get("authentication_evidence"))
    if action == "STEWARD_AUTH_APPLY":
        a = _exact(args, {"proposal", "approval"})
        return "ril_steward_authorization.apply_authorization_change", apply_authorization_change(project_root, a["proposal"], a["approval"])
    raise KeyError(action)


def orchestrate(project_root: Path, request: dict[str, Any], package_root: Path | None = None) -> dict[str, Any]:
    if not isinstance(request, dict) or set(request) != {"contract", "action", "arguments"}:
        return _fail(None, "INVALID_ORCHESTRATOR_REQUEST", "request fields do not match contract")
    if request.get("contract") != REQUEST_CONTRACT:
        return _fail(request.get("action") if isinstance(request.get("action"), str) else None, "INVALID_ORCHESTRATOR_REQUEST", "unsupported request contract")
    action = request.get("action")
    if not isinstance(action, str) or not action:
        return _fail(None, "INVALID_ORCHESTRATOR_REQUEST", "action must be a non-empty string")
    try:
        primitive, result = _route(project_root, (package_root or Path(__file__).resolve().parents[1]).resolve(), action, request["arguments"])
        return _ok(action, primitive, result)
    except KeyError:
        return _fail(action, "UNKNOWN_ACTION")
    except (TypeError, ValueError) as exc:
        return _fail(action, "INVALID_ACTION_ARGUMENTS", str(exc))


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    print(json.dumps(_fail(None, "LIBRARY_PRIMITIVE", "R15 composition is exposed as orchestrate(); public ril UX is R16"), sort_keys=True, separators=(",", ":")))
