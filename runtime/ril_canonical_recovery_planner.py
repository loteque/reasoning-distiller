#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from ril_admission import jcs, sha256_bytes
from ril_canonical_recovery_recipe import (
    MODE,
    RECIPE_ID,
    ModeARecipeCandidate,
    build_missing_top_level_semantic_pems2,
    git_blob_sha1,
)
from ril_canonical_store import BARRIER_CONTRACT, COVE_RELATIVE_PATH, PEMS_RELATIVE_PATH
from ril_mutation import ContractError

PLAN_CONTRACT = "reasoning-distiller-canonical-recovery-plan/1"
TERMINAL_PROVENANCE_CLASS = "VERIFIED_RECOVERED"
CANONICAL_PEMS_PATH = PEMS_RELATIVE_PATH.as_posix()
CANONICAL_COVE_PATH = COVE_RELATIVE_PATH.as_posix()
RECOVERY_CONTRACT_PATH = "docs/operations/RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md"
R14_CONTRACT_PATH = "docs/operations/RIL_STORAGE_VERIFICATION_CONTRACT.md"
PACKAGE_BUILD_PATH = "packaging/package-build.json"
RECOVERY_EXECUTOR_PATH = "runtime/ril_canonical_recovery_executor.py"


@dataclass(frozen=True)
class RecoveryPlanCandidate:
    plan: dict[str, Any]
    plan_bytes: bytes
    plan_sha256: str
    preserved_evidence_inventory: dict[str, Any]
    preserved_evidence_inventory_bytes: bytes
    preserved_evidence_inventory_sha256: str
    recipe_candidate: ModeARecipeCandidate


def _safe_relative_path(value: str, code: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ContractError(code, "relative path is required")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ContractError(code, f"unsafe relative path: {value}")
    return path


def _ordinary_relative_file(root: Path, relative: str, code: str) -> Path:
    rel = _safe_relative_path(relative, code)
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
    return resolved


def _source_identity(
    root: Path,
    relative: str,
    *,
    code: str = "EXECUTOR_CLOSURE_MISMATCH",
    symbol: str | None = None,
) -> dict[str, str]:
    path = _ordinary_relative_file(root, relative, code)
    data = path.read_bytes()
    identity: dict[str, str] = {
        "path": _safe_relative_path(relative, code).as_posix(),
        "sha256": sha256_bytes(data),
        "git_blob": git_blob_sha1(data),
    }
    if symbol is not None:
        identity["symbol"] = symbol
    return identity


def _enrich_proof_identity(package_root: Path, identity: dict[str, Any]) -> dict[str, str]:
    path = identity.get("path")
    digest = identity.get("sha256")
    if not isinstance(path, str) or not isinstance(digest, str) or len(digest) != 64:
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "recipe proof identity is malformed")
    if Path(path).is_absolute():
        resolved = Path(path)
        if resolved.is_symlink() or not resolved.is_file():
            raise ContractError("EXECUTOR_CLOSURE_MISMATCH", f"recipe proof identity path is unsafe: {path}")
        data = resolved.read_bytes()
        actual = {"path": path, "sha256": sha256_bytes(data), "git_blob": git_blob_sha1(data)}
    else:
        actual = _source_identity(package_root, path)
    if actual["sha256"] != digest:
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", f"recipe proof identity drift: {path}")
    symbol = identity.get("symbol")
    if symbol is not None:
        if not isinstance(symbol, str) or not symbol:
            raise ContractError("EXECUTOR_CLOSURE_MISMATCH", f"invalid symbol identity: {path}")
        actual["symbol"] = symbol
    return actual


def _validate_generation(generation: str) -> str:
    if not isinstance(generation, str) or not generation or generation in {".", ".."}:
        raise ContractError("RECOVERY_PLAN_MISMATCH", "recovery generation is required")
    if "/" in generation or "\\" in generation or any(ord(ch) < 0x20 for ch in generation):
        raise ContractError("RECOVERY_PLAN_MISMATCH", "recovery generation must be one path-safe component")
    return generation


def _runtime_identity() -> dict[str, str]:
    try:
        jsonschema_version = importlib.metadata.version("jsonschema")
    except importlib.metadata.PackageNotFoundError as exc:
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "jsonschema runtime identity is unavailable") from exc
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_cache_tag": sys.implementation.cache_tag or "",
        "jsonschema_version": jsonschema_version,
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
    }


