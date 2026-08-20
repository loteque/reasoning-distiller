#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

lifecycle = importlib.import_module("rupi_lifecycle")
human_agent = importlib.import_module("ril_human_agent")
status_module = importlib.import_module("ril_status")
bootstrap_module = importlib.import_module("rd_bootstrap")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("rd_builder_rupi_r4", ROOT / "packaging/build_release_package.py")
installer = load_module("rd_installer_rupi_r4", ROOT / "packaging/rd_install.py")
SOURCE_COMMIT = "c" * 40


def setup_intent() -> dict:
    return human_agent.bind_contextual_intent(
        "proceed with all",
        ["install_or_update", "bootstrap_project"],
        closed_set=True,
    )


def install_only_intent() -> dict:
    return human_agent.bind_contextual_intent("yes", ["install_or_update"])


class RupiInstallBootstrapR4Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.project = self.base / "project"
        self.project.mkdir()
        self.artifacts = self.base / "artifacts"
        self.built = builder.build("0.4.2", SOURCE_COMMIT, self.artifacts, ROOT)

    def tearDown(self):
        self.tmp.cleanup()

    def run_flow(self, *, surface=installer, intent=None):
        return lifecycle.run_install_bootstrap_handoff(
            installer=surface,
            package=self.built["archive"],
            manifest_path=self.built["manifest"],
            transport_sha256=self.built["transport_sha256"],
            target=self.project,
            bound_intent=intent or setup_intent(),
        )

    def direct_install(self):
        return installer.install(
            self.built["archive"],
            self.built["manifest"],
            self.built["transport_sha256"],
            self.project,
        )

    def test_fresh_install_runs_exact_primitive_chain_and_stops_at_authority_boundary(self):
        calls: list[str] = []
        original_verify = installer.verify_release_bundle
        original_plan = installer.plan_installation_transition
        original_install = installer.install
        original_status = status_module.classify_status
        original_bootstrap = bootstrap_module.bootstrap

        def verify(*args, **kwargs):
            calls.append("verify_release_bundle")
            return original_verify(*args, **kwargs)

        def plan(*args, **kwargs):
            calls.append("plan_install_transition")
            return original_plan(*args, **kwargs)

        def install(*args, **kwargs):
            calls.append("install_or_update")
            return original_install(*args, **kwargs)

        def status(*args, **kwargs):
            calls.append("inspect_status")
            return original_status(*args, **kwargs)

        def bootstrap(*args, **kwargs):
            calls.append("bootstrap_project")
            return original_bootstrap(*args, **kwargs)

        with mock.patch.object(installer, "verify_release_bundle", side_effect=verify), \
             mock.patch.object(installer, "plan_installation_transition", side_effect=plan), \
             mock.patch.object(installer, "install", side_effect=install), \
             mock.patch.object(lifecycle.ril_status, "classify_status", side_effect=status), \
             mock.patch.object(lifecycle.rd_bootstrap, "bootstrap", side_effect=bootstrap):
            result = self.run_flow()

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "BOOTSTRAP_COMPLETE")
        self.assertEqual(
            calls,
            [
                "verify_release_bundle",
                "plan_install_transition",
                "install_or_update",
                "inspect_status",
                "bootstrap_project",
                "inspect_status",
            ],
        )
        self.assertTrue((self.project / ".reasoning-distiller").is_dir())
        self.assertTrue((self.project / "project-knowledge/project.json").is_file())
        checkpoint = result["checkpoint"]
        self.assertEqual(checkpoint["status"]["next_action"], "ESTABLISH_INITIAL_OPERATOR")
        self.assertEqual(result["control_return"]["boundary"], "INITIAL_OPERATOR_REQUIRED")
        self.assertIn(".reasoning-distiller", checkpoint["durable_artifacts"])
        self.assertIn("project-knowledge/project.json", checkpoint["durable_artifacts"])

    def test_already_installed_unbootstrapped_skips_install_and_runs_bootstrap(self):
        self.direct_install()
        with mock.patch.object(installer, "install", wraps=installer.install) as install_call, \
             mock.patch.object(lifecycle.rd_bootstrap, "bootstrap", wraps=bootstrap_module.bootstrap) as bootstrap_call:
            result = self.run_flow()
        install_call.assert_not_called()
        bootstrap_call.assert_called_once_with(self.project.resolve())
        self.assertEqual(result["outcome"], "BOOTSTRAP_COMPLETE")
        self.assertTrue((self.project / "project-knowledge/project.json").is_file())

    def test_already_installed_and_bootstrapped_is_no_change_without_mutation(self):
        self.direct_install()
        code, boot = bootstrap_module.bootstrap(self.project)
        self.assertEqual(code, 0)
        self.assertEqual(boot["status"], "PASS")
        before = {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in self.project.rglob("*")
            if path.is_file()
        }
        with mock.patch.object(installer, "install", wraps=installer.install) as install_call, \
             mock.patch.object(lifecycle.rd_bootstrap, "bootstrap", wraps=bootstrap_module.bootstrap) as bootstrap_call:
            result = self.run_flow()
        install_call.assert_not_called()
        bootstrap_call.assert_not_called()
        after = {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in self.project.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "BOOTSTRAP_NOT_REQUIRED")

    def test_partial_compatible_bootstrap_state_is_completed_by_bootstrap_primitive(self):
        self.direct_install()
        evidence = self.project / "project-knowledge/evidence"
        evidence.mkdir(parents=True)
        result = self.run_flow()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "BOOTSTRAP_COMPLETE")
        completed = [item for item in result["checkpoint"]["completed_operations"] if item["action"] == "bootstrap_project"]
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["outcome"], "COMPLETED")
        self.assertTrue((self.project / "project-knowledge/invocations").is_dir())
        self.assertTrue((self.project / "project-knowledge/submissions").is_dir())

    def test_bootstrap_conflict_stops_before_any_authority_work(self):
        self.direct_install()
        pk = self.project / "project-knowledge"
        pk.mkdir()
        (pk / "project.json").write_text("{}\n", encoding="utf-8")
        result = self.run_flow()
        self.assertEqual(result["status"], "STOPPED")
        self.assertEqual(result["outcome"], "BOOTSTRAP_FAILED")
        self.assertEqual(result["checkpoint"]["status"]["blocker"]["code"], "PROJECT_BOOTSTRAP_CONFLICT")
        self.assertEqual(result["checkpoint"]["boundary"], "PROJECT_BOOTSTRAP_CONFLICT")
        failed = [item["action"] for item in result["checkpoint"]["failed_operations"]]
        self.assertEqual(failed, ["bootstrap_project"])
        self.assertFalse((self.project / "project-knowledge/operators").exists())
        self.assertFalse((self.project / "project-knowledge/steward-authorization").exists())

    def test_install_failure_never_advances_to_status_or_bootstrap(self):
        surface = SimpleNamespace(
            INSTALLER_CONTRACT=installer.INSTALLER_CONTRACT,
            RELEASE_VERIFICATION_CONTRACT=installer.RELEASE_VERIFICATION_CONTRACT,
            TRANSITION_PLAN_CONTRACT=installer.TRANSITION_PLAN_CONTRACT,
            verify_release_bundle=installer.verify_release_bundle,
            plan_installation_transition=installer.plan_installation_transition,
            install=mock.Mock(side_effect=ValueError("injected install failure")),
        )
        with mock.patch.object(lifecycle.rd_bootstrap, "bootstrap", wraps=bootstrap_module.bootstrap) as bootstrap_call, \
             mock.patch.object(lifecycle.ril_status, "classify_status", wraps=status_module.classify_status) as status_call:
            with self.assertRaisesRegex(ValueError, "injected install failure"):
                self.run_flow(surface=surface)
        surface.install.assert_called_once()
        status_call.assert_not_called()
        bootstrap_call.assert_not_called()
        self.assertFalse((self.project / "project-knowledge").exists())

    def test_install_success_followed_by_new_bootstrap_blocker_is_observed_and_stops(self):
        def install_then_conflict(*args, **kwargs):
            result = installer.install(*args, **kwargs)
            (self.project / "project-knowledge").write_text("conflict\n", encoding="utf-8")
            return result

        surface = SimpleNamespace(
            INSTALLER_CONTRACT=installer.INSTALLER_CONTRACT,
            RELEASE_VERIFICATION_CONTRACT=installer.RELEASE_VERIFICATION_CONTRACT,
            TRANSITION_PLAN_CONTRACT=installer.TRANSITION_PLAN_CONTRACT,
            verify_release_bundle=installer.verify_release_bundle,
            plan_installation_transition=installer.plan_installation_transition,
            install=install_then_conflict,
        )
        result = self.run_flow(surface=surface)
        self.assertEqual(result["status"], "STOPPED")
        self.assertEqual(result["outcome"], "BOOTSTRAP_FAILED")
        self.assertEqual(result["checkpoint"]["status"]["blocker"]["code"], "PROJECT_BOOTSTRAP_CONFLICT")
        self.assertEqual(result["control_return"]["boundary"], "PROJECT_BOOTSTRAP_CONFLICT")

    def test_bootstrap_requires_bound_intent_even_after_successful_install(self):
        result = self.run_flow(intent=install_only_intent())
        self.assertEqual(result["status"], "STOPPED")
        self.assertEqual(result["outcome"], "BOOTSTRAP_INTENT_REQUIRED")
        self.assertEqual(result["checkpoint"]["status"]["next_action"], "BOOTSTRAP_PROJECT")
        self.assertEqual(result["checkpoint"]["boundary"], "INTENT_REQUIRED")
        self.assertTrue((self.project / ".reasoning-distiller").is_dir())
        self.assertFalse((self.project / "project-knowledge").exists())

    def test_installer_surface_must_match_exact_primitive_contracts(self):
        bad_surface = SimpleNamespace(
            INSTALLER_CONTRACT="other/1",
            RELEASE_VERIFICATION_CONTRACT=installer.RELEASE_VERIFICATION_CONTRACT,
            TRANSITION_PLAN_CONTRACT=installer.TRANSITION_PLAN_CONTRACT,
            verify_release_bundle=installer.verify_release_bundle,
            plan_installation_transition=installer.plan_installation_transition,
            install=installer.install,
        )
        with self.assertRaisesRegex(ValueError, "INSTALLER_CONTRACT mismatch"):
            self.run_flow(surface=bad_surface)
        self.assertFalse((self.project / ".reasoning-distiller").exists())


if __name__ == "__main__":
    unittest.main()
