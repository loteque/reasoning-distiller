#!/usr/bin/env python3
from __future__ import annotations

"""Primitive-only lifecycle orchestration for Rupi.

This module composes accepted primitives. It owns no installer, bootstrap,
lifecycle, authority, or intent semantics. The standalone installer surface is
provided by the lifecycle runner because packaging/ is intentionally not part of
the installed managed runtime.
"""

from pathlib import Path
from typing import Any

import rd_bootstrap
import rd_install_recovery
import ril_human_agent as human_agent
import ril_status
import rupi

FLOW_CONTRACT = "reasoning-distiller-rupi-lifecycle-flow/1"

_INSTALLER_CONTRACT = "reasoning-distiller-installer/1"
_RELEASE_VERIFICATION_CONTRACT = "reasoning-distiller-release-verification/1"
_TRANSITION_PLAN_CONTRACT = "reasoning-distiller-install-transition-plan/1"

_INSTALL_ACTION = "install_or_update"
_RECOVERY_ACTION = "recover_install_transaction"
_BOOTSTRAP_ACTION = "bootstrap_project"
_STATUS_ACTION = "inspect_status"

_EXECUTABLE_TRANSITIONS = {"FRESH_INSTALL", "UPDATE", "DOWNGRADE"}
_BLOCKED_TRANSITIONS = {
    "DOWNGRADE_REQUIRES_AUTHORIZATION",
    "IDENTITY_COLLISION",
    "MANAGED_DRIFT",
    "RECOVERY_REQUIRED",
    "INCOMPATIBLE",
}


def _installer_surface(installer: Any) -> Any:
    required_constants = {
        "INSTALLER_CONTRACT": _INSTALLER_CONTRACT,
        "RELEASE_VERIFICATION_CONTRACT": _RELEASE_VERIFICATION_CONTRACT,
        "TRANSITION_PLAN_CONTRACT": _TRANSITION_PLAN_CONTRACT,
    }
    for name, expected in required_constants.items():
        if getattr(installer, name, None) != expected:
            raise ValueError(f"installer surface {name} mismatch")
    for name in ("verify_release_bundle", "plan_installation_transition", "install"):
        if not callable(getattr(installer, name, None)):
            raise ValueError(f"installer surface missing callable {name}")
    return installer


def _recovery_installer_surface(installer: Any) -> Any:
    installer = _installer_surface(installer)
    if not callable(getattr(installer, "recover_interrupted_transaction", None)):
        raise ValueError("installer surface missing callable recover_interrupted_transaction")
    return installer


def _bound_operations(intent_result: dict[str, Any]) -> set[str]:
    if not isinstance(intent_result, dict):
        raise ValueError("bound_intent must be an object")
    if intent_result.get("contract") != human_agent.INTENT_CONTRACT:
        raise ValueError("bound_intent must use the Human-Agent intent contract")
    if intent_result.get("status") != "PASS":
        raise ValueError("bound_intent must be a PASS result")
    operations = intent_result.get("operations")
    if not isinstance(operations, list) or any(not isinstance(item, str) or not item for item in operations):
        raise ValueError("bound_intent operations must be non-empty strings")
    return set(operations)


def _observation(action: str, result: dict[str, Any]) -> dict[str, Any]:
    return {"action": action, "result": result}


def _status_observation(project_root: Path, observations: list[dict[str, Any]]) -> dict[str, Any]:
    status = ril_status.classify_status(project_root)
    observations.append(_observation(_STATUS_ACTION, status))
    return status


def _durable_artifacts(observations: list[dict[str, Any]]) -> list[str]:
    artifacts: set[str] = set()
    for item in observations:
        action = item["action"]
        result = item["result"]
        if action == _INSTALL_ACTION and result.get("status") == "PASS":
            managed_root = result.get("managed_root")
            if isinstance(managed_root, str) and managed_root:
                artifacts.add(managed_root)
        if action == _BOOTSTRAP_ACTION and result.get("status") == "PASS":
            created = result.get("created", [])
            if isinstance(created, list):
                artifacts.update(value for value in created if isinstance(value, str) and value)
    return sorted(artifacts)


def _finish(
    *,
    requested_goal: str,
    status: dict[str, Any],
    observations: list[dict[str, Any]],
    outcome: str,
    flow_status: str,
    boundary: str | None = None,
    not_completed: list[str] | None = None,
) -> dict[str, Any]:
    checkpoint = rupi.build_checkpoint(
        requested_goal=requested_goal,
        status_result=status,
        primitive_results=observations,
        durable_artifacts=_durable_artifacts(observations),
        not_completed=not_completed,
        boundary=boundary,
    )
    return {
        "contract": FLOW_CONTRACT,
        "status": flow_status,
        "outcome": outcome,
        "checkpoint": checkpoint,
        "control_return": rupi.control_return_from_checkpoint(checkpoint),
    }


