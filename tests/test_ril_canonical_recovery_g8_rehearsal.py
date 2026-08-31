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
from ril_mutation import ContractError  # noqa: E402
from ril_storage_verification import verify_storage  # noqa: E402


class CanonicalRecoveryG8IncidentRehearsal(unittest.TestCase):
    """Read-only CR2-CR9 rehearsal over the exact immutable incident pair."""

    PEMS_PATH = Path("project-knowledge/canonical/pems2.jcs.json")
    COVE_PATH = Path("project-knowledge/canonical/cove1.jcs.json")
    BLOCKER_PATH = Path(
        "evaluation/context-packaging/blocker-evidence/"
        "2026-08-26-p3-pems-schema-invalid.json"
    )
    HISTORICAL_G8_PATH = Path(
        "evaluation/context-packaging/canonical-recovery-rehearsal/"
        "2026-08-26-g8-blocked.json"
    )
    CORRECTIVE_G8_PATH = Path(
        "evaluation/context-packaging/canonical-recovery-rehearsal/"
        "2026-08-31-g8-corrected.json"
    )
    RECEIPT_PATH = Path(
        "project-knowledge/admission/receipts/"
        "35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json"
    )
    SOURCE_SCHEMA_PATH = Path(
        ".reasoning-distiller/backends/pems-cove/pems-v2.schema.json"
    )

    PROJECT_ID = "reasoning-distiller"
    GENERATION = "2026-08-26-canonical-pems-cove-recovery-v1"
    PEMS_SHA256 = "22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061"
    COVE_SHA256 = "ce1f6dd7fe8889ce1bf126f7ec161b08fdc19a1705a2d5be350ed80b7d197e24"
    PEMS_GIT_BLOB = "bb7c474e935243b45ff02a5778a94bbcdc654d72"
    COVE_GIT_BLOB = "7ff52fb925a667c4cc1782da9b475dff831e45ef"
    BLOCKER_GIT_BLOB = "0f122f6d3a72571fbb51a8ad3083441d5f3440ab"
    HISTORICAL_G8_GIT_BLOB = "bb5a4dd13e38f83dbbefbf5ec1bfabb165eee9ed"
    RECEIPT_GIT_BLOB = "3d35dd4af7ab868262305a79a12cbe991d1d21ef"
    SOURCE_SCHEMA_GIT_BLOB = "cd7683d704e8aef2842a0c1b25b453fb1dbc8030"

    BEHAVIOR_DEPENDENCIES = (
        "runtime/ril_canonical_recovery_approval.py",
        "runtime/ril_mutation.py",
        "runtime/ril_operators.py",
        "runtime/ril_storage_verification.py",
    )

    CR2_CR9 = {
        "CR2": "PASS",
        "CR3": "FAIL_NOT_ACCEPTED_MODE_A_RECOVERABLE_CLASS",
        "CR4": "NOT_REACHED_CR3_FAILED",
        "CR5": "FAIL_CLOSED_MODE_A_PREDICATE_2",
        "CR6": "NOT_REACHED_MODE_A_INELIGIBLE",
        "CR7": "NOT_REACHED_MODE_A_INELIGIBLE",
        "CR8": "NOT_REACHED_NO_RECOVERY_PLAN",
        "CR9": "NOT_REACHED_MODE_A_INELIGIBLE",
    }

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
            selected_evidence_paths=(
                self.BLOCKER_PATH.as_posix(),
                self.HISTORICAL_G8_PATH.as_posix(),
                self.RECEIPT_PATH.as_posix(),
            ),
            behavior_dependency_paths=self.BEHAVIOR_DEPENDENCIES,
            package_root=ROOT,
        )

    def test_complete_g8_rehearsal_cr2_through_cr9(self):
        pems_bytes = (ROOT / self.PEMS_PATH).read_bytes()
        cove_bytes = (ROOT / self.COVE_PATH).read_bytes()
        blocker_bytes = (ROOT / self.BLOCKER_PATH).read_bytes()
        historical_g8_bytes = (ROOT / self.HISTORICAL_G8_PATH).read_bytes()
        receipt_bytes = (ROOT / self.RECEIPT_PATH).read_bytes()
        corrective_g8_bytes = (ROOT / self.CORRECTIVE_G8_PATH).read_bytes()
        source_schema_bytes = (ROOT / self.SOURCE_SCHEMA_PATH).read_bytes()
        immutable_inputs = {
            self.PEMS_PATH.as_posix(): pems_bytes,
            self.COVE_PATH.as_posix(): cove_bytes,
            self.BLOCKER_PATH.as_posix(): blocker_bytes,
            self.HISTORICAL_G8_PATH.as_posix(): historical_g8_bytes,
            self.RECEIPT_PATH.as_posix(): receipt_bytes,
            self.CORRECTIVE_G8_PATH.as_posix(): corrective_g8_bytes,
            self.SOURCE_SCHEMA_PATH.as_posix(): source_schema_bytes,
        }

        # CR2: bind the selected incident bytes and preserved historical evidence.
        self.assertEqual(sha256_bytes(pems_bytes), self.PEMS_SHA256)
        self.assertEqual(sha256_bytes(cove_bytes), self.COVE_SHA256)
        self.assertEqual(git_blob_sha1(pems_bytes), self.PEMS_GIT_BLOB)
        self.assertEqual(git_blob_sha1(cove_bytes), self.COVE_GIT_BLOB)
        self.assertEqual(git_blob_sha1(blocker_bytes), self.BLOCKER_GIT_BLOB)
        self.assertEqual(git_blob_sha1(historical_g8_bytes), self.HISTORICAL_G8_GIT_BLOB)
        self.assertEqual(git_blob_sha1(receipt_bytes), self.RECEIPT_GIT_BLOB)
        self.assertEqual(git_blob_sha1(source_schema_bytes), self.SOURCE_SCHEMA_GIT_BLOB)

        source = json.loads(pems_bytes.decode("utf-8"))
        blocker = json.loads(blocker_bytes.decode("utf-8"))
        historical_g8 = json.loads(historical_g8_bytes.decode("utf-8"))
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        source_schema = json.loads(source_schema_bytes.decode("utf-8"))
        corrective_g8 = json.loads(corrective_g8_bytes.decode("utf-8"))

        self.assertEqual(source["project_id"], self.PROJECT_ID)
        self.assertEqual(source.get("semantic"), "pems/2")
        self.assertEqual(
            sorted(source),
            ["project_id", "records", "relations", "semantic"],
        )
        self.assertTrue(source["relations"])
        self.assertNotIn("lifecycle", source["relations"][0])
        self.assertNotIn("data", source["relations"][0])
        self.assertIn("lifecycle", source_schema["$defs"]["relation"]["required"])
        self.assertIn("data", source_schema["$defs"]["relation"]["required"])

        # Preserve the historical assertions as evidence, but do not promote
        # their unestablished missing-semantic diagnosis over immutable bytes.
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

        # CR3: live R14 proves the exact pair invalid, but not in the one
        # accepted Mode A class. The failure is relation-schema damage, not a
        # missing top-level semantic discriminator.
        current_verification = verify_storage(ROOT, ROOT)
        self.assertEqual(
            current_verification["contract"],
            "reasoning-distiller-storage-verification-result/2",
        )
        self.assertEqual(current_verification["status"], "FAIL")
        self.assertEqual(current_verification["outcome"], "PEMS_SCHEMA_INVALID")
        detail = current_verification["detail"]
        self.assertIn(
            "['relations', 0]: 'lifecycle' is a required property",
            detail,
        )
        self.assertIn(
            "['relations', 0]: 'data' is a required property",
            detail,
        )
        self.assertNotIn("'semantic' is a required property", detail)

        # CR5 predicate probe: the closed V1 planner is read-only and must
        # reject before producing any candidate or plan because semantic exists.
        with self.assertRaises(ContractError) as plan_error:
            self._build_plan(pems_bytes, cove_bytes)
        self.assertEqual(plan_error.exception.code, "UNSUPPORTED_CANONICAL_DAMAGE")
        self.assertEqual(
            plan_error.exception.detail,
            "prestate must be an object with no top-level semantic key",
        )

        # CR4 and CR6-CR9 are not entered after CR3/CR5 establish that the only
        # accepted recipe is ineligible. No semantic repair is attempted.
        self.assertEqual(
            corrective_g8["disposition"],
            "G8_INCIDENT_REHEARSAL_BLOCKED_UNSUPPORTED_CANONICAL_DAMAGE",
        )
        self.assertEqual(
            corrective_g8["stable_outcome"],
            "UNSUPPORTED_CANONICAL_DAMAGE",
        )
        self.assertEqual(corrective_g8["cr2_cr9"], self.CR2_CR9)
        self.assertEqual(
            corrective_g8["immutable_observation"]["pems_semantic"],
            "pems/2",
        )
        self.assertEqual(
            corrective_g8["r14"]["outcome"],
            "PEMS_SCHEMA_INVALID",
        )
        self.assertEqual(
            corrective_g8["mode_a_probe"],
            {
                "candidate_count": 0,
                "error_code": "UNSUPPORTED_CANONICAL_DAMAGE",
                "error_detail": "prestate must be an object with no top-level semantic key",
                "predicate_failure": 2,
                "recovery_plan_computed": False,
            },
        )
        self.assertEqual(
            corrective_g8["root_cause"]["reconstructed_source_failure_cause"],
            "PEMS relation objects omit schema-required lifecycle/data fields.",
        )
        self.assertEqual(
            corrective_g8["root_cause"]["historical_missing_semantic_diagnosis"],
            "CONTRADICTED_BY_IMMUTABLE_PEMS",
        )
        self.assertFalse(
            corrective_g8["root_cause"]["source_run_emitted_missing_semantic_diagnosis"]
        )

        for field in (
            "candidate_computed",
            "recovery_plan_computed",
            "protected_root_approval_created",
            "canon_mutated",
            "g10_performed",
            "p3_performed",
            "semantic_judgment_performed",
        ):
            self.assertFalse(corrective_g8["mutation_guards"][field])

        # G8 is read-only. Re-read every selected/evidence/implementation input.
        for relative, before in immutable_inputs.items():
            self.assertEqual((ROOT / relative).read_bytes(), before)

        rehearsal = {
            "phase": "G8",
            "status": "PASS_FAIL_CLOSED",
            "disposition": "G8_INCIDENT_REHEARSAL_BLOCKED_UNSUPPORTED_CANONICAL_DAMAGE",
            "stable_outcome": "UNSUPPORTED_CANONICAL_DAMAGE",
            "pems_git_blob": self.PEMS_GIT_BLOB,
            "pems_sha256": self.PEMS_SHA256,
            "cove_git_blob": self.COVE_GIT_BLOB,
            "cove_sha256": self.COVE_SHA256,
            "pems_semantic": source["semantic"],
            "r14_status": current_verification["status"],
            "r14_outcome": current_verification["outcome"],
            "r14_detail": detail,
            "mode_a_error_code": plan_error.exception.code,
            "mode_a_error_detail": plan_error.exception.detail,
            "candidate_count": 0,
            "recovery_plan_computed": False,
            "cr2_cr9": self.CR2_CR9,
            "root_approval_created": False,
            "canonical_mutation": False,
            "g10_authorized": False,
            "semantic_judgment_performed": False,
        }
        print(
            "G8_REHEARSAL="
            + json.dumps(rehearsal, sort_keys=True, separators=(",", ":"))
        )


if __name__ == "__main__":
    unittest.main()
