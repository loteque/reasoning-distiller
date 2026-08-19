#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

_BASE = Path(__file__).resolve().parent

def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _BASE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

_mut = _load("ril_mutation_grant", "ril_mutation.py")
_gov = _load("ril_governance_grant", "ril_governance.py")

ContractError = _mut.ContractError
canonical_json_bytes = _mut.canonical_json_bytes
digest = _mut.digest
load_json = _mut.load_json
make_grant_approval_v2 = _mut.make_grant_approval_v2
revalidate_proposal = _mut.revalidate_proposal

GRANT_CONTRACT = "reasoning-distiller-authority-grant/1"
GRANT_EVENT_CONTRACT = "reasoning-distiller-authority-grant-event/1"
GRANT_PROJECTION_CONTRACT = "reasoning-distiller-authority-grant-projection/1"
CORE_EVENTS = frozenset({"core/approval-issued", "core/revoked", "core/exhausted"})
TERMINAL_WORKFLOW_LIFECYCLES = frozenset({"COMPLETED", "CANCELLED", "SUPERSEDED"})
VALID_SELECTOR_MATCHES = frozenset({"exact", "one-of", "within"})
VALID_PREDICATES = frozenset({"eq", "one-of", "max-count", "subset-of"})


def grant_payload(*, grantor: str, workflow: str, operations: list[str], targets: list[dict[str, Any]], constraints: list[dict[str, Any]] | None = None, approvals_limit: int | None = None) -> dict[str, Any]:
    if not _typed_ref(grantor, "operator"):
        raise ContractError("INVALID_GRANTOR", "grantor must use operator:<id>")
    if not _typed_ref(workflow, "workflow"):
        raise ContractError("INVALID_GRANT_WORKFLOW", "workflow must use workflow:<id>")
    if not isinstance(operations, list) or not operations or len(set(operations)) != len(operations):
        raise ContractError("INVALID_GRANT_SCOPE", "operations must be a non-empty unique explicit list")
    for operation_class in operations:
        if not isinstance(operation_class, str) or not operation_class:
            raise ContractError("INVALID_GRANT_SCOPE", "operation class is invalid")
        if not _gov.delegation_metadata(operation_class).get("delegable"):
            raise ContractError("NON_DELEGABLE", f"{operation_class} is not grant-delegable")
    if not isinstance(targets, list):
        raise ContractError("INVALID_GRANT_SCOPE", "targets must be a list")
    for selector in targets:
        _validate_selector(selector)
    constraints = constraints or []
    for constraint in constraints:
        _validate_constraint(constraint)
    if approvals_limit is not None and (not isinstance(approvals_limit, int) or isinstance(approvals_limit, bool) or approvals_limit < 1):
        raise ContractError("INVALID_GRANT_LIMIT", "approvals_limit must be a positive integer")
    value = {
        "grantor": grantor,
        "workflow": workflow,
        "scope": {
            "operations": sorted(operations),
            "targets": sorted(targets, key=canonical_json_bytes),
            "constraints": sorted(constraints, key=canonical_json_bytes),
        },
        "limits": {"approvals": approvals_limit},
    }
    canonical_json_bytes(value)
    return value


def make_grant_auth(payload: dict[str, Any], operator_id: str, *, method: str = "human_confirmation", confirmation: str = "CREATE_AUTHORITY_GRANT") -> dict[str, Any]:
    if operator_id != payload.get("grantor"):
        raise ContractError("INVALID_GRANT_AUTH", "grantor must authenticate exact grant")
    return {"operator_id": operator_id, "method": method, "confirmation": confirmation, "payload_digest": digest(payload)}


def make_grant(payload: dict[str, Any], authentication: dict[str, Any]) -> dict[str, Any]:
    _validate_payload(payload)
    _validate_creation_auth(payload, authentication)
    value = {"contract": GRANT_CONTRACT, "payload": payload, "authentication": authentication}
    canonical_json_bytes(value)
    return value


