#!/usr/bin/env python3
"""Apply a Steward-authorized RGP admission transaction to an exact PEMS/2 snapshot."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CONTRACT = "rgp-pems2-admission-transaction/1"
PROFILE = "pems/2"
COVE = "cove/1"
SERIALIZER = "jcs/1"
REASONING_RELATIONS = {"derived_from", "supports", "contradicts", "depends_on"}


def jcs(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def _shapes(value: Any, dictionary_index: dict[str, int], out: set[tuple[int, ...]]) -> None:
    if isinstance(value, list):
        for item in value:
            _shapes(item, dictionary_index, out)
    elif isinstance(value, dict):
        out.add(tuple(sorted(dictionary_index[key] for key in value)))
        for item in value.values():
            _shapes(item, dictionary_index, out)


def _encode(value: Any, dictionary_index: dict[str, int], shape_index: dict[tuple[int, ...], int]) -> Any:
    if isinstance(value, str):
        return [0, dictionary_index[value]]
    if isinstance(value, list):
        return [1, *[_encode(item, dictionary_index, shape_index) for item in value]]
    if isinstance(value, dict):
        shape = tuple(sorted(dictionary_index[key] for key in value))
        keys = sorted(value, key=lambda key: dictionary_index[key])
        return [2, shape_index[shape], *[_encode(value[key], dictionary_index, shape_index) for key in keys]]
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
            raise ValueError("COVE shape arity mismatch")
        return {key: _decode(item, dictionary, shapes) for key, item in zip(keys, values)}
    raise ValueError("unknown COVE tag")


def encode_cove(document: dict[str, Any]) -> dict[str, Any]:
    strings: set[str] = set()
    _strings(document, strings)
    dictionary = sorted(strings, key=lambda item: item.encode("utf-8"))
    dictionary_index = {item: index for index, item in enumerate(dictionary)}
    shapes: set[tuple[int, ...]] = set()
    _shapes(document, dictionary_index, shapes)
    ordered_shapes = sorted(shapes)
    shape_index = {shape: index for index, shape in enumerate(ordered_shapes)}
    return {
        "c": COVE,
        "p": PROFILE,
        "s": SERIALIZER,
        "d": dictionary,
        "h": [list(shape) for shape in ordered_shapes],
        "x": _encode(document, dictionary_index, shape_index),
    }


def normalize_pems(document: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(document)
    normalized["records"] = sorted(normalized.get("records", []), key=lambda item: item["id"])
    normalized["relations"] = sorted(normalized.get("relations", []), key=lambda item: item["id"])

    def sort_ids(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {
                    "about_ids",
                    "supersedes",
                    "superseded_by",
                    "primary",
                    "corroborating",
                    "context",
                    "untyped",
                } and isinstance(child, list) and all(isinstance(item, str) for item in child):
                    child.sort()
                else:
                    sort_ids(child)
        elif isinstance(value, list):
            for child in value:
                sort_ids(child)

    sort_ids(normalized)
    return normalized


def validate_plan(plan: Any) -> None:
    if not isinstance(plan, dict):
        raise ValueError("transaction plan must be an object")
    if plan.get("contract") != CONTRACT:
        raise ValueError(f"transaction plan contract must be {CONTRACT}")
    if not isinstance(plan.get("expected_base_sha256"), str) or not plan["expected_base_sha256"]:
        raise ValueError("expected_base_sha256 is required")
    for key in ("reuse_record_ids", "new_records", "new_relations"):
        if key not in plan or not isinstance(plan[key], list):
            raise ValueError(f"{key} must be an array")


def validate_graph_integrity(document: dict[str, Any]) -> dict[str, Any]:
    records = document["records"]
    relations = document["relations"]
    record_ids = [record["id"] for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("duplicate record IDs")
    relation_ids = [relation["id"] for relation in relations]
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError("duplicate relation IDs")
    record_set = set(record_ids)
    contradiction_pairs: set[tuple[str, str]] = set()
    derived_count = 0
    for relation in relations:
        source = relation["from"]
        target = relation["to"]
        kind = relation["kind"]
        if source not in record_set or target not in record_set:
            raise ValueError(f"relation {relation['id']} has dangling endpoint")
        if source == target:
            raise ValueError(f"relation {relation['id']} is self-referential")
        if kind == "derived_from":
            derived_count += 1
        if kind == "contradicts":
            if source > target:
                raise ValueError(f"contradiction {relation['id']} is not in canonical lexical endpoint order")
            pair = (source, target)
            if pair in contradiction_pairs:
                raise ValueError(f"duplicate contradiction pair {pair}")
            contradiction_pairs.add(pair)
        if kind == "depends_on" and relation.get("data", {}).get("dependency_kind") == "legacy_untyped":
            raise ValueError("native admission transaction may not create legacy_untyped dependencies")

    derived_records = {
        record["id"]
        for record in records
        if record.get("kind") == "proposition" and record.get("data", {}).get("epistemic_role") == "derived"
    }
    premise_targets = {relation["from"] for relation in relations if relation["kind"] == "derived_from"}
    missing = sorted(derived_records - premise_targets)
    if missing:
        raise ValueError(f"derived propositions without derived_from premise: {missing}")

    return {
        "record_ids_unique": True,
        "relation_ids_unique": True,
        "dangling_relation_endpoints": 0,
        "derived_relation_count": derived_count,
        "derived_propositions_have_premises": True,
        "contradictions_canonicalized": True,
    }


def apply_transaction(base: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if base.get("semantic") != PROFILE:
        raise ValueError("base document must be pems/2")
    validate_plan(plan)
    normalized_base = normalize_pems(base)
    actual_base_sha = sha256(jcs(normalized_base))
    if actual_base_sha != plan["expected_base_sha256"]:
        raise ValueError(
            f"base hash mismatch: expected {plan['expected_base_sha256']} got {actual_base_sha}"
        )

    existing_records = {record["id"]: record for record in normalized_base["records"]}
    existing_relations = {relation["id"]: relation for relation in normalized_base["relations"]}

    for record_id in plan["reuse_record_ids"]:
        if record_id not in existing_records:
            raise ValueError(f"reused canonical record does not exist: {record_id}")

    additions: list[dict[str, Any]] = []
    seen_new_records: set[str] = set()
    for record in plan["new_records"]:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError("every new record requires id")
        if record_id in existing_records or record_id in seen_new_records:
            raise ValueError(f"new record ID collision: {record_id}")
        seen_new_records.add(record_id)
        additions.append(copy.deepcopy(record))

    relation_additions: list[dict[str, Any]] = []
    seen_new_relations: set[str] = set()
    for relation in plan["new_relations"]:
        relation_id = relation.get("id")
        if not isinstance(relation_id, str) or not relation_id:
            raise ValueError("every new relation requires id")
        if relation_id in existing_relations or relation_id in seen_new_relations:
            raise ValueError(f"new relation ID collision: {relation_id}")
        seen_new_relations.add(relation_id)
        relation_additions.append(copy.deepcopy(relation))

    candidate = copy.deepcopy(normalized_base)
    candidate["records"].extend(additions)
    candidate["relations"].extend(relation_additions)
    return normalize_pems(candidate)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    base = json.loads(args.base.read_text(encoding="utf-8"))
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))

    normalized_base = normalize_pems(base)
    candidate = apply_transaction(normalized_base, plan)

    schema_errors = sorted(Draft202012Validator(schema).iter_errors(candidate), key=lambda err: list(err.path))
    if schema_errors:
        rendered = "; ".join(f"{list(err.path)}: {err.message}" for err in schema_errors[:20])
        raise ValueError(f"PEMS/2 schema validation failed: {rendered}")

    graph_proof = validate_graph_integrity(candidate)
    pems_bytes = jcs(candidate)
    cove = encode_cove(candidate)
    decoded = _decode(cove["x"], cove["d"], cove["h"])
    if decoded != candidate:
        raise ValueError("COVE structural round-trip failed")
    cove_bytes = jcs(cove)

    if jcs(normalize_pems(json.loads(pems_bytes))) != pems_bytes:
        raise ValueError("repeated PEMS/JCS generation is not deterministic")
    if jcs(encode_cove(json.loads(pems_bytes))) != cove_bytes:
        raise ValueError("repeated COVE/JCS generation is not deterministic")

    proof = {
        "contract": CONTRACT,
        "base": {
            "sha256": sha256(jcs(normalized_base)),
            "record_count": len(normalized_base["records"]),
            "relation_count": len(normalized_base["relations"]),
        },
        "transaction": {
            "reuse_record_count": len(plan["reuse_record_ids"]),
            "new_record_count": len(plan["new_records"]),
            "new_relation_count": len(plan["new_relations"]),
        },
        "candidate": {
            "semantic": candidate["semantic"],
            "record_count": len(candidate["records"]),
            "relation_count": len(candidate["relations"]),
            "pems_jcs_sha256": sha256(pems_bytes),
            "cove_jcs_sha256": sha256(cove_bytes),
            "cove_tuple": f"{COVE}|{PROFILE}|{SERIALIZER}",
        },
        "proofs": {
            "pems_schema_valid": True,
            "graph_integrity": graph_proof,
            "cove_structural_round_trip": True,
            "repeated_pems_bytes_identical": True,
            "repeated_cove_bytes_identical": True,
            "canonical_written": False,
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "candidate.pems2.jcs.json").write_bytes(pems_bytes)
    (args.out_dir / "candidate.cove.json").write_bytes(cove_bytes)
    (args.out_dir / "admission-proof.json").write_bytes(jcs(proof))
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
