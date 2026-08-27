from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import encode_cove, jcs, sha256_bytes  # noqa: E402
from ril_canonical_recovery_approval import RECOVERY_CONFIRMATION, ROOT_APPROVAL_CONTRACT  # noqa: E402
from ril_canonical_recovery_executor import apply_mode_a_recovery  # noqa: E402
from ril_canonical_recovery_planner import build_mode_a_recovery_plan  # noqa: E402
from ril_canonical_recovery_recipe import git_blob_sha1  # noqa: E402
from ril_operator_management import (  # noqa: E402
    apply_operator_change,
    apply_root_transfer,
    approve_operator_change,
    approve_root_transfer,
    plan_operator_change,
    plan_root_transfer,
)
from ril_operators import CORE_CAPABILITIES, apply_initial_operator, approve_initial_operator, plan_initial_operator  # noqa: E402
from ril_storage_verification import verify_storage  # noqa: E402


class CanonicalRecoveryExecutorG6Tests(unittest.TestCase):
    BEHAVIOR_DEPENDENCIES = (
        "runtime/ril_canonical_recovery_approval.py",
        "runtime/ril_mutation.py",
        "runtime/ril_operators.py",
        "runtime/ril_storage_verification.py",
    )

    def valid_pems(self) -> dict:
        return {
            "semantic": "pems/2",
            "project_id": "example-project",
            "records": [
                {
                    "id": "example-project",
                    "kind": "project",
                    "lifecycle": "current",
                    "data": {
                        "name": "Example Project",
                        "repository": "example/project",
                        "summary": "G6 recovery executor fixture.",
                    },
                }
            ],
            "relations": [],
        }

    def prestate(self) -> tuple[bytes, bytes]:
        source = self.valid_pems()
        source.pop("semantic")
        return jcs(source), jcs(encode_cove(source))

    def project(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        proposal = plan_initial_operator(root, "operator:root")["proposal"]
        approval = approve_initial_operator(proposal, "operator:root")
        self.assertEqual(apply_initial_operator(root, proposal, approval)["status"], "PASS")
        canonical = root / "project-knowledge" / "canonical"
        canonical.mkdir(parents=True)
        pems, cove = self.prestate()
        (canonical / "pems2.jcs.json").write_bytes(pems)
        (canonical / "cove1.jcs.json").write_bytes(cove)
        evidence = root / "project-knowledge" / "admission" / "receipts"
        evidence.mkdir(parents=True)
        (evidence / "historical.json").write_bytes(b'{"historical":true}')
        return td, root

    def planned(self, root: Path, generation: str = "g6-fixture-0001"):
        pems, cove = self.prestate()
        return build_mode_a_recovery_plan(
            pems,
            cove,
            project_root=root,
            expected_project_id="example-project",
            generation=generation,
            expected_prestate_pems_sha256=sha256_bytes(pems),
            expected_prestate_cove_sha256=sha256_bytes(cove),
            expected_prestate_pems_git_blob=git_blob_sha1(pems),
            expected_prestate_cove_git_blob=git_blob_sha1(cove),
            selected_evidence_paths=("project-knowledge/admission/receipts/historical.json",),
            behavior_dependency_paths=self.BEHAVIOR_DEPENDENCIES,
            package_root=ROOT,
        )

    def approval_bytes(self, plan, root_id: str = "operator:root") -> bytes:
        return jcs(
            {
                "contract": ROOT_APPROVAL_CONTRACT,
                "project_id": plan.plan["project_id"],
                "generation": plan.plan["generation"],
                "recovery_plan_sha256": plan.plan_sha256,
                "protected_root_id": root_id,
                "authentication": {
                    "method": "human_confirmation",
                    "confirmation": RECOVERY_CONFIRMATION,
                },
            }
        )

    def canonical_bytes(self, root: Path) -> tuple[bytes, bytes]:
        canonical = root / "project-knowledge" / "canonical"
        return (canonical / "pems2.jcs.json").read_bytes(), (canonical / "cove1.jcs.json").read_bytes()

    def barrier(self, root: Path) -> Path:
        return root / "project-knowledge" / "recovery" / "canonical-pems-cove" / "active.json"

    def generation(self, root: Path, name: str = "g6-fixture-0001") -> Path:
        return root / "project-knowledge" / "recovery" / "canonical-pems-cove" / "generations" / name

    def apply(self, root: Path, plan, approval: bytes | None = None):
        return apply_mode_a_recovery(
            root,
            plan.plan_bytes,
            approval or self.approval_bytes(plan),
            plan.preserved_evidence_inventory_bytes,
            package_root=ROOT,
        )

    def test_exact_root_approved_recovery_publishes_pair_and_verified_completion(self):
        td, root = self.project()
        with td:
            before_pems, before_cove = self.canonical_bytes(root)
            plan = self.planned(root)
            result = self.apply(root, plan)
            self.assertEqual((result["status"], result["outcome"]), ("PASS", "RECOVERED"))
            self.assertEqual(self.canonical_bytes(root), (plan.recipe_candidate.candidate_pems_bytes, plan.recipe_candidate.candidate_cove_bytes))
            self.assertFalse(self.barrier(root).exists())
            generation = self.generation(root)
            self.assertEqual((generation / "prestate/pems2.raw").read_bytes(), before_pems)
            self.assertEqual((generation / "prestate/cove1.raw").read_bytes(), before_cove)
            self.assertEqual((generation / "plan.json").read_bytes(), plan.plan_bytes)
            self.assertEqual((generation / "inventory.json").read_bytes(), plan.preserved_evidence_inventory_bytes)
            self.assertEqual((generation / "equivalence-proof.json").read_bytes(), plan.recipe_candidate.equivalence_proof_bytes)
            self.assertTrue((generation / "completion.json").is_file())
            self.assertTrue((generation / "evidence/project-knowledge/admission/receipts/historical.json").is_file())
            self.assertFalse((root / "project-knowledge/admission/receipts").joinpath("recovery.json").exists())
            verified = verify_storage(root, ROOT)
            self.assertEqual((verified["status"], verified["outcome"]), ("PASS", "VERIFIED_RECOVERED"))

    def test_exact_completed_retry_is_no_change(self):
        td, root = self.project()
        with td:
            plan = self.planned(root)
            first = self.apply(root, plan)
            self.assertEqual(first["outcome"], "RECOVERED")
            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            second = self.apply(root, plan)
            after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual((second["status"], second["outcome"]), ("PASS", "NO_CHANGE"))
            self.assertEqual(before, after)

    def test_missing_or_wrong_root_approval_fails_before_recovery_state_mutation(self):
        td, root = self.project()
        with td:
            plan = self.planned(root)
            before = self.canonical_bytes(root)
            wrong = self.approval_bytes(plan, root_id="operator:delegate")
            result = self.apply(root, plan, wrong)
            self.assertEqual((result["status"], result["outcome"]), ("FAIL", "ROOT_RECOVERY_APPROVAL_MISMATCH"))
            self.assertEqual(self.canonical_bytes(root), before)
            self.assertFalse((root / "project-knowledge/recovery").exists())

    def test_root_transfer_after_approval_invalidates_apply(self):
        td, root = self.project()
        with td:
            plan = self.planned(root)
            approval = self.approval_bytes(plan)
            add = plan_operator_change(root, "ADD_OPERATOR", "operator:next", list(CORE_CAPABILITIES))["proposal"]
            self.assertEqual(apply_operator_change(root, add, approve_operator_change(add, "operator:root"))["status"], "PASS")
            transfer = plan_root_transfer(root, "operator:next")["proposal"]
            self.assertEqual(apply_root_transfer(root, transfer, approve_root_transfer(transfer, "operator:root"))["status"], "PASS")
            before = self.canonical_bytes(root)
            result = self.apply(root, plan, approval)
            self.assertEqual(result["outcome"], "ROOT_RECOVERY_APPROVAL_MISMATCH")
            self.assertEqual(self.canonical_bytes(root), before)
            self.assertFalse((root / "project-knowledge/recovery").exists())

    def test_prestate_drift_fails_before_recovery_state_mutation(self):
        td, root = self.project()
        with td:
            plan = self.planned(root)
            canonical = root / "project-knowledge/canonical/pems2.jcs.json"
            changed = bytearray(canonical.read_bytes()); changed[-1:] = b" "
            canonical.write_bytes(bytes(changed))
            result = self.apply(root, plan)
            self.assertEqual(result["outcome"], "CANONICAL_PRESTATE_MISMATCH")
            self.assertFalse((root / "project-knowledge/recovery").exists())

    def test_valid_canonical_state_returns_recovery_not_required(self):
        td, root = self.project()
        with td:
            plan = self.planned(root)
            canonical = root / "project-knowledge/canonical"
            canonical.joinpath("pems2.jcs.json").write_bytes(plan.recipe_candidate.candidate_pems_bytes)
            canonical.joinpath("cove1.jcs.json").write_bytes(plan.recipe_candidate.candidate_cove_bytes)
            result = self.apply(root, plan)
            self.assertEqual((result["status"], result["outcome"]), ("FAIL", "RECOVERY_NOT_REQUIRED"))
            self.assertFalse((root / "project-knowledge/recovery").exists())

    def test_publication_fault_rolls_back_exact_prestate_and_clears_barrier(self):
        td, root = self.project()
        with td:
            plan = self.planned(root)
            before = self.canonical_bytes(root)
            real_replace = os.replace
            calls = {"count": 0}

            def fail_second_replace(src, dst):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("fixture second publication failure")
                return real_replace(src, dst)

            with patch("ril_canonical_store.os.replace", side_effect=fail_second_replace):
                result = self.apply(root, plan)
            self.assertEqual((result["status"], result["outcome"]), ("FAIL", "RECOVERY_PUBLICATION_FAILED_ROLLED_BACK"))
            self.assertEqual(self.canonical_bytes(root), before)
            self.assertFalse(self.barrier(root).exists())
            self.assertFalse((self.generation(root) / "completion.json").exists())

    def test_crash_after_pems_publication_resumes_exact_transaction(self):
        td, root = self.project()
        with td:
            plan = self.planned(root)
            pre_pems, pre_cove = self.canonical_bytes(root)
            real_replace = os.replace
            calls = {"count": 0}

            def crash_second_replace(src, dst):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise KeyboardInterrupt("simulated process loss")
                return real_replace(src, dst)

            with self.assertRaises(KeyboardInterrupt):
                with patch("ril_canonical_store.os.replace", side_effect=crash_second_replace):
                    self.apply(root, plan)
            self.assertTrue(self.barrier(root).is_file())
            pems_now, cove_now = self.canonical_bytes(root)
            self.assertEqual(pems_now, plan.recipe_candidate.candidate_pems_bytes)
            self.assertEqual(cove_now, pre_cove)
            self.assertNotEqual(pems_now, pre_pems)

            resumed = self.apply(root, plan)
            self.assertEqual((resumed["status"], resumed["outcome"]), ("PASS", "RECOVERED"))
            self.assertFalse(self.barrier(root).exists())
            self.assertEqual(self.canonical_bytes(root), (plan.recipe_candidate.candidate_pems_bytes, plan.recipe_candidate.candidate_cove_bytes))

    def test_conflicting_active_barrier_fails_closed_and_remains(self):
        td, root = self.project()
        with td:
            plan = self.planned(root)
            real_replace = os.replace
            calls = {"count": 0}

            def crash_second_replace(src, dst):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise KeyboardInterrupt("simulated process loss")
                return real_replace(src, dst)

            with self.assertRaises(KeyboardInterrupt):
                with patch("ril_canonical_store.os.replace", side_effect=crash_second_replace):
                    self.apply(root, plan)
            barrier = self.barrier(root)
            value = __import__("json").loads(barrier.read_text())
            value["generation"] = "other-generation"
            barrier.write_bytes(jcs(value))
            result = self.apply(root, plan)
            self.assertEqual(result["outcome"], "RECOVERY_CONFLICT")
            self.assertTrue(barrier.exists())

    def test_executor_surface_has_no_role_steward_activation_or_semantic_authority_inputs(self):
        params = set(inspect.signature(apply_mode_a_recovery).parameters)
        self.assertEqual(
            params,
            {"project_root", "recovery_plan_bytes", "root_approval_bytes", "preserved_evidence_inventory_bytes", "package_root"},
        )
        for forbidden in ("role", "steward", "activation", "admission", "reconciliation", "semantic", "authority"):
            self.assertFalse(any(forbidden in name for name in params))


if __name__ == "__main__":
    unittest.main()
