#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ril_mutation import (
    APPROVAL_CONTRACT,
    ContractError,
    canonical_json_bytes,
    digest,
    load_json,
    make_approval,
    make_proposal,
    replay,
    validate_approval,
)
from ril_operators import EMPTY_OPERATOR_STATE, operator_paths
from ril_roles import DEFAULT_ROLE_STATE, role_paths
from ril_steward_authorization import EMPTY_AUTH_STATE, authorization_paths

DOMAIN = "exceptional_recovery"
OPERATION = "RECOVER_HISTORY"
RESULT_CONTRACT = "reasoning-distiller-exceptional-recovery-result/1"
RECORD_CONTRACT = "reasoning-distiller-recovery-event/1"


def _spec(root: Path, domain: str) -> tuple[Path, Path, Any]:
    if domain == "operator_registry":
        e, p = operator_paths(root); return e, p, EMPTY_OPERATOR_STATE
    if domain == "role_registry":
        e, p = role_paths(root); return e, p, DEFAULT_ROLE_STATE
    if domain == "steward_authorization":
        e, p = authorization_paths(root); return e, p, EMPTY_AUTH_STATE
    raise ContractError("UNKNOWN_RECOVERY_DOMAIN", domain)


def recovery_dir(root: Path, domain: str) -> Path:
    _spec(root, domain)
    return root / "project-knowledge" / "recovery" / domain / "events"


def _fingerprint(events_dir: Path) -> str:
    h = hashlib.sha256()
    if not events_dir.exists():
        return "sha256:" + h.hexdigest()
    if events_dir.is_symlink() or not events_dir.is_dir():
        raise ContractError("EVENT_STORE_CONFLICT", "event store is not a normal directory")
    for path in sorted(events_dir.iterdir(), key=lambda p: p.name):
        if path.is_symlink() or not path.is_file():
            raise ContractError("EVENT_STORE_CONFLICT", f"unsafe event-store entry: {path.name}")
        raw = path.read_bytes()
        h.update(path.name.encode("utf-8") + b"\0" + raw + b"\0")
    return "sha256:" + h.hexdigest()


def _valid_prefix(events_dir: Path, initial: Any) -> Any:
    state = initial
    if not events_dir.exists() or not events_dir.is_dir() or events_dir.is_symlink():
        return state
    for expected, path in enumerate(sorted(events_dir.iterdir(), key=lambda p: p.name), 1):
        if path.name != f"{expected:08d}.json":
            break
        try:
            event = load_json(path)
            required = {"contract","sequence","domain","operation","proposal_digest","approval_digest","basis_digest","result_digest","result_state"}
            if not isinstance(event, dict) or set(event) != required or event["sequence"] != expected:
                break
            if event["basis_digest"] != digest(state) or event["result_digest"] != digest(event["result_state"]):
                break
            state = event["result_state"]
        except (ContractError, OSError):
            break
    return state


def _root_id(root: Path) -> str:
    events, _ = operator_paths(root)
    state = _valid_prefix(events, EMPTY_OPERATOR_STATE)
    root_id = state.get("root_operator_id") if isinstance(state, dict) else None
    if not isinstance(root_id, str) or not root_id.startswith("operator:"):
        raise ContractError("ROOT_IDENTITY_UNAVAILABLE", "protected root cannot be established from valid operator history prefix")
    entry = state.get("operators", {}).get(root_id, {})
    if not entry.get("protected_root"):
        raise ContractError("ROOT_IDENTITY_UNAVAILABLE", "valid prefix does not establish a protected root")
    return root_id


def plan_recovery(root: Path, target_domain: str, continuation_state: Any, evidence: dict[str, Any]) -> dict[str, Any]:
    events, _, initial = _spec(root, target_domain)
    try:
        replay(events, initial)
        raise ContractError("RECOVERY_NOT_REQUIRED", "ordinary authoritative history is valid")
    except ContractError as exc:
        if exc.code == "RECOVERY_NOT_REQUIRED":
            raise
    if not isinstance(evidence, dict) or not evidence.get("method") or "damage" not in evidence:
        raise ContractError("INVALID_RECOVERY_EVIDENCE", "evidence.method and evidence.damage are required")
    canonical_json_bytes(continuation_state)
    change = {
        "target_domain": target_domain,
        "damaged_history_fingerprint": _fingerprint(events),
        "continuation_state": continuation_state,
        "continuation_digest": digest(continuation_state),
        "evidence": evidence,
    }
    proposal = make_proposal(DOMAIN, OPERATION, {}, change)
    return {"status":"PASS","outcome":"PLANNED","proposal":proposal,"proposal_digest":digest(proposal)}


