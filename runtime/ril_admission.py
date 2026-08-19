#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

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
    value: dict[str, Any] = {"contract": RESULT_CONTRACT, "status": status, "outcome": outcome}
    if detail:
        value["detail"] = detail
    value.update(extra)
    return value


def jcs(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("NON_CANONICAL_VALUE", str(exc)) from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_pems(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict) or document.get("semantic") != PROFILE:
        raise ContractError("INVALID_PEMS", "canonical document must use pems/2")
    if not isinstance(document.get("records"), list) or not isinstance(document.get("relations"), list):
        raise ContractError("INVALID_PEMS", "records and relations must be arrays")
    normalized = copy.deepcopy(document)
    try:
        normalized["records"] = sorted(normalized["records"], key=lambda item: item["id"])
        normalized["relations"] = sorted(normalized["relations"], key=lambda item: item["id"])
    except Exception as exc:
        raise ContractError("INVALID_PEMS", "all records and relations require stable IDs") from exc
    return normalized


def _validate_graph(document: dict[str, Any]) -> None:
    records = document["records"]
    relations = document["relations"]
    record_ids = [item.get("id") for item in records]
    relation_ids = [item.get("id") for item in relations]
    if any(not isinstance(value, str) or not value for value in record_ids + relation_ids):
        raise ContractError("INVALID_PEMS", "record/relation IDs must be non-empty strings")
    if len(record_ids) != len(set(record_ids)):
        raise ContractError("DUPLICATE_RECORD_ID", "record IDs must be unique")
    if len(relation_ids) != len(set(relation_ids)):
        raise ContractError("DUPLICATE_RELATION_ID", "relation IDs must be unique")
    known = set(record_ids)
    for relation in relations:
        if relation.get("from") not in known or relation.get("to") not in known:
            raise ContractError("DANGLING_RELATION", str(relation.get("id")))
        if relation.get("from") == relation.get("to"):
            raise ContractError("SELF_RELATION", str(relation.get("id")))


def _strings(value: Any, out: set[str]) -> None:
    if isinstance(value, str): out.add(value)
    elif isinstance(value, list):
        for item in value: _strings(item, out)
    elif isinstance(value, dict):
        for key, item in value.items(): out.add(key); _strings(item, out)


def _shapes(value: Any, index: dict[str, int], out: set[tuple[int, ...]]) -> None:
    if isinstance(value, list):
        for item in value: _shapes(item, index, out)
    elif isinstance(value, dict):
        out.add(tuple(sorted(index[key] for key in value)))
        for item in value.values(): _shapes(item, index, out)


def _encode(value: Any, index: dict[str, int], shape_index: dict[tuple[int, ...], int]) -> Any:
    if isinstance(value, str): return [0, index[value]]
    if isinstance(value, list): return [1, *[_encode(item, index, shape_index) for item in value]]
    if isinstance(value, dict):
        shape = tuple(sorted(index[key] for key in value))
        keys = sorted(value, key=lambda key: index[key])
        return [2, shape_index[shape], *[_encode(value[key], index, shape_index) for key in keys]]
    return value


def _decode(value: Any, dictionary: list[str], shapes: list[list[int]]) -> Any:
    if not isinstance(value, list): return value
    if value[0] == 0: return dictionary[value[1]]
    if value[0] == 1: return [_decode(item, dictionary, shapes) for item in value[1:]]
    if value[0] == 2:
        keys = [dictionary[i] for i in shapes[value[1]]]
        vals = value[2:]
        if len(keys) != len(vals): raise ContractError("COVE_ROUNDTRIP_FAILED", "shape arity mismatch")
        return {key: _decode(item, dictionary, shapes) for key, item in zip(keys, vals)}
    raise ContractError("COVE_ROUNDTRIP_FAILED", "unknown COVE tag")


def encode_cove(document: dict[str, Any]) -> dict[str, Any]:
    strings: set[str] = set(); _strings(document, strings)
    dictionary = sorted(strings, key=lambda item: item.encode("utf-8")); index = {v: i for i, v in enumerate(dictionary)}
    shapes: set[tuple[int, ...]] = set(); _shapes(document, index, shapes)
    ordered = sorted(shapes); shape_index = {v: i for i, v in enumerate(ordered)}
    return {"c": COVE, "p": PROFILE, "s": SERIALIZER, "d": dictionary, "h": [list(s) for s in ordered], "x": _encode(document, index, shape_index)}


def validate_plan(plan: Any) -> dict[str, Any]:
    required = {"contract", "expected_base_sha256", "reuse_record_ids", "record_updates", "new_records", "new_relations"}
    if not isinstance(plan, dict) or set(plan) != required or plan.get("contract") != PLAN_CONTRACT:
        raise ContractError("INVALID_ADMISSION_PLAN", "plan fields/contract do not match rgp-pems2-admission-transaction/2")
    if not isinstance(plan["expected_base_sha256"], str) or len(plan["expected_base_sha256"]) != 64:
        raise ContractError("INVALID_ADMISSION_PLAN", "expected_base_sha256 is invalid")
    for key in ("reuse_record_ids", "record_updates", "new_records", "new_relations"):
        if not isinstance(plan[key], list): raise ContractError("INVALID_ADMISSION_PLAN", f"{key} must be an array")
    return copy.deepcopy(plan)


def apply_plan(base: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    base = normalize_pems(base); plan = validate_plan(plan)
    if sha256_bytes(jcs(base)) != plan["expected_base_sha256"]:
        raise ContractError("BASE_MISMATCH", "admission plan was not built against current canonical PEMS")
    records = {r["id"]: r for r in base["records"]}; relations = {r["id"]: r for r in base["relations"]}
    reuse = plan["reuse_record_ids"]
    if len(reuse) != len(set(reuse)): raise ContractError("INVALID_ADMISSION_PLAN", "duplicate reuse_record_ids")
    for rid in reuse:
        if rid not in records: raise ContractError("REUSED_RECORD_NOT_FOUND", str(rid))
    replacements: dict[str, dict[str, Any]] = {}; update_ids: set[str] = set()
    for update in plan["record_updates"]:
        if not isinstance(update, dict) or set(update) != {"record_id", "expected_before_sha256", "replacement"}:
            raise ContractError("INVALID_RECORD_UPDATE", "record update fields do not match contract")
        rid = update["record_id"]
        if rid in update_ids or rid not in records or rid not in reuse: raise ContractError("INVALID_RECORD_UPDATE", str(rid))
        replacement = update["replacement"]
        if not isinstance(replacement, dict) or replacement.get("id") != rid or replacement.get("kind") != records[rid].get("kind"):
            raise ContractError("INVALID_RECORD_UPDATE", str(rid))
        if sha256_bytes(jcs(records[rid])) != update["expected_before_sha256"]:
            raise ContractError("RECORD_BEFORE_MISMATCH", str(rid))
        update_ids.add(rid); replacements[rid] = copy.deepcopy(replacement)
    new_records: list[dict[str, Any]] = []; seen_r: set[str] = set()
    for record in plan["new_records"]:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"]: raise ContractError("INVALID_NEW_RECORD", "new record requires id")
        rid = record["id"]
        if rid in records or rid in seen_r: raise ContractError("RECORD_ID_COLLISION", rid)
        seen_r.add(rid); new_records.append(copy.deepcopy(record))
    new_relations: list[dict[str, Any]] = []; seen_l: set[str] = set()
    for relation in plan["new_relations"]:
        if not isinstance(relation, dict) or not isinstance(relation.get("id"), str) or not relation["id"]: raise ContractError("INVALID_NEW_RELATION", "new relation requires id")
        rid = relation["id"]
        if rid in relations or rid in seen_l: raise ContractError("RELATION_ID_COLLISION", rid)
        seen_l.add(rid); new_relations.append(copy.deepcopy(relation))
    candidate = copy.deepcopy(base)
    candidate["records"] = [copy.deepcopy(replacements.get(r["id"], r)) for r in base["records"]] + new_records
    candidate["relations"] = copy.deepcopy(base["relations"]) + new_relations
    candidate = normalize_pems(candidate); _validate_graph(candidate)
    return candidate


def _safe_regular(path: Path) -> None:
    if path.exists() and (path.is_symlink() or not path.is_file()): raise ContractError("CANONICAL_PATH_CONFLICT", str(path))
    if path.parent.exists() and (path.parent.is_symlink() or not path.parent.is_dir()): raise ContractError("CANONICAL_PATH_CONFLICT", str(path.parent))


def _replace(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); _safe_regular(path)
    temp = path.with_name(path.name + ".admit.tmp")
    if temp.exists() or temp.is_symlink(): raise ContractError("CANONICAL_PATH_CONFLICT", str(temp))
    try:
        with open(temp, "xb") as h: h.write(data); h.flush(); os.fsync(h.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists() and not temp.is_symlink(): temp.unlink()


def _persist(path: Path, value: dict[str, Any], code: str) -> None:
    data = canonical_json_bytes(value)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data: raise ContractError(code, str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "xb") as h: h.write(data); h.flush(); os.fsync(h.fileno())
    except FileExistsError:
        if path.is_symlink() or path.read_bytes() != data: raise ContractError(code, str(path))


def _load_disposition(project_root: Path, disposition_path: Path) -> tuple[dict[str, Any], Path]:
    root = project_root.resolve(); base = (root / "project-knowledge" / "reconciliation" / "dispositions").resolve(strict=False)
    raw = disposition_path if disposition_path.is_absolute() else root / disposition_path
    if raw.is_symlink(): raise ContractError("INVALID_DISPOSITION_PATH", str(disposition_path))
    try: path = raw.resolve(strict=True); path.relative_to(base)
    except (OSError, ValueError) as exc: raise ContractError("INVALID_DISPOSITION_PATH", str(disposition_path)) from exc
    value = load_json(path)
    if not isinstance(value, dict) or value.get("contract") != DISPOSITION_CONTRACT: raise ContractError("INVALID_DISPOSITION", "unsupported reconciliation disposition")
    assessment = value.get("assessment", {})
    if assessment.get("semantic_status") != "COMPATIBLE" or assessment.get("admission_recommendation") != "RECOMMEND":
        raise ContractError("ADMISSION_NOT_RECOMMENDED", "reconciliation disposition does not recommend admission")
    candidate = load_json(root / value["candidate_path"])
    if digest(candidate) != value.get("candidate_digest"): raise ContractError("CANDIDATE_CHANGED", "candidate no longer matches reconciled identity")
    return value, path


def admit(project_root: Path, disposition_path: Path, activation: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    try:
        disposition, disposition_file = _load_disposition(project_root, disposition_path)
        activation_result = validate_activation(project_root, SCOPE, activation)
        if activation_result.get("status") != "PASS": return _result("FAIL", activation_result.get("outcome", "ACTIVATION_REJECTED"), activation_result.get("detail"))
        canonical = project_root / "project-knowledge" / "canonical"; pems_path = canonical / "pems2.jcs.json"; cove_path = canonical / "cove1.jcs.json"
        _safe_regular(pems_path); _safe_regular(cove_path)
        base = normalize_pems(json.loads(pems_path.read_text("utf-8"))) if pems_path.exists() else copy.deepcopy(EMPTY_PEMS)
        candidate = apply_plan(base, plan); pems_bytes = jcs(candidate); cove = encode_cove(candidate); cove_bytes = jcs(cove)
        if _decode(cove["x"], cove["d"], cove["h"]) != candidate: raise ContractError("COVE_ROUNDTRIP_FAILED", "COVE does not decode to admitted PEMS")
        admission = project_root / "project-knowledge" / "admission"; candidate_hex = disposition["candidate_digest"].split(":", 1)[1]
        activation_digest = digest(activation); plan_digest = digest(plan)
        receipt = {"contract": RECEIPT_CONTRACT, "candidate_digest": disposition["candidate_digest"], "disposition_digest": digest(disposition), "activation_digest": activation_digest, "plan_digest": plan_digest, "role_id": activation_result["role_id"], "invocation_id": activation_result["invocation_id"], "base_pems_sha256": sha256_bytes(jcs(base)), "admitted_pems_sha256": sha256_bytes(pems_bytes), "admitted_cove_sha256": sha256_bytes(cove_bytes)}
        receipt_path = admission / "receipts" / f"{candidate_hex}.json"
        if receipt_path.exists():
            existing = load_json(receipt_path)
            if existing != receipt: raise ContractError("ADMISSION_CONFLICT", "candidate already has a different admission receipt")
            if not pems_path.exists() or pems_path.read_bytes() != pems_bytes or not cove_path.exists() or cove_path.read_bytes() != cove_bytes: raise ContractError("CANONICAL_STATE_CONFLICT", "receipt exists but canonical state no longer matches")
            return _result("PASS", "NO_CHANGE", receipt_path=receipt_path.relative_to(project_root).as_posix(), admitted_pems_sha256=receipt["admitted_pems_sha256"])
        _persist(admission / "activation-evidence" / f"{activation_digest.split(':',1)[1]}.json", activation, "ACTIVATION_EVIDENCE_CONFLICT")
        _persist(admission / "plans" / f"{plan_digest.split(':',1)[1]}.json", plan, "ADMISSION_PLAN_CONFLICT")
        _replace(pems_path, pems_bytes); _replace(cove_path, cove_bytes); _persist(receipt_path, receipt, "ADMISSION_CONFLICT")
        return _result("PASS", "ADMITTED", receipt_path=receipt_path.relative_to(project_root).as_posix(), pems_path=pems_path.relative_to(project_root).as_posix(), cove_path=cove_path.relative_to(project_root).as_posix(), admitted_pems_sha256=receipt["admitted_pems_sha256"], admitted_cove_sha256=receipt["admitted_cove_sha256"])
    except (ContractError, json.JSONDecodeError, OSError) as exc:
        if isinstance(exc, ContractError): return _result("FAIL", exc.code, exc.detail)
        return _result("FAIL", "ADMISSION_IO_ERROR", str(exc))


if __name__ == "__main__":
    print(json.dumps(_result("FAIL", "LIBRARY_PRIMITIVE", "R13 is exposed as deterministic functions; public ril UX is not implemented yet"), sort_keys=True, separators=(",", ":")))
