from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import sha256_bytes  # noqa: E402
from ril_canonical_recovery_planner import build_mode_a_recovery_plan  # noqa: E402
from ril_canonical_recovery_recipe import git_blob_sha1  # noqa: E402


class CanonicalRecoveryG8IncidentRehearsal(unittest.TestCase):
    """Diagnostic pass over the exact immutable incident pair for G8 remediation."""

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

    def test_emit_exact_g8_rehearsal_identities(self):
        pems_bytes = (ROOT / self.PEMS_PATH).read_bytes()
        cove_bytes = (ROOT / self.COVE_PATH).read_bytes()
        blocker_bytes = (ROOT / self.BLOCKER_PATH).read_bytes()
        receipt_bytes = (ROOT / self.RECEIPT_PATH).read_bytes()

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
        recipe = planned.recipe_candidate
        repaired = json.loads(recipe.candidate_pems_bytes.decode("utf-8"))
        self.assertEqual(repaired["semantic"], "pems/2")
        restored = dict(repaired)
        del restored["semantic"]
        self.assertEqual(restored, source)
        self.assertTrue(all(item["passed"] for item in recipe.equivalence_proof["predicate_results"]))
        self.assertIs(recipe.equivalence_proof["semantic_judgment_required"], False)

        diagnostic = {
            "candidate_pems_sha256": recipe.candidate_pems_sha256,
            "candidate_cove_sha256": recipe.candidate_cove_sha256,
            "equivalence_proof_sha256": recipe.equivalence_proof_sha256,
            "preserved_evidence_inventory_sha256": planned.preserved_evidence_inventory_sha256,
            "recovery_plan_sha256": planned.plan_sha256,
            "runtime_identity": planned.plan["runtime_identity"],
        }
        self.fail("G8_DIAGNOSTIC=" + json.dumps(diagnostic, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