def run_install_bootstrap_handoff(
    *,
    installer: Any,
    package: Path,
    manifest_path: Path,
    transport_sha256: str,
    target: Path,
    bound_intent: dict[str, Any],
    requested_goal: str = "install and initialize Reasoning Distiller",
    managed_root: str = ".reasoning-distiller",
    project_package: Path | None = None,
    allow_downgrade: bool = False,
    installed_at: str = "1970-01-01T00:00:00Z",
    runner_id: str | None = None,
    source_repository: str | None = None,
    source_locator: str | None = None,
    update_locator: str | None = None,
) -> dict[str, Any]:
    """Run the R4 install -> status -> optional bootstrap -> status chain.

    `bound_intent` must already be produced by the accepted Human-Agent intent
    primitive. Protected authority setup is deliberately outside this R4 surface.
    """
    installer = _installer_surface(installer)
    operations = _bound_operations(bound_intent)
    target = target.resolve()
    observations: list[dict[str, Any]] = []

    verification = installer.verify_release_bundle(package, manifest_path, transport_sha256)
    observations.append(_observation("verify_release_bundle", verification))
    if verification.get("status") != "PASS":
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="RELEASE_VERIFICATION_FAILED",
            flow_status="STOPPED",
            boundary="RELEASE_VERIFICATION_FAILED",
            not_completed=[_INSTALL_ACTION, _BOOTSTRAP_ACTION],
        )

    plan = installer.plan_installation_transition(
        manifest_path,
        target,
        managed_root=managed_root,
        project_package=project_package,
        allow_downgrade=allow_downgrade,
    )
    observations.append(_observation("plan_install_transition", plan))
    if plan.get("status") != "PASS":
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INSTALLATION_PLANNING_FAILED",
            flow_status="STOPPED",
            boundary="INSTALLATION_PLANNING_FAILED",
            not_completed=[_INSTALL_ACTION, _BOOTSTRAP_ACTION],
        )

    transition = plan.get("outcome")
    if transition in _BLOCKED_TRANSITIONS:
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome=str(transition),
            flow_status="STOPPED",
            boundary=f"INSTALL_TRANSITION_{transition}",
            not_completed=[_INSTALL_ACTION, _BOOTSTRAP_ACTION],
        )
    if transition not in (_EXECUTABLE_TRANSITIONS | {"NO_CHANGE"}):
        raise ValueError(f"unsupported installation transition: {transition!r}")

    if _INSTALL_ACTION not in operations:
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INSTALL_INTENT_REQUIRED",
            flow_status="STOPPED",
            boundary="INTENT_REQUIRED",
            not_completed=[_INSTALL_ACTION, _BOOTSTRAP_ACTION],
        )

    if transition != "NO_CHANGE":
        install_result = installer.install(
            package,
            manifest_path,
            transport_sha256,
            target,
            managed_root=managed_root,
            project_package=project_package,
            allow_downgrade=allow_downgrade,
            installed_at=installed_at,
            runner_id=runner_id,
            source_repository=source_repository,
            source_locator=source_locator,
            update_locator=update_locator,
        )
        observations.append(_observation(_INSTALL_ACTION, install_result))
        if install_result.get("status") != "PASS":
            status = _status_observation(target, observations)
            return _finish(
                requested_goal=requested_goal,
                status=status,
                observations=observations,
                outcome="INSTALLATION_FAILED",
                flow_status="STOPPED",
                boundary="INSTALLATION_FAILED",
                not_completed=[_INSTALL_ACTION, _BOOTSTRAP_ACTION],
            )

    status = _status_observation(target, observations)
    if status["next_action"] != "BOOTSTRAP_PROJECT":
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="BOOTSTRAP_NOT_REQUIRED",
            flow_status="PASS",
        )

    if _BOOTSTRAP_ACTION not in operations:
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="BOOTSTRAP_INTENT_REQUIRED",
            flow_status="STOPPED",
            boundary="INTENT_REQUIRED",
            not_completed=[_BOOTSTRAP_ACTION],
        )

    _, bootstrap_result = rd_bootstrap.bootstrap(target)
    observations.append(_observation(_BOOTSTRAP_ACTION, bootstrap_result))
    status = _status_observation(target, observations)
    if bootstrap_result.get("status") != "PASS":
        blocker = status.get("blocker")
        boundary = blocker.get("code") if isinstance(blocker, dict) else "BOOTSTRAP_FAILED"
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="BOOTSTRAP_FAILED",
            flow_status="STOPPED",
            boundary=boundary,
            not_completed=[_BOOTSTRAP_ACTION],
        )

    return _finish(
        requested_goal=requested_goal,
        status=status,
        observations=observations,
        outcome="BOOTSTRAP_COMPLETE",
        flow_status="PASS",
    )


