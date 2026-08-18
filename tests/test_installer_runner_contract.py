#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "packaging/validate_install_package_contract.py"
spec = importlib.util.spec_from_file_location("rd_package_contract", MODULE_PATH)
rd = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(rd)

MANIFEST = ROOT / "packaging/examples/manifest.example.json"
INSTALLATION = ROOT / "packaging/examples/installation.example.json"


class InstallerRunnerContractTests(unittest.TestCase):
    def test_canonical_installer_identity(self):
        item = json.loads(INSTALLATION.read_text(encoding="utf-8"))
        rd.validate_schema(item, rd.INSTALL_SCHEMA)
        self.assertEqual(item["installer"]["contract"], "reasoning-distiller-installer/1")
        self.assertEqual(item["installer"]["entrypoint"], "rd_install.py")
        self.assertEqual(item["installer"]["runtime"], "python3")

    def test_event_metadata_does_not_change_package_identity(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        installation = json.loads(INSTALLATION.read_text(encoding="utf-8"))
        identity = rd.compute_content_identity(manifest)
        changed = copy.deepcopy(installation)
        changed["installed_at"] = "2030-01-01T00:00:00Z"
        changed["runner"] = {"kind": "other-runner", "invocation_id": "other-run"}
        self.assertNotEqual(installation, changed)
        self.assertEqual(identity, rd.compute_content_identity(manifest))

    def test_schema_rejects_noncanonical_entrypoint(self):
        item = json.loads(INSTALLATION.read_text(encoding="utf-8"))
        item["installer"]["entrypoint"] = "other_installer.py"
        with self.assertRaises(ValueError):
            rd.validate_schema(item, rd.INSTALL_SCHEMA)


if __name__ == "__main__":
    unittest.main()
