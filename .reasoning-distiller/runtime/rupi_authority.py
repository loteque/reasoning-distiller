#!/usr/bin/env python3
from __future__ import annotations

"""Primitive-only first-use authority orchestration for Rupi.

Rupi does not create authority semantics here. Preparation and confirmation are
separate calls so every protected ceremony returns control to the Human before an
approval primitive can be invoked. Confirmation always re-plans from current state
and binds the exact Human phrase to the exact proposal reference.
"""

from pathlib import Path
from typing import Any

import ril_human_agent as human_agent
import ril_human_confirmation as human_confirmation
import ril_operators
import ril_status
import ril_steward_authorization as steward_authorization
import rupi

FLOW_CONTRACT = "reasoning-distiller-rupi-authority-flow/1"
ROOT_CEREMONY = "ESTABLISH_ROOT_OPERATOR"
STEWARD_CEREMONY = "STEWARD_AUTHORIZATION_CHANGE"


def _observation(action: str, result: dict[str, Any]) -> dict[str, Any]:
    return {"action": action, "result": result}


def _status(project_root: Path, observations: list[dict[str, Any]]) -> dict[str, Any]:
    result = ril_status.classify_status(project_root)
    observations.append(_observation("inspect_status", result))
    return result


def _boundary_code(status: dict[str, Any], fallback: str) -> str:
    blocker = status.get("blocker")
    if isinstance(blocker, dict) and isinstance(blocker.get("code"), str):
        return blocker["code"]
    return fallback


def _finish(
    *,
    requested_goal: str,
    status: dict[str, Any],
    observations: list[dict[str, Any]],
    outcome: str,
    flow_status: str,
    boundary: str | None = None,
    not_completed: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    checkpoint = rupi.build_checkpoint(
        requested_goal=requested_goal,
        status_result=status,
        primitive_results=observations,
        boundary=boundary,
        not_completed=not_completed,
    )
    result: dict[str, Any] = {
        "contract": FLOW_CONTRACT,
        "status": flow_status,
        "outcome": outcome,
        "checkpoint": checkpoint,
        "control_return": rupi.control_return_from_checkpoint(checkpoint),
    }
    result.update(extra)
    return result


def prepare_initial_root(
    project_root: Path,
    *,
    operator_id: str | None,
    requested_goal: str = "initialize Reasoning Distiller project authority",
) -> dict[str, Any]:
    """Prepare and disclose the protected initial-root proposal without mutation."""
    project_root = project_root.resolve()
    observations: list[dict[str, Any]] = []
    status = _status(project_root, observations)
    if status.get("next_action") != "ESTABLISH_INITIAL_OPERATOR":
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INITIAL_ROOT_NOT_REQUIRED",
            flow_status="PASS",
        )
    if not isinstance(operator_id, str) or not operator_id:
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="OPERATOR_ID_REQUIRED",
            flow_status="STOPPED",
            boundary="OPERATOR_ID_REQUIRED",
            not_completed=["plan_initial_operator", "approve_initial_operator", "apply_initial_operator"],
        )

    plan = ril_operators.plan_initial_operator(project_root, operator_id)
    observations.append(_observation("plan_initial_operator", plan))
    if plan.get("status") != "PASS":
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INITIAL_ROOT_PLANNING_FAILED",
            flow_status="STOPPED",
            boundary=str(plan.get("outcome", "INITIAL_ROOT_PLANNING_FAILED")),
            not_completed=["approve_initial_operator", "apply_initial_operator"],
        )

    presentation = human_agent.present_proposal(
        plan["proposal"],
        material_effect=f"Establish {operator_id} as the one protected root operator with the exact core Reasoning Distiller capabilities.",
        authority_implications=[
            "Creates the protected root operator for this project.",
            "The root receives rd:operator_management, rd:role_registry, and rd:steward_authorization.",
            "This does not authorize a Steward scope, create activation, reconcile a candidate, admit knowledge, or mutate Canon.",
        ],
        application_prospectively_disclosed=True,
    )
    ceremony = human_agent.protected_ceremony_boundary(ROOT_CEREMONY)
    return _finish(
        requested_goal=requested_goal,
        status=status,
        observations=observations,
        outcome="INITIAL_ROOT_CONFIRMATION_REQUIRED",
        flow_status="STOPPED",
        boundary=ceremony["outcome"],
        not_completed=["approve_initial_operator", "apply_initial_operator"],
        proposal_reference=presentation["proposal_reference"],
        proposal_presentation=presentation,
        ceremony_boundary=ceremony,
        required_confirmation=ROOT_CEREMONY,
    )


