#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable

PROPOSAL_CONTRACT = "reasoning-distiller-proposal/1"
APPROVAL_CONTRACT = "reasoning-distiller-approval/1"
APPROVAL_V2_CONTRACT = "reasoning-distiller-approval/2"
EVENT_CONTRACT = "reasoning-distiller-mutation-event/1"
PROJECTION_STATUS_CONTRACT = "reasoning-distiller-projection-status/1"
RESULT_CONTRACT = "reasoning-distiller-operation-result/1"
REVALIDATION_CONTRACT = "reasoning-distiller-proposal-revalidation/1"

EMPTY_STATE: dict[str, Any] = {}


class ContractError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def canonical_json_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ContractError("NON_CANONICAL_VALUE", str(exc)) from exc
    return (text + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def operation_result(status: str, outcome: str, detail: str | None = None, **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"contract": RESULT_CONTRACT, "status": status, "outcome": outcome}
    if detail:
        result["detail"] = detail
    result.update(extra)
    return result


def make_proposal(domain: str, operation: str, current_state: Any, change: Any) -> dict[str, Any]:
    if not domain or not operation:
        raise ContractError("INVALID_PROPOSAL", "domain and operation are required")
    return {"contract": PROPOSAL_CONTRACT, "domain": domain, "operation": operation, "basis_digest": digest(current_state), "change": change}


def make_approval(proposal: dict[str, Any], operator_id: str, authentication: dict[str, Any]) -> dict[str, Any]:
    """Create legacy approval/1 evidence; retained for R1-R15 compatibility."""
    validate_proposal(proposal)
    _validate_direct_operator(operator_id, authentication)
    return {"contract": APPROVAL_CONTRACT, "proposal_digest": digest(proposal), "operator_id": operator_id, "authentication": authentication}


def make_direct_approval_v2(proposal: dict[str, Any], operator_id: str, authentication: dict[str, Any]) -> dict[str, Any]:
    validate_proposal(proposal)
    _validate_direct_operator(operator_id, authentication)
    return {
        "contract": APPROVAL_V2_CONTRACT,
        "proposal_digest": digest(proposal),
        "authority_basis": {"kind": "direct-operator", "operator_id": operator_id, "authentication": authentication},
    }


def make_grant_approval_v2(proposal: dict[str, Any], grant: str, grant_event: str) -> dict[str, Any]:
    validate_proposal(proposal)
    if not isinstance(grant, str) or not grant.startswith("authority-grant:"):
        raise ContractError("INVALID_AUTHORITY_BASIS", "grant must use authority-grant: namespace")
    if not isinstance(grant_event, str) or not grant_event.startswith("authority-grant-event:"):
        raise ContractError("INVALID_AUTHORITY_BASIS", "grant_event must use authority-grant-event: namespace")
    return {
        "contract": APPROVAL_V2_CONTRACT,
        "proposal_digest": digest(proposal),
        "authority_basis": {"kind": "authority-grant", "grant": grant, "grant_event": grant_event},
    }


def _validate_direct_operator(operator_id: Any, authentication: Any) -> None:
    if not isinstance(operator_id, str) or not operator_id.startswith("operator:"):
        raise ContractError("INVALID_OPERATOR_ID", "operator_id must use operator: namespace")
    if not isinstance(authentication, dict) or not authentication.get("method"):
        raise ContractError("INVALID_AUTHENTICATION", "authentication.method is required")


def validate_proposal(proposal: dict[str, Any]) -> None:
    required = {"contract", "domain", "operation", "basis_digest", "change"}
    if not isinstance(proposal, dict) or set(proposal) != required:
        raise ContractError("INVALID_PROPOSAL", "proposal fields do not match contract")
    if proposal["contract"] != PROPOSAL_CONTRACT or not proposal["domain"] or not proposal["operation"]:
        raise ContractError("INVALID_PROPOSAL", "unsupported proposal contract/domain/operation")
    if not _valid_digest(proposal["basis_digest"]):
        raise ContractError("INVALID_PROPOSAL", "basis_digest is invalid")
    canonical_json_bytes(proposal)


def validate_approval(approval: dict[str, Any], proposal: dict[str, Any]) -> None:
    validate_proposal(proposal)
    if not isinstance(approval, dict):
        raise ContractError("INVALID_APPROVAL", "approval must be an object")
    contract = approval.get("contract")
    if contract == APPROVAL_CONTRACT:
        if set(approval) != {"contract", "proposal_digest", "operator_id", "authentication"}:
            raise ContractError("INVALID_APPROVAL", "approval/1 fields do not match contract")
        _validate_direct_operator(approval["operator_id"], approval["authentication"])
    elif contract == APPROVAL_V2_CONTRACT:
        if set(approval) != {"contract", "proposal_digest", "authority_basis"}:
            raise ContractError("INVALID_APPROVAL", "approval/2 fields do not match contract")
        basis = approval["authority_basis"]
        if not isinstance(basis, dict):
            raise ContractError("INVALID_AUTHORITY_BASIS", "authority_basis must be an object")
        if basis.get("kind") == "direct-operator":
            if set(basis) != {"kind", "operator_id", "authentication"}:
                raise ContractError("INVALID_AUTHORITY_BASIS", "direct authority basis fields do not match contract")
            _validate_direct_operator(basis["operator_id"], basis["authentication"])
        elif basis.get("kind") == "authority-grant":
            if set(basis) != {"kind", "grant", "grant_event"}:
                raise ContractError("INVALID_AUTHORITY_BASIS", "grant authority basis fields do not match contract")
            if not isinstance(basis["grant"], str) or not basis["grant"].startswith("authority-grant:"):
                raise ContractError("INVALID_AUTHORITY_BASIS", "invalid grant reference")
            if not isinstance(basis["grant_event"], str) or not basis["grant_event"].startswith("authority-grant-event:"):
                raise ContractError("INVALID_AUTHORITY_BASIS", "invalid grant event reference")
        else:
            raise ContractError("INVALID_AUTHORITY_BASIS", "unknown authority basis kind")
    else:
        raise ContractError("INVALID_APPROVAL", "unsupported approval contract")
    if approval["proposal_digest"] != digest(proposal):
        raise ContractError("APPROVAL_MISMATCH", "approval is not bound to this proposal")
    canonical_json_bytes(approval)


def revalidate_proposal(proposal: dict[str, Any], current_state: Any, *, blocked_reasons: list[str] | None = None) -> dict[str, Any]:
    """Deterministic, read-only D3 applicability check against authoritative current state."""
    try:
        validate_proposal(proposal)
    except ContractError as exc:
        return {"contract": REVALIDATION_CONTRACT, "proposal_digest": digest(proposal) if isinstance(proposal, dict) else None, "classification": "INVALID", "reasons": [exc.code]}
    if blocked_reasons:
        return {"contract": REVALIDATION_CONTRACT, "proposal_digest": digest(proposal), "classification": "BLOCKED", "basis_digest": digest(current_state), "reasons": sorted(set(blocked_reasons))}
    current_digest = digest(current_state)
    if proposal["basis_digest"] != current_digest:
        return {"contract": REVALIDATION_CONTRACT, "proposal_digest": digest(proposal), "classification": "STALE", "basis_digest": current_digest, "reasons": ["STALE_BASIS"]}
    return {"contract": REVALIDATION_CONTRACT, "proposal_digest": digest(proposal), "classification": "APPLICABLE", "basis_digest": current_digest, "reasons": []}


def _valid_digest(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    tail = value[7:]
    return len(tail) == 64 and all(c in "0123456789abcdef" for c in tail)


def _event_path(events_dir: Path, sequence: int) -> Path:
    return events_dir / f"{sequence:08d}.json"


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
    if temp.exists(): temp.unlink()
    with open(temp, "xb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    os.replace(temp, path)


def load_json(path: Path) -> Any:
    with open(path, "rb") as handle: raw = handle.read()
    try: value = json.loads(raw.decode("utf-8"))
    except Exception as exc: raise ContractError("INVALID_JSON", f"invalid JSON at {path}") from exc
    if raw != canonical_json_bytes(value): raise ContractError("NON_CANONICAL_ARTIFACT", f"artifact is not canonical JSON: {path}")
    return value


def replay(events_dir: Path, initial_state: Any | None = None) -> tuple[Any, list[dict[str, Any]]]:
    state: Any = EMPTY_STATE if initial_state is None else initial_state
    consumed: set[tuple[str, str]] = set(); events: list[dict[str, Any]] = []
    if not events_dir.exists(): return state, events
    if not events_dir.is_dir() or events_dir.is_symlink(): raise ContractError("EVENT_STORE_CONFLICT", "event store is not a normal directory")
    paths = sorted(p for p in events_dir.iterdir() if p.name.endswith(".json"))
    for expected, path in enumerate(paths, start=1):
        if path.name != f"{expected:08d}.json": raise ContractError("EVENT_SEQUENCE_CONFLICT", "event sequence is not contiguous")
        event = load_json(path)
        required = {"contract", "sequence", "domain", "operation", "proposal_digest", "approval_digest", "basis_digest", "result_digest", "result_state"}
        if not isinstance(event, dict) or set(event) != required: raise ContractError("INVALID_EVENT", f"invalid event fields: {path.name}")
        if event["contract"] != EVENT_CONTRACT or event["sequence"] != expected: raise ContractError("INVALID_EVENT", f"invalid event contract/sequence: {path.name}")
        if event["basis_digest"] != digest(state) or event["result_digest"] != digest(event["result_state"]): raise ContractError("EVENT_CHAIN_CONFLICT", f"digest mismatch at {path.name}")
        key = (event["proposal_digest"], event["approval_digest"])
        if key in consumed: raise ContractError("APPROVAL_REUSE", f"approval/proposal pair reused at {path.name}")
        consumed.add(key); state = event["result_state"]; events.append(event)
    return state, events


def projection_status(events_dir: Path, projection_path: Path, initial_state: Any | None = None) -> dict[str, Any]:
    try: state, events = replay(events_dir, initial_state)
    except ContractError as exc: return {"contract": PROJECTION_STATUS_CONTRACT, "status": "CONFLICT", "reason_code": exc.code, "detail": exc.detail}
    replay_digest = digest(state)
    if not projection_path.exists(): return {"contract": PROJECTION_STATUS_CONTRACT, "status": "REBUILDABLE", "replay_digest": replay_digest, "event_count": len(events)}
    if not projection_path.is_file() or projection_path.is_symlink(): return {"contract": PROJECTION_STATUS_CONTRACT, "status": "CONFLICT", "reason_code": "PROJECTION_PATH_CONFLICT"}
    try: projection = load_json(projection_path)
    except ContractError as exc: return {"contract": PROJECTION_STATUS_CONTRACT, "status": "CONFLICT", "reason_code": exc.code, "detail": exc.detail}
    if digest(projection) != replay_digest: return {"contract": PROJECTION_STATUS_CONTRACT, "status": "CONFLICT", "reason_code": "PROJECTION_MISMATCH", "replay_digest": replay_digest, "projection_digest": digest(projection)}
    return {"contract": PROJECTION_STATUS_CONTRACT, "status": "VALID", "replay_digest": replay_digest, "event_count": len(events)}


def rebuild_projection(events_dir: Path, projection_path: Path, initial_state: Any | None = None) -> dict[str, Any]:
    status = projection_status(events_dir, projection_path, initial_state)
    if status["status"] == "CONFLICT": return operation_result("FAIL", "PROJECTION_CONFLICT", status.get("detail"), projection_status=status)
    if status["status"] == "VALID": return operation_result("PASS", "NO_CHANGE", projection_digest=status["replay_digest"])
    state, _ = replay(events_dir, initial_state); _write_replace(projection_path, canonical_json_bytes(state))
    return operation_result("PASS", "REBUILT", projection_digest=digest(state))


def apply_transition(*, proposal: dict[str, Any], approval: dict[str, Any], events_dir: Path, projection_path: Path, transition: Callable[[Any, Any], Any], initial_state: Any | None = None) -> dict[str, Any]:
    try:
        validate_proposal(proposal); validate_approval(approval, proposal)
        status = projection_status(events_dir, projection_path, initial_state)
        if status["status"] == "CONFLICT": return operation_result("FAIL", "PROJECTION_CONFLICT", status.get("detail"), projection_status=status)
        current, events = replay(events_dir, initial_state); proposal_digest = digest(proposal); approval_digest = digest(approval)
        consumed_event = next((e for e in events if e["proposal_digest"] == proposal_digest and e["approval_digest"] == approval_digest), None)
        if consumed_event is not None:
            if digest(current) == consumed_event["result_digest"]:
                if status["status"] == "REBUILDABLE": _write_replace(projection_path, canonical_json_bytes(current))
                return operation_result("PASS", "NO_CHANGE", event_sequence=consumed_event["sequence"])
            return operation_result("FAIL", "APPROVAL_ALREADY_CONSUMED")
        rv = revalidate_proposal(proposal, current)
        if rv["classification"] != "APPLICABLE": return operation_result("FAIL", "STALE_BASIS" if rv["classification"] == "STALE" else rv["classification"], revalidation=rv)
        result_state = transition(current, proposal["change"]); canonical_json_bytes(result_state)
        if digest(result_state) == digest(current):
            if status["status"] == "REBUILDABLE": _write_replace(projection_path, canonical_json_bytes(current))
            return operation_result("PASS", "NO_CHANGE")
        sequence = len(events) + 1
        event = {"contract": EVENT_CONTRACT, "sequence": sequence, "domain": proposal["domain"], "operation": proposal["operation"], "proposal_digest": proposal_digest, "approval_digest": approval_digest, "basis_digest": digest(current), "result_digest": digest(result_state), "result_state": result_state}
        _write_exclusive(_event_path(events_dir, sequence), canonical_json_bytes(event)); _write_replace(projection_path, canonical_json_bytes(result_state))
        return operation_result("PASS", "APPLIED", event_sequence=sequence, event_digest=digest(event), projection_digest=digest(result_state))
    except ContractError as exc: return operation_result("FAIL", exc.code, exc.detail)
    except FileExistsError: return operation_result("FAIL", "EVENT_APPEND_CONFLICT")
