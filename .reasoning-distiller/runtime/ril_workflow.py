#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any, Callable

_SPEC = importlib.util.spec_from_file_location("ril_mutation_workflow", Path(__file__).with_name("ril_mutation.py"))
_mut = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_mut)

ContractError = _mut.ContractError
canonical_json_bytes = _mut.canonical_json_bytes
digest = _mut.digest
load_json = _mut.load_json

WORKFLOW_CONTRACT = "reasoning-distiller-workflow/1"
WORKFLOW_EVENT_CONTRACT = "reasoning-distiller-workflow-event/1"
WORKFLOW_HEADS_CONTRACT = "reasoning-distiller-workflow-heads/1"
WORKFLOW_PROJECTION_CONTRACT = "reasoning-distiller-workflow-projection/1"

CORE_EVENTS = frozenset({
    "core/operation-result-bound",
    "core/attempt-failed",
    "core/materiality-paused",
    "core/materiality-acknowledged",
    "core/cancelled",
    "core/superseded",
    "core/completed",
})
TERMINAL_EVENTS = {
    "core/cancelled": "CANCELLED",
    "core/superseded": "SUPERSEDED",
    "core/completed": "COMPLETED",
}
OPEN_CONDITIONS = frozenset({
    "READY", "AWAITING_APPROVAL", "AWAITING_ACTIVATION", "AWAITING_EVIDENCE",
    "UNRESOLVED", "BLOCKED", "MATERIALITY_PAUSE", "EXECUTION_FAILED",
})


def workflow_payload(
    *,
    requester: str,
    intent: dict[str, Any],
    execution_mode: str = "operator-driven",
    continuation_policy: dict[str, Any] | None = None,
    materiality_policy: dict[str, Any] | None = None,
    plan: list[dict[str, Any]] | None = None,
    supersedes: str | None = None,
    resumes: str | None = None,
) -> dict[str, Any]:
    if not _operator_ref(requester):
        raise ContractError("INVALID_WORKFLOW_REQUESTER", "requester must use operator: namespace")
    if execution_mode not in {"operator-driven", "auto-advance"}:
        raise ContractError("INVALID_WORKFLOW_MODE", "unsupported execution mode")
    if not isinstance(intent, dict) or not intent:
        raise ContractError("INVALID_WORKFLOW_INTENT", "bounded intent must be a non-empty object")
    value = {
        "requester": requester,
        "intent": intent,
        "execution_mode": execution_mode,
        "continuation_policy": continuation_policy or {"kind": "requester-only"},
        "materiality_policy": materiality_policy or {"kind": "requester-only"},
        "plan": plan or [],
        "supersedes": supersedes,
        "resumes": resumes,
    }
    _validate_policy(value["continuation_policy"])
    _validate_policy(value["materiality_policy"])
    if supersedes is not None and not _typed_ref(supersedes, "workflow"):
        raise ContractError("INVALID_WORKFLOW_RELATION", "supersedes must be workflow:<id>")
    if resumes is not None and not _typed_ref(resumes, "workflow"):
        raise ContractError("INVALID_WORKFLOW_RELATION", "resumes must be workflow:<id>")
    canonical_json_bytes(value)
    return value


def make_workflow_auth(payload: dict[str, Any], operator_id: str, *, method: str = "human_confirmation", confirmation: str | None = None) -> dict[str, Any]:
    if not _operator_ref(operator_id):
        raise ContractError("INVALID_OPERATOR_ID", "operator_id must use operator: namespace")
    auth = {"operator_id": operator_id, "method": method, "payload_digest": digest(payload)}
    if confirmation is not None:
        auth["confirmation"] = confirmation
    return auth


def make_workflow(payload: dict[str, Any], authentication: dict[str, Any]) -> dict[str, Any]:
    _validate_payload(payload)
    _validate_creation_auth(payload, authentication)
    value = {"contract": WORKFLOW_CONTRACT, "payload": payload, "authentication": authentication}
    canonical_json_bytes(value)
    return value


def workflow_reference(workflow: dict[str, Any]) -> str:
    validate_workflow(workflow)
    return "workflow:" + digest(workflow).split(":", 1)[1]


