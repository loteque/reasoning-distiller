#!/usr/bin/env python3
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from ril_mutation import (
    ContractError,
    apply_transition,
    canonical_json_bytes,
    digest,
    make_approval,
    make_proposal,
    operation_result,
    projection_status,
    rebuild_projection,
    replay,
    validate_approval,
    validate_proposal,
)
from ril_operators import EMPTY_OPERATOR_STATE, operator_paths

REGISTRY_CONTRACT = "reasoning-distiller-role-registry/1"
SUBMISSION_CONTRACT = "reasoning-distiller-role-submission/1"
DOMAIN = "role_registry"
OPERATION = "APPLY_ROLE_SUBMISSION"
CONFIRMATION = "ROLE_REGISTRY_CHANGE"
DEFAULT_STEWARD_ID = "steward:default"
ROLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]*$")
FORBIDDEN_ROLE_IDS = {
    "architect",
    "project-architect",
    "rgp-engineer",
    "reasoning-graph-protocol-engineer",
}
FORBIDDEN_TITLES = {
    "architect",
    "project architect",
    "rgp engineer",
    "reasoning graph protocol engineer",
}

DEFAULT_ROLE_STATE: dict[str, Any] = {
    "contract": REGISTRY_CONTRACT,
    "roles": {
        DEFAULT_STEWARD_ID: {
            "definition": {
                "role_id": DEFAULT_STEWARD_ID,
                "title": "Default Steward",
                "description": "Package-provided generic Steward role.",
                "capabilities": [],
            },
            "status": "available",
            "origin": "package",
            "protected": True,
            "sources": ["reasoning-distiller-package"],
        }
    },
}


def role_paths(project_root: Path) -> tuple[Path, Path]:
    base = project_root / "project-knowledge" / "roles"
    return base / "events", base / "current.json"


def evidence_paths(project_root: Path) -> tuple[Path, Path, Path]:
    base = project_root / "project-knowledge" / "roles"
    return base / "submissions", base / "proposals", base / "approvals"


