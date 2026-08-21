#!/usr/bin/env python3
"""Deterministic scaffolding for the relationship-discovery benchmark.

This module performs no semantic relationship judgment. It freezes an eligible
PEMS proposition corpus, partitions it for bounded exhaustive A0 assessment,
verifies pair-space coverage, validates algorithm reports, and renders the
standard human-readable report from the normative JSON report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

BENCHMARK_CONTRACT = "reasoning-distiller-relationship-benchmark/1"
REPORT_CONTRACT = "reasoning-distiller-relationship-algorithm-report/1"
COVERAGE_CONTRACT = "reasoning-distiller-relationship-coverage/1"
BATCH_CONTRACT = "reasoning-distiller-relationship-analysis-batch/1"
RELATION_TYPES = ("supports", "depends_on", "supersedes", "contradicts")
VERDICTS = {"PASS", "FAIL_LOSS", "FAIL_INVALID", "INCOMPLETE"}
METRIC_STATUSES = {"measured", "derived", "unavailable", "pending"}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_prefixed(data: bytes) -> str:
    return f"sha256:{sha256_hex(data)}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def select_eligible_propositions(pems: dict[str, Any]) -> list[dict[str, Any]]:
    if pems.get("semantic") != "pems/2":
        raise ValueError("benchmark corpus must be pems/2")
    records = pems.get("records")
    if not isinstance(records, list):
        raise ValueError("PEMS records must be an array")
    eligible = [
        record
        for record in records
        if isinstance(record, dict)
        and record.get("kind") == "proposition"
        and record.get("lifecycle") == "current"
    ]
    ids = [record.get("id") for record in eligible]
    if any(not isinstance(record_id, str) or not record_id for record_id in ids):
        raise ValueError("eligible proposition IDs must be non-empty strings")
    if len(ids) != len(set(ids)):
        raise ValueError("eligible proposition IDs must be unique")
    return sorted(eligible, key=lambda record: record["id"])


def pair_count(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    return n * (n - 1) // 2


def _block_digest(record_ids: Iterable[str]) -> str:
    return sha256_prefixed(canonical_json_bytes(list(record_ids)))


def build_coverage(
    pems_bytes: bytes,
    *,
    benchmark_id: str,
    repository_commit: str,
    expected_pems_sha256: str,
    block_size: int = 32,
) -> dict[str, Any]:
    if block_size <= 1:
        raise ValueError("block_size must be greater than 1")
    actual_pems_sha256 = sha256_hex(pems_bytes)
    expected = expected_pems_sha256.removeprefix("sha256:")
    if actual_pems_sha256 != expected:
        raise ValueError(
            f"frozen PEMS digest mismatch: expected {expected}, got {actual_pems_sha256}"
        )
    pems = json.loads(pems_bytes)
    eligible = select_eligible_propositions(pems)
    blocks: list[dict[str, Any]] = []
    for block_index, start in enumerate(range(0, len(eligible), block_size)):
        block_records = eligible[start : start + block_size]
        record_ids = [record["id"] for record in block_records]
        blocks.append(
            {
                "index": block_index,
                "count": len(record_ids),
                "record_ids": record_ids,
                "record_ids_digest": _block_digest(record_ids),
            }
        )

    batches: list[dict[str, Any]] = []
    for left in range(len(blocks)):
        for right in range(left, len(blocks)):
            left_count = blocks[left]["count"]
            right_count = blocks[right]["count"]
            count = pair_count(left_count) if left == right else left_count * right_count
            batches.append(
                {
                    "batch_id": f"A0-B{left:02d}-B{right:02d}",
                    "left_block": left,
                    "right_block": right,
                    "pair_mode": "unique_within" if left == right else "cartesian_between",
                    "pair_count": count,
                }
            )

    coverage = {
        "contract": COVERAGE_CONTRACT,
        "benchmark_id": benchmark_id,
        "repository_commit": repository_commit,
        "pems_sha256": f"sha256:{actual_pems_sha256}",
        "eligibility": {"kind": "proposition", "lifecycle": "current"},
        "ordering": "lexicographic_record_id",
        "block_size": block_size,
        "eligible_propositions": len(eligible),
        "expected_pair_count": pair_count(len(eligible)),
        "expected_hypothesis_count": pair_count(len(eligible)) * 7,
        "blocks": blocks,
        "batches": batches,
    }
    verify_coverage(coverage)
    return coverage


def verify_coverage(coverage: dict[str, Any]) -> None:
    if coverage.get("contract") != COVERAGE_CONTRACT:
        raise ValueError("unsupported coverage contract")
    blocks = coverage.get("blocks")
    batches = coverage.get("batches")
    if not isinstance(blocks, list) or not blocks:
        raise ValueError("coverage blocks must be a non-empty array")
    if not isinstance(batches, list) or not batches:
        raise ValueError("coverage batches must be a non-empty array")

    seen_ids: set[str] = set()
    total_records = 0
    for expected_index, block in enumerate(blocks):
        if block.get("index") != expected_index:
            raise ValueError("coverage block indexes must be contiguous")
        record_ids = block.get("record_ids")
        if not isinstance(record_ids, list) or not record_ids:
            raise ValueError("coverage block record_ids must be non-empty")
        if record_ids != sorted(record_ids):
            raise ValueError("record IDs in each block must be lexicographically sorted")
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("duplicate record ID inside coverage block")
        overlap = seen_ids.intersection(record_ids)
        if overlap:
            raise ValueError(f"record IDs occur in multiple blocks: {sorted(overlap)}")
        seen_ids.update(record_ids)
        total_records += len(record_ids)
        if block.get("count") != len(record_ids):
            raise ValueError("coverage block count mismatch")
        if block.get("record_ids_digest") != _block_digest(record_ids):
            raise ValueError("coverage block record_ids digest mismatch")

    if coverage.get("eligible_propositions") != total_records:
        raise ValueError("eligible proposition count mismatch")

    expected_batch_keys = {(left, right) for left in range(len(blocks)) for right in range(left, len(blocks))}
    seen_batch_keys: set[tuple[int, int]] = set()
    total_pairs = 0
    for batch in batches:
        left = batch.get("left_block")
        right = batch.get("right_block")
        key = (left, right)
        if key not in expected_batch_keys:
            raise ValueError(f"invalid A0 batch block pair {key}")
        if key in seen_batch_keys:
            raise ValueError(f"duplicate A0 batch block pair {key}")
        seen_batch_keys.add(key)
        left_count = blocks[left]["count"]
        right_count = blocks[right]["count"]
        expected_count = pair_count(left_count) if left == right else left_count * right_count
        if batch.get("pair_count") != expected_count:
            raise ValueError(f"pair count mismatch for batch {batch.get('batch_id')}")
        expected_mode = "unique_within" if left == right else "cartesian_between"
        if batch.get("pair_mode") != expected_mode:
            raise ValueError(f"pair mode mismatch for batch {batch.get('batch_id')}")
        total_pairs += expected_count

    if seen_batch_keys != expected_batch_keys:
        missing = sorted(expected_batch_keys - seen_batch_keys)
        raise ValueError(f"missing A0 block-pair batches: {missing}")
    expected_pairs = pair_count(total_records)
    if total_pairs != expected_pairs or coverage.get("expected_pair_count") != expected_pairs:
        raise ValueError("A0 pair-space coverage is incomplete")
    if coverage.get("expected_hypothesis_count") != expected_pairs * 7:
        raise ValueError("A0 hypothesis-space count mismatch")


def materialize_batch(
    pems_bytes: bytes,
    coverage: dict[str, Any],
    batch_id: str,
) -> dict[str, Any]:
    verify_coverage(coverage)
    actual_pems_sha = sha256_prefixed(pems_bytes)
    if actual_pems_sha != coverage.get("pems_sha256"):
        raise ValueError("batch materialization PEMS digest mismatch")
    pems = json.loads(pems_bytes)
    eligible = {record["id"]: record for record in select_eligible_propositions(pems)}
    batch = next((item for item in coverage["batches"] if item["batch_id"] == batch_id), None)
    if batch is None:
        raise ValueError(f"unknown batch {batch_id}")
    left_block = coverage["blocks"][batch["left_block"]]
    right_block = coverage["blocks"][batch["right_block"]]
    left_records = [eligible[record_id] for record_id in left_block["record_ids"]]
    right_records = [eligible[record_id] for record_id in right_block["record_ids"]]
    payload = {
        "contract": BATCH_CONTRACT,
        "benchmark_id": coverage["benchmark_id"],
        "batch_id": batch_id,
        "pems_sha256": coverage["pems_sha256"],
        "pair_mode": batch["pair_mode"],
        "pair_count": batch["pair_count"],
        "relation_hypotheses": [
            "left supports right",
            "right supports left",
            "left depends_on right",
            "right depends_on left",
            "left supersedes right",
            "right supersedes left",
            "left contradicts right",
        ],
        "left_records": left_records,
        "right_records": right_records,
    }
    payload["batch_digest"] = sha256_prefixed(canonical_json_bytes(payload))
    return payload


def _require_nonempty_string(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty string")


def validate_report(report: dict[str, Any]) -> None:
    if report.get("contract") != REPORT_CONTRACT:
        raise ValueError("unsupported relationship algorithm report contract")
    identity = report.get("identity")
    hypothesis = report.get("hypothesis")
    method = report.get("method")
    metrics = report.get("metrics")
    verdict = report.get("verdict")
    for name, value in (("identity", identity), ("hypothesis", hypothesis), ("method", method), ("metrics", metrics)):
        if not isinstance(value, dict):
            raise ValueError(f"{name} must be an object")
    for field in (
        "algorithm_id",
        "algorithm_version",
        "implementation_digest",
        "benchmark_id",
        "benchmark_digest",
        "execution_id",
    ):
        _require_nonempty_string(identity.get(field), f"identity.{field}")
    for field in ("algorithm_summary", "selection_rationale", "expected_behavior"):
        _require_nonempty_string(hypothesis.get(field), f"hypothesis.{field}")
    _require_nonempty_string(method.get("summary"), "method.summary")
    if verdict not in VERDICTS:
        raise ValueError(f"verdict must be one of {sorted(VERDICTS)}")
    if not metrics:
        raise ValueError("metrics must not be empty")
    for name, metric in metrics.items():
        if not isinstance(metric, dict):
            raise ValueError(f"metrics.{name} must be an object")
        status = metric.get("status")
        if status not in METRIC_STATUSES:
            raise ValueError(f"metrics.{name}.status must be one of {sorted(METRIC_STATUSES)}")
        if status in {"measured", "derived"} and "value" not in metric:
            raise ValueError(f"metrics.{name}.value is required for status {status}")
        if status in {"pending", "unavailable"} and "value" in metric:
            raise ValueError(f"metrics.{name}.value must be omitted for status {status}")
    misses = report.get("misses")
    if not isinstance(misses, list):
        raise ValueError("misses must be an array")
    notes = report.get("notes", [])
    if not isinstance(notes, list) or any(not isinstance(note, str) for note in notes):
        raise ValueError("notes must be an array of strings")


def _metric_text(metric: dict[str, Any]) -> str:
    status = metric["status"]
    if status in {"pending", "unavailable"}:
        return status.upper()
    value = metric["value"]
    unit = metric.get("unit")
    return f"{value}{(' ' + unit) if unit else ''} ({status})"


def render_report(report: dict[str, Any]) -> str:
    validate_report(report)
    identity = report["identity"]
    hypothesis = report["hypothesis"]
    metrics = report["metrics"]
    lines = [
        "# Relationship Discovery Algorithm Report",
        "",
        "## Identity",
        "",
        f"- Algorithm: `{identity['algorithm_id']}/{identity['algorithm_version']}`",
        f"- Benchmark: `{identity['benchmark_id']}`",
        f"- Execution: `{identity['execution_id']}`",
        f"- Implementation: `{identity['implementation_digest']}`",
        f"- Benchmark digest: `{identity['benchmark_digest']}`",
        "",
        "## Hypothesis",
        "",
        f"**Algorithm.** {hypothesis['algorithm_summary']}",
        "",
        f"**Why selected.** {hypothesis['selection_rationale']}",
        "",
        f"**Expected behavior.** {hypothesis['expected_behavior']}",
        "",
        "## Method",
        "",
        report["method"]["summary"],
        "",
        "## Work",
        "",
        "| Metric | Result |",
        "|---|---:|",
    ]
    work_names = [
        "eligible_propositions",
        "total_possible_pairs",
        "pairs_retained",
        "pairs_pruned",
        "pair_space_searched_percent",
        "pair_space_reduction_percent",
        "relationship_hypotheses_retained",
        "semantic_analyses_required",
        "candidate_generation_runtime_seconds",
        "input_tokens",
        "output_tokens",
        "monetary_cost",
        "index_storage_bytes",
    ]
    for name in work_names:
        if name in metrics:
            lines.append(f"| {name.replace('_', ' ')} | {_metric_text(metrics[name])} |")

    lines += ["", "## Relationship Results", "", "| Metric | Result |", "|---|---:|"]
    result_names = [
        "baseline_relations",
        "baseline_relations_covered",
        "baseline_relations_missed",
        "baseline_recall_percent",
    ]
    for name in result_names:
        if name in metrics:
            lines.append(f"| {name.replace('_', ' ')} | {_metric_text(metrics[name])} |")

    lines += ["", "## Misses", ""]
    if report["misses"]:
        for miss in report["misses"]:
            lines.append(f"- {json.dumps(miss, sort_keys=True, ensure_ascii=False)}")
    else:
        lines.append("None recorded at this stage.")

    reduction = metrics.get("pair_space_reduction_percent", {"status": "unavailable"})
    recall = metrics.get("baseline_recall_percent", {"status": "unavailable"})
    lines += [
        "",
        "## Efficiency",
        "",
        f"**Pair-space reduction:** {_metric_text(reduction)}  ",
        f"**Baseline recall:** {_metric_text(recall)}",
        "",
        "## Verdict",
        "",
        f"**{report['verdict']}**",
    ]
    for note in report.get("notes", []):
        lines.append(f"\n{note}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap = sub.add_parser("bootstrap")
    bootstrap.add_argument("--pems", type=Path, required=True)
    bootstrap.add_argument("--benchmark", type=Path, required=True)
    bootstrap.add_argument("--coverage-out", type=Path, required=True)

    verify = sub.add_parser("verify-coverage")
    verify.add_argument("coverage", type=Path)

    batch = sub.add_parser("materialize-batch")
    batch.add_argument("--pems", type=Path, required=True)
    batch.add_argument("--coverage", type=Path, required=True)
    batch.add_argument("--batch-id", required=True)
    batch.add_argument("--out", type=Path, required=True)

    validate = sub.add_parser("validate-report")
    validate.add_argument("report", type=Path)

    render = sub.add_parser("render-report")
    render.add_argument("report", type=Path)
    render.add_argument("--out", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "bootstrap":
        benchmark = load_json(args.benchmark)
        if benchmark.get("contract") != BENCHMARK_CONTRACT:
            raise SystemExit("unsupported benchmark contract")
        pems_bytes = args.pems.read_bytes()
        coverage = build_coverage(
            pems_bytes,
            benchmark_id=benchmark["benchmark_id"],
            repository_commit=benchmark["repository_commit"],
            expected_pems_sha256=benchmark["pems_sha256"],
            block_size=benchmark["a0"]["block_size"],
        )
        expected = benchmark["expected"]
        actual = {
            "eligible_propositions": coverage["eligible_propositions"],
            "unordered_pairs": coverage["expected_pair_count"],
            "relationship_hypotheses": coverage["expected_hypothesis_count"],
        }
        if actual != expected:
            raise SystemExit(f"benchmark expectation mismatch: expected {expected}, got {actual}")
        args.coverage_out.parent.mkdir(parents=True, exist_ok=True)
        args.coverage_out.write_bytes(canonical_json_bytes(coverage) + b"\n")
        print(f"PASS {args.coverage_out}: {actual}")
        return 0
    if args.command == "verify-coverage":
        verify_coverage(load_json(args.coverage))
        print(f"PASS {args.coverage}")
        return 0
    if args.command == "materialize-batch":
        payload = materialize_batch(args.pems.read_bytes(), load_json(args.coverage), args.batch_id)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(canonical_json_bytes(payload) + b"\n")
        print(f"PASS {args.out}: {payload['batch_id']} {payload['pair_count']} pairs")
        return 0
    if args.command == "validate-report":
        validate_report(load_json(args.report))
        print(f"PASS {args.report}")
        return 0
    if args.command == "render-report":
        text = render_report(load_json(args.report))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"PASS {args.out}")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
