#!/usr/bin/env python3
from __future__ import annotations

"""Read-only Rupi lifecycle checkpoint/presentation adapter.

Rupi owns no lifecycle truth, mutation semantics, or authority. This module turns
accepted primitive results into deterministic Human-facing checkpoint structure.
It never invokes a mutation primitive.
"""

from copy import deepcopy
from typing import Any

import ril_human_agent as human_agent
import rupi_primitive_map as primitive_map

ADAPTER_CONTRACT = "reasoning-distiller-rupi-adapter/1"
CHECKPOINT_CONTRACT = "reasoning-distiller-rupi-checkpoint/1"
STATUS_CONTRACT = "reasoning-distiller-status/1"

_READINESS_DIMENSIONS = (
    ("installation", "VALID", "FRAMEWORK_INSTALLED"),
    ("project_bootstrap", "VALID", "PROJECT_BOOTSTRAPPED"),
    ("operator", "VALID", "AUTHORITY_INITIALIZED"),
    ("reconciliation_authority", "AVAILABLE", "RECONCILIATION_READY"),
    ("admission_authority", "AVAILABLE", "ADMISSION_READY"),
)


def _require_nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_string_list(value: list[str] | None, name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{name} must be a list of non-empty strings")
    return list(value)


def _validate_status(status_result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(status_result, dict):
        raise ValueError("status_result must be an object")
    if status_result.get("contract") != STATUS_CONTRACT:
        raise ValueError("status_result must use reasoning-distiller-status/1")
    if status_result.get("status") != "PASS":
        raise ValueError("status_result must be a PASS result")
    dimensions = status_result.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("status_result dimensions are required")
    next_action = status_result.get("next_action")
    if not isinstance(next_action, str) or not next_action:
        raise ValueError("status_result next_action is required")
    blocker = status_result.get("blocker")
    if blocker is not None and not isinstance(blocker, dict):
        raise ValueError("status_result blocker must be an object or null")
    lifecycle = status_result.get("lifecycle")
    if not isinstance(lifecycle, str) or not lifecycle:
        raise ValueError("status_result lifecycle is required")
    return status_result


def _readiness_labels(status_result: dict[str, Any]) -> list[str]:
    dimensions = status_result["dimensions"]
    return [
        label
        for dimension, expected, label in _READINESS_DIMENSIONS
        if dimensions.get(dimension) == expected
    ]


def _primitive_observation(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"action", "result"}:
        raise ValueError("primitive_results entries require exactly action and result")
    action = _require_nonempty_string(value["action"], "primitive action")
    if action not in primitive_map.PRIMITIVE_MAP:
        raise ValueError(f"unknown Rupi primitive action: {action}")
    result = value["result"]
    if not isinstance(result, dict):
        raise ValueError("primitive result must be an object")
    status = result.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError("primitive result status is required")

    mapped = primitive_map.PRIMITIVE_MAP[action]
    observation: dict[str, Any] = {
        "action": action,
        "primitive": mapped["primitive"],
        "kind": mapped["kind"],
        "result_status": status,
    }
    if isinstance(result.get("contract"), str):
        observation["result_contract"] = result["contract"]
    elif isinstance(result.get("installer_contract"), str):
        observation["result_contract"] = result["installer_contract"]
    if isinstance(result.get("outcome"), str):
        observation["outcome"] = result["outcome"]
    if isinstance(result.get("reason_code"), str):
        observation["reason_code"] = result["reason_code"]
    return observation


def _validate_capability_steps(value: list[dict[str, str]] | None) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("capability_required must be a list")
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"capability", "action"}:
            raise ValueError("capability_required entries require capability and action")
        result.append({
            "capability": _require_nonempty_string(item["capability"], "capability"),
            "action": _require_nonempty_string(item["action"], "capability action"),
        })
    return result


def build_checkpoint(
    *,
    requested_goal: str,
    status_result: dict[str, Any],
    primitive_results: list[dict[str, Any]],
    capability_required: list[dict[str, str]] | None = None,
    optional_later: list[str] | None = None,
    durable_artifacts: list[str] | None = None,
    not_completed: list[str] | None = None,
    boundary: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic, non-authoritative checkpoint from primitive facts.

    Completion is derived exclusively from primitive results whose exact status is
    PASS. Callers cannot inject arbitrary completed-work claims.
    """
    goal = _require_nonempty_string(requested_goal, "requested_goal")
    status = _validate_status(status_result)
    if not isinstance(primitive_results, list):
        raise ValueError("primitive_results must be a list")

    observations = [_primitive_observation(item) for item in primitive_results]
    completed = [item for item in observations if item["result_status"] == "PASS"]
    failed = [item for item in observations if item["result_status"] != "PASS"]

    required_next = [] if status["next_action"] == "READY" else [status["next_action"]]
    capability_steps = _validate_capability_steps(capability_required)
    optional_steps = _require_string_list(optional_later, "optional_later")
    artifacts = _require_string_list(durable_artifacts, "durable_artifacts")
    incomplete = _require_string_list(not_completed, "not_completed")
    boundary_value = None if boundary is None else _require_nonempty_string(boundary, "boundary")

    checkpoint = {
        "contract": CHECKPOINT_CONTRACT,
        "adapter_contract": ADAPTER_CONTRACT,
        "authoritative": False,
        "requested_goal": goal,
        "completed_operations": completed,
        "failed_operations": failed,
        "status": {
            "contract": status["contract"],
            "lifecycle": status["lifecycle"],
            "dimensions": deepcopy(status["dimensions"]),
            "blocker": deepcopy(status.get("blocker")),
            "next_action": status["next_action"],
        },
        "readiness_labels": _readiness_labels(status),
        "required_next": required_next,
        "capability_required": capability_steps,
        "optional_later": optional_steps,
        "boundary": boundary_value,
        "durable_artifacts": artifacts,
        "not_completed": incomplete,
    }
    return checkpoint


def control_return_from_checkpoint(checkpoint: dict[str, Any]) -> dict[str, Any]:
    """Route final Human control return through the accepted Human↔Agent primitive."""
    if not isinstance(checkpoint, dict) or checkpoint.get("contract") != CHECKPOINT_CONTRACT:
        raise ValueError("checkpoint must use reasoning-distiller-rupi-checkpoint/1")

    completed = [item["action"] for item in checkpoint.get("completed_operations", [])]
    failed = [item["action"] for item in checkpoint.get("failed_operations", [])]
    incomplete = list(checkpoint.get("not_completed", [])) + failed
    next_actions = list(checkpoint.get("required_next", []))
    next_actions.extend(item["action"] for item in checkpoint.get("capability_required", []))
    next_actions.extend(checkpoint.get("optional_later", []))

    boundary = checkpoint.get("boundary")
    if boundary is None:
        blocker = checkpoint.get("status", {}).get("blocker")
        boundary = blocker.get("code") if isinstance(blocker, dict) and isinstance(blocker.get("code"), str) else "NONE"

    return human_agent.control_return(
        requested_work=[checkpoint["requested_goal"]],
        completed_work=completed,
        not_completed_work=incomplete,
        durable_artifacts=list(checkpoint.get("durable_artifacts", [])),
        boundary=boundary,
        next_actions=next_actions,
    )
