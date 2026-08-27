#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from ril_admission import jcs, sha256_bytes
from ril_canonical_recovery_approval import (
    ROOT_APPROVAL_CONTRACT,
    parse_and_validate_recovery_root_approval,
)
from ril_canonical_recovery_planner import (
    CANONICAL_COVE_PATH,
    CANONICAL_PEMS_PATH,
    PLAN_CONTRACT,
    TERMINAL_PROVENANCE_CLASS,
    build_mode_a_recovery_plan,
)
from ril_canonical_recovery_recipe import RECIPE_ID, build_missing_top_level_semantic_pems2, git_blob_sha1
from ril_canonical_store import (
    BARRIER_ACTIVE_STATE,
    BARRIER_CONTRACT,
    BARRIER_RELATIVE_PATH,
    CanonicalPairSnapshot,
    exclusive_canonical_store,
)
from ril_mutation import ContractError
from ril_storage_verification import verify_storage_snapshot

RESULT_CONTRACT = "reasoning-distiller-canonical-recovery-result/1"
COMPLETION_CONTRACT = "reasoning-distiller-canonical-recovery-completion/1"
JOURNAL_CONTRACT = "reasoning-distiller-canonical-recovery-journal/1"
RECOVERY_NAMESPACE = PurePosixPath("project-knowledge/recovery/canonical-pems-cove")

_STABLE_OUTCOMES = frozenset({
    "RECOVERED",
    "RECOVERY_NOT_REQUIRED",
    "UNSUPPORTED_CANONICAL_DAMAGE",
    "CANONICAL_PRESTATE_MISMATCH",
    "ROOT_RECOVERY_APPROVAL_REQUIRED",
    "ROOT_RECOVERY_APPROVAL_MISMATCH",
    "RECOVERY_PLAN_MISMATCH",
    "MIGRATION_RECIPE_MISMATCH",
    "EXECUTOR_CLOSURE_MISMATCH",
    "PEMS_RECOVERY_INVALID",
    "COVE_PRESTATE_MISMATCH",
    "COVE_RECOVERY_MISMATCH",
    "CANONICAL_RECOVERY_BUSY",
    "CANONICAL_RECOVERY_ACTIVE",
    "CANONICAL_RECOVERY_BARRIER_INVALID",
    "RECOVERY_PUBLICATION_FAILED_ROLLED_BACK",
    "CANONICAL_RECOVERY_INDETERMINATE",
    "RECOVERY_CONFLICT",
    "NO_CHANGE",
})

_PLAN_FIELDS = {
    "contract",
    "project_id",
    "generation",
    "canonical_paths",
    "prestate",
    "preserved_evidence_inventory_sha256",
    "mode",
    "recipe_id",
    "recipe_implementation_identity",
    "candidate",
    "equivalence_proof_sha256",
    "implementation_closure",
    "runtime_identity",
    "recovery_contract_identity",
    "r14_v2_contract_identity",
    "expected_barrier_identity",
    "expected_terminal_provenance_class",
}


