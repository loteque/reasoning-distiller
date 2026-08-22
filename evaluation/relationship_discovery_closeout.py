#!/usr/bin/env python3
"""Deterministically close out complete A0 relationship-analysis evidence.

This module performs no semantic judgment. It requires the exact complete A0
coverage and validated non-authoritative batch results, aggregates those results
without changing their relation claims, and renders the pre-reconciliation A0
report. Steward reconciliation remains a separate authority boundary.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import relationship_analysis_result as analysis
import relationship_discovery_benchmark as bench

CANDIDATES_CONTRACT = "reasoning-distiller-relationship-candidates/1"
A0_ALGORITHM_ID = "A0-exhaustive/1"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bench.canonical_json_bytes(value) + b"\n")


def _candidate_payload_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("candidate_set_digest", None)
    return bench.sha256_prefixed(bench.canonical_json_bytes(unsigned))


def validate_candidate_set(candidates: dict[str, Any], coverage: dict[str, Any]) -> None:
    bench.verify_coverage(coverage)
    if candidates.get("contract") != CANDIDATES_CONTRACT:
        raise ValueError("unsupported relationship candidate-set contract")
    if candidates.get("benchmark_id") != coverage.get("benchmark_id"):
        raise ValueError("candidate-set benchmark_id mismatch")
    if candidates.get("algorithm_id") != A0_ALGORITHM_ID:
        raise ValueError("candidate-set algorithm_id mismatch")
    if candidates.get("pems_sha256") != coverage.get("pems_sha256"):
        raise ValueError("candidate-set PEMS digest mismatch")
    if candidates.get("coverage_digest") != bench.sha256_prefixed(bench.canonical_json_bytes(coverage)):
        raise ValueError("candidate-set coverage digest mismatch")

    source_results = candidates.get("source_results")
    relations = candidates.get("candidate_relations")
    if not isinstance(source_results, list) or not isinstance(relations, list):
        raise ValueError("candidate-set source_results and candidate_relations must be arrays")

    expected_batch_ids = [batch["batch_id"] for batch in coverage["batches"]]
    actual_batch_ids = [item.get("batch_id") for item in source_results if isinstance(item, dict)]
    if actual_batch_ids != expected_batch_ids:
        raise ValueError("candidate-set source result manifest does not exactly match coverage order")
    if candidates.get("source_result_count") != len(source_results):
        raise ValueError("candidate-set source_result_count mismatch")

    total_pairs = 0
    total_hypotheses = 0
    total_candidates = 0
    source_digest_by_batch: dict[str, str] = {}
    for item in source_results:
        if not isinstance(item, dict):
            raise ValueError("candidate-set source result manifest entries must be objects")
        batch_id = item.get("batch_id")
        result_digest = item.get("result_digest")
        if not isinstance(result_digest, str) or not result_digest.startswith("sha256:"):
            raise ValueError(f"candidate-set source result {batch_id} has invalid result digest")
        source_digest_by_batch[batch_id] = result_digest
        for field in ("assessed_pair_count", "assessed_hypothesis_count", "candidate_relation_count"):
            if not isinstance(item.get(field), int) or item[field] < 0:
                raise ValueError(f"candidate-set source result {batch_id} has invalid {field}")
        total_pairs += item["assessed_pair_count"]
        total_hypotheses += item["assessed_hypothesis_count"]
        total_candidates += item["candidate_relation_count"]

    if total_pairs != coverage["expected_pair_count"] or candidates.get("assessed_pair_count") != total_pairs:
        raise ValueError("candidate-set assessed pair count mismatch")
    if total_hypotheses != coverage["expected_hypothesis_count"] or candidates.get("assessed_hypothesis_count") != total_hypotheses:
        raise ValueError("candidate-set assessed hypothesis count mismatch")
    if total_candidates != len(relations) or candidates.get("candidate_relation_count") != total_candidates:
        raise ValueError("candidate-set relation count mismatch")

    seen: set[tuple[str, str, str]] = set()
    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            raise ValueError(f"candidate_relations[{index}] must be an object")
        key = (relation.get("from_record_id"), relation.get("type"), relation.get("to_record_id"))
        if any(not isinstance(value, str) or not value for value in key):
            raise ValueError(f"candidate_relations[{index}] has invalid identity")
        if key in seen:
            raise ValueError(f"candidate_relations[{index}] duplicates a relation identity")
        seen.add(key)
        batch_id = relation.get("source_batch_id")
        result_digest = relation.get("source_result_digest")
        if source_digest_by_batch.get(batch_id) != result_digest:
            raise ValueError(f"candidate_relations[{index}] provenance does not bind to source result")

    if candidates.get("candidate_set_digest") != _candidate_payload_digest(candidates):
        raise ValueError("candidate_set_digest mismatch")


def aggregate_candidates(
    coverage: dict[str, Any],
    *,
    batch_dir: Path,
    result_dir: Path,
) -> dict[str, Any]:
    bench.verify_coverage(coverage)
    expected_batch_ids = [batch["batch_id"] for batch in coverage["batches"]]
    persisted_result_ids = sorted(path.name.removesuffix(".result.json") for path in result_dir.glob("A0-B??-B??.result.json"))
    if persisted_result_ids != sorted(expected_batch_ids):
        missing = sorted(set(expected_batch_ids) - set(persisted_result_ids))
        extra = sorted(set(persisted_result_ids) - set(expected_batch_ids))
        raise ValueError(f"A0 closeout requires exact complete result set; missing={missing}, extra={extra}")

    source_results: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    analyzers: set[tuple[str, str, str]] = set()
    for batch_id in expected_batch_ids:
        batch_path = batch_dir / f"{batch_id}.json"
        result_path = result_dir / f"{batch_id}.result.json"
        if not batch_path.is_file():
            raise ValueError(f"missing immutable input batch {batch_id}")
        batch = _load(batch_path)
        result = _load(result_path)
        analysis.validate_result(result, batch)
        analyzer = result["analyzer"]
        analyzers.add((analyzer["protocol"], analyzer["model"], analyzer["authority"]))
        source_results.append(
            {
                "batch_id": batch_id,
                "input_batch_digest": result["input_batch_digest"],
                "result_digest": result["result_digest"],
                "assessed_pair_count": result["assessed_pair_count"],
                "assessed_hypothesis_count": result["assessed_hypothesis_count"],
                "candidate_relation_count": len(result["candidate_relations"]),
            }
        )
        for relation in result["candidate_relations"]:
            item = dict(relation)
            item["source_batch_id"] = batch_id
            item["source_result_digest"] = result["result_digest"]
            relations.append(item)

    relations.sort(key=lambda item: (item["from_record_id"], item["type"], item["to_record_id"], item["source_batch_id"]))
    source_results.sort(key=lambda item: item["batch_id"])
    payload: dict[str, Any] = {
        "contract": CANDIDATES_CONTRACT,
        "benchmark_id": coverage["benchmark_id"],
        "algorithm_id": A0_ALGORITHM_ID,
        "pems_sha256": coverage["pems_sha256"],
        "coverage_digest": bench.sha256_prefixed(bench.canonical_json_bytes(coverage)),
        "analyzers": [
            {"protocol": protocol, "model": model, "authority": authority}
            for protocol, model, authority in sorted(analyzers)
        ],
        "source_result_count": len(source_results),
        "source_results": source_results,
        "assessed_pair_count": sum(item["assessed_pair_count"] for item in source_results),
        "assessed_hypothesis_count": sum(item["assessed_hypothesis_count"] for item in source_results),
        "candidate_relation_count": len(relations),
        "candidate_relations": relations,
    }
    payload["candidate_set_digest"] = _candidate_payload_digest(payload)
    validate_candidate_set(payload, coverage)
    return payload


def finalize_report(
    report_template: dict[str, Any],
    coverage: dict[str, Any],
    candidates: dict[str, Any],
) -> dict[str, Any]:
    bench.validate_report(report_template)
    if report_template["identity"]["algorithm_id"] != "A0-exhaustive":
        raise ValueError("A0 closeout report template has unexpected algorithm identity")
    if report_template["identity"]["algorithm_version"] != "1":
        raise ValueError("A0 closeout report template has unexpected algorithm version")
    if report_template["identity"]["benchmark_id"] != coverage["benchmark_id"]:
        raise ValueError("A0 closeout report template benchmark mismatch")

    original_hypothesis = copy.deepcopy(report_template["hypothesis"])
    report = copy.deepcopy(report_template)
    metrics = report["metrics"]
    metrics["eligible_propositions"] = {"status": "measured", "value": coverage["eligible_propositions"]}
    metrics["total_possible_pairs"] = {"status": "derived", "value": coverage["expected_pair_count"]}
    metrics["pairs_retained"] = {"status": "derived", "value": coverage["expected_pair_count"]}
    metrics["pairs_pruned"] = {"status": "derived", "value": 0}
    metrics["pair_space_searched_percent"] = {"status": "derived", "value": 100.0, "unit": "%"}
    metrics["pair_space_reduction_percent"] = {"status": "derived", "value": 0.0, "unit": "%"}
    metrics["relationship_hypotheses_retained"] = {"status": "derived", "value": coverage["expected_hypothesis_count"]}
    metrics["semantic_analyses_required"] = {"status": "derived", "value": coverage["expected_pair_count"]}
    metrics["assessed_batches"] = {"status": "measured", "value": candidates["source_result_count"]}
    metrics["assessed_pairs"] = {"status": "measured", "value": candidates["assessed_pair_count"]}
    metrics["assessed_hypotheses"] = {"status": "measured", "value": candidates["assessed_hypothesis_count"]}
    metrics["raw_candidate_relations"] = {"status": "measured", "value": candidates["candidate_relation_count"]}
    metrics["candidate_generation_runtime_seconds"] = {"status": "unavailable"}
    metrics["input_tokens"] = {"status": "unavailable"}
    metrics["output_tokens"] = {"status": "unavailable"}
    metrics["monetary_cost"] = {"status": "unavailable"}
    metrics["baseline_relations"] = {"status": "pending"}
    metrics["baseline_relations_covered"] = {"status": "pending"}
    metrics["baseline_relations_missed"] = {"status": "pending"}
    metrics["baseline_recall_percent"] = {"status": "pending"}
    report["misses"] = []
    report["verdict"] = "INCOMPLETE"
    report["notes"] = [
        "The pre-result hypothesis is preserved unchanged from the report template.",
        (
            f"All {candidates['source_result_count']} exhaustive A0 semantic batches are COMPLETE and validated: "
            f"{candidates['assessed_pair_count']} unordered pairs, {candidates['assessed_hypothesis_count']} "
            f"relationship hypotheses, and {candidates['candidate_relation_count']} raw non-authoritative candidate relations."
        ),
        "A0 remains INCOMPLETE pending fresh Steward semantic reconciliation; raw candidate count is not the baseline relation count.",
    ]
    if report["hypothesis"] != original_hypothesis:
        raise AssertionError("A0 closeout modified the pre-result hypothesis")
    bench.validate_report(report)
    return report


def build_closeout(
    *,
    coverage_path: Path,
    batch_dir: Path,
    result_dir: Path,
    report_template_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    coverage = _load(coverage_path)
    candidates = aggregate_candidates(coverage, batch_dir=batch_dir, result_dir=result_dir)
    report_template = _load(report_template_path)
    report = finalize_report(report_template, coverage, candidates)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "coverage.json", coverage)
    _write_json(out_dir / "candidates.json", candidates)
    _write_json(out_dir / "report.json", report)
    (out_dir / "report.md").write_text(bench.render_report(report), encoding="utf-8")
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--coverage", type=Path, required=True)
    build.add_argument("--batch-dir", type=Path, required=True)
    build.add_argument("--result-dir", type=Path, required=True)
    build.add_argument("--report-template", type=Path, required=True)
    build.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        candidates = build_closeout(
            coverage_path=args.coverage,
            batch_dir=args.batch_dir,
            result_dir=args.result_dir,
            report_template_path=args.report_template,
            out_dir=args.out_dir,
        )
        print(
            "PASS A0 closeout: "
            f"{candidates['source_result_count']} batches, "
            f"{candidates['assessed_pair_count']} pairs, "
            f"{candidates['assessed_hypothesis_count']} hypotheses, "
            f"{candidates['candidate_relation_count']} raw candidates"
        )
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
