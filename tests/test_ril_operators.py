from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_mutation import canonical_json_bytes  # noqa: E402
from ril_operators import (  # noqa: E402
    CORE_CAPABILITIES,
    apply_initial_operator,
    approve_initial_operator,
    initial_required,
    operator_paths,
    plan_initial_operator,
    read_operator_registry,
    rebuild_operator_projection,
)


class OperatorRegistryR4Tests(unittest.TestCase):
    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "project-knowledge").mkdir()
        return root

    def establish(self, root: Path, operator_id: str = "operator:owner"):
        planned = plan_initial_operator(root, operator_id)
        self.assertEqual(planned["status"], "PASS")
        approval = approve_initial_operator(planned["proposal"], operator_id)
        result = apply_initial_operator(root, planned["proposal"], approval)
        return planned, approval, result

    def test_initial_operator_required_on_empty_project(self):
        root = self.project()
        result = initial_required(root)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "INITIAL_OPERATOR_REQUIRED"))

    def test_plan_is_deterministic_and_mutation_free(self):
        root = self.project()
        before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
        a = plan_initial_operator(root, "operator:owner")
        b = plan_initial_operator(root, "operator:owner")
        after = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
        self.assertEqual(a, b)
        self.assertEqual(before, after)

    def test_wrong_human_confirmation_rejected(self):
        root = self.project()
        planned = plan_initial_operator(root, "operator:owner")
        approval = approve_initial_operator(planned["proposal"], "operator:owner")
        approval = copy.deepcopy(approval)
        approval["authentication"]["confirmation"] = "NO"
        result = apply_initial_operator(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "HUMAN_CONFIRMATION_REQUIRED"))

    def test_mismatched_proposal_rejected(self):
        root = self.project()
        p1 = plan_initial_operator(root, "operator:owner")["proposal"]
        p2 = plan_initial_operator(root, "operator:other")["proposal"]
        approval = approve_initial_operator(p1, "operator:owner")
        result = apply_initial_operator(root, p2, approval)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["outcome"], "APPROVAL_MISMATCH")

    def test_apply_creates_exact_protected_root(self):
        root = self.project()
        _, _, result = self.establish(root)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))
        ready = read_operator_registry(root)
        registry = ready["registry"]
        self.assertEqual(registry["root_operator_id"], "operator:owner")
        entry = registry["operators"]["operator:owner"]
        self.assertTrue(entry["protected_root"])
        self.assertEqual(entry["capabilities"], CORE_CAPABILITIES)
        self.assertEqual(entry["status"], "active")

    def test_retry_is_no_change(self):
        root = self.project()
        planned, approval, first = self.establish(root)
        second = apply_initial_operator(root, planned["proposal"], approval)
        self.assertEqual(first["outcome"], "APPLIED")
        self.assertEqual((second["status"], second["outcome"]), ("PASS", "NO_CHANGE"))

    def test_second_distinct_root_rejected(self):
        root = self.project()
        self.establish(root)
        result = plan_initial_operator(root, "operator:other")
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "ROOT_ALREADY_ESTABLISHED"))

    def test_missing_projection_rebuilds(self):
        root = self.project()
        self.establish(root)
        events, projection = operator_paths(root)
        projection.unlink()
        rebuilt = rebuild_operator_projection(root)
        self.assertEqual((rebuilt["status"], rebuilt["outcome"]), ("PASS", "REBUILT"))
        self.assertTrue(projection.exists())
        self.assertTrue(events.exists())

    def test_conflicting_projection_fails_closed(self):
        root = self.project()
        self.establish(root)
        _, projection = operator_paths(root)
        projection.write_bytes(canonical_json_bytes({"bad": True}))
        result = read_operator_registry(root)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "PROJECTION_CONFLICT"))

    def test_no_steward_or_canonical_state_created(self):
        root = self.project()
        self.establish(root)
        forbidden = [
            root / "project-knowledge" / "steward",
            root / "project-knowledge" / "authority",
            root / "project-knowledge" / "canonical",
            root / "project-knowledge" / "pems",
            root / "project-knowledge" / "cove",
        ]
        self.assertTrue(all(not p.exists() for p in forbidden))


if __name__ == "__main__":
    unittest.main()