def confirm_initial_root(
    project_root: Path,
    *,
    operator_id: str,
    proposal_reference: str,
    confirmation: str,
    requested_goal: str = "initialize Reasoning Distiller project authority",
) -> dict[str, Any]:
    """Re-plan, bind exact protected confirmation, approve, and apply initial root."""
    project_root = project_root.resolve()
    observations: list[dict[str, Any]] = []
    status = _status(project_root, observations)
    if status.get("next_action") != "ESTABLISH_INITIAL_OPERATOR":
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INITIAL_ROOT_NOT_REQUIRED",
            flow_status="PASS",
        )

    plan = ril_operators.plan_initial_operator(project_root, operator_id)
    observations.append(_observation("plan_initial_operator", plan))
    if plan.get("status") != "PASS":
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INITIAL_ROOT_PLANNING_FAILED",
            flow_status="STOPPED",
            boundary=str(plan.get("outcome", "INITIAL_ROOT_PLANNING_FAILED")),
            not_completed=["approve_initial_operator", "apply_initial_operator"],
        )

    presentation = human_agent.present_proposal(
        plan["proposal"],
        material_effect=f"Establish {operator_id} as the one protected root operator with the exact core Reasoning Distiller capabilities.",
        authority_implications=[
            "Creates the protected root operator for this project.",
            "The root receives rd:operator_management, rd:role_registry, and rd:steward_authorization.",
            "This does not authorize a Steward scope, create activation, reconcile a candidate, admit knowledge, or mutate Canon.",
        ],
        application_prospectively_disclosed=True,
    )
    current_reference = presentation["proposal_reference"]
    if proposal_reference != current_reference:
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="PROPOSAL_REFERENCE_MISMATCH",
            flow_status="STOPPED",
            boundary="PROPOSAL_REFERENCE_MISMATCH",
            not_completed=["approve_initial_operator", "apply_initial_operator"],
            proposal_reference=current_reference,
            proposal_presentation=presentation,
        )

    binding = human_confirmation.bind_exact_confirmation(
        confirmation,
        ceremony=ROOT_CEREMONY,
        proposal_reference=current_reference,
    )
    observations.append(_observation("bind_protected_confirmation", binding))
    if binding.get("status") != "PASS":
        ceremony = human_agent.protected_ceremony_boundary(ROOT_CEREMONY)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INITIAL_ROOT_CONFIRMATION_REQUIRED",
            flow_status="STOPPED",
            boundary=ceremony["outcome"],
            not_completed=["approve_initial_operator", "apply_initial_operator"],
            proposal_reference=current_reference,
            proposal_presentation=presentation,
            ceremony_boundary=ceremony,
            required_confirmation=ROOT_CEREMONY,
        )

    approval = ril_operators.approve_initial_operator(
        plan["proposal"],
        operator_id,
        authentication_evidence={"protected_confirmation": binding},
    )
    apply_result = ril_operators.apply_initial_operator(project_root, plan["proposal"], approval)
    observations.append(_observation("apply_initial_operator", apply_result))
    final_status = _status(project_root, observations)
    if apply_result.get("status") != "PASS":
        return _finish(
            requested_goal=requested_goal,
            status=final_status,
            observations=observations,
            outcome="INITIAL_ROOT_APPLICATION_FAILED",
            flow_status="STOPPED",
            boundary=_boundary_code(final_status, str(apply_result.get("outcome", "INITIAL_ROOT_APPLICATION_FAILED"))),
            not_completed=["apply_initial_operator"],
            proposal_reference=current_reference,
            proposal=plan["proposal"],
            approval=approval,
        )
    return _finish(
        requested_goal=requested_goal,
        status=final_status,
        observations=observations,
        outcome="INITIAL_ROOT_ESTABLISHED",
        flow_status="PASS",
        proposal_reference=current_reference,
        proposal=plan["proposal"],
        approval=approval,
    )


