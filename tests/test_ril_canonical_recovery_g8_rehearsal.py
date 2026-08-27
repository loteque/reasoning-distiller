from __future__ import annotations

import base64
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import jcs, sha256_bytes  # noqa: E402
from ril_canonical_recovery_approval import (  # noqa: E402
    RECOVERY_CONFIRMATION,
    ROOT_APPROVAL_CONTRACT,
    validate_recovery_root_approval,
)
from ril_canonical_recovery_executor import apply_mode_a_recovery  # noqa: E402
from ril_canonical_recovery_planner import build_mode_a_recovery_plan  # noqa: E402
from ril_canonical_recovery_recipe import git_blob_sha1  # noqa: E402
from ril_operators import apply_initial_operator, approve_initial_operator, plan_initial_operator  # noqa: E402
from ril_storage_verification import verify_storage  # noqa: E402


class CanonicalRecoveryG8IncidentRehearsal(unittest.TestCase):
    """Read-only rehearsal of the exact blocked canonical PEMS/COVE incident."""

    PEMS_PATH = Path("project-knowledge/canonical/pems2.jcs.json")
    COVE_PATH = Path("project-knowledge/canonical/cove1.jcs.json")
    BLOCKER_PATH = Path("evaluation/context-packaging/blocker-evidence/2026-08-26-p3-pems-schema-invalid.json")
    RECEIPT_PATH = Path("project-knowledge/admission/receipts/35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json")
    REHEARSAL_PATH = Path("evaluation/context-packaging/canonical-recovery-rehearsal/2026-08-26-g8.json")

    PROJECT_ID = "reasoning-distiller"
    GENERATION = "2026-08-26-canonical-pems-cove-recovery-v1"
    PEMS_SHA256 = "22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061"
    COVE_SHA256 = "ce1f6dd7fe8889ce1bf126f7ec161b08fdc19a1705a2d5be350ed80b7d197e24"
    PEMS_GIT_BLOB = "bb7c474e935243b45ff02a5778a94bbcdc654d72"
    COVE_GIT_BLOB = "7ff52fb925a667c4cc1782da9b475dff831e45ef"
    BLOCKER_GIT_BLOB = "0f122f6d3a72571fbb51a8ad3083441d5f3440ab"
    RECEIPT_GIT_BLOB = "3d35dd4af7ab868262305a79a12cbe991d1d21ef"
    COORDINATION_REVISION = "d46300a54a444cc866717986c1f5b493de3ab13f"

    BEHAVIOR_DEPENDENCIES = (
        "runtime/ril_canonical_recovery_approval.py",
        "runtime/ril_mutation.py",
        "runtime/ril_operators.py",
        "runtime/ril_storage_verification.py",
    )

    def copy_relative(self, target_root: Path, relative: Path) -> None:
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)

    def snapshot_recovery_tree(self) -> dict[str, bytes]:
        recovery = ROOT / "project-knowledge/recovery/canonical-pems-cove"
        if not recovery.exists():
            return {}
        return {
            path.relative_to(recovery).as_posix(): path.read_bytes()
            for path in sorted(recovery.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def test_exact_incident_rehearsal_freezes_cr2_through_cr9(self):
        pems_bytes = (ROOT / self.PEMS_PATH).read_bytes()
        cove_bytes = (ROOT / self.COVE_PATH).read_bytes()
        blocker_bytes = (ROOT / self.BLOCKER_PATH).read_bytes()
        receipt_bytes = (ROOT / self.RECEIPT_PATH).read_bytes()
        live_recovery_before = self.snapshot_recovery_tree()

        # CR2: the rehearsal source is the exact immutable blocked pair.
        self.assertEqual(sha256_bytes(pems_bytes), self.PEMS_SHA256)
        self.assertEqual(sha256_bytes(cove_bytes), self.COVE_SHA256)
        self.assertEqual(git_blob_sha1(pems_bytes), self.PEMS_GIT_BLOB)
        self.assertEqual(git_blob_sha1(cove_bytes), self.COVE_GIT_BLOB)
        self.assertEqual(git_blob_sha1(blocker_bytes), self.BLOCKER_GIT_BLOB)
        self.assertEqual(git_blob_sha1(receipt_bytes), self.RECEIPT_GIT_BLOB)

        blocker = json.loads(blocker_bytes.decode("utf-8"))
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        self.assertEqual(blocker["status"], "BLOCKED_PEMS_SCHEMA_INVALID")
        self.assertEqual(blocker["coordination_revision"], self.COORDINATION_REVISION)
        self.assertEqual(blocker["canonical_pems"]["git_blob"], self.PEMS_GIT_BLOB)
        self.assertEqual(blocker["canonical_cove"]["git_blob"], self.COVE_GIT_BLOB)
        self.assertEqual(blocker["observed_p3_failure"]["code"], "PEMS_SCHEMA_INVALID")
        self.assertEqual(blocker["standing_evidence"]["admission_receipt_git_blob"], self.RECEIPT_GIT_BLOB)
        self.assertEqual(receipt["admitted_pems_sha256"], self.PEMS_SHA256)
        self.assertEqual(receipt["admitted_cove_sha256"], self.COVE_SHA256)

        planned = build_mode_a_recovery_plan(
            pems_bytes,
            cove_bytes,
            project_root=ROOT,
            expected_project_id=self.PROJECT_ID,
            generation=self.GENERATION,
            expected_prestate_pems_sha256=self.PEMS_SHA256,
            expected_prestate_cove_sha256=self.COVE_SHA256,
            expected_prestate_pems_git_blob=self.PEMS_GIT_BLOB,
            expected_prestate_cove_git_blob=self.COVE_GIT_BLOB,
            selected_evidence_paths=(self.BLOCKER_PATH.as_posix(), self.RECEIPT_PATH.as_posix()),
            behavior_dependency_paths=self.BEHAVIOR_DEPENDENCIES,
            package_root=ROOT,
        )
        repeated = build_mode_a_recovery_plan(
            pems_bytes,
            cove_bytes,
            project_root=ROOT,
            expected_project_id=self.PROJECT_ID,
            generation=self.GENERATION,
            expected_prestate_pems_sha256=self.PEMS_SHA256,
            expected_prestate_cove_sha256=self.COVE_SHA256,
            expected_prestate_pems_git_blob=self.PEMS_GIT_BLOB,
            expected_prestate_cove_git_blob=self.COVE_GIT_BLOB,
            selected_evidence_paths=(self.RECEIPT_PATH.as_posix(), self.BLOCKER_PATH.as_posix()),
            behavior_dependency_paths=self.BEHAVIOR_DEPENDENCIES,
            package_root=ROOT,
        )
        self.assertEqual(repeated.plan_bytes, planned.plan_bytes)
        self.assertEqual(repeated.preserved_evidence_inventory_bytes, planned.preserved_evidence_inventory_bytes)

        proof = planned.recipe_candidate.equivalence_proof
        predicates = proof["predicate_results"]
        self.assertEqual([item["id"] for item in predicates], list(range(1, 16)))
        self.assertTrue(all(item["passed"] is True for item in predicates))

        # CR4: the exact Git-backed malformed pair plus exact blocker/receipt are digest-bound by the plan inventory.
        inventory_by_path = {
            entry["path"]: entry for entry in planned.preserved_evidence_inventory["entries"]
        }
        self.assertEqual(
            set(inventory_by_path),
            {self.PEMS_PATH.as_posix(), self.COVE_PATH.as_posix(), self.BLOCKER_PATH.as_posix(), self.RECEIPT_PATH.as_posix()},
        )
        self.assertEqual(inventory_by_path[self.PEMS_PATH.as_posix()]["git_blob"], self.PEMS_GIT_BLOB)
        self.assertEqual(inventory_by_path[self.COVE_PATH.as_posix()]["git_blob"], self.COVE_GIT_BLOB)
        self.assertEqual(inventory_by_path[self.BLOCKER_PATH.as_posix()]["git_blob"], self.BLOCKER_GIT_BLOB)
        self.assertEqual(inventory_by_path[self.RECEIPT_PATH.as_posix()]["git_blob"], self.RECEIPT_GIT_BLOB)

        # CR5-CR7 and CR9 are mechanically proven by the closed recipe proof.
        self.assertEqual(proof["project_id"], self.PROJECT_ID)
        self.assertEqual(proof["semantic_delta"], {"operation": "insert_top_level_member", "key": "semantic", "value": "pems/2"})
        self.assertIs(proof["semantic_judgment_required"], False)
        self.assertEqual(proof["candidate"]["cove_tuple"], "cove/1|pems/2|jcs/1")

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            for relative in (self.BLOCKER_PATH, self.RECEIPT_PATH):
                self.copy_relative(project, relative)
            canonical = project / "project-knowledge/canonical"
            canonical.mkdir(parents=True, exist_ok=True)
            (canonical / "pems2.jcs.json").write_bytes(pems_bytes)
            (canonical / "cove1.jcs.json").write_bytes(cove_bytes)

            # CR3: ordinary verification reproduces the accepted malformed class.
            malformed = verify_storage(project, ROOT)
            self.assertEqual((malformed["status"], malformed["outcome"]), ("FAIL", "PEMS_SCHEMA_INVALID"))

            # Recompute the exact incident plan from copied immutable evidence. It must be byte-identical.
            copied_plan = build_mode_a_recovery_plan(
                pems_bytes,
                cove_bytes,
                project_root=project,
                expected_project_id=self.PROJECT_ID,
                generation=self.GENERATION,
                expected_prestate_pems_sha256=self.PEMS_SHA256,
                expected_prestate_cove_sha256=self.COVE_SHA256,
                expected_prestate_pems_git_blob=self.PEMS_GIT_BLOB,
                expected_prestate_cove_git_blob=self.COVE_GIT_BLOB,
                selected_evidence_paths=(self.BLOCKER_PATH.as_posix(), self.RECEIPT_PATH.as_posix()),
                behavior_dependency_paths=self.BEHAVIOR_DEPENDENCIES,
                package_root=ROOT,
            )
            self.assertEqual(copied_plan.plan_bytes, planned.plan_bytes)

            # CR8 rehearsal only: validate the exact plan digest under an isolated protected-root history.
            initial = plan_initial_operator(project, "operator:g8-rehearsal-root")["proposal"]
            initial_approval = approve_initial_operator(initial, "operator:g8-rehearsal-root")
            self.assertEqual(apply_initial_operator(project, initial, initial_approval)["status"], "PASS")
            root_approval = {
                "contract": ROOT_APPROVAL_CONTRACT,
                "project_id": self.PROJECT_ID,
                "generation": self.GENERATION,
                "recovery_plan_sha256": planned.plan_sha256,
                "protected_root_id": "operator:g8-rehearsal-root",
                "authentication": {
                    "method": "human_confirmation",
                    "confirmation": RECOVERY_CONFIRMATION,
                    "evidence": {"purpose": "G8 isolated approval-binding rehearsal only"},
                },
            }
            root_binding = validate_recovery_root_approval(project, planned.plan, root_approval)
            self.assertEqual(root_binding["recovery_plan_sha256"], planned.plan_sha256)

            # CR3 valid-state side: content-valid repaired Canon must refuse exceptional recovery.
            (canonical / "pems2.jcs.json").write_bytes(planned.recipe_candidate.candidate_pems_bytes)
            (canonical / "cove1.jcs.json").write_bytes(planned.recipe_candidate.candidate_cove_bytes)
            content = verify_storage(project, ROOT)
            self.assertEqual(content["status"], "FAIL")
            self.assertEqual(content["outcome"], "ADMISSION_RECEIPT_MISMATCH")
            no_recovery = apply_mode_a_recovery(
                project,
                planned.plan_bytes,
                jcs(root_approval),
                planned.preserved_evidence_inventory_bytes,
                package_root=ROOT,
            )
            self.assertEqual((no_recovery["status"], no_recovery["outcome"]), ("FAIL", "RECOVERY_NOT_REQUIRED"))
            self.assertFalse((project / "project-knowledge/recovery/canonical-pems-cove").exists())

        rehearsal = {
            "artifact_kind": "derived_read_only_rehearsal",
            "gate": "G8",
            "project_id": self.PROJECT_ID,
            "coordination_revision": self.COORDINATION_REVISION,
            "generation": self.GENERATION,
            "source_incident": {
                "pems_sha256": self.PEMS_SHA256,
                "pems_git_blob": self.PEMS_GIT_BLOB,
                "cove_sha256": self.COVE_SHA256,
                "cove_git_blob": self.COVE_GIT_BLOB,
                "blocker_path": self.BLOCKER_PATH.as_posix(),
                "blocker_git_blob": self.BLOCKER_GIT_BLOB,
                "historical_receipt_path": self.RECEIPT_PATH.as_posix(),
                "historical_receipt_git_blob": self.RECEIPT_GIT_BLOB,
            },
            "expected_repaired_pair": {
                "pems_sha256": planned.recipe_candidate.candidate_pems_sha256,
                "pems_git_blob": git_blob_sha1(planned.recipe_candidate.candidate_pems_bytes),
                "cove_sha256": planned.recipe_candidate.candidate_cove_sha256,
                "cove_git_blob": git_blob_sha1(planned.recipe_candidate.candidate_cove_bytes),
            },
            "equivalence_proof_sha256": planned.recipe_candidate.equivalence_proof_sha256,
            "preserved_evidence_inventory_sha256": planned.preserved_evidence_inventory_sha256,
            "recovery_plan_sha256": planned.plan_sha256,
            "recovery_plan": planned.plan,
            "cr2_cr9": {
                "CR2": {"rehearsal_passed": True, "proof": "exact project identity plus prestate SHA-256 and Git blob identities matched"},
                "CR3": {"rehearsal_passed": True, "malformed_outcome": "PEMS_SCHEMA_INVALID", "valid_outcome": "RECOVERY_NOT_REQUIRED"},
                "CR4": {"rehearsal_passed": True, "proof": "Git-backed malformed pair and selected blocker/receipt evidence are inventory-digest-bound; G10 persistence remains unapplied"},
                "CR5": {"rehearsal_passed": True, "predicate_count": 15, "candidate_count": 1},
                "CR6": {"rehearsal_passed": True, "proof": "closed recipe passed exact schema, integrity, project identity, and normalization predicates"},
                "CR7": {"rehearsal_passed": True, "proof": "prestate COVE witness and regenerated candidate COVE exact round-trip predicates passed"},
                "CR8": {
                    "rehearsal_passed": True,
                    "approval_target_sha256": planned.plan_sha256,
                    "isolated_root_approval_sha256": root_binding["root_approval_sha256"],
                    "live_operational_gate_satisfied": False,
                    "g10_requires_fresh_direct_live_approval": True,
                },
                "CR9": {"rehearsal_passed": True, "semantic_judgment_required": False},
            },
            "live_effects": {
                "canonical_mutation": False,
                "recovery_standing_mutation": False,
                "protected_root_approval_created": False,
                "g10_operation_performed": False,
                "p3_performed": False,
            },
        }

        # The checked-in artifact is a freeze of this deterministic result, never an input to the planner.
        artifact = ROOT / self.REHEARSAL_PATH
        if not artifact.exists():
            encoded = base64.b64encode(jcs(rehearsal)).decode("ascii")
            self.fail("G8_REHEARSAL_FREEZE_REQUIRED_BASE64=" + encoded)
        stored = json.loads(artifact.read_text(encoding="utf-8"))
        self.assertEqual(jcs(stored), jcs(rehearsal))

        self.assertEqual((ROOT / self.PEMS_PATH).read_bytes(), pems_bytes)
        self.assertEqual((ROOT / self.COVE_PATH).read_bytes(), cove_bytes)
        self.assertEqual(self.snapshot_recovery_tree(), live_recovery_before)


if __name__ == "__main__":
    unittest.main()
