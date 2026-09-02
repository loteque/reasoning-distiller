#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from ril_admission import COVE, PROFILE, RECEIPT_CONTRACT, SERIALIZER, _decode, encode_cove, jcs, normalize_pems, sha256_bytes
from ril_canonical_store import CanonicalPairSnapshot, shared_canonical_store
from ril_mutation import ContractError, load_json

RESULT_CONTRACT = "reasoning-distiller-storage-verification-result/2"
RECOVERY_PLAN_CONTRACT = "reasoning-distiller-canonical-recovery-plan/1"
RECOVERY_APPROVAL_CONTRACT = "reasoning-distiller-canonical-recovery-root-approval/1"
RECOVERY_COMPLETION_CONTRACT = "reasoning-distiller-canonical-recovery-completion/1"
RECOVERY_NAMESPACE = PurePosixPath("project-knowledge/recovery/canonical-pems-cove")
RECOVERY_RECIPE = "missing_top_level_semantic_pems2/1"
RECOVERED_CLASS = "VERIFIED_RECOVERED"
ADMITTED_CLASS = "VERIFIED_ADMITTED"
RECOVERY_CONFIRMATION = "AUTHORIZE_CANONICAL_PEMS_COVE_RECOVERY"


def _result(status: str, outcome: str, detail: str | None = None, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"contract": RESULT_CONTRACT, "status": status, "outcome": outcome}
    if detail:
        out["detail"] = detail
    out.update(extra)
    return out


def _ordinary_dir(path: Path, code: str) -> None:
    if path.exists() and (path.is_symlink() or not path.is_dir()):
        raise ContractError(code, str(path))


