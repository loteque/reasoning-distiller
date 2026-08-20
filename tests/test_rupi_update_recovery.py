#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

bootstrap = importlib.import_module("rd_bootstrap")
human_agent = importlib.import_module("ril_human_agent")
operators = importlib.import_module("ril_operators")
steward = importlib.import_module("ril_steward_authorization")
recovery_adapter = importlib.import_module("rd_install_recovery")
lifecycle = importlib.import_module("rupi_lifecycle")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("rd_builder_rupi_r6", ROOT / "packaging/build_release_package.py")
installer = load_module("rd_installer_rupi_r6", ROOT / "packaging/rd_install.py")
SOURCE_COMMIT = "e" * 40


def update_intent() -> dict:
    return human_agent.bind_contextual_intent("yes", ["install_or_update"])


def recovery_update_intent() -> dict:
    return human_agent.bind_contextual_intent(
        "proceed with all",
        ["recover_install_transaction", "install_or_update"],
        closed_set=True,
    )


def recovery_only_intent() -> dict:
    return human_agent.bind_contextual_intent("yes", ["recover_install_transaction"])


class RupiUpdateRecoveryR6Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.project = self.base / "project"
        self.project.mkdir()
        self.artifacts = self.base / "artifacts"
        self.v1 = builder.build("0.4.1", SOURCE_COMMIT, self.artifacts / "v1", ROOT)
        self.v2 = builder.build("0.4.2", SOURCE_COMMIT, self.artifacts / "v2", ROOT)
        self.v3 = builder.build("0.4.3", SOURCE_COMMIT, self.artifacts / "v3", ROOT)

    def tearDown(self):
        self.tmp.cleanup()

    def direct_install(self, built: dict, **kwargs):
        return installer.install(
            built["archive"],
            built["manifest"],
            built["transport_sha256"],
            self.project,
            **kwargs,
        )

    def live_version(self) -> str:
        data = json.loads(
            (self.project / ".reasoning-distiller/.installation/MANIFEST.json").read_text(encoding="utf-8")
        )
        return data["version"]

    def run_flow(self, built: dict, *, intent=None, allow_downgrade: bool = False):
        return lifecycle.run_update_recovery_handoff(
            installer=installer,
            package=built["archive"],
            manifest_path=built["manifest"],
            transport_sha256=built["transport_sha256"],
            target=self.project,
            bound_intent=intent or update_intent(),
            allow_downgrade=allow_downgrade,
        )

    def project_owned_bytes(self) -> dict[str, bytes]:
        result: dict[str, bytes] = {}
        for path in self.project.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(self.project).as_posix()
            if rel.startswith(".reasoning-distiller/"):
                continue
            if rel == installer.JOURNAL_NAME or rel.startswith(installer.BACKUP_NAME + "/"):
                continue
            result[rel] = path.read_bytes()
        return result

    def establish_authority(self):
        code, boot = bootstrap.bootstrap(self.project)
        self.assertEqual(code, 0)
        self.assertEqual(boot["status"], "PASS")
        planned = operators.plan_initial_operator(self.project, "operator:human")
        approval = operators.approve_initial_operator(planned["proposal"], "operator:human")
        applied = operators.apply_initial_operator(self.project, planned["proposal"], approval)
        self.assertEqual(applied["status"], "PASS")
        planned_auth = steward.plan_authorization_change(
            self.project, "AUTHORIZE", "semantic_reconciliation", "steward:default"
        )
        approval_auth = steward.approve_authorization_change(planned_auth["proposal"], "operator:human")
        applied_auth = steward.apply_authorization_change(self.project, planned_auth["proposal"], approval_auth)
        self.assertEqual(applied_auth["status"], "PASS")

    def test_recovery_result_adapter_delegates_exactly_once_and_adds_no_recovery_semantics(self):
        calls = []

        def primitive(target, managed_root):
            calls.append((target, managed_root))
            return {"status": "RESTORED_PREVIOUS"}

        result = recovery_adapter.recover_install_transaction(
            primitive, self.project, ".reasoning-distiller"
        )
        self.assertEqual(calls, [(self.project, ".reasoning-distiller")])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "RESTORED_PREVIOUS")
        self.assertEqual(result["primitive"], "rd_install.recover_interrupted_transaction")
        self.assertEqual(result["primitive_result"], {"status": "RESTORED_PREVIOUS"})

    def test_update_uses_same_installer_mutation_primitive_as_fresh_install(self):
        self.direct_install(self.v1)
        with mock.patch.object(installer, "install", wraps=installer.install) as install_call:
            result = self.run_flow(self.v2)
        install_call.assert_called_once()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "UPDATED")
        self.assertEqual(self.live_version(), "0.4.2")
        source = (RUNTIME / "rupi_lifecycle.py").read_text(encoding="utf-8")
        self.assertNotIn("def rupi_update", source)
        self.assertIn("installer.install(", source)

    def test_no_change_reports_without_managed_tree_rewrite(self):
        self.direct_install(self.v1)
        before = {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in (self.project / ".reasoning-distiller").rglob("*")
            if path.is_file()
        }
        with mock.patch.object(installer, "install", wraps=installer.install) as install_call:
            result = self.run_flow(self.v1)
        install_call.assert_not_called()
        after = {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in (self.project / ".reasoning-distiller").rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "NO_CHANGE")

    def test_recovery_required_without_bound_recovery_intent_stops_before_recovery(self):
        self.direct_install(self.v1)
        with self.assertRaises(installer.SimulatedInterruption):
            self.direct_install(self.v2, _simulate_interrupt_after="activation")
        journal = self.project / installer.JOURNAL_NAME
        self.assertTrue(journal.exists())
        with mock.patch.object(installer, "recover_interrupted_transaction", wraps=installer.recover_interrupted_transaction) as recover_call:
            result = self.run_flow(self.v3, intent=update_intent())
        recover_call.assert_not_called()
        self.assertEqual(result["status"], "STOPPED")
        self.assertEqual(result["outcome"], "RECOVERY_INTENT_REQUIRED")
        self.assertTrue(journal.exists())

    def test_recovery_replans_before_update_and_records_one_explicit_recovery_action(self):
        self.direct_install(self.v1)
        with self.assertRaises(installer.SimulatedInterruption):
            self.direct_install(self.v2, _simulate_interrupt_after="activation")
        result = self.run_flow(self.v3, intent=recovery_update_intent())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "UPDATED")
        self.assertEqual(self.live_version(), "0.4.3")
        completed = result["checkpoint"]["completed_operations"]
        actions = [item["action"] for item in completed]
        self.assertEqual(actions.count("recover_install_transaction"), 1)
        self.assertEqual(actions.count("plan_install_transition"), 2)
        recovery = next(item for item in completed if item["action"] == "recover_install_transaction")
        self.assertEqual(recovery["outcome"], "RESTORED_PREVIOUS")
        self.assertFalse((self.project / installer.JOURNAL_NAME).exists())
        self.assertFalse((self.project / installer.BACKUP_NAME).exists())

    def test_downgrade_requires_installer_authorization_and_bounded_install_intent(self):
        self.direct_install(self.v2)
        blocked = self.run_flow(self.v1, intent=update_intent())
        self.assertEqual(blocked["status"], "STOPPED")
        self.assertEqual(blocked["outcome"], "DOWNGRADE_REQUIRES_AUTHORIZATION")
        self.assertEqual(self.live_version(), "0.4.2")

        no_intent = self.run_flow(self.v1, intent=recovery_only_intent(), allow_downgrade=True)
        self.assertEqual(no_intent["status"], "STOPPED")
        self.assertEqual(no_intent["outcome"], "INSTALL_INTENT_REQUIRED")
        self.assertEqual(self.live_version(), "0.4.2")

        allowed = self.run_flow(self.v1, intent=update_intent(), allow_downgrade=True)
        self.assertEqual(allowed["status"], "PASS")
        self.assertEqual(allowed["outcome"], "DOWNGRADED")
        self.assertEqual(self.live_version(), "0.4.1")

    def test_managed_drift_stops_before_update_mutation(self):
        self.direct_install(self.v1)
        manifest = json.loads(
            (self.project / ".reasoning-distiller/.installation/MANIFEST.json").read_text(encoding="utf-8")
        )
        path = self.project / ".reasoning-distiller" / manifest["files"][0]["path"]
        path.write_bytes(path.read_bytes() + b"drift")
        with mock.patch.object(installer, "install", wraps=installer.install) as install_call:
            result = self.run_flow(self.v2)
        install_call.assert_not_called()
        self.assertEqual(result["status"], "STOPPED")
        self.assertEqual(result["outcome"], "MANAGED_DRIFT")

    def test_update_preserves_real_project_owned_authority_state_byte_for_byte(self):
        self.direct_install(self.v1)
        self.establish_authority()
        (self.project / "project-owned.txt").write_text("keep me\n", encoding="utf-8")
        before = self.project_owned_bytes()
        result = self.run_flow(self.v2)
        after = self.project_owned_bytes()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "UPDATED")
        self.assertEqual(before, after)
        auth = steward.read_authorization(self.project)["authorization"]
        self.assertEqual(auth["assignments"]["semantic_reconciliation"], "steward:default")
        self.assertIsNone(auth["assignments"]["admission"])

    def test_update_can_surface_authority_setup_but_never_performs_it(self):
        self.direct_install(self.v1)
        code, boot = bootstrap.bootstrap(self.project)
        self.assertEqual(code, 0)
        self.assertEqual(boot["status"], "PASS")
        result = self.run_flow(self.v2)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checkpoint"]["status"]["next_action"], "ESTABLISH_INITIAL_OPERATOR")
        self.assertEqual(operators.initial_required(self.project)["outcome"], "INITIAL_OPERATOR_REQUIRED")

    def test_failed_update_rolls_back_and_rupi_never_returns_false_success(self):
        self.direct_install(self.v1)
        code, _ = bootstrap.bootstrap(self.project)
        self.assertEqual(code, 0)
        before_project = self.project_owned_bytes()
        original_validate = installer.validate_installed_tree
        calls = {"count": 0}

        def fail_live(managed, manifest):
            calls["count"] += 1
            if calls["count"] == 2:
                raise ValueError("injected live validation failure")
            return original_validate(managed, manifest)

        with mock.patch.object(installer, "validate_installed_tree", side_effect=fail_live):
            with self.assertRaisesRegex(ValueError, "injected live validation failure"):
                self.run_flow(self.v2)
        self.assertEqual(self.live_version(), "0.4.1")
        self.assertEqual(self.project_owned_bytes(), before_project)
        self.assertFalse((self.project / installer.JOURNAL_NAME).exists())
        self.assertFalse((self.project / installer.BACKUP_NAME).exists())


if __name__ == "__main__":
    unittest.main()
