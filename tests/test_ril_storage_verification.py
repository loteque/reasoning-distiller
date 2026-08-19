from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import RECEIPT_CONTRACT, encode_cove, jcs, sha256_bytes  # noqa: E402
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
                {
                    "id": "pems:project:p",
                    "kind": "project",
                    "lifecycle": "current",
                    "data": {"name": "Fixture", "repository": "o/r", "summary": "Fixture"},
                },
                {
                    "id": "pems:source:s",
                    "kind": "source",
                    "lifecycle": "current",
                    "data": {"source_kind": "repository", "authority": "repository_state", "identity_locator": {"repository": "o/r"}},
                },
                {
                    "id": "pems:source_observation:o",
                    "kind": "source_observation",
                    "lifecycle": "historical",
                    "data": {
                        "source_id": "pems:source:s",
                        "evidence_state": "immutable_snapshot",
                        "observed_at": "2026-08-15T00:00:00Z",
                        "evidence_locator": {"commit": "abc"},
                    },
                },
                {
                    "id": "pems:proposition:a",
                    "kind": "proposition",
                    "lifecycle": "current",
                    "data": {"statement": "A", "proposition_kind": "observation", "epistemic_role": "asserted"},
                    "provenance": {"primary": ["pems:source_observation:o"]},
                },
                {
                    "id": "pems:proposition:b",
                    "kind": "proposition",
                    "lifecycle": "current",
                    "data": {"statement": "B", "proposition_kind": "claim", "epistemic_role": "derived"},
                },
            ],
            "relations": [
                {
                    "id": "pems:relation:r",
                    "kind": "derived_from",
                    "from": "pems:proposition:b",
                    "to": "pems:proposition:a",
                    "lifecycle": "current",
                    "data": {},
                }
            ],
        }

    def install_state(self, root: Path, pems: dict | None = None) -> tuple[Path, Path, Path]:
        pems = copy.deepcopy(pems or self.valid_pems())
        canonical = root / "project-knowledge" / "canonical"
        receipts = root / "project-knowledge" / "admission" / "receipts"
        canonical.mkdir(parents=True)
        receipts.mkdir(parents=True)
        pems_path = canonical / "pems2.jcs.json"
        cove_path = canonical / "cove1.jcs.json"
        pems_bytes = jcs(pems)
        cove_bytes = jcs(encode_cove(pems))
        pems_path.write_bytes(pems_bytes)
        cove_path.write_bytes(cove_bytes)
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

    def snapshot(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def test_valid_admitted_state_is_verified_and_read_only(self):
        root = self.root()
        self.install_state(root)
        before = self.snapshot(root)
        result = verify_storage(root, ROOT)
        after = self.snapshot(root)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "VERIFIED"))
        self.assertEqual(result["cove_tuple"], "cove/1|pems/2|jcs/1")
        self.assertTrue(result["receipt_paths"])
        self.assertEqual(before, after)

    def test_retry_is_deterministic(self):
        root = self.root()
        self.install_state(root)
        self.assertEqual(verify_storage(root, ROOT), verify_storage(root, ROOT))

    def test_no_admitted_state(self):
        result = verify_storage(self.root(), ROOT)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "NO_ADMITTED_STATE"))

    def test_incomplete_pair_fails(self):
        root = self.root()
        pems_path, cove_path, _ = self.install_state(root)
        cove_path.unlink()
        result = verify_storage(root, ROOT)
        self.assertEqual(result["outcome"], "INCOMPLETE_CANONICAL_PAIR")

    def test_noncanonical_pems_bytes_fail(self):
        root = self.root()
        pems_path, _, _ = self.install_state(root)
        parsed = json.loads(pems_path.read_text())
        pems_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
        result = verify_storage(root, ROOT)
        self.assertEqual(result["outcome"], "NONCANONICAL_PEMS_BYTES")

    def test_schema_invalid_pems_fails(self):
        root = self.root()
        bad = self.valid_pems()
        bad["records"][-1]["data"]["epistemic_role"] = "guessed"
        self.install_state(root, bad)
        result = verify_storage(root, ROOT)
        self.assertEqual(result["outcome"], "PEMS_SCHEMA_INVALID")

    def test_cove_mismatch_fails(self):
        root = self.root()
        _, cove_path, _ = self.install_state(root)
        cove = json.loads(cove_path.read_text())
        cove["p"] = "pems/999"
        cove_path.write_bytes(jcs(cove))
        result = verify_storage(root, ROOT)
        self.assertEqual(result["outcome"], "COVE_MISMATCH")

    def test_receipt_mismatch_fails(self):
        root = self.root()
        _, _, receipt_path = self.install_state(root)
        receipt = json.loads(receipt_path.read_text())
        receipt["admitted_pems_sha256"] = "f" * 64
        receipt_path.write_bytes(canonical_json_bytes(receipt))
        result = verify_storage(root, ROOT)
        self.assertEqual(result["outcome"], "ADMISSION_RECEIPT_MISMATCH")

    def test_symlink_canonical_file_fails_closed(self):
        root = self.root()
        pems_path, _, _ = self.install_state(root)
        target = root / "outside.json"
        target.write_bytes(pems_path.read_bytes())
        pems_path.unlink()
        pems_path.symlink_to(target)
        result = verify_storage(root, ROOT)
        self.assertEqual(result["outcome"], "CANONICAL_PATH_CONFLICT")


if __name__ == "__main__":
    unittest.main()
