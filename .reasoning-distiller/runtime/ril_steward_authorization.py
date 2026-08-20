#!/usr/bin/env python3
from __future__ import annotations

import copy
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
from ril_operators import EMPTY_OPERATOR_STATE, operator_paths
from ril_roles import DEFAULT_ROLE_STATE, role_paths

STATE_CONTRACT = "reasoning-distiller-steward-authorization-state/1"
DOMAIN = "steward_authorization"
CONFIRMATION = "STEWARD_AUTHORIZATION_CHANGE"
SCOPES = {"semantic_reconciliation", "admission"}
OPERATIONS = {"AUTHORIZE", "REASSIGN", "REVOKE"}

EMPTY_AUTH_STATE: dict[str, Any] = {
    "contract": STATE_CONTRACT,
    "assignments": {
        "admission": None,
        "semantic_reconciliation": None,
    },
}


def authorization_paths(project_root: Path) -> tuple[Path, Path]:
    base = project_root / "project-knowledge" / "steward-authorization"
    return base / "events", base / "current.json"


def evidence_paths(project_root: Path) -> tuple[Path, Path]:
    base = project_root / "project-knowledge" / "steward-authorization"
    return base / "proposals", base / "approvals"


def _load_authorization(project_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    events_dir, projection_path = authorization_paths(project_root)
    status = projection_status(events_dir, projection_path, EMPTY_AUTH_STATE)
    if status["status"] == "CONFLICT":
        raise ContractError("PROJECTION_CONFLICT", "Steward authorization projection conflicts with authoritative history")
    state, events = replay(events_dir, EMPTY_AUTH_STATE)
    return state, events


def _load_operator_state(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = operator_paths(project_root)
    status = projection_status(events_dir, projection_path, EMPTY_OPERATOR_STATE)
    if status["status"] == "CONFLICT":
        raise ContractError("OPERATOR_PROJECTION_CONFLICT", "operator projection conflicts with authoritative history")
    state, _ = replay(events_dir, EMPTY_OPERATOR_STATE)
    if state == EMPTY_OPERATOR_STATE:
        raise ContractError("INITIAL_OPERATOR_REQUIRED", "initial operator must be established first")
    return state


def _load_role_state(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = role_paths(project_root)
    status = projection_status(events_dir, projection_path, DEFAULT_ROLE_STATE)
    if status["status"] == "CONFLICT":
        raise ContractError("ROLE_PROJECTION_CONFLICT", "role projection conflicts with authoritative history")
    state, _ = replay(events_dir, DEFAULT_ROLE_STATE)
    return state


def _validate_approver(operator_state: dict[str, Any], operator_id: str) -> None:
    entry = operator_state.get("operators", {}).get(operator_id)
    if not entry or entry.get("status") != "active" or "rd:steward_authorization" not in entry.get("capabilities", []):
        raise ContractError("APPROVER_NOT_AUTHORIZED", "approver must be active and hold rd:steward_authorization")


def _validate_target(role_state: dict[str, Any], role_id: str) -> None:
    if not isinstance(role_id, str) or not role_id:
        raise ContractError("ROLE_REQUIRED", "role_id is required")
    entry = role_state.get("roles", {}).get(role_id)
    if entry is None:
        raise ContractError("ROLE_NOT_FOUND", role_id)
    if entry.get("status") != "available":
        raise ContractError("ROLE_UNAVAILABLE", role_id)


def _normalize_change(operation: str, scope: str, role_id: str | None) -> dict[str, Any]:
    if operation not in OPERATIONS:
        raise ContractError("INVALID_AUTHORIZATION_OPERATION", operation)
    if scope not in SCOPES:
        raise ContractError("UNKNOWN_SCOPE", scope)
    if operation == "REVOKE":
        if role_id is not None:
            raise ContractError("INVALID_AUTHORIZATION_OPERATION", "REVOKE does not accept role_id")
        return {"scope": scope, "role_id": None}
    if not isinstance(role_id, str) or not role_id:
        raise ContractError("ROLE_REQUIRED", f"{operation} requires role_id")
    return {"scope": scope, "role_id": role_id}


def _parse_proposal(proposal: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    validate_proposal(proposal)
    operation = proposal["operation"]
    if proposal["domain"] != DOMAIN or operation not in OPERATIONS:
        raise ContractError("INVALID_AUTHORIZATION_PROPOSAL", "proposal is not a Steward authorization transition")
    raw = proposal["change"]
    if not isinstance(raw, dict) or set(raw) != {"scope", "role_id"}:
        raise ContractError("INVALID_AUTHORIZATION_PROPOSAL", "authorization change shape is invalid")
    change = _normalize_change(operation, raw["scope"], raw["role_id"])
    if change != raw:
        raise ContractError("INVALID_AUTHORIZATION_PROPOSAL", "authorization change is not canonical")
    return operation, change


def _validate_transition_preconditions(state: dict[str, Any], operation: str, change: dict[str, Any], role_state: dict[str, Any] | None = None) -> None:
    scope = change["scope"]
    current = state["assignments"][scope]
    target = change["role_id"]
    if operation == "AUTHORIZE":
        if current is not None:
            raise ContractError("SCOPE_ALREADY_ASSIGNED", scope)
        assert target is not None
        if role_state is None:
            raise ContractError("ROLE_STATE_REQUIRED", "role state required for assignment")
        _validate_target(role_state, target)
    elif operation == "REASSIGN":
        if current is None:
            raise ContractError("SCOPE_UNASSIGNED", scope)
        if current == target:
            raise ContractError("NO_AUTHORIZATION_CHANGE", "target already holds scope")
        assert target is not None
        if role_state is None:
            raise ContractError("ROLE_STATE_REQUIRED", "role state required for assignment")
        _validate_target(role_state, target)
    elif operation == "REVOKE":
        if current is None:
            raise ContractError("SCOPE_UNASSIGNED", scope)
    else:
        raise ContractError("INVALID_AUTHORIZATION_OPERATION", operation)


def plan_authorization_change(project_root: Path, operation: str, scope: str, role_id: str | None = None) -> dict[str, Any]:
    try:
        state, _ = _load_authorization(project_root)
        change = _normalize_change(operation, scope, role_id)
        role_state = _load_role_state(project_root) if operation != "REVOKE" else None
        _validate_transition_preconditions(state, operation, change, role_state)
        proposal = make_proposal(DOMAIN, operation, state, change)
        return operation_result("PASS", "PLANNED", proposal=proposal, proposal_digest=digest(proposal))
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)


def approve_authorization_change(
    proposal: dict[str, Any],
    approving_operator_id: str,
    authentication_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    auth: dict[str, Any] = {"method": "human_confirmation", "confirmation": CONFIRMATION}
    if authentication_evidence:
        auth["evidence"] = authentication_evidence
    return make_approval(proposal, approving_operator_id, auth)


def _validate_approval(approval: dict[str, Any], proposal: dict[str, Any]) -> None:
    validate_approval(approval, proposal)
    auth = approval["authentication"]
    if auth.get("method") != "human_confirmation" or auth.get("confirmation") != CONFIRMATION:
        raise ContractError("HUMAN_CONFIRMATION_REQUIRED", f"explicit {CONFIRMATION} confirmation is required")


def _transition(current: Any, change: Any) -> dict[str, Any]:
    state = copy.deepcopy(current)
    state["assignments"][change["scope"]] = change["role_id"]
    return state


def _persist_artifact(directory: Path, artifact: dict[str, Any]) -> None:
    data = canonical_json_bytes(artifact)
    hex_digest = digest(artifact).split(":", 1)[1]
    path = directory / f"{hex_digest}.json"
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ContractError("EVIDENCE_CONFLICT", str(path))
        return
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "xb") as handle:
            handle.write(data)
            handle.flush()
    except FileExistsError:
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ContractError("EVIDENCE_CONFLICT", str(path))


def apply_authorization_change(project_root: Path, proposal: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    events_dir, projection_path = authorization_paths(project_root)
    proposals_dir, approvals_dir = evidence_paths(project_root)
    try:
        state, events = _load_authorization(project_root)
        operation, change = _parse_proposal(proposal)
        _validate_approval(approval, proposal)
        pd = digest(proposal)
        ad = digest(approval)
        consumed = next((e for e in events if e["proposal_digest"] == pd and e["approval_digest"] == ad), None)
        if consumed is None:
            role_state = _load_role_state(project_root) if operation != "REVOKE" else None
            _validate_transition_preconditions(state, operation, change, role_state)
            operator_state = _load_operator_state(project_root)
            _validate_approver(operator_state, approval["operator_id"])
        _persist_artifact(proposals_dir, proposal)
        _persist_artifact(approvals_dir, approval)
        return apply_transition(
            proposal=proposal,
            approval=approval,
            events_dir=events_dir,
            projection_path=projection_path,
            transition=_transition,
            initial_state=EMPTY_AUTH_STATE,
        )
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)


def rebuild_authorization_projection(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = authorization_paths(project_root)
    return rebuild_projection(events_dir, projection_path, EMPTY_AUTH_STATE)


def read_authorization(project_root: Path) -> dict[str, Any]:
    try:
        events_dir, projection_path = authorization_paths(project_root)
        status = projection_status(events_dir, projection_path, EMPTY_AUTH_STATE)
        if status["status"] == "CONFLICT":
            return operation_result("FAIL", "PROJECTION_CONFLICT", projection_status=status)
        if status["status"] == "REBUILDABLE":
            rebuilt = rebuild_projection(events_dir, projection_path, EMPTY_AUTH_STATE)
            if rebuilt["status"] != "PASS":
                return rebuilt
        state, _ = replay(events_dir, EMPTY_AUTH_STATE)
        return operation_result("PASS", "STEWARD_AUTHORIZATION_READY", authorization=state)
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)
