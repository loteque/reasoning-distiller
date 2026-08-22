#!/usr/bin/env python3
"""Materialize the already-reconciled A0 relationship baseline through R12/R13.

This module makes no new semantic relationship judgment. It projects the
immutable A0 Steward reconciliation into the standard R12 candidate/disposition
shape, then admits exactly the already-approved relations through R13.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVALUATION = ROOT / "evaluation"
RUNTIME = ROOT / "runtime"
sys.path.insert(0, str(EVALUATION))
sys.path.insert(0, str(RUNTIME))

import relationship_discovery_reconciliation as recon  # noqa: E402
from ril_activation import make_explicit_activation, validate_activation  # noqa: E402
from ril_admission import (  # noqa: E402
    PLAN_CONTRACT,
    _decode,
    admit,
    jcs,
    normalize_pems,
    sha256_bytes,
)
from ril_mutation import canonical_json_bytes, digest, load_json  # noqa: E402
from ril_reconciliation import (  # noqa: E402
    ASSESSMENT_CONTRACT,
    reconcile_candidate,
)

BASE = EVALUATION / "relationship-discovery" / "benchmark-v1" / "baseline" / "A0-exhaustive"
CANDIDATES_PATH = BASE / "candidates.json"
RESULT_DIR = BASE / "batches"
STEWARDSHIP_PATH = BASE / "steward-dispositions.json"
RECONCILIATION_ACTIVATION_PATH = (
    ROOT
    / "project-knowledge"
    / "reconciliation"
    / "activation-evidence"
    / "a81360a9a4ab349a377dd378b5ed55e7e4a28d45ca26f6de51888dfac477928b.json"
)
MANIFEST_PATH = BASE / "admission-manifest.json"

CANDIDATE_CONTRACT = "reasoning-distiller-relationship-a0-admission-candidate/1"
MANIFEST_CONTRACT = "reasoning-distiller-relationship-a0-admission-manifest/1"
EXPECTED_RECOMMENDED_COUNT = 668
EXPECTED_RECOMMENDED_DIGEST = "sha256:ab07f98f8e280a7008d60b12b31e0376eec3ea761b70979ffae32a39482b8efd"
EXPECTED_STEWARD_DISPOSITIONS_DIGEST = "sha256:6120a78291d48d4cda586dc7bbf6cb6fc2cff1e38f8373ad4c1c67a4b2ddbcd1"
EXPECTED_CANDIDATE_SET_DIGEST = "sha256:b4a19d54c0ed9fdd0768b3e5b70135829f65943aaaf1bdb7bf4c487a156fb892"
EXPECTED_CANDIDATE_RELATIONS_DIGEST = "sha256:e1a89418c1723d2fdf7cfd34f3fa13b49dc6b2eec4cc0829acf15c50ef8289bb"
EXPECTED_BASE_PEMS_SHA256 = "217eaedc614420a904b1ccc637b46a7cefce5c4b54b98ae9d39615ad1af5be0e"
EXPECTED_BASE_COVE_SHA256 = "3e7326f1a1c6e35bc9c615f92ff9808922fff7a02609e0e3569f6042522b5925"
EXPECTED_RECORD_COUNT = 802
EXPECTED_KIND_COUNTS = {"supports": 661, "depends_on": 7}

ADMISSION_ROLE_ID = "steward:default"
ADMISSION_INVOCATION_ID = "admit-relationship-discovery-a0-v1-20260821"
ADMISSION_SOURCE = (
    "Activate steward:default for admission in invocation "
    "admit-relationship-discovery-a0-v1-20260821."
)
EXPECTED_ADMISSION_ACTIVATION_DIGEST = (
    "sha256:4cd950d09846ea811c18487fb07e1c164b2fc2da32f59d512f5261914fd7bb8d"
)

PROJECTION_RATIONALE = (
    "Deterministic standard-contract projection of the already-final A0 Steward "
    "reconciliation; no new semantic judgment."
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _persist_immutable(path: Path, value: dict[str, Any]) -> None:
    data = canonical_json_bytes(value)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ValueError(f"immutable artifact conflict: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _relation_set_digest(relations: list[dict[str, str]]) -> str:
    ordered = sorted(
        relations,
        key=lambda item: (item["from_record_id"], item["type"], item["to_record_id"]),
    )
    return recon.bench.sha256_prefixed(recon.bench.canonical_json_bytes(ordered))


def _record_set_digest(records: list[dict[str, Any]]) -> str:
    return digest(sorted(copy.deepcopy(records), key=lambda record: record["id"]))


def _load_approved_relations() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    candidates = _load(CANDIDATES_PATH)
    stewardship, recommended = recon.validate_bundle(
        candidates_path=CANDIDATES_PATH,
        result_dir=RESULT_DIR,
        activation_path=RECONCILIATION_ACTIVATION_PATH,
        dispositions_path=STEWARDSHIP_PATH,
    )
    if candidates.get("candidate_set_digest") != EXPECTED_CANDIDATE_SET_DIGEST:
        raise ValueError("A0 candidate-set digest changed")
    if candidates.get("candidate_relations_digest") != EXPECTED_CANDIDATE_RELATIONS_DIGEST:
        raise ValueError("A0 aggregate candidate-relations digest changed")
    if candidates.get("pems_sha256") != f"sha256:{EXPECTED_BASE_PEMS_SHA256}":
        raise ValueError("A0 frozen PEMS digest changed")
    if stewardship.get("dispositions_digest") != EXPECTED_STEWARD_DISPOSITIONS_DIGEST:
        raise ValueError("A0 Steward disposition digest changed")
    if stewardship.get("recommended_relation_count") != EXPECTED_RECOMMENDED_COUNT:
        raise ValueError("A0 approved relation count changed")
    if stewardship.get("recommended_relations_digest") != EXPECTED_RECOMMENDED_DIGEST:
        raise ValueError("A0 approved relation-set digest changed")
    if len(recommended) != EXPECTED_RECOMMENDED_COUNT:
        raise ValueError("validated A0 approved relation count changed")
    if _relation_set_digest(recommended) != EXPECTED_RECOMMENDED_DIGEST:
        raise ValueError("validated A0 approved relation identities changed")
    return candidates, stewardship, recommended


def build_standard_candidate(
    pems: dict[str, Any],
    candidates: dict[str, Any],
    stewardship: dict[str, Any],
    recommended: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "contract": CANDIDATE_CONTRACT,
        "benchmark_id": candidates["benchmark_id"],
        "algorithm_id": candidates["algorithm_id"],
        "source_pems_sha256": candidates["pems_sha256"],
        "source_cove_sha256": f"sha256:{EXPECTED_BASE_COVE_SHA256}",
        "source_record_count": len(pems["records"]),
        "source_records_digest": _record_set_digest(pems["records"]),
        "candidate_set_digest": candidates["candidate_set_digest"],
        "candidate_relations_digest": candidates["candidate_relations_digest"],
        "steward_dispositions_digest": stewardship["dispositions_digest"],
        "recommended_relation_count": stewardship["recommended_relation_count"],
        "recommended_relations_digest": stewardship["recommended_relations_digest"],
        "approved_relations": copy.deepcopy(recommended),
    }


def relation_id(relation: dict[str, str]) -> str:
    identity = {
        "from": relation["from_record_id"],
        "kind": relation["type"],
        "to": relation["to_record_id"],
    }
    relation_hash = hashlib.sha256(recon.bench.canonical_json_bytes(identity)).hexdigest()
    return f"relation:a0:{relation_hash}"


def build_pems_relations(recommended: list[dict[str, str]]) -> list[dict[str, str]]:
    relations = [
        {
            "id": relation_id(relation),
            "from": relation["from_record_id"],
            "kind": relation["type"],
            "to": relation["to_record_id"],
        }
        for relation in recommended
    ]
    if len({relation["id"] for relation in relations}) != len(relations):
        raise ValueError("deterministic relation ID collision")
    return relations


def _validate_admitted_state(
    *,
    candidate: dict[str, Any],
    recommended: list[dict[str, str]],
) -> dict[str, Any]:
    pems_path = ROOT / "project-knowledge" / "canonical" / "pems2.jcs.json"
    cove_path = ROOT / "project-knowledge" / "canonical" / "cove1.jcs.json"
    pems = normalize_pems(_load(pems_path))
    cove = _load(cove_path)

    if len(pems["records"]) != EXPECTED_RECORD_COUNT:
        raise ValueError("admission changed the PEMS record count")
    if _record_set_digest(pems["records"]) != candidate["source_records_digest"]:
        raise ValueError("admission changed existing PEMS records")
    if len(pems["relations"]) != EXPECTED_RECOMMENDED_COUNT:
        raise ValueError("admitted relation count mismatch")
    for relation in pems["relations"]:
        if set(relation) != {"id", "from", "kind", "to"}:
            raise ValueError("admitted PEMS relation shape changed")

    projected = [
        {
            "from_record_id": relation["from"],
            "type": relation["kind"],
            "to_record_id": relation["to"],
        }
        for relation in pems["relations"]
    ]
    if _relation_set_digest(projected) != EXPECTED_RECOMMENDED_DIGEST:
        raise ValueError("Canon relation set differs from the approved A0 baseline")
    if sorted(projected, key=lambda x: (x["from_record_id"], x["type"], x["to_record_id"])) != recommended:
        raise ValueError("Canon contains a relation outside the approved A0 baseline")
    counts = dict(sorted(Counter(relation["kind"] for relation in pems["relations"]).items()))
    if counts != EXPECTED_KIND_COUNTS:
        raise ValueError("admitted relation kind counts changed")
    if _decode(cove["x"], cove["d"], cove["h"]) != pems:
        raise ValueError("COVE does not round-trip to admitted PEMS")

    return {
        "record_count": len(pems["records"]),
        "relation_count": len(pems["relations"]),
        "counts_by_relation_type": counts,
        "recommended_relations_digest": _relation_set_digest(projected),
        "admitted_pems_sha256": sha256_bytes(pems_path.read_bytes()),
        "admitted_cove_sha256": sha256_bytes(cove_path.read_bytes()),
    }


def materialize() -> dict[str, Any]:
    candidates, stewardship, recommended = _load_approved_relations()
    pems_path = ROOT / "project-knowledge" / "canonical" / "pems2.jcs.json"
    cove_path = ROOT / "project-knowledge" / "canonical" / "cove1.jcs.json"
    current_pems = normalize_pems(_load(pems_path))
    if len(current_pems["records"]) != EXPECTED_RECORD_COUNT:
        raise ValueError("unexpected pre-admission PEMS record count")

    candidate = build_standard_candidate(current_pems, candidates, stewardship, recommended)
    candidate_digest = digest(candidate)
    candidate_path = ROOT / "project-knowledge" / "submissions" / f"{candidate_digest.split(':', 1)[1]}.json"
    _persist_immutable(candidate_path, candidate)

    reconciliation_activation = _load(RECONCILIATION_ACTIVATION_PATH)
    reconciliation_result = validate_activation(ROOT, "semantic_reconciliation", reconciliation_activation)
    if reconciliation_result.get("status") != "PASS":
        raise ValueError(f"historical reconciliation activation rejected: {reconciliation_result}")
    assessment = {
        "contract": ASSESSMENT_CONTRACT,
        "semantic_status": "COMPATIBLE",
        "admission_recommendation": "RECOMMEND",
        "rationale": PROJECTION_RATIONALE,
    }
    reconciliation = reconcile_candidate(ROOT, candidate_path, reconciliation_activation, assessment)
    if reconciliation.get("status") != "PASS" or reconciliation.get("outcome") not in {"RECONCILED", "NO_CHANGE"}:
        raise ValueError(f"standard reconciliation projection failed: {reconciliation}")
    disposition_path = ROOT / reconciliation["disposition_path"]
    disposition = _load(disposition_path)

    admission_activation = make_explicit_activation(
        ADMISSION_ROLE_ID,
        ADMISSION_INVOCATION_ID,
        ADMISSION_SOURCE,
    )
    if digest(admission_activation) != EXPECTED_ADMISSION_ACTIVATION_DIGEST:
        raise ValueError("admission activation digest mismatch")
    activation_result = validate_activation(ROOT, "admission", admission_activation)
    if activation_result.get("status") != "PASS":
        raise ValueError(f"admission activation rejected: {activation_result}")

    receipt_path = (
        ROOT
        / "project-knowledge"
        / "admission"
        / "receipts"
        / f"{candidate_digest.split(':', 1)[1]}.json"
    )
    before_records = copy.deepcopy(current_pems["records"])

    if receipt_path.exists():
        receipt = _load(receipt_path)
        plan_path = (
            ROOT
            / "project-knowledge"
            / "admission"
            / "plans"
            / f"{receipt['plan_digest'].split(':', 1)[1]}.json"
        )
        plan = _load(plan_path)
    else:
        if _sha256(pems_path) != EXPECTED_BASE_PEMS_SHA256:
            raise ValueError("live PEMS does not match the frozen pre-admission base")
        if _sha256(cove_path) != EXPECTED_BASE_COVE_SHA256:
            raise ValueError("live COVE does not match the frozen pre-admission base")
        if current_pems["relations"]:
            raise ValueError("pre-admission PEMS already contains relations")
        plan = {
            "contract": PLAN_CONTRACT,
            "expected_base_sha256": sha256_bytes(jcs(current_pems)),
            "reuse_record_ids": [],
            "record_updates": [],
            "new_records": [],
            "new_relations": build_pems_relations(recommended),
        }

    admission = admit(ROOT, disposition_path, admission_activation, plan)
    if admission.get("status") != "PASS" or admission.get("outcome") not in {"ADMITTED", "NO_CHANGE"}:
        raise ValueError(f"R13 admission failed: {admission}")

    admitted_pems = normalize_pems(_load(pems_path))
    if before_records != admitted_pems["records"]:
        raise ValueError("R13 changed an existing PEMS record")
    state = _validate_admitted_state(candidate=candidate, recommended=recommended)
    receipt = _load(receipt_path)
    if state["admitted_pems_sha256"] != receipt["admitted_pems_sha256"]:
        raise ValueError("receipt PEMS digest does not match Canon")
    if state["admitted_cove_sha256"] != receipt["admitted_cove_sha256"]:
        raise ValueError("receipt COVE digest does not match Canon")

    manifest = {
        "contract": MANIFEST_CONTRACT,
        "candidate_digest": candidate_digest,
        "disposition_digest": digest(disposition),
        "admission_activation_digest": digest(admission_activation),
        "plan_digest": digest(plan),
        "receipt_path": receipt_path.relative_to(ROOT).as_posix(),
        "base_pems_sha256": receipt["base_pems_sha256"],
        "admitted_pems_sha256": receipt["admitted_pems_sha256"],
        "admitted_cove_sha256": receipt["admitted_cove_sha256"],
        "record_count": state["record_count"],
        "relation_count": state["relation_count"],
        "counts_by_relation_type": state["counts_by_relation_type"],
        "recommended_relations_digest": state["recommended_relations_digest"],
        "source_records_digest": candidate["source_records_digest"],
        "source_candidate_set_digest": candidates["candidate_set_digest"],
        "source_candidate_relations_digest": candidates["candidate_relations_digest"],
        "source_steward_dispositions_digest": stewardship["dispositions_digest"],
    }
    _persist_immutable(MANIFEST_PATH, manifest)
    return manifest


def validate_materialized() -> dict[str, Any]:
    manifest = _load(MANIFEST_PATH)
    if manifest.get("contract") != MANIFEST_CONTRACT:
        raise ValueError("unsupported A0 admission manifest")
    candidates, stewardship, recommended = _load_approved_relations()
    pems = normalize_pems(_load(ROOT / "project-knowledge/canonical/pems2.jcs.json"))
    candidate = build_standard_candidate(pems, candidates, stewardship, recommended)
    if digest(candidate) != manifest.get("candidate_digest"):
        raise ValueError("admission candidate digest mismatch")
    candidate_path = ROOT / "project-knowledge/submissions" / f"{manifest['candidate_digest'].split(':', 1)[1]}.json"
    if _load(candidate_path) != candidate:
        raise ValueError("persisted admission candidate mismatch")
    disposition_path = ROOT / "project-knowledge/reconciliation/dispositions" / f"{manifest['candidate_digest'].split(':', 1)[1]}.json"
    disposition = _load(disposition_path)
    if digest(disposition) != manifest.get("disposition_digest"):
        raise ValueError("standard disposition digest mismatch")
    receipt = _load(ROOT / manifest["receipt_path"])
    if receipt.get("plan_digest") != manifest.get("plan_digest"):
        raise ValueError("receipt plan digest mismatch")
    plan_path = ROOT / "project-knowledge/admission/plans" / f"{manifest['plan_digest'].split(':', 1)[1]}.json"
    plan = _load(plan_path)
    if digest(plan) != manifest["plan_digest"]:
        raise ValueError("admission plan digest mismatch")
    if plan["new_records"] or plan["record_updates"] or plan["reuse_record_ids"]:
        raise ValueError("A0 relationship admission must not mutate records")
    if len(plan["new_relations"]) != EXPECTED_RECOMMENDED_COUNT:
        raise ValueError("A0 admission plan relation count mismatch")
    state = _validate_admitted_state(candidate=candidate, recommended=recommended)
    for key in ("record_count", "relation_count", "counts_by_relation_type", "recommended_relations_digest", "admitted_pems_sha256", "admitted_cove_sha256"):
        if manifest.get(key) != state[key]:
            raise ValueError(f"admission manifest {key} mismatch")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("materialize", "validate"))
    args = parser.parse_args()
    result = materialize() if args.command == "materialize" else validate_materialized()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
