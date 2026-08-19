#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ril_admission import COVE, PROFILE, RECEIPT_CONTRACT, SERIALIZER, _decode, encode_cove, jcs, normalize_pems, sha256_bytes
from ril_mutation import ContractError, load_json

RESULT_CONTRACT = "reasoning-distiller-storage-verification-result/1"


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


def _parse_json_bytes(path: Path, invalid_code: str) -> tuple[Any, bytes]:
    _ordinary_file(path, "CANONICAL_PATH_CONFLICT")
    data = path.read_bytes()
    try:
        return json.loads(data.decode("utf-8")), data
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(invalid_code, str(exc)) from exc


def verify_storage(project_root: Path, package_root: Path | None = None) -> dict[str, Any]:
    try:
        root = project_root.resolve()
        package = (package_root or Path(__file__).resolve().parents[1]).resolve()
        canonical = root / "project-knowledge" / "canonical"
        pems_path = canonical / "pems2.jcs.json"
        cove_path = canonical / "cove1.jcs.json"

        _ordinary_dir(canonical, "CANONICAL_PATH_CONFLICT")
        pems_exists = pems_path.exists() or pems_path.is_symlink()
        cove_exists = cove_path.exists() or cove_path.is_symlink()
        if not pems_exists and not cove_exists:
            return _result("FAIL", "NO_ADMITTED_STATE")
        if pems_exists != cove_exists:
            return _result("FAIL", "INCOMPLETE_CANONICAL_PAIR")

        pems, pems_bytes = _parse_json_bytes(pems_path, "INVALID_PEMS_JSON")
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

        cove, cove_bytes = _parse_json_bytes(cove_path, "INVALID_COVE_JSON")
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

        pems_sha = sha256_bytes(pems_bytes)
        cove_sha = sha256_bytes(cove_bytes)
        receipts_dir = root / "project-knowledge" / "admission" / "receipts"
        if not receipts_dir.exists():
            return _result("FAIL", "ADMISSION_RECEIPT_MISSING")
        _ordinary_dir(receipts_dir, "ADMISSION_RECEIPT_INVALID")
        receipt_paths: list[str] = []
        saw_receipt = False
        for receipt_path in sorted(receipts_dir.glob("*.json"), key=lambda p: p.name):
            saw_receipt = True
            if receipt_path.is_symlink() or not receipt_path.is_file():
                return _result("FAIL", "ADMISSION_RECEIPT_INVALID", str(receipt_path))
            try:
                receipt = load_json(receipt_path)
            except ContractError as exc:
                return _result("FAIL", "ADMISSION_RECEIPT_INVALID", exc.detail)
            if not isinstance(receipt, dict) or receipt.get("contract") != RECEIPT_CONTRACT:
                return _result("FAIL", "ADMISSION_RECEIPT_INVALID", str(receipt_path))
            if receipt.get("admitted_pems_sha256") == pems_sha and receipt.get("admitted_cove_sha256") == cove_sha:
                receipt_paths.append(receipt_path.relative_to(root).as_posix())
        if not saw_receipt:
            return _result("FAIL", "ADMISSION_RECEIPT_MISSING")
        if not receipt_paths:
            return _result("FAIL", "ADMISSION_RECEIPT_MISMATCH")

        return _result(
            "PASS",
            "VERIFIED",
            pems_sha256=pems_sha,
            cove_sha256=cove_sha,
            cove_tuple=f"{COVE}|{PROFILE}|{SERIALIZER}",
            receipt_paths=receipt_paths,
            pems_integrity=integrity,
        )
    except ContractError as exc:
        return _result("FAIL", exc.code, exc.detail)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _result("FAIL", "STORAGE_VERIFICATION_ERROR", str(exc))


if __name__ == "__main__":
    print(json.dumps(_result("FAIL", "LIBRARY_PRIMITIVE", "R14 is exposed as a deterministic function; public ril UX is not implemented yet"), sort_keys=True, separators=(",", ":")))