def validate_workflow(workflow: dict[str, Any]) -> None:
    if not isinstance(workflow, dict) or set(workflow) != {"contract", "payload", "authentication"}:
        raise ContractError("INVALID_WORKFLOW", "workflow fields do not match contract")
    if workflow["contract"] != WORKFLOW_CONTRACT:
        raise ContractError("INVALID_WORKFLOW", "unsupported workflow contract")
    _validate_payload(workflow["payload"])
    _validate_creation_auth(workflow["payload"], workflow["authentication"])
    canonical_json_bytes(workflow)


def create_workflow(store: Path, workflow: dict[str, Any]) -> str:
    validate_workflow(workflow)
    ref = workflow_reference(workflow)
    root = _workflow_dir(store, ref)
    definition = root / "definition.json"
    heads = root / "heads.json"
    if definition.exists():
        existing = load_json(definition)
        if existing != workflow:
            raise ContractError("WORKFLOW_IDENTITY_COLLISION", "workflow reference collision")
        return ref
    root.mkdir(parents=True, exist_ok=True)
    _write_exclusive(definition, canonical_json_bytes(workflow))
    _write_replace(heads, canonical_json_bytes(_empty_heads(ref)))
    return ref


def load_workflow(store: Path, workflow_ref: str) -> dict[str, Any]:
    _require_typed_ref(workflow_ref, "workflow")
    workflow = load_json(_workflow_dir(store, workflow_ref) / "definition.json")
    validate_workflow(workflow)
    if workflow_reference(workflow) != workflow_ref:
        raise ContractError("WORKFLOW_IDENTITY_MISMATCH", "definition does not match requested workflow")
    return workflow


def append_extension_event(store: Path, workflow_ref: str, event_type: str, payload: dict[str, Any]) -> str:
    if event_type.startswith("core/") or "/" not in event_type:
        raise ContractError("INVALID_EXTENSION_EVENT", "extension event must be namespaced and non-core")
    return _append_event(store, workflow_ref, event_type, payload, normative=False, expected_normative_head=None, authentication=None)


def append_core_event(
    store: Path,
    workflow_ref: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    expected_normative_head: str | None,
    authentication: dict[str, Any] | None = None,
) -> str:
    if event_type not in CORE_EVENTS:
        raise ContractError("INVALID_CORE_EVENT", "unsupported core event")
    return _append_event(store, workflow_ref, event_type, payload, normative=True, expected_normative_head=expected_normative_head, authentication=authentication)


def bind_operation_result(store: Path, workflow_ref: str, result_ref: str, *, expected_normative_head: str | None, in_scope: Callable[[dict[str, Any], str], bool]) -> str:
    workflow = load_workflow(store, workflow_ref)
    if not _typed_reference(result_ref):
        raise ContractError("INVALID_RESULT_REFERENCE", "result must be a typed durable reference")
    if not in_scope(workflow["payload"]["intent"], result_ref):
        raise ContractError("WORKFLOW_RESULT_OUT_OF_SCOPE", "result does not advance bounded intent")
    return append_core_event(store, workflow_ref, "core/operation-result-bound", {"result": result_ref}, expected_normative_head=expected_normative_head)


def record_attempt_failure(store: Path, workflow_ref: str, reason: str, *, expected_normative_head: str | None) -> str:
    if not reason:
        raise ContractError("INVALID_ATTEMPT_FAILURE", "reason is required")
    return append_core_event(store, workflow_ref, "core/attempt-failed", {"reason": reason}, expected_normative_head=expected_normative_head)


def pause_materiality(store: Path, workflow_ref: str, discovery: dict[str, Any], *, expected_normative_head: str | None) -> str:
    if not isinstance(discovery, dict) or not discovery:
        raise ContractError("INVALID_MATERIALITY", "material discovery is required")
    return append_core_event(store, workflow_ref, "core/materiality-paused", {"discovery": discovery}, expected_normative_head=expected_normative_head)


def acknowledge_materiality(store: Path, workflow_ref: str, pause_ref: str, operator_id: str, authentication: dict[str, Any], *, protected_root: bool = False) -> str:
    projection = project_workflow(store, workflow_ref)
    if projection["lifecycle"] != "OPEN" or projection["condition"] != "MATERIALITY_PAUSE" or projection["materiality_pause"] != pause_ref:
        raise ContractError("MATERIALITY_PAUSE_MISMATCH", "acknowledgement must bind the current exact pause")
    workflow = load_workflow(store, workflow_ref)
    if not _policy_allows(workflow["payload"]["materiality_policy"], workflow["payload"]["requester"], operator_id, protected_root):
        raise ContractError("WORKFLOW_ACK_NOT_PERMITTED", "operator may not acknowledge this workflow")
    _validate_operator_auth(authentication, operator_id, "ACKNOWLEDGE_MATERIALITY", pause_ref)
    return append_core_event(store, workflow_ref, "core/materiality-acknowledged", {"pause": pause_ref, "operator": operator_id}, expected_normative_head=projection["normative_head"], authentication=authentication)


