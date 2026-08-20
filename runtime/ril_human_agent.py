#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import ril_authority_grant as grants
import ril_mutation as mutation
import ril_shared_orchestration as shared
import ril_workflow as workflows

ADAPTER_CONTRACT = "reasoning-distiller-ril-human-agent-adapter/1"
INTENT_CONTRACT = "reasoning-distiller-ril-human-agent-intent/1"
PRESENTATION_CONTRACT = "reasoning-distiller-ril-human-agent-presentation/1"
CONTROL_RETURN_CONTRACT = "reasoning-distiller-ril-human-agent-control-return/1"

_SINGLE_AFFIRMATIONS = {"yes", "proceed", "do it", "approve"}
_SET_AFFIRMATIONS = {"approve all", "proceed with all", "do all"}


def _result(status: str, outcome: str, **extra: Any) -> dict[str, Any]:
    value = {"contract": ADAPTER_CONTRACT, "status": status, "outcome": outcome}
    value.update(extra)
    return value


def _normalize_utterance(value: str) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().lower().split()).rstrip(".!?")


def proposal_reference(proposal: dict[str, Any]) -> str:
    mutation.validate_proposal(proposal)
    return "proposal:" + mutation.digest(proposal).split(":", 1)[1]


def approval_reference(approval: dict[str, Any], proposal: dict[str, Any]) -> str:
    mutation.validate_approval(approval, proposal)
    return "approval:" + mutation.digest(approval).split(":", 1)[1]


def bind_contextual_intent(
    utterance: str,
    offered_operations: list[str],
    *,
    closed_set: bool = False,
    material_modification: bool = False,
) -> dict[str, Any]:
    """Bind only narrow, immediately contextual conversational affirmations.

    Natural-language interpretation outside this deliberately tiny surface is not
    an authority primitive. A caller that detects a material modification must set
    `material_modification=True`, which converts the turn into a revision request.
    """
    if not isinstance(offered_operations, list) or any(
        not isinstance(op, str) or not op for op in offered_operations
    ):
        return {
            "contract": INTENT_CONTRACT,
            "status": "STOPPED",
            "outcome": "INVALID_CONTEXT",
            "operations": [],
        }
    operations = list(offered_operations)
    normalized = _normalize_utterance(utterance)

    if material_modification:
        return {
            "contract": INTENT_CONTRACT,
            "status": "STOPPED",
            "outcome": "REVISION_REQUEST",
            "operations": operations,
        }
    if not operations:
        return {"contract": INTENT_CONTRACT, "status": "STOPPED", "outcome": "NO_OFFERED_OPERATION", "operations": []}

    if len(operations) == 1 and normalized in _SINGLE_AFFIRMATIONS:
        return {
            "contract": INTENT_CONTRACT,
            "status": "PASS",
            "outcome": "BOUND_INTENT",
            "operations": operations,
        }

    if len(operations) > 1 and closed_set and normalized in _SET_AFFIRMATIONS:
        return {
            "contract": INTENT_CONTRACT,
            "status": "PASS",
            "outcome": "BOUND_INTENT_SET",
            "operations": operations,
        }

    if normalized in (_SINGLE_AFFIRMATIONS | _SET_AFFIRMATIONS):
        return {
            "contract": INTENT_CONTRACT,
            "status": "STOPPED",
            "outcome": "AMBIGUOUS_INTENT",
            "operations": operations,
        }

    return {
        "contract": INTENT_CONTRACT,
        "status": "STOPPED",
        "outcome": "NO_AUTHORITY",
        "operations": operations,
    }


def disclose_bounded_chain(operations: list[str]) -> dict[str, Any]:
    """Return the exact closed chain that must be prospectively disclosed."""
    if not isinstance(operations, list) or not operations or any(not isinstance(op, str) or not op for op in operations):
        raise ValueError("bounded chain requires one or more explicit operations")
    return {
        "contract": PRESENTATION_CONTRACT,
        "kind": "bounded-chain-disclosure",
        "closed_set": True,
        "operations": list(operations),
    }


