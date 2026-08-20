#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ril_mutation import (
    ContractError,
    apply_transition,
    canonical_json_bytes,
    digest,
    make_approval,
    make_proposal,
    operation_result,
    projection_status,
    rebuild_projection,
    replay,
    validate_approval,
    validate_proposal,
)

REGISTRY_CONTRACT = "reasoning-distiller-operator-registry/1"
INITIAL_REQUEST_CONTRACT = "reasoning-distiller-initial-operator-request/1"
INITIAL_RESULT_CONTRACT = "reasoning-distiller-initial-operator-result/1"
DOMAIN = "operator_registry"
INITIAL_OPERATION = "INITIALIZE_ROOT"
CORE_CAPABILITIES = [
    "rd:operator_management",
    "rd:role_registry",
    "rd:steward_authorization",
]
EMPTY_OPERATOR_STATE: dict[str, Any] = {}


def operator_paths(project_root: Path) -> tuple[Path, Path]:
    base = project_root / "project-knowledge" / "operators"
    return base / "events", base / "current.json"


def initial_required(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = operator_paths(project_root)
    try:
        state, events = replay(events_dir, EMPTY_OPERATOR_STATE)
        if not events and state == EMPTY_OPERATOR_STATE:
            return operation_result("FAIL", "INITIAL_OPERATOR_REQUIRED")
        status = projection_status(events_dir, projection_path, EMPTY_OPERATOR_STATE)
        if status["status"] == "CONFLICT":
            return operation_result("FAIL", "PROJECTION_CONFLICT", projection_status=status)
        return operation_result("PASS", "OPERATOR_READY", root_operator_id=state.get("root_operator_id"))
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)


def _root_change(operator_id: str) -> dict[str, Any]:
    if not isinstance(operator_id, str) or not operator_id.startswith("operator:") or len(operator_id) <= len("operator:"):
        raise ContractError("INVALID_INITIAL_OPERATOR", "operator_id must use non-empty operator: namespace")
    return {
        "root_operator_id": operator_id,
        "operator": {
            "status": "active",
            "protected_root": True,
            "capabilities": list(CORE_CAPABILITIES),
        },
    }


def plan_initial_operator(project_root: Path, operator_id: str) -> dict[str, Any]:
    events_dir, _ = operator_paths(project_root)
    state, events = replay(events_dir, EMPTY_OPERATOR_STATE)
    if events or state != EMPTY_OPERATOR_STATE:
        return operation_result("FAIL", "ROOT_ALREADY_ESTABLISHED")
    proposal = make_proposal(DOMAIN, INITIAL_OPERATION, EMPTY_OPERATOR_STATE, _root_change(operator_id))
    return {
        "contract": INITIAL_REQUEST_CONTRACT,
        "status": "PASS",
        "outcome": "PLANNED",
        "proposal": proposal,
        "proposal_digest": digest(proposal),
    }


def approve_initial_operator(proposal: dict[str, Any], operator_id: str, authentication_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    validate_proposal(proposal)
    auth: dict[str, Any] = {
        "method": "human_confirmation",
        "confirmation": "ESTABLISH_ROOT_OPERATOR",
    }
    if authentication_evidence:
        auth["evidence"] = authentication_evidence
    return make_approval(proposal, operator_id, auth)


def _validate_initial_proposal(proposal: dict[str, Any]) -> str:
    validate_proposal(proposal)
    if proposal["domain"] != DOMAIN or proposal["operation"] != INITIAL_OPERATION:
        raise ContractError("INVALID_INITIAL_OPERATOR", "proposal is not an initial operator transition")
    if proposal["basis_digest"] != digest(EMPTY_OPERATOR_STATE):
        raise ContractError("INVALID_INITIAL_OPERATOR", "initial operator proposal must use empty-state basis")
    change = proposal["change"]
    if not isinstance(change, dict) or set(change) != {"root_operator_id", "operator"}:
        raise ContractError("INVALID_INITIAL_OPERATOR", "initial operator change shape is invalid")
    operator_id = change["root_operator_id"]
    expected = _root_change(operator_id)
    if change != expected:
        raise ContractError("INVALID_INITIAL_OPERATOR", "root operator must receive exact protected core capabilities")
    return operator_id


def _validate_initial_approval(approval: dict[str, Any], proposal: dict[str, Any], operator_id: str) -> None:
    validate_approval(approval, proposal)
    if approval["operator_id"] != operator_id:
        raise ContractError("INVALID_INITIAL_OPERATOR", "approving human identity must equal initial root operator")
    auth = approval["authentication"]
    if auth.get("method") != "human_confirmation" or auth.get("confirmation") != "ESTABLISH_ROOT_OPERATOR":
        raise ContractError("HUMAN_CONFIRMATION_REQUIRED", "explicit ESTABLISH_ROOT_OPERATOR confirmation is required")


def _transition(current: Any, change: Any) -> dict[str, Any]:
    if current != EMPTY_OPERATOR_STATE:
        raise ContractError("ROOT_ALREADY_ESTABLISHED", "initial root may only be established from empty operator state")
    operator_id = change["root_operator_id"]
    return {
        "contract": REGISTRY_CONTRACT,
        "root_operator_id": operator_id,
        "operators": {
            operator_id: change["operator"],
        },
    }


def apply_initial_operator(project_root: Path, proposal: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    events_dir, projection_path = operator_paths(project_root)
    try:
        operator_id = _validate_initial_proposal(proposal)
        _validate_initial_approval(approval, proposal, operator_id)
        state, events = replay(events_dir, EMPTY_OPERATOR_STATE)
        proposal_digest = digest(proposal)
        approval_digest = digest(approval)
        consumed = next((e for e in events if e["proposal_digest"] == proposal_digest and e["approval_digest"] == approval_digest), None)
        if events and consumed is None:
            return operation_result("FAIL", "ROOT_ALREADY_ESTABLISHED")
        result = apply_transition(
            proposal=proposal,
            approval=approval,
            events_dir=events_dir,
            projection_path=projection_path,
            transition=_transition,
            initial_state=EMPTY_OPERATOR_STATE,
        )
        result["contract"] = INITIAL_RESULT_CONTRACT
        if result["status"] == "PASS":
            result["root_operator_id"] = operator_id
        return result
    except ContractError as exc:
        return {
            "contract": INITIAL_RESULT_CONTRACT,
            "status": "FAIL",
            "outcome": exc.code,
            "detail": exc.detail,
        }


def rebuild_operator_projection(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = operator_paths(project_root)
    return rebuild_projection(events_dir, projection_path, EMPTY_OPERATOR_STATE)


def read_operator_registry(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = operator_paths(project_root)
    status = projection_status(events_dir, projection_path, EMPTY_OPERATOR_STATE)
    if status["status"] == "CONFLICT":
        return operation_result("FAIL", "PROJECTION_CONFLICT", projection_status=status)
    if status["status"] == "REBUILDABLE":
        rebuilt = rebuild_projection(events_dir, projection_path, EMPTY_OPERATOR_STATE)
        if rebuilt["status"] != "PASS":
            return rebuilt
    state, _ = replay(events_dir, EMPTY_OPERATOR_STATE)
    if state == EMPTY_OPERATOR_STATE:
        return operation_result("FAIL", "INITIAL_OPERATOR_REQUIRED")
    return operation_result("PASS", "OPERATOR_READY", registry=state)


def _emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    _emit(operation_result("FAIL", "LIBRARY_PRIMITIVE", "R4 is exposed as deterministic functions; public ril UX is not implemented yet"))
