from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_activation import make_explicit_activation  # noqa: E402
from ril_mutation import canonical_json_bytes  # noqa: E402
from ril_operators import apply_initial_operator, approve_initial_operator, plan_initial_operator  # noqa: E402
from ril_reconciliation import ASSESSMENT_CONTRACT, reconcile_candidate  # noqa: E402
from ril_steward_authorization import (  # noqa: E402
    apply_authorization_change,
    approve_authorization_change,
    plan_authorization_change,
)


class ReconciliationR12Tests(unittest.TestCase):
    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "project-knowledge" / "submissions").mkdir(parents=True)
        return root

    def establish_root(self, root: Path) -> None:
        planned = plan_initial_operator(root, "operator:owner")
        approval = approve_initial_operator(planned["proposal"], "operator:owner")
        result = apply_initial_operator(root, planned["proposal"], approval)
        self.assertEqual(result["status"], "PASS")

    def authorize_default_steward(self, root: Path) -> None:
        planned = plan_authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        self.assertEqual(planned["status"], "PASS")
        approval = approve_authorization_change(planned["proposal"], "operator:owner")
        result = apply_authorization_change(root, planned["proposal"], approval)
        self.assertEqual(result["status"], "PASS")

    def ready(self) -> tuple[Path, Path, dict]:
        root = self.project()
        self.establish_root(root)
        self.authorize_default_steward(root)
        candidate = root / "project-knowledge" / "submissions" / "candidate.json"
        candidate.write_bytes(canonical_json_bytes({"contract": "test-candidate/1", "claim": "x"}))
        activation = make_explicit_activation("steward:default", "invocation:1", "test")
        return root, candidate, activation

    def assessment(self, status: str = "COMPATIBLE", recommendation: str = "RECOMMEND") -> dict:
        return {
            "contract": ASSESSMENT_CONTRACT,
            "semantic_status": status,
            "admission_recommendation": recommendation,
            "rationale": "Semantically compatible with the current project knowledge.",
        }

    def test_activation_authority_is_required(self):
        root = self.project()
        self.establish_root(root)
        candidate = root / "project-knowledge" / "submissions" / "candidate.json"
        candidate.write_bytes(canonical_json_bytes({"x": 1}))
        activation = make_explicit_activation("steward:default", "invocation:1", "test")
        result = reconcile_candidate(root, candidate, activation, self.assessment())
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "SCOPE_UNASSIGNED"))

    def test_candidate_outside_submissions_is_rejected(self):
        root, _, activation = self.ready()
        outside = root / "outside.json"
        outside.write_bytes(canonical_json_bytes({"x": 1}))
        result = reconcile_candidate(root, outside, activation, self.assessment())
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "CANDIDATE_PATH_OUTSIDE_SUBMISSIONS"))

    def test_invalid_assessment_combination_is_rejected(self):
        root, candidate, activation = self.ready()
        result = reconcile_candidate(root, candidate, activation, self.assessment("INCOMPATIBLE", "RECOMMEND"))
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "INVALID_ADMISSION_RECOMMENDATION"))

    def test_success_creates_immutable_disposition_and_activation_evidence(self):
        root, candidate, activation = self.ready()
        result = reconcile_candidate(root, candidate, activation, self.assessment())
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "RECONCILED"))
        disposition = root / result["disposition_path"]
        self.assertTrue(disposition.is_file())
        activation_dir = root / "project-knowledge" / "reconciliation" / "activation-evidence"
        self.assertEqual(len(list(activation_dir.glob("*.json"))), 1)

    def test_retry_is_no_change(self):
        root, candidate, activation = self.ready()
        first = reconcile_candidate(root, candidate, activation, self.assessment())
        second = reconcile_candidate(root, candidate, activation, self.assessment())
        self.assertEqual(first["outcome"], "RECONCILED")
        self.assertEqual((second["status"], second["outcome"]), ("PASS", "NO_CHANGE"))

    def test_conflicting_second_disposition_is_rejected(self):
        root, candidate, activation = self.ready()
        first = reconcile_candidate(root, candidate, activation, self.assessment())
        self.assertEqual(first["status"], "PASS")
        changed = self.assessment("COMPATIBLE", "DEFER")
        result = reconcile_candidate(root, candidate, activation, changed)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "DISPOSITION_CONFLICT"))

    def test_candidate_mutation_creates_new_identity_not_rewrite(self):
        root, candidate, activation = self.ready()
        first = reconcile_candidate(root, candidate, activation, self.assessment())
        first_path = root / first["disposition_path"]
        first_bytes = first_path.read_bytes()
        candidate.write_bytes(canonical_json_bytes({"contract": "test-candidate/1", "claim": "y"}))
        second = reconcile_candidate(root, candidate, activation, self.assessment())
        self.assertEqual((second["status"], second["outcome"]), ("PASS", "RECONCILED"))
        self.assertNotEqual(first["candidate_digest"], second["candidate_digest"])
        self.assertEqual(first_path.read_bytes(), first_bytes)

    def test_no_admission_or_canonical_state_is_created(self):
        root, candidate, activation = self.ready()
        result = reconcile_candidate(root, candidate, activation, self.assessment())
        self.assertEqual(result["status"], "PASS")
        forbidden = [
            root / "project-knowledge" / "admission",
            root / "project-knowledge" / "canonical",
            root / "project-knowledge" / "pems",
            root / "project-knowledge" / "cove",
        ]
        self.assertTrue(all(not path.exists() for path in forbidden))


if __name__ == "__main__":
    unittest.main()
