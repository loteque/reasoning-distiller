#!/usr/bin/env python3
"""Apply a Steward-authorized RGP admission transaction with exact guarded reused-record updates."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from apply_admission_transaction import (
    COVE,
    PROFILE,
    SERIALIZER,
    _decode,
    encode_cove,
    jcs,
    normalize_pems,
    sha256,
    validate_graph_integrity,
)

CONTRACT = "rgp-pems2-admission-transaction/2"


def validate_plan(plan: Any) -> None:
    if not isinstance(plan, dict):
        raise ValueError("transaction plan must be an object")
    if plan.get("contract") != CONTRACT:
        raise ValueError(f"transaction plan contract must be {CONTRACT}")
    if not isinstance(plan.get("expected_base_sha256"), str) or not plan["expected_base_sha256"]:
        raise ValueError("expected_base_sha256 is required")
    for key in ("reuse_record_ids", "record_updates", "new_records", "new_relations"):
        if key not in plan or not isinstance(plan[key], list):
            raise ValueError(f"{key} must be an array")


def apply_transaction(
    base: dict[str, Any], plan: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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

    reuse_ids = plan["reuse_record_ids"]
    if len(reuse_ids) != len(set(reuse_ids)):
        raise ValueError("reuse_record_ids contains duplicates")
    for record_id in reuse_ids:
        if record_id not in existing_records:
            raise ValueError(f"reused canonical record does not exist: {record_id}")

    update_ids: set[str] = set()
    applied_updates: list[dict[str, Any]] = []
    replacements: dict[str, dict[str, Any]] = {}
    for update in plan["record_updates"]:
        if not isinstance(update, dict):
            raise ValueError("every record update must be an object")
        record_id = update.get("record_id")
        expected_before_sha256 = update.get("expected_before_sha256")
        replacement = update.get("replacement")

        if not isinstance(record_id, str) or not record_id:
            raise ValueError("every record update requires record_id")
        if record_id in update_ids:
            raise ValueError(f"duplicate record update target: {record_id}")
        update_ids.add(record_id)

        if record_id not in existing_records:
            raise ValueError(f"updated canonical record does not exist: {record_id}")
        if record_id not in reuse_ids:
            raise ValueError(f"updated record must also be declared reused: {record_id}")
        if not isinstance(expected_before_sha256, str) or not expected_before_sha256:
            raise ValueError(f"record update {record_id} requires expected_before_sha256")
        if not isinstance(replacement, dict):
            raise ValueError(f"record update {record_id} replacement must be an object")
        if replacement.get("id") != record_id:
            raise ValueError(f"record update {record_id} may not rebind record identity")
        if replacement.get("kind") != existing_records[record_id].get("kind"):
            raise ValueError(f"record update {record_id} may not change record kind")

        before_sha = sha256(jcs(existing_records[record_id]))
        if before_sha != expected_before_sha256:
            raise ValueError(
                f"record update before-state mismatch for {record_id}: "
                f"expected {expected_before_sha256} got {before_sha}"
            )

        replacements[record_id] = copy.deepcopy(replacement)
        applied_updates.append(
            {
                "record_id": record_id,
                "before_sha256": before_sha,
                "after_sha256": sha256(jcs(replacement)),
            }
        )

    additions: list[dict[str, Any]] = []
    seen_new_records: set[str] = set()
    for record in plan["new_records"]:
        if not isinstance(record, dict):
            raise ValueError("every new record must be an object")
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
        if not isinstance(relation, dict):
            raise ValueError("every new relation must be an object")
        relation_id = relation.get("id")
        if not isinstance(relation_id, str) or not relation_id:
            raise ValueError("every new relation requires id")
        if relation_id in existing_relations or relation_id in seen_new_relations:
            raise ValueError(f"new relation ID collision: {relation_id}")
        seen_new_relations.add(relation_id)
        relation_additions.append(copy.deepcopy(relation))

    candidate = copy.deepcopy(normalized_base)
    candidate["records"] = [
        copy.deepcopy(replacements.get(record["id"], record))
        for record in candidate["records"]
    ]
    candidate["records"].extend(additions)
    candidate["relations"].extend(relation_additions)
    return normalize_pems(candidate), applied_updates


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
    candidate, applied_updates = apply_transaction(normalized_base, plan)

    schema_errors = sorted(
        Draft202012Validator(schema).iter_errors(candidate), key=lambda err: list(err.path)
    )
    if schema_errors:
        rendered = "; ".join(
            f"{list(err.path)}: {err.message}" for err in schema_errors[:20]
        )
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
            "record_update_count": len(plan["record_updates"]),
            "record_updates": applied_updates,
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
            "base_exact_match": True,
            "record_update_before_states_exact": True,
            "record_identity_preserved": True,
            "record_kind_preserved": True,
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