def validate_grant(grant: dict[str, Any]) -> None:
    if not isinstance(grant, dict) or set(grant) != {"contract", "payload", "authentication"} or grant.get("contract") != GRANT_CONTRACT:
        raise ContractError("INVALID_GRANT", "grant fields do not match contract")
    _validate_payload(grant["payload"])
    _validate_creation_auth(grant["payload"], grant["authentication"])
    canonical_json_bytes(grant)


def grant_reference(grant: dict[str, Any]) -> str:
    validate_grant(grant)
    return "authority-grant:" + digest(grant).split(":", 1)[1]


def create_grant(store: Path, grant: dict[str, Any]) -> str:
    validate_grant(grant)
    ref = grant_reference(grant)
    root = _grant_dir(store, ref)
    definition = root / "definition.json"
    if definition.exists():
        if load_json(definition) != grant:
            raise ContractError("GRANT_IDENTITY_COLLISION", "grant reference collision")
        return ref
    root.mkdir(parents=True, exist_ok=True)
    _write_exclusive(definition, canonical_json_bytes(grant))
    return ref


def load_grant(store: Path, grant_ref: str) -> dict[str, Any]:
    _require_ref(grant_ref, "authority-grant")
    grant = load_json(_grant_dir(store, grant_ref) / "definition.json")
    validate_grant(grant)
    if grant_reference(grant) != grant_ref:
        raise ContractError("GRANT_IDENTITY_MISMATCH", "grant definition does not match reference")
    return grant


def read_events(store: Path, grant_ref: str) -> list[dict[str, Any]]:
    _require_ref(grant_ref, "authority-grant")
    events_dir = _grant_dir(store, grant_ref) / "events"
    if not events_dir.exists():
        return []
    events: list[dict[str, Any]] = []
    prior: str | None = None
    for sequence, path in enumerate(sorted(events_dir.glob("*.json")), 1):
        if path.name != f"{sequence:08d}.json":
            raise ContractError("GRANT_EVENT_SEQUENCE_CONFLICT", "grant event sequence is not contiguous")
        event = load_json(path)
        validate_event(event)
        if event["grant"] != grant_ref or event["sequence"] != sequence or event["expected_normative_head"] != prior:
            raise ContractError("GRANT_EVENT_CHAIN_CONFLICT", "grant event chain is invalid")
        prior = event["reference"]
        events.append(event)
    return events


def validate_event(event: dict[str, Any]) -> None:
    required = {"contract", "reference", "grant", "sequence", "event_type", "expected_normative_head", "payload", "authentication"}
    if not isinstance(event, dict) or set(event) != required or event.get("contract") != GRANT_EVENT_CONTRACT or event.get("event_type") not in CORE_EVENTS:
        raise ContractError("INVALID_GRANT_EVENT", "grant event fields do not match contract")
    body = {k: event[k] for k in required if k != "reference"}
    expected = "authority-grant-event:" + digest(body).split(":", 1)[1]
    if event["reference"] != expected:
        raise ContractError("GRANT_EVENT_IDENTITY_MISMATCH", "grant event reference does not match content")
    canonical_json_bytes(event)


def project_grant(store: Path, grant_ref: str, *, workflow_lifecycle: str = "OPEN") -> dict[str, Any]:
    grant = load_grant(store, grant_ref)
    events = read_events(store, grant_ref)
    issued = [e for e in events if e["event_type"] == "core/approval-issued"]
    revoked = any(e["event_type"] == "core/revoked" for e in events)
    exhausted = any(e["event_type"] == "core/exhausted" for e in events)
    limit = grant["payload"]["limits"]["approvals"]
    if workflow_lifecycle in TERMINAL_WORKFLOW_LIFECYCLES:
        state = "WORKFLOW_TERMINAL"
    elif revoked:
        state = "REVOKED"
    elif exhausted or (limit is not None and len(issued) >= limit):
        state = "EXHAUSTED"
    else:
        state = "ACTIVE"
    return {
        "contract": GRANT_PROJECTION_CONTRACT,
        "grant": grant_ref,
        "workflow": grant["payload"]["workflow"],
        "state": state,
        "normative_head": events[-1]["reference"] if events else None,
        "approvals_issued": len(issued),
        "approvals_remaining": None if limit is None else max(0, limit - len(issued)),
    }