def _result(
    status: str,
    outcome: str,
    *,
    plan: dict[str, Any] | None = None,
    plan_sha256: str | None = None,
    snapshot: CanonicalPairSnapshot | None = None,
    completion_path: str | None = None,
    completion_sha256: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {"contract": RESULT_CONTRACT, "status": status, "outcome": outcome}
    if plan is not None:
        value["project_id"] = plan.get("project_id")
        value["generation"] = plan.get("generation")
    if plan_sha256 is not None:
        value["recovery_plan_sha256"] = plan_sha256
    if snapshot is not None and snapshot.state == "PRESENT":
        value["pems_sha256"] = snapshot.pems_sha256
        value["cove_sha256"] = snapshot.cove_sha256
    if completion_path is not None:
        value["completion_path"] = completion_path
    if completion_sha256 is not None:
        value["completion_sha256"] = completion_sha256
    if detail:
        value["detail"] = detail
    return value


def _strict_canonical_object(raw: bytes, code: str) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(code, "artifact is not UTF-8") from exc

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate object key: {key}")
            out[key] = value
        return out

    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-JSON numeric constant: {value}")

    try:
        value = json.loads(text, object_pairs_hook=pairs_hook, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ContractError(code, "artifact JSON is invalid") from exc
    if not isinstance(value, dict):
        raise ContractError(code, "artifact must be a JSON object")
    try:
        canonical = jcs(value)
    except Exception as exc:
        raise ContractError(code, "artifact is not canonical JSON data") from exc
    if canonical != raw:
        raise ContractError(code, "artifact bytes are not canonical")
    return value


def _validate_plan(plan: dict[str, Any]) -> None:
    if set(plan) != _PLAN_FIELDS or plan.get("contract") != PLAN_CONTRACT:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "recovery plan fields do not match G4 contract realization")
    if plan.get("mode") != "A" or plan.get("recipe_id") != RECIPE_ID:
        raise ContractError("MIGRATION_RECIPE_MISMATCH", "recovery plan is outside V1 Mode A recipe")
    if plan.get("expected_terminal_provenance_class") != TERMINAL_PROVENANCE_CLASS:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "terminal provenance class mismatch")
    if plan.get("canonical_paths") != {"pems": CANONICAL_PEMS_PATH, "cove": CANONICAL_COVE_PATH}:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "canonical path binding mismatch")
    project_id = plan.get("project_id")
    generation = plan.get("generation")
    if not isinstance(project_id, str) or not project_id or not isinstance(generation, str) or not generation:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "project identity or generation is invalid")
    if "/" in generation or "\\" in generation or any(ord(ch) < 0x20 for ch in generation):
        raise ContractError("RECOVERY_PLAN_MISMATCH", "generation is not one safe path component")
    prestate = plan.get("prestate")
    candidate = plan.get("candidate")
    if not isinstance(prestate, dict) or not isinstance(candidate, dict):
        raise ContractError("RECOVERY_PLAN_MISMATCH", "prestate/candidate bindings are invalid")
    if set(prestate) != {"pems_sha256", "cove_sha256", "pems_git_blob", "cove_git_blob"}:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "prestate binding fields changed")
    if set(candidate) != {"pems_sha256", "cove_sha256"}:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "candidate binding fields changed")
    barrier = plan.get("expected_barrier_identity")
    if not isinstance(barrier, dict) or barrier.get("contract") != BARRIER_CONTRACT or barrier.get("transaction_state") != BARRIER_ACTIVE_STATE:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "expected barrier identity mismatch")
    if not isinstance(barrier.get("recovery_contract_sha256"), str):
        raise ContractError("RECOVERY_PLAN_MISMATCH", "expected barrier recovery contract identity missing")


def _validate_inventory(plan: dict[str, Any], raw: bytes) -> tuple[dict[str, Any], list[str]]:
    inventory = _strict_canonical_object(raw, "RECOVERY_PLAN_MISMATCH")
    if sha256_bytes(raw) != plan.get("preserved_evidence_inventory_sha256"):
        raise ContractError("RECOVERY_PLAN_MISMATCH", "preserved evidence inventory digest mismatch")
    if set(inventory) != {"entries"} or not isinstance(inventory.get("entries"), list):
        raise ContractError("RECOVERY_PLAN_MISMATCH", "preserved evidence inventory shape is invalid")
    selected: list[str] = []
    canonical_seen: dict[str, dict[str, Any]] = {}
    seen_paths: set[str] = set()
    for entry in inventory["entries"]:
        if not isinstance(entry, dict) or set(entry) != {"kind", "path", "byte_length", "sha256", "git_blob"}:
            raise ContractError("RECOVERY_PLAN_MISMATCH", "preserved evidence inventory entry is invalid")
        relative = _safe_relative(entry.get("path"), "RECOVERY_PLAN_MISMATCH")
        rendered = relative.as_posix()
        if rendered in seen_paths:
            raise ContractError("RECOVERY_PLAN_MISMATCH", "preserved evidence inventory has duplicate path")
        seen_paths.add(rendered)
        if not isinstance(entry.get("byte_length"), int) or isinstance(entry.get("byte_length"), bool) or entry["byte_length"] < 0:
            raise ContractError("RECOVERY_PLAN_MISMATCH", "preserved evidence byte length is invalid")
        if not _hex_digest(entry.get("sha256"), 64) or not _hex_digest(entry.get("git_blob"), 40):
            raise ContractError("RECOVERY_PLAN_MISMATCH", "preserved evidence identity is invalid")
        if entry["kind"] == "canonical_prestate":
            canonical_seen[rendered] = entry
        elif entry["kind"] == "immutable_project_evidence":
            if rendered in {CANONICAL_PEMS_PATH, CANONICAL_COVE_PATH}:
                raise ContractError("RECOVERY_PLAN_MISMATCH", "canonical paths may not be selected evidence")
            selected.append(rendered)
        else:
            raise ContractError("RECOVERY_PLAN_MISMATCH", "unknown preserved evidence kind")
    if set(canonical_seen) != {CANONICAL_PEMS_PATH, CANONICAL_COVE_PATH}:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "canonical prestate inventory entries are incomplete")
    if canonical_seen[CANONICAL_PEMS_PATH]["sha256"] != plan["prestate"]["pems_sha256"]:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "inventory PEMS prestate digest mismatch")
    if canonical_seen[CANONICAL_COVE_PATH]["sha256"] != plan["prestate"]["cove_sha256"]:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "inventory COVE prestate digest mismatch")
    return inventory, sorted(selected)