def run_update_recovery_handoff(
    *,
    installer: Any,
    package: Path,
    manifest_path: Path,
    transport_sha256: str,
    target: Path,
    bound_intent: dict[str, Any],
    requested_goal: str = "update Reasoning Distiller",
    managed_root: str = ".reasoning-distiller",
    project_package: Path | None = None,
    allow_downgrade: bool = False,
    installed_at: str = "1970-01-01T00:00:00Z",
    runner_id: str | None = None,
    source_repository: str | None = None,
    source_locator: str | None = None,
    update_locator: str | None = None,
) -> dict[str, Any]:
    """Run the R6 update/recovery chain over accepted installer primitives.

    Recovery is invoked only after the read-only planner reports
    ``RECOVERY_REQUIRED`` and only when bounded intent includes the recovery
    operation. A recovery result is always followed by a fresh transition plan.
    """
    installer = _recovery_installer_surface(installer)
    operations = _bound_operations(bound_intent)
    target = target.resolve()
    observations: list[dict[str, Any]] = []

    verification = installer.verify_release_bundle(package, manifest_path, transport_sha256)
    observations.append(_observation("verify_release_bundle", verification))
    if verification.get("status") != "PASS":
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="RELEASE_VERIFICATION_FAILED",
            flow_status="STOPPED",
            boundary="RELEASE_VERIFICATION_FAILED",
            not_completed=[_INSTALL_ACTION],
        )

    def plan_transition() -> dict[str, Any]:
        result = installer.plan_installation_transition(
            manifest_path,
            target,
            managed_root=managed_root,
            project_package=project_package,
            allow_downgrade=allow_downgrade,
        )
        observations.append(_observation("plan_install_transition", result))
        return result

    plan = plan_transition()
    if plan.get("status") != "PASS":
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INSTALLATION_PLANNING_FAILED",
            flow_status="STOPPED",
            boundary="INSTALLATION_PLANNING_FAILED",
            not_completed=[_INSTALL_ACTION],
        )

    transition = plan.get("outcome")
    if transition == "RECOVERY_REQUIRED":
        if _RECOVERY_ACTION not in operations:
            status = _status_observation(target, observations)
            return _finish(
                requested_goal=requested_goal,
                status=status,
                observations=observations,
                outcome="RECOVERY_INTENT_REQUIRED",
                flow_status="STOPPED",
                boundary="INTENT_REQUIRED",
                not_completed=[_RECOVERY_ACTION, _INSTALL_ACTION],
            )
        try:
            recovery = rd_install_recovery.recover_install_transaction(
                installer.recover_interrupted_transaction,
                target,
                managed_root,
            )
        except Exception as exc:
            recovery = {
                "contract": rd_install_recovery.RECOVERY_RESULT_CONTRACT,
                "status": "FAIL",
                "outcome": "RECOVERY_FAILED",
                "detail": str(exc),
            }
            observations.append(_observation(_RECOVERY_ACTION, recovery))
            status = _status_observation(target, observations)
            return _finish(
                requested_goal=requested_goal,
                status=status,
                observations=observations,
                outcome="RECOVERY_FAILED",
                flow_status="STOPPED",
                boundary="RECOVERY_FAILED",
                not_completed=[_RECOVERY_ACTION, _INSTALL_ACTION],
            )
        observations.append(_observation(_RECOVERY_ACTION, recovery))
        plan = plan_transition()
        if plan.get("status") != "PASS":
            status = _status_observation(target, observations)
            return _finish(
                requested_goal=requested_goal,
                status=status,
                observations=observations,
                outcome="POST_RECOVERY_PLANNING_FAILED",
                flow_status="STOPPED",
                boundary="INSTALLATION_PLANNING_FAILED",
                not_completed=[_INSTALL_ACTION],
            )
        transition = plan.get("outcome")

    if transition in _BLOCKED_TRANSITIONS:
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome=str(transition),
            flow_status="STOPPED",
            boundary=f"INSTALL_TRANSITION_{transition}",
            not_completed=[_INSTALL_ACTION],
        )

    if transition == "FRESH_INSTALL":
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="FRESH_INSTALL_REQUIRES_INSTALL_FLOW",
            flow_status="STOPPED",
            boundary="INSTALL_FLOW_REQUIRED",
            not_completed=[_INSTALL_ACTION],
        )

    if transition == "NO_CHANGE":
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="NO_CHANGE",
            flow_status="PASS",
        )

    if transition not in {"UPDATE", "DOWNGRADE"}:
        raise ValueError(f"unsupported update transition: {transition!r}")

    if _INSTALL_ACTION not in operations:
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INSTALL_INTENT_REQUIRED",
            flow_status="STOPPED",
            boundary="INTENT_REQUIRED",
            not_completed=[_INSTALL_ACTION],
        )

    install_result = installer.install(
        package,
        manifest_path,
        transport_sha256,
        target,
        managed_root=managed_root,
        project_package=project_package,
        allow_downgrade=allow_downgrade,
        installed_at=installed_at,
        runner_id=runner_id,
        source_repository=source_repository,
        source_locator=source_locator,
        update_locator=update_locator,
    )
    observations.append(_observation(_INSTALL_ACTION, install_result))
    if install_result.get("status") != "PASS":
        status = _status_observation(target, observations)
        return _finish(
            requested_goal=requested_goal,
            status=status,
            observations=observations,
            outcome="INSTALLATION_FAILED",
            flow_status="STOPPED",
            boundary="INSTALLATION_FAILED",
            not_completed=[_INSTALL_ACTION],
        )

    status = _status_observation(target, observations)
    return _finish(
        requested_goal=requested_goal,
        status=status,
        observations=observations,
        outcome="UPDATED" if transition == "UPDATE" else "DOWNGRADED",
        flow_status="PASS",
    )
