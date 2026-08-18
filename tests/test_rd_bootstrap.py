#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rd_bootstrap", ROOT / "runtime/rd_bootstrap.py")
rd = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(rd)


class BootstrapConformance(unittest.TestCase):
    def project(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / ".reasoning-distiller").mkdir()
        return td, root

    def test_creates_minimum_state_and_is_idempotent(self):
        td, root = self.project()
        self.addCleanup(td.cleanup)
        code, result = rd.bootstrap(root)
        self.assertEqual(code, 0)
        self.assertEqual(result["outcome"], "CREATED")
        self.assertEqual(json.loads((root / "project-knowledge/project.json").read_text()), rd.PROJECT_CONFIG)
        for rel in rd.DIRS:
            self.assertTrue((root / rel).is_dir())
        code2, result2 = rd.bootstrap(root)
        self.assertEqual(code2, 0)
        self.assertEqual(result2["outcome"], "ALREADY_BOOTSTRAPPED")
        self.assertEqual(result2["created"], [])

    def test_completes_partial_compatible_state(self):
        td, root = self.project()
        self.addCleanup(td.cleanup)
        (root / "project-knowledge/evidence").mkdir(parents=True)
        code, result = rd.bootstrap(root)
        self.assertEqual(code, 0)
        self.assertEqual(result["outcome"], "COMPLETED")
        self.assertNotIn("project-knowledge/evidence", result["created"])

    def test_missing_installation_fails_without_mutation(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            code, result = rd.bootstrap(root)
            self.assertEqual(code, 2)
            self.assertEqual(result["reason_code"], "INSTALLATION_MISSING")
            self.assertFalse((root / "project-knowledge").exists())

    def test_config_conflict_fails_without_repair(self):
        td, root = self.project()
        self.addCleanup(td.cleanup)
        pk = root / "project-knowledge"
        pk.mkdir()
        config = pk / "project.json"
        original = b'{"foreign":true}\n'
        config.write_bytes(original)
        code, result = rd.bootstrap(root)
        self.assertEqual(code, 2)
        self.assertEqual(result["reason_code"], "PROJECT_CONFIG_CONFLICT")
        self.assertEqual(config.read_bytes(), original)
        for rel in rd.DIRS:
            self.assertFalse((root / rel).exists())

    def test_path_conflict_preflight_is_mutation_free(self):
        td, root = self.project()
        self.addCleanup(td.cleanup)
        pk = root / "project-knowledge"
        pk.mkdir()
        (pk / "submissions").write_text("collision", encoding="utf-8")
        code, result = rd.bootstrap(root)
        self.assertEqual(code, 2)
        self.assertEqual(result["reason_code"], "PATH_CONFLICT")
        self.assertFalse((pk / "project.json").exists())
        self.assertFalse((pk / "evidence").exists())
        self.assertFalse((pk / "invocations").exists())

    def test_symlink_managed_path_rejected(self):
        td, root = self.project()
        self.addCleanup(td.cleanup)
        pk = root / "project-knowledge"
        pk.mkdir()
        outside = root / "outside"
        outside.mkdir()
        try:
            (pk / "evidence").symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable")
        code, result = rd.bootstrap(root)
        self.assertEqual(code, 2)
        self.assertEqual(result["reason_code"], "PATH_CONFLICT")

    def test_bootstrap_does_not_create_authority_or_canonical_state(self):
        td, root = self.project()
        self.addCleanup(td.cleanup)
        code, _ = rd.bootstrap(root)
        self.assertEqual(code, 0)
        forbidden = [
            "project-knowledge/authority",
            "project-knowledge/canonical",
            "project-knowledge/pems",
            "project-knowledge/cove",
        ]
        for rel in forbidden:
            self.assertFalse((root / rel).exists(), rel)


if __name__ == "__main__":
    unittest.main()
