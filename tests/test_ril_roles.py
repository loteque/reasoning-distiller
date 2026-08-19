from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_mutation import canonical_json_bytes  # noqa: E402
from ril_operators import apply_initial_operator, approve_initial_operator, plan_initial_operator  # noqa: E402
from ril_operator_management import apply_operator_change, approve_operator_change, plan_operator_change  # noqa: E402
from ril_roles import (  # noqa: E402
    DEFAULT_STEWARD_ID,
    SUBMISSION_CONTRACT,
    apply_role_submission,
    approve_role_submission,
    evidence_paths,
    plan_role_submission,
    read_role_registry,
    role_paths,
)


class RoleRegistryR6Tests(unittest.TestCase):
    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "project-knowledge").mkdir()
        p = plan_initial_operator(root, "operator:owner")
        a = approve_initial_operator(p["proposal"], "operator:owner")
        r = apply_initial_operator(root, p["proposal"], a)
        self.assertEqual((r["status"], r["outcome"]), ("PASS", "APPLIED"))
        return root

    def role(self, role_id: str, title: str | None = None, description: str = "", capabilities=None):
        return {
            "role_id": role_id,
            "title": title or role_id.replace("-", " ").title(),
            "description": description,
            "capabilities": capabilities or [],
        }

    def submission(self, roles, *, mode="incremental", source="active-chat", scope=None):
        return {
            "contract": SUBMISSION_CONTRACT,
            "mode": mode,
            "source": source,
            "scope": scope,
            "roles": roles,
        }

    def apply(self, root: Path, submission, approver="operator:owner"):
        planned = plan_role_submission(root, submission)
        self.assertEqual(planned["status"], "PASS")
        self.assertEqual(planned["outcome"], "PLANNED")
        approval = approve_role_submission(planned["proposal"], approver)
        result = apply_role_submission(root, planned["proposal"], approval)
        return planned, approval, result

    def test_default_steward_exists_without_authority_state(self):
        root = self.project()
        ready = read_role_registry(root)
        entry = ready["registry"]["roles"][DEFAULT_STEWARD_ID]
        self.assertEqual(entry["status"], "available")
        self.assertTrue(entry["protected"])
        self.assertEqual(entry["origin"], "package")
        self.assertFalse((root / "project-knowledge" / "steward").exists())
        self.assertFalse((root / "project-knowledge" / "authority").exists())

    def test_plan_is_deterministic_and_mutation_free(self):
        root = self.project()
        sub = self.submission([self.role("gameplay-engineer")])
        before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
        a = plan_role_submission(root, sub)
        b = plan_role_submission(root, sub)
        after = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
        self.assertEqual(a, b)
        self.assertEqual(before, after)

    def test_incremental_add_and_retry_and_evidence_preservation(self):
        root = self.project()
        sub = self.submission([self.role("gameplay-engineer", capabilities=["project:gameplay"])])
        planned, approval, first = self.apply(root, sub)
        self.assertEqual((first["status"], first["outcome"]), ("PASS", "APPLIED"))
        second = apply_role_submission(root, planned["proposal"], approval)
        self.assertEqual((second["status"], second["outcome"]), ("PASS", "NO_CHANGE"))
        ready = read_role_registry(root)
        self.assertEqual(ready["registry"]["roles"]["gameplay-engineer"]["status"], "available")
        submissions, proposals, approvals = evidence_paths(root)
        self.assertEqual(len(list(submissions.glob("*.json"))), 1)
        self.assertEqual(len(list(proposals.glob("*.json"))), 1)
        self.assertEqual(len(list(approvals.glob("*.json"))), 1)

    def test_identical_submission_is_no_change(self):
        root = self.project()
        sub = self.submission([self.role("qa-engineer")])
        self.apply(root, sub)
        planned = plan_role_submission(root, sub)
        self.assertEqual((planned["status"], planned["outcome"]), ("PASS", "NO_CHANGE"))
        self.assertNotIn("proposal", planned)

    def test_changed_definition_is_update(self):
        root = self.project()
        first = self.submission([self.role("qa-engineer", description="old")])
        self.apply(root, first)
        second = self.submission([self.role("qa-engineer", description="new")])
        planned = plan_role_submission(root, second)
        self.assertEqual(planned["proposal"]["change"]["changes"][0]["action"], "UPDATE")
        approval = approve_role_submission(planned["proposal"], "operator:owner")
        result = apply_role_submission(root, planned["proposal"], approval)
        self.assertEqual(result["outcome"], "APPLIED")
        self.assertEqual(read_role_registry(root)["registry"]["roles"]["qa-engineer"]["definition"]["description"], "new")

    def test_scoped_snapshot_disables_only_absent_in_scope_and_reenable(self):
        root = self.project()
        self.apply(root, self.submission([self.role("qa-engineer"), self.role("build-engineer")]))
        snap = self.submission(
            [self.role("build-engineer")],
            mode="snapshot",
            scope={"role_ids": ["build-engineer", "qa-engineer"]},
        )
        _, _, result = self.apply(root, snap)
        self.assertEqual(result["outcome"], "APPLIED")
        roles = read_role_registry(root)["registry"]["roles"]
        self.assertEqual(roles["qa-engineer"]["status"], "disabled")
        self.assertEqual(roles["build-engineer"]["status"], "available")
        self.assertEqual(roles[DEFAULT_STEWARD_ID]["status"], "available")

        reappear = self.submission([self.role("qa-engineer")])
        planned = plan_role_submission(root, reappear)
        self.assertEqual(planned["proposal"]["change"]["changes"][0]["action"], "REENABLE")
        approval = approve_role_submission(planned["proposal"], "operator:owner")
        self.assertEqual(apply_role_submission(root, planned["proposal"], approval)["outcome"], "APPLIED")
        self.assertEqual(read_role_registry(root)["registry"]["roles"]["qa-engineer"]["status"], "available")

    def test_snapshot_scope_does_not_touch_role_outside_scope(self):
        root = self.project()
        self.apply(root, self.submission([self.role("qa-engineer"), self.role("build-engineer")]))
        snap = self.submission([], mode="snapshot", scope={"role_ids": ["qa-engineer"]})
        self.apply(root, snap)
        roles = read_role_registry(root)["registry"]["roles"]
        self.assertEqual(roles["qa-engineer"]["status"], "disabled")
        self.assertEqual(roles["build-engineer"]["status"], "available")

    def test_package_role_submission_and_scope_rejected(self):
        root = self.project()
        direct = self.submission([self.role(DEFAULT_STEWARD_ID, title="Default Steward")])
        self.assertEqual(plan_role_submission(root, direct)["outcome"], "PACKAGE_ROLE_PROTECTED")
        snap = self.submission([], mode="snapshot", scope={"role_ids": [DEFAULT_STEWARD_ID]})
        self.assertEqual(plan_role_submission(root, snap)["outcome"], "PACKAGE_ROLE_PROTECTED")

    def test_forbidden_protocol_roles_and_rd_capabilities_rejected(self):
        root = self.project()
        architect = self.submission([self.role("project-architect", title="Project Architect")])
        self.assertEqual(plan_role_submission(root, architect)["outcome"], "FORBIDDEN_PROTOCOL_ROLE")
        rgp = self.submission([self.role("rgp-engineer", title="RGP Engineer")])
        self.assertEqual(plan_role_submission(root, rgp)["outcome"], "FORBIDDEN_PROTOCOL_ROLE")
        reserved = self.submission([self.role("gameplay-engineer", capabilities=["rd:protocol_governance"])])
        self.assertEqual(plan_role_submission(root, reserved)["outcome"], "FORBIDDEN_PACKAGE_CAPABILITY")

    def test_unauthorized_operator_cannot_apply(self):
        root = self.project()
        p = plan_operator_change(root, "ADD_OPERATOR", "operator:viewer", ["project:view"])
        a = approve_operator_change(p["proposal"], "operator:owner")
        self.assertEqual(apply_operator_change(root, p["proposal"], a)["outcome"], "APPLIED")

        role_plan = plan_role_submission(root, self.submission([self.role("qa-engineer")]))
        approval = approve_role_submission(role_plan["proposal"], "operator:viewer")
        result = apply_role_submission(root, role_plan["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "APPROVER_NOT_AUTHORIZED"))

    def test_conflicting_role_projection_fails_closed(self):
        root = self.project()
        self.apply(root, self.submission([self.role("qa-engineer")]))
        _, projection = role_paths(root)
        projection.write_bytes(canonical_json_bytes({"bad": True}))
        result = plan_role_submission(root, self.submission([self.role("build-engineer")]))
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "PROJECTION_CONFLICT"))

    def test_no_semantic_authority_or_canonical_state_created(self):
        root = self.project()
        self.apply(root, self.submission([self.role("qa-engineer")]))
        forbidden = [
            root / "project-knowledge" / "steward",
            root / "project-knowledge" / "authority",
            root / "project-knowledge" / "reconciliation",
            root / "project-knowledge" / "canonical",
            root / "project-knowledge" / "pems",
            root / "project-knowledge" / "cove",
        ]
        self.assertTrue(all(not path.exists() for path in forbidden))


if __name__ == "__main__":
    unittest.main()
