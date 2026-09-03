#!/usr/bin/env python3
"""Mode B B3 recovery-specific semantic-disposition primitive.

This module records a project-scoped semantic judgment.  It deliberately has
no candidate, plan, approval, recovery, Canon, admission, or authority-state
mutation capability.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from ril_activation import validate_activation
from ril_mutation import ContractError

DISPOSITION_CONTRACT = "reasoning-distiller-canonical-recovery-semantic-disposition/1"
RESULT_CONTRACT = "reasoning-distiller-canonical-recovery-semantic-disposition-result/1"
DAMAGE_CONTRACT = "reasoning-distiller-canonical-recovery-damage-analysis/1"
SCOPE = "semantic_reconciliation"
BASE = Path("project-knowledge/recovery/canonical-pems-cove-mode-b")
LIFECYCLES = {"current", "historical", "superseded", "tombstoned"}
DEPENDENCY_KINDS = {"conditional_validity", "structural", "legacy_untyped"}
RESULTS = {
    "ACCEPT_REPAIR": ("PASS", "ACCEPT_REPAIR"),
    "REJECT_REPAIR": ("FAIL", "SEMANTIC_DISPOSITION_REJECTED"),
    "DEFER_REPAIR": ("FAIL", "SEMANTIC_DISPOSITION_DEFERRED"),
}


def _bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("SEMANTIC_DISPOSITION_INVALID", str(exc)) from exc


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _safe_path(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative or relative.startswith("/"):
        raise ContractError("SEMANTIC_DISPOSITION_INVALID", "artifact path must be relative")
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ContractError("SEMANTIC_DISPOSITION_INVALID", "artifact path escapes project root") from exc
    if path.is_symlink() or not path.is_file():
        raise ContractError("SEMANTIC_DISPOSITION_INVALID", f"artifact is unavailable: {relative}")
    return path


def _load_ref(root: Path, ref: Any) -> tuple[Any, bytes]:
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        raise ContractError("SEMANTIC_DISPOSITION_INVALID", "artifact reference shape is invalid")
    raw = _safe_path(root, ref["path"]).read_bytes()
    if _sha(raw) != ref["sha256"]:
        raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", f"artifact digest mismatch: {ref['path']}")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("SEMANTIC_DISPOSITION_INVALID", f"invalid JSON: {ref['path']}") from exc
    return value, raw


def _validator(root: Path) -> Draft202012Validator:
    names = ("canonical-recovery-mode-b-common.schema.json", "canonical-recovery-semantic-disposition.schema.json")
    schemas = [json.loads((root / "schemas" / name).read_text(encoding="utf-8")) for name in names]
    registry = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in schemas])
    return Draft202012Validator(schemas[1], registry=registry)


def _validate_schema(root: Path, disposition: Any) -> None:
    errors = sorted(_validator(root).iter_errors(disposition), key=lambda e: list(e.absolute_path))
    if errors:
        path = "/" + "/".join(str(part) for part in errors[0].absolute_path)
        raise ContractError("SEMANTIC_DISPOSITION_INVALID", f"{path}: {errors[0].message}")
    # Round trip also excludes NaN and non-JSON values.
    if json.loads(_bytes(disposition)) != disposition:
        raise ContractError("SEMANTIC_DISPOSITION_INVALID", "disposition is not canonically representable")


def _validate_prestate(root: Path, damage: dict[str, Any], disposition: dict[str, Any]) -> None:
    if damage.get("contract") != DAMAGE_CONTRACT or damage.get("candidate_count") != 0:
        raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", "damage analysis contract is invalid")
    if damage.get("project") != disposition["project"] or damage.get("prestate") != disposition["prestate"]:
        raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", "project or prestate differs from damage analysis")
    if damage.get("damage_set", {}).get("additional_damage") is not False:
        raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", "damage analysis is not a closed repair profile")
    for name in ("pems", "cove"):
        identity = disposition["prestate"][name]
        if not isinstance(identity, dict) or set(identity) != {"path", "sha256", "git_blob"}:
            raise ContractError("SEMANTIC_DISPOSITION_INVALID", f"invalid {name} identity")
        raw = _safe_path(root, identity["path"]).read_bytes()
        if _sha(raw) != identity["sha256"] or _git_blob(raw) != identity["git_blob"]:
            raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", f"current {name} bytes differ from exact prestate")


def _expected_relations(root: Path, damage: dict[str, Any]) -> list[dict[str, Any]]:
    inventory, _ = _load_ref(root, damage.get("evidence_inventory"))
    relations = inventory.get("relations") if isinstance(inventory, dict) else None
    if not isinstance(relations, list):
        raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", "evidence inventory has no relation list")
    expected = [{"relation_id": r.get("id"), "from": r.get("from"), "to": r.get("to"), "kind": r.get("kind")} for r in relations]
    if len(expected) != damage["damage_set"]["relation_count"]:
        raise ContractError("MODE_B_DAMAGE_SET_MISMATCH", "inventory relation count differs from damage analysis")
    relation_inventory_bytes = json.dumps(relations, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"
    if _sha(relation_inventory_bytes) != damage["damage_set"]["ordered_relation_set_sha256"]:
        raise ContractError("MODE_B_DAMAGE_SET_MISMATCH", "inventory relation-set digest differs from damage analysis")
    return expected


def _validate_rows(root: Path, disposition: dict[str, Any], expected: list[dict[str, Any]]) -> None:
    # The digest names the complete ordered B2 inventory rows (including index
    # and key_set); row equality below binds the disposition projection.
    if not isinstance(disposition["ordered_relation_set_sha256"], str):
        raise ContractError("MODE_B_DAMAGE_SET_MISMATCH", "disposition relation-set digest is invalid")
    rows = disposition["values"]
    if len(rows) != len(expected):
        raise ContractError("MODE_B_DAMAGE_SET_MISMATCH", "value table must contain exactly one row per relation")
    seen: set[str] = set()
    for index, (row, relation) in enumerate(zip(rows, expected, strict=True)):
        actual = {key: row[key] for key in ("relation_id", "from", "to", "kind")}
        if actual != relation or row["relation_id"] in seen:
            raise ContractError("MODE_B_DAMAGE_SET_MISMATCH", f"relation row {index} is missing, duplicate, reordered, or mismatched")
        seen.add(row["relation_id"])
        if row["lifecycle"] not in LIFECYCLES:
            raise ContractError("SEMANTIC_DISPOSITION_INVALID", f"invalid lifecycle at row {index}")
        data = row["data"]
        if row["kind"] == "depends_on":
            if data.get("dependency_kind") not in DEPENDENCY_KINDS:
                raise ContractError("SEMANTIC_EVIDENCE_INSUFFICIENT", f"depends_on row {index} lacks a valid dependency_kind")
        elif "dependency_kind" in data:
            raise ContractError("SEMANTIC_DISPOSITION_INVALID", f"dependency_kind is invalid for row {index}")
        for ref in row["evidence"]:
            _load_ref(root, ref)


def _validate_r8(root: Path, disposition: dict[str, Any]) -> None:
    activation = disposition["activation"]
    if activation["requested_scope"] != SCOPE:
        raise ContractError("SEMANTIC_ACTIVATION_INVALID", "requested scope must be semantic_reconciliation")
    artifact, raw = _load_ref(root, activation["artifact"])
    if artifact.get("role_id") != activation["role_id"] or artifact.get("context", {}).get("invocation_id") != activation["invocation_id"]:
        raise ContractError("SEMANTIC_ACTIVATION_INVALID", "activation envelope does not match its artifact")
    result = validate_activation(root, SCOPE, artifact)
    if result.get("status") != "PASS" or result.get("outcome") != "ACTIVATION_ACCEPTED":
        raise ContractError("SEMANTIC_ACTIVATION_INVALID", result.get("outcome", "activation rejected"))
    if result.get("activation_digest") != "sha256:" + _sha(raw):
        raise ContractError("SEMANTIC_ACTIVATION_INVALID", "activation digest binding differs")


def _identity_key(disposition: dict[str, Any]) -> tuple[Any, Any, Any]:
    return disposition["project"], disposition["prestate"], disposition["damage_analysis"]


def _check_conflicts(root: Path, disposition: dict[str, Any], raw: bytes) -> None:
    directory = root / BASE / "semantic-dispositions"
    if not directory.exists():
        return
    for path in directory.glob("*.json"):
        if path.is_symlink() or not path.is_file():
            raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", "disposition store contains a non-ordinary entry")
        other_raw = path.read_bytes()
        try:
            other = json.loads(other_raw.decode("utf-8"))
        except Exception as exc:
            raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", "stored disposition is invalid") from exc
        if _identity_key(other) == _identity_key(disposition) and other_raw != raw:
            raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", "conflicting disposition already exists for damage/prestate")


def _publish(path: Path, raw: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        if path.is_symlink() or not path.is_file() or path.read_bytes() != raw:
            raise ContractError("SEMANTIC_DISPOSITION_MISMATCH", f"immutable artifact conflict: {path}")
        return False
    with os.fdopen(fd, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return True


def apply_semantic_disposition(project_root: Path, disposition: dict[str, Any]) -> dict[str, Any]:
    """Validate and immutably record one B3 disposition; always emits zero candidates."""
    try:
        _validate_schema(project_root, disposition)
        damage, _ = _load_ref(project_root, disposition["damage_analysis"])
        _validate_prestate(project_root, damage, disposition)
        expected = _expected_relations(project_root, damage)
        if disposition["ordered_relation_set_sha256"] != damage["damage_set"]["ordered_relation_set_sha256"]:
            raise ContractError("MODE_B_DAMAGE_SET_MISMATCH", "disposition relation-set digest differs")
        _validate_rows(project_root, disposition, expected)
        _validate_r8(project_root, disposition)

        raw = _bytes(disposition)
        digest = _sha(raw)
        _check_conflicts(project_root, disposition, raw)
        disposition_path = project_root / BASE / "semantic-dispositions" / f"{digest}.json"
        disposition_ref = {"path": disposition_path.relative_to(project_root).as_posix(), "sha256": digest}
        status, outcome = RESULTS[disposition["outcome"]]
        result = {
            "contract": RESULT_CONTRACT,
            "status": status,
            "outcome": outcome,
            "project": disposition["project"],
            "disposition": disposition_ref,
            "candidate_count": 0,
        }
        result_raw = _bytes(result)
        result_path = project_root / BASE / "semantic-disposition-results" / f"{digest}.json"

        wrote_disposition = _publish(disposition_path, raw)
        try:
            wrote_result = _publish(result_path, result_raw)
        except Exception:
            if wrote_disposition:
                disposition_path.unlink()
            raise
        return result
    except ContractError as exc:
        return {
            "contract": RESULT_CONTRACT,
            "status": "FAIL",
            "outcome": exc.code if exc.code in {
                "SEMANTIC_EVIDENCE_INSUFFICIENT", "SEMANTIC_DISPOSITION_MISMATCH",
                "SEMANTIC_ACTIVATION_INVALID"
            } else "SEMANTIC_DISPOSITION_INVALID",
            "project": disposition.get("project", {"project_id": "unknown"}) if isinstance(disposition, dict) else {"project_id": "unknown"},
            "disposition": {"path": "project-knowledge/recovery/canonical-pems-cove-mode-b/semantic-dispositions/unpublished.json", "sha256": "0" * 64},
            "candidate_count": 0,
        }
