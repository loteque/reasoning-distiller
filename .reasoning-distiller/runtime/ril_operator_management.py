#!/usr/bin/env python3
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from ril_mutation import (
    ContractError,
    apply_transition,
    digest,
    make_approval,
    make_proposal,
    operation_result,
    projection_status,
    replay,
    validate_approval,
    validate_proposal,
)
from ril_operators import CORE_CAPABILITIES, EMPTY_OPERATOR_STATE, DOMAIN, operator_paths

ORDINARY_CONFIRMATION = "ADMINISTER_OPERATORS"
ROOT_TRANSFER_CONFIRMATION = "TRANSFER_ROOT_OPERATOR"

ORDINARY_OPERATIONS = {
    "ADD_OPERATOR",
    "UPDATE_CAPABILITIES",
    "DISABLE_OPERATOR",
    "REENABLE_OPERATOR",
}
ROOT_TRANSFER_OPERATION = "TRANSFER_ROOT"


def _valid_operator_id(operator_id: Any) -> bool:
    return isinstance(operator_id, str) and operator_id.startswith("operator:") and len(operator_id) > len("operator:")


def _normalize_capabilities(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, list):
        raise ContractError("INVALID_CAPABILITY", "capabilities must be a list")
    values: set[str] = set()
    for capability in capabilities:
        if not isinstance(capability, str) or not capability:
            raise ContractError("INVALID_CAPABILITY", "capability names must be non-empty strings")
        if capability.startswith("rd:"):
            if capability not in CORE_CAPABILITIES:
                raise ContractError("INVALID_CAPABILITY", f"unknown Reasoning Distiller capability: {capability}")
        elif capability.startswith("project:"):
            if len(capability) <= len("project:"):
                raise ContractError("INVALID_CAPABILITY", "project capability namespace requires a non-empty name")
        else:
            raise ContractError("INVALID_CAPABILITY", "capabilities must use rd: or project: namespace")
        values.add(capability)
    return sorted(values)


def _load_registry(project_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    events_dir, projection_path = operator_paths(project_root)
    status = projection_status(events_dir, projection_path, EMPTY_OPERATOR_STATE)
    if status["status"] == "CONFLICT":
        raise ContractError("PROJECTION_CONFLICT", "operator projection conflicts with authoritative history")
    state, events = replay(events_dir, EMPTY_OPERATOR_STATE)
    if state == EMPTY_OPERATOR_STATE:
        raise ContractError("INITIAL_OPERATOR_REQUIRED", "initial operator must be established first")
    return state, events


def _validate_manager(state: dict[str, Any], operator_id: str) -> None:
    entry = state.get("operators", {}).get(operator_id)
    if not entry or entry.get("status") != "active" or "rd:operator_management" not in entry.get("capabilities", []):
        raise ContractError("APPROVER_NOT_AUTHORIZED", "approver must be an active operator with rd:operator_management")


def _ordinary_change(operation: str, target_operator_id: str, capabilities: list[str] | None = None) -> dict[str, Any]:
    if operation not in ORDINARY_OPERATIONS:
        raise ContractError("INVALID_OPERATOR_OPERATION", operation)
    if not _valid_operator_id(target_operator_id):
        raise ContractError("INVALID_OPERATOR_ID", "target operator_id must use non-empty operator: namespace")
    change: dict[str, Any] = {"target_operator_id": target_operator_id}
    if operation in {"ADD_OPERATOR", "UPDATE_CAPABILITIES"}:
        change["capabilities"] = _normalize_capabilities(capabilities)
    elif capabilities is not None:
        raise ContractError("INVALID_OPERATOR_OPERATION", "capabilities are not accepted for this operation")
    return change


def plan_operator_change(
    project_root: Path,
    operation: str,
    target_operator_id: str,
    capabilities: list[str] | None = None,
) -> dict[str, Any]:
    try:
        state, _ = _load_registry(project_root)
        change = _ordinary_change(operation, target_operator_id, capabilities)
        _ordinary_transition(state, operation, change)
        proposal = make_proposal(DOMAIN, operation, state, change)
        return operation_result("PASS", "PLANNED", proposal=proposal, proposal_digest=digest(proposal))
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)