def _selected_evidence_inventory(
    project_root: Path,
    selected_evidence_paths: Iterable[str],
    *,
    prestate_pems_bytes: bytes,
    prestate_cove_bytes: bytes,
    pems_git_blob: str,
    cove_git_blob: str,
) -> tuple[dict[str, Any], bytes, str]:
    paths = list(selected_evidence_paths)
    if len(paths) != len(set(paths)):
        raise ContractError("RECOVERY_PLAN_MISMATCH", "preserved evidence inventory contains duplicate paths")
    forbidden = {CANONICAL_PEMS_PATH, CANONICAL_COVE_PATH}
    if any(path in forbidden for path in paths):
        raise ContractError("RECOVERY_PLAN_MISMATCH", "canonical prestate paths are inventoried automatically")

    entries: list[dict[str, Any]] = [
        {
            "kind": "canonical_prestate",
            "path": CANONICAL_PEMS_PATH,
            "byte_length": len(prestate_pems_bytes),
            "sha256": sha256_bytes(prestate_pems_bytes),
            "git_blob": pems_git_blob,
        },
        {
            "kind": "canonical_prestate",
            "path": CANONICAL_COVE_PATH,
            "byte_length": len(prestate_cove_bytes),
            "sha256": sha256_bytes(prestate_cove_bytes),
            "git_blob": cove_git_blob,
        },
    ]
    for relative in sorted(paths):
        path = _ordinary_relative_file(project_root, relative, "RECOVERY_PLAN_MISMATCH")
        data = path.read_bytes()
        entries.append(
            {
                "kind": "immutable_project_evidence",
                "path": _safe_relative_path(relative, "RECOVERY_PLAN_MISMATCH").as_posix(),
                "byte_length": len(data),
                "sha256": sha256_bytes(data),
                "git_blob": git_blob_sha1(data),
            }
        )
    entries.sort(key=lambda entry: (entry["path"], entry["kind"]))
    inventory = {"entries": entries}
    encoded = jcs(inventory)
    return inventory, encoded, sha256_bytes(encoded)


def _implementation_closure(
    package_root: Path,
    recipe_candidate: ModeARecipeCandidate,
    *,
    behavior_dependency_paths: Iterable[str],
) -> dict[str, Any]:
    proof_identities = recipe_candidate.equivalence_proof.get("identities")
    if not isinstance(proof_identities, dict):
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "recipe proof has no implementation identities")
    expected = {"recipe", "schema", "validator", "normalizer", "serializer", "cove_codec"}
    if set(proof_identities) != expected:
        raise ContractError("EXECUTOR_CLOSURE_MISMATCH", "recipe proof implementation identity set changed")

    closure: dict[str, Any] = {
        role: _enrich_proof_identity(package_root, proof_identities[role])
        for role in sorted(expected)
    }
    closure["planner"] = _source_identity(
        package_root,
        "runtime/ril_canonical_recovery_planner.py",
        symbol="build_mode_a_recovery_plan",
    )
    closure["canonical_store"] = _source_identity(
        package_root,
        "runtime/ril_canonical_store.py",
        symbol="CanonicalStoreSession",
    )
    closure["recovery_executor"] = _source_identity(
        package_root,
        RECOVERY_EXECUTOR_PATH,
        code="EXECUTOR_CLOSURE_MISMATCH",
    )

    dependencies = list(behavior_dependency_paths)
    if not dependencies or len(dependencies) != len(set(dependencies)):
        raise ContractError(
            "EXECUTOR_CLOSURE_MISMATCH",
            "behavior-bearing dependency paths must be a non-empty unique set",
        )
    dependency_identities = [
        _source_identity(package_root, relative, code="EXECUTOR_CLOSURE_MISMATCH")
        for relative in sorted(dependencies)
    ]
    closure["behavior_dependencies"] = dependency_identities
    closure["package_build"] = _source_identity(
        package_root,
        PACKAGE_BUILD_PATH,
        code="EXECUTOR_CLOSURE_MISMATCH",
    )

    role_paths = {
        value["path"]
        for key, value in closure.items()
        if key not in {"behavior_dependencies"} and isinstance(value, dict) and "path" in value
    }
    dependency_paths = {item["path"] for item in dependency_identities}
    if role_paths & dependency_paths:
        raise ContractError(
            "EXECUTOR_CLOSURE_MISMATCH",
            "behavior dependency paths must not duplicate explicitly bound closure roles",
        )
    return closure