def _ordinary_file(path: Path, code: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise ContractError(code, str(path))


def _load_package_validator(package_root: Path):
    module_path = package_root / "backends" / "pems-cove" / "validate_pems2_contract.py"
    schema_path = package_root / "backends" / "pems-cove" / "pems-v2.schema.json"
    _ordinary_file(module_path, "PACKAGE_VALIDATOR_MISSING")
    _ordinary_file(schema_path, "PACKAGE_SCHEMA_MISSING")
    spec = importlib.util.spec_from_file_location("_ril_package_pems2_validator", module_path)
    if spec is None or spec.loader is None:
        raise ContractError("PACKAGE_VALIDATOR_MISSING", str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return module, Draft202012Validator(schema)


def _parse_json_bytes(data: bytes, invalid_code: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(invalid_code, str(exc)) from exc


def _strict_json_object(data: bytes, code: str) -> dict[str, Any]:
    def pairs(items):
        out: dict[str, Any] = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate JSON member: {key}")
            out[key] = value
        return out

    def reject_constant(value: str):
        raise ValueError(f"non-finite JSON value: {value}")

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ContractError(code, str(exc)) from exc
    if not isinstance(value, dict):
        raise ContractError(code, "recovery artifact must be a JSON object")
    return value


def _control_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("RECOVERY_PROVENANCE_INVALID", str(exc)) from exc


def _artifact_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _artifact_digest(data: bytes) -> str:
    return "sha256:" + _artifact_sha256(data)


def _relative_recovery_file(root: Path, relative: Any, code: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ContractError(code, "recovery artifact path must be a non-empty relative path")
    posix = PurePosixPath(relative)
    if posix.is_absolute() or any(part in {"", ".", ".."} for part in posix.parts):
        raise ContractError(code, relative)
    try:
        posix.relative_to(RECOVERY_NAMESPACE)
    except ValueError as exc:
        raise ContractError(code, relative) from exc
    current = root
    for part in posix.parts:
        current = current / part
        if current.is_symlink():
            raise ContractError(code, relative)
    if not current.is_file():
        raise ContractError(code, relative)
    return current


def _load_control_artifact(root: Path, relative: Any, contract: str | None, code: str) -> tuple[dict[str, Any], bytes, str]:
    path = _relative_recovery_file(root, relative, code)
    raw = path.read_bytes()
    value = _strict_json_object(raw, code)
    if _control_bytes(value) != raw:
        raise ContractError(code, f"recovery artifact is not canonical JSON: {relative}")
    if contract is not None and value.get("contract") != contract:
        raise ContractError(code, f"unexpected recovery artifact contract: {relative}")
    return value, raw, _artifact_sha256(raw)


def _scan_receipts(root: Path, pems_sha: str, cove_sha: str) -> tuple[list[str], dict[str, str], str | None]:
    receipts_dir = root / "project-knowledge" / "admission" / "receipts"
    if not receipts_dir.exists():
        return [], {}, "ADMISSION_RECEIPT_MISSING"
    _ordinary_dir(receipts_dir, "ADMISSION_RECEIPT_INVALID")
    paths: list[str] = []
    digests: dict[str, str] = {}
    saw_receipt = False
    for receipt_path in sorted(receipts_dir.glob("*.json"), key=lambda p: p.name):
        saw_receipt = True
        if receipt_path.is_symlink() or not receipt_path.is_file():
            raise ContractError("ADMISSION_RECEIPT_INVALID", str(receipt_path))
        try:
            receipt = load_json(receipt_path)
        except ContractError as exc:
            raise ContractError("ADMISSION_RECEIPT_INVALID", exc.detail) from exc
        if not isinstance(receipt, dict) or receipt.get("contract") != RECEIPT_CONTRACT:
            raise ContractError("ADMISSION_RECEIPT_INVALID", str(receipt_path))
        if receipt.get("admitted_pems_sha256") == pems_sha and receipt.get("admitted_cove_sha256") == cove_sha:
            rel = receipt_path.relative_to(root).as_posix()
            paths.append(rel)
            digests[rel] = _artifact_digest(receipt_path.read_bytes())
    if paths:
        return paths, digests, None
    return [], {}, "ADMISSION_RECEIPT_MISMATCH" if saw_receipt else "ADMISSION_RECEIPT_MISSING"


def _generation_dirs(root: Path) -> list[Path]:
    generations = root / RECOVERY_NAMESPACE / "generations"
    if not os.path.lexists(generations):
        return []
    if generations.is_symlink() or not generations.is_dir():
        raise ContractError("RECOVERY_PROVENANCE_INVALID", str(generations))
    result: list[Path] = []
    for path in sorted(generations.iterdir(), key=lambda p: p.name):
        if path.is_symlink() or not path.is_dir():
            raise ContractError("RECOVERY_PROVENANCE_INVALID", str(path))
        result.append(path)
    return result


def _completion_candidates(root: Path, pems_sha: str, cove_sha: str) -> list[tuple[Path, dict[str, Any], bytes]]:
    matches: list[tuple[Path, dict[str, Any], bytes]] = []
    for generation in _generation_dirs(root):
        path = generation / "completion.json"
        if not os.path.lexists(path):
            continue
        if path.is_symlink() or not path.is_file():
            raise ContractError("RECOVERY_PROVENANCE_INVALID", str(path))
        raw = path.read_bytes()
        value = _strict_json_object(raw, "RECOVERY_PROVENANCE_INVALID")
        if value.get("contract") != RECOVERY_COMPLETION_CONTRACT:
            raise ContractError("RECOVERY_PROVENANCE_INVALID", f"unexpected completion contract: {path}")
        if _control_bytes(value) != raw:
            raise ContractError("RECOVERY_PROVENANCE_INVALID", f"completion is not canonical JSON: {path}")
        poststate = value.get("poststate")
        if isinstance(poststate, dict) and poststate.get("pems_sha256") == pems_sha and poststate.get("cove_sha256") == cove_sha:
            matches.append((path, value, raw))
    return matches


def _find_plan(root: Path, generation_dir: Path, expected_sha256: Any) -> tuple[str, dict[str, Any], bytes, str]:
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise ContractError("RECOVERY_PROVENANCE_INVALID", "completion recovery_plan_sha256 is invalid")
    path = generation_dir / "plan.json"
    if path.is_symlink() or not path.is_file():
        raise ContractError("RECOVERY_PROVENANCE_MISSING", "immutable recovery plan is absent")
    raw = path.read_bytes()
    plan = _strict_json_object(raw, "RECOVERY_PROVENANCE_INVALID")
    if _control_bytes(plan) != raw or plan.get("contract") != RECOVERY_PLAN_CONTRACT:
        raise ContractError("RECOVERY_PROVENANCE_INVALID", "recovery plan artifact is invalid")
    actual = _artifact_sha256(raw)
    if actual != expected_sha256:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "recovery plan digest differs from completion")
    return path.relative_to(root).as_posix(), plan, raw, actual


def _verify_recovered_provenance(root: Path, pems_sha: str, cove_sha: str) -> tuple[list[str], dict[str, str]]:
    if not _generation_dirs(root):
        raise ContractError("RECOVERY_PROVENANCE_MISSING", "no recovery generation evidence is present")
    matches = _completion_candidates(root, pems_sha, cove_sha)
    if not matches:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "no immutable completion record binds the current pair")
    if len(matches) != 1:
        raise ContractError("RECOVERY_PROVENANCE_CONFLICT", "multiple completion records bind the current pair")

    completion_path, completion, completion_raw = matches[0]
    generation_dir = completion_path.parent
    generation = generation_dir.name
    completion_fields = {
        "contract", "project_id", "generation", "recovery_plan_sha256",
        "root_approval_path", "root_approval_sha256",
        "preserved_evidence_inventory_path", "preserved_evidence_inventory_sha256",
        "equivalence_proof_path", "equivalence_proof_sha256",
        "prestate", "poststate", "recipe_id", "recipe_implementation_identity",
        "implementation_closure", "recovery_contract_identity", "r14_v2_contract_identity",
        "provenance_class", "journal_path", "journal_sha256",
    }
    if set(completion) != completion_fields:
        raise ContractError("RECOVERY_PROVENANCE_INVALID", "completion fields do not match G6 contract realization")
    if completion["generation"] != generation or completion["provenance_class"] != RECOVERED_CLASS:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "completion generation/provenance class mismatch")
    if completion["recipe_id"] != RECOVERY_RECIPE:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "completion recipe is outside V1")
    poststate = completion.get("poststate")
    if not isinstance(poststate, dict) or poststate != {"pems_sha256": pems_sha, "cove_sha256": cove_sha}:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "completion poststate does not match current pair")

    plan_path, plan, plan_raw, plan_sha = _find_plan(root, generation_dir, completion["recovery_plan_sha256"])
    plan_required = {
        "contract", "project_id", "generation", "canonical_paths", "prestate",
        "preserved_evidence_inventory_sha256", "mode", "recipe_id",
        "recipe_implementation_identity", "candidate", "equivalence_proof_sha256",
        "implementation_closure", "runtime_identity", "recovery_contract_identity",
        "r14_v2_contract_identity", "expected_barrier_identity", "expected_terminal_provenance_class",
    }
    if set(plan) != plan_required:
        raise ContractError("RECOVERY_PROVENANCE_INVALID", "recovery plan fields do not match G4 contract realization")
    if plan["generation"] != generation or plan["mode"] != "A" or plan["recipe_id"] != RECOVERY_RECIPE:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "recovery plan generation/mode/recipe mismatch")
    if plan["project_id"] != completion["project_id"]:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "recovery plan project identity mismatch")
    if plan.get("candidate") != poststate:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "recovery plan candidate hashes do not match current pair")
    if plan.get("prestate") != completion.get("prestate"):
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "completion prestate differs from plan")
    if plan["expected_terminal_provenance_class"] != RECOVERED_CLASS:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "recovery plan terminal provenance class mismatch")
    for field in (
        "recipe_id", "recipe_implementation_identity", "implementation_closure",
        "recovery_contract_identity", "r14_v2_contract_identity",
    ):
        if completion[field] != plan[field]:
            raise ContractError("RECOVERY_PROVENANCE_MISMATCH", f"completion/plan binding mismatch: {field}")
    if completion["preserved_evidence_inventory_sha256"] != plan["preserved_evidence_inventory_sha256"]:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "preserved inventory digest differs from plan")
    if completion["equivalence_proof_sha256"] != plan["equivalence_proof_sha256"]:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "equivalence proof digest differs from plan")

    approval, approval_raw, approval_sha = _load_control_artifact(
        root, completion["root_approval_path"], RECOVERY_APPROVAL_CONTRACT, "RECOVERY_PROVENANCE_INVALID"
    )
    if approval_sha != completion["root_approval_sha256"]:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "root approval digest mismatch")
    approval_fields = {"contract", "project_id", "generation", "recovery_plan_sha256", "protected_root_id", "authentication"}
    if set(approval) != approval_fields:
        raise ContractError("RECOVERY_PROVENANCE_INVALID", "root approval fields do not match G5 contract realization")
    authentication = approval.get("authentication")
    if not isinstance(authentication, dict) or not {"method", "confirmation"}.issubset(authentication):
        raise ContractError("RECOVERY_PROVENANCE_INVALID", "root approval authentication is invalid")
    if set(authentication) - {"method", "confirmation", "evidence"}:
        raise ContractError("RECOVERY_PROVENANCE_INVALID", "root approval authentication contains unsupported fields")
    if authentication.get("method") != "human_confirmation" or authentication.get("confirmation") != RECOVERY_CONFIRMATION:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "root approval confirmation mismatch")
    if approval["project_id"] != completion["project_id"] or approval["generation"] != generation or approval["recovery_plan_sha256"] != plan_sha:
        raise ContractError("RECOVERY_PROVENANCE_MISMATCH", "root approval is not bound to completion plan")

    paths = [completion_path.relative_to(root).as_posix(), plan_path]
    digests = {
        paths[0]: _artifact_digest(completion_raw),
        plan_path: _artifact_digest(plan_raw),
    }
    for path_field, digest_field in (
        ("root_approval_path", "root_approval_sha256"),
        ("preserved_evidence_inventory_path", "preserved_evidence_inventory_sha256"),
        ("equivalence_proof_path", "equivalence_proof_sha256"),
        ("journal_path", "journal_sha256"),
    ):
        rel = completion[path_field]
        _, raw, actual_sha = _load_control_artifact(root, rel, None, "RECOVERY_PROVENANCE_INVALID")
        if actual_sha != completion[digest_field]:
            raise ContractError("RECOVERY_PROVENANCE_MISMATCH", f"recovery artifact digest mismatch: {rel}")
        if rel not in paths:
            paths.append(rel)
        digests[rel] = _artifact_digest(raw)
    return paths, digests


