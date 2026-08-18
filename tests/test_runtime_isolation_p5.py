#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
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


builder = load_module("rd_builder_p5", ROOT / "packaging/build_release_package.py")
installer = load_module("rd_installer_p5", ROOT / "packaging/rd_install.py")
auditor = load_module("rd_audit_p5", ROOT / "packaging/audit_runtime_isolation.py")
SOURCE_COMMIT = "c" * 40


class RuntimeIsolationP5Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.artifacts = self.base / "artifacts"
        self.project = self.base / "project"
        self.project.mkdir()
        self.project_package = self.project / "project-package.json"
        self.project_package.write_text(json.dumps({
            "contract": "project-knowledge-package/1",
            "project": {"id": "p5"},
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
        built = builder.build("0.5.0-p5", SOURCE_COMMIT, self.artifacts, ROOT)
        installer.install(
            built["archive"], built["manifest"], built["transport_sha256"], self.project,
            project_package=self.project_package,
            source_repository="loteque/reasoning-distiller",
            source_locator="https://github.com/loteque/reasoning-distiller",
            update_locator="https://github.com/loteque/reasoning-distiller/releases",
        )
        self.installed = self.project / ".reasoning-distiller"
        self.blocker = self.base / "network-blocker"
        self.blocker.mkdir()
        (self.blocker / "sitecustomize.py").write_text(
            "import socket\n"
            "def _blocked(*a, **k): raise RuntimeError('network disabled by P5')\n"
            "socket.create_connection = _blocked\n"
            "socket.getaddrinfo = _blocked\n"
            "_orig_socket = socket.socket\n"
            "class BlockedSocket(_orig_socket):\n"
            "    def connect(self, *a, **k): return _blocked(*a, **k)\n"
            "    def connect_ex(self, *a, **k): return _blocked(*a, **k)\n"
            "socket.socket = BlockedSocket\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def runtime_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.blocker)
        env["HOME"] = str(self.base / "offline-home")
        env["NO_PROXY"] = "*"
        env["no_proxy"] = "*"
        for name in list(env):
            if name.lower().endswith("_proxy") and name.lower() not in {"no_proxy"}:
                env.pop(name, None)
        return env

    def run_local(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *args], cwd=self.project, env=self.runtime_env(),
            text=True, capture_output=True, check=False,
        )

    def test_audit_allows_provenance_only_repository_references(self):
        result = auditor.audit(self.installed)
        self.assertEqual(result["status"], "PASS", result)
        installation = json.loads((self.installed / ".installation/INSTALLATION.json").read_text())
        self.assertEqual(installation["source_repository"], "loteque/reasoning-distiller")

    def test_audit_rejects_executable_remote_reference(self):
        path = self.installed / "validators/remote_probe.py"
        path.write_text("URL='https://github.com/loteque/reasoning-distiller/raw/main/x'\n")
        result = auditor.audit(self.installed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(v["path"] == "validators/remote_probe.py" for v in result["violations"]))

    def test_rgp_validator_runs_from_installed_tree_with_network_blocked(self):
        graph = self.project / "candidate.json"
        graph.write_text(json.dumps({
            "records": [{
                "temp_id": "r1", "kind": "observation", "statement": "local fact",
                "provenance": {"primary": ["local:evidence"]}
            }]
        }), encoding="utf-8")
        result = self.run_local(str(self.installed / "validators/rgp_validator.py"), str(graph))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_pems_backend_contract_runs_from_installed_tree_with_network_blocked(self):
        result = self.run_local(str(self.installed / "backends/pems-cove/validate_pems2_contract.py"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS schema_draft_2020_12", result.stdout)

    def test_guarded_admission_pressure_suite_runs_locally_with_network_blocked(self):
        result = self.run_local(str(self.installed / "admission/test_admission_transaction_v2.py"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"pressure_cases": 7', result.stdout)

    def test_installed_runtime_survives_removal_of_retrieval_artifacts(self):
        shutil.rmtree(self.artifacts)
        self.assertFalse(self.artifacts.exists())
        result = self.run_local(str(self.installed / "validators/rgp_validator.py"), "--version")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "rgp-validator/1")


if __name__ == "__main__":
    unittest.main()