def _safe_relative(value: Any, code: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ContractError(code, "relative path is required")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ContractError(code, f"unsafe relative path: {value}")
    return path


def _hex_digest(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and all(ch in "0123456789abcdef" for ch in value)


def _read_project_file(root: Path, relative: str, code: str) -> bytes:
    rel = _safe_relative(relative, code)
    base = root.resolve()
    current = base
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ContractError(code, f"symlink path component: {relative}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(base)
    except (OSError, ValueError) as exc:
        raise ContractError(code, relative) from exc
    if not resolved.is_file():
        raise ContractError(code, relative)
    return resolved.read_bytes()


def _behavior_dependency_paths(plan: dict[str, Any]) -> list[str]:
    closure = plan.get("implementation_closure")
    if not isinstance(closure, dict):
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "implementation closure is invalid")
    dependencies = closure.get("behavior_dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "behavior dependency closure is empty")
    paths: list[str] = []
    for identity in dependencies:
        if not isinstance(identity, dict) or not isinstance(identity.get("path"), str):
            raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "behavior dependency identity is invalid")
        paths.append(identity["path"])
    if len(paths) != len(set(paths)):
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "behavior dependency paths are duplicated")
    return paths


def _validate_identity(package_root: Path, identity: Any, code: str) -> None:
    if not isinstance(identity, dict):
        raise ContractError(code, "implementation identity must be an object")
    path = identity.get("path")
    expected_sha = identity.get("sha256")
    expected_blob = identity.get("git_blob")
    if not isinstance(path, str) or not _hex_digest(expected_sha, 64):
        raise ContractError(code, "implementation identity is malformed")
    if expected_blob is not None and not _hex_digest(expected_blob, 40):
        raise ContractError(code, "implementation git blob identity is malformed")
    data = _read_project_file(package_root, path, code) if not Path(path).is_absolute() else Path(path).read_bytes()
    if sha256_bytes(data) != expected_sha:
        raise ContractError(code, f"implementation SHA-256 drift: {path}")
    if expected_blob is not None and git_blob_sha1(data) != expected_blob:
        raise ContractError(code, f"implementation Git blob drift: {path}")


def _validate_current_implementation_closure(plan: dict[str, Any], package_root: Path) -> None:
    closure = plan.get("implementation_closure")
    if not isinstance(closure, dict):
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "implementation closure is invalid")
    expected_roles = {
        "recipe", "schema", "validator", "normalizer", "serializer", "cove_codec",
        "planner", "canonical_store", "recovery_executor", "behavior_dependencies", "package_build",
    }
    if set(closure) != expected_roles:
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "implementation closure role set changed")
    for role in sorted(expected_roles - {"behavior_dependencies"}):
        _validate_identity(package_root, closure[role], "EXECUTOR_CLOSURE_MISMATCH")
    for identity in closure["behavior_dependencies"]:
        _validate_identity(package_root, identity, "EXECUTOR_CLOSURE_MISMATCH")
    _validate_identity(package_root, plan.get("recovery_contract_identity"), "RECOVERY_PLAN_MISMATCH")
    _validate_identity(package_root, plan.get("r14_v2_contract_identity"), "RECOVERY_PLAN_MISMATCH")
    recipe_identity = plan.get("recipe_implementation_identity")
    if recipe_identity != closure.get("recipe"):
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "recipe identity differs from implementation closure")
    barrier_identity = plan["expected_barrier_identity"]
    if barrier_identity.get("recovery_contract_sha256") != plan["recovery_contract_identity"].get("sha256"):
        raise ContractError("RECOVERY_PLAN_MISMATCH", "barrier recovery-contract identity mismatch")


def _verify_inventory_sources(root: Path, inventory: dict[str, Any]) -> dict[str, bytes]:
    selected: dict[str, bytes] = {}
    for entry in inventory["entries"]:
        if entry["kind"] != "immutable_project_evidence":
            continue
        raw = _read_project_file(root, entry["path"], "RECOVERY_PLAN_MISMATCH")
        if len(raw) != entry["byte_length"] or sha256_bytes(raw) != entry["sha256"] or git_blob_sha1(raw) != entry["git_blob"]:
            raise ContractError("RECOVERY_PLAN_MISMATCH", f"selected evidence drift: {entry['path']}")
        selected[entry["path"]] = raw
    return selected


