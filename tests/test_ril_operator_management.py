from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_operator_management import (  # noqa: E402
    apply_operator_change,
    apply_root_transfer,
    approve_operator_change,
    approve_root_transfer,
    plan_operator_change,
    plan_root_transfer,
)
from ril_operators import (  # noqa: E402
    CORE_CAPABILITIES,
    apply_initial_operator,
    approve_initial_operator,
    plan_initial_operator,
    read_operator_registry,
)


class OperatorManagementR5Tests(unittest.TestCase):
    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "project-knowledge").mkdir()
        initial = plan_initial_operator(root, "operator:owner")
        approval = approve_initial_operator(initial["proposal"], "operator:owner")
        result = apply_initial_operator(root, initial["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))
        return root

    def registry(self, root: Path):
        result = read_operator_registry(root)
        self.assertEqual(result["status"], "PASS")
        return result["registry"]

    def add(self, root: Path, operator_id: str, capabilities: list[str], approver: str = "operator:owner"):
        planned = plan_operator_change(root, "ADD_OPERATOR", operator_id, capabilities)
        self.assertEqual(planned["status"], "PASS")
        approval = approve_operator_change(planned["proposal"], approver)
        result = apply_operator_change(root, planned["proposal"], approval)
        return planned, approval, result

    def test_authorized_manager_can_add_operator(self):
        root = self.project()
        _, _, result = self.add(root, "operator:alice", ["rd:role_registry", "project:release"])
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))
        alice = self.registry(root)["operators"]["operator:alice"]
        self.assertEqual(alice["status"], "active")
        self.assertFalse(alice["protected_root"])
        self.assertEqual(alice["capabilities"], ["project:release", "rd:role_registry"])

    def test_unauthorized_approver_rejected(self):
        root = self.project()
        self.add(root, "operator:alice", ["rd:role_registry"])
        planned = plan_operator_change(root, "ADD_OPERATOR", "operator:bob", [])
        approval = approve_operator_change(planned["proposal"], "operator:alice")
        result = apply_operator_change(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "APPROVER_NOT_AUTHORIZED"))

    def test_project_capability_does_not_satisfy_rd_manager(self):
        root = self.project()
        self.add(root, "operator:alice", ["project:operator_management"])
        planned = plan_operator_change(root, "ADD_OPERATOR", "operator:bob", [])
        approval = approve_operator_change(planned["proposal"], "operator:alice")
        result = apply_operator_change(root, planned["proposal"], approval)
        self.assertEqual(result["outcome"], "APPROVER_NOT_AUTHORIZED")

    def test_capability_replacement_requires_approved_mutation(self):
        root = self.project()
        self.add(root, "operator:alice", ["rd:role_registry"])
        planned = plan_operator_change(root, "UPDATE_CAPABILITIES", "operator:alice", ["rd:operator_management"])
        approval = approve_operator_change(planned["proposal"], "operator:owner")
        result = apply_operator_change(root, planned["proposal"], approval)
        self.assertEqual(result["outcome"], "APPLIED")
        self.assertEqual(self.registry(root)["operators"]["operator:alice"]["capabilities"], ["rd:operator_management"])

    def test_disable_and_reenable_delegated_operator(self):
        root = self.project()
        self.add(root, "operator:alice", ["rd:operator_management"])
        disable = plan_operator_change(root, "DISABLE_OPERATOR", "operator:alice")
        dapproval = approve_operator_change(disable["proposal"], "operator:owner")
        self.assertEqual(apply_operator_change(root, disable["proposal"], dapproval)["outcome"], "APPLIED")
        self.assertEqual(self.registry(root)["operators"]["operator:alice"]["status"], "disabled")
        reenable = plan_operator_change(root, "REENABLE_OPERATOR", "operator:alice")
        rapproval = approve_operator_change(reenable["proposal"], "operator:owner")
        self.assertEqual(apply_operator_change(root, reenable["proposal"], rapproval)["outcome"], "APPLIED")
        self.assertEqual(self.registry(root)["operators"]["operator:alice"]["status"], "active")

    def test_inactive_manager_cannot_approve(self):
        root = self.project()
        self.add(root, "operator:alice", ["rd:operator_management"])
        disable = plan_operator_change(root, "DISABLE_OPERATOR", "operator:alice")
        dapproval = approve_operator_change(disable["proposal"], "operator:owner")
        apply_operator_change(root, disable["proposal"], dapproval)
        planned = plan_operator_change(root, "ADD_OPERATOR", "operator:bob", [])
        approval = approve_operator_change(planned["proposal"], "operator:alice")
        result = apply_operator_change(root, planned["proposal"], approval)
        self.assertEqual(result["outcome"], "APPROVER_NOT_AUTHORIZED")

    def test_ordinary_mutation_cannot_change_root(self):
        root = self.project()
        for operation, caps in [
            ("UPDATE_CAPABILITIES", ["rd:operator_management"]),
            ("DISABLE_OPERATOR", None),
            ("REENABLE_OPERATOR", None),
        ]:
            result = plan_operator_change(root, operation, "operator:owner", caps)
            self.assertEqual((result["status"], result["outcome"]), ("FAIL", "ROOT_PROTECTED"))

    def test_unknown_rd_capability_rejected(self):
        root = self.project()
        result = plan_operator_change(root, "ADD_OPERATOR", "operator:alice", ["rd:god_mode"])
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "INVALID_CAPABILITY"))

    def test_root_transfer_requires_current_root_approval(self):
        root = self.project()
        self.add(root, "operator:alice", CORE_CAPABILITIES)
        planned = plan_root_transfer(root, "operator:alice")
        approval = approve_root_transfer(planned["proposal"], "operator:alice")
        result = apply_root_transfer(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "ROOT_APPROVAL_REQUIRED"))

    def test_root_transfer_target_requires_all_core_capabilities(self):
        root = self.project()
        self.add(root, "operator:alice", ["rd:operator_management"])
        result = plan_root_transfer(root, "operator:alice")
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "TARGET_MISSING_CORE_CAPABILITIES"))

    def test_root_transfer_target_must_be_active(self):
        root = self.project()
        self.add(root, "operator:alice", CORE_CAPABILITIES)
        disable = plan_operator_change(root, "DISABLE_OPERATOR", "operator:alice")
        approval = approve_operator_change(disable["proposal"], "operator:owner")
        apply_operator_change(root, disable["proposal"], approval)
        result = plan_root_transfer(root, "operator:alice")
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "TARGET_INACTIVE"))

    def test_successful_root_transfer_preserves_one_root_and_old_operator(self):
        root = self.project()
        self.add(root, "operator:alice", CORE_CAPABILITIES)
        planned = plan_root_transfer(root, "operator:alice")
        approval = approve_root_transfer(planned["proposal"], "operator:owner")
        result = apply_root_transfer(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))
        registry = self.registry(root)
        self.assertEqual(registry["root_operator_id"], "operator:alice")
        roots = [oid for oid, entry in registry["operators"].items() if entry["protected_root"]]
        self.assertEqual(roots, ["operator:alice"])
        self.assertEqual(registry["operators"]["operator:owner"]["status"], "active")
        self.assertFalse(registry["operators"]["operator:owner"]["protected_root"])

    def test_root_transfer_retry_is_idempotent_then_old_approval_expires_after_change(self):
        root = self.project()
        self.add(root, "operator:alice", CORE_CAPABILITIES)
        planned = plan_root_transfer(root, "operator:alice")
        approval = approve_root_transfer(planned["proposal"], "operator:owner")
        first = apply_root_transfer(root, planned["proposal"], approval)
        second = apply_root_transfer(root, planned["proposal"], approval)
        self.assertEqual(first["outcome"], "APPLIED")
        self.assertEqual((second["status"], second["outcome"]), ("PASS", "NO_CHANGE"))

        # Make a later operator-registry transition; the consumed transfer approval can no longer replay authority.
        add = plan_operator_change(root, "ADD_OPERATOR", "operator:bob", [])
        aapproval = approve_operator_change(add["proposal"], "operator:alice")
        self.assertEqual(apply_operator_change(root, add["proposal"], aapproval)["outcome"], "APPLIED")
        third = apply_root_transfer(root, planned["proposal"], approval)
        self.assertEqual((third["status"], third["outcome"]), ("FAIL", "APPROVAL_ALREADY_CONSUMED"))

    def test_wrong_confirmation_rejected(self):
        root = self.project()
        planned = plan_operator_change(root, "ADD_OPERATOR", "operator:alice", [])
        approval = approve_operator_change(planned["proposal"], "operator:owner")
        bad = copy.deepcopy(approval)
        bad["authentication"]["confirmation"] = "NO"
        result = apply_operator_change(root, planned["proposal"], bad)
        self.assertEqual(result["outcome"], "HUMAN_CONFIRMATION_REQUIRED")

    def test_no_steward_or_canonical_state_created(self):
        root = self.project()
        self.add(root, "operator:alice", CORE_CAPABILITIES)
        planned = plan_root_transfer(root, "operator:alice")
        approval = approve_root_transfer(planned["proposal"], "operator:owner")
        apply_root_transfer(root, planned["proposal"], approval)
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
