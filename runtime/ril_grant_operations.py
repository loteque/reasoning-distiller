#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import ril_authority_grant as grants
import ril_governance as governance
import ril_mutation as mutation
import ril_operator_management as operators
import ril_roles as roles
from ril_operators import EMPTY_OPERATOR_STATE, operator_paths

# G3 deliberately loads its mutation substrate under an isolated module name.
# G4 is the integration boundary, so expose one stable exception identity here
# and normalize lower-layer contract failures into it.
ContractError = grants.ContractError

ROLE_OPERATION_CLASS = "role-registry.change"
OPERATOR_DISABLE_OPERATION_CLASS = "operator-registry.disable"


def _normalize_contract_error(exc: Exception) -> ContractError:
    if isinstance(exc, ContractError):
        return exc
    code = getattr(exc, "code", "CONTRACT_ERROR")
    detail = getattr(exc, "detail", str(exc))
    return ContractError(code, detail)


def _load_authoritative_operator_state(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = operator_paths(project_root)
    status = mutation.projection_status(events_dir, projection_path, EMPTY_OPERATOR_STATE)
    if status["status"] == "CONFLICT":
        raise ContractError("OPERATOR_PROJECTION_CONFLICT", "operator projection conflicts with authoritative history")
    state, _ = mutation.replay(events_dir, EMPTY_OPERATOR_STATE)
    if state == EMPTY_OPERATOR_STATE:
        raise ContractError("INITIAL_OPERATOR_REQUIRED", "initial operator must be established first")
    return state


def validate_grant_creation_authority(
    project_root: Path,
    grant: dict[str, Any],
    *,
    workflow_contains_grant_scope: bool,
) -> None:
    """Operation-specific authority check performed before durable grant creation."""
    grants.validate_grant(grant)
    if not workflow_contains_grant_scope:
        raise ContractError("GRANT_OUTSIDE_WORKFLOW", "grant scope must be a subset of immutable workflow intent")
    state = _load_authoritative_operator_state(project_root)
    grantor = grant["payload"]["grantor"]
    entry = state.get("operators", {}).get(grantor)
    if not entry or entry.get("status") != "active":
        raise ContractError("GRANTOR_NOT_AUTHORIZED", "grantor must be an active operator")
    capabilities = set(entry.get("capabilities", []))
    for operation_class in grant["payload"]["scope"]["operations"]:
        metadata = governance.delegation_metadata(operation_class)
        if not metadata.get("delegable"):
            raise ContractError("NON_DELEGABLE", operation_class)
        required = metadata.get("grantor_capability")
        if required and required not in capabilities:
            raise ContractError("GRANTOR_NOT_AUTHORIZED", f"grantor lacks {required} for {operation_class}")


def create_authorized_grant(
    project_root: Path,
    grant_store: Path,
    grant: dict[str, Any],
    *,
    workflow_contains_grant_scope: bool,
) -> str:
    validate_grant_creation_authority(
        project_root,
        grant,
        workflow_contains_grant_scope=workflow_contains_grant_scope,
    )
    return grants.create_grant(grant_store, grant)


def role_authority_fields(proposal: dict[str, Any]) -> dict[str, Any]:
    change = roles._validate_proposal_shape(proposal)
    role_ids = sorted({item["role_id"] for item in change["changes"]})
    mutation_kinds = sorted({item["action"] for item in change["changes"]})
    return {
        "role_id": role_ids,
        "mutation_kinds": mutation_kinds,
        "role_ids": role_ids,
        "submission_mode": change["submission"]["mode"],
    }


def operator_disable_authority_fields(proposal: dict[str, Any]) -> dict[str, Any]:
    try:
        operation = operators._validate_ordinary_proposal(proposal)
    except Exception as exc:
        if hasattr(exc, "code"):
            raise _normalize_contract_error(exc) from exc
        raise
    if operation != "DISABLE_OPERATOR":
        raise ContractError("NON_DELEGABLE", f"{operation} is not grant-delegable")
    return {
        "operator_id": proposal["change"]["target_operator_id"],
        "operation": "DISABLE_OPERATOR",
    }


def issue_role_grant_approval(
    project_root: Path,
    grant_store: Path,
    grant_ref: str,
    proposal: dict[str, Any],
    *,
    workflow_ref: str,
    workflow_lifecycle: str,
    workflow_condition: str,
    workflow_contains_proposal: bool,
    expected_grant_head: str | None,
) -> dict[str, Any]:
    try:
        state, _ = roles._load_role_state(project_root)
        roles._validate_proposal_semantics(state, proposal)
        _load_authoritative_operator_state(project_root)
    except Exception as exc:
        if hasattr(exc, "code"):
            raise _normalize_contract_error(exc) from exc
        raise
    return grants.issue_approval(
        grant_store,
        grant_ref,
        proposal,
        operation_class=ROLE_OPERATION_CLASS,
        authority_fields=role_authority_fields(proposal),
        workflow_ref=workflow_ref,
        workflow_lifecycle=workflow_lifecycle,
        workflow_condition=workflow_condition,
        workflow_contains_proposal=workflow_contains_proposal,
        current_state=state,
        expected_normative_head=expected_grant_head,
    )


def issue_operator_disable_grant_approval(
    project_root: Path,
    grant_store: Path,
    grant_ref: str,
    proposal: dict[str, Any],
    *,
    workflow_ref: str,
    workflow_lifecycle: str,
    workflow_condition: str,
    workflow_contains_proposal: bool,
    expected_grant_head: str | None,
) -> dict[str, Any]:
    try:
        state, _ = operators._load_registry(project_root)
        operation = operators._validate_ordinary_proposal(proposal)
        if operation != "DISABLE_OPERATOR":
            raise ContractError("NON_DELEGABLE", f"{operation} is not grant-delegable")
        operators._ordinary_transition(state, operation, proposal["change"])
    except Exception as exc:
        if hasattr(exc, "code"):
            raise _normalize_contract_error(exc) from exc
        raise
    return grants.issue_approval(
        grant_store,
        grant_ref,
        proposal,
        operation_class=OPERATOR_DISABLE_OPERATION_CLASS,
        authority_fields=operator_disable_authority_fields(proposal),
        workflow_ref=workflow_ref,
        workflow_lifecycle=workflow_lifecycle,
        workflow_condition=workflow_condition,
        workflow_contains_proposal=workflow_contains_proposal,
        current_state=state,
        expected_normative_head=expected_grant_head,
    )


def _is_grant_approval(approval: dict[str, Any]) -> bool:
    return (
        isinstance(approval, dict)
        and approval.get("contract") == mutation.APPROVAL_V2_CONTRACT
        and isinstance(approval.get("authority_basis"), dict)
        and approval["authority_basis"].get("kind") == "authority-grant"
    )


def apply_role_submission_with_authority(
    project_root: Path,
    grant_store: Path,
    proposal: dict[str, Any],
    approval: dict[str, Any],
) -> dict[str, Any]:
    if not _is_grant_approval(approval):
        return roles.apply_role_submission(project_root, proposal, approval)

    events_dir, projection_path = roles.role_paths(project_root)
    submissions_dir, proposals_dir, approvals_dir = roles.evidence_paths(project_root)
    try:
        state, events = roles._load_role_state(project_root)
        change = roles._validate_proposal_shape(proposal)
        grants.validate_issuance_evidence(
            grant_store,
            approval,
            proposal,
            operation_class=ROLE_OPERATION_CLASS,
        )
        pd = mutation.digest(proposal)
        ad = mutation.digest(approval)
        consumed = next(
            (e for e in events if e["proposal_digest"] == pd and e["approval_digest"] == ad),
            None,
        )
        if consumed is None:
            change = roles._validate_proposal_semantics(state, proposal)
            _load_authoritative_operator_state(project_root)
        roles._persist_artifact(submissions_dir, change["submission"])
        roles._persist_artifact(proposals_dir, proposal)
        roles._persist_artifact(approvals_dir, approval)
        return mutation.apply_transition(
            proposal=proposal,
            approval=approval,
            events_dir=events_dir,
            projection_path=projection_path,
            transition=roles._transition,
            initial_state=roles.DEFAULT_ROLE_STATE,
        )
    except Exception as exc:
        if not hasattr(exc, "code"):
            raise
        normalized = _normalize_contract_error(exc)
        return mutation.operation_result("FAIL", normalized.code, normalized.detail)


def apply_operator_change_with_authority(
    project_root: Path,
    grant_store: Path,
    proposal: dict[str, Any],
    approval: dict[str, Any],
) -> dict[str, Any]:
    if not _is_grant_approval(approval):
        return operators.apply_operator_change(project_root, proposal, approval)

    events_dir, projection_path = operator_paths(project_root)
    try:
        operation = operators._validate_ordinary_proposal(proposal)
        if operation != "DISABLE_OPERATOR":
            raise ContractError("NON_DELEGABLE", f"{operation} is not grant-delegable")
        grants.validate_issuance_evidence(
            grant_store,
            approval,
            proposal,
            operation_class=OPERATOR_DISABLE_OPERATION_CLASS,
        )
        state, events = operators._load_registry(project_root)
        pd = mutation.digest(proposal)
        ad = mutation.digest(approval)
        consumed = next(
            (e for e in events if e["proposal_digest"] == pd and e["approval_digest"] == ad),
            None,
        )
        if consumed is None:
            operators._ordinary_transition(state, operation, proposal["change"])
        return mutation.apply_transition(
            proposal=proposal,
            approval=approval,
            events_dir=events_dir,
            projection_path=projection_path,
            transition=lambda current, change: operators._ordinary_transition(current, operation, change),
            initial_state=EMPTY_OPERATOR_STATE,
        )
    except Exception as exc:
        if not hasattr(exc, "code"):
            raise
        normalized = _normalize_contract_error(exc)
        return mutation.operation_result("FAIL", normalized.code, normalized.detail)
