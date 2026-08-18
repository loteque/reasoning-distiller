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

EXAMPLE = ROOT / "packaging/examples/manifest.example.json"
INSTALLATION = ROOT / "packaging/examples/installation.example.json"


class InstallPackageContractTests(unittest.TestCase):
    def manifest(self):
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_examples_validate(self):
        rd.validate_manifest(EXAMPLE)
        rd.validate_installation(INSTALLATION)

    def test_identity_is_order_independent(self):
        a = self.manifest()
        b = copy.deepcopy(a)
        b["files"].reverse()
        b["managed_roots"].reverse()
        self.assertEqual(rd.compute_content_identity(a), rd.compute_content_identity(b))

    def test_transport_digest_not_in_content_identity(self):
        a = self.manifest()
        b = copy.deepcopy(a)
        b["transport_sha256"] = "d" * 64
        self.assertEqual(rd.compute_content_identity(a), rd.compute_content_identity(b))

    def test_identity_changes_for_semantic_package_fields(self):
        base = self.manifest()
        variants = []

        v = copy.deepcopy(base); v["version"] = "0.1.1"; variants.append(v)
        v = copy.deepcopy(base); v["source_commit"] = "1" * 40; variants.append(v)
        v = copy.deepcopy(base); v["managed_roots"].append("protocols"); variants.append(v)
        v = copy.deepcopy(base); v["compatibility"]["rgp"] = ["rgp/9"]; variants.append(v)
        v = copy.deepcopy(base); v["files"][0]["path"] = "validators/other.py"; variants.append(v)
        v = copy.deepcopy(base); v["files"][0]["mode"] = "0644"; variants.append(v)
        v = copy.deepcopy(base); v["files"][0]["sha256"] = "e" * 64; variants.append(v)

        identity = rd.compute_content_identity(base)
        for variant in variants:
            self.assertNotEqual(identity, rd.compute_content_identity(variant))

    def test_rejects_duplicate_path(self):
        m = self.manifest()
        m["files"].append(copy.deepcopy(m["files"][0]))
        m["content_identity"] = rd.compute_content_identity(m)
        with self.assertRaisesRegex(ValueError, "duplicate file path"):
            rd.validate_manifest_semantics(m)

    def test_rejects_casefold_collision(self):
        m = self.manifest()
        item = copy.deepcopy(m["files"][0])
        item["path"] = "Validators/rgp_validator.py"
        m["files"].append(item)
        m["managed_roots"].append("Validators")
        m["content_identity"] = rd.compute_content_identity(m)
        with self.assertRaisesRegex(ValueError, "case-fold collision"):
            rd.validate_manifest_semantics(m)

    def test_rejects_unsafe_paths(self):
        for bad in ("../x", "/x", "a//b", "a/./b", "a/../b", "a\\b"):
            m = self.manifest()
            m["files"][0]["path"] = bad
            m["content_identity"] = rd.compute_content_identity(m)
            with self.subTest(path=bad):
                with self.assertRaises(ValueError):
                    rd.validate_manifest_semantics(m)

    def test_rejects_file_outside_managed_roots(self):
        m = self.manifest()
        m["files"][0]["path"] = "protocols/rgp.md"
        m["content_identity"] = rd.compute_content_identity(m)
        with self.assertRaisesRegex(ValueError, "outside managed_roots"):
            rd.validate_manifest_semantics(m)

    def test_rejects_generated_installation_metadata_in_release_payload(self):
        for path in ("VERSION", ".installation/MANIFEST.json", ".installation/INSTALLATION.json"):
            m = self.manifest()
            m["files"][0]["path"] = path
            m["content_identity"] = rd.compute_content_identity(m)
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, "generated installation metadata"):
                    rd.validate_manifest_semantics(m)

    def test_schema_rejects_invalid_mode_and_digest(self):
        for field, value in (("mode", "0777"), ("sha256", "nope")):
            m = self.manifest()
            m["files"][0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    rd.validate_schema(m, rd.MANIFEST_SCHEMA)

    def test_rejects_wrong_content_identity(self):
        m = self.manifest()
        m["content_identity"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "content_identity mismatch"):
            rd.validate_manifest_semantics(m)


if __name__ == "__main__":
    unittest.main()
