from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import RECEIPT_CONTRACT, encode_cove, jcs, normalize_pems, sha256_bytes  # noqa: E402
from ril_mutation import canonical_json_bytes  # noqa: E402
from ril_storage_verification import verify_storage  # noqa: E402


class StorageVerificationR14Tests(unittest.TestCase):
    def root(self) -> Path:
        return Path(tempfile.mkdtemp())

    def valid_pems(self) -> dict:
        return {
            "semantic": "pems/2",
            "project_id": "pems:project:p",
            "records": [
                {"id": "pems:project:p", "kind": "project", "lifecycle": "current", "data": {"name": "Fixture", "repository": "o/r", "summary": "Fixture"}},
                {"id": "pems:source:s", "kind": "source", "lifecycle": "current", "data": {"source_kind": "repository", "authority": "repository_state", "identity_locator": {"repository": "o/r"}}},
                {"id": "pems:source_observation:o", "kind": "source_observation", "lifecycle": "historical", "data": {"source_id": "pems:source:s", "evidence_state": "immutable_snapshot", "observed_at": "2026-08-15T00:00:00Z", "evidence_locator": {"commit": "abc"}}},
                {"id": "pems:proposition:a", "kind": "proposition", "lifecycle": "current", "data": {"statement": "A", "proposition_kind": "observation", "epistemic_role": "asserted"}, "provenance": {"primary": ["pems:source_observation:o"]}},
                {"id": "pems:proposition:b", "kind": "proposition", "lifecycle": "current", "data": {"statement": "B", "proposition_kind": "claim", "epistemic_role": "derived"}},
            ],
            "relations": [
                {"id": "pems:relation:r", "kind": "derived_from", "from": "pems:proposition:b", "to": "pems:proposition:a", "lifecycle": "current", "data": {}}
            ],
        }

    def control_bytes(self, value: dict) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

    def digest(self, data: bytes) -> str:
        return "sha256:" + hashlib.sha256(data).hexdigest()

    def write_control(self, root: Path, relative: str, value: dict) -> str:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.control_bytes(value)
        path.write_bytes(data)
        return self.digest(data)

    def install_pair(self, root: Path, pems: dict | None = None) -> tuple[Path, Path, bytes, bytes]:
        pems = normalize_pems(copy.deepcopy(pems or self.valid_pems()))
        canonical = root / "project-knowledge" / "canonical"
        canonical.mkdir(parents=True)
        pems_path = canonical / "pems2.jcs.json"
        cove_path = canonical / "cove1.jcs.json"
        pems_bytes = jcs(pems)
        cove_bytes = jcs(encode_cove(pems))
        pems_path.write_bytes(pems_bytes)
        cove_path.write_bytes(cove_bytes)
        return pems_path, cove_path, pems_bytes, cove_bytes

    def install_admitted_state(self, root: Path, pems: dict | None = None) -> tuple[Path, Path, Path]:
        pems_path, cove_path, pems_bytes, cove_bytes = self.install_pair(root, pems)
        receipts = root / "project-knowledge" / "admission" / "receipts"
        receipts.mkdir(parents=True)
        receipt = {
            "contract": RECEIPT_CONTRACT,
            "candidate_digest": "sha256:" + "1" * 64,
            "disposition_digest": "sha256:" + "2" * 64,
            "activation_digest": "sha256:" + "3" * 64,
            "plan_digest": "sha256:" + "4" * 64,
            "role_id": "steward:default",
            "invocation_id": "invocation:test",
            "base_pems_sha256": "0" * 64,
            "admitted_pems_sha256": sha256_bytes(pems_bytes),
            "admitted_cove_sha256": sha256_bytes(cove_bytes),
        }
        receipt_path = receipts / ("1" * 64 + ".json")
        receipt_path.write_bytes(canonical_json_bytes(receipt))
        return pems_path, cove_path, receipt_path

    def install_recovered_state(self, root: Path) -> tuple[Path, Path, Path]:
        pems_path, cove_path, pems_bytes, cove_bytes = self.install_pair(root)
        generation = "generation-test"
        base = f"project-knowledge/recovery/canonical-pems-cove/generations/{generation}"
        project = {"id": "pems:project:p"}
        inventory_path = f"{base}/preserved-inventory.json"
        equivalence_path = f"{base}/equivalence-proof.json"
        journal_path = f"{base}/journal.json"
        inventory_digest = self.write_control(root, inventory_path, {"contract": "test-preserved-inventory/1", "generation": generation})
        equivalence_digest = self.write_control(root, equivalence_path, {"contract": "test-equivalence-proof/1", "generation": generation, "eligible": True})
        journal_digest = self.write_control(root, journal_path, {"contract": "test-recovery-journal/1", "generation": generation, "state": "COMPLETED"})
        pems_sha = sha256_bytes(pems_bytes)
        cove_sha = sha256_bytes(cove_bytes)
        plan = {
            "contract": "reasoning-distiller-canonical-recovery-plan/1",
            "project": project,
            "generation": generation,
            "mode": "A",
            "recipe_id": "missing_top_level_semantic_pems2/1",
            "recipe_implementation_identity": "sha256:" + "5" * 64,
            "candidate_pems_sha256": pems_sha,
            "candidate_cove_sha256": cove_sha,
            "preserved_evidence_inventory_digest": inventory_digest,
            "equivalence_proof_digest": equivalence_digest,
            "executor_closure_identity": "sha256:" + "6" * 64,
            "recovery_contract_identity": "git-blob:" + "7" * 40,
            "r14_v2_contract_identity": "git-blob:" + "8" * 40,
            "expected_terminal_provenance_class": "VERIFIED_RECOVERED",
        }
        plan_path = f"{base}/recovery-plan.json"
        plan_digest = self.write_control(root, plan_path, plan)
        approval_path = f"{base}/root-approval.json"
        approval = {
            "contract": "reasoning-distiller-canonical-recovery-root-approval/1",
            "project": project,
            "generation": generation,
            "recovery_plan_digest": plan_digest,
            "authentication_method": "human_confirmation",
            "confirmation": "AUTHORIZE_CANONICAL_PEMS_COVE_RECOVERY",
        }
        approval_digest = self.write_control(root, approval_path, approval)
        completion = {
            "contract": "reasoning-distiller-canonical-recovery-completion/1",
            "project": project,
            "generation": generation,
            "recovery_plan_digest": plan_digest,
            "root_approval_path": approval_path,
            "root_approval_digest": approval_digest,
            "preserved_evidence_inventory_path": inventory_path,
            "preserved_evidence_inventory_digest": inventory_digest,
            "equivalence_proof_path": equivalence_path,
            "equivalence_proof_digest": equivalence_digest,
            "prestate_pems_sha256": "a" * 64,
            "prestate_cove_sha256": "b" * 64,
            "poststate_pems_sha256": pems_sha,
            "poststate_cove_sha256": cove_sha,
            "recipe_id": plan["recipe_id"],
            "recipe_implementation_identity": plan["recipe_implementation_identity"],
            "executor_closure_identity": plan["executor_closure_identity"],
            "recovery_contract_identity": plan["recovery_contract_identity"],
            "r14_v2_contract_identity": plan["r14_v2_contract_identity"],
            "provenance_class": "VERIFIED_RECOVERED",
            "journal_path": journal_path,
            "journal_digest": journal_digest,
        }
        completion_path = root / base / "completion.json"
        self.write_control(root, completion_path.relative_to(root).as_posix(), completion)
        return pems_path, cove_path, completion_path

    def snapshot(self, root: Path) -> dict[str, bytes]:
        return {path.relative_to(root).as_posix(): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file() and not path.is_symlink()}

    def test_valid_admitted_state_is_v2_verified_and_read_only(self):
        root = self.root()
        self.install_admitted_state(root)
        before = self.snapshot(root)
        result = verify_storage(root, ROOT)
        after = self.snapshot(root)
        self.assertEqual((result["contract"], result["status"], result["outcome"]), ("reasoning-distiller-storage-verification-result/2", "PASS", "VERIFIED_ADMITTED"))
        self.assertEqual(result["provenance_class"], "VERIFIED_ADMITTED")
        self.assertEqual(result["cove_tuple"], "cove/1|pems/2|jcs/1")
        self.assertTrue(result["provenance_paths"])
        self.assertEqual(set(result["provenance_paths"]), set(result["provenance_digests"]))
        self.assertEqual(before, after)

    def test_completed_recovered_state_is_v2_verified_and_read_only(self):
        root = self.root()
        _, _, completion = self.install_recovered_state(root)
        before = self.snapshot(root)
        result = verify_storage(root, ROOT)
        after = self.snapshot(root)
        self.assertEqual((result["status"], result["outcome"], result["provenance_class"]), ("PASS", "VERIFIED_RECOVERED", "VERIFIED_RECOVERED"))
        self.assertEqual(result["completion_path"], completion.relative_to(root).as_posix())
        self.assertIn(result["completion_path"], result["provenance_digests"])
        self.assertEqual(before, after)

    def test_retry_is_deterministic_for_both_provenance_classes(self):
        admitted = self.root(); self.install_admitted_state(admitted)
        recovered = self.root(); self.install_recovered_state(recovered)
        self.assertEqual(verify_storage(admitted, ROOT), verify_storage(admitted, ROOT))
        self.assertEqual(verify_storage(recovered, ROOT), verify_storage(recovered, ROOT))

    def test_no_admitted_state(self):
        result = verify_storage(self.root(), ROOT)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "NO_ADMITTED_STATE"))

    def test_incomplete_pair_fails(self):
        root = self.root(); _, cove_path, _ = self.install_admitted_state(root); cove_path.unlink()
        self.assertEqual(verify_storage(root, ROOT)["outcome"], "INCOMPLETE_CANONICAL_PAIR")

    def test_noncanonical_pems_bytes_fail_identically_before_provenance(self):
        for recovered in (False, True):
            root = self.root()
            pems_path = self.install_recovered_state(root)[0] if recovered else self.install_admitted_state(root)[0]
            parsed = json.loads(pems_path.read_text())
            pems_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
            self.assertEqual(verify_storage(root, ROOT)["outcome"], "NONCANONICAL_PEMS_BYTES")

    def test_schema_invalid_pems_fails(self):
        root = self.root(); bad = self.valid_pems(); bad["records"][-1]["data"]["epistemic_role"] = "guessed"
        self.install_admitted_state(root, bad)
        self.assertEqual(verify_storage(root, ROOT)["outcome"], "PEMS_SCHEMA_INVALID")

    def test_cove_mismatch_fails(self):
        root = self.root(); _, cove_path, _ = self.install_admitted_state(root)
        cove = json.loads(cove_path.read_text()); cove["p"] = "pems/999"; cove_path.write_bytes(jcs(cove))
        self.assertEqual(verify_storage(root, ROOT)["outcome"], "COVE_MISMATCH")

    def test_receipt_mismatch_falls_closed_without_recovery_evidence(self):
        root = self.root(); _, _, receipt_path = self.install_admitted_state(root)
        receipt = json.loads(receipt_path.read_text()); receipt["admitted_pems_sha256"] = "f" * 64; receipt_path.write_bytes(canonical_json_bytes(receipt))
        self.assertEqual(verify_storage(root, ROOT)["outcome"], "ADMISSION_RECEIPT_MISMATCH")

    def test_recovered_completion_digest_mismatch_fails_closed(self):
        root = self.root(); _, _, completion_path = self.install_recovered_state(root)
        completion = json.loads(completion_path.read_text()); completion["root_approval_digest"] = "sha256:" + "0" * 64
        completion_path.write_bytes(self.control_bytes(completion))
        self.assertEqual(verify_storage(root, ROOT)["outcome"], "RECOVERY_PROVENANCE_MISMATCH")

    def test_completion_record_is_never_an_admission_receipt(self):
        root = self.root(); _, _, completion_path = self.install_recovered_state(root)
        receipts = root / "project-knowledge/admission/receipts"; receipts.mkdir(parents=True)
        (receipts / "fake.json").write_bytes(completion_path.read_bytes())
        self.assertEqual(verify_storage(root, ROOT)["outcome"], "ADMISSION_RECEIPT_INVALID")

    def test_active_recovery_barrier_blocks_public_verification(self):
        root = self.root(); self.install_admitted_state(root)
        barrier = root / "project-knowledge/recovery/canonical-pems-cove/active.json"; barrier.parent.mkdir(parents=True)
        barrier.write_bytes(self.control_bytes({"contract": "reasoning-distiller-canonical-recovery-barrier/1", "transaction_state": "ACTIVE"}))
        self.assertEqual(verify_storage(root, ROOT)["outcome"], "CANONICAL_RECOVERY_ACTIVE")

    def test_symlink_canonical_file_fails_closed(self):
        root = self.root(); pems_path, _, _ = self.install_admitted_state(root)
        target = root / "outside.json"; target.write_bytes(pems_path.read_bytes()); pems_path.unlink(); pems_path.symlink_to(target)
        self.assertEqual(verify_storage(root, ROOT)["outcome"], "CANONICAL_PATH_CONFLICT")


if __name__ == "__main__":
    unittest.main()
