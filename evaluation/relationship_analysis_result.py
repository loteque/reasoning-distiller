#!/usr/bin/env python3
"""Validate non-authoritative semantic batch results for relationship benchmark A0."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RESULT_CONTRACT = "reasoning-distiller-relationship-analysis-result/1"
ANALYZER_PROTOCOL = "reasoning-distiller-fixed-relation-analyzer/1"
RELATION_TYPES = {"supports", "depends_on", "supersedes", "contradicts"}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_string(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty string")


def candidate_record_digest(record: dict[str, Any]) -> str:
    return digest(record)


def finalize_result(result_without_digest: dict[str, Any]) -> dict[str, Any]:
    if "result_digest" in result_without_digest:
        raise ValueError("result_digest must not be present before finalization")
    result = dict(result_without_digest)
    result["result_digest"] = digest(result_without_digest)
    return result


def validate_result(result: dict[str, Any], batch: dict[str, Any]) -> None:
    if result.get("contract") != RESULT_CONTRACT:
        raise ValueError("unsupported analysis-result contract")
    if result.get("benchmark_id") != batch.get("benchmark_id"):
        raise ValueError("benchmark_id does not match input batch")
    if result.get("batch_id") != batch.get("batch_id"):
        raise ValueError("batch_id does not match input batch")
    if result.get("input_batch_digest") != batch.get("batch_digest"):
        raise ValueError("input batch digest mismatch")
    if result.get("algorithm_id") != "A0-exhaustive/1":
        raise ValueError("A0 result must declare algorithm A0-exhaustive/1")
    if result.get("status") != "COMPLETE":
        raise ValueError("analysis result status must be COMPLETE")
    analyzer = result.get("analyzer")
    if not isinstance(analyzer, dict):
        raise ValueError("analyzer must be an object")
    if analyzer.get("protocol") != ANALYZER_PROTOCOL:
        raise ValueError("unexpected semantic analyzer protocol")
    _require_string(analyzer.get("model"), "analyzer.model")
    if analyzer.get("authority") != "none":
        raise ValueError("relationship analyzer must declare authority=none")

    expected_pairs = batch.get("pair_count")
    if result.get("assessed_pair_count") != expected_pairs:
        raise ValueError("assessed pair count does not cover the exact batch")
    if result.get("assessed_hypothesis_count") != expected_pairs * 7:
        raise ValueError("assessed hypothesis count does not cover the exact batch")

    left = {record["id"]: record for record in batch.get("left_records", [])}
    right = {record["id"]: record for record in batch.get("right_records", [])}
    all_records = dict(left)
    all_records.update(right)
    pair_mode = batch.get("pair_mode")

    relations = result.get("candidate_relations")
    if not isinstance(relations, list):
        raise ValueError("candidate_relations must be an array")
    seen: set[tuple[str, str, str]] = set()
    for index, relation in enumerate(relations):
        path = f"candidate_relations[{index}]"
        if not isinstance(relation, dict):
            raise ValueError(f"{path} must be an object")
        source = relation.get("from_record_id")
        target = relation.get("to_record_id")
        relation_type = relation.get("type")
        if source not in all_records or target not in all_records:
            raise ValueError(f"{path} endpoint is outside the input batch")
        if source == target:
            raise ValueError(f"{path} self relation is forbidden")
        if relation_type not in RELATION_TYPES:
            raise ValueError(f"{path}.type is invalid")
        if pair_mode == "cartesian_between":
            if not ((source in left and target in right) or (source in right and target in left)):
                raise ValueError(f"{path} does not cross the two scoped blocks")
        elif pair_mode == "unique_within":
            if source not in left or target not in left:
                raise ValueError(f"{path} is outside the diagonal block")
        else:
            raise ValueError("unknown pair_mode")
        if relation.get("from_record_digest") != candidate_record_digest(all_records[source]):
            raise ValueError(f"{path}.from_record_digest mismatch")
        if relation.get("to_record_digest") != candidate_record_digest(all_records[target]):
            raise ValueError(f"{path}.to_record_digest mismatch")
        _require_string(relation.get("rationale"), f"{path}.rationale")
        if relation_type == "contradicts" and source > target:
            raise ValueError(f"{path} symmetric contradiction endpoints must be lexicographically normalized")
        key = (source, relation_type, target)
        if key in seen:
            raise ValueError(f"{path} duplicates an earlier relation")
        seen.add(key)

    result_digest = result.get("result_digest")
    _require_string(result_digest, "result_digest")
    payload = dict(result)
    payload.pop("result_digest")
    if result_digest != digest(payload):
        raise ValueError("result_digest mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    validate_result(result, batch)
    print(
        f"PASS {args.result}: {result['batch_id']} "
        f"{result['assessed_pair_count']} pairs, {len(result['candidate_relations'])} candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
