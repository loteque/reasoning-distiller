#!/usr/bin/env python3
from __future__ import annotations

import io
import importlib.util
import json
import tarfile
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


builder = load_module("rd_builder_rupi_r2", ROOT / "packaging/build_release_package.py")
installer = load_module("rd_installer_rupi_r2", ROOT / "packaging/rd_install.py")


class RupiInstallerPrimitiveTests(unittest.TestCase):
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
                    "project": {"id": "rupi-r2"},
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

    def package(self, version: str, name: str, source_commit: str = "a" * 40) -> dict:
        return builder.build(version, source_commit, self.artifacts / name, ROOT)

    def install(self, built: dict, **kwargs) -> dict:
        return installer.install(
            built["archive"],
            built["manifest"],
            built["transport_sha256"],
            self.project,
            project_package=self.project_package,
            **kwargs,
        )

    def plan(self, built: dict, **kwargs) -> dict:
        return installer.plan_installation_transition(
            built["manifest"],
            self.project,
            project_package=self.project_package,
            **kwargs,
        )

    def rewrite_archive(self, built: dict, name: str, mutate) -> tuple[Path, Path, str]:
        archive = self.base / f"{name}.tar.gz"
        with tarfile.open(built["archive"], "r:gz") as source:
            members = []
            for member in source.getmembers():
                extracted = source.extractfile(member) if member.isfile() else None
                data = extracted.read() if extracted is not None else b""
                members.append((member, data))
        members = mutate(members)
        with tarfile.open(archive, "w:gz") as target:
            for member, data in members:
                target.addfile(member, io.BytesIO(data) if member.isfile() else None)
        transport = installer.sha256_file(archive)
        manifest = self.base / f"{name}.manifest.json"
        value = json.loads(Path(built["manifest"]).read_text(encoding="utf-8"))
        value["transport_sha256"] = transport
        manifest.write_text(
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return archive, manifest, transport

    def test_release_verification_is_read_only_and_reports_identity(self):
        built = self.package("0.1.0", "verify")
        before = sorted(path.relative_to(self.project).as_posix() for path in self.project.rglob("*"))
        result = installer.verify_release_bundle(
            built["archive"], built["manifest"], built["transport_sha256"]
        )
        after = sorted(path.relative_to(self.project).as_posix() for path in self.project.rglob("*"))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["contract"], installer.RELEASE_VERIFICATION_CONTRACT)
        self.assertEqual(result["content_identity"], built["content_identity"])
        self.assertEqual(before, after)
        self.assertFalse((self.project / ".reasoning-distiller").exists())

    def test_release_verification_rejects_bad_transport_and_archive_mismatch(self):
        built = self.package("0.1.0", "bad")
        bad_digest = installer.verify_release_bundle(
            built["archive"], built["manifest"], "0" * 64
        )
        self.assertEqual(bad_digest["status"], "FAIL")

        archive, manifest, transport = self.rewrite_archive(
            built,
            "missing-member",
            lambda members: members[:-1],
        )
        mismatch = installer.verify_release_bundle(archive, manifest, transport)
        self.assertEqual(mismatch["status"], "FAIL")
        self.assertEqual(mismatch["outcome"], "INVALID_RELEASE")

    def test_release_verification_rejects_mode_mismatch(self):
        built = self.package("0.1.0", "mode")

        def change_mode(members):
            members[0][0].mode ^= 0o100
            return members

        archive, manifest, transport = self.rewrite_archive(built, "mode-mismatch", change_mode)
        result = installer.verify_release_bundle(archive, manifest, transport)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("mode mismatch", result["detail"])

    def test_transition_planner_classifies_fresh_no_change_update_and_downgrade(self):
        v1 = self.package("0.1.0", "v1")
        v2 = self.package("0.2.0", "v2")
        self.assertEqual(self.plan(v1)["outcome"], "FRESH_INSTALL")
        self.install(v1)
        self.assertEqual(self.plan(v1)["outcome"], "NO_CHANGE")
        self.assertEqual(self.plan(v2)["outcome"], "UPDATE")
        self.install(v2)
        self.assertEqual(self.plan(v1)["outcome"], "DOWNGRADE_REQUIRES_AUTHORIZATION")
        self.assertEqual(self.plan(v1, allow_downgrade=True)["outcome"], "DOWNGRADE")

    def test_same_version_different_identity_is_collision(self):
        first = self.package("1.0.0", "first", "a" * 40)
        other = self.package("1.0.0", "other", "b" * 40)
        self.install(first)
        plan = self.plan(other)
        self.assertEqual(plan["outcome"], "IDENTITY_COLLISION")
        with self.assertRaisesRegex(ValueError, "same release version"):
            self.install(other)

    def test_drift_plan_and_install_fail_closed_consistently(self):
        v1 = self.package("0.1.0", "drift-v1")
        v2 = self.package("0.2.0", "drift-v2")
        self.install(v1)
        manifest = json.loads(
            (self.project / ".reasoning-distiller/.installation/MANIFEST.json").read_text(encoding="utf-8")
        )
        path = self.project / ".reasoning-distiller" / manifest["files"][0]["path"]
        path.write_bytes(path.read_bytes() + b"drift")
        plan = self.plan(v2)
        self.assertEqual(plan["outcome"], "MANAGED_DRIFT")
        with self.assertRaisesRegex(ValueError, "managed-file drift"):
            self.install(v2)

    def test_unknown_managed_tree_and_incompatible_project_are_classified(self):
        root = self.project / ".reasoning-distiller"
        root.mkdir()
        (root / "unknown.txt").write_text("unknown", encoding="utf-8")
        built = self.package("0.1.0", "unknown")
        plan = self.plan(built)
        self.assertEqual(plan["outcome"], "INCOMPATIBLE")
        self.assertEqual(plan["reason_code"], "MANAGED_STATE_INVALID")

        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
        root.rmdir()
        data = json.loads(self.project_package.read_text(encoding="utf-8"))
        data["framework"]["compatible_contracts"] = ["other/1"]
        self.project_package.write_text(json.dumps(data), encoding="utf-8")
        incompatible = self.plan(built)
        self.assertEqual(incompatible["outcome"], "INCOMPATIBLE")
        self.assertEqual(incompatible["reason_code"], "PROJECT_INCOMPATIBLE")

    def test_interrupted_transaction_is_observed_not_recovered_by_planner(self):
        v1 = self.package("0.1.0", "recovery-v1")
        v2 = self.package("0.2.0", "recovery-v2")
        v3 = self.package("0.3.0", "recovery-v3")
        self.install(v1)
        with self.assertRaises(installer.SimulatedInterruption):
            self.install(v2, _simulate_interrupt_after="activation")
        journal = self.project / installer.JOURNAL_NAME
        before = journal.read_bytes()
        plan = self.plan(v3)
        self.assertEqual(plan["outcome"], "RECOVERY_REQUIRED")
        self.assertEqual(journal.read_bytes(), before)
        result = self.install(v3)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["recovery_before_install"], "RESTORED_PREVIOUS")

    def test_install_uses_shared_verification_and_transition_internals(self):
        built = self.package("0.1.0", "shared")
        with mock.patch.object(
            installer,
            "_verify_release_bundle_internal",
            wraps=installer._verify_release_bundle_internal,
        ) as verify, mock.patch.object(
            installer,
            "_plan_installation_transition_internal",
            wraps=installer._plan_installation_transition_internal,
        ) as plan:
            self.install(built)
        self.assertEqual(verify.call_count, 1)
        self.assertEqual(plan.call_count, 1)

    def test_stale_successful_plan_never_bypasses_install_revalidation(self):
        v1 = self.package("0.1.0", "stale-v1")
        v2 = self.package("0.2.0", "stale-v2")
        self.install(v1)
        self.assertEqual(self.plan(v2)["outcome"], "UPDATE")
        manifest = json.loads(
            (self.project / ".reasoning-distiller/.installation/MANIFEST.json").read_text(encoding="utf-8")
        )
        path = self.project / ".reasoning-distiller" / manifest["files"][0]["path"]
        path.write_bytes(path.read_bytes() + b"after-plan")
        with self.assertRaisesRegex(ValueError, "managed-file drift"):
            self.install(v2)


if __name__ == "__main__":
    unittest.main()