def prepare_steward_authorization(
    project_root: Path,
    *,
    scope: str,
    role_id: str | None,
    requested_goal: str | None = None,
) -> dict[str, Any]:
    """Prepare one exact Steward-scope authorization and stop for ceremony."""
    project_root = project_root.resolve()
    observations: list[dict[str, Any]] = []
    status = _status(project_root, observations)
    goal = requested_goal or f"authorize Steward for {scope}"
    if status.get("dimensions", {}).get("operator") != "VALID":
        return _finish(
            requested_goal=goal,
            status=status,
            observations=observations,
            outcome="ROOT_OPERATOR_REQUIRED",
            flow_status="STOPPED",
            boundary=_boundary_code(status, "ROOT_OPERATOR_REQUIRED"),
            not_completed=["plan_steward_authorization", "approve_steward_authorization", "apply_steward_authorization"],
        )

    plan = steward_authorization.plan_authorization_change(project_root, "AUTHORIZE", scope, role_id)
    observations.append(_observation("plan_steward_authorization", plan))
    if plan.get("status") != "PASS":
        return _finish(
            requested_goal=goal,
            status=status,
            observations=observations,
            outcome="STEWARD_AUTHORIZATION_PLANNING_FAILED",
            flow_status="STOPPED",
            boundary=str(plan.get("outcome", "STEWARD_AUTHORIZATION_PLANNING_FAILED")),
            not_completed=["approve_steward_authorization", "apply_steward_authorization"],
        )

    proposal = plan["proposal"]
    presentation = human_agent.present_proposal(
        proposal,
        material_effect=f"Authorize role {role_id} for the single Steward scope {scope}.",
        authority_implications=[
            f"Changes only the {scope} Steward assignment.",
            "Does not authorize the other Steward scope.",
            "Does not create activation, reconcile a candidate, admit knowledge, or mutate Canon.",
        ],
        application_prospectively_disclosed=True,
    )
    ceremony = human_agent.protected_ceremony_boundary(STEWARD_CEREMONY)
    return _finish(
        requested_goal=goal,
        status=status,
        observations=observations,
        outcome="STEWARD_CONFIRMATION_REQUIRED",
        flow_status="STOPPED",
        boundary=ceremony["outcome"],
        not_completed=["approve_steward_authorization", "apply_steward_authorization"],
        scope=scope,
        role_id=role_id,
        proposal_reference=presentation["proposal_reference"],
        proposal_presentation=presentation,
        ceremony_boundary=ceremony,
        required_confirmation=STEWARD_CEREMONY,
    )


