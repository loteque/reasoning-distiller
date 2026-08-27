from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import sha256_bytes  # noqa: E402
from ril_canonical_recovery_approval import (  # noqa: E402
    recovery_plan_sha256,
    validate_recovery_root_approval,
)
from ril_canonical_recovery_executor import _postpublication_content_verified  # noqa: E402
from ril_canonical_recovery_planner import build_mode_a_recovery_plan  # noqa: E402
from ril_canonical_recovery_recipe import git_blob_sha1  # noqa: E402
from ril_canonical_store import CanonicalPairSnapshot  # noqa: E402
from ril_mutation import ContractError  # noqa: E402
from ril_storage_verification import verify_storage, verify_storage_snapshot  # noqa: E402


class CanonicalRecoveryG8IncidentRehearsal(unittest.TestCase):
    """Read-only CR2-CR9 rehearsal over the exact immutable incident pair."""

    PEMS_PATH = Path("project-knowledge/canonical/pems2.jcs.json")
    COVE_PATH = Path("project-knowledge/canonical/cove1.jcs.json")
    BLOCKER_PATH = Path("evaluation/context-packaging/blocker-evidence/2026-08-26-p3-pems-schema-invalid.json")
    RECEIPT_PATH = Path("project-knowledge/admission/receipts/35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json")

    PROJECT_ID = "reasoning-distiller"
    GENERATION = "2026-08-26-canonical-pems-cove-recovery-v1"
    PEMS_SHA256 = "22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061"
    COVE_SHA256 = "ce1f6dd7fe8889ce1bf126f7ec161b08fdc19a1705a2d5be350ed80b7d197e24"
    PEMS_GIT_BLOB = "bb7c474e935243b45ff02a5778a94bbcdc654d72"
    COVE_GIT_BLOB = "7ff52fb925a667c4cc1782da9b475dff831e45ef"
    BLOCKER_GIT_BLOB = "0f122f6d3a72571fbb51a8ad3083441d5f3440ab"
    RECEIPT_GIT_BLOB = "3d35dd4af7ab868262305a79a12cbe991d1d21ef"

    BEHAVIOR_DEPENDENCIES = (
        "runtime/ril_canonical_recovery_approval.py",
        "runtime/ril_mutation.py",
        "runtime/ril_operators.py",
        "runtime/ril_storage_verification.py",
    )

    def _build_plan(self, pems_bytes: bytes, cove_bytes: bytes):
        return build_mode_a_recovery_plan(
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

    def test_complete_g8_rehearsal_cr2_through_cr9(self):
        pems_bytes = (ROOT / self.PEMS_PATH).read_bytes()
        cove_bytes = (ROOT / self.COVE_PATH).read_bytes()
        blocker_bytes = (ROOT / self.BLOCKER_PATH).read_bytes()
        receipt_bytes = (ROOT / self.RECEIPT_PATH).read_bytes()
        immutable_inputs = {
            self.PEMS_PATH.as_posix(): pems_bytes,
            self.COVE_PATH.as_posix(): cove_bytes,
            self.BLOCKER_PATH.as_posix(): blocker_bytes,
            self.RECEIPT_PATH.as_posix(): receipt_bytes,
        }

        # CR2: bind the exact incident project and malformed pair identities.
        self.assertEqual(sha256_bytes(pems_bytes), self.PEMS_SHA256)
        self.assertEqual(sha256_bytes(cove_bytes), self.COVE_SHA256)
        self.assertEqual(git_blob_sha1(pems_bytes), self.PEMS_GIT_BLOB)
        self.assertEqual(git_blob_sha1(cove_bytes), self.COVE_GIT_BLOB)
        self.assertEqual(git_blob_sha1(blocker_bytes), self.BLOCKER_GIT_BLOB)
        self.assertEqual(git_blob_sha1(receipt_bytes), self.RECEIPT_GIT_BLOB)

        blocker = json.loads(blocker_bytes.decode("utf-8"))
        source = json.loads(pems_bytes.decode("utf-8"))
        self.assertIs(blocker["canonical_pems"]["semantic_present"], False)
        self.assertEqual(blocker["canonical_pems"]["top_level_keys"], ["project_id", "records", "relations"])
        self.assertNotIn("semantic", source)
        self.assertEqual(list(source), ["project_id", "records", "relations"])
        self.assertEqual(source["project_id"], self.PROJECT_ID)

        # CR3: ordinary R14 proves this exact Canon invalid. The exact repaired
        # pair passes the executor's content-valid predicate used by its
        # RECOVERY_NOT_REQUIRED branch, without requiring recovery provenance.
        current_verification = verify_storage(ROOT, ROOT)
        self.assertEqual(current_verification["status"], "FAIL")
        self.assertEqual(current_verification["outcome"], "PEMS_SCHEMA_INVALID")

        planned = self._build_plan(pems_bytes, cove_bytes)
        plan = planned.plan
        recipe = planned.recipe_candidate
        self.assertEqual(plan["project_id"], self.PROJECT_ID)
        self.assertEqual(plan["generation"], self.GENERATION)
        self.assertEqual(
            plan["prestate"],
            {
                "pems_sha256": self.PEMS_SHA256,
                "cove_sha256": self.COVE_SHA256,
                "pems_git_blob": self.PEMS_GIT_BLOB,
                "cove_git_blob": self.COVE_GIT_BLOB,
            },
        )

        candidate_snapshot = CanonicalPairSnapshot(
            state="PRESENT",
            pems_bytes=recipe.candidate_pems_bytes,
            cove_bytes=recipe.candidate_cove_bytes,
            pems_sha256=recipe.candidate_pems_sha256,
            cove_sha256=recipe.candidate_cove_sha256,
        )
        candidate_verification = verify_storage_snapshot(ROOT, ROOT, candidate_snapshot)
        self.assertEqual(candidate_verification["status"], "FAIL")
        self.assertIn(
            candidate_verification["outcome"],
            {
                "ADMISSION_RECEIPT_MISSING",
                "ADMISSION_RECEIPT_MISMATCH",
                "RECOVERY_PROVENANCE_MISSING",
                "RECOVERY_PROVENANCE_INVALID",
                "RECOVERY_PROVENANCE_MISMATCH",
                "RECOVERY_PROVENANCE_CONFLICT",
            },
        )
        self.assertTrue(_postpublication_content_verified(ROOT, ROOT, candidate_snapshot))

        # CR4: the exact malformed pair and selected immutable evidence are
        # digest-bound by the canonical preserved-evidence inventory.
        self.assertEqual(
            sha256_bytes(planned.preserved_evidence_inventory_bytes),
            planned.preserved_evidence_inventory_sha256,
        )
        self.assertEqual(
            plan["preserved_evidence_inventory_sha256"],
            planned.preserved_evidence_inventory_sha256,
        )
        inventory_entries = {
            entry["path"]: entry for entry in planned.preserved_evidence_inventory["entries"]
        }
        self.assertEqual(set(inventory_entries), set(immutable_inputs))
        for relative, raw in immutable_inputs.items():
            entry = inventory_entries[relative]
            self.assertEqual(entry["byte_length"], len(raw))
            self.assertEqual(entry["sha256"], sha256_bytes(raw))
            self.assertEqual(entry["git_blob"], git_blob_sha1(raw))

        # CR5: one closed Mode A recipe yields one deterministic candidate and
        # complete predicate/implementation proof. A second planning pass is
        # byte-identical.
        predicate_results = recipe.equivalence_proof["predicate_results"]
        self.assertEqual([item["id"] for item in predicate_results], list(range(1, 16)))
        self.assertTrue(all(item["passed"] for item in predicate_results))
        repeated = self._build_plan(pems_bytes, cove_bytes)
        self.assertEqual(repeated.plan_bytes, planned.plan_bytes)
        self.assertEqual(repeated.preserved_evidence_inventory_bytes, planned.preserved_evidence_inventory_bytes)
        self.assertEqual(repeated.recipe_candidate.candidate_pems_bytes, recipe.candidate_pems_bytes)
        self.assertEqual(repeated.recipe_candidate.candidate_cove_bytes, recipe.candidate_cove_bytes)
        self.assertEqual(repeated.recipe_candidate.equivalence_proof_bytes, recipe.equivalence_proof_bytes)

        # CR6: candidate PEMS is exactly the normalized current PEMS/2 document;
        # recipe predicates 7-9 and 11 cover normalization/schema/integrity/JCS.
        repaired = json.loads(recipe.candidate_pems_bytes.decode("utf-8"))
        self.assertEqual(repaired["project_id"], self.PROJECT_ID)
        self.assertEqual(repaired["semantic"], "pems/2")
        by_id = {item["id"]: item for item in predicate_results}
        for predicate_id in (7, 8, 9, 11):
            self.assertTrue(by_id[predicate_id]["passed"])

        # CR7: prestate COVE is only a witness; candidate COVE comes solely from
        # candidate PEMS and round-trips deterministically.
        for predicate_id in (10, 12, 13, 14):
            self.assertTrue(by_id[predicate_id]["passed"])
        self.assertEqual(
            plan["candidate"],
            {
                "pems_sha256": recipe.candidate_pems_sha256,
                "cove_sha256": recipe.candidate_cove_sha256,
            },
        )

        # CR8 rehearsal: bind the exact immutable approval target, including
        # generation and executor closure, and prove that no unapproved object
        # crosses the root gate. This creates no root approval.
        self.assertEqual(recovery_plan_sha256(plan), planned.plan_sha256)
        self.assertEqual(plan["generation"], self.GENERATION)
        self.assertIn("recovery_executor", plan["implementation_closure"])
        with self.assertRaises(ContractError) as approval_error:
            validate_recovery_root_approval(ROOT, plan, {})
        self.assertIn(
            approval_error.exception.code,
            {"ROOT_RECOVERY_APPROVAL_REQUIRED", "ROOT_RECOVERY_APPROVAL_MISMATCH"},
        )

        # CR9: the closed recipe has exactly the one representation-only delta
        # and explicitly requires no semantic judgment.
        restored = dict(repaired)
        del restored["semantic"]
        self.assertEqual(restored, source)
        self.assertEqual(
            recipe.equivalence_proof["semantic_delta"],
            {"operation": "insert_top_level_member", "key": "semantic", "value": "pems/2"},
        )
        self.assertIs(recipe.equivalence_proof["semantic_judgment_required"], False)

        # G8 is read-only. Re-read every incident/evidence input after all
        # rehearsal machinery and require byte identity.
        for relative, before in immutable_inputs.items():
            self.assertEqual((ROOT / relative).read_bytes(), before)

        rehearsal = {
            "cr2_exact_incident_binding": True,
            "cr3_recoverable_invalid_and_valid_content_predicate": True,
            "cr4_preservation_inventory_digest_bound": True,
            "cr5_single_closed_deterministic_candidate": True,
            "cr6_candidate_pems_valid": True,
            "cr7_cove_witness_and_roundtrip": True,
            "cr8_approval_target_bound_unapproved_rejected": True,
            "cr9_semantic_judgment_required": False,
            "candidate_pems_sha256": recipe.candidate_pems_sha256,
            "candidate_cove_sha256": recipe.candidate_cove_sha256,
            "equivalence_proof_sha256": recipe.equivalence_proof_sha256,
            "preserved_evidence_inventory_sha256": planned.preserved_evidence_inventory_sha256,
            "recovery_plan_sha256": planned.plan_sha256,
            "runtime_identity": plan["runtime_identity"],
            "g10_authorized": False,
            "root_approval_created": False,
            "canonical_mutation": False,
        }
        print("G8_REHEARSAL=" + json.dumps(rehearsal, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