def approve_operator_change(
    proposal: dict[str, Any],
    approving_operator_id: str,
    authentication_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    auth: dict[str, Any] = {"method": "human_confirmation", "confirmation": ORDINARY_CONFIRMATION}
    if authentication_evidence:
        auth["evidence"] = authentication_evidence
    return make_approval(proposal, approving_operator_id, auth)


def _validate_ordinary_proposal(proposal: dict[str, Any]) -> str:
    validate_proposal(proposal)
    if proposal["domain"] != DOMAIN or proposal["operation"] not in ORDINARY_OPERATIONS:
        raise ContractError("INVALID_OPERATOR_OPERATION", "proposal is not an ordinary operator-management transition")
    change = proposal["change"]
    if not isinstance(change, dict) or "target_operator_id" not in change:
        raise ContractError("INVALID_OPERATOR_OPERATION", "invalid operator-management change")
    expected = _ordinary_change(proposal["operation"], change["target_operator_id"], change.get("capabilities"))
    if change != expected:
        raise ContractError("INVALID_OPERATOR_OPERATION", "operator-management proposal change is not canonical")
    return proposal["operation"]


def _validate_ordinary_approval(approval: dict[str, Any], proposal: dict[str, Any]) -> None:
    validate_approval(approval, proposal)
    auth = approval["authentication"]
    if auth.get("method") != "human_confirmation" or auth.get("confirmation") != ORDINARY_CONFIRMATION:
        raise ContractError("HUMAN_CONFIRMATION_REQUIRED", f"explicit {ORDINARY_CONFIRMATION} confirmation is required")


def _ordinary_transition(current: Any, operation: str, change: Any) -> dict[str, Any]:
    if not isinstance(current, dict) or current == EMPTY_OPERATOR_STATE:
        raise ContractError("INITIAL_OPERATOR_REQUIRED", "operator registry is not established")
    state = copy.deepcopy(current)
    target = change["target_operator_id"]
    operators = state["operators"]
    root_id = state["root_operator_id"]

    if target == root_id:
        raise ContractError("ROOT_PROTECTED", "ordinary operator operations cannot mutate the protected root")

    if operation == "ADD_OPERATOR":
        if target in operators:
            raise ContractError("OPERATOR_ALREADY_EXISTS", target)
        operators[target] = {
            "status": "active",
            "protected_root": False,
            "capabilities": list(change["capabilities"]),
        }
    elif operation == "UPDATE_CAPABILITIES":
        if target not in operators:
            raise ContractError("OPERATOR_NOT_FOUND", target)
        operators[target]["capabilities"] = list(change["capabilities"])
    elif operation == "DISABLE_OPERATOR":
        if target not in operators:
            raise ContractError("OPERATOR_NOT_FOUND", target)
        operators[target]["status"] = "disabled"
    elif operation == "REENABLE_OPERATOR":
        if target not in operators:
            raise ContractError("OPERATOR_NOT_FOUND", target)
        operators[target]["status"] = "active"
    else:
        raise ContractError("INVALID_OPERATOR_OPERATION", operation)
    return state


def apply_operator_change(project_root: Path, proposal: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    events_dir, projection_path = operator_paths(project_root)
    try:
        operation = _validate_ordinary_proposal(proposal)
        _validate_ordinary_approval(approval, proposal)
        state, events = _load_registry(project_root)
        pd = digest(proposal)
        ad = digest(approval)
        consumed = next((e for e in events if e["proposal_digest"] == pd and e["approval_digest"] == ad), None)
        if consumed is None:
            _validate_manager(state, approval["operator_id"])
            _ordinary_transition(state, operation, proposal["change"])

        result = apply_transition(
            proposal=proposal,
            approval=approval,
            events_dir=events_dir,
            projection_path=projection_path,
            transition=lambda current, change: _ordinary_transition(current, operation, change),
            initial_state=EMPTY_OPERATOR_STATE,
        )
        return result
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)


def _root_transfer_change(from_operator_id: str, to_operator_id: str) -> dict[str, str]:
    if not _valid_operator_id(from_operator_id) or not _valid_operator_id(to_operator_id):
        raise ContractError("INVALID_OPERATOR_ID", "root transfer IDs must use non-empty operator: namespace")
    if from_operator_id == to_operator_id:
        raise ContractError("INVALID_ROOT_TRANSFER", "root transfer target must differ from current root")
    return {"from_operator_id": from_operator_id, "to_operator_id": to_operator_id}


def _validate_root_transfer_preconditions(state: dict[str, Any], change: dict[str, str]) -> None:
    source = change["from_operator_id"]
    target = change["to_operator_id"]
    if state.get("root_operator_id") != source:
        raise ContractError("ROOT_TRANSFER_SOURCE_MISMATCH", "proposal source is not the current protected root")
    target_entry = state.get("operators", {}).get(target)
    if target_entry is None:
        raise ContractError("OPERATOR_NOT_FOUND", target)
    if target_entry.get("status") != "active":
        raise ContractError("TARGET_INACTIVE", target)
    target_caps = set(target_entry.get("capabilities", []))
    missing = [cap for cap in CORE_CAPABILITIES if cap not in target_caps]
    if missing:
        raise ContractError("TARGET_MISSING_CORE_CAPABILITIES", ",".join(missing))
    if target_entry.get("protected_root"):
        raise ContractError("INVALID_ROOT_TRANSFER", "target is already marked protected root")


def plan_root_transfer(project_root: Path, to_operator_id: str) -> dict[str, Any]:
    try:
        state, _ = _load_registry(project_root)
        change = _root_transfer_change(state["root_operator_id"], to_operator_id)
        _validate_root_transfer_preconditions(state, change)
        proposal = make_proposal(DOMAIN, ROOT_TRANSFER_OPERATION, state, change)
        return operation_result("PASS", "PLANNED", proposal=proposal, proposal_digest=digest(proposal))
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)


