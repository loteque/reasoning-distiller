#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from rd_bootstrap import validate_project_config
from ril_activation import validate_activation
from ril_mutation import ContractError, canonical_json_bytes, digest, load_json
from ril_reconciliation import DISPOSITION_CONTRACT

RESULT_CONTRACT = "reasoning-distiller-admission-result/1"
RECEIPT_CONTRACT = "reasoning-distiller-admission-receipt/1"
PLAN_CONTRACT = "rgp-pems2-admission-transaction/2"
PROFILE = "pems/2"
COVE = "cove/1"
SERIALIZER = "jcs/1"
SCOPE = "admission"
EMPTY_PEMS = {"semantic": PROFILE, "records": [], "relations": []}


def _result(status: str, outcome: str, detail: str | None = None, **extra: Any) -> dict[str, Any]:
    value = {"contract": RESULT_CONTRACT, "status": status, "outcome": outcome}
    if detail:
        value["detail"] = detail
    value.update(extra)
    return value


def jcs(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    except (TypeError, ValueError) as exc:
        raise ContractError("NON_CANONICAL_VALUE", str(exc)) from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_pems(document: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(document, dict)
        or document.get("semantic") != PROFILE
        or not isinstance(document.get("records"), list)
        or not isinstance(document.get("relations"), list)
    ):
        raise ContractError("INVALID_PEMS", "document must be pems/2 with records/relations arrays")
    normalized = copy.deepcopy(document)
    try:
        normalized["records"] = sorted(normalized["records"], key=lambda record: record["id"])
        normalized["relations"] = sorted(normalized["relations"], key=lambda relation: relation["id"])
    except Exception as exc:
        raise ContractError("INVALID_PEMS", "all records and relations require IDs") from exc
    return normalized


def first_admission_base(project_root: Path) -> dict[str, Any]:
    """Return the exact schema-valid project-seeded base used for first admission."""
    config_path = project_root / "project-knowledge/project.json"
    if not config_path.exists() or config_path.is_symlink() or not config_path.is_file():
        raise ContractError("PROJECT_IDENTITY_REQUIRED", "project-knowledge/project.json with explicit project identity is required")
    config = load_json(config_path)
    if not validate_project_config(config):
        raise ContractError("PROJECT_IDENTITY_REQUIRED", "reasoning-distiller-project/2 identity is required before first admission")
    project = config["project"]
    return normalize_pems(
        {
            "semantic": PROFILE,
            "project_id": project["id"],
            "records": [
                {
                    "id": project["id"],
                    "kind": "project",
                    "lifecycle": "current",
                    "data": {
                        "name": project["name"],
                        "repository": project["repository"],
                        "summary": project["summary"],
                    },
                }
            ],
            "relations": [],
        }
    )


def _validate_graph(document: dict[str, Any]) -> None:
    record_ids = [record.get("id") for record in document["records"]]
    relation_ids = [relation.get("id") for relation in document["relations"]]
    if any(not isinstance(item, str) or not item for item in record_ids + relation_ids):
        raise ContractError("INVALID_PEMS", "IDs must be non-empty strings")
    if len(record_ids) != len(set(record_ids)):
        raise ContractError("DUPLICATE_RECORD_ID", "record IDs must be unique")
    if len(relation_ids) != len(set(relation_ids)):
        raise ContractError("DUPLICATE_RELATION_ID", "relation IDs must be unique")
    known = set(record_ids)
    for relation in document["relations"]:
        if relation.get("from") not in known or relation.get("to") not in known:
            raise ContractError("DANGLING_RELATION", str(relation.get("id")))
        if relation.get("from") == relation.get("to"):
            raise ContractError("SELF_RELATION", str(relation.get("id")))


def _strings(value: Any, out: set[str]) -> None:
    if isinstance(value, str):
        out.add(value)
    elif isinstance(value, list):
        for item in value:
            _strings(item, out)
    elif isinstance(value, dict):
        for key, item in value.items():
            out.add(key)
            _strings(item, out)


def _shapes(value: Any, index: dict[str, int], out: set[tuple[int, ...]]) -> None:
    if isinstance(value, list):
        for item in value:
            _shapes(item, index, out)
    elif isinstance(value, dict):
        out.add(tuple(sorted(index[key] for key in value)))
        for item in value.values():
            _shapes(item, index, out)


def _encode(value: Any, index: dict[str, int], shape_index: dict[tuple[int, ...], int]) -> Any:
    if isinstance(value, str):
        return [0, index[value]]
    if isinstance(value, list):
        return [1, *[_encode(item, index, shape_index) for item in value]]
    if isinstance(value, dict):
        shape = tuple(sorted(index[key] for key in value))
        keys = sorted(value, key=lambda key: index[key])
        return [2, shape_index[shape], *[_encode(value[key], index, shape_index) for key in keys]]
    return value


def _decode(value: Any, dictionary: list[str], shapes: list[list[int]]) -> Any:
    if not isinstance(value, list):
        return value
    if value[0] == 0:
        return dictionary[value[1]]
    if value[0] == 1:
        return [_decode(item, dictionary, shapes) for item in value[1:]]
    if value[0] == 2:
        keys = [dictionary[index] for index in shapes[value[1]]]
        values = value[2:]
        if len(keys) != len(values):
            raise ContractError("COVE_ROUNDTRIP_FAILED", "shape arity mismatch")
        return {key: _decode(item, dictionary, shapes) for key, item in zip(keys, values)}
    raise ContractError("COVE_ROUNDTRIP_FAILED", "unknown tag")


def encode_cove(document: dict[str, Any]) -> dict[str, Any]:
    strings: set[str] = set()
    _strings(document, strings)
    dictionary = sorted(strings, key=lambda item: item.encode())
    index = {item: number for number, item in enumerate(dictionary)}
    shapes: set[tuple[int, ...]] = set()
    _shapes(document, index, shapes)
    ordered = sorted(shapes)
    shape_index = {shape: number for number, shape in enumerate(ordered)}
    return {
        "c": COVE,
        "p": PROFILE,
        "s": SERIALIZER,
        "d": dictionary,
        "h": [list(shape) for shape in ordered],
        "x": _encode(document, index, shape_index),
    }


def validate_plan(plan: Any) -> dict[str, Any]:
    required = {"contract", "expected_base_sha256", "reuse_record_ids", "record_updates", "new_records", "new_relations"}
    if not isinstance(plan, dict) or set(plan) != required or plan.get("contract") != PLAN_CONTRACT:
        raise ContractError("INVALID_ADMISSION_PLAN", "plan contract/fields invalid")
    if not isinstance(plan["expected_base_sha256"], str) or len(plan["expected_base_sha256"]) != 64:
        raise ContractError("INVALID_ADMISSION_PLAN", "expected_base_sha256 invalid")
    for key in ("reuse_record_ids", "record_updates", "new_records", "new_relations"):
        if not isinstance(plan[key], list):
            raise ContractError("INVALID_ADMISSION_PLAN", f"{key} must be array")
    return copy.deepcopy(plan)


def apply_plan(base: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    base = normalize_pems(base)
    plan = validate_plan(plan)
    if sha256_bytes(jcs(base)) != plan["expected_base_sha256"]:
        raise ContractError("BASE_MISMATCH", "plan not built against current canonical PEMS")
    records = {record["id"]: record for record in base["records"]}
    relations = {relation["id"]: relation for relation in base["relations"]}
    reuse = plan["reuse_record_ids"]
    if len(reuse) != len(set(reuse)):
        raise ContractError("INVALID_ADMISSION_PLAN", "duplicate reuse IDs")
    for record_id in reuse:
        if record_id not in records:
            raise ContractError("REUSED_RECORD_NOT_FOUND", str(record_id))

    replacements: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for update in plan["record_updates"]:
        if not isinstance(update, dict) or set(update) != {"record_id", "expected_before_sha256", "replacement"}:
            raise ContractError("INVALID_RECORD_UPDATE", "invalid update shape")
        record_id = update["record_id"]
        replacement = update["replacement"]
        if (
            record_id in seen
            or record_id not in records
            or record_id not in reuse
            or not isinstance(replacement, dict)
            or replacement.get("id") != record_id
            or replacement.get("kind") != records[record_id].get("kind")
        ):
            raise ContractError("INVALID_RECORD_UPDATE", str(record_id))
        if sha256_bytes(jcs(records[record_id])) != update["expected_before_sha256"]:
            raise ContractError("RECORD_BEFORE_MISMATCH", str(record_id))
        seen.add(record_id)
        replacements[record_id] = copy.deepcopy(replacement)

    new_records: list[dict[str, Any]] = []
    new_record_ids: set[str] = set()
    for record in plan["new_records"]:
        record_id = record.get("id") if isinstance(record, dict) else None
        if not isinstance(record_id, str) or not record_id:
            raise ContractError("INVALID_NEW_RECORD", "id required")
        if record_id in records or record_id in new_record_ids:
            raise ContractError("RECORD_ID_COLLISION", record_id)
        new_record_ids.add(record_id)
        new_records.append(copy.deepcopy(record))

    new_relations: list[dict[str, Any]] = []
    new_relation_ids: set[str] = set()
    for relation in plan["new_relations"]:
        relation_id = relation.get("id") if isinstance(relation, dict) else None
        if not isinstance(relation_id, str) or not relation_id:
            raise ContractError("INVALID_NEW_RELATION", "id required")
        if relation_id in relations or relation_id in new_relation_ids:
            raise ContractError("RELATION_ID_COLLISION", relation_id)
        new_relation_ids.add(relation_id)
        new_relations.append(copy.deepcopy(relation))

    out = copy.deepcopy(base)
    out["records"] = [copy.deepcopy(replacements.get(record["id"], record)) for record in base["records"]] + new_records
    out["relations"] = copy.deepcopy(base["relations"]) + new_relations
    out = normalize_pems(out)
    _validate_graph(out)
    return out


def _safe(path: Path) -> None:
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise ContractError("CANONICAL_PATH_CONFLICT", str(path))
    if path.parent.exists() and (path.parent.is_symlink() or not path.parent.is_dir()):
        raise ContractError("CANONICAL_PATH_CONFLICT", str(path.parent))


def _replace(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _safe(path)
    tmp = path.with_name(path.name + ".admit.tmp")
    if tmp.exists() or tmp.is_symlink():
        raise ContractError("CANONICAL_PATH_CONFLICT", str(tmp))
    try:
        with open(tmp, "xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists() and not tmp.is_symlink():
            tmp.unlink()


def _persist(path: Path, value: dict[str, Any], code: str) -> None:
    data = canonical_json_bytes(value)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ContractError(code, str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        if path.is_symlink() or path.read_bytes() != data:
            raise ContractError(code, str(path))


def _load_disposition(root: Path, path_arg: Path) -> dict[str, Any]:
    base = (root.resolve() / "project-knowledge/reconciliation/dispositions").resolve(strict=False)
    raw = path_arg if path_arg.is_absolute() else root / path_arg
    if raw.is_symlink():
        raise ContractError("INVALID_DISPOSITION_PATH", str(path_arg))
    try:
        path = raw.resolve(strict=True)
        path.relative_to(base)
    except (OSError, ValueError) as exc:
        raise ContractError("INVALID_DISPOSITION_PATH", str(path_arg)) from exc
    value = load_json(path)
    if not isinstance(value, dict) or value.get("contract") != DISPOSITION_CONTRACT:
        raise ContractError("INVALID_DISPOSITION", "unsupported disposition")
    assessment = value.get("assessment", {})
    if assessment.get("semantic_status") != "COMPATIBLE" or assessment.get("admission_recommendation") != "RECOMMEND":
        raise ContractError("ADMISSION_NOT_RECOMMENDED", "disposition does not recommend admission")
    candidate = load_json(root / value["candidate_path"])
    if digest(candidate) != value.get("candidate_digest"):
        raise ContractError("CANDIDATE_CHANGED", "candidate no longer matches reconciled identity")
    return value


def admit(project_root: Path, disposition_path: Path, activation: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    try:
        disposition = _load_disposition(project_root, disposition_path)
        activation_result = validate_activation(project_root, SCOPE, activation)
        if activation_result.get("status") != "PASS":
            return _result("FAIL", activation_result.get("outcome", "ACTIVATION_REJECTED"), activation_result.get("detail"))
        validate_plan(plan)
        activation_digest = digest(activation)
        plan_digest = digest(plan)
        candidate_hex = disposition["candidate_digest"].split(":", 1)[1]
        admission = project_root / "project-knowledge/admission"
        receipt_path = admission / "receipts" / f"{candidate_hex}.json"
        canonical = project_root / "project-knowledge/canonical"
        pems_path = canonical / "pems2.jcs.json"
        cove_path = canonical / "cove1.jcs.json"
        _safe(pems_path)
        _safe(cove_path)

        # Idempotent retry is recognized from immutable evidence before stale-base evaluation.
        if receipt_path.exists():
            receipt = load_json(receipt_path)
            if (
                receipt.get("contract") != RECEIPT_CONTRACT
                or receipt.get("candidate_digest") != disposition["candidate_digest"]
                or receipt.get("disposition_digest") != digest(disposition)
                or receipt.get("activation_digest") != activation_digest
                or receipt.get("plan_digest") != plan_digest
            ):
                raise ContractError("ADMISSION_CONFLICT", "candidate already admitted under different evidence")
            if (
                not pems_path.exists()
                or not cove_path.exists()
                or sha256_bytes(pems_path.read_bytes()) != receipt.get("admitted_pems_sha256")
                or sha256_bytes(cove_path.read_bytes()) != receipt.get("admitted_cove_sha256")
            ):
                raise ContractError("CANONICAL_STATE_CONFLICT", "receipt does not match canonical bytes")
            return _result(
                "PASS",
                "NO_CHANGE",
                receipt_path=receipt_path.relative_to(project_root).as_posix(),
                admitted_pems_sha256=receipt["admitted_pems_sha256"],
            )

        base = normalize_pems(json.loads(pems_path.read_text("utf-8"))) if pems_path.exists() else first_admission_base(project_root)
        candidate = apply_plan(base, plan)
        pems_bytes = jcs(candidate)
        cove = encode_cove(candidate)
        cove_bytes = jcs(cove)
        if _decode(cove["x"], cove["d"], cove["h"]) != candidate:
            raise ContractError("COVE_ROUNDTRIP_FAILED", "COVE does not decode to PEMS")
        receipt = {
            "contract": RECEIPT_CONTRACT,
            "candidate_digest": disposition["candidate_digest"],
            "disposition_digest": digest(disposition),
            "activation_digest": activation_digest,
            "plan_digest": plan_digest,
            "role_id": activation_result["role_id"],
            "invocation_id": activation_result["invocation_id"],
            "base_pems_sha256": sha256_bytes(jcs(base)),
            "admitted_pems_sha256": sha256_bytes(pems_bytes),
            "admitted_cove_sha256": sha256_bytes(cove_bytes),
        }
        _persist(admission / "activation-evidence" / f"{activation_digest.split(':', 1)[1]}.json", activation, "ACTIVATION_EVIDENCE_CONFLICT")
        _persist(admission / "plans" / f"{plan_digest.split(':', 1)[1]}.json", plan, "ADMISSION_PLAN_CONFLICT")
        _replace(pems_path, pems_bytes)
        _replace(cove_path, cove_bytes)
        _persist(receipt_path, receipt, "ADMISSION_CONFLICT")
        return _result(
            "PASS",
            "ADMITTED",
            receipt_path=receipt_path.relative_to(project_root).as_posix(),
            pems_path=pems_path.relative_to(project_root).as_posix(),
            cove_path=cove_path.relative_to(project_root).as_posix(),
            admitted_pems_sha256=receipt["admitted_pems_sha256"],
            admitted_cove_sha256=receipt["admitted_cove_sha256"],
        )
    except (ContractError, json.JSONDecodeError, OSError) as exc:
        return _result("FAIL", exc.code, exc.detail) if isinstance(exc, ContractError) else _result("FAIL", "ADMISSION_IO_ERROR", str(exc))


if __name__ == "__main__":
    print(json.dumps(_result("FAIL", "LIBRARY_PRIMITIVE", "R13 is exposed as deterministic functions; public ril UX is not implemented yet"), sort_keys=True, separators=(",", ":")))
