#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ril_admission import COVE, PROFILE, SERIALIZER, _decode, encode_cove, jcs, normalize_pems, sha256_bytes
from ril_mutation import ContractError

RECIPE_ID = "missing_top_level_semantic_pems2/1"
MODE = "A"
_EXPECTED_PRESTATE_KEYS = {"project_id", "records", "relations"}


@dataclass(frozen=True)
class ModeARecipeCandidate:
    recipe_id: str
    candidate_pems_bytes: bytes
    candidate_cove_bytes: bytes
    candidate_pems_sha256: str
    candidate_cove_sha256: str
    equivalence_proof: dict[str, Any]
    equivalence_proof_bytes: bytes
    equivalence_proof_sha256: str


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _strict_json_bytes(data: bytes, code: str) -> Any:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(code, f"invalid UTF-8: {exc}") from exc

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
        return json.loads(text, object_pairs_hook=pairs_hook, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ContractError(code, str(exc)) from exc


def _ordinary_file(path: Path, code: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise ContractError(code, str(path))


def _file_identity(path: Path, package_root: Path, *, symbol: str | None = None) -> dict[str, str]:
    _ordinary_file(path, "RECOVERY_IMPLEMENTATION_IDENTITY_INVALID")
    resolved = path.resolve()
    try:
        rendered = resolved.relative_to(package_root.resolve()).as_posix()
    except ValueError:
        rendered = resolved.as_posix()
    out = {"path": rendered, "sha256": sha256_bytes(resolved.read_bytes())}
    if symbol is not None:
        out["symbol"] = symbol
    return out


def _load_validator(package_root: Path):
    validator_path = package_root / "backends" / "pems-cove" / "validate_pems2_contract.py"
    schema_path = package_root / "backends" / "pems-cove" / "pems-v2.schema.json"
    _ordinary_file(validator_path, "RECOVERY_IMPLEMENTATION_IDENTITY_INVALID")
    _ordinary_file(schema_path, "RECOVERY_IMPLEMENTATION_IDENTITY_INVALID")
    spec = importlib.util.spec_from_file_location("_ril_recovery_recipe_pems2_validator", validator_path)
    if spec is None or spec.loader is None:
        raise ContractError("RECOVERY_IMPLEMENTATION_IDENTITY_INVALID", str(validator_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise ContractError("RECOVERY_IMPLEMENTATION_IDENTITY_INVALID", f"invalid PEMS schema: {exc}") from exc
    return module, Draft202012Validator(schema), validator_path, schema_path


def _implementation_identities(package_root: Path, validator_path: Path, schema_path: Path) -> dict[str, Any]:
    admission_path = package_root / "runtime" / "ril_admission.py"
    recipe_path = Path(__file__).resolve()
    return {
        "recipe": _file_identity(recipe_path, package_root, symbol="build_missing_top_level_semantic_pems2"),
        "schema": _file_identity(schema_path, package_root),
        "validator": _file_identity(validator_path, package_root, symbol="validate_candidate_document"),
        "normalizer": _file_identity(admission_path, package_root, symbol="normalize_pems"),
        "serializer": _file_identity(admission_path, package_root, symbol="jcs"),
        "cove_codec": _file_identity(admission_path, package_root, symbol="encode_cove/_decode"),
    }


def _predicate(predicate_id: int, name: str) -> dict[str, Any]:
    return {"id": predicate_id, "name": name, "passed": True}


def build_missing_top_level_semantic_pems2(
    prestate_pems_bytes: bytes,
    prestate_cove_bytes: bytes,
    *,
    expected_project_id: str,
    expected_prestate_pems_sha256: str,
    expected_prestate_cove_sha256: str,
    expected_prestate_pems_git_blob: str | None = None,
    expected_prestate_cove_git_blob: str | None = None,
    package_root: Path | None = None,
) -> ModeARecipeCandidate:
    """Build the one V1 Mode A candidate and its exact mechanical equivalence proof.

    This function is read-only. It accepts no migration callback, transform DSL,
    semantic override, or alternate recipe. Any state outside the frozen missing
    top-level ``semantic`` predicate fails closed.
    """

    if not isinstance(expected_project_id, str) or not expected_project_id:
        raise ContractError("CANONICAL_PRESTATE_MISMATCH", "expected project identity is required")
    if sha256_bytes(prestate_pems_bytes) != expected_prestate_pems_sha256:
        raise ContractError("CANONICAL_PRESTATE_MISMATCH", "prestate PEMS SHA-256 mismatch")
    if sha256_bytes(prestate_cove_bytes) != expected_prestate_cove_sha256:
        raise ContractError("CANONICAL_PRESTATE_MISMATCH", "prestate COVE SHA-256 mismatch")
    if expected_prestate_pems_git_blob is not None and git_blob_sha1(prestate_pems_bytes) != expected_prestate_pems_git_blob:
        raise ContractError("CANONICAL_PRESTATE_MISMATCH", "prestate PEMS Git blob mismatch")
    if expected_prestate_cove_git_blob is not None and git_blob_sha1(prestate_cove_bytes) != expected_prestate_cove_git_blob:
        raise ContractError("CANONICAL_PRESTATE_MISMATCH", "prestate COVE Git blob mismatch")
    predicates = [_predicate(1, "approved_prestate_identity_matches")]

    try:
        source = _strict_json_bytes(prestate_pems_bytes, "UNSUPPORTED_CANONICAL_DAMAGE")
    except ContractError:
        raise
    if not isinstance(source, dict) or "semantic" in source:
        raise ContractError("UNSUPPORTED_CANONICAL_DAMAGE", "prestate must be an object with no top-level semantic key")
    predicates.append(_predicate(2, "prestate_object_missing_semantic"))

    # The current PEMS/2 schema has exactly four top-level members. Requiring the
    # malformed prestate to contain exactly the other three closes the V1 recipe
    # against alternate discriminator fields and unrelated top-level edits.
    if set(source) != _EXPECTED_PRESTATE_KEYS:
        raise ContractError("UNSUPPORTED_CANONICAL_DAMAGE", "prestate top-level shape is not the single missing-semantic class")
    predicates.append(_predicate(3, "no_alternate_or_conflicting_discriminator"))

    if source.get("project_id") != expected_project_id or not isinstance(source.get("records"), list) or not isinstance(source.get("relations"), list):
        raise ContractError("CANONICAL_PRESTATE_MISMATCH", "prestate project identity or graph structure mismatch")
    predicates.append(_predicate(4, "expected_project_records_relations_structure"))

    candidate = copy.deepcopy(source)
    candidate["semantic"] = PROFILE
    predicates.append(_predicate(5, "candidate_is_deep_copy_plus_semantic_only"))

    reversed_candidate = copy.deepcopy(candidate)
    del reversed_candidate["semantic"]
    if reversed_candidate != source:
        raise ContractError("UNSUPPORTED_CANONICAL_DAMAGE", "candidate differs from prestate beyond semantic insertion")
    predicates.append(_predicate(6, "semantic_removal_restores_exact_object"))

    try:
        normalized = normalize_pems(candidate)
    except ContractError as exc:
        raise ContractError("PEMS_RECOVERY_INVALID", exc.detail) from exc
    if normalized != candidate:
        raise ContractError("UNSUPPORTED_CANONICAL_DAMAGE", "normalization would reorder or alter semantic graph content")
    predicates.append(_predicate(7, "normalization_preserves_graph_order_and_values"))

    package = (package_root or Path(__file__).resolve().parents[1]).resolve()
    validator_module, schema_validator, validator_path, schema_path = _load_validator(package)
    try:
        errors = sorted(schema_validator.iter_errors(normalized), key=lambda err: list(err.path))
    except Exception as exc:
        raise ContractError("PEMS_RECOVERY_INVALID", str(exc)) from exc
    if errors:
        rendered = "; ".join(f"{list(err.path)}: {err.message}" for err in errors[:20])
        raise ContractError("PEMS_RECOVERY_INVALID", rendered)
    predicates.append(_predicate(8, "candidate_passes_exact_pems2_schema"))

    try:
        integrity = validator_module.validate_candidate_document(normalized, schema_validator)
    except Exception as exc:
        raise ContractError("PEMS_RECOVERY_INVALID", str(exc)) from exc
    predicates.append(_predicate(9, "candidate_passes_exact_pems2_integrity"))

    prestate_cove = _strict_json_bytes(prestate_cove_bytes, "COVE_PRESTATE_MISMATCH")
    if not isinstance(prestate_cove, dict) or prestate_cove.get("c") != COVE or prestate_cove.get("p") != PROFILE or prestate_cove.get("s") != SERIALIZER:
        raise ContractError("COVE_PRESTATE_MISMATCH", "prestate COVE tuple mismatch")
    try:
        decoded_prestate = _decode(prestate_cove["x"], prestate_cove["d"], prestate_cove["h"])
    except Exception as exc:
        raise ContractError("COVE_PRESTATE_MISMATCH", str(exc)) from exc
    if decoded_prestate != source:
        raise ContractError("COVE_PRESTATE_MISMATCH", "prestate COVE does not decode exactly to prestate PEMS")
    predicates.append(_predicate(10, "prestate_cove_decodes_exactly_to_prestate_pems"))

    candidate_pems_bytes = jcs(normalized)
    if candidate_pems_bytes != jcs(candidate):
        raise ContractError("PEMS_RECOVERY_INVALID", "candidate PEMS serialization mismatch")
    predicates.append(_predicate(11, "candidate_pems_is_exact_normalized_jcs"))

    candidate_cove = encode_cove(normalized)
    candidate_cove_bytes = jcs(candidate_cove)
    predicates.append(_predicate(12, "candidate_cove_generated_only_from_candidate_pems"))

    try:
        decoded_candidate = _decode(candidate_cove["x"], candidate_cove["d"], candidate_cove["h"])
    except Exception as exc:
        raise ContractError("COVE_RECOVERY_MISMATCH", str(exc)) from exc
    if decoded_candidate != candidate or jcs(decoded_candidate) != candidate_pems_bytes:
        raise ContractError("COVE_RECOVERY_MISMATCH", "candidate COVE round-trip does not reproduce candidate PEMS bytes")
    predicates.append(_predicate(13, "candidate_cove_roundtrip_exact"))

    repeated_pems = jcs(normalize_pems(copy.deepcopy(candidate)))
    repeated_cove = jcs(encode_cove(copy.deepcopy(candidate)))
    if repeated_pems != candidate_pems_bytes or repeated_cove != candidate_cove_bytes:
        raise ContractError("MIGRATION_RECIPE_MISMATCH", "repeated candidate generation is not byte-identical")
    predicates.append(_predicate(14, "repeated_generation_byte_identical"))

    identities = _implementation_identities(package, validator_path, schema_path)
    predicates.append(_predicate(15, "equivalence_proof_binds_all_predicates_and_implementation_identities"))

    candidate_pems_sha = sha256_bytes(candidate_pems_bytes)
    candidate_cove_sha = sha256_bytes(candidate_cove_bytes)
    proof: dict[str, Any] = {
        "mode": MODE,
        "recipe_id": RECIPE_ID,
        "project_id": expected_project_id,
        "prestate": {
            "pems_sha256": expected_prestate_pems_sha256,
            "cove_sha256": expected_prestate_cove_sha256,
            "pems_git_blob": expected_prestate_pems_git_blob,
            "cove_git_blob": expected_prestate_cove_git_blob,
        },
        "candidate": {
            "pems_sha256": candidate_pems_sha,
            "cove_sha256": candidate_cove_sha,
            "cove_tuple": f"{COVE}|{PROFILE}|{SERIALIZER}",
        },
        "predicate_results": predicates,
        "identities": identities,
        "pems_integrity": integrity,
        "semantic_delta": {"operation": "insert_top_level_member", "key": "semantic", "value": PROFILE},
        "semantic_judgment_required": False,
    }
    proof_bytes = jcs(proof)
    return ModeARecipeCandidate(
        recipe_id=RECIPE_ID,
        candidate_pems_bytes=candidate_pems_bytes,
        candidate_cove_bytes=candidate_cove_bytes,
        candidate_pems_sha256=candidate_pems_sha,
        candidate_cove_sha256=candidate_cove_sha,
        equivalence_proof=proof,
        equivalence_proof_bytes=proof_bytes,
        equivalence_proof_sha256=sha256_bytes(proof_bytes),
    )