def present_proposal(
    proposal: dict[str, Any],
    *,
    material_effect: str,
    authority_implications: list[str],
    application_prospectively_disclosed: bool = False,
) -> dict[str, Any]:
    """Produce the minimum layered R16B direct-approval presentation."""
    ref = proposal_reference(proposal)
    if not isinstance(material_effect, str) or not material_effect.strip():
        raise ValueError("material_effect is required")
    if not isinstance(authority_implications, list) or any(not isinstance(item, str) or not item for item in authority_implications):
        raise ValueError("authority_implications must be a list of strings")
    return {
        "contract": PRESENTATION_CONTRACT,
        "kind": "proposal-review",
        "material_effect": material_effect,
        "authority_implications": list(authority_implications),
        "proposal_reference": ref,
        "complete_normative_proposal": proposal,
        "application_prospectively_disclosed": bool(application_prospectively_disclosed),
    }


def direct_approve(
    proposal: dict[str, Any],
    operator_id: str,
    authentication: dict[str, Any],
    current_state_loader: Callable[[], Any],
    *,
    blocked_reasons: list[str] | None = None,
) -> dict[str, Any]:
    """Convert fresh human intent into direct approval only after immediate D3.

    The current-state callback is invoked inside this function so adapters do not
    precompute applicability and later create an approval from stale validation.
    """
    current_state = current_state_loader()
    revalidation = mutation.revalidate_proposal(proposal, current_state, blocked_reasons=blocked_reasons)
    classification = revalidation["classification"]
    if classification != "APPLICABLE":
        try:
            proposal_ref = proposal_reference(proposal)
        except Exception:
            proposal_ref = None
        return _result(
            "STOPPED",
            f"PROPOSAL_{classification}",
            proposal=proposal_ref,
            revalidation=revalidation,
        )

    approval = mutation.make_direct_approval_v2(proposal, operator_id, authentication)
    return _result(
        "PASS",
        "APPROVED",
        proposal=proposal_reference(proposal),
        approval=approval,
        approval_reference=approval_reference(approval, proposal),
        revalidation=revalidation,
    )


def create_durable_workflow(
    workflow_store: Path,
    definition: dict[str, Any],
    *,
    persistence_disclosed: bool,
) -> dict[str, Any]:
    """Create durable intent only when persistence was prospectively disclosed."""
    if not persistence_disclosed:
        return _result("STOPPED", "WORKFLOW_PERSISTENCE_DISCLOSURE_REQUIRED")
    ref = workflows.create_workflow(workflow_store, definition)
    return _result("PASS", "WORKFLOW_CREATED", workflow=ref)


def cancel_durable_workflow(
    workflow_store: Path,
    workflow_ref: str,
    operator_id: str,
    authentication: dict[str, Any],
    *,
    protected_root: bool = False,
) -> str:
    return workflows.cancel_workflow(
        workflow_store,
        workflow_ref,
        operator_id,
        authentication,
        protected_root=protected_root,
    )


def revise_durable_workflow(
    workflow_store: Path,
    predecessor_ref: str,
    successor: dict[str, Any],
    *,
    expected_normative_head: str | None,
) -> str:
    return workflows.revise_workflow(
        workflow_store,
        predecessor_ref,
        successor,
        expected_normative_head=expected_normative_head,
    )


def acknowledge_workflow_materiality(
    workflow_store: Path,
    workflow_ref: str,
    pause_ref: str,
    operator_id: str,
    authentication: dict[str, Any],
    *,
    protected_root: bool = False,
) -> str:
    return workflows.acknowledge_materiality(
        workflow_store,
        workflow_ref,
        pause_ref,
        operator_id,
        authentication,
        protected_root=protected_root,
    )


def create_authority_grant(
    project_root: Path,
    grant_store: Path,
    definition: dict[str, Any],
    *,
    workflow_scope_confirmed: bool,
    prospective_delegation_disclosed: bool,
) -> dict[str, Any]:
    """Create bounded prospective authority only from explicit disclosed scope."""
    if not prospective_delegation_disclosed:
        return _result("STOPPED", "GRANT_PROSPECTIVE_DELEGATION_DISCLOSURE_REQUIRED")
    if not workflow_scope_confirmed:
        return _result("STOPPED", "GRANT_WORKFLOW_SCOPE_CONFIRMATION_REQUIRED")
    ref = shared.g4.create_authorized_grant(
        project_root,
        grant_store,
        definition,
        workflow_contains_grant_scope=True,
    )
    return _result("PASS", "AUTHORITY_GRANT_CREATED", grant=ref)


