from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_activation import (  # noqa: E402
    ACTIVATION_CONTRACT,
    make_explicit_activation,
    validate_activation,
)
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
    plan_authorization_change,
)


class ActivationEvidenceR8Tests(unittest.TestCase):
    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "project-knowledge").mkdir()
        planned = plan_initial_operator(root, "operator:owner")
        approval = approve_initial_operator(planned["proposal"], "operator:owner")
        result = apply_initial_operator(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))
        return root

    def authorize(self, root: Path, scope: str, role_id: str) -> None:
        planned = plan_authorization_change(root, "AUTHORIZE", scope, role_id)
        self.assertEqual(planned["status"], "PASS")
        approval = approve_authorization_change(planned["proposal"], "operator:owner")
        result = apply_authorization_change(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))

    def apply_submission(self, root: Path, submission: dict) -> None:
        planned = plan_role_submission(root, submission)
        self.assertEqual(planned["status"], "PASS")
        if planned["outcome"] == "NO_CHANGE":
            return
        approval = approve_role_submission(planned["proposal"], "operator:owner")
        result = apply_role_submission(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))

    def test_authorized_available_role_activation_passes(self):
        root = self.project()
        self.authorize(root, "semantic_reconciliation", "steward:default")
        artifact = make_explicit_activation("steward:default", "invocation-1", "agent-session")
        result = validate_activation(root, "semantic_reconciliation", artifact)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "ACTIVATION_ACCEPTED"))
        self.assertEqual(result["role_id"], "steward:default")
        self.assertEqual(result["invocation_id"], "invocation-1")

    def test_malformed_evidence_fails(self):
        root = self.project()
        self.authorize(root, "semantic_reconciliation", "steward:default")
        artifact = {
            "contract": ACTIVATION_CONTRACT,
            "role_id": "steward:default",
            "method": "explicit_declaration",
            "context": {"invocation_id": "x"},
        }
        result = validate_activation(root, "semantic_reconciliation", artifact)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "INVALID_ACTIVATION_EVIDENCE"))

    def test_unknown_method_fails(self):
        root = self.project()
        self.authorize(root, "semantic_reconciliation", "steward:default")
        artifact = make_explicit_activation("steward:default", "invocation-1", "agent-session")
        artifact = copy.deepcopy(artifact)
        artifact["method"] = "signature-v9"
        result = validate_activation(root, "semantic_reconciliation", artifact)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "UNSUPPORTED_ACTIVATION_METHOD"))

    def test_unassigned_scope_fails(self):
        root = self.project()
        artifact = make_explicit_activation("steward:default", "invocation-1", "agent-session")
        result = validate_activation(root, "admission", artifact)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "SCOPE_UNASSIGNED"))

    def test_different_authorized_role_fails(self):
        root = self.project()
        self.authorize(root, "semantic_reconciliation", "steward:default")
        submission = {
            "contract": SUBMISSION_CONTRACT,
            "mode": "incremental",
            "source": "test",
            "scope": None,
            "roles": [{
                "role_id": "project-steward",
                "title": "Project Steward",
                "description": "Project supplied Steward.",
                "capabilities": [],
            }],
        }
        self.apply_submission(root, submission)
        artifact = make_explicit_activation("project-steward", "invocation-2", "agent-session")
        result = validate_activation(root, "semantic_reconciliation", artifact)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "ROLE_NOT_AUTHORIZED_FOR_SCOPE"))

    def test_unavailable_authorized_role_fails_without_fallback(self):
        root = self.project()
        definition = {
            "role_id": "project-steward",
            "title": "Project Steward",
            "description": "Project supplied Steward.",
            "capabilities": [],
        }
        self.apply_submission(root, {
            "contract": SUBMISSION_CONTRACT,
            "mode": "incremental",
            "source": "test",
            "scope": None,
            "roles": [definition],
        })
        self.authorize(root, "semantic_reconciliation", "project-steward")
        self.apply_submission(root, {
            "contract": SUBMISSION_CONTRACT,
            "mode": "snapshot",
            "source": "test",
            "scope": {"role_ids": ["project-steward"]},
            "roles": [],
        })
        artifact = make_explicit_activation("project-steward", "invocation-3", "agent-session")
        result = validate_activation(root, "semantic_reconciliation", artifact)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "ROLE_UNAVAILABLE"))

    def test_scopes_are_independent(self):
        root = self.project()
        self.authorize(root, "semantic_reconciliation", "steward:default")
        artifact = make_explicit_activation("steward:default", "invocation-1", "agent-session")
        ok = validate_activation(root, "semantic_reconciliation", artifact)
        blocked = validate_activation(root, "admission", artifact)
        self.assertEqual(ok["outcome"], "ACTIVATION_ACCEPTED")
        self.assertEqual(blocked["outcome"], "SCOPE_UNASSIGNED")

    def test_validation_is_deterministic_and_mutation_free(self):
        root = self.project()
        self.authorize(root, "semantic_reconciliation", "steward:default")
        artifact = make_explicit_activation("steward:default", "invocation-1", "agent-session")
        before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        first = validate_activation(root, "semantic_reconciliation", artifact)
        second = validate_activation(root, "semantic_reconciliation", artifact)
        after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        self.assertEqual(first, second)
        self.assertEqual(before, after)

    def test_conflicting_authorization_projection_fails_closed(self):
        root = self.project()
        self.authorize(root, "semantic_reconciliation", "steward:default")
        _, projection = authorization_paths(root)
        projection.write_bytes(canonical_json_bytes({"bad": True}))
        artifact = make_explicit_activation("steward:default", "invocation-1", "agent-session")
        result = validate_activation(root, "semantic_reconciliation", artifact)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "AUTHORIZATION_PROJECTION_CONFLICT"))

    def test_activation_does_not_create_authority(self):
        root = self.project()
        artifact = make_explicit_activation("steward:default", "invocation-1", "agent-session")
        before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        result = validate_activation(root, "semantic_reconciliation", artifact)
        after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "SCOPE_UNASSIGNED"))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
