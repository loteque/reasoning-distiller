#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ril_admission import jcs, sha256_bytes
from ril_mutation import ContractError, projection_status, replay
from ril_operators import CORE_CAPABILITIES, EMPTY_OPERATOR_STATE, REGISTRY_CONTRACT, operator_paths

ROOT_APPROVAL_CONTRACT = "reasoning-distiller-canonical-recovery-root-approval/1"
PLAN_CONTRACT = "reasoning-distiller-canonical-recovery-plan/1"
RECOVERY_CONFIRMATION = "AUTHORIZE_CANONICAL_PEMS_COVE_RECOVERY"

_APPROVAL_FIELDS = {
    "contract",
    "project_id",
    "generation",
    "recovery_plan_sha256",
    "protected_root_id",
    "authentication",
}
_AUTH_REQUIRED_FIELDS = {"method", "confirmation"}
_AUTH_OPTIONAL_FIELDS = {"evidence"}


def recovery_plan_sha256(plan: dict[str, Any]) -> str:
    if not isinstance(plan, dict) or plan.get("contract") != PLAN_CONTRACT:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "approval target is not a canonical recovery plan")
    project_id = plan.get("project_id")
    generation = plan.get("generation")
    if not isinstance(project_id, str) or not project_id:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "recovery plan project identity is invalid")
    if not isinstance(generation, str) or not generation:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "recovery plan generation is invalid")
    return sha256_bytes(jcs(plan))


def _live_protected_root(project_root: Path) -> str:
    events_dir, projection_path = operator_paths(project_root)
    try:
        status = projection_status(events_dir, projection_path, EMPTY_OPERATOR_STATE)
        if status.get("status") == "CONFLICT":
            raise ContractError(
                "ROOT_RECOVERY_APPROVAL_REQUIRED",
                "operator projection conflicts with authoritative root history",
            )
        state, events = replay(events_dir, EMPTY_OPERATOR_STATE)
    except (ContractError, OSError) as exc:
        if isinstance(exc, ContractError) and exc.code == "ROOT_RECOVERY_APPROVAL_REQUIRED":
            raise
        raise ContractError(
            "ROOT_RECOVERY_APPROVAL_REQUIRED",
            "protected root identity cannot be established from live operator history",
        ) from exc

    if not events or not isinstance(state, dict) or state.get("contract") != REGISTRY_CONTRACT:
        raise ContractError(
            "ROOT_RECOVERY_APPROVAL_REQUIRED",
            "protected root identity is not established",
        )
    root_id = state.get("root_operator_id")
    operators = state.get("operators")
    if not isinstance(root_id, str) or not root_id.startswith("operator:") or not isinstance(operators, dict):
        raise ContractError(
            "ROOT_RECOVERY_APPROVAL_REQUIRED",
            "live operator state does not identify one protected root",
        )
    entry = operators.get(root_id)
    if not isinstance(entry, dict):
        raise ContractError("ROOT_RECOVERY_APPROVAL_REQUIRED", "live protected root entry is missing")
    protected = sorted(
        operator_id
        for operator_id, value in operators.items()
        if isinstance(value, dict) and value.get("protected_root") is True
    )
    if protected != [root_id]:
        raise ContractError(
            "ROOT_RECOVERY_APPROVAL_REQUIRED",
            "live operator state does not establish exactly one protected root",
        )
    capabilities = entry.get("capabilities")
    if (
        entry.get("status") != "active"
        or entry.get("protected_root") is not True
        or not isinstance(capabilities, list)
        or not set(CORE_CAPABILITIES).issubset(set(capabilities))
    ):
        raise ContractError(
            "ROOT_RECOVERY_APPROVAL_REQUIRED",
            "live protected root is not active with the required root capabilities",
        )
    return root_id


def _validate_authentication(authentication: Any) -> None:
    if not isinstance(authentication, dict):
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval authentication must be an object")
    keys = set(authentication)
    if not _AUTH_REQUIRED_FIELDS.issubset(keys) or not keys.issubset(_AUTH_REQUIRED_FIELDS | _AUTH_OPTIONAL_FIELDS):
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval authentication fields are invalid")
    if authentication.get("method") != "human_confirmation":
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval requires human_confirmation")
    if authentication.get("confirmation") != RECOVERY_CONFIRMATION:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval confirmation does not match recovery ceremony")
    if "evidence" in authentication:
        try:
            jcs(authentication["evidence"])
        except Exception as exc:
            raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval evidence is not canonical JSON data") from exc


def validate_recovery_root_approval(
    project_root: Path,
    plan: dict[str, Any],
    approval: dict[str, Any],
) -> dict[str, str]:
    """Validate one exact recovery approval against the current protected root.

    This primitive issues no approval and creates no authority. It validates a
    separately supplied immutable approval artifact and re-establishes root
    identity from the live authoritative operator history on every call.
    """

    plan_sha = recovery_plan_sha256(plan)
    live_root = _live_protected_root(project_root)
    if not isinstance(approval, dict) or set(approval) != _APPROVAL_FIELDS:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval fields do not match contract")
    if approval.get("contract") != ROOT_APPROVAL_CONTRACT:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval contract is invalid")
    if approval.get("project_id") != plan.get("project_id"):
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval project identity mismatch")
    if approval.get("generation") != plan.get("generation"):
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval generation mismatch")
    if approval.get("recovery_plan_sha256") != plan_sha:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval recovery-plan digest mismatch")
    if approval.get("protected_root_id") != live_root:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval is not from the current protected root")
    _validate_authentication(approval.get("authentication"))
    try:
        approval_bytes = jcs(approval)
    except Exception as exc:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval is not canonical JSON data") from exc
    return {
        "protected_root_id": live_root,
        "recovery_plan_sha256": plan_sha,
        "root_approval_sha256": sha256_bytes(approval_bytes),
    }


def parse_and_validate_recovery_root_approval(
    project_root: Path,
    plan: dict[str, Any],
    raw_approval_bytes: bytes,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Strictly parse canonical approval bytes, then validate live root binding."""

    try:
        text = raw_approval_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval is not UTF-8") from exc

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate object key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-JSON numeric constant: {value}")

    try:
        approval = json.loads(text, object_pairs_hook=pairs_hook, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval JSON is invalid") from exc
    if not isinstance(approval, dict):
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval must be an object")
    try:
        canonical = jcs(approval)
    except Exception as exc:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval is not canonical JSON data") from exc
    if canonical != raw_approval_bytes:
        raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "root approval bytes are not canonical")
    evidence = validate_recovery_root_approval(project_root, plan, approval)
    return approval, evidence
