#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("rd_builder_p3", ROOT / "packaging/build_release_package.py")
installer = load_module("rd_installer_p3", ROOT / "packaging/rd_install.py")

SOURCE_COMMIT = "a" * 40


class InstallerP3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.artifacts = self.base / "artifacts"
        self.project = self.base / "project"
        self.project.mkdir()
        (self.project / "keep.txt").write_text("project-owned\n", encoding="utf-8")
        self.project_package = self.project / "project-package.json"
        self.project_package.write_text(
            json.dumps(
                {
                    "contract": "project-knowledge-package/1",
                    "project": {"id": "test"},
                    "framework": {
                        "compatible_contracts": [
                            "reasoning-distiller-install-package/1",
                            "reasoning-distiller-installer/1",
                        ]
                    },
                    "canonical_backend": {"type": "pems-cove", "config": "backend.json"},
                    "locations": {
                        "sources": "sources",
                        "rules": "rules",
                        "roles": "roles",
                        "authority": "authority",
                        "evidence": "evidence",
                        "transactions": "transactions",
                        "dispositions": "dispositions",
                        "adapters": "adapters",
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def package(self, version: str, directory: str = "build") -> dict:
        return builder.build(version, SOURCE_COMMIT, self.artifacts / directory, ROOT)

    def install_result(self, built: dict, **kwargs) -> dict:
        return installer.install(
            built["archive"],
            built["manifest"],
            built["transport_sha256"],
            self.project,
            project_package=self.project_package,
            **kwargs,
        )

    def manifest(self) -> dict:
        return json.loads(
            (self.project / ".reasoning-distiller/.installation/MANIFEST.json").read_text(encoding="utf-8")
        )

    def payload_digest_map(self, project: Path) -> dict[str, str]:
        manifest = json.loads(
            (project / ".reasoning-distiller/.installation/MANIFEST.json").read_text(encoding="utf-8")
        )
        return {
            item["path"]: installer.sha256_file(project / ".reasoning-distiller" / item["path"])
            for item in manifest["files"]
        }

    def test_clean_install_is_local_and_preserves_project_files(self):
        built = self.package("0.1.0")
        result = self.install_result(built)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual((self.project / "keep.txt").read_text(encoding="utf-8"), "project-owned\n")
        self.assertEqual(self.manifest()["content_identity"], built["content_identity"])
        installation = json.loads(
            (self.project / ".reasoning-distiller/.installation/INSTALLATION.json").read_text(encoding="utf-8")
        )
        self.assertEqual(installation["installer"]["contract"], installer.INSTALLER_CONTRACT)
        self.assertEqual(installation["installed_at"], installer.DEFAULT_INSTALLED_AT)

    def test_same_inputs_produce_same_installed_payload_and_metadata(self):
        built = self.package("0.1.0")
        self.install_result(built)
        first_payload = self.payload_digest_map(self.project)
        first_metadata = (self.project / ".reasoning-distiller/.installation/INSTALLATION.json").read_bytes()

        second = self.base / "project2"
        second.mkdir()
        project_package2 = second / "project-package.json"
        project_package2.write_bytes(self.project_package.read_bytes())
        installer.install(
            built["archive"], built["manifest"], built["transport_sha256"], second,
            project_package=project_package2,
        )
        self.assertEqual(first_payload, self.payload_digest_map(second))
        self.assertEqual(first_metadata, (second / ".reasoning-distiller/.installation/INSTALLATION.json").read_bytes())

    def test_update_replaces_only_managed_tree(self):
        v1 = self.package("0.1.0", "v1")
        v2 = self.package("0.2.0", "v2")
        self.install_result(v1)
        self.install_result(v2)
        self.assertEqual(self.manifest()["version"], "0.2.0")
        self.assertEqual((self.project / "keep.txt").read_text(encoding="utf-8"), "project-owned\n")

    def test_downgrade_requires_explicit_authorization(self):
        v2 = self.package("0.2.0", "v2")
        v1 = self.package("0.1.0", "v1")
        self.install_result(v2)
        with self.assertRaisesRegex(ValueError, "downgrade rejected"):
            self.install_result(v1)
        self.assertEqual(self.manifest()["version"], "0.2.0")
        self.install_result(v1, allow_downgrade=True)
        self.assertEqual(self.manifest()["version"], "0.1.0")

    def test_modified_managed_file_fails_closed(self):
        built = self.package("0.1.0")
        self.install_result(built)
        item = self.manifest()["files"][0]
        path = self.project / ".reasoning-distiller" / item["path"]
        path.write_bytes(path.read_bytes() + b"drift")
        with self.assertRaisesRegex(ValueError, "managed-file drift"):
            self.install_result(self.package("0.2.0", "v2"))

    def test_unexpected_file_in_managed_root_fails_closed(self):
        built = self.package("0.1.0")
        self.install_result(built)
        extra = self.project / ".reasoning-distiller/agents/LOCAL_EDIT.txt"
        extra.write_text("no\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unexpected:agents/LOCAL_EDIT.txt"):
            self.install_result(self.package("0.2.0", "v2"))

    def test_bad_transport_digest_fails_without_live_change(self):
        built = self.package("0.1.0")
        with self.assertRaisesRegex(ValueError, "transport digest mismatch"):
            installer.install(
                built["archive"], built["manifest"], "0" * 64, self.project,
                project_package=self.project_package,
            )
        self.assertFalse((self.project / ".reasoning-distiller").exists())

    def test_incompatible_project_contract_fails_before_install(self):
        built = self.package("0.1.0")
        data = json.loads(self.project_package.read_text(encoding="utf-8"))
        data["framework"]["compatible_contracts"] = ["other/1"]
        self.project_package.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "compatibility missing"):
            self.install_result(built)
        self.assertFalse((self.project / ".reasoning-distiller").exists())

    def test_unknown_existing_managed_root_fails_closed(self):
        root = self.project / ".reasoning-distiller"
        root.mkdir()
        (root / "unknown.txt").write_text("unknown", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "without verified"):
            self.install_result(self.package("0.1.0"))

    def test_post_activation_validation_failure_restores_previous_install(self):
        v1 = self.package("0.1.0", "v1")
        v2 = self.package("0.2.0", "v2")
        self.install_result(v1)
        before = self.payload_digest_map(self.project)
        original = installer.validate_installed_tree
        calls = {"count": 0}

        def fail_live(managed, manifest):
            calls["count"] += 1
            if calls["count"] == 2:
                raise ValueError("injected post-activation failure")
            return original(managed, manifest)

        with mock.patch.object(installer, "validate_installed_tree", side_effect=fail_live):
            with self.assertRaisesRegex(ValueError, "injected post-activation failure"):
                self.install_result(v2)
        self.assertEqual(self.manifest()["version"], "0.1.0")
        self.assertEqual(before, self.payload_digest_map(self.project))
        self.assertFalse((self.project / ".rd-install-backup").exists())


if __name__ == "__main__":
    unittest.main()
