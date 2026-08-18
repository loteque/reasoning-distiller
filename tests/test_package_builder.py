#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "packaging/build_release_package.py"
spec = importlib.util.spec_from_file_location("rd_package_builder", MODULE_PATH)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(builder)

SOURCE_COMMIT = "1" * 40
VERSION = "0.2.0-p2"


class PackageBuilderTests(unittest.TestCase):
    def test_two_clean_builds_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            a = builder.build(VERSION, SOURCE_COMMIT, base / "a")
            b = builder.build(VERSION, SOURCE_COMMIT, base / "b")

            self.assertEqual(a["content_identity"], b["content_identity"])
            self.assertEqual(a["transport_sha256"], b["transport_sha256"])
            self.assertEqual(a["archive"].read_bytes(), b["archive"].read_bytes())
            self.assertEqual(a["manifest"].read_bytes(), b["manifest"].read_bytes())
            self.assertEqual(a["sha256"].read_bytes(), b["sha256"].read_bytes())

    def test_manifest_contains_only_allowlisted_roots(self):
        with tempfile.TemporaryDirectory() as td:
            result = builder.build(VERSION, SOURCE_COMMIT, Path(td))
            manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
            allowed = set(builder.load_config()["managed_roots"])
            for item in manifest["files"]:
                top = item["path"].split("/", 1)[0]
                self.assertIn(top, allowed)
                self.assertNotIn(top, {"docs", "evaluation", "tests", ".github", "project-knowledge"})

    def test_project_owned_material_cannot_enter_package(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "source"
            self.make_minimal_source(root)
            (root / "project-knowledge").mkdir()
            (root / "project-knowledge/secret.json").write_text('{"authority":"project"}\n', encoding="utf-8")
            (root / "evaluation").mkdir()
            (root / "evaluation/reference.json").write_text("{}\n", encoding="utf-8")

            result = builder.build(VERSION, SOURCE_COMMIT, Path(td) / "out", root=root)
            manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
            paths = {item["path"] for item in manifest["files"]}
            self.assertNotIn("project-knowledge/secret.json", paths)
            self.assertNotIn("evaluation/reference.json", paths)

    def test_symlink_inside_managed_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "source"
            self.make_minimal_source(root)
            outside = Path(td) / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            link = root / "agents/escape.txt"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "symlink forbidden"):
                builder.build(VERSION, SOURCE_COMMIT, Path(td) / "out", root=root)

    def test_content_change_changes_content_and_transport_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "source"
            self.make_minimal_source(root)
            first = builder.build(VERSION, SOURCE_COMMIT, Path(td) / "one", root=root)
            (root / "agents/a.txt").write_text("changed\n", encoding="utf-8")
            second = builder.build(VERSION, SOURCE_COMMIT, Path(td) / "two", root=root)
            self.assertNotEqual(first["content_identity"], second["content_identity"])
            self.assertNotEqual(first["transport_sha256"], second["transport_sha256"])

    def test_source_commit_change_changes_content_identity_not_file_set(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "source"
            self.make_minimal_source(root)
            one = builder.build(VERSION, "1" * 40, Path(td) / "one", root=root)
            two = builder.build(VERSION, "2" * 40, Path(td) / "two", root=root)
            self.assertNotEqual(one["content_identity"], two["content_identity"])
            m1 = json.loads(one["manifest"].read_text(encoding="utf-8"))
            m2 = json.loads(two["manifest"].read_text(encoding="utf-8"))
            self.assertEqual(m1["files"], m2["files"])

    def test_invalid_source_commit_and_version_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                builder.build("bad/version", SOURCE_COMMIT, Path(td))
            with self.assertRaises(ValueError):
                builder.build(VERSION, "not-a-sha", Path(td))

    @staticmethod
    def make_minimal_source(root: Path) -> None:
        config = builder.load_config()
        (root / "packaging").mkdir(parents=True)
        (root / "packaging/package-build.json").write_text(
            json.dumps(config, sort_keys=True) + "\n", encoding="utf-8"
        )
        for managed_root in config["managed_roots"]:
            directory = root / managed_root
            directory.mkdir(parents=True)
            (directory / "a.txt").write_text(f"{managed_root}\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
