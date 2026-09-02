from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import jcs  # noqa: E402
from ril_canonical_recovery_approval import (  # noqa: E402
    PLAN_CONTRACT,
    RECOVERY_CONFIRMATION,
    ROOT_APPROVAL_CONTRACT,
    parse_and_validate_recovery_root_approval,
    recovery_plan_sha256,
    validate_recovery_root_approval,
)
from ril_mutation import ContractError  # noqa: E402
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
    operator_paths,
    plan_initial_operator,
)


class CanonicalRecoveryRootApprovalG5Tests(unittest.TestCase):
    def root_project(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        proposal = plan_initial_operator(root, "operator:root")["proposal"]
        approval = approve_initial_operator(proposal, "operator:root")
        self.assertEqual(apply_initial_operator(root, proposal, approval)["status"], "PASS")
        return td, root

    def plan(self, **overrides):
        value = {
            "contract": PLAN_CONTRACT,
            "project_id": "example-project",
            "generation": "00000001",
            "candidate": {"pems_sha256": "1" * 64, "cove_sha256": "2" * 64},
            "implementation_closure": {
                "recovery_executor": {"path": "runtime/ril_canonical_recovery_executor.py", "sha256": "3" * 64}
            },
        }
        value.update(overrides)
        return value

    def approval(self, plan, root_id="operator:root", **overrides):
        value = {
            "contract": ROOT_APPROVAL_CONTRACT,
            "project_id": plan["project_id"],
            "generation": plan["generation"],
            "recovery_plan_sha256": recovery_plan_sha256(plan),
            "protected_root_id": root_id,
            "authentication": {
                "method": "human_confirmation",
                "confirmation": RECOVERY_CONFIRMATION,
            },
        }
        value.update(overrides)
        return value

    def assert_code(self, code, fn):
        with self.assertRaises(ContractError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def snapshot(self, root):
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def test_exact_current_root_approval_validates_and_binds_digest(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            approval = self.approval(plan)
            result = validate_recovery_root_approval(root, plan, approval)
            self.assertEqual(result["protected_root_id"], "operator:root")
            self.assertEqual(result["recovery_plan_sha256"], recovery_plan_sha256(plan))
            self.assertEqual(len(result["root_approval_sha256"]), 64)

    def test_validation_is_read_only_for_project_state(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            approval = self.approval(plan)
            before = self.snapshot(root)
            validate_recovery_root_approval(root, plan, approval)
            self.assertEqual(self.snapshot(root), before)

    def test_missing_projection_uses_authoritative_history_without_rebuilding(self):
        td, root = self.root_project()
        with td:
            _, projection = operator_paths(root)
            projection.unlink()
            plan = self.plan()
            approval = self.approval(plan)
            validate_recovery_root_approval(root, plan, approval)
            self.assertFalse(projection.exists())

    def test_projection_conflict_blocks_root_authority(self):
        td, root = self.root_project()
        with td:
            _, projection = operator_paths(root)
            projection.write_bytes(b"{}\n")
            plan = self.plan()
            approval = self.approval(plan)
            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_REQUIRED",
                lambda: validate_recovery_root_approval(root, plan, approval),
            )

    def test_missing_root_history_blocks_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = self.plan()
            approval = self.approval(plan)
            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_REQUIRED",
                lambda: validate_recovery_root_approval(root, plan, approval),
            )

    def test_delegated_or_nonroot_operator_cannot_satisfy_recovery_approval(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            approval = self.approval(plan, root_id="operator:delegate")
            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_MISMATCH",
                lambda: validate_recovery_root_approval(root, plan, approval),
            )

    def test_root_transfer_after_approval_invalidates_old_root_binding(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            old_approval = self.approval(plan)
            validate_recovery_root_approval(root, plan, old_approval)

            add = plan_operator_change(root, "ADD_OPERATOR", "operator:next", list(CORE_CAPABILITIES))["proposal"]
            add_approval = approve_operator_change(add, "operator:root")
            self.assertEqual(apply_operator_change(root, add, add_approval)["status"], "PASS")
            transfer = plan_root_transfer(root, "operator:next")["proposal"]
            transfer_approval = approve_root_transfer(transfer, "operator:root")
            self.assertEqual(apply_root_transfer(root, transfer, transfer_approval)["status"], "PASS")

            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_MISMATCH",
                lambda: validate_recovery_root_approval(root, plan, old_approval),
            )
            validate_recovery_root_approval(root, plan, self.approval(plan, root_id="operator:next"))

    def test_approval_replay_against_another_generation_fails(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            approval = self.approval(plan)
            other = copy.deepcopy(plan)
            other["generation"] = "00000002"
            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_MISMATCH",
                lambda: validate_recovery_root_approval(root, other, approval),
            )

    def test_any_plan_change_after_approval_fails_digest_binding(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            approval = self.approval(plan)
            altered = copy.deepcopy(plan)
            altered["implementation_closure"]["recovery_executor"]["sha256"] = "4" * 64
            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_MISMATCH",
                lambda: validate_recovery_root_approval(root, altered, approval),
            )

    def test_wrong_project_plan_digest_confirmation_or_method_fails(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            cases = []
            wrong_project = self.approval(plan)
            wrong_project["project_id"] = "other-project"
            cases.append(wrong_project)
            wrong_digest = self.approval(plan)
            wrong_digest["recovery_plan_sha256"] = "0" * 64
            cases.append(wrong_digest)
            wrong_confirmation = self.approval(plan)
            wrong_confirmation["authentication"]["confirmation"] = "AUTHORIZE_EXCEPTIONAL_RECOVERY"
            cases.append(wrong_confirmation)
            wrong_method = self.approval(plan)
            wrong_method["authentication"]["method"] = "agent_claim"
            cases.append(wrong_method)
            for approval in cases:
                with self.subTest(approval=approval):
                    self.assert_code(
                        "ROOT_RECOVERY_APPROVAL_MISMATCH",
                        lambda approval=approval: validate_recovery_root_approval(root, plan, approval),
                    )

    def test_authentication_evidence_is_optional_canonical_data(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            approval = self.approval(plan)
            approval["authentication"]["evidence"] = {"interface": "test-human-interface", "confirmed": True}
            validate_recovery_root_approval(root, plan, approval)

    def test_extra_approval_or_authentication_fields_fail_closed(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            approval = self.approval(plan)
            approval["candidate_sha256"] = "1" * 64
            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_MISMATCH",
                lambda: validate_recovery_root_approval(root, plan, approval),
            )
            approval = self.approval(plan)
            approval["authentication"]["operator_claim"] = "human"
            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_MISMATCH",
                lambda: validate_recovery_root_approval(root, plan, approval),
            )

    def test_canonical_raw_approval_bytes_validate(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            approval = self.approval(plan)
            parsed, result = parse_and_validate_recovery_root_approval(root, plan, jcs(approval))
            self.assertEqual(parsed, approval)
            self.assertEqual(result["protected_root_id"], "operator:root")

    def test_noncanonical_or_duplicate_key_raw_approval_is_rejected(self):
        td, root = self.root_project()
        with td:
            plan = self.plan()
            approval = self.approval(plan)
            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_MISMATCH",
                lambda: parse_and_validate_recovery_root_approval(root, plan, jcs(approval) + b"\n"),
            )
            duplicate = (
                b'{"authentication":{"confirmation":"AUTHORIZE_CANONICAL_PEMS_COVE_RECOVERY","method":"human_confirmation"},'
                b'"contract":"reasoning-distiller-canonical-recovery-root-approval/1",'
                b'"contract":"reasoning-distiller-canonical-recovery-root-approval/1",'
                b'"generation":"00000001","project_id":"example-project",'
                b'"protected_root_id":"operator:root","recovery_plan_sha256":"' + recovery_plan_sha256(plan).encode("ascii") + b'"}'
            )
            self.assert_code(
                "ROOT_RECOVERY_APPROVAL_MISMATCH",
                lambda: parse_and_validate_recovery_root_approval(root, plan, duplicate),
            )


if __name__ == "__main__":
    unittest.main()
