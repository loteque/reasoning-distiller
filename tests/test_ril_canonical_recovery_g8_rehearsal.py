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


class CanonicalRecoveryG8IncidentRehearsal(unittest.TestCase):
    """Fail-closed read-only rehearsal of the exact selected incident evidence."""

    PEMS_PATH = Path("project-knowledge/canonical/pems2.jcs.json")
    COVE_PATH = Path("project-knowledge/canonical/cove1.jcs.json")
    BLOCKER_PATH = Path("evaluation/context-packaging/blocker-evidence/2026-08-26-p3-pems-schema-invalid.json")
    RECEIPT_PATH = Path("project-knowledge/admission/receipts/35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json")
    REHEARSAL_PATH = Path("evaluation/context-packaging/canonical-recovery-rehearsal/2026-08-26-g8-blocked.json")

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

    def snapshot_recovery_tree(self) -> dict[str, bytes]:
        recovery = ROOT / "project-knowledge/recovery/canonical-pems-cove"
        if not recovery.exists():
            return {}
        return {
            path.relative_to(recovery).as_posix(): path.read_bytes()
            for path in sorted(recovery.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def expected_rehearsal(self) -> dict:
        return {
            "artifact_kind": "derived_read_only_rehearsal",
            "boundary": {
                "alternate_recipe_authorized": False,
                "canonical_mutation_performed": False,
                "evidence_reconciliation_performed": False,
                "g10_operation_performed": False,
                "p3_performed": False,
                "protected_root_approval_created": False,
                "recovery_standing_mutation_performed": False,
            },
            "coordination_revision": self.COORDINATION_REVISION,
            "cr2_cr9": {
                "CR2": {
                    "status": "PASS",
                    "proof": "Exact selected PEMS/COVE SHA-256 and Git blob identities matched the incident bindings.",
                },
                "CR3": {
                    "status": "NOT_ESTABLISHED",
                    "reason": "The historical blocker classifies the same exact PEMS identity as missing top-level semantic and PEMS_SCHEMA_INVALID, while the exact selected bytes contain semantic=pems/2. The accepted invalid class therefore cannot be coherently re-proven from this evidence set.",
                },
                "CR4": {
                    "status": "PASS_WITH_CONTRADICTION",
                    "proof": "The exact Git-backed PEMS/COVE pair, historical blocker record, and historical admission receipt are preserved and identity-bound; preservation does not resolve their semantic-presence contradiction.",
                },
                "CR5": {
                    "status": "FAIL",
                    "candidate_count": 0,
                    "failed_predicate": 2,
                    "outcome": "UNSUPPORTED_CANONICAL_DAMAGE",
                    "detail": "prestate must be an object with no top-level semantic key",
                },
                "CR6": {"status": "NOT_REACHED"},
                "CR7": {"status": "NOT_REACHED"},
                "CR8": {
                    "status": "NOT_REACHED",
                    "reason": "No recovery candidate or immutable recovery plan exists, so there is no plan digest for protected-root approval.",
                },
                "CR9": {
                    "status": "PASS",
                    "semantic_judgment_required": False,
                    "proof": "The rehearsal stopped at the closed Mode A eligibility boundary and did not invent an alternate repair or semantic interpretation.",
                },
            },
            "disposition": "G8_INCIDENT_REHEARSAL_BLOCKED_UNSUPPORTED_CANONICAL_DAMAGE",
            "evidence_contradiction": {
                "exact_pems_bytes": {
                    "observed_semantic": "pems/2",
                    "observed_top_level_keys": ["project_id", "records", "relations", "semantic"],
                },
                "historical_blocker_claim": {
                    "semantic_present": False,
                    "top_level_keys": ["project_id", "records", "relations"],
                },
                "identity_is_same": True,
            },
            "expected_repaired_pair": None,
            "gate": "G8",
            "historical_blocker": {
                "git_blob": self.BLOCKER_GIT_BLOB,
                "path": self.BLOCKER_PATH.as_posix(),
                "status": "BLOCKED_PEMS_SCHEMA_INVALID",
            },
            "historical_receipt": {
                "git_blob": self.RECEIPT_GIT_BLOB,
                "path": self.RECEIPT_PATH.as_posix(),
            },
            "mode": "A",
            "project_id": self.PROJECT_ID,
            "recipe_id": "missing_top_level_semantic_pems2/1",
            "recovery_plan_sha256": None,
            "selected_incident": {
                "cove_git_blob": self.COVE_GIT_BLOB,
                "cove_sha256": self.COVE_SHA256,
                "pems_git_blob": self.PEMS_GIT_BLOB,
                "pems_sha256": self.PEMS_SHA256,
            },
        }

    def test_exact_incident_rehearsal_stops_at_closed_mode_a_boundary(self):
        pems_bytes = (ROOT / self.PEMS_PATH).read_bytes()
        cove_bytes = (ROOT / self.COVE_PATH).read_bytes()
        blocker_bytes = (ROOT / self.BLOCKER_PATH).read_bytes()
        receipt_bytes = (ROOT / self.RECEIPT_PATH).read_bytes()
        live_recovery_before = self.snapshot_recovery_tree()

        # CR2: all selected immutable incident identities match exactly.
        self.assertEqual(sha256_bytes(pems_bytes), self.PEMS_SHA256)
        self.assertEqual(sha256_bytes(cove_bytes), self.COVE_SHA256)
        self.assertEqual(git_blob_sha1(pems_bytes), self.PEMS_GIT_BLOB)
        self.assertEqual(git_blob_sha1(cove_bytes), self.COVE_GIT_BLOB)
        self.assertEqual(git_blob_sha1(blocker_bytes), self.BLOCKER_GIT_BLOB)
        self.assertEqual(git_blob_sha1(receipt_bytes), self.RECEIPT_GIT_BLOB)

        blocker = json.loads(blocker_bytes.decode("utf-8"))
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        source = json.loads(pems_bytes.decode("utf-8"))

        self.assertEqual(blocker["status"], "BLOCKED_PEMS_SCHEMA_INVALID")
        self.assertEqual(blocker["coordination_revision"], self.COORDINATION_REVISION)
        self.assertEqual(blocker["canonical_pems"]["git_blob"], self.PEMS_GIT_BLOB)
        self.assertEqual(blocker["canonical_cove"]["git_blob"], self.COVE_GIT_BLOB)
        self.assertEqual(blocker["observed_p3_failure"]["code"], "PEMS_SCHEMA_INVALID")
        self.assertIs(blocker["canonical_pems"]["semantic_present"], False)
        self.assertEqual(blocker["canonical_pems"]["top_level_keys"], ["project_id", "records", "relations"])
        self.assertEqual(blocker["standing_evidence"]["admission_receipt_git_blob"], self.RECEIPT_GIT_BLOB)
        self.assertEqual(receipt["admitted_pems_sha256"], self.PEMS_SHA256)
        self.assertEqual(receipt["admitted_cove_sha256"], self.COVE_SHA256)

        # Same exact PEMS identity contradicts the blocker metadata.
        self.assertEqual(source["semantic"], "pems/2")
        self.assertEqual(list(source), ["project_id", "records", "relations", "semantic"])

        # CR5: the accepted closed recipe must stop, not reinterpret or repair this evidence.
        with self.assertRaises(ContractError) as caught:
            build_mode_a_recovery_plan(
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
        self.assertEqual(caught.exception.code, "UNSUPPORTED_CANONICAL_DAMAGE")
        self.assertEqual(caught.exception.detail, "prestate must be an object with no top-level semantic key")

        # Freeze only the observed fail-closed result. There is no candidate pair or plan digest to approve.
        stored = json.loads((ROOT / self.REHEARSAL_PATH).read_text(encoding="utf-8"))
        self.assertEqual(stored, self.expected_rehearsal())

        # G8 is read-only with respect to Canon and recovery standing state.
        self.assertEqual((ROOT / self.PEMS_PATH).read_bytes(), pems_bytes)
        self.assertEqual((ROOT / self.COVE_PATH).read_bytes(), cove_bytes)
        self.assertEqual(self.snapshot_recovery_tree(), live_recovery_before)


if __name__ == "__main__":
    unittest.main()