def cancel_workflow(store: Path, workflow_ref: str, operator_id: str, authentication: dict[str, Any], *, protected_root: bool = False) -> str:
    projection = project_workflow(store, workflow_ref)
    if projection["lifecycle"] != "OPEN":
        raise ContractError("WORKFLOW_TERMINAL", "terminal workflow cannot be cancelled")
    workflow = load_workflow(store, workflow_ref)
    if operator_id != workflow["payload"]["requester"] and not protected_root:
        raise ContractError("WORKFLOW_CANCEL_NOT_PERMITTED", "only requester or protected root may cancel")
    _validate_operator_auth(authentication, operator_id, "CANCEL_WORKFLOW", workflow_ref)
    return append_core_event(store, workflow_ref, "core/cancelled", {"operator": operator_id}, expected_normative_head=projection["normative_head"], authentication=authentication)


def revise_workflow(store: Path, predecessor_ref: str, successor: dict[str, Any], *, expected_normative_head: str | None) -> str:
    predecessor = load_workflow(store, predecessor_ref)
    projection = project_workflow(store, predecessor_ref)
    if projection["lifecycle"] != "OPEN":
        raise ContractError("WORKFLOW_TERMINAL", "only OPEN workflow may be revised")
    if projection["normative_head"] != expected_normative_head:
        raise ContractError("WORKFLOW_NORMATIVE_HEAD_CONFLICT", "predecessor normative head changed")
    validate_workflow(successor)
    if successor["payload"].get("supersedes") != predecessor_ref:
        raise ContractError("WORKFLOW_REVISION_MISMATCH", "successor must explicitly supersede predecessor")
    if successor["payload"]["requester"] != predecessor["payload"]["requester"]:
        raise ContractError("WORKFLOW_REVISION_REQUESTER_MISMATCH", "revision requester must be preserved")
    successor_ref = create_workflow(store, successor)
    try:
        append_core_event(store, predecessor_ref, "core/superseded", {"successor": successor_ref}, expected_normative_head=expected_normative_head)
    except Exception:
        # The successor definition may exist as an immutable orphan artifact, but it is
        # not an authoritative successor until the predecessor's superseded event binds it.
        raise
    return successor_ref


def complete_if(
    store: Path,
    workflow_ref: str,
    authoritative_state: Any,
    completion_validator: Callable[[dict[str, Any], list[str], Any], bool],
) -> str | None:
    projection = project_workflow(store, workflow_ref)
    if projection["lifecycle"] != "OPEN":
        return None
    workflow = load_workflow(store, workflow_ref)
    results = projection["bound_results"]
    if not completion_validator(workflow["payload"]["intent"], results, authoritative_state):
        return None
    return append_core_event(store, workflow_ref, "core/completed", {"results": results}, expected_normative_head=projection["normative_head"])


def continuation_permitted(store: Path, workflow_ref: str, operator_id: str, *, protected_root: bool = False) -> bool:
    projection = project_workflow(store, workflow_ref)
    if projection["lifecycle"] != "OPEN" or projection["condition"] == "MATERIALITY_PAUSE":
        return False
    workflow = load_workflow(store, workflow_ref)
    return _policy_allows(workflow["payload"]["continuation_policy"], workflow["payload"]["requester"], operator_id, protected_root)


