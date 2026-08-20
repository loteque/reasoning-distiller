#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import ril_authority_grant as grants
import ril_governance as governance
import ril_grant_operations as g4
import ril_mutation as mutation
import ril_operator_management as operators
import ril_roles as roles
import ril_workflow as workflow

RESULT_CONTRACT = "reasoning-distiller-shared-orchestration-result/1"


class OrchestrationError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _result(status: str, outcome: str, **extra: Any) -> dict[str, Any]:
    value = {"contract": RESULT_CONTRACT, "status": status, "outcome": outcome}
    value.update(extra)
    return value


def _normalize_error(exc: Exception) -> OrchestrationError:
    return OrchestrationError(getattr(exc, "code", "CONTRACT_ERROR"), getattr(exc, "detail", str(exc)))


def list_grants(grant_store: Path) -> list[str]:
    root = Path(grant_store) / "authority-grants"
    if not root.exists():
        return []
    if not root.is_dir() or root.is_symlink():
        raise OrchestrationError("GRANT_STORE_CONFLICT", "authority-grants store is not a normal directory")
    refs: list[str] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if not entry.is_dir() or entry.is_symlink():
            raise OrchestrationError("GRANT_STORE_CONFLICT", f"unexpected grant-store entry: {entry.name}")
        ref = f"authority-grant:{entry.name}"
        try:
            grants.load_grant(grant_store, ref)
        except Exception as exc:
            raise _normalize_error(exc) from exc
        refs.append(ref)
    return refs


def default_workflow_scope_validator(
    workflow_definition: dict[str, Any],
    proposal: dict[str, Any],
    operation_class: str,
    authority_fields: dict[str, Any],
) -> bool:
    """Conservative common validator for the currently implemented workflow intent shape.

    The D1 primitive leaves bounded intent extensible. G5 therefore only treats an
    explicit `operations` allowlist as machine-proven scope. If a workflow carries
    authority-relevant target/scope/constraint keys that this validator does not
    understand, it fails closed rather than inferring permission.
    """
    payload = workflow_definition.get("payload", {}) if isinstance(workflow_definition, dict) else {}
    intent = payload.get("intent")
    if not isinstance(intent, dict):
        return False
    operations = intent.get("operations")
    if not isinstance(operations, list) or operation_class not in operations:
        return False
    if any(key in intent for key in ("targets", "scope", "constraints", "selectors")):
        return False
    return True


def _descriptor(project_root: Path, proposal: dict[str, Any]) -> dict[str, Any]:
    try:
        mutation.validate_proposal(proposal)
    except Exception as exc:
        raise _normalize_error(exc) from exc

    domain = proposal["domain"]
    operation = proposal["operation"]

    if domain == roles.DOMAIN and operation == roles.OPERATION:
        try:
            current_state, _ = roles._load_role_state(project_root)
            authority_fields = g4.role_authority_fields(proposal)
        except Exception as exc:
            raise _normalize_error(exc) from exc
        return {
            "operation_class": g4.ROLE_OPERATION_CLASS,
            "current_state": current_state,
            "authority_fields": authority_fields,
            "issue": g4.issue_role_grant_approval,
            "apply": g4.apply_role_submission_with_authority,
        }

    if domain == "operator_registry":
        try:
            current_state, _ = operators._load_registry(project_root)
        except Exception as exc:
            raise _normalize_error(exc) from exc
        if operation == "DISABLE_OPERATOR":
            try:
                authority_fields = g4.operator_disable_authority_fields(proposal)
            except Exception as exc:
                raise _normalize_error(exc) from exc
            return {
                "operation_class": g4.OPERATOR_DISABLE_OPERATION_CLASS,
                "current_state": current_state,
                "authority_fields": authority_fields,
                "issue": g4.issue_operator_disable_grant_approval,
                "apply": g4.apply_operator_change_with_authority,
            }
        operation_classes = {
            "ADD_OPERATOR": "operator-registry.add",
            "UPDATE_CAPABILITIES": "operator-registry.update-capabilities",
            "REENABLE_OPERATOR": "operator-registry.reenable",
            "TRANSFER_ROOT": "operator-registry.transfer-root",
            "INITIALIZE_ROOT": "operator-registry.initialize-root",
        }
        return {
            "operation_class": operation_classes.get(operation, f"operator-registry.{operation.lower()}"),
            "current_state": current_state,
            "authority_fields": {},
            "issue": None,
            "apply": None,
        }

    raise OrchestrationError("UNSUPPORTED_SHARED_OPERATION", f"no shared G5 descriptor for {domain}/{operation}")