def confirm_steward_authorization(
    project_root: Path,
    *,
    scope: str,
    role_id: str,
    approving_operator_id: str,
    proposal_reference: str,
    confirmation: str,
    requested_goal: str | None = None,
) -> dict[str, Any]:
    """Re-plan and apply exactly one independently confirmed Steward scope."""
    project_root = project_root.resolve()
    observations: list[dict[str, Any]] = []
    status = _status(project_root, observations)
    goal = requested_goal or f"authorize Steward for {scope}"
    if status.get("dimensions", {}).get("operator") != "VALID":
        return _finish(
            requested_goal=goal,
            status=status,
            observations=observations,
            outcome="ROOT_OPERATOR_REQUIRED",
            flow_status="STOPPED",
            boundary=_boundary_code(status, "ROOT_OPERATOR_REQUIRED"),
            not_completed=["approve_steward_authorization", "apply_steward_authorization"],
        )

    plan = steward_authorization.plan_authorization_change(project_root, "AUTHORIZE", scope, role_id)
    observations.append(_observation("plan_steward_authorization", plan))
    if plan.get("status") != "PASS":
        return _finish(
            requested_goal=goal,
            status=status,
            observations=observations,
            outcome="STEWARD_AUTHORIZATION_PLANNING_FAILED",
            flow_status="STOPPED",
            boundary=str(plan.get("outcome", "STEWARD_AUTHORIZATION_PLANNING_FAILED")),
            not_completed=["approve_steward_authorization", "apply_steward_authorization"],
        )

    proposal = plan["proposal"]
    presentation = human_agent.present_proposal(
        proposal,
        material_effect=f"Authorize role {role_id} for the single Steward scope {scope}.",
        authority_implications=[
            f"Changes only the {scope} Steward assignment.",
            "Does not authorize the other Steward scope.",
            "Does not create activation, reconcile a candidate, admit knowledge, or mutate Canon.",
        ],
        application_prospectively_disclosed=True,
    )
    current_reference = presentation["proposal_reference"]
    if proposal_reference != current_reference:
        return _finish(
            requested_goal=goal,
            status=status,
            observations=observations,
            outcome="PROPOSAL_REFERENCE_MISMATCH",
            flow_status="STOPPED",
            boundary="PROPOSAL_REFERENCE_MISMATCH",
            not_completed=["approve_steward_authorization", "apply_steward_authorization"],
            scope=scope,
            role_id=role_id,
            proposal_reference=current_reference,
            proposal_presentation=presentation,
        )

    binding = human_confirmation.bind_exact_confirmation(
        confirmation,
        ceremony=STEWARD_CEREMONY,
        proposal_reference=current_reference,
    )
    observations.append(_observation("bind_protected_confirmation", binding))
    if binding.get("status") != "PASS":
        ceremony = human_agent.protected_ceremony_boundary(STEWARD_CEREMONY)
        return _finish(
            requested_goal=goal,
            status=status,
            observations=observations,
            outcome="STEWARD_CONFIRMATION_REQUIRED",
            flow_status="STOPPED",
            boundary=ceremony["outcome"],
            not_completed=["approve_steward_authorization", "apply_steward_authorization"],
            scope=scope,
            role_id=role_id,
            proposal_reference=current_reference,
            proposal_presentation=presentation,
            ceremony_boundary=ceremony,
            required_confirmation=STEWARD_CEREMONY,
        )

    approval = steward_authorization.approve_authorization_change(
        proposal,
        approving_operator_id,
        authentication_evidence={"protected_confirmation": binding},
    )
    apply_result = steward_authorization.apply_authorization_change(project_root, proposal, approval)
    observations.append(_observation("apply_steward_authorization", apply_result))
    final_status = _status(project_root, observations)
    if apply_result.get("status") != "PASS":
        return _finish(
            requested_goal=goal,
            status=final_status,
            observations=observations,
            outcome="STEWARD_AUTHORIZATION_APPLICATION_FAILED",
            flow_status="STOPPED",
            boundary=_boundary_code(final_status, str(apply_result.get("outcome", "STEWARD_AUTHORIZATION_APPLICATION_FAILED"))),
            not_completed=["apply_steward_authorization"],
            scope=scope,
            role_id=role_id,
            proposal_reference=current_reference,
            proposal=proposal,
            approval=approval,
        )
    return _finish(
        requested_goal=goal,
        status=final_status,
        observations=observations,
        outcome="STEWARD_SCOPE_AUTHORIZED",
        flow_status="PASS",
        scope=scope,
        role_id=role_id,
        proposal_reference=current_reference,
        proposal=proposal,
        approval=approval,
    )