def validate_scope(store: Path, grant_ref: str, proposal: dict[str, Any], *, operation_class: str, authority_fields: dict[str, Any], workflow_ref: str, workflow_lifecycle: str = "OPEN", workflow_contains_proposal: bool) -> dict[str, Any]:
    try:
        grant = load_grant(store, grant_ref)
        _mut.validate_proposal(proposal)
    except ContractError:
        return {"classification": "INVALID", "grant": grant_ref}
    projection = project_grant(store, grant_ref, workflow_lifecycle=workflow_lifecycle)
    if projection["state"] == "REVOKED":
        return {"classification": "GRANT_INACTIVE", "grant": grant_ref}
    if projection["state"] == "EXHAUSTED":
        return {"classification": "GRANT_EXHAUSTED", "grant": grant_ref}
    if projection["state"] == "WORKFLOW_TERMINAL":
        return {"classification": "GRANT_INACTIVE", "grant": grant_ref}
    if grant["payload"]["workflow"] != workflow_ref:
        return {"classification": "WORKFLOW_MISMATCH", "grant": grant_ref}
    metadata = _gov.delegation_metadata(operation_class)
    if not metadata.get("delegable"):
        return {"classification": "NON_DELEGABLE", "grant": grant_ref}
    if operation_class not in grant["payload"]["scope"]["operations"] or not workflow_contains_proposal:
        return {"classification": "OUTSIDE_GRANT", "grant": grant_ref}
    expected_fields = set(metadata.get("target_fields", [])) | set(metadata.get("constraints", {}).keys())
    if set(authority_fields) != expected_fields:
        return {"classification": "OUTSIDE_GRANT", "grant": grant_ref}
    if not _targets_match(grant["payload"]["scope"]["targets"], metadata, authority_fields):
        return {"classification": "OUTSIDE_GRANT", "grant": grant_ref}
    if not _constraints_match(grant["payload"]["scope"]["constraints"], metadata, authority_fields):
        return {"classification": "OUTSIDE_GRANT", "grant": grant_ref}
    return {"classification": "WITHIN_GRANT", "grant": grant_ref}


def issue_approval(store: Path, grant_ref: str, proposal: dict[str, Any], *, operation_class: str, authority_fields: dict[str, Any], workflow_ref: str, workflow_lifecycle: str, workflow_condition: str, workflow_contains_proposal: bool, current_state: Any, expected_normative_head: str | None) -> dict[str, Any]:
    if workflow_condition == "MATERIALITY_PAUSE":
        raise ContractError("MATERIALITY_PAUSE", "grant-derived approval cannot bypass materiality pause")
    d3 = revalidate_proposal(proposal, current_state)
    if d3["classification"] != "APPLICABLE":
        raise ContractError("PROPOSAL_" + d3["classification"], "proposal is not currently applicable")
    scope = validate_scope(store, grant_ref, proposal, operation_class=operation_class, authority_fields=authority_fields, workflow_ref=workflow_ref, workflow_lifecycle=workflow_lifecycle, workflow_contains_proposal=workflow_contains_proposal)
    if scope["classification"] != "WITHIN_GRANT":
        raise ContractError(scope["classification"], "proposal is not eligible for grant-derived approval")
    projection = project_grant(store, grant_ref, workflow_lifecycle=workflow_lifecycle)
    if projection["normative_head"] != expected_normative_head:
        raise ContractError("GRANT_NORMATIVE_HEAD_CONFLICT", "grant normative head changed")

    # The event commits the exact proposal digest, grant and predecessor. The resulting
    # approval is deterministic from that event reference, so no self-referential hash cycle exists.
    event_ref = _append_event(store, grant_ref, "core/approval-issued", {"proposal_digest": digest(proposal)}, expected_normative_head=expected_normative_head, authentication=None)
    approval = make_grant_approval_v2(proposal, grant_ref, event_ref)

    after = project_grant(store, grant_ref, workflow_lifecycle=workflow_lifecycle)
    limit = load_grant(store, grant_ref)["payload"]["limits"]["approvals"]
    exhausted_event = None
    if limit is not None and after["approvals_issued"] >= limit:
        exhausted_event = _append_event(store, grant_ref, "core/exhausted", {"approvals_issued": after["approvals_issued"]}, expected_normative_head=event_ref, authentication=None)
    return {"approval": approval, "grant_event": event_ref, "exhausted_event": exhausted_event}