def approve_recovery(root: Path, proposal: dict[str, Any], authentication_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    root_id = _root_id(root)
    auth: dict[str, Any] = {"method":"human_confirmation","confirmation":"AUTHORIZE_EXCEPTIONAL_RECOVERY"}
    if authentication_evidence:
        auth["evidence"] = authentication_evidence
    return make_approval(proposal, root_id, auth)


def _record_path(root: Path, target_domain: str) -> Path:
    return recovery_dir(root, target_domain) / "00000001.json"


def apply_recovery(root: Path, proposal: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    try:
        change = proposal.get("change", {})
        if proposal.get("domain") != DOMAIN or proposal.get("operation") != OPERATION:
            raise ContractError("INVALID_RECOVERY_PROPOSAL", "wrong recovery proposal domain/operation")
        target = change.get("target_domain")
        events, _, initial = _spec(root, target)
        try:
            replay(events, initial)
            return {"contract":RESULT_CONTRACT,"status":"FAIL","outcome":"RECOVERY_NOT_REQUIRED"}
        except ContractError:
            pass
        validate_approval(approval, proposal)
        root_id = _root_id(root)
        if approval["operator_id"] != root_id:
            raise ContractError("ROOT_APPROVAL_REQUIRED", "exceptional recovery requires protected root approval")
        auth = approval["authentication"]
        if auth.get("method") != "human_confirmation" or auth.get("confirmation") != "AUTHORIZE_EXCEPTIONAL_RECOVERY":
            raise ContractError("ROOT_APPROVAL_REQUIRED", "explicit root human recovery confirmation required")
        if change.get("damaged_history_fingerprint") != _fingerprint(events):
            raise ContractError("DAMAGED_HISTORY_CHANGED", "damaged history differs from approved recovery proposal")
        if change.get("continuation_digest") != digest(change.get("continuation_state")):
            raise ContractError("INVALID_CONTINUATION_STATE", "continuation digest mismatch")
        path = _record_path(root, target)
        record = {
            "contract":RECORD_CONTRACT,
            "sequence":1,
            "target_domain":target,
            "proposal_digest":digest(proposal),
            "approval_digest":digest(approval),
            "previous_recovery_digest":None,
            "damaged_history_fingerprint":change["damaged_history_fingerprint"],
            "continuation_digest":change["continuation_digest"],
            "continuation_state":change["continuation_state"],
        }
        data = canonical_json_bytes(record)
        if path.exists():
            existing = path.read_bytes()
            if existing == data:
                return {"contract":RESULT_CONTRACT,"status":"PASS","outcome":"NO_CHANGE","recovery_digest":digest(record)}
            raise ContractError("RECOVERY_ALREADY_ESTABLISHED", "different recovery already exists for domain")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent.is_symlink() or not path.parent.is_dir():
            raise ContractError("RECOVERY_PATH_CONFLICT", "recovery event parent is unsafe")
        with open(path, "xb") as handle:
            handle.write(data); handle.flush()
        return {"contract":RESULT_CONTRACT,"status":"PASS","outcome":"RECOVERED","recovery_digest":digest(record),"continuation_digest":change["continuation_digest"]}
    except (ContractError, OSError) as exc:
        code = exc.code if isinstance(exc, ContractError) else "RECOVERY_WRITE_FAILED"
        detail = exc.detail if isinstance(exc, ContractError) else str(exc)
        return {"contract":RESULT_CONTRACT,"status":"FAIL","outcome":code,"detail":detail}


def replay_recovered_domain(root: Path, target_domain: str) -> Any:
    events, _, initial = _spec(root, target_domain)
    path = _record_path(root, target_domain)
    if not path.exists():
        return replay(events, initial)[0]
    record = load_json(path)
    required = {"contract","sequence","target_domain","proposal_digest","approval_digest","previous_recovery_digest","damaged_history_fingerprint","continuation_digest","continuation_state"}
    if not isinstance(record, dict) or set(record) != required or record["contract"] != RECORD_CONTRACT or record["sequence"] != 1 or record["target_domain"] != target_domain:
        raise ContractError("INVALID_RECOVERY_RECORD", "recovery record contract is invalid")
    if record["previous_recovery_digest"] is not None:
        raise ContractError("INVALID_RECOVERY_RECORD", "first recovery record must have null predecessor")
    if record["damaged_history_fingerprint"] != _fingerprint(events):
        raise ContractError("DAMAGED_HISTORY_CHANGED", "preserved damaged history changed after recovery")
    if record["continuation_digest"] != digest(record["continuation_state"]):
        raise ContractError("INVALID_RECOVERY_RECORD", "continuation digest mismatch")
    return record["continuation_state"]