def _generation_root(root: Path, generation: str) -> Path:
    return root / RECOVERY_NAMESPACE / "generations" / generation


def _ensure_dir(path: Path, parent: Path) -> None:
    if os.path.lexists(path):
        if path.is_symlink() or not path.is_dir():
            raise ContractError("RECOVERY_CONFLICT", str(path))
        return
    os.mkdir(path)
    _fsync_dir(parent)


def _write_immutable(path: Path, data: bytes) -> None:
    if os.path.lexists(path):
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ContractError("RECOVERY_CONFLICT", f"conflicting immutable recovery artifact: {path}")
        return
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd: int | None = None
    try:
        fd = os.open(path, flags, 0o600)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short immutable recovery artifact write")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = None
        _fsync_dir(path.parent)
    finally:
        if fd is not None:
            os.close(fd)


def _fsync_dir(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _preserve_generation(
    root: Path,
    plan: dict[str, Any],
    plan_bytes: bytes,
    approval_bytes: bytes,
    inventory_bytes: bytes,
    inventory: dict[str, Any],
    selected_sources: dict[str, bytes],
    prestate: CanonicalPairSnapshot,
    recipe_candidate,
) -> dict[str, Path]:
    recovery = root / RECOVERY_NAMESPACE
    generations = recovery / "generations"
    generation_root = generations / plan["generation"]
    knowledge = root / "project-knowledge"
    _ensure_dir(knowledge, root)
    _ensure_dir(root / "project-knowledge" / "recovery", knowledge)
    _ensure_dir(recovery, root / "project-knowledge" / "recovery")
    _ensure_dir(generations, recovery)
    _ensure_dir(generation_root, generations)
    prestate_dir = generation_root / "prestate"
    evidence_dir = generation_root / "evidence"
    candidate_dir = generation_root / "candidate"
    _ensure_dir(prestate_dir, generation_root)
    _ensure_dir(evidence_dir, generation_root)
    _ensure_dir(candidate_dir, generation_root)

    paths = {
        "generation": generation_root,
        "prestate_pems": prestate_dir / "pems2.raw",
        "prestate_cove": prestate_dir / "cove1.raw",
        "inventory": generation_root / "inventory.json",
        "plan": generation_root / "plan.json",
        "approval": generation_root / "root-approval.json",
        "proof": generation_root / "equivalence-proof.json",
        "closure": generation_root / "executor-closure.json",
        "candidate_pems": candidate_dir / "pems2.jcs.json",
        "candidate_cove": candidate_dir / "cove1.jcs.json",
        "journal": generation_root / "journal.json",
        "completion": generation_root / "completion.json",
    }
    assert prestate.pems_bytes is not None and prestate.cove_bytes is not None
    _write_immutable(paths["prestate_pems"], prestate.pems_bytes)
    _write_immutable(paths["prestate_cove"], prestate.cove_bytes)
    _write_immutable(paths["inventory"], inventory_bytes)
    _write_immutable(paths["plan"], plan_bytes)
    _write_immutable(paths["approval"], approval_bytes)
    _write_immutable(paths["proof"], recipe_candidate.equivalence_proof_bytes)
    _write_immutable(paths["closure"], jcs(plan["implementation_closure"]))
    _write_immutable(paths["candidate_pems"], recipe_candidate.candidate_pems_bytes)
    _write_immutable(paths["candidate_cove"], recipe_candidate.candidate_cove_bytes)

    for relative, raw in selected_sources.items():
        destination = evidence_dir
        parts = _safe_relative(relative, "RECOVERY_PLAN_MISMATCH").parts
        for part in parts[:-1]:
            parent = destination
            destination = destination / part
            _ensure_dir(destination, parent)
        _write_immutable(destination / parts[-1], raw)

    _fsync_dir(generation_root)
    return paths


def _journal(plan: dict[str, Any], plan_sha: str) -> dict[str, Any]:
    return {
        "contract": JOURNAL_CONTRACT,
        "project_id": plan["project_id"],
        "generation": plan["generation"],
        "recovery_plan_sha256": plan_sha,
        "prestate": {
            "pems_sha256": plan["prestate"]["pems_sha256"],
            "cove_sha256": plan["prestate"]["cove_sha256"],
        },
        "poststate": {
            "pems_sha256": plan["candidate"]["pems_sha256"],
            "cove_sha256": plan["candidate"]["cove_sha256"],
        },
        "publication_order": [CANONICAL_PEMS_PATH, CANONICAL_COVE_PATH],
        "transaction_state": BARRIER_ACTIVE_STATE,
    }


def _barrier(plan: dict[str, Any], plan_sha: str, journal_path: str, journal_sha: str) -> dict[str, Any]:
    return {
        "contract": BARRIER_CONTRACT,
        "project_id": plan["project_id"],
        "generation": plan["generation"],
        "recovery_plan_sha256": plan_sha,
        "prestate": {
            "pems_path": CANONICAL_PEMS_PATH,
            "pems_sha256": plan["prestate"]["pems_sha256"],
            "cove_path": CANONICAL_COVE_PATH,
            "cove_sha256": plan["prestate"]["cove_sha256"],
        },
        "poststate": {
            "pems_sha256": plan["candidate"]["pems_sha256"],
            "cove_sha256": plan["candidate"]["cove_sha256"],
        },
        "transaction_state": BARRIER_ACTIVE_STATE,
        "journal_path": journal_path,
        "journal_sha256": journal_sha,
        "recovery_contract_sha256": plan["recovery_contract_identity"]["sha256"],
    }


def _completion(
    root: Path,
    plan: dict[str, Any],
    plan_sha: str,
    approval_sha: str,
    inventory_sha: str,
    proof_sha: str,
    journal_sha: str,
    paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "contract": COMPLETION_CONTRACT,
        "project_id": plan["project_id"],
        "generation": plan["generation"],
        "recovery_plan_sha256": plan_sha,
        "root_approval_path": _relative(paths["approval"], root),
        "root_approval_sha256": approval_sha,
        "preserved_evidence_inventory_path": _relative(paths["inventory"], root),
        "preserved_evidence_inventory_sha256": inventory_sha,
        "equivalence_proof_path": _relative(paths["proof"], root),
        "equivalence_proof_sha256": proof_sha,
        "prestate": dict(plan["prestate"]),
        "poststate": dict(plan["candidate"]),
        "recipe_id": plan["recipe_id"],
        "recipe_implementation_identity": plan["recipe_implementation_identity"],
        "implementation_closure": plan["implementation_closure"],
        "recovery_contract_identity": plan["recovery_contract_identity"],
        "r14_v2_contract_identity": plan["r14_v2_contract_identity"],
        "provenance_class": TERMINAL_PROVENANCE_CLASS,
        "journal_path": _relative(paths["journal"], root),
        "journal_sha256": journal_sha,
    }


def _snapshot_class(snapshot: CanonicalPairSnapshot, plan: dict[str, Any]) -> str:
    if snapshot.state != "PRESENT":
        return "OTHER"
    pair = (snapshot.pems_sha256, snapshot.cove_sha256)
    pre = (plan["prestate"]["pems_sha256"], plan["prestate"]["cove_sha256"])
    post = (plan["candidate"]["pems_sha256"], plan["candidate"]["cove_sha256"])
    if pair == pre:
        return "PRESTATE"
    if pair == post:
        return "POSTSTATE"
    if pair == (post[0], pre[1]):
        return "PEMS_PUBLISHED"
    return "OTHER"


def _validate_generation_artifact(path: Path, expected: bytes) -> None:
    if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
        raise ContractError("RECOVERY_CONFLICT", f"generation artifact mismatch: {path}")


def _load_preserved_prestate(paths: dict[str, Path], plan: dict[str, Any], package_root: Path):
    pems = paths["prestate_pems"].read_bytes()
    cove = paths["prestate_cove"].read_bytes()
    return build_missing_top_level_semantic_pems2(
        pems,
        cove,
        expected_project_id=plan["project_id"],
        expected_prestate_pems_sha256=plan["prestate"]["pems_sha256"],
        expected_prestate_cove_sha256=plan["prestate"]["cove_sha256"],
        expected_prestate_pems_git_blob=plan["prestate"]["pems_git_blob"],
        expected_prestate_cove_git_blob=plan["prestate"]["cove_git_blob"],
        package_root=package_root,
    )


def _postpublication_content_verified(root: Path, package_root: Path, snapshot: CanonicalPairSnapshot) -> bool:
    result = verify_storage_snapshot(root, package_root, snapshot)
    if result.get("status") == "PASS":
        return True
    return result.get("outcome") in {
        "ADMISSION_RECEIPT_MISSING",
        "ADMISSION_RECEIPT_MISMATCH",
        "RECOVERY_PROVENANCE_MISSING",
        "RECOVERY_PROVENANCE_INVALID",
        "RECOVERY_PROVENANCE_MISMATCH",
        "RECOVERY_PROVENANCE_CONFLICT",
    }


def _paths_for_existing(root: Path, generation: str) -> dict[str, Path]:
    generation_root = _generation_root(root, generation)
    return {
        "generation": generation_root,
        "prestate_pems": generation_root / "prestate" / "pems2.raw",
        "prestate_cove": generation_root / "prestate" / "cove1.raw",
        "inventory": generation_root / "inventory.json",
        "plan": generation_root / "plan.json",
        "approval": generation_root / "root-approval.json",
        "proof": generation_root / "equivalence-proof.json",
        "closure": generation_root / "executor-closure.json",
        "candidate_pems": generation_root / "candidate" / "pems2.jcs.json",
        "candidate_cove": generation_root / "candidate" / "cove1.jcs.json",
        "journal": generation_root / "journal.json",
        "completion": generation_root / "completion.json",
    }


def _completed_retry(
    root: Path,
    package_root: Path,
    store,
    plan: dict[str, Any],
    plan_bytes: bytes,
    plan_sha: str,
    approval_bytes: bytes,
    inventory_bytes: bytes,
) -> dict[str, Any] | None:
    paths = _paths_for_existing(root, plan["generation"])
    if not os.path.lexists(paths["generation"]) or not os.path.lexists(paths["completion"]):
        return None
    if paths["generation"].is_symlink() or not paths["generation"].is_dir():
        raise ContractError("RECOVERY_CONFLICT", "generation path is unsafe")
    _validate_generation_artifact(paths["plan"], plan_bytes)
    _validate_generation_artifact(paths["approval"], approval_bytes)
    _validate_generation_artifact(paths["inventory"], inventory_bytes)
    snapshot = store.recovery_pair_snapshot()
    if _snapshot_class(snapshot, plan) != "POSTSTATE":
        raise ContractError("RECOVERY_CONFLICT", "completed generation does not match current pair")
    verification = verify_storage_snapshot(root, package_root, snapshot)
    if verification.get("status") != "PASS" or verification.get("outcome") != TERMINAL_PROVENANCE_CLASS:
        raise ContractError("RECOVERY_CONFLICT", "completed generation does not verify as recovered")
    completion_raw = paths["completion"].read_bytes()
    completion = _strict_canonical_object(completion_raw, "RECOVERY_CONFLICT")
    if completion.get("recovery_plan_sha256") != plan_sha:
        raise ContractError("RECOVERY_CONFLICT", "completion recovery plan mismatch")
    return _result(
        "PASS",
        "NO_CHANGE",
        plan=plan,
        plan_sha256=plan_sha,
        snapshot=snapshot,
        completion_path=_relative(paths["completion"], root),
        completion_sha256=sha256_bytes(completion_raw),
    )


def apply_mode_a_recovery(
    project_root: Path,
    recovery_plan_bytes: bytes,
    root_approval_bytes: bytes,
    preserved_evidence_inventory_bytes: bytes,
    *,
    package_root: Path | None = None,
) -> dict[str, Any]:
    """Apply one exact, root-approved V1 Mode A canonical recovery transaction.

    The executor accepts only immutable canonical plan/approval/inventory bytes.
    It has no role, Steward, activation, semantic-reconciliation, or admission
    authority input. A valid exact protected-root approval is mandatory.
    """

    plan: dict[str, Any] | None = None
    plan_sha: str | None = None
    latest_snapshot: CanonicalPairSnapshot | None = None
    barrier_installed = False
    store = None
    staged: tuple[Path, Path] | None = None
    try:
        root = project_root.resolve()
        package = (package_root or Path(__file__).resolve().parents[1]).resolve()
        plan = _strict_canonical_object(recovery_plan_bytes, "RECOVERY_PLAN_MISMATCH")
        _validate_plan(plan)
        plan_sha = sha256_bytes(recovery_plan_bytes)
        inventory, selected_paths = _validate_inventory(plan, preserved_evidence_inventory_bytes)
        _validate_current_implementation_closure(plan, package)

        with exclusive_canonical_store(root) as store:
            _, approval_evidence = parse_and_validate_recovery_root_approval(root, plan, root_approval_bytes)
            approval_sha = approval_evidence["root_approval_sha256"]
            if approval_evidence["recovery_plan_sha256"] != plan_sha:
                raise ContractError("ROOT_RECOVERY_APPROVAL_MISMATCH", "approval digest differs from exact plan bytes")

            barrier = store.recovery_barrier()
            if barrier is None:
                completed = _completed_retry(
                    root,
                    package,
                    store,
                    plan,
                    recovery_plan_bytes,
                    plan_sha,
                    root_approval_bytes,
                    preserved_evidence_inventory_bytes,
                )
                if completed is not None:
                    return completed

                latest_snapshot = store.recovery_pair_snapshot()
                if latest_snapshot.state != "PRESENT" or latest_snapshot.pems_bytes is None or latest_snapshot.cove_bytes is None:
                    raise ContractError("CANONICAL_PRESTATE_MISMATCH", "canonical pair is not complete")
                ordinary = verify_storage_snapshot(root, package, latest_snapshot)
                if ordinary.get("status") == "PASS":
                    return _result(
                        "FAIL", "RECOVERY_NOT_REQUIRED", plan=plan, plan_sha256=plan_sha, snapshot=latest_snapshot
                    )
                if latest_snapshot.pems_sha256 != plan["prestate"]["pems_sha256"] or latest_snapshot.cove_sha256 != plan["prestate"]["cove_sha256"]:
                    raise ContractError("CANONICAL_PRESTATE_MISMATCH", "live canonical pair differs from approved prestate")

                selected_sources = _verify_inventory_sources(root, inventory)
                rebuilt = build_mode_a_recovery_plan(
                    latest_snapshot.pems_bytes,
                    latest_snapshot.cove_bytes,
                    project_root=root,
                    expected_project_id=plan["project_id"],
                    generation=plan["generation"],
                    expected_prestate_pems_sha256=plan["prestate"]["pems_sha256"],
                    expected_prestate_cove_sha256=plan["prestate"]["cove_sha256"],
                    expected_prestate_pems_git_blob=plan["prestate"]["pems_git_blob"],
                    expected_prestate_cove_git_blob=plan["prestate"]["cove_git_blob"],
                    selected_evidence_paths=selected_paths,
                    behavior_dependency_paths=_behavior_dependency_paths(plan),
                    package_root=package,
                )
                if rebuilt.plan_bytes != recovery_plan_bytes or rebuilt.preserved_evidence_inventory_bytes != preserved_evidence_inventory_bytes:
                    raise ContractError("RECOVERY_PLAN_MISMATCH", "apply-time rebuilt plan differs from approved plan")
                recipe_candidate = rebuilt.recipe_candidate
                paths = _preserve_generation(
                    root,
                    plan,
                    recovery_plan_bytes,
                    root_approval_bytes,
                    preserved_evidence_inventory_bytes,
                    inventory,
                    selected_sources,
                    latest_snapshot,
                    recipe_candidate,
                )
                staged = store.stage_recovery_pair(
                    recipe_candidate.candidate_pems_bytes,
                    recipe_candidate.candidate_cove_bytes,
                    plan["generation"],
                )
                journal = _journal(plan, plan_sha)
                journal_bytes = jcs(journal)
                _write_immutable(paths["journal"], journal_bytes)
                journal_sha = sha256_bytes(journal_bytes)
                barrier_value = _barrier(plan, plan_sha, _relative(paths["journal"], root), journal_sha)
                barrier_bytes = jcs(barrier_value)
                store.install_recovery_barrier(barrier_bytes)
                barrier_installed = True
            else:
                paths = _paths_for_existing(root, plan["generation"])
                if not paths["generation"].is_dir() or paths["generation"].is_symlink():
                    raise ContractError("CANONICAL_RECOVERY_INDETERMINATE", "active barrier generation is unavailable")
                _validate_generation_artifact(paths["plan"], recovery_plan_bytes)
                _validate_generation_artifact(paths["approval"], root_approval_bytes)
                _validate_generation_artifact(paths["inventory"], preserved_evidence_inventory_bytes)
                recipe_candidate = _load_preserved_prestate(paths, plan, package)
                _validate_generation_artifact(paths["proof"], recipe_candidate.equivalence_proof_bytes)
                _validate_generation_artifact(paths["candidate_pems"], recipe_candidate.candidate_pems_bytes)
                _validate_generation_artifact(paths["candidate_cove"], recipe_candidate.candidate_cove_bytes)
                journal_bytes = paths["journal"].read_bytes()
                journal = _strict_canonical_object(journal_bytes, "CANONICAL_RECOVERY_INDETERMINATE")
                journal_sha = sha256_bytes(journal_bytes)
                expected_barrier = _barrier(plan, plan_sha, _relative(paths["journal"], root), journal_sha)
                barrier_bytes = jcs(expected_barrier)
                if jcs(barrier) != barrier_bytes:
                    raise ContractError("RECOVERY_CONFLICT", "active barrier does not bind exact recovery transaction")
                barrier_installed = True
                latest_snapshot = store.recovery_pair_snapshot()
                classification = _snapshot_class(latest_snapshot, plan)
                if classification not in {"PRESTATE", "PEMS_PUBLISHED", "POSTSTATE"}:
                    raise ContractError("CANONICAL_RECOVERY_INDETERMINATE", "active transaction pair state is not mechanically classifiable")
                if classification != "POSTSTATE":
                    staged = store.stage_recovery_pair(
                        recipe_candidate.candidate_pems_bytes,
                        recipe_candidate.candidate_cove_bytes,
                        plan["generation"],
                    )

            if latest_snapshot is None:
                latest_snapshot = store.recovery_pair_snapshot()
            if _snapshot_class(latest_snapshot, plan) != "POSTSTATE":
                try:
                    assert staged is not None
                    latest_snapshot = store.publish_staged_recovery_pair(*staged)
                    staged = None
                except Exception as publication_exc:
                    if staged is not None:
                        try:
                            store.cleanup_recovery_stage(*staged)
                        except Exception:
                            pass
                    try:
                        pre_pems = paths["prestate_pems"].read_bytes()
                        pre_cove = paths["prestate_cove"].read_bytes()
                        rolled_back = store.rollback_recovery_pair(pre_pems, pre_cove)
                        if _snapshot_class(rolled_back, plan) != "PRESTATE":
                            raise ContractError("CANONICAL_RECOVERY_INDETERMINATE", "rollback hashes do not match approved prestate")
                        store.clear_recovery_barrier(barrier_bytes)
                        barrier_installed = False
                        return _result(
                            "FAIL",
                            "RECOVERY_PUBLICATION_FAILED_ROLLED_BACK",
                            plan=plan,
                            plan_sha256=plan_sha,
                            snapshot=rolled_back,
                            detail=str(publication_exc),
                        )
                    except Exception as rollback_exc:
                        return _result(
                            "FAIL",
                            "CANONICAL_RECOVERY_INDETERMINATE",
                            plan=plan,
                            plan_sha256=plan_sha,
                            snapshot=store.recovery_pair_snapshot(),
                            detail=str(rollback_exc),
                        )

            if _snapshot_class(latest_snapshot, plan) != "POSTSTATE":
                raise ContractError("CANONICAL_RECOVERY_INDETERMINATE", "publication did not reach exact approved poststate")
            if not _postpublication_content_verified(root, package, latest_snapshot):
                raise ContractError("CANONICAL_RECOVERY_INDETERMINATE", "poststate content verification failed")

            completion = _completion(
                root,
                plan,
                plan_sha,
                approval_sha,
                sha256_bytes(preserved_evidence_inventory_bytes),
                recipe_candidate.equivalence_proof_sha256,
                journal_sha,
                paths,
            )
            completion_bytes = jcs(completion)
            _write_immutable(paths["completion"], completion_bytes)
            _fsync_dir(paths["generation"])

            recovered = verify_storage_snapshot(root, package, store.internal_verification_snapshot())
            if recovered.get("status") != "PASS" or recovered.get("outcome") != TERMINAL_PROVENANCE_CLASS:
                raise ContractError(
                    "CANONICAL_RECOVERY_INDETERMINATE",
                    f"R14 recovered verification failed: {recovered.get('outcome')}",
                )
            store.clear_recovery_barrier(barrier_bytes)
            barrier_installed = False
            if staged is not None:
                store.cleanup_recovery_stage(*staged)
            final_snapshot = store.recovery_pair_snapshot()
            return _result(
                "PASS",
                "RECOVERED",
                plan=plan,
                plan_sha256=plan_sha,
                snapshot=final_snapshot,
                completion_path=_relative(paths["completion"], root),
                completion_sha256=sha256_bytes(completion_bytes),
            )
    except ContractError as exc:
        code = exc.code if exc.code in _STABLE_OUTCOMES else "CANONICAL_RECOVERY_INDETERMINATE"
        return _result(
            "FAIL",
            code,
            plan=plan,
            plan_sha256=plan_sha,
            snapshot=latest_snapshot,
            detail=exc.detail,
        )
    except OSError as exc:
        return _result(
            "FAIL",
            "CANONICAL_RECOVERY_INDETERMINATE" if barrier_installed else "RECOVERY_CONFLICT",
            plan=plan,
            plan_sha256=plan_sha,
            snapshot=latest_snapshot,
            detail=str(exc),
        )


if __name__ == "__main__":
    print(json.dumps(_result("FAIL", "CANONICAL_RECOVERY_INDETERMINATE", detail="library primitive only"), sort_keys=True, separators=(",", ":")))