def revoke_authority_grant(
    grant_store: Path,
    grant_ref: str,
    operator_id: str,
    authentication: dict[str, Any],
    *,
    protected_root: bool = False,
    expected_normative_head: str | None,
) -> str:
    return grants.revoke_grant(
        grant_store,
        grant_ref,
        operator_id,
        authentication,
        protected_root=protected_root,
        expected_normative_head=expected_normative_head,
    )


def continue_auto_workflow(
    project_root: Path,
    workflow_store: Path,
    grant_store: Path,
    workflow_ref: str,
    proposal: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """Peer-adapter route to G5; this layer adds no authority semantics."""
    return shared.advance_auto_proposal(
        project_root,
        workflow_store,
        grant_store,
        workflow_ref,
        proposal,
        **kwargs,
    )


def apply_delegable_proposal(
    project_root: Path,
    grant_store: Path,
    proposal: dict[str, Any],
    approval: dict[str, Any],
) -> dict[str, Any]:
    """Apply the delegable operation through the exact shared G4 primitive."""
    descriptor = shared._descriptor(project_root, proposal)
    apply = descriptor.get("apply")
    if apply is None:
        return mutation.operation_result("FAIL", "NON_DELEGABLE")
    return apply(project_root, grant_store, proposal, approval)


def resume_proposal(
    proposal_ref: str,
    loader: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    """Reconstruct proposal continuity from a durable exact reference, not chat."""
    if not isinstance(proposal_ref, str) or not proposal_ref.startswith("proposal:"):
        return _result("STOPPED", "INVALID_PROPOSAL_REFERENCE")
    proposal = loader(proposal_ref)
    try:
        actual = proposal_reference(proposal)
    except Exception as exc:
        return _result("STOPPED", "INVALID_PROPOSAL_ARTIFACT", detail=str(exc))
    if actual != proposal_ref:
        return _result("STOPPED", "DURABLE_REFERENCE_MISMATCH", expected=proposal_ref, actual=actual)
    return _result("PASS", "PROPOSAL_RECONSTRUCTED", proposal_reference=actual, proposal=proposal)


def protected_ceremony_boundary(ceremony: str) -> dict[str, Any]:
    if not isinstance(ceremony, str) or not ceremony:
        raise ValueError("ceremony is required")
    return _result("STOPPED", "PROTECTED_CEREMONY_REQUIRED", ceremony=ceremony)


def approval_authority(approval: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(approval, dict):
        raise ValueError("approval must be an object")
    if approval.get("contract") == mutation.APPROVAL_CONTRACT:
        return {"kind": "direct", "operator": approval.get("operator_id")}
    if approval.get("contract") != mutation.APPROVAL_V2_CONTRACT:
        raise ValueError("unsupported approval contract")
    basis = approval.get("authority_basis", {})
    if basis.get("kind") == "direct-operator":
        return {"kind": "direct", "operator": basis.get("operator_id")}
    if basis.get("kind") == "authority-grant":
        return {"kind": "grant-derived", "grant": basis.get("grant"), "grant_event": basis.get("grant_event")}
    raise ValueError("unsupported approval authority basis")


def control_return(
    *,
    requested_work: list[str],
    completed_work: list[str],
    not_completed_work: list[str],
    durable_artifacts: list[str],
    boundary: str,
    next_actions: list[str],
    approvals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Structured control-return surface that never conflates stage with completion."""
    for name, value in (
        ("requested_work", requested_work),
        ("completed_work", completed_work),
        ("not_completed_work", not_completed_work),
        ("durable_artifacts", durable_artifacts),
        ("next_actions", next_actions),
    ):
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            raise ValueError(f"{name} must be a list of strings")
    if not isinstance(boundary, str) or not boundary:
        raise ValueError("boundary is required")

    authority = [approval_authority(item) for item in (approvals or [])]
    return {
        "contract": CONTROL_RETURN_CONTRACT,
        "requested_work": list(requested_work),
        "completed_work": list(completed_work),
        "not_completed_work": list(not_completed_work),
        "durable_artifacts": list(durable_artifacts),
        "approval_authority": authority,
        "boundary": boundary,
        "next_actions": list(next_actions),
    }