def _load_role_state(project_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    events_dir, projection_path = role_paths(project_root)
    status = projection_status(events_dir, projection_path, DEFAULT_ROLE_STATE)
    if status["status"] == "CONFLICT":
        raise ContractError("PROJECTION_CONFLICT", "role projection conflicts with authoritative history")
    state, events = replay(events_dir, DEFAULT_ROLE_STATE)
    return state, events


def _load_operator_state(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = operator_paths(project_root)
    status = projection_status(events_dir, projection_path, EMPTY_OPERATOR_STATE)
    if status["status"] == "CONFLICT":
        raise ContractError("OPERATOR_PROJECTION_CONFLICT", "operator projection conflicts with authoritative history")
    state, _ = replay(events_dir, EMPTY_OPERATOR_STATE)
    if state == EMPTY_OPERATOR_STATE:
        raise ContractError("INITIAL_OPERATOR_REQUIRED", "initial operator must be established first")
    return state


def _validate_role_approver(operator_state: dict[str, Any], operator_id: str) -> None:
    entry = operator_state.get("operators", {}).get(operator_id)
    if not entry or entry.get("status") != "active" or "rd:role_registry" not in entry.get("capabilities", []):
        raise ContractError("APPROVER_NOT_AUTHORIZED", "approver must be active and hold rd:role_registry")


def _normalize_definition(role: Any) -> dict[str, Any]:
    required = {"role_id", "title", "description", "capabilities"}
    if not isinstance(role, dict) or set(role) != required:
        raise ContractError("INVALID_ROLE", "role fields do not match contract")
    role_id = role["role_id"]
    title = role["title"]
    description = role["description"]
    capabilities = role["capabilities"]
    if not isinstance(role_id, str) or not ROLE_ID_RE.fullmatch(role_id):
        raise ContractError("INVALID_ROLE_ID", "role_id must be a lowercase stable project identifier")
    if role_id == DEFAULT_STEWARD_ID:
        raise ContractError("PACKAGE_ROLE_PROTECTED", "package-provided roles are excluded from submissions")
    if role_id in FORBIDDEN_ROLE_IDS:
        raise ContractError("FORBIDDEN_PROTOCOL_ROLE", role_id)
    if not isinstance(title, str) or not title.strip():
        raise ContractError("INVALID_ROLE", "title must be a non-empty string")
    if title.strip().lower() in FORBIDDEN_TITLES:
        raise ContractError("FORBIDDEN_PROTOCOL_ROLE", title)
    if not isinstance(description, str):
        raise ContractError("INVALID_ROLE", "description must be a string")
    if not isinstance(capabilities, list):
        raise ContractError("INVALID_ROLE", "capabilities must be a list")
    caps: set[str] = set()
    for capability in capabilities:
        if not isinstance(capability, str) or not capability:
            raise ContractError("INVALID_ROLE", "capabilities must be non-empty strings")
        if capability.startswith("rd:"):
            raise ContractError("FORBIDDEN_PACKAGE_CAPABILITY", capability)
        caps.add(capability)
    return {
        "role_id": role_id,
        "title": title.strip(),
        "description": description,
        "capabilities": sorted(caps),
    }


def normalize_submission(submission: Any) -> dict[str, Any]:
    required = {"contract", "mode", "source", "scope", "roles"}
    if not isinstance(submission, dict) or set(submission) != required:
        raise ContractError("INVALID_ROLE_SUBMISSION", "submission fields do not match contract")
    if submission["contract"] != SUBMISSION_CONTRACT:
        raise ContractError("INVALID_ROLE_SUBMISSION", "unsupported submission contract")
    mode = submission["mode"]
    source = submission["source"]
    if mode not in {"incremental", "snapshot"}:
        raise ContractError("INVALID_ROLE_SUBMISSION", "mode must be incremental or snapshot")
    if not isinstance(source, str) or not source.strip():
        raise ContractError("INVALID_ROLE_SUBMISSION", "source must be a non-empty string")
    if not isinstance(submission["roles"], list):
        raise ContractError("INVALID_ROLE_SUBMISSION", "roles must be a list")
    roles = [_normalize_definition(role) for role in submission["roles"]]
    ids = [role["role_id"] for role in roles]
    if len(ids) != len(set(ids)):
        raise ContractError("DUPLICATE_ROLE_ID", "submission contains duplicate role_id")
    roles.sort(key=lambda role: role["role_id"])

    scope: Any = submission["scope"]
    if mode == "incremental":
        if scope is not None:
            raise ContractError("INVALID_ROLE_SUBMISSION", "incremental scope must be null")
        normalized_scope = None
    else:
        if not isinstance(scope, dict) or set(scope) != {"role_ids"} or not isinstance(scope["role_ids"], list):
            raise ContractError("INVALID_SNAPSHOT_SCOPE", "snapshot scope must contain role_ids list")
        role_ids: list[str] = []
        for role_id in scope["role_ids"]:
            if not isinstance(role_id, str) or not ROLE_ID_RE.fullmatch(role_id):
                raise ContractError("INVALID_SNAPSHOT_SCOPE", "scope role_ids must be valid role IDs")
            if role_id == DEFAULT_STEWARD_ID:
                raise ContractError("PACKAGE_ROLE_PROTECTED", "package-provided roles are excluded from snapshot scope")
            role_ids.append(role_id)
        role_ids = sorted(set(role_ids))
        if not set(ids).issubset(set(role_ids)):
            raise ContractError("INVALID_SNAPSHOT_SCOPE", "all submitted snapshot roles must be included in scope")
        normalized_scope = {"role_ids": role_ids}

    normalized = {
        "contract": SUBMISSION_CONTRACT,
        "mode": mode,
        "source": source.strip(),
        "scope": normalized_scope,
        "roles": roles,
    }
    canonical_json_bytes(normalized)
    return normalized


def _entry_for(definition: dict[str, Any], source: str, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    sources = set(previous.get("sources", []) if previous else [])
    sources.add(source)
    return {
        "definition": definition,
        "status": "available",
        "origin": "project",
        "protected": False,
        "sources": sorted(sources),
    }


def _classify_changes(state: dict[str, Any], submission: dict[str, Any]) -> list[dict[str, Any]]:
    roles = state["roles"]
    source = submission["source"]
    submitted = {role["role_id"]: role for role in submission["roles"]}
    changes: list[dict[str, Any]] = []

    for role_id in sorted(submitted):
        definition = submitted[role_id]
        current = roles.get(role_id)
        if current is None:
            changes.append({"action": "ADD", "role_id": role_id, "entry": _entry_for(definition, source)})
            continue
        if current.get("origin") == "package" or current.get("protected"):
            raise ContractError("PACKAGE_ROLE_PROTECTED", role_id)
        target = _entry_for(definition, source, current)
        if current == target:
            continue
        action = "REENABLE" if current.get("status") == "disabled" and current.get("definition") == definition and current.get("sources") == target["sources"] else "UPDATE"
        changes.append({"action": action, "role_id": role_id, "entry": target})

    if submission["mode"] == "snapshot":
        scope_ids = submission["scope"]["role_ids"]
        for role_id in scope_ids:
            if role_id in submitted:
                continue
            current = roles.get(role_id)
            if current is None:
                continue
            if current.get("origin") == "package" or current.get("protected"):
                raise ContractError("PACKAGE_ROLE_PROTECTED", role_id)
            if current.get("status") == "available":
                changes.append({"action": "DISABLE", "role_id": role_id})

    changes.sort(key=lambda item: (item["role_id"], item["action"]))
    return changes


def plan_role_submission(project_root: Path, submission: dict[str, Any]) -> dict[str, Any]:
    try:
        state, _ = _load_role_state(project_root)
        normalized = normalize_submission(submission)
        changes = _classify_changes(state, normalized)
        submission_digest = digest(normalized)
        if not changes:
            return operation_result("PASS", "NO_CHANGE", submission=normalized, submission_digest=submission_digest)
        change = {"submission": normalized, "changes": changes}
        proposal = make_proposal(DOMAIN, OPERATION, state, change)
        return operation_result(
            "PASS",
            "PLANNED",
            submission=normalized,
            submission_digest=submission_digest,
            proposal=proposal,
            proposal_digest=digest(proposal),
        )
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)


def approve_role_submission(proposal: dict[str, Any], approving_operator_id: str, authentication_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    auth: dict[str, Any] = {"method": "human_confirmation", "confirmation": CONFIRMATION}
    if authentication_evidence:
        auth["evidence"] = authentication_evidence
    return make_approval(proposal, approving_operator_id, auth)


def _validate_proposal_semantics(state: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    validate_proposal(proposal)
    if proposal["domain"] != DOMAIN or proposal["operation"] != OPERATION:
        raise ContractError("INVALID_ROLE_PROPOSAL", "proposal is not a role-registry transition")
    change = proposal["change"]
    if not isinstance(change, dict) or set(change) != {"submission", "changes"}:
        raise ContractError("INVALID_ROLE_PROPOSAL", "role proposal change shape is invalid")
    normalized = normalize_submission(change["submission"])
    expected = _classify_changes(state, normalized)
    if not expected:
        raise ContractError("INVALID_ROLE_PROPOSAL", "proposal contains no mutation")
    expected_change = {"submission": normalized, "changes": expected}
    if change != expected_change:
        raise ContractError("INVALID_ROLE_PROPOSAL", "proposal does not match deterministic role diff")
    return expected_change


def _validate_approval(approval: dict[str, Any], proposal: dict[str, Any]) -> None:
    validate_approval(approval, proposal)
    auth = approval["authentication"]
    if auth.get("method") != "human_confirmation" or auth.get("confirmation") != CONFIRMATION:
        raise ContractError("HUMAN_CONFIRMATION_REQUIRED", f"explicit {CONFIRMATION} confirmation is required")


def _transition(current: Any, change: Any) -> dict[str, Any]:
    state = copy.deepcopy(current)
    roles = state["roles"]
    for item in change["changes"]:
        role_id = item["role_id"]
        action = item["action"]
        if action in {"ADD", "UPDATE", "REENABLE"}:
            roles[role_id] = copy.deepcopy(item["entry"])
        elif action == "DISABLE":
            entry = roles.get(role_id)
            if entry is None:
                raise ContractError("ROLE_NOT_FOUND", role_id)
            if entry.get("origin") == "package" or entry.get("protected"):
                raise ContractError("PACKAGE_ROLE_PROTECTED", role_id)
            entry["status"] = "disabled"
        else:
            raise ContractError("INVALID_ROLE_ACTION", action)
    return state


def _persist_artifact(directory: Path, artifact: dict[str, Any]) -> None:
    data = canonical_json_bytes(artifact)
    hex_digest = digest(artifact).split(":", 1)[1]
    path = directory / f"{hex_digest}.json"
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ContractError("EVIDENCE_CONFLICT", str(path))
        return
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "xb") as handle:
            handle.write(data)
            handle.flush()
    except FileExistsError:
        if path.is_symlink() or path.read_bytes() != data:
            raise ContractError("EVIDENCE_CONFLICT", str(path))


def apply_role_submission(project_root: Path, proposal: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    events_dir, projection_path = role_paths(project_root)
    submissions_dir, proposals_dir, approvals_dir = evidence_paths(project_root)
    try:
        state, events = _load_role_state(project_root)
        change = _validate_proposal_semantics(state, proposal)
        _validate_approval(approval, proposal)
        pd = digest(proposal)
        ad = digest(approval)
        consumed = next((e for e in events if e["proposal_digest"] == pd and e["approval_digest"] == ad), None)
        if consumed is None:
            operator_state = _load_operator_state(project_root)
            _validate_role_approver(operator_state, approval["operator_id"])
        _persist_artifact(submissions_dir, change["submission"])
        _persist_artifact(proposals_dir, proposal)
        _persist_artifact(approvals_dir, approval)
        return apply_transition(
            proposal=proposal,
            approval=approval,
            events_dir=events_dir,
            projection_path=projection_path,
            transition=_transition,
            initial_state=DEFAULT_ROLE_STATE,
        )
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)


def rebuild_role_projection(project_root: Path) -> dict[str, Any]:
    events_dir, projection_path = role_paths(project_root)
    return rebuild_projection(events_dir, projection_path, DEFAULT_ROLE_STATE)


def read_role_registry(project_root: Path) -> dict[str, Any]:
    try:
        events_dir, projection_path = role_paths(project_root)
        status = projection_status(events_dir, projection_path, DEFAULT_ROLE_STATE)
        if status["status"] == "CONFLICT":
            return operation_result("FAIL", "PROJECTION_CONFLICT", projection_status=status)
        if status["status"] == "REBUILDABLE":
            rebuilt = rebuild_projection(events_dir, projection_path, DEFAULT_ROLE_STATE)
            if rebuilt["status"] != "PASS":
                return rebuilt
        state, _ = replay(events_dir, DEFAULT_ROLE_STATE)
        return operation_result("PASS", "ROLE_REGISTRY_READY", registry=state)
    except ContractError as exc:
        return operation_result("FAIL", exc.code, exc.detail)
