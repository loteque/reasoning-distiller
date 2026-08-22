#!/usr/bin/env python3
"""Materialize expanded A0 Steward dispositions from immutable selection evidence."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import relationship_discovery_reconciliation as recon

SELECTION_CONTRACT = "reasoning-distiller-relationship-steward-selection/1"
ORDERING = "lexicographic_from_type_to_source_batch"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _selection_digest(selection: dict[str, Any]) -> str:
    unsigned = copy.deepcopy(selection)
    unsigned.pop("selection_digest", None)
    return recon._digest(unsigned)


def validate_selection(
    selection: dict[str, Any],
    *,
    candidates: dict[str, Any],
    raw_candidates: list[dict[str, Any]],
    activation: dict[str, Any],
) -> list[bool]:
    required = {
        "contract",
        "benchmark_id",
        "algorithm_id",
        "candidate_set_digest",
        "candidate_relations_digest",
        "candidate_order",
        "candidate_order_digest",
        "activation_digest",
        "reviewed_candidate_count",
        "decision_encoding",
        "decisions",
        "rationale_policy",
        "selection_digest",
    }
    if set(selection) != required:
        raise ValueError("Steward selection fields do not match contract")
    if selection["contract"] != SELECTION_CONTRACT:
        raise ValueError("unsupported Steward selection contract")
    for field in (
        "benchmark_id",
        "algorithm_id",
        "candidate_set_digest",
        "candidate_relations_digest",
    ):
        if selection[field] != candidates[field]:
            raise ValueError(f"Steward selection {field} mismatch")
    if selection["candidate_order"] != ORDERING:
        raise ValueError("unsupported candidate ordering")
    expected_digests = [recon.candidate_digest(candidate) for candidate in raw_candidates]
    if selection["candidate_order_digest"] != recon._digest(expected_digests):
        raise ValueError("candidate_order_digest mismatch")
    if selection["activation_digest"] != recon._activation_digest(activation):
        raise ValueError("activation_digest mismatch")
    if selection["reviewed_candidate_count"] != len(raw_candidates):
        raise ValueError("reviewed_candidate_count mismatch")
    if selection["decision_encoding"] != {
        "R": "COMPATIBLE/RECOMMEND",
        "X": "INCOMPATIBLE/DO_NOT_RECOMMEND",
    }:
        raise ValueError("decision_encoding mismatch")
    policy = selection["rationale_policy"]
    if not isinstance(policy, dict) or set(policy) != {"R", "X"}:
        raise ValueError("rationale_policy must contain exactly R and X")
    for key in ("R", "X"):
        if not isinstance(policy[key], str) or not policy[key].strip():
            raise ValueError(f"rationale_policy.{key} must be non-empty")
    decisions = selection["decisions"]
    if not isinstance(decisions, str) or len(decisions) != len(raw_candidates):
        raise ValueError("decisions must contain exactly one code per raw candidate")
    if set(decisions) - {"R", "X"}:
        raise ValueError("decisions contains an unknown code")
    if selection["selection_digest"] != _selection_digest(selection):
        raise ValueError("selection_digest mismatch")
    return [code == "R" for code in decisions]


def build_dispositions(
    *,
    candidates: dict[str, Any],
    raw_candidates: list[dict[str, Any]],
    activation: dict[str, Any],
    selection: dict[str, Any],
) -> dict[str, Any]:
    decisions = validate_selection(
        selection,
        candidates=candidates,
        raw_candidates=raw_candidates,
        activation=activation,
    )
    rows: list[dict[str, Any]] = []
    recommended: list[dict[str, str]] = []
    counts = {
        relation_type: {"recommended": 0, "rejected": 0}
        for relation_type in recon.RELATION_TYPES
    }
    policy = selection["rationale_policy"]
    for candidate, recommend in zip(raw_candidates, decisions, strict=True):
        relation = recon.relation_identity(candidate)
        code = "R" if recommend else "X"
        assessment = {
            "semantic_status": "COMPATIBLE" if recommend else "INCOMPATIBLE",
            "admission_recommendation": recon.RECOMMEND if recommend else recon.REJECT,
            "rationale": policy[code],
        }
        rows.append(
            {
                "candidate_digest": recon.candidate_digest(candidate),
                "relation": relation,
                "assessment": assessment,
            }
        )
        if recommend:
            recommended.append(relation)
            counts[relation["type"]]["recommended"] += 1
        else:
            counts[relation["type"]]["rejected"] += 1
    rows.sort(
        key=lambda item: (
            item["relation"]["from_record_id"],
            item["relation"]["type"],
            item["relation"]["to_record_id"],
            item["candidate_digest"],
        )
    )
    recommended.sort(
        key=lambda relation: (
            relation["from_record_id"],
            relation["type"],
            relation["to_record_id"],
        )
    )
    context = activation["context"]
    payload: dict[str, Any] = {
        "contract": recon.DISPOSITIONS_CONTRACT,
        "benchmark_id": candidates["benchmark_id"],
        "algorithm_id": candidates["algorithm_id"],
        "pems_sha256": candidates["pems_sha256"],
        "candidate_set_digest": candidates["candidate_set_digest"],
        "candidate_relations_digest": candidates["candidate_relations_digest"],
        "activation": {
            "scope": recon.RECONCILIATION_SCOPE,
            "role_id": activation["role_id"],
            "invocation_id": context["invocation_id"],
            "activation_digest": recon._activation_digest(activation),
        },
        "reviewed_candidate_count": len(raw_candidates),
        "dispositions": rows,
        "counts_by_relation_type": counts,
        "recommended_relation_count": len(recommended),
        "recommended_relations_digest": recon._digest(recommended),
    }
    payload["dispositions_digest"] = recon.dispositions_digest(payload)
    recon.validate_dispositions(
        payload,
        candidates=candidates,
        raw_candidates=raw_candidates,
        activation=activation,
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--activation", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    candidates = _load(args.candidates)
    raw_candidates = recon.aggregate_raw_candidates(candidates, result_dir=args.result_dir)
    activation = _load(args.activation)
    selection = _load(args.selection)
    payload = build_dispositions(
        candidates=candidates,
        raw_candidates=raw_candidates,
        activation=activation,
        selection=selection,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(recon.bench.canonical_json_bytes(payload) + b"\n")
    print(
        "PASS materialized A0 Steward dispositions: "
        f"{payload['reviewed_candidate_count']} reviewed, "
        f"{payload['recommended_relation_count']} recommended"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