def build_mode_a_recovery_plan(
    prestate_pems_bytes: bytes,
    prestate_cove_bytes: bytes,
    *,
    project_root: Path,
    expected_project_id: str,
    generation: str,
    expected_prestate_pems_sha256: str,
    expected_prestate_cove_sha256: str,
    expected_prestate_pems_git_blob: str | None = None,
    expected_prestate_cove_git_blob: str | None = None,
    selected_evidence_paths: Iterable[str] = (),
    behavior_dependency_paths: Iterable[str],
    package_root: Path | None = None,
) -> RecoveryPlanCandidate:
    """Build one canonical Mode A recovery plan without mutating project state.

    The planner has no authority or apply surface. It refuses to emit a plan
    unless every required executable role, including the recovery executor, can
    be fingerprinted from exact source bytes. This lets G4 implement planning
    before G6 exists without inventing a future executor identity: a complete
    incident plan becomes constructible only after that source actually exists.
    """

    root = project_root.resolve()
    package = (package_root or Path(__file__).resolve().parents[1]).resolve()
    generation = _validate_generation(generation)

    computed_pems_blob = git_blob_sha1(prestate_pems_bytes)
    computed_cove_blob = git_blob_sha1(prestate_cove_bytes)
    pems_blob = expected_prestate_pems_git_blob or computed_pems_blob
    cove_blob = expected_prestate_cove_git_blob or computed_cove_blob

    recipe_candidate = build_missing_top_level_semantic_pems2(
        prestate_pems_bytes,
        prestate_cove_bytes,
        expected_project_id=expected_project_id,
        expected_prestate_pems_sha256=expected_prestate_pems_sha256,
        expected_prestate_cove_sha256=expected_prestate_cove_sha256,
        expected_prestate_pems_git_blob=pems_blob,
        expected_prestate_cove_git_blob=cove_blob,
        package_root=package,
    )

    inventory, inventory_bytes, inventory_sha = _selected_evidence_inventory(
        root,
        selected_evidence_paths,
        prestate_pems_bytes=prestate_pems_bytes,
        prestate_cove_bytes=prestate_cove_bytes,
        pems_git_blob=pems_blob,
        cove_git_blob=cove_blob,
    )

    closure = _implementation_closure(
        package,
        recipe_candidate,
        behavior_dependency_paths=behavior_dependency_paths,
    )
    recovery_contract_identity = _source_identity(
        package,
        RECOVERY_CONTRACT_PATH,
        code="RECOVERY_PLAN_MISMATCH",
    )
    r14_contract_identity = _source_identity(
        package,
        R14_CONTRACT_PATH,
        code="RECOVERY_PLAN_MISMATCH",
    )

    plan: dict[str, Any] = {
        "contract": PLAN_CONTRACT,
        "project_id": expected_project_id,
        "generation": generation,
        "canonical_paths": {
            "pems": CANONICAL_PEMS_PATH,
            "cove": CANONICAL_COVE_PATH,
        },
        "prestate": {
            "pems_sha256": expected_prestate_pems_sha256,
            "cove_sha256": expected_prestate_cove_sha256,
            "pems_git_blob": pems_blob,
            "cove_git_blob": cove_blob,
        },
        "preserved_evidence_inventory_sha256": inventory_sha,
        "mode": MODE,
        "recipe_id": RECIPE_ID,
        "recipe_implementation_identity": closure["recipe"],
        "candidate": {
            "pems_sha256": recipe_candidate.candidate_pems_sha256,
            "cove_sha256": recipe_candidate.candidate_cove_sha256,
        },
        "equivalence_proof_sha256": recipe_candidate.equivalence_proof_sha256,
        "implementation_closure": closure,
        "runtime_identity": _runtime_identity(),
        "recovery_contract_identity": recovery_contract_identity,
        "r14_v2_contract_identity": r14_contract_identity,
        "expected_barrier_identity": {
            "contract": BARRIER_CONTRACT,
            "transaction_state": "ACTIVE",
            "recovery_contract_sha256": recovery_contract_identity["sha256"],
        },
        "expected_terminal_provenance_class": TERMINAL_PROVENANCE_CLASS,
    }
    plan_bytes = jcs(plan)
    return RecoveryPlanCandidate(
        plan=plan,
        plan_bytes=plan_bytes,
        plan_sha256=sha256_bytes(plan_bytes),
        preserved_evidence_inventory=inventory,
        preserved_evidence_inventory_bytes=inventory_bytes,
        preserved_evidence_inventory_sha256=inventory_sha,
        recipe_candidate=recipe_candidate,
    )
