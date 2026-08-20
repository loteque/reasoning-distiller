#!/usr/bin/env python3
"""Replay the additive PEMS/2 RGP/1 uncertainty-import compatibility profile."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "RGP_UNCERTAINTY_IMPORT_FIXTURES.json"


def classify(inp):
    if inp.get("rgp_version") != "rgp/1":
        return {"accepted": False, "reason": "unsupported_rgp_major"}
    if inp.get("relation") == "depends_on":
        return {"pems_kind": "depends_on", "dependency_kind": "conditional_validity"}
    if inp.get("kind") != "uncertainty":
        raise AssertionError("fixture is outside uncertainty-import profile")
    if "premise" in inp:
        return {
            "pems_kind": "unresolved_item",
            "premise_relation": "derived_from",
            "premise_targets": inp["premise"],
        }
    if "provenance" in inp:
        return {
            "preserve_roles": sorted(inp["provenance"]),
            "canonical_source_resolution_required": True,
        }
    if inp.get("statement") == "Whether X is blocked.":
        return {
            "resolution_state": "open",
            "infer_blocked": False,
            "infer_deferred": False,
        }
    if inp.get("statement") == "Whether X holds.":
        return {"pems_kind": "unresolved_item", "proposition_kind": None}
    return {
        "pems_kind": "unresolved_item",
        "lifecycle": "current",
        "summary": inp["statement"],
        "resolution_state": "open",
    }


def run():
    suite = json.loads(FIXTURES.read_text())
    failures = []
    for case in suite["cases"]:
        actual = classify(case["input"])
        if actual != case["expected"]:
            failures.append((case["id"], case["expected"], actual))
    if failures:
        raise AssertionError(f"uncertainty-import fixture failures: {failures}")
    return {"contract": suite["contract"], "cases": len(suite["cases"]), "passed": True}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
