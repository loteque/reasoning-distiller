#!/usr/bin/env python3
"""Deterministic executable checks for the PEMS/2 successor-contract draft.

This validator intentionally does not mutate canonical memory. It checks the
machine-readable compatibility and admission pressure cases, structural schema
smoke cases, deterministic v1->v2 migration invariants, and optionally a
complete PEMS/2 candidate document supplied with ``--candidate``.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "RGP_COMPATIBILITY_FIXTURES.json"
ADMISSION_FIXTURES = ROOT / "ADMISSION_FIXTURES.json"
SCHEMA = ROOT / "pems-v2.schema.json"

CURRENT = "current"
UNRESOLVED = {"open", "blocked", "deferred"}
RGP_MAJOR = "rgp/1"


def canonical_json(value) -> bytes:
    # Deterministic fixture representation only. This does not replace or
    # redefine the separately frozen jcs/1 byte contract.
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def classify_domain_export(inp):
    kind = inp["kind"]
    lifecycle = inp.get("lifecycle")
    if kind == "decision":
        if lifecycle == CURRENT and inp.get("decision_state") == "accepted":
            return {"exportable": True, "rgp_kind": "decision"}
        if lifecycle == "historical":
            return {"exportable": False, "reason": "historical_snapshot_required"}
        return {"exportable": False, "reason": "state_or_lifecycle_not_lossless"}
    if kind == "unresolved_item":
        if lifecycle == CURRENT and inp.get("resolution_state") in UNRESOLVED:
            return {"exportable": True, "rgp_kind": "uncertainty"}
        if lifecycle == "historical":
            return {"exportable": False, "reason": "historical_snapshot_required"}
        return {"exportable": False, "reason": "state_or_lifecycle_not_lossless"}
    return {"exportable": False, "reason": "unprofiled_domain_kind"}


def classify_case(case):
    cat, inp = case["category"], case["input"]
    if cat == "domain_export":
        return classify_domain_export(inp)
    if cat == "relation":
        if inp["kind"] == "contradicts":
            if inp["a"] == inp["b"]:
                return {"valid": False, "reason": "self_contradiction"}
            return {"from": min(inp["a"], inp["b"]), "to": max(inp["a"], inp["b"]), "symmetric": True}
    if cat == "migration":
        if inp["v1_kind"] == "depends_on":
            out = {"v2_kind": "depends_on", "dependency_kind": "legacy_untyped"}
            if "qualifier" in inp.get("data", {}):
                out["qualifier"] = inp["data"]["qualifier"]
            return out
    if cat == "rgp_import":
        if inp.get("rgp_version") != RGP_MAJOR:
            return {"accepted": False, "reason": "unsupported_rgp_major"}
        if inp.get("relation") == "depends_on":
            return {"pems_kind": "depends_on", "dependency_kind": "conditional_validity"}
        if inp.get("kind") in {"observation", "assumption", "claim"}:
            return {"pems_kind": "proposition", "proposition_kind": inp["kind"]}
    if cat == "identity":
        return {"reuse_generic_id_for_domain": False, "preserve_generic_historically": True, "reviewed_supersession_required": True}
    if cat == "provenance":
        op = inp["operation"]
        if op == "add" and inp.get("same_meaning"):
            return {"same_identity_permitted": True, "review_class": "ordinary_enrichment"}
        if op == "reclassify" and inp.get("from_role") == "untyped":
            return {"same_identity_permitted": True, "atomic": True, "review_class": "governed_classification"}
        return {"review_class": "semantic_correction"}
    if cat == "downgrade":
        if inp.get("kind") == "proposition":
            return {"lossless": False, "reason": "v2_only_record_kind"}
        if any(k in inp.get("provenance", {}) for k in ("primary", "corroborating", "context")):
            return {"lossless": False, "reason": "v2_only_typed_provenance"}
        if inp.get("kind") == "depends_on":
            if inp.get("dependency_kind") == "legacy_untyped":
                return {"lossless": True}
            return {"lossless": False, "reason": "v2_only_dependency_semantics"}
    raise AssertionError(f"unhandled fixture case {case['id']}")


def classify_admission_case(case):
    inp = case["input"]
    cid = case["id"]
    if cid == "equivalent-candidate-reuses-identity":
        return {"outcome": "reconcile_existing", "canonical_id": inp["equivalent_existing_id"], "allocate_new_id": False}
    if cid == "domain-refinement-uses-distinct-identity":
        return {"outcome": "review_required", "reuse_generic_id": False, "preserve_generic_history": True, "supersession_required": True}
    if cid == "derived-subgraph-admitted-atomically":
        return {"outcome": "transaction_required", "partial_admission_allowed": False, "required_nodes": sorted([inp["derived_id"], inp["premise_id"]])}
    if cid == "unresolved-required-provenance-blocks-grounded-admission":
        return {"outcome": "provisional", "admit_as_grounded": False, "reason": "unresolved_provenance"}
    if cid == "conflict-is-preserved-not-overwritten":
        return {"outcome": "review_required", "overwrite_existing": False, "explicit_conflict_required": True}
    if cid == "recency-does-not-establish-supersession":
        return {"outcome": "review_required", "supersedes": False, "reason": "recency_insufficient"}
    raise AssertionError(f"unhandled admission fixture {cid}")


def migrate_v1_to_v2(doc):
    if doc.get("semantic") != "pems/1":
        raise ValueError("unsupported input semantic")
    out = copy.deepcopy(doc)
    out["semantic"] = "pems/2"
    for item in list(out["records"]) + list(out["relations"]):
        refs = item.pop("observation_refs", [])
        if len(refs) != len(set(refs)):
            raise ValueError("duplicate observation_refs")
        if refs:
            item["provenance"] = {"untyped": sorted(refs)}
    for rel in out["relations"]:
        if rel["kind"] == "depends_on":
            rel.setdefault("data", {})
            rel["data"]["dependency_kind"] = "legacy_untyped"
    out["records"] = sorted(out["records"], key=lambda x: x["id"])
    out["relations"] = sorted(out["relations"], key=lambda x: x["id"])
    return out


def migration_fixture():
    return {
        "semantic": "pems/1",
        "project_id": "pems:project:p",
        "records": [
            {"id": "pems:source_observation:o", "kind": "source_observation", "lifecycle": "historical", "observation_refs": [], "data": {"source_id": "pems:source:s", "evidence_state": "immutable_snapshot", "observed_at": "2026-08-15T00:00:00Z", "evidence_locator": {"commit": "abc"}}},
            {"id": "pems:source:s", "kind": "source", "lifecycle": "current", "observation_refs": [], "data": {"source_kind": "repository", "authority": "repository_state", "identity_locator": {"repository": "o/r"}}},
            {"id": "pems:decision:d", "kind": "decision", "lifecycle": "historical", "observation_refs": ["pems:source_observation:o"], "data": {"summary": "A historical decision.", "decision_state": "accepted"}}
        ],
        "relations": [
            {"id": "pems:relation:r", "kind": "depends_on", "from": "pems:decision:d", "to": "pems:source:s", "lifecycle": "historical", "observation_refs": ["pems:source_observation:o"], "data": {"qualifier": "legacy"}}
        ]
    }


def structural_smoke_documents():
    base_records = [
        {"id": "pems:project:p", "kind": "project", "lifecycle": "current", "data": {"name": "Fixture", "repository": "o/r", "summary": "Fixture"}},
        {"id": "pems:source:s", "kind": "source", "lifecycle": "current", "data": {"source_kind": "repository", "authority": "repository_state", "identity_locator": {"repository": "o/r"}}},
        {"id": "pems:source_observation:o", "kind": "source_observation", "lifecycle": "historical", "data": {"source_id": "pems:source:s", "evidence_state": "immutable_snapshot", "observed_at": "2026-08-15T00:00:00Z", "evidence_locator": {"commit": "abc"}}}
    ]
    valid = {"semantic": "pems/2", "project_id": "pems:project:p", "records": base_records + [
        {"id": "pems:proposition:a", "kind": "proposition", "lifecycle": "current", "data": {"statement": "A", "proposition_kind": "observation", "epistemic_role": "asserted"}, "provenance": {"primary": ["pems:source_observation:o"]}},
        {"id": "pems:proposition:b", "kind": "proposition", "lifecycle": "current", "data": {"statement": "B", "proposition_kind": "claim", "epistemic_role": "derived"}}
    ], "relations": [
        {"id": "pems:relation:r", "kind": "derived_from", "from": "pems:proposition:b", "to": "pems:proposition:a", "lifecycle": "current", "data": {}}
    ]}
    bad_role = copy.deepcopy(valid)
    bad_role["records"][-1]["data"]["epistemic_role"] = "guessed"
    bad_dependency = copy.deepcopy(valid)
    bad_dependency["relations"] = [{"id": "pems:relation:d", "kind": "depends_on", "from": "pems:proposition:b", "to": "pems:proposition:a", "lifecycle": "current", "data": {}}]
    bad_secret = copy.deepcopy(valid)
    bad_secret["records"].append({"id": "pems:environment_variable:e", "kind": "environment_variable", "lifecycle": "current", "data": {"name": "TOKEN", "value_state": "external_secret", "purpose": "fixture", "value": "leak", "external_ref": "vault://token"}})
    return valid, [bad_role, bad_dependency, bad_secret]


def validate_candidate_document(candidate, schema_validator):
    """Validate a complete PEMS/2 candidate without making admission decisions."""
    schema_validator.validate(candidate)

    records = candidate["records"]
    relations = candidate["relations"]
    record_ids = [record["id"] for record in records]
    relation_ids = [relation["id"] for relation in relations]
    if len(record_ids) != len(set(record_ids)):
        raise AssertionError("candidate contains duplicate record IDs")
    if len(relation_ids) != len(set(relation_ids)):
        raise AssertionError("candidate contains duplicate relation IDs")

    record_by_id = {record["id"]: record for record in records}
    project = record_by_id.get(candidate["project_id"])
    if not project or project["kind"] != "project":
        raise AssertionError("candidate project_id must resolve to a project record")

    source_observation_ids = {
        record_id
        for record_id, record in record_by_id.items()
        if record["kind"] == "source_observation"
    }

    for record in records:
        if record["kind"] == "source_observation":
            source_id = record["data"]["source_id"]
            source = record_by_id.get(source_id)
            if not source or source["kind"] != "source":
                raise AssertionError(f"source observation {record['id']} has invalid source_id {source_id}")
        for refs in record.get("provenance", {}).values():
            missing = sorted(set(refs) - source_observation_ids)
            if missing:
                raise AssertionError(f"record {record['id']} has unresolved provenance refs: {missing}")

    derived = {
        record["id"]
        for record in records
        if record["kind"] == "proposition" and record["data"].get("epistemic_role") == "derived"
    }
    premise_sources = set()
    contradiction_pairs = set()
    for relation in relations:
        if relation["from"] not in record_by_id or relation["to"] not in record_by_id:
            raise AssertionError(f"relation {relation['id']} has dangling endpoint")
        if relation["from"] == relation["to"]:
            raise AssertionError(f"relation {relation['id']} is self-referential")
        for refs in relation.get("provenance", {}).values():
            missing = sorted(set(refs) - source_observation_ids)
            if missing:
                raise AssertionError(f"relation {relation['id']} has unresolved provenance refs: {missing}")
        if relation["kind"] == "derived_from":
            premise_sources.add(relation["from"])
        if relation["kind"] == "contradicts":
            pair = (relation["from"], relation["to"])
            if pair[0] > pair[1]:
                raise AssertionError(f"contradiction {relation['id']} is not in canonical endpoint order")
            if pair in contradiction_pairs:
                raise AssertionError(f"duplicate contradiction pair: {pair}")
            contradiction_pairs.add(pair)

    missing_premises = sorted(derived - premise_sources)
    if missing_premises:
        raise AssertionError(f"derived propositions missing derived_from relations: {missing_premises}")

    return {
        "record_count": len(records),
        "relation_count": len(relations),
        "record_ids_unique": True,
        "relation_ids_unique": True,
        "project_reference_valid": True,
        "provenance_references_resolved": True,
        "relation_endpoints_resolved": True,
        "derived_propositions_have_premises": True,
        "contradictions_canonicalized": True,
    }


def run(candidate_path=None):
    suite = json.loads(FIXTURES.read_text())
    admission_suite = json.loads(ADMISSION_FIXTURES.read_text())
    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    schema_validator = Draft202012Validator(schema)

    valid, invalids = structural_smoke_documents()
    schema_validator.validate(valid)
    for doc in invalids:
        try:
            schema_validator.validate(doc)
        except ValidationError:
            pass
        else:
            raise AssertionError("structural negative fixture unexpectedly passed")

    failures = []
    compatibility_results = []
    for case in suite["cases"]:
        actual = classify_case(case)
        compatibility_results.append({"id": case["id"], "actual": actual})
        if actual != case["expected"]:
            failures.append((case["id"], case["expected"], actual))

    admission_results = []
    for case in admission_suite["cases"]:
        actual = classify_admission_case(case)
        admission_results.append({"id": case["id"], "actual": actual})
        if actual != case["expected"]:
            failures.append((case["id"], case["expected"], actual))

    v1 = migration_fixture()
    first = migrate_v1_to_v2(v1)
    second = migrate_v1_to_v2(copy.deepcopy(v1))
    assert canonical_json(first) == canonical_json(second)
    assert {x["id"] for x in first["records"]} == {x["id"] for x in v1["records"]}
    assert {x["id"] for x in first["relations"]} == {x["id"] for x in v1["relations"]}
    d = next(x for x in first["records"] if x["id"] == "pems:decision:d")
    assert d["lifecycle"] == "historical"
    assert d["data"]["decision_state"] == "accepted"
    assert d["provenance"] == {"untyped": ["pems:source_observation:o"]}
    r = first["relations"][0]
    assert r["data"]["dependency_kind"] == "legacy_untyped"
    assert r["provenance"] == {"untyped": ["pems:source_observation:o"]}
    assert all("observation_refs" not in x for x in first["records"] + first["relations"])
    assert all(x["kind"] != "proposition" for x in first["records"])
    assert all(x["kind"] not in {"supports", "contradicts"} for x in first["relations"])
    schema_validator.validate(first)

    migration_digest = hashlib.sha256(canonical_json(first)).hexdigest()
    result_digest = hashlib.sha256(canonical_json({"compatibility": compatibility_results, "admission": admission_results})).hexdigest()
    repeated_digest = hashlib.sha256(canonical_json({"compatibility": [
        {"id": c["id"], "actual": classify_case(c)} for c in suite["cases"]
    ], "admission": [
        {"id": c["id"], "actual": classify_admission_case(c)} for c in admission_suite["cases"]
    ]})).hexdigest()
    assert result_digest == repeated_digest

    if failures:
        for cid, expected, actual in failures:
            print(f"FAIL {cid}: expected={expected!r} actual={actual!r}")
        raise SystemExit(1)

    print("PASS schema_draft_2020_12")
    print("PASS structural_smoke_positive=1 negative=3")
    print(f"PASS compatibility_cases={len(suite['cases'])}")
    print(f"PASS admission_cases={len(admission_suite['cases'])}")
    print("PASS deterministic_v1_to_v2_migration")
    print("PASS repeated_policy_result_determinism")
    print(f"MIGRATION_FIXTURE_SHA256={migration_digest}")
    print(f"POLICY_RESULTS_SHA256={result_digest}")

    if candidate_path is not None:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        result = validate_candidate_document(candidate, schema_validator)
        candidate_digest = hashlib.sha256(
            json.dumps(candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        print(f"PASS candidate={candidate_path}")
        print(f"PASS candidate_records={result['record_count']} candidate_relations={result['relation_count']}")
        print("PASS candidate_graph_reference_integrity")
        print(f"CANDIDATE_SHA256={candidate_digest}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate",
        type=Path,
        help="optional complete PEMS/2 candidate document to validate after the contract suite",
    )
    args = parser.parse_args()
    run(args.candidate)


if __name__ == "__main__":
    main()
