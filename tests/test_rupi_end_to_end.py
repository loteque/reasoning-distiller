#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

human_agent = importlib.import_module("ril_human_agent")
status_module = importlib.import_module("ril_status")
rupi = importlib.import_module("rupi")
rupi_authority = importlib.import_module("rupi_authority")
lifecycle = importlib.import_module("rupi_lifecycle")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("rd_builder_rupi_r8", ROOT / "packaging/build_release_package.py")
installer = load_module("rd_installer_rupi_r8", ROOT / "packaging/rd_install.py")
SOURCE_COMMIT = "8" * 40


def setup_intent() -> dict:
    return human_agent.bind_contextual_intent(
        "proceed with all",
        ["install_or_update", "bootstrap_project"],
        closed_set=True,
    )


def install_only_intent() -> dict:
    return human_agent.bind_contextual_intent("yes", ["install_or_update"])


def update_intent() -> dict:
    return human_agent.bind_contextual_intent("yes", ["install_or_update"])


class RupiEndToEndR8Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.project = self.base / "project"
        self.project.mkdir()
        self.artifacts = self.base / "artifacts"
        self.v1 = builder.build("0.8.0", SOURCE_COMMIT, self.artifacts / "v1", ROOT)
        self.v2 = builder.build("0.8.1", SOURCE_COMMIT, self.artifacts / "v2", ROOT)

    def tearDown(self):
        self.tmp.cleanup()

    def install_bootstrap(self) -> dict:
        return lifecycle.run_install_bootstrap_handoff(
            installer=installer,
            package=self.v1["archive"],
            manifest_path=self.v1["manifest"],
            transport_sha256=self.v1["transport_sha256"],
            target=self.project,
            bound_intent=setup_intent(),
        )

    def establish_root(self, operator_id: str = "operator:human") -> dict:
        prepared = rupi_authority.prepare_initial_root(self.project, operator_id=operator_id)
        self.assertEqual(prepared["status"], "STOPPED")
        self.assertEqual(prepared["outcome"], "INITIAL_ROOT_CONFIRMATION_REQUIRED")
        return rupi_authority.confirm_initial_root(
            self.project,
            operator_id=operator_id,
            proposal_reference=prepared["proposal_reference"],
            confirmation="ESTABLISH_ROOT_OPERATOR",
        )

    def authorize_scope(self, scope: str, operator_id: str = "operator:human") -> dict:
        prepared = rupi_authority.prepare_steward_authorization(
            self.project,
            scope=scope,
            role_id="steward:default",
        )
        self.assertEqual(prepared["status"], "STOPPED")
        self.assertEqual(prepared["outcome"], "STEWARD_CONFIRMATION_REQUIRED")
        return rupi_authority.confirm_steward_authorization(
            self.project,
            scope=scope,
            role_id="steward:default",
            approving_operator_id=operator_id,
            proposal_reference=prepared["proposal_reference"],
            confirmation="STEWARD_AUTHORIZATION_CHANGE",
        )

    def fully_configure(self) -> None:
        installed = self.install_bootstrap()
        self.assertEqual(installed["status"], "PASS")
        self.assertEqual(self.establish_root()["status"], "PASS")
        self.assertEqual(self.authorize_scope("semantic_reconciliation")["status"], "PASS")
        self.assertEqual(self.authorize_scope("admission")["status"], "PASS")

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

    def all_project_bytes(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in self.project.rglob("*")
            if path.is_file()
        }

    def test_scenario_a_fresh_project_reaches_protected_root_boundary_with_separate_primitive_evidence(self):
        result = self.install_bootstrap()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "BOOTSTRAP_COMPLETE")
        self.assertEqual(result["checkpoint"]["status"]["next_action"], "ESTABLISH_INITIAL_OPERATOR")

        actions = [item["action"] for item in result["checkpoint"]["completed_operations"]]
        self.assertEqual(
            actions,
            [
                "verify_release_bundle",
                "plan_install_transition",
                "install_or_update",
                "inspect_status",
                "bootstrap_project",
                "inspect_status",
            ],
        )

        before_authority = self.all_project_bytes()
        prepared = rupi_authority.prepare_initial_root(self.project, operator_id="operator:human")
        self.assertEqual(prepared["status"], "STOPPED")
        self.assertEqual(prepared["outcome"], "INITIAL_ROOT_CONFIRMATION_REQUIRED")
        self.assertEqual(prepared["ceremony_boundary"]["outcome"], "PROTECTED_CEREMONY_REQUIRED")
        self.assertEqual(prepared["required_confirmation"], "ESTABLISH_ROOT_OPERATOR")
        self.assertEqual(self.all_project_bytes(), before_authority)

    def test_scenario_b_first_authority_setup_binds_each_protected_mutation_independently_then_hands_off(self):
        self.assertEqual(self.install_bootstrap()["status"], "PASS")

        root = self.establish_root()
        self.assertEqual(root["status"], "PASS")
        self.assertEqual(root["outcome"], "INITIAL_ROOT_ESTABLISHED")

        recon = self.authorize_scope("semantic_reconciliation")
        self.assertEqual(recon["status"], "PASS")
        self.assertEqual(recon["scope"], "semantic_reconciliation")

        admission = self.authorize_scope("admission")
        self.assertEqual(admission["status"], "PASS")
        self.assertEqual(admission["scope"], "admission")

        status = status_module.classify_status(self.project)
        self.assertEqual(status["dimensions"]["operator"], "VALID")
        self.assertEqual(status["dimensions"]["reconciliation_authority"], "AVAILABLE")
        self.assertEqual(status["dimensions"]["admission_authority"], "AVAILABLE")
        self.assertEqual(status["next_action"], "ADD_EVIDENCE")

        for rel in (
            "project-knowledge/canonical",
            "project-knowledge/reconciliation",
            "project-knowledge/admission",
            "project-knowledge/activations",
        ):
            self.assertFalse((self.project / rel).exists(), rel)
        self.assertEqual(list((self.project / "project-knowledge/submissions").iterdir()), [])

    def test_scenario_c_update_uses_verified_installer_path_and_preserves_project_owned_state(self):
        self.fully_configure()
        before = self.project_owned_bytes()

        result = lifecycle.run_update_recovery_handoff(
            installer=installer,
            package=self.v2["archive"],
            manifest_path=self.v2["manifest"],
            transport_sha256=self.v2["transport_sha256"],
            target=self.project,
            bound_intent=update_intent(),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "UPDATED")
        self.assertEqual(self.project_owned_bytes(), before)

        actions = [item["action"] for item in result["checkpoint"]["completed_operations"]]
        self.assertEqual(actions, ["verify_release_bundle", "plan_install_transition", "install_or_update", "inspect_status"])
        self.assertEqual(result["checkpoint"]["status"]["dimensions"]["reconciliation_authority"], "AVAILABLE")
        self.assertEqual(result["checkpoint"]["status"]["dimensions"]["admission_authority"], "AVAILABLE")

    def test_scenario_d_resume_discards_conversation_and_continues_from_first_incomplete_durable_requirement(self):
        first = lifecycle.run_install_bootstrap_handoff(
            installer=installer,
            package=self.v1["archive"],
            manifest_path=self.v1["manifest"],
            transport_sha256=self.v1["transport_sha256"],
            target=self.project,
            bound_intent=install_only_intent(),
        )
        self.assertEqual(first["status"], "STOPPED")
        self.assertEqual(first["outcome"], "BOOTSTRAP_INTENT_REQUIRED")
        self.assertTrue((self.project / ".reasoning-distiller").is_dir())
        self.assertFalse((self.project / "project-knowledge/project.json").exists())

        # New invocation, no conversational state carried forward. Durable project
        # state alone must cause installation to be skipped and bootstrap to resume.
        with mock.patch.object(installer, "install", wraps=installer.install) as install_call:
            resumed = lifecycle.run_install_bootstrap_handoff(
                installer=installer,
                package=self.v1["archive"],
                manifest_path=self.v1["manifest"],
                transport_sha256=self.v1["transport_sha256"],
                target=self.project,
                bound_intent=setup_intent(),
            )
        install_call.assert_not_called()
        self.assertEqual(resumed["status"], "PASS")
        self.assertEqual(resumed["outcome"], "BOOTSTRAP_COMPLETE")
        self.assertEqual(resumed["checkpoint"]["status"]["next_action"], "ESTABLISH_INITIAL_OPERATOR")

        prepared = rupi_authority.prepare_initial_root(self.project, operator_id="operator:human")
        established = rupi_authority.confirm_initial_root(
            self.project,
            operator_id="operator:human",
            proposal_reference=prepared["proposal_reference"],
            confirmation="ESTABLISH_ROOT_OPERATOR",
        )
        self.assertEqual(established["status"], "PASS")

        # Another clean invocation reconstructs that root setup is already done.
        replay = rupi_authority.prepare_initial_root(self.project, operator_id="operator:human")
        self.assertEqual(replay["status"], "PASS")
        self.assertEqual(replay["outcome"], "INITIAL_ROOT_NOT_REQUIRED")

    def test_scenario_e_already_configured_project_reports_setup_readiness_without_mutation_or_fake_ready_state(self):
        self.fully_configure()
        before = self.all_project_bytes()

        status = status_module.classify_status(self.project)
        checkpoint = rupi.build_checkpoint(
            requested_goal="check Reasoning Distiller setup readiness",
            status_result=status,
            primitive_results=[{"action": "inspect_status", "result": status}],
        )
        control = rupi.control_return_from_checkpoint(checkpoint)
        after = self.all_project_bytes()

        self.assertEqual(after, before)
        self.assertEqual(
            checkpoint["readiness_labels"],
            [
                "FRAMEWORK_INSTALLED",
                "PROJECT_BOOTSTRAPPED",
                "AUTHORITY_INITIALIZED",
                "RECONCILIATION_READY",
                "ADMISSION_READY",
            ],
        )
        # Rupi does not invent a second lifecycle truth. Setup is ready, while the
        # authoritative semantic lifecycle correctly hands off to ADD_EVIDENCE.
        self.assertEqual(checkpoint["status"]["next_action"], "ADD_EVIDENCE")
        self.assertEqual(checkpoint["required_next"], ["ADD_EVIDENCE"])
        self.assertEqual(control["boundary"], "EVIDENCE_REQUIRED")
        self.assertNotIn("READY", checkpoint["readiness_labels"])


if __name__ == "__main__":
    unittest.main()