def project_workflow(store: Path, workflow_ref: str, *, condition_resolver: Callable[[dict[str, Any], dict[str, Any]], str] | None = None) -> dict[str, Any]:
    workflow = load_workflow(store, workflow_ref)
    events = read_events(store, workflow_ref)
    history_head = events[-1]["reference"] if events else None
    normative = [e for e in events if e["event_type"] in CORE_EVENTS]
    normative_head = normative[-1]["reference"] if normative else None
    lifecycle = "OPEN"
    condition = "READY"
    pause_ref = None
    bound_results: list[str] = []
    for event in normative:
        typ = event["event_type"]
        if typ in TERMINAL_EVENTS:
            lifecycle = TERMINAL_EVENTS[typ]
            condition = None
        elif typ == "core/materiality-paused":
            condition = "MATERIALITY_PAUSE"; pause_ref = event["reference"]
        elif typ == "core/materiality-acknowledged":
            condition = "READY"; pause_ref = None
        elif typ == "core/attempt-failed":
            condition = "EXECUTION_FAILED"
        elif typ == "core/operation-result-bound":
            bound_results.append(event["payload"]["result"]); condition = "READY"
    projection = {
        "contract": WORKFLOW_PROJECTION_CONTRACT,
        "workflow": workflow_ref,
        "lifecycle": lifecycle,
        "condition": condition,
        "history_head": history_head,
        "normative_head": normative_head,
        "materiality_pause": pause_ref,
        "bound_results": bound_results,
        "event_count": len(events),
    }
    if lifecycle == "OPEN" and condition not in {"MATERIALITY_PAUSE", "EXECUTION_FAILED"} and condition_resolver is not None:
        resolved = condition_resolver(workflow, projection)
        if resolved not in OPEN_CONDITIONS:
            raise ContractError("INVALID_WORKFLOW_CONDITION", "condition resolver returned unsupported condition")
        projection["condition"] = resolved
    return projection


def read_events(store: Path, workflow_ref: str) -> list[dict[str, Any]]:
    _require_typed_ref(workflow_ref, "workflow")
    events_dir = _workflow_dir(store, workflow_ref) / "events"
    if not events_dir.exists():
        return []
    paths = sorted(events_dir.glob("*.json"))
    events: list[dict[str, Any]] = []
    prior: str | None = None
    normative_head: str | None = None
    for expected, path in enumerate(paths, 1):
        if path.name != f"{expected:08d}.json":
            raise ContractError("WORKFLOW_EVENT_SEQUENCE_CONFLICT", "event sequence is not contiguous")
        event = load_json(path)
        validate_event(event)
        if event["workflow"] != workflow_ref or event["sequence"] != expected or event["previous_history"] != prior:
            raise ContractError("WORKFLOW_EVENT_CHAIN_CONFLICT", "workflow event chain is invalid")
        if event["event_type"] in CORE_EVENTS:
            if event["expected_normative_head"] != normative_head:
                raise ContractError("WORKFLOW_NORMATIVE_CHAIN_CONFLICT", "core event normative predecessor is invalid")
            normative_head = event["reference"]
        prior = event["reference"]
        events.append(event)
    return events


def validate_event(event: dict[str, Any]) -> None:
    required = {"contract", "reference", "workflow", "sequence", "event_type", "previous_history", "expected_normative_head", "payload", "authentication"}
    if not isinstance(event, dict) or set(event) != required or event.get("contract") != WORKFLOW_EVENT_CONTRACT:
        raise ContractError("INVALID_WORKFLOW_EVENT", "workflow event fields do not match contract")
    if not _typed_ref(event["workflow"], "workflow") or not isinstance(event["sequence"], int) or event["sequence"] < 1:
        raise ContractError("INVALID_WORKFLOW_EVENT", "workflow event identity fields are invalid")
    if event["event_type"] not in CORE_EVENTS and (event["event_type"].startswith("core/") or "/" not in event["event_type"]):
        raise ContractError("INVALID_WORKFLOW_EVENT", "unknown core or unnamespaced event")
    body = {k: event[k] for k in required if k != "reference"}
    expected = "workflow-event:" + digest(body).split(":", 1)[1]
    if event["reference"] != expected:
        raise ContractError("WORKFLOW_EVENT_IDENTITY_MISMATCH", "event reference does not match content")
    canonical_json_bytes(event)