def _mutation_event_reference(apply_result: dict[str, Any]) -> str | None:
    digest_value = apply_result.get("event_digest") if isinstance(apply_result, dict) else None
    if not isinstance(digest_value, str) or not digest_value.startswith("sha256:"):
        return None
    return "mutation-event:" + digest_value.split(":", 1)[1]


def advance_auto_proposal(
    project_root: Path,
    workflow_store: Path,
    grant_store: Path,
    workflow_ref: str,
    proposal: dict[str, Any],
    *,
    workflow_scope_validator: Callable[[dict[str, Any], dict[str, Any], str, dict[str, Any]], bool] = default_workflow_scope_validator,
    workflow_condition_resolver: Callable[[dict[str, Any], dict[str, Any]], str] | None = None,
    result_scope_validator: Callable[[dict[str, Any], str], bool] | None = None,
    grant_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Adapter-neutral G5 auto-advance path for one exact immutable proposal.

    This function owns check ordering. Adapters supply inputs and presentation only.
    It never manufactures direct human approval.
    """
    try:
        descriptor = _descriptor(project_root, proposal)
        operation_class = descriptor["operation_class"]
        current_state = descriptor["current_state"]

        d3 = mutation.revalidate_proposal(proposal, current_state)
        if d3["classification"] != "APPLICABLE":
            return _result("STOPPED", f"PROPOSAL_{d3['classification']}", revalidation=d3)

        metadata = governance.delegation_metadata(operation_class)
        if not metadata.get("delegable") or descriptor["issue"] is None:
            return _result(
                "STOPPED",
                "AWAITING_APPROVAL",
                operation_class=operation_class,
                reason="NON_DELEGABLE",
                revalidation=d3,
            )

        definition = workflow.load_workflow(workflow_store, workflow_ref)
        projection = workflow.project_workflow(
            workflow_store,
            workflow_ref,
            condition_resolver=workflow_condition_resolver,
        )
        observed_normative_head = projection["normative_head"]
        in_scope = bool(workflow_scope_validator(definition, proposal, operation_class, descriptor["authority_fields"]))

        candidates: list[tuple[str, dict[str, Any]]] = []
        for grant_ref in sorted(set(grant_refs if grant_refs is not None else list_grants(grant_store))):
            check = grants.validate_scope(
                grant_store,
                grant_ref,
                proposal,
                operation_class=operation_class,
                authority_fields=descriptor["authority_fields"],
                workflow_ref=workflow_ref,
                workflow_lifecycle=projection["lifecycle"],
                workflow_contains_proposal=in_scope,
            )
            if check["classification"] == "WITHIN_GRANT":
                candidates.append((grant_ref, check))

        # Scope is a workflow boundary, not absence of approval authority. Discovery
        # still ran first so adapters cannot use scope failure to bypass grant rules.
        if not in_scope:
            return _result("STOPPED", "WORKFLOW_SCOPE_BOUNDARY", operation_class=operation_class, revalidation=d3)

        if not candidates:
            return _result(
                "STOPPED",
                "AWAITING_APPROVAL",
                operation_class=operation_class,
                reason="NO_APPLICABLE_GRANT",
                revalidation=d3,
            )

        if len(candidates) > 1:
            return _result(
                "STOPPED",
                "GRANT_AUTHORITY_AMBIGUITY",
                operation_class=operation_class,
                grants=[ref for ref, _ in candidates],
                revalidation=d3,
            )

        if definition["payload"]["execution_mode"] != "auto-advance":
            return _result("STOPPED", "CONTINUATION_REQUIRED", operation_class=operation_class)

        # Re-read derived workflow state immediately before consuming authority.
        # A competing normative transition cannot be silently rebased into this
        # attempt, and a newly surfaced materiality/machine-state boundary wins.
        current_projection = workflow.project_workflow(
            workflow_store,
            workflow_ref,
            condition_resolver=workflow_condition_resolver,
        )
        if current_projection["lifecycle"] != "OPEN":
            return _result("STOPPED", "WORKFLOW_TERMINAL", lifecycle=current_projection["lifecycle"])
        if current_projection["condition"] == "MATERIALITY_PAUSE":
            return _result(
                "STOPPED",
                "MATERIALITY_PAUSE",
                materiality_pause=current_projection["materiality_pause"],
            )
        if current_projection["normative_head"] != observed_normative_head:
            return _result(
                "STOPPED",
                "WORKFLOW_NORMATIVE_HEAD_CONFLICT",
                operation_class=operation_class,
                expected_normative_head=observed_normative_head,
                actual_normative_head=current_projection["normative_head"],
            )
        if current_projection["condition"] not in {"READY", "AWAITING_APPROVAL"}:
            return _result("STOPPED", current_projection["condition"], operation_class=operation_class)
        projection = current_projection

        grant_ref = candidates[0][0]
        grant_projection = grants.project_grant(grant_store, grant_ref, workflow_lifecycle=projection["lifecycle"])
        issue = descriptor["issue"](
            project_root,
            grant_store,
            grant_ref,
            proposal,
            workflow_ref=workflow_ref,
            workflow_lifecycle=projection["lifecycle"],
            workflow_condition=projection["condition"],
            workflow_contains_proposal=True,
            expected_grant_head=grant_projection["normative_head"],
        )
        approval = issue["approval"]

        applied = descriptor["apply"](project_root, grant_store, proposal, approval)
        if applied.get("status") != "PASS":
            try:
                workflow.record_attempt_failure(
                    workflow_store,
                    workflow_ref,
                    applied.get("outcome", "APPLY_FAILED"),
                    expected_normative_head=projection["normative_head"],
                )
            except Exception as exc:
                raise _normalize_error(exc) from exc
            return _result(
                "STOPPED",
                "APPLY_FAILED",
                operation_class=operation_class,
                grant=grant_ref,
                approval=approval,
                apply_result=applied,
            )

        result_ref = _mutation_event_reference(applied)
        bound_event = None
        if result_ref is not None:
            validator = result_scope_validator or (lambda intent, ref: True)
            try:
                bound_event = workflow.bind_operation_result(
                    workflow_store,
                    workflow_ref,
                    result_ref,
                    expected_normative_head=projection["normative_head"],
                    in_scope=validator,
                )
            except Exception as exc:
                raise _normalize_error(exc) from exc

        after = workflow.project_workflow(
            workflow_store,
            workflow_ref,
            condition_resolver=workflow_condition_resolver,
        )
        return _result(
            "PASS",
            "ADVANCED",
            operation_class=operation_class,
            grant=grant_ref,
            grant_event=issue["grant_event"],
            approval=approval,
            apply_result=applied,
            result_reference=result_ref,
            workflow_event=bound_event,
            workflow_condition=after["condition"],
            workflow_normative_head=after["normative_head"],
        )
    except OrchestrationError as exc:
        return _result("FAIL", exc.code, detail=exc.detail)
    except Exception as exc:
        if hasattr(exc, "code"):
            normalized = _normalize_error(exc)
            return _result("FAIL", normalized.code, detail=normalized.detail)
        raise
