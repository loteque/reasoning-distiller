from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_canonical_store import (  # noqa: E402
    BARRIER_CONTRACT,
    exclusive_canonical_store,
    shared_canonical_store,
)
from ril_mutation import ContractError  # noqa: E402


class CanonicalStoreG1Tests(unittest.TestCase):
    def root(self) -> Path:
        return Path(tempfile.mkdtemp())

    def barrier(self, root: Path, state: str = "ACTIVE") -> Path:
        path = root / "project-knowledge/recovery/canonical-pems-cove/active.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        value = {"contract": BARRIER_CONTRACT, "transaction_state": state}
        path.write_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        return path

    def test_read_only_absent_snapshot_creates_nothing(self):
        root = self.root()
        before = list(root.iterdir())
        with shared_canonical_store(root) as store:
            snapshot = store.snapshot()
        self.assertEqual(snapshot.state, "ABSENT")
        self.assertEqual(before, list(root.iterdir()))

    def test_complete_pair_snapshot_binds_bytes_and_hashes_under_one_lock(self):
        root = self.root()
        canonical = root / "project-knowledge/canonical"
        canonical.mkdir(parents=True)
        pems = b'{"semantic":"pems/2"}'
        cove = b'{"c":"cove/1"}'
        (canonical / "pems2.jcs.json").write_bytes(pems)
        (canonical / "cove1.jcs.json").write_bytes(cove)
        with shared_canonical_store(root) as store:
            snapshot = store.snapshot()
        self.assertEqual(snapshot.state, "PRESENT")
        self.assertEqual(snapshot.pems_bytes, pems)
        self.assertEqual(snapshot.cove_bytes, cove)
        self.assertEqual(len(snapshot.pems_sha256 or ""), 64)
        self.assertEqual(len(snapshot.cove_sha256 or ""), 64)

    def test_incomplete_pair_is_explicit_not_silently_absent(self):
        root = self.root()
        canonical = root / "project-knowledge/canonical"
        canonical.mkdir(parents=True)
        (canonical / "pems2.jcs.json").write_bytes(b"{}")
        with shared_canonical_store(root) as store:
            snapshot = store.snapshot()
        self.assertEqual(snapshot.state, "INCOMPLETE")

    def test_valid_active_barrier_blocks_normal_reader(self):
        root = self.root()
        self.barrier(root)
        with self.assertRaises(ContractError) as caught:
            with shared_canonical_store(root) as store:
                store.snapshot()
        self.assertEqual(caught.exception.code, "CANONICAL_RECOVERY_ACTIVE")

    def test_unknown_barrier_state_is_invalid(self):
        root = self.root()
        self.barrier(root, "PUBLISHING")
        with self.assertRaises(ContractError) as caught:
            with shared_canonical_store(root) as store:
                store.snapshot()
        self.assertEqual(caught.exception.code, "CANONICAL_RECOVERY_BARRIER_INVALID")

    def test_noncanonical_barrier_bytes_are_invalid(self):
        root = self.root()
        path = self.barrier(root)
        value = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        with self.assertRaises(ContractError) as caught:
            with shared_canonical_store(root) as store:
                store.snapshot()
        self.assertEqual(caught.exception.code, "CANONICAL_RECOVERY_BARRIER_INVALID")

    def test_symlink_barrier_is_invalid(self):
        root = self.root()
        path = self.barrier(root)
        target = root / "outside.json"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        with self.assertRaises(ContractError) as caught:
            with shared_canonical_store(root) as store:
                store.snapshot()
        self.assertEqual(caught.exception.code, "CANONICAL_RECOVERY_BARRIER_INVALID")

    def test_internal_verification_requires_exclusive_lock_and_active_barrier(self):
        root = self.root()
        self.barrier(root)
        with shared_canonical_store(root) as store:
            with self.assertRaises(ContractError):
                store.internal_verification_snapshot()
        with exclusive_canonical_store(root) as store:
            self.assertEqual(store.internal_verification_snapshot().state, "ABSENT")

    def test_exclusive_publication_is_durable_and_guarded(self):
        root = self.root()
        pems = b'{"semantic":"pems/2"}'
        cove = b'{"c":"cove/1"}'
        with exclusive_canonical_store(root) as store:
            published = store.publish_pair(pems, cove)
        self.assertEqual(published.state, "PRESENT")
        self.assertEqual((root / "project-knowledge/canonical/pems2.jcs.json").read_bytes(), pems)
        self.assertEqual((root / "project-knowledge/canonical/cove1.jcs.json").read_bytes(), cove)
        leftovers = list((root / "project-knowledge/canonical").glob("*.canonical-store.*.tmp"))
        self.assertEqual(leftovers, [])

    def test_lock_contention_fails_closed(self):
        root = self.root()
        with shared_canonical_store(root):
            with self.assertRaises(ContractError) as caught:
                with exclusive_canonical_store(root):
                    pass
        self.assertEqual(caught.exception.code, "CANONICAL_RECOVERY_BUSY")

    def test_package_sources_have_no_direct_fixed_canonical_reader(self):
        forbidden = ("pems2.jcs.json", "cove1.jcs.json", "project-knowledge/canonical")
        allowed = {Path("runtime/ril_canonical_store.py")}
        offenders: list[str] = []
        for source_root in (ROOT / "runtime", ROOT / "context_packaging"):
            for path in sorted(source_root.rglob("*.py")):
                rel = path.relative_to(ROOT)
                if rel in allowed:
                    continue
                text = path.read_text(encoding="utf-8")
                if any(token in text for token in forbidden):
                    offenders.append(rel.as_posix())
        self.assertEqual(offenders, [], "fixed canonical pair access must stay inside ril_canonical_store.py")


if __name__ == "__main__":
    unittest.main()