def _append_event(store: Path, workflow_ref: str, event_type: str, payload: dict[str, Any], *, normative: bool, expected_normative_head: str | None, authentication: dict[str, Any] | None) -> str:
    load_workflow(store, workflow_ref)
    events = read_events(store, workflow_ref)
    current_normative = next((e["reference"] for e in reversed(events) if e["event_type"] in CORE_EVENTS), None)
    if normative and expected_normative_head != current_normative:
        raise ContractError("WORKFLOW_NORMATIVE_HEAD_CONFLICT", "normative predecessor changed")
    terminal = next((e for e in reversed(events) if e["event_type"] in TERMINAL_EVENTS), None)
    if terminal is not None:
        raise ContractError("WORKFLOW_TERMINAL", "terminal workflow cannot append semantic events")
    sequence = len(events) + 1
    body = {
        "contract": WORKFLOW_EVENT_CONTRACT,
        "workflow": workflow_ref,
        "sequence": sequence,
        "event_type": event_type,
        "previous_history": events[-1]["reference"] if events else None,
        "expected_normative_head": current_normative if normative else None,
        "payload": payload,
        "authentication": authentication,
    }
    ref = "workflow-event:" + digest(body).split(":", 1)[1]
    event = {"reference": ref, **body}
    validate_event(event)
    _write_exclusive(_workflow_dir(store, workflow_ref) / "events" / f"{sequence:08d}.json", canonical_json_bytes(event))
    heads = {"contract": WORKFLOW_HEADS_CONTRACT, "workflow": workflow_ref, "history_head": ref, "normative_head": ref if normative else current_normative}
    _write_replace(_workflow_dir(store, workflow_ref) / "heads.json", canonical_json_bytes(heads))
    return ref


def _empty_heads(workflow_ref: str) -> dict[str, Any]:
    return {"contract": WORKFLOW_HEADS_CONTRACT, "workflow": workflow_ref, "history_head": None, "normative_head": None}


def _validate_payload(payload: dict[str, Any]) -> None:
    required = {"requester", "intent", "execution_mode", "continuation_policy", "materiality_policy", "plan", "supersedes", "resumes"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ContractError("INVALID_WORKFLOW", "workflow payload fields do not match contract")
    workflow_payload(**payload)


def _validate_creation_auth(payload: dict[str, Any], auth: dict[str, Any]) -> None:
    if not isinstance(auth, dict) or auth.get("operator_id") != payload["requester"] or auth.get("payload_digest") != digest(payload) or not auth.get("method"):
        raise ContractError("INVALID_WORKFLOW_AUTH", "authentication does not bind requester to exact payload")
    if payload["execution_mode"] == "auto-advance" and auth.get("confirmation") != "AUTO_ADVANCE":
        raise ContractError("AUTO_ADVANCE_CONFIRMATION_REQUIRED", "auto-advance requires prospective confirmation")


def _validate_operator_auth(auth: dict[str, Any], operator_id: str, confirmation: str, subject: str) -> None:
    if not isinstance(auth, dict) or auth.get("operator_id") != operator_id or not auth.get("method") or auth.get("confirmation") != confirmation or auth.get("subject") != subject:
        raise ContractError("INVALID_WORKFLOW_AUTH", "operator authentication does not bind exact workflow act")


def _validate_policy(policy: dict[str, Any]) -> None:
    if not isinstance(policy, dict) or policy.get("kind") not in {"requester-only", "any-enabled-operator", "operator-set"}:
        raise ContractError("INVALID_WORKFLOW_POLICY", "unsupported workflow policy")
    if policy["kind"] == "operator-set":
        operators = policy.get("operators")
        if not isinstance(operators, list) or not operators or any(not _operator_ref(v) for v in operators):
            raise ContractError("INVALID_WORKFLOW_POLICY", "operator-set requires explicit operators")


def _policy_allows(policy: dict[str, Any], requester: str, operator_id: str, protected_root: bool) -> bool:
    if protected_root:
        return True
    kind = policy["kind"]
    if kind == "requester-only":
        return operator_id == requester
    if kind == "any-enabled-operator":
        return _operator_ref(operator_id)
    return operator_id in policy.get("operators", [])


def _workflow_dir(store: Path, workflow_ref: str) -> Path:
    _require_typed_ref(workflow_ref, "workflow")
    return Path(store) / "workflows" / workflow_ref.split(":", 1)[1]


def _write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
    finally:
        os.close(fd)


def _write_replace(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    if temp.exists():
        temp.unlink()
    with open(temp, "xb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    os.replace(temp, path)


def _operator_ref(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("operator:") and len(value) > len("operator:")


def _typed_ref(value: Any, kind: str) -> bool:
    return isinstance(value, str) and value.startswith(kind + ":") and len(value) > len(kind) + 1


def _typed_reference(value: Any) -> bool:
    return isinstance(value, str) and ":" in value and bool(value.split(":", 1)[0]) and bool(value.split(":", 1)[1])


def _require_typed_ref(value: Any, kind: str) -> None:
    if not _typed_ref(value, kind):
        raise ContractError("INVALID_TYPED_REFERENCE", f"expected {kind}:<id>")