def verify_storage_snapshot(project_root: Path, package_root: Path, snapshot: CanonicalPairSnapshot) -> dict[str, Any]:
    """Verify one lock-bound snapshot without acquiring another canonical lock.

    Recovery execution may call this only with the exclusive-session internal
    verification snapshot while the active barrier is intentionally present.
    Ordinary callers should use ``verify_storage``.
    """
    try:
        root = project_root.resolve()
        package = package_root.resolve()
        if snapshot.state == "ABSENT":
            return _result("FAIL", "NO_ADMITTED_STATE")
        if snapshot.state == "INCOMPLETE":
            return _result("FAIL", "INCOMPLETE_CANONICAL_PAIR")
        if snapshot.state != "PRESENT" or snapshot.pems_bytes is None or snapshot.cove_bytes is None:
            return _result("FAIL", "CANONICAL_PATH_CONFLICT", "unsupported canonical snapshot state")

        pems_bytes = snapshot.pems_bytes
        cove_bytes = snapshot.cove_bytes
        pems = _parse_json_bytes(pems_bytes, "INVALID_PEMS_JSON")
        try:
            normalized = normalize_pems(pems)
        except ContractError as exc:
            return _result("FAIL", exc.code, exc.detail)
        if pems_bytes != jcs(normalized):
            return _result("FAIL", "NONCANONICAL_PEMS_BYTES")

        validator_module, schema_validator = _load_package_validator(package)
        errors = sorted(schema_validator.iter_errors(normalized), key=lambda err: list(err.path))
        if errors:
            rendered = "; ".join(f"{list(err.path)}: {err.message}" for err in errors[:20])
            return _result("FAIL", "PEMS_SCHEMA_INVALID", rendered)
        try:
            integrity = validator_module.validate_candidate_document(normalized, schema_validator)
        except Exception as exc:
            return _result("FAIL", "PEMS_INTEGRITY_INVALID", str(exc))

        cove = _parse_json_bytes(cove_bytes, "INVALID_COVE_JSON")
        if cove_bytes != jcs(cove):
            return _result("FAIL", "NONCANONICAL_COVE_BYTES")
        expected_cove = encode_cove(normalized)
        if cove != expected_cove:
            return _result("FAIL", "COVE_MISMATCH")
        if cove.get("c") != COVE or cove.get("p") != PROFILE or cove.get("s") != SERIALIZER:
            return _result("FAIL", "COVE_MISMATCH", "unsupported COVE/PEMS/serializer tuple")
        try:
            decoded = _decode(cove["x"], cove["d"], cove["h"])
        except Exception as exc:
            return _result("FAIL", "COVE_ROUNDTRIP_FAILED", str(exc))
        if decoded != normalized:
            return _result("FAIL", "COVE_ROUNDTRIP_FAILED")

        pems_sha = snapshot.pems_sha256 or sha256_bytes(pems_bytes)
        cove_sha = snapshot.cove_sha256 or sha256_bytes(cove_bytes)
        receipt_paths, receipt_digests, admission_failure = _scan_receipts(root, pems_sha, cove_sha)
        if receipt_paths:
            return _result(
                "PASS", ADMITTED_CLASS,
                provenance_class=ADMITTED_CLASS,
                pems_sha256=pems_sha,
                cove_sha256=cove_sha,
                cove_tuple=f"{COVE}|{PROFILE}|{SERIALIZER}",
                provenance_paths=receipt_paths,
                provenance_digests=receipt_digests,
                receipt_paths=receipt_paths,
                pems_integrity=integrity,
            )

        if _generation_dirs(root):
            paths, digests = _verify_recovered_provenance(root, pems_sha, cove_sha)
            return _result(
                "PASS", RECOVERED_CLASS,
                provenance_class=RECOVERED_CLASS,
                pems_sha256=pems_sha,
                cove_sha256=cove_sha,
                cove_tuple=f"{COVE}|{PROFILE}|{SERIALIZER}",
                provenance_paths=paths,
                provenance_digests=digests,
                completion_path=paths[0],
                completion_digest=digests[paths[0]],
                pems_integrity=integrity,
            )
        return _result("FAIL", admission_failure or "ADMISSION_RECEIPT_MISSING")
    except ContractError as exc:
        return _result("FAIL", exc.code, exc.detail)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _result("FAIL", "STORAGE_VERIFICATION_ERROR", str(exc))


def verify_storage(project_root: Path, package_root: Path | None = None) -> dict[str, Any]:
    try:
        root = project_root.resolve()
        package = (package_root or Path(__file__).resolve().parents[1]).resolve()
        with shared_canonical_store(root) as store:
            snapshot = store.snapshot()
        return verify_storage_snapshot(root, package, snapshot)
    except ContractError as exc:
        return _result("FAIL", exc.code, exc.detail)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _result("FAIL", "STORAGE_VERIFICATION_ERROR", str(exc))


if __name__ == "__main__":
    print(json.dumps(_result("FAIL", "LIBRARY_PRIMITIVE", "R14 is exposed as a deterministic function; public ril UX is not implemented yet"), sort_keys=True, separators=(",", ":")))
