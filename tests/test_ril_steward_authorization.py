from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_mutation import canonical_json_bytes  # noqa: E402
from ril_operators import (  # noqa: E402
    apply_initial_operator,
    approve_initial_operator,
    plan_initial_operator,
)
from ril_roles import (  # noqa: E402
    SUBMISSION_CONTRACT,
    apply_role_submission,
    approve_role_submission,
    plan_role_submission,
)
from ril_steward_authorization import (  # noqa: E402
    apply_authorization_change,
    approve_authorization_change,
    authorization_paths,
    evidence_paths,
    plan_authorization_change,
    read_authorization,
    rebuild_authorization_projection,
)


class StewardAuthorizationR7Tests(unittest.TestCase):
    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "project-knowledge").mkdir()
        self.establish_operator(root)
        return root

    def establish_operator(self, root: Path) -> None:
        planned = plan_initial_operator(root, "operator:owner")
        approval = approve_initial_operator(planned["proposal"], "operator:owner")
        result = apply_initial_operator(root, planned["proposal"], approval)
        self.assertEqual(result["status"], "PASS")

    def role(self, role_id: str = "project-steward") -> dict:
        return {
            "role_id": role_id,
            "title": "Project Steward",
            "description": "Project-defined Steward candidate.",
            "capabilities": ["project:steward_candidate"],
        }

    def apply_role(self, root: Path, submission: dict) -> dict:
        planned = plan_role_submission(root, submission)
        self.assertEqual(planned["status"], "PASS")
        if planned["outcome"] == "NO_CHANGE":
            return planned
        approval = approve_role_submission(planned["proposal"], "operator:owner")
        result = apply_role_submission(root, planned["proposal"], approval)
        self.assertEqual(result["status"], "PASS")
        return result

    def add_role(self, root: Path, role_id: str = "project-steward") -> None:
        self.apply_role(root, {
            "contract": SUBMISSION_CONTRACT,
            "mode": "incremental",
            "source": "test-session",
            "scope": None,
            "roles": [self.role(role_id)],
        })

    def disable_role(self, root: Path, role_id: str = "project-steward") -> None:
        self.apply_role(root, {
            "contract": SUBMISSION_CONTRACT,
            "mode": "snapshot",
            "source": "test-session",
            "scope": {"role_ids": [role_id]},
            "roles": [],
        })

    def apply_auth(self, root: Path, operation: str, scope: str, role_id: str | None = None):
        planned = plan_authorization_change(root, operation, scope, role_id)
        self.assertEqual(planned["status"], "PASS")
        approval = approve_authorization_change(planned["proposal"], "operator:owner")
        result = apply_authorization_change(root, planned["proposal"], approval)
        self.assertEqual(result["status"], "PASS")
        return planned, approval, result

    def assignments(self, root: Path) -> dict:
        result = read_authorization(root)
        self.assertEqual(result["status"], "PASS")
        return result["authorization"]["assignments"]

    def test_scopes_begin_unassigned_and_default_is_not_automatic(self):
        root = self.project()
        self.assertEqual(self.assignments(root), {"admission": None, "semantic_reconciliation": None})

    def test_authorize_default_steward_for_one_scope_only(self):
        root = self.project()
        self.apply_auth(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        self.assertEqual(self.assignments(root), {
            "admission": None,
            "semantic_reconciliation": "steward:default",
        })

    def test_scopes_are_independent(self):
        root = self.project()
        self.add_role(root)
        self.apply_auth(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        self.apply_auth(root, "AUTHORIZE", "admission", "project-steward")
        self.assertEqual(self.assignments(root), {
            "admission": "project-steward",
            "semantic_reconciliation": "steward:default",
        })

    def test_reassign_changes_only_selected_scope(self):
        root = self.project()
        self.add_role(root)
        self.apply_auth(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        self.apply_auth(root, "AUTHORIZE", "admission", "steward:default")
        self.apply_auth(root, "REASSIGN", "semantic_reconciliation", "project-steward")
        self.assertEqual(self.assignments(root), {
            "admission": "steward:default",
            "semantic_reconciliation": "project-steward",
        })

    def test_revoke_leaves_scope_explicitly_unassigned(self):
        root = self.project()
        self.apply_auth(root, "AUTHORIZE", "admission", "steward:default")
        self.apply_auth(root, "REVOKE", "admission")
        self.assertIsNone(self.assignments(root)["admission"])

    def test_unknown_and_unavailable_targets_are_rejected(self):
        root = self.project()
        missing = plan_authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "missing-role")
        self.assertEqual((missing["status"], missing["outcome"]), ("FAIL", "ROLE_NOT_FOUND"))
        self.add_role(root)
        self.disable_role(root)
        disabled = plan_authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "project-steward")
        self.assertEqual((disabled["status"], disabled["outcome"]), ("FAIL", "ROLE_UNAVAILABLE"))

    def test_unauthorized_operator_cannot_apply(self):
        root = self.project()
        planned = plan_authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        approval = approve_authorization_change(planned["proposal"], "operator:ghost")
        result = apply_authorization_change(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "APPROVER_NOT_AUTHORIZED"))
        self.assertIsNone(self.assignments(root)["semantic_reconciliation"])

    def test_approval_is_bound_to_exact_proposal(self):
        root = self.project()
        p1 = plan_authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")["proposal"]
        p2 = plan_authorization_change(root, "AUTHORIZE", "admission", "steward:default")["proposal"]
        approval = approve_authorization_change(p1, "operator:owner")
        result = apply_authorization_change(root, p2, approval)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "APPROVAL_MISMATCH"))

    def test_retry_is_idempotent_no_change(self):
        root = self.project()
        planned, approval, first = self.apply_auth(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        second = apply_authorization_change(root, planned["proposal"], approval)
        self.assertEqual(first["outcome"], "APPLIED")
        self.assertEqual((second["status"], second["outcome"]), ("PASS", "NO_CHANGE"))

    def test_missing_projection_rebuilds_and_conflict_fails_closed(self):
        root = self.project()
        self.apply_auth(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        events, projection = authorization_paths(root)
        projection.unlink()
        rebuilt = rebuild_authorization_projection(root)
        self.assertEqual((rebuilt["status"], rebuilt["outcome"]), ("PASS", "REBUILT"))
        self.assertTrue(events.exists())
        projection.write_bytes(canonical_json_bytes({"bad": True}))
        result = read_authorization(root)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "PROJECTION_CONFLICT"))

    def test_evidence_is_preserved_and_no_semantic_or_canonical_state_created(self):
        root = self.project()
        self.apply_auth(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        proposals, approvals = evidence_paths(root)
        self.assertEqual(len(list(proposals.glob("*.json"))), 1)
        self.assertEqual(len(list(approvals.glob("*.json"))), 1)
        forbidden = [
            root / "project-knowledge" / "reconciliation",
            root / "project-knowledge" / "admission",
            root / "project-knowledge" / "canonical",
            root / "project-knowledge" / "pems",
            root / "project-knowledge" / "cove",
        ]
        self.assertTrue(all(not p.exists() for p in forbidden))


if __name__ == "__main__":
    unittest.main()
