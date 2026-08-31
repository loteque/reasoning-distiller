from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import sha256_bytes  # noqa: E402
from ril_canonical_recovery_recipe import git_blob_sha1  # noqa: E402
from ril_storage_verification import verify_storage  # noqa: E402


class CanonicalRecoveryG8IncidentRehearsal(unittest.TestCase):
    """Read-only CR2-CR9 rehearsal over the exact immutable incident pair."""

    PEMS_PATH = Path("project-knowledge/canonical/pems2.jcs.json")
    COVE_PATH = Path("project-knowledge/canonical/cove1.jcs.json")
    BLOCKER_PATH = Path("evaluation/context-packaging/blocker-evidence/2026-08-26-p3-pems-schema-invalid.json")
    HISTORICAL_G8_PATH = Path(
        "evaluation/context-packaging/canonical-recovery-rehearsal/2026-08-26-g8-blocked.json"
    )
    CORRECTIVE_G8_PATH = Path(
        "evaluation/context-packaging/canonical-recovery-rehearsal/2026-08-31-g8-corrected.json"
    )
    RECEIPT_PATH = Path(
        "project-knowledge/admission/receipts/"
        "35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json"
    )

    PROJECT_ID = "reasoning-distiller"
    PEMS_SHA256 = "22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061"
    COVE_SHA256 = "ce1f6dd7fe8889ce1bf126f7ec161b08fdc19a1705a2d5be350ed80b7d197e24"
    PEMS_GIT_BLOB = "bb7c474e935243b45ff02a5778a94bbcdc654d72"
    COVE_GIT_BLOB = "7ff52fb925a667c4cc1782da9b475dff831e45ef"
    BLOCKER_GIT_BLOB = "0f122f6d3a72571fbb51a8ad3083441d5f3440ab"
    HISTORICAL_G8_GIT_BLOB = "bb5a4dd13e38f83dbbefbf5ec1bfabb165eee9ed"
    RECEIPT_GIT_BLOB = "3d35dd4af7ab868262305a79a12cbe991d1d21ef"

    def test_complete_g8_rehearsal_cr2_through_cr9(self):
        pems_bytes = (ROOT / self.PEMS_PATH).read_bytes()
        cove_bytes = (ROOT / self.COVE_PATH).read_bytes()
        blocker_bytes = (ROOT / self.BLOCKER_PATH).read_bytes()
        historical_g8_bytes = (ROOT / self.HISTORICAL_G8_PATH).read_bytes()
        receipt_bytes = (ROOT / self.RECEIPT_PATH).read_bytes()
        corrective_g8_bytes = (ROOT / self.CORRECTIVE_G8_PATH).read_bytes()
        immutable_inputs = {
            self.PEMS_PATH.as_posix(): pems_bytes,
            self.COVE_PATH.as_posix(): cove_bytes,
            self.BLOCKER_PATH.as_posix(): blocker_bytes,
            self.HISTORICAL_G8_PATH.as_posix(): historical_g8_bytes,
            self.RECEIPT_PATH.as_posix(): receipt_bytes,
            self.CORRECTIVE_G8_PATH.as_posix(): corrective_g8_bytes,
        }

        # CR2: bind the exact selected incident pair and preserve the historical
        # evidence records without treating their derived diagnosis as byte truth.
        self.assertEqual(sha256_bytes(pems_bytes), self.PEMS_SHA256)
        self.assertEqual(sha256_bytes(cove_bytes), self.COVE_SHA256)
        self.assertEqual(git_blob_sha1(pems_bytes), self.PEMS_GIT_BLOB)
        self.assertEqual(git_blob_sha1(cove_bytes), self.COVE_GIT_BLOB)
        self.assertEqual(git_blob_sha1(blocker_bytes), self.BLOCKER_GIT_BLOB)
        self.assertEqual(git_blob_sha1(historical_g8_bytes), self.HISTORICAL_G8_GIT_BLOB)
        self.assertEqual(git_blob_sha1(receipt_bytes), self.RECEIPT_GIT_BLOB)

        source = json.loads(pems_bytes.decode("utf-8"))
        blocker = json.loads(blocker_bytes.decode("utf-8"))
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        historical_g8 = json.loads(historical_g8_bytes.decode("utf-8"))
        corrective_g8 = json.loads(corrective_g8_bytes.decode("utf-8"))

        self.assertEqual(source["project_id"], self.PROJECT_ID)
        self.assertEqual(source.get("semantic"), "pems/2")
        self.assertEqual(sorted(source), ["project_id", "records", "relations", "semantic"])

        # The historical blocker remains immutable evidence of what was recorded,
        # but its missing-semantic diagnosis is contradicted by the selected bytes
        # and was not emitted by the cited source run.
        self.assertIs(blocker["canonical_pems"]["semantic_present"], False)
        self.assertEqual(
            blocker["canonical_pems"]["top_level_keys"],
            ["project_id", "records", "relations"],
        )
        self.assertEqual(
            historical_g8["disposition"],
            "G8_INCIDENT_REHEARSAL_BLOCKED_UNSUPPORTED_CANONICAL_DAMAGE",
        )

        self.assertEqual(receipt["admitted_pems_sha256"], self.PEMS_SHA256)
        self.assertEqual(receipt["admitted_cove_sha256"], self.COVE_SHA256)

        # CR3 is terminal for this incident. R14 PASS means valid Canon, so the
        # recovery contract requires RECOVERY_NOT_REQUIRED and forbids entering
        # CR4-CR9 recovery construction for these bytes.
        current_verification = verify_storage(ROOT, ROOT)
        self.assertEqual(current_verification["status"], "PASS")
        self.assertEqual(current_verification["outcome"], "VERIFIED_ADMITTED")
        self.assertEqual(current_verification["provenance_class"], "VERIFIED_ADMITTED")
        self.assertEqual(current_verification["pems_sha256"], self.PEMS_SHA256)
        self.assertEqual(current_verification["cove_sha256"], self.COVE_SHA256)
        self.assertIn(self.RECEIPT_PATH.as_posix(), current_verification["provenance_paths"])

        disposition = "RECOVERY_NOT_REQUIRED"
        cr2_cr9 = {
            "CR2": "PASS",
            "CR3": "PASS_RECOVERY_NOT_REQUIRED",
            "CR4": "NOT_ENTERED_RECOVERY_NOT_REQUIRED",
            "CR5": "NOT_ENTERED_RECOVERY_NOT_REQUIRED",
            "CR6": "NOT_ENTERED_RECOVERY_NOT_REQUIRED",
            "CR7": "NOT_ENTERED_RECOVERY_NOT_REQUIRED",
            "CR8": "NOT_ENTERED_RECOVERY_NOT_REQUIRED",
            "CR9": "NOT_ENTERED_RECOVERY_NOT_REQUIRED",
        }

        self.assertEqual(corrective_g8["disposition"], disposition)
        self.assertEqual(corrective_g8["cr2_cr9"], cr2_cr9)
        self.assertEqual(corrective_g8["immutable_observation"]["pems_semantic"], "pems/2")
        self.assertEqual(
            corrective_g8["recovery_entry"],
            {
                "r14_status": "PASS",
                "r14_outcome": "VERIFIED_ADMITTED",
                "provenance_class": "VERIFIED_ADMITTED",
                "disposition": "RECOVERY_NOT_REQUIRED",
            },
        )
        self.assertEqual(
            corrective_g8["historical_blocker"]["diagnostic_provenance"],
            "UNESTABLISHED",
        )
        self.assertEqual(
            corrective_g8["root_cause"]["underlying_2026_08_26_schema_failure_cause"],
            "UNESTABLISHED",
        )
        self.assertFalse(corrective_g8["mutation_guards"]["mode_a_entered"])
        self.assertFalse(corrective_g8["mutation_guards"]["candidate_computed"])
        self.assertFalse(corrective_g8["mutation_guards"]["recovery_plan_computed"])
        self.assertFalse(corrective_g8["mutation_guards"]["protected_root_approval_created"])
        self.assertFalse(corrective_g8["mutation_guards"]["canon_mutated"])
        self.assertFalse(corrective_g8["mutation_guards"]["g10_performed"])
        self.assertFalse(corrective_g8["mutation_guards"]["p3_performed"])

        # G8 is read-only. Re-read every selected/evidence input after the
        # rehearsal and require byte identity.
        for relative, before in immutable_inputs.items():
            self.assertEqual((ROOT / relative).read_bytes(), before)

        rehearsal = {
            "phase": "G8",
            "status": "PASS",
            "disposition": disposition,
            "pems_git_blob": self.PEMS_GIT_BLOB,
            "pems_sha256": self.PEMS_SHA256,
            "cove_git_blob": self.COVE_GIT_BLOB,
            "cove_sha256": self.COVE_SHA256,
            "pems_semantic": "pems/2",
            "r14_status": current_verification["status"],
            "r14_outcome": current_verification["outcome"],
            "provenance_class": current_verification["provenance_class"],
            "cr2_cr9": cr2_cr9,
            "mode_a_entered": False,
            "candidate_computed": False,
            "recovery_plan_computed": False,
            "root_approval_created": False,
            "canonical_mutation": False,
            "g10_authorized": False,
        }
        print("G8_REHEARSAL=" + json.dumps(rehearsal, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