def approve_root_transfer(
    proposal: dict[str, Any],
    current_root_operator_id: str,
    authentication_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    auth: dict[str, Any] = {"method": "human_confirmation", "confirmation": ROOT_TRANSFER_CONFIRMATION}
    if authentication_evidence:
        auth["evidence"] = authentication_evidence
    return make_approval(proposal, current_root_operator_id, auth)


def _validate_root_proposal(proposal: dict[str, Any]) -> dict[str, str]:
    validate_proposal(proposal)
    if proposal["domain"] != DOMAIN or proposal["operation"] != ROOT_TRANSFER_OPERATION:
        raise ContractError("INVALID_ROOT_TRANSFER", "proposal is not a root-transfer transition")
    change = proposal["change"]
    if not isinstance(change, dict) or set(change) != {"from_operator_id", "to_operator_id"}:
        raise ContractError("INVALID_ROOT_TRANSFER", "invalid root-transfer change")
    expected = _root_transfer_change(change["from_operator_id"], change["to_operator_id"])
    if change != expected:
        raise ContractError("INVALID_ROOT_TRANSFER", "root-transfer proposal change is not canonical")
    return change


def _validate_root_approval(approval: dict[str, Any], proposal: dict[str, Any], source_operator_id: str) -> None:
    validate_approval(approval, proposal)
    if approval["operator_id"] != source_operator_id:
        raise ContractError("ROOT_APPROVAL_REQUIRED", "root transfer must be approved by the current root identity")
    auth = approval["authentication"]
    if auth.get("method") != "human_confirmation" or auth.get("confirmation") != ROOT_TRANSFER_CONFIRMATION:
        raise ContractError("HUMAN_CONFIRMATION_REQUIRED", f"explicit {ROOT_TRANSFER_CONFIRMATION} confirmation is required")


def _root_transfer_transition(current: Any, change: Any) -> dict[str, Any]:
    if not isinstance(current, dict) or current == EMPTY_OPERATOR_STATE:
        raise ContractError("INITIAL_OPERATOR_REQUIRED", "operator registry is not established")
    _validate_root_transfer_preconditions(current, change)
    state = copy.deepcopy(current)
    old_root = change["from_operator_id"]
    new_root = change["to_operator_id"]
    state["operators"][old_root]["protected_root"] = False
    state["operators"][new_root]["protected_root"] = True
    state["root_operator_id"] = new_root
    return state


def apply_root_transfer(project_root: Path, proposal: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    events_dir, projection_path = operator_paths(project_root)
    try:
        change = _validate_root_proposal(proposal)
        _validate_root_approval(approval, proposal, change["from_operator_id"])
        state, events = _load_registry(project_root)
        pd = digest(proposal)
        ad = digest(approval)
        consumed = next((e for e in events if e["proposal_digest"] == pd and e["approval_digest"] == ad), None)
        if consumed is None:
            _validate_root_transfer_preconditions(state, change)

        return apply_transition(
            proposal=proposal,
            approval=approval,
            events_dir=events_dir,
            projection_path=projection_path,
            transition=_root_transfer_transition,
            initial_state=EMPTY_OPERATOR_STATE,
        )
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)
