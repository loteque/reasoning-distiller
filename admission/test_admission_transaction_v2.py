#!/usr/bin/env python3
"""Pressure tests for exact-base guarded reused-record updates."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import apply_admission_transaction_v2 as v2


def base_document():
    return {
        "semantic": "pems/2",
        "project_id": "pems:project:test",
        "records": [
            {
                "id": "pems:unresolved_item:test",
                "kind": "unresolved_item",
                "lifecycle": "current",
                "data": {"summary": "Whether X remains unverified.", "resolution_state": "open"},
            }
        ],
        "relations": [],
    }


def plan_for(base):
    record = base["records"][0]
    replacement = copy.deepcopy(record)
    replacement["lifecycle"] = "historical"
    return {
        "contract": v2.CONTRACT,
        "expected_base_sha256": v2.sha256(v2.jcs(v2.normalize_pems(base))),
        "reuse_record_ids": [record["id"]],
        "record_updates": [
            {
                "record_id": record["id"],
                "expected_before_sha256": v2.sha256(v2.jcs(record)),
                "replacement": replacement,
            }
        ],
        "new_records": [],
        "new_relations": [],
    }


def expect_failure(name, mutate, text):
    base = base_document()
    plan = plan_for(base)
    mutate(base, plan)
    try:
        v2.apply_transaction(base, plan)
    except ValueError as exc:
        if text not in str(exc):
            raise AssertionError(f"{name}: unexpected error: {exc}") from exc
        return
    raise AssertionError(f"{name}: expected failure")


def main():
    base = base_document()
    plan = plan_for(base)
    candidate, updates = v2.apply_transaction(base, plan)
    updated = candidate["records"][0]
    assert updated["id"] == "pems:unresolved_item:test"
    assert updated["kind"] == "unresolved_item"
    assert updated["lifecycle"] == "historical"
    assert updates[0]["before_sha256"] == plan["record_updates"][0]["expected_before_sha256"]

    expect_failure(
        "base hash",
        lambda base, plan: plan.__setitem__("expected_base_sha256", "0" * 64),
        "base hash mismatch",
    )
    expect_failure(
        "before state",
        lambda base, plan: plan["record_updates"][0].__setitem__("expected_before_sha256", "0" * 64),
        "before-state mismatch",
    )
    expect_failure(
        "identity rebind",
        lambda base, plan: plan["record_updates"][0]["replacement"].__setitem__("id", "pems:unresolved_item:other"),
        "may not rebind record identity",
    )
    expect_failure(
        "kind rebind",
        lambda base, plan: plan["record_updates"][0]["replacement"].__setitem__("kind", "proposition"),
        "may not change record kind",
    )
    expect_failure(
        "undeclared reuse",
        lambda base, plan: plan.__setitem__("reuse_record_ids", []),
        "must also be declared reused",
    )
    expect_failure(
        "duplicate update",
        lambda base, plan: plan["record_updates"].append(copy.deepcopy(plan["record_updates"][0])),
        "duplicate record update target",
    )

    print(json.dumps({"contract": v2.CONTRACT, "pressure_cases": 7, "passed": True}, sort_keys=True))


if __name__ == "__main__":
    main()