def revoke_grant(store: Path, grant_ref: str, operator_id: str, authentication: dict[str, Any], *, protected_root: bool = False, expected_normative_head: str | None) -> str:
    grant = load_grant(store, grant_ref)
    projection = project_grant(store, grant_ref)
    if projection["state"] != "ACTIVE":
        raise ContractError("GRANT_INACTIVE", "only active grant may be revoked")
    if projection["normative_head"] != expected_normative_head:
        raise ContractError("GRANT_NORMATIVE_HEAD_CONFLICT", "grant normative head changed")
    if operator_id != grant["payload"]["grantor"] and not protected_root:
        raise ContractError("GRANT_REVOKE_NOT_PERMITTED", "only grantor or protected root may revoke")
    confirmation = "ROOT_REVOKE_AUTHORITY_GRANT" if protected_root and operator_id != grant["payload"]["grantor"] else "REVOKE_AUTHORITY_GRANT"
    if not isinstance(authentication, dict) or authentication.get("operator_id") != operator_id or authentication.get("subject") != grant_ref or authentication.get("confirmation") != confirmation or not authentication.get("method"):
        raise ContractError("INVALID_GRANT_AUTH", "revocation authentication does not bind exact grant act")
    return _append_event(store, grant_ref, "core/revoked", {"operator": operator_id, "protected_root": bool(protected_root)}, expected_normative_head=expected_normative_head, authentication=authentication)


def _append_event(store: Path, grant_ref: str, event_type: str, payload: dict[str, Any], *, expected_normative_head: str | None, authentication: dict[str, Any] | None) -> str:
    events = read_events(store, grant_ref)
    current = events[-1]["reference"] if events else None
    if current != expected_normative_head:
        raise ContractError("GRANT_NORMATIVE_HEAD_CONFLICT", "grant normative head changed")
    body = {
        "contract": GRANT_EVENT_CONTRACT,
        "grant": grant_ref,
        "sequence": len(events) + 1,
        "event_type": event_type,
        "expected_normative_head": current,
        "payload": payload,
        "authentication": authentication,
    }
    ref = "authority-grant-event:" + digest(body).split(":", 1)[1]
    event = {"reference": ref, **body}
    validate_event(event)
    _write_exclusive(_grant_dir(store, grant_ref) / "events" / f"{body['sequence']:08d}.json", canonical_json_bytes(event))
    return ref


def _targets_match(selectors: list[dict[str, Any]], metadata: dict[str, Any], fields: dict[str, Any]) -> bool:
    by_field = {s["field"]: s for s in selectors}
    for field in metadata.get("target_fields", []):
        selector = by_field.get(field)
        if selector is None or selector["match"] not in metadata.get("selectors", {}).get(field, []):
            return False
        actual = fields.get(field)
        if selector["match"] == "exact" and actual != selector.get("value"):
            return False
        if selector["match"] == "one-of" and actual not in selector.get("values", []):
            return False
        if selector["match"] == "within" and selector.get("value") not in fields.get(field + "__parents", []):
            return False
    return True


