#!/usr/bin/env python3
from __future__ import annotations

# P4 proof branch marker; intentionally not merged.

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("rd_builder_p4", ROOT / "packaging/build_release_package.py")
installer = load_module("rd_installer_p4", ROOT / "packaging/rd_install.py")
SOURCE_COMMIT = "b" * 40


class InstallerP4Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.artifacts = self.base / "artifacts"
        self.project = self.base / "project"
        self.project.mkdir()
        (self.project / "keep.txt").write_text("project-owned\n", encoding="utf-8")
        self.project_package = self.project / "project-package.json"
        self.project_package.write_text(json.dumps({
            "contract": "project-knowledge-package/1",
            "project": {"id": "p4"},
            "framework": {"compatible_contracts": [
                "reasoning-distiller-install-package/1",
                "reasoning-distiller-installer/1"
            ]},
            "canonical_backend": {"type": "pems-cove", "config": "backend.json"},
            "locations": {
                "sources": "sources", "rules": "rules", "roles": "roles",
                "authority": "authority", "evidence": "evidence",
                "transactions": "transactions", "dispositions": "dispositions",
                "adapters": "adapters"
            }
        }, sort_keys=True), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def package(self, version: str, name: str) -> dict:
        return builder.build(version, SOURCE_COMMIT, self.artifacts / name, ROOT)

    def install(self, built: dict, **kwargs):
        return installer.install(
            built["archive"], built["manifest"], built["transport_sha256"], self.project,
            project_package=self.project_package, **kwargs)

    def live_manifest(self) -> dict:
        return json.loads((self.project / ".reasoning-distiller/.installation/MANIFEST.json").read_text())

    def assert_clean_transaction_state(self):
        self.assertFalse((self.project / installer.JOURNAL_NAME).exists())
        self.assertFalse((self.project / installer.BACKUP_NAME).exists())

    def test_interruption_after_backup_restores_previous_before_next_install(self):
        v1 = self.package("0.1.0", "v1")
        v2 = self.package("0.2.0", "v2")
        v3 = self.package("0.3.0", "v3")
        self.install(v1)
        with self.assertRaises(installer.SimulatedInterruption):
            self.install(v2, _simulate_interrupt_after="backup")
        self.assertFalse((self.project / ".reasoning-distiller").exists())
        self.assertTrue((self.project / installer.BACKUP_NAME).exists())
        result = self.install(v3)
        self.assertEqual(result["recovery_before_install"], "RESTORED_PREVIOUS")
        self.assertEqual(self.live_manifest()["version"], "0.3.0")
        self.assert_clean_transaction_state()

    def test_interruption_after_activation_rolls_back_then_allows_next_install(self):
        v1 = self.package("1.0.0", "v1")
        v2 = self.package("2.0.0", "v2")
        self.install(v1)
        with self.assertRaises(installer.SimulatedInterruption):
            self.install(v2, _simulate_interrupt_after="activation")
        self.assertEqual(self.live_manifest()["version"], "2.0.0")
        recovery = installer.recover_interrupted_transaction(self.project)
        self.assertEqual(recovery["status"], "RESTORED_PREVIOUS")
        self.assertEqual(self.live_manifest()["version"], "1.0.0")
        self.assert_clean_transaction_state()

    def test_interrupted_first_install_restores_empty_state(self):
        v1 = self.package("0.1.0", "v1")
        with self.assertRaises(installer.SimulatedInterruption):
            self.install(v1, _simulate_interrupt_after="activation")
        self.assertTrue((self.project / ".reasoning-distiller").exists())
        recovery = installer.recover_interrupted_transaction(self.project)
        self.assertEqual(recovery["status"], "RESTORED_EMPTY")
        self.assertFalse((self.project / ".reasoning-distiller").exists())
        self.assert_clean_transaction_state()

    def test_committed_interruption_finalizes_new_install_not_rollback(self):
        v1 = self.package("0.1.0", "v1")
        v2 = self.package("0.2.0", "v2")
        self.install(v1)
        with self.assertRaises(installer.SimulatedInterruption):
            self.install(v2, _simulate_interrupt_after="committed")
        self.assertEqual(self.live_manifest()["version"], "0.2.0")
        self.assertTrue((self.project / installer.BACKUP_NAME).exists())
        recovery = installer.recover_interrupted_transaction(self.project)
        self.assertEqual(recovery["status"], "COMMIT_FINALIZED")
        self.assertEqual(self.live_manifest()["version"], "0.2.0")
        self.assert_clean_transaction_state()

    def test_recovery_is_idempotent_after_restore_rename_interruption(self):
        v1 = self.package("0.1.0", "v1")
        v2 = self.package("0.2.0", "v2")
        self.install(v1)
        with self.assertRaises(installer.SimulatedInterruption):
            self.install(v2, _simulate_interrupt_after="activation")
        journal_path = self.project / installer.JOURNAL_NAME
        journal = json.loads(journal_path.read_text())
        installer.write_journal(journal_path, journal, "RESTORE_PENDING")
        live = self.project / ".reasoning-distiller"
        backup = self.project / installer.BACKUP_NAME
        live.rename(self.project / ".discarded-new")
        backup.rename(live)
        recovery = installer.recover_interrupted_transaction(self.project)
        self.assertEqual(recovery["status"], "RESTORED_PREVIOUS")
        self.assertEqual(self.live_manifest()["version"], "0.1.0")
        self.assert_clean_transaction_state()

    def test_orphan_backup_fails_closed(self):
        (self.project / installer.BACKUP_NAME).mkdir()
        with self.assertRaisesRegex(ValueError, "orphan installer backup"):
            installer.recover_interrupted_transaction(self.project)

    def test_malformed_journal_fails_closed_without_touching_project_file(self):
        (self.project / installer.JOURNAL_NAME).write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid installer recovery journal fields"):
            installer.recover_interrupted_transaction(self.project)
        self.assertEqual((self.project / "keep.txt").read_text(), "project-owned\n")


if __name__ == "__main__":
    unittest.main()
