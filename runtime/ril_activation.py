#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from ril_mutation import ContractError, canonical_json_bytes, digest, operation_result, projection_status, replay
from ril_roles import DEFAULT_ROLE_STATE, role_paths
from ril_steward_authorization import EMPTY_AUTH_STATE, SCOPES, authorization_paths

ACTIVATION_CONTRACT = "reasoning-distiller-role-activation/1"
SUPPORTED_METHODS = {"explicit_declaration"}


def make_explicit_activation(role_id: str, invocation_id: str, source: str) -> dict[str, Any]:
    artifact = {
        "contract": ACTIVATION_CONTRACT,
        "role_id": role_id,
        "method": "explicit_declaration",
        "context": {
            "invocation_id": invocation_id,
            "source": source,
        },
    }
    validate_activation_artifact(artifact)
    return artifact


def validate_activation_artifact(artifact: Any) -> None:
    required = {"contract", "role_id", "method", "context"}
    if not isinstance(artifact, dict) or set(artifact) != required:
        raise ContractError("INVALID_ACTIVATION_EVIDENCE", "activation fields do not match contract")
    if artifact["contract"] != ACTIVATION_CONTRACT:
        raise ContractError("INVALID_ACTIVATION_EVIDENCE", "unsupported activation contract")
    role_id = artifact["role_id"]
    if not isinstance(role_id, str) or not role_id:
        raise ContractError("INVALID_ACTIVATION_EVIDENCE", "role_id must be a non-empty string")
    method = artifact["method"]
    if not isinstance(method, str) or not method:
        raise ContractError("INVALID_ACTIVATION_EVIDENCE", "method must be a non-empty string")
    if method not in SUPPORTED_METHODS:
        raise ContractError("UNSUPPORTED_ACTIVATION_METHOD", method)
    context = artifact["context"]
    if not isinstance(context, dict) or set(context) != {"invocation_id", "source"}:
        raise ContractError("INVALID_ACTIVATION_EVIDENCE", "context must contain exactly invocation_id and source")
    for key in ("invocation_id", "source"):
        if not isinstance(context[key], str) or not context[key].strip():
            raise ContractError("INVALID_ACTIVATION_EVIDENCE", f"context.{key} must be a non-empty string")
    canonical_json_bytes(artifact)


def _load_role_state(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = role_paths(project_root)
    status = projection_status(events_dir, projection_path, DEFAULT_ROLE_STATE)
    if status["status"] == "CONFLICT":
        raise ContractError("ROLE_PROJECTION_CONFLICT", "role projection conflicts with authoritative history")
    state, _ = replay(events_dir, DEFAULT_ROLE_STATE)
    return state


def _load_authorization_state(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = authorization_paths(project_root)
    status = projection_status(events_dir, projection_path, EMPTY_AUTH_STATE)
    if status["status"] == "CONFLICT":
        raise ContractError("AUTHORIZATION_PROJECTION_CONFLICT", "Steward authorization projection conflicts with authoritative history")
    state, _ = replay(events_dir, EMPTY_AUTH_STATE)
    return state


def validate_activation(project_root: Path, scope: str, artifact: dict[str, Any]) -> dict[str, Any]:
    try:
        if scope not in SCOPES:
            raise ContractError("UNKNOWN_SCOPE", scope)
        validate_activation_artifact(artifact)

        role_state = _load_role_state(project_root)
        role_id = artifact["role_id"]
        role_entry = role_state.get("roles", {}).get(role_id)
        if role_entry is None:
            raise ContractError("ROLE_NOT_FOUND", role_id)
        if role_entry.get("status") != "available":
            raise ContractError("ROLE_UNAVAILABLE", role_id)

        auth_state = _load_authorization_state(project_root)
        assigned = auth_state.get("assignments", {}).get(scope)
        if assigned is None:
            raise ContractError("SCOPE_UNASSIGNED", scope)
        if assigned != role_id:
            raise ContractError("ROLE_NOT_AUTHORIZED_FOR_SCOPE", f"{role_id} is not authorized for {scope}")

        return operation_result(
            "PASS",
            "ACTIVATION_ACCEPTED",
            scope=scope,
            role_id=role_id,
            invocation_id=artifact["context"]["invocation_id"],
            activation_digest=digest(artifact),
        )
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)