def _constraints_match(constraints: list[dict[str, Any]], metadata: dict[str, Any], fields: dict[str, Any]) -> bool:
    by_field = {c["field"]: c for c in constraints}
    for field, predicates in metadata.get("constraints", {}).items():
        constraint = by_field.get(field)
        if constraint is None or constraint["predicate"] not in predicates:
            return False
        pred = constraint["predicate"]
        actual = fields.get(field)
        if pred == "eq" and actual != constraint.get("value"):
            return False
        if pred == "one-of" and actual not in constraint.get("values", []):
            return False
        if pred == "max-count" and (not hasattr(actual, "__len__") or len(actual) > constraint.get("value")):
            return False
        if pred == "subset-of" and not set(actual).issubset(set(constraint.get("values", []))):
            return False
    return True


def _validate_selector(value: dict[str, Any]) -> None:
    if not isinstance(value, dict) or value.get("match") not in VALID_SELECTOR_MATCHES or not isinstance(value.get("field"), str):
        raise ContractError("INVALID_GRANT_SCOPE", "invalid target selector")
    if value["match"] in {"exact", "within"} and set(value) != {"field", "match", "value"}:
        raise ContractError("INVALID_GRANT_SCOPE", "selector fields do not match")
    if value["match"] == "one-of" and (set(value) != {"field", "match", "values"} or not isinstance(value.get("values"), list) or not value["values"]):
        raise ContractError("INVALID_GRANT_SCOPE", "one-of selector requires finite values")


def _validate_constraint(value: dict[str, Any]) -> None:
    if not isinstance(value, dict) or value.get("predicate") not in VALID_PREDICATES or not isinstance(value.get("field"), str):
        raise ContractError("INVALID_GRANT_SCOPE", "invalid constraint")
    if value["predicate"] in {"eq", "max-count"} and set(value) != {"field", "predicate", "value"}:
        raise ContractError("INVALID_GRANT_SCOPE", "constraint fields do not match")
    if value["predicate"] in {"one-of", "subset-of"} and (set(value) != {"field", "predicate", "values"} or not isinstance(value.get("values"), list)):
        raise ContractError("INVALID_GRANT_SCOPE", "constraint values must be a finite list")


def _validate_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or set(payload) != {"grantor", "workflow", "scope", "limits"}:
        raise ContractError("INVALID_GRANT", "grant payload fields do not match contract")
    scope, limits = payload.get("scope"), payload.get("limits")
    if not isinstance(scope, dict) or set(scope) != {"operations", "targets", "constraints"} or not isinstance(limits, dict) or set(limits) != {"approvals"}:
        raise ContractError("INVALID_GRANT", "grant scope/limits fields do not match contract")
    rebuilt = grant_payload(grantor=payload["grantor"], workflow=payload["workflow"], operations=scope["operations"], targets=scope["targets"], constraints=scope["constraints"], approvals_limit=limits["approvals"])
    if rebuilt != payload:
        raise ContractError("INVALID_GRANT", "grant payload is not canonical")


def _validate_creation_auth(payload: dict[str, Any], auth: dict[str, Any]) -> None:
    if not isinstance(auth, dict) or auth.get("operator_id") != payload["grantor"] or auth.get("payload_digest") != digest(payload) or auth.get("confirmation") != "CREATE_AUTHORITY_GRANT" or not auth.get("method"):
        raise ContractError("INVALID_GRANT_AUTH", "authentication does not bind exact prospective grant")


def _grant_dir(store: Path, grant_ref: str) -> Path:
    _require_ref(grant_ref, "authority-grant")
    return Path(store) / "authority-grants" / grant_ref.split(":", 1)[1]


def _write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
    finally:
        os.close(fd)


def _typed_ref(value: Any, kind: str) -> bool:
    return isinstance(value, str) and value.startswith(kind + ":") and len(value) > len(kind) + 1


def _require_ref(value: Any, kind: str) -> None:
    if not _typed_ref(value, kind):
        raise ContractError("INVALID_TYPED_REFERENCE", f"expected {kind}:<id>")
