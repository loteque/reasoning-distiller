#!/usr/bin/env python3
"""Validate immutable Steward dispositions for the A0 relationship baseline.

This module performs no semantic judgment. It validates a complete Steward-
supplied assessment of the already-frozen A0 raw candidate set, binds every
disposition to the exact raw candidate and activation evidence, derives the
approved benchmark baseline, and updates the A0 report without admitting any
relation or mutating Canon.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import relationship_discovery_benchmark as bench
import relationship_discovery_closeout as closeout

DISPOSITIONS_CONTRACT = "reasoning-distiller-relationship-steward-dispositions/1"
A0_ALGORITHM_ID = "A0-exhaustive/1"
RELATION_TYPES = ("supports", "depends_on", "supersedes", "contradicts")
RECONCILIATION_SCOPE = "semantic_reconciliation"
RECOMMEND = "RECOMMEND"
REJECT = "DO_NOT_RECOMMEND"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bench.canonical_json_bytes(value) + b"\n")


def _digest(value: Any) -> str:
    return bench.sha256_prefixed(bench.canonical_json_bytes(value))


def _activation_digest(activation: dict[str, Any]) -> str:
    # R1/R8 canonical JSON includes one terminal LF in the digested bytes.
    return "sha256:" + hashlib.sha256(bench.canonical_json_bytes(activation) + b"\n").hexdigest()


def _candidate_identity(candidate: dict[str, Any]) -> dict[str, Any]:
    required = {
        "from_record_id",
        "from_record_digest",
        "type",
        "to_record_id",
        "to_record_digest",
        "rationale",
        "source_batch_id",
        "source_result_digest",
    }
    if set(candidate) != required:
        raise ValueError("raw candidate fields do not match A0 aggregate identity")
    return {key: candidate[key] for key in sorted(required)}


def candidate_digest(candidate: dict[str, Any]) -> str:
    return _digest(_candidate_identity(candidate))


def relation_identity(candidate: dict[str, Any]) -> dict[str, str]:
    return {
        "from_record_id": candidate["from_record_id"],
        "type": candidate["type"],
        "to_record_id": candidate["to_record_id"],
    }


def aggregate_raw_candidates(
    candidates: dict[str, Any],
    *,
    result_dir: Path,
) -> list[dict[str, Any]]:
    """Reconstruct the exact candidate list bound by candidates.json."""
    if candidates.get("contract") != closeout.CANDIDATES_CONTRACT:
        raise ValueError("unsupported relationship candidate-set contract")
    if candidates.get("algorithm_id") != A0_ALGORITHM_ID:
        raise ValueError("unexpected A0 algorithm identity")
    source_results = candidates.get("source_results")
    if not isinstance(source_results, list):
        raise ValueError("candidate-set source_results must be an array")

    relations: list[dict[str, Any]] = []
    for item in source_results:
        if not isinstance(item, dict):
            raise ValueError("candidate-set source result entries must be objects")
        batch_id = item.get("batch_id")
        if not isinstance(batch_id, str) or not batch_id:
            raise ValueError("candidate-set batch_id must be a non-empty string")
        result_path = result_dir / f"{batch_id}.result.json"
        if not result_path.is_file():
            raise ValueError(f"missing persisted A0 result {batch_id}")
        result = _load(result_path)
        result_digest = result.get("result_digest")
        unsigned = dict(result)
        unsigned.pop("result_digest", None)
        if result_digest != _digest(unsigned):
            raise ValueError(f"{batch_id} result_digest mismatch")
        if result_digest != item.get("result_digest"):
            raise ValueError(f"{batch_id} source-result digest mismatch")
        raw = result.get("candidate_relations")
        if not isinstance(raw, list):
            raise ValueError(f"{batch_id} candidate_relations must be an array")
        if len(raw) != item.get("candidate_relation_count"):
            raise ValueError(f"{batch_id} candidate relation count mismatch")
        for relation in raw:
            if not isinstance(relation, dict):
                raise ValueError(f"{batch_id} candidate relation must be an object")
            candidate = dict(relation)
            candidate["source_batch_id"] = batch_id
            candidate["source_result_digest"] = result_digest
            relations.append(_candidate_identity(candidate))

    relations.sort(
        key=lambda relation: (
            relation["from_record_id"],
            relation["type"],
            relation["to_record_id"],
            relation["source_batch_id"],
        )
    )
    if len(relations) != candidates.get("candidate_relation_count"):
        raise ValueError("aggregate candidate relation count mismatch")
    if _digest(relations) != candidates.get("candidate_relations_digest"):
        raise ValueError("aggregate candidate_relations_digest mismatch")
    return relations


def _validate_activation_binding(
    activation: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    if activation.get("contract") != "reasoning-distiller-role-activation/1":
        raise ValueError("unsupported activation contract")
    if activation.get("method") != "explicit_declaration":
        raise ValueError("unsupported activation method")
    context = activation.get("context")
    if not isinstance(context, dict):
        raise ValueError("activation context must be an object")
    expected = {
        "scope": RECONCILIATION_SCOPE,
        "role_id": activation.get("role_id"),
        "invocation_id": context.get("invocation_id"),
        "activation_digest": _activation_digest(activation),
    }
    if payload.get("activation") != expected:
        raise ValueError("disposition activation binding mismatch")


def _validate_assessment(value: Any, path: str) -> str:
    if not isinstance(value, dict) or set(value) != {
        "semantic_status",
        "admission_recommendation",
        "rationale",
    }:
        raise ValueError(f"{path} assessment fields do not match R12 semantics")
    rationale = value.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError(f"{path}.rationale must be a non-empty string")
    pair = (value.get("semantic_status"), value.get("admission_recommendation"))
    if pair == ("COMPATIBLE", RECOMMEND):
        return RECOMMEND
    if pair == ("INCOMPATIBLE", REJECT):
        return REJECT
    raise ValueError(
        f"{path} must be final COMPATIBLE/RECOMMEND or "
        "INCOMPATIBLE/DO_NOT_RECOMMEND for the complete A0 baseline"
    )


def _unsigned_disposition_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned = copy.deepcopy(payload)
    unsigned.pop("dispositions_digest", None)
    return unsigned


def dispositions_digest(payload: dict[str, Any]) -> str:
    return _digest(_unsigned_disposition_payload(payload))


def validate_dispositions(
    payload: dict[str, Any],
    *,
    candidates: dict[str, Any],
    raw_candidates: list[dict[str, Any]],
    activation: dict[str, Any],
) -> list[dict[str, str]]:
    required = {
        "contract",
        "benchmark_id",
        "algorithm_id",
        "pems_sha256",
        "candidate_set_digest",
        "candidate_relations_digest",
        "activation",
        "reviewed_candidate_count",
        "dispositions",
        "counts_by_relation_type",
        "recommended_relation_count",
        "recommended_relations_digest",
        "dispositions_digest",
    }
    if set(payload) != required:
        raise ValueError("Steward disposition bundle fields do not match contract")
    if payload.get("contract") != DISPOSITIONS_CONTRACT:
        raise ValueError("unsupported Steward disposition contract")
    for field in (
        "benchmark_id",
        "algorithm_id",
        "pems_sha256",
        "candidate_set_digest",
        "candidate_relations_digest",
    ):
        if payload.get(field) != candidates.get(field):
            raise ValueError(f"Steward disposition {field} mismatch")
    if payload.get("algorithm_id") != A0_ALGORITHM_ID:
        raise ValueError("unexpected A0 algorithm identity")
    _validate_activation_binding(activation, payload)

    dispositions = payload.get("dispositions")
    if not isinstance(dispositions, list):
        raise ValueError("dispositions must be an array")
    if len(dispositions) != len(raw_candidates):
        raise ValueError("dispositions must cover every raw candidate exactly once")
    if payload.get("reviewed_candidate_count") != len(raw_candidates):
        raise ValueError("reviewed_candidate_count mismatch")

    expected = {candidate_digest(candidate): candidate for candidate in raw_candidates}
    if len(expected) != len(raw_candidates):
        raise ValueError("raw candidate identities are not unique")
    seen: set[str] = set()
    recommended: list[dict[str, str]] = []
    counts = {
        relation_type: {"recommended": 0, "rejected": 0}
        for relation_type in RELATION_TYPES
    }

    for index, disposition in enumerate(dispositions):
        path = f"dispositions[{index}]"
        if not isinstance(disposition, dict) or set(disposition) != {
            "candidate_digest",
            "relation",
            "assessment",
        }:
            raise ValueError(f"{path} fields do not match contract")
        bound_digest = disposition.get("candidate_digest")
        if bound_digest in seen:
            raise ValueError(f"{path} duplicates a candidate")
        candidate = expected.get(bound_digest)
        if candidate is None:
            raise ValueError(f"{path} references an unknown candidate")
        seen.add(bound_digest)
        relation = relation_identity(candidate)
        if disposition.get("relation") != relation:
            raise ValueError(f"{path}.relation does not match its candidate")
        recommendation = _validate_assessment(disposition.get("assessment"), path)
        relation_type = relation["type"]
        if recommendation == RECOMMEND:
            recommended.append(relation)
            counts[relation_type]["recommended"] += 1
        else:
            counts[relation_type]["rejected"] += 1

    if seen != set(expected):
        raise ValueError("dispositions do not exactly cover the raw candidate set")
    recommended.sort(
        key=lambda relation: (
            relation["from_record_id"],
            relation["type"],
            relation["to_record_id"],
        )
    )
    if payload.get("counts_by_relation_type") != counts:
        raise ValueError("counts_by_relation_type mismatch")
    if payload.get("recommended_relation_count") != len(recommended):
        raise ValueError("recommended_relation_count mismatch")
    if payload.get("recommended_relations_digest") != _digest(recommended):
        raise ValueError("recommended_relations_digest mismatch")
    if payload.get("dispositions_digest") != dispositions_digest(payload):
        raise ValueError("dispositions_digest mismatch")
    return recommended


def finalize_report(
    report: dict[str, Any],
    *,
    dispositions: dict[str, Any],
) -> dict[str, Any]:
    """Return the completed A0 report for a fully validated Steward bundle."""
    bench.validate_report(report)
    if report["identity"]["algorithm_id"] != "A0-exhaustive":
        raise ValueError("unexpected report algorithm identity")
    completed = copy.deepcopy(report)
    baseline_count = dispositions["recommended_relation_count"]
    metrics = completed["metrics"]
    metrics["baseline_relations"] = {"status": "measured", "value": baseline_count}
    metrics["baseline_relations_covered"] = {"status": "derived", "value": baseline_count}
    metrics["baseline_relations_missed"] = {"status": "derived", "value": 0}
    metrics["baseline_recall_percent"] = {
        "status": "derived",
        "value": 100.0,
        "unit": "%",
    }
    completed["misses"] = []
    completed["verdict"] = "PASS"
    notes = [
        note
        for note in completed.get("notes", [])
        if "pending fresh Steward semantic reconciliation" not in note
    ]
    notes.append(
        "Fresh Steward semantic reconciliation reviewed all "
        f"{dispositions['reviewed_candidate_count']} raw A0 candidates and established "
        f"{baseline_count} approved exhaustive baseline relations."
    )
    notes.append(
        "This reconciliation is non-admitting; canonical PEMS/COVE state remains unchanged "
        "until a separately activated admission invocation."
    )
    completed["notes"] = notes
    bench.validate_report(completed)
    return completed


def validate_bundle(
    *,
    candidates_path: Path,
    result_dir: Path,
    activation_path: Path,
    dispositions_path: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    candidates = _load(candidates_path)
    raw_candidates = aggregate_raw_candidates(candidates, result_dir=result_dir)
    activation = _load(activation_path)
    payload = _load(dispositions_path)
    recommended = validate_dispositions(
        payload,
        candidates=candidates,
        raw_candidates=raw_candidates,
        activation=activation,
    )
    return payload, recommended


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--candidates", type=Path, required=True)
    validate.add_argument("--result-dir", type=Path, required=True)
    validate.add_argument("--activation", type=Path, required=True)
    validate.add_argument("--dispositions", type=Path, required=True)

    complete = sub.add_parser("complete-report")
    complete.add_argument("--report", type=Path, required=True)
    complete.add_argument("--dispositions", type=Path, required=True)
    complete.add_argument("--out-json", type=Path, required=True)
    complete.add_argument("--out-md", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "validate":
        payload, recommended = validate_bundle(
            candidates_path=args.candidates,
            result_dir=args.result_dir,
            activation_path=args.activation,
            dispositions_path=args.dispositions,
        )
        print(
            "PASS A0 Steward reconciliation: "
            f"{payload['reviewed_candidate_count']} reviewed, "
            f"{len(recommended)} recommended, "
            f"{payload['reviewed_candidate_count'] - len(recommended)} rejected"
        )
        return 0

    if args.command == "complete-report":
        report = _load(args.report)
        dispositions = _load(args.dispositions)
        completed = finalize_report(report, dispositions=dispositions)
        _write_json(args.out_json, completed)
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(bench.render_report(completed), encoding="utf-8")
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
