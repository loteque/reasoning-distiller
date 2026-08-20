#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.util
import json
import socket
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

bootstrap = importlib.import_module("rd_bootstrap")
human_agent = importlib.import_module("ril_human_agent")
operators = importlib.import_module("ril_operators")
steward = importlib.import_module("ril_steward_authorization")
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


builder = load_module("rd_builder_rupi_r7", ROOT / "packaging/build_release_package.py")
installer = load_module("rd_installer_rupi_r7", ROOT / "packaging/rd_install.py")
SOURCE_COMMIT = "f" * 40


def install_only_intent() -> dict:
    return human_agent.bind_contextual_intent("yes", ["install_or_update"])


def setup_intent() -> dict:
    disclosure = human_agent.disclose_bounded_chain(["install_or_update", "bootstrap_project"])
    return human_agent.bind_contextual_intent(
        "proceed with all",
        disclosure["operations"],
        closed_set=disclosure["closed_set"],
    )


def update_intent() -> dict:
    return human_agent.bind_contextual_intent("yes", ["install_or_update"])


class RupiAdversarialR7Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.project = self.base / "project"
        self.project.mkdir()
        self.artifacts = self.base / "artifacts"
        self.v1 = builder.build("0.4.1", SOURCE_COMMIT, self.artifacts / "v1", ROOT)
        self.v2 = builder.build("0.4.2", SOURCE_COMMIT, self.artifacts / "v2", ROOT)

    def tearDown(self):
        self.tmp.cleanup()

    def direct_install(self, built: dict | None = None, **kwargs):
        built = built or self.v1
        return installer.install(
            built["archive"],
            built["manifest"],
            built["transport_sha256"],
            self.project,
            **kwargs,
        )

    def install_and_bootstrap(self):
        self.direct_install()
        code, result = bootstrap.bootstrap(self.project)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "PASS")

    def establish_root(self, operator_id: str = "operator:human"):
        prepared = rupi_authority.prepare_initial_root(self.project, operator_id=operator_id)
        self.assertEqual(prepared["status"], "STOPPED")
        self.assertEqual(prepared["outcome"], "INITIAL_ROOT_CONFIRMATION_REQUIRED")
        result = rupi_authority.confirm_initial_root(
            self.project,
            operator_id=operator_id,
            proposal_reference=prepared["proposal_reference"],
            confirmation="ESTABLISH_ROOT_OPERATOR",
        )
        self.assertEqual(result["status"], "PASS")
        return result

    def authorize_scope(self, scope: str, role_id: str = "steward:default", operator_id: str = "operator:human"):
        prepared = rupi_authority.prepare_steward_authorization(
            self.project,
            scope=scope,
            role_id=role_id,
        )
        self.assertEqual(prepared["status"], "STOPPED")
        self.assertEqual(prepared["outcome"], "STEWARD_CONFIRMATION_REQUIRED")
        result = rupi_authority.confirm_steward_authorization(
            self.project,
            scope=scope,
            role_id=role_id,
            approving_operator_id=operator_id,
            proposal_reference=prepared["proposal_reference"],
            confirmation="STEWARD_AUTHORIZATION_CHANGE",
        )
        self.assertEqual(result["status"], "PASS")
        return result

    def test_01_admin_language_before_exact_root_proposal_has_no_authority(self):
        self.install_and_bootstrap()
        intent = human_agent.bind_contextual_intent(
            "just make me the admin",
            ["apply_initial_operator"],
        )
        self.assertEqual(intent["status"], "STOPPED")
        self.assertEqual(intent["outcome"], "NO_AUTHORITY")
        with mock.patch.object(rupi_authority, "prepare_initial_root", wraps=rupi_authority.prepare_initial_root) as prepare:
            if intent["status"] == "PASS":
                prepare(self.project, operator_id="operator:human")
        prepare.assert_not_called()
        self.assertEqual(operators.initial_required(self.project)["outcome"], "INITIAL_OPERATOR_REQUIRED")

    def test_02_repository_or_runner_identity_is_never_inferred_as_operator(self):
        result = lifecycle.run_install_bootstrap_handoff(
            installer=installer,
            package=self.v1["archive"],
            manifest_path=self.v1["manifest"],
            transport_sha256=self.v1["transport_sha256"],
            target=self.project,
            bound_intent=setup_intent(),
            runner_id="operator:loteque",
            source_repository="operator:loteque/reasoning-distiller",
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checkpoint"]["status"]["next_action"], "ESTABLISH_INITIAL_OPERATOR")
        self.assertEqual(operators.initial_required(self.project)["outcome"], "INITIAL_OPERATOR_REQUIRED")
        missing = rupi_authority.prepare_initial_root(self.project, operator_id=None)
        self.assertEqual(missing["status"], "STOPPED")
        self.assertEqual(missing["outcome"], "OPERATOR_ID_REQUIRED")

    def test_03_install_only_intent_never_silently_bootstraps_or_initializes_authority(self):
        result = lifecycle.run_install_bootstrap_handoff(
            installer=installer,
            package=self.v1["archive"],
            manifest_path=self.v1["manifest"],
            transport_sha256=self.v1["transport_sha256"],
            target=self.project,
            bound_intent=install_only_intent(),
        )
        self.assertEqual(result["status"], "STOPPED")
        self.assertEqual(result["outcome"], "BOOTSTRAP_INTENT_REQUIRED")
        self.assertTrue((self.project / ".reasoning-distiller").is_dir())
        self.assertFalse((self.project / "project-knowledge/project.json").exists())
        self.assertEqual(operators.initial_required(self.project)["outcome"], "INITIAL_OPERATOR_REQUIRED")

    def test_04_disclosed_install_setup_chain_still_stops_at_protected_root_boundary(self):
        result = lifecycle.run_install_bootstrap_handoff(
            installer=installer,
            package=self.v1["archive"],
            manifest_path=self.v1["manifest"],
            transport_sha256=self.v1["transport_sha256"],
            target=self.project,
            bound_intent=setup_intent(),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outcome"], "BOOTSTRAP_COMPLETE")
        self.assertEqual(result["control_return"]["boundary"], "INITIAL_OPERATOR_REQUIRED")
        self.assertEqual(operators.initial_required(self.project)["outcome"], "INITIAL_OPERATOR_REQUIRED")
        events_dir, projection = operators.operator_paths(self.project)
        self.assertFalse(events_dir.exists())
        self.assertFalse(projection.exists())

    def test_05_approve_all_without_closed_steward_set_is_ambiguous(self):
        self.install_and_bootstrap()
        self.establish_root()
        recon = rupi_authority.prepare_steward_authorization(
            self.project, scope="semantic_reconciliation", role_id="steward:default"
        )
        admission = rupi_authority.prepare_steward_authorization(
            self.project, scope="admission", role_id="steward:default"
        )
        self.assertEqual(recon["status"], "STOPPED")
        self.assertEqual(admission["status"], "STOPPED")
        intent = human_agent.bind_contextual_intent(
            "approve all",
            ["authorize semantic_reconciliation", "authorize admission"],
            closed_set=False,
        )
        self.assertEqual(intent["status"], "STOPPED")
        self.assertEqual(intent["outcome"], "AMBIGUOUS_INTENT")
        auth = steward.read_authorization(self.project)["authorization"]
        self.assertIsNone(auth["assignments"]["semantic_reconciliation"])
        self.assertIsNone(auth["assignments"]["admission"])

    def test_06_admission_ready_label_cannot_contradict_status_authority_dimension(self):
        self.install_and_bootstrap()
        self.establish_root()
        status = status_module.classify_status(self.project)
        self.assertEqual(status["dimensions"]["admission_authority"], "UNASSIGNED")
        checkpoint = rupi.build_checkpoint(
            requested_goal="inspect readiness",
            status_result=status,
            primitive_results=[{"action": "inspect_status", "result": status}],
        )
        self.assertNotIn("ADMISSION_READY", checkpoint["readiness_labels"])
        self.assertEqual(
            "ADMISSION_READY" in checkpoint["readiness_labels"],
            status["dimensions"]["admission_authority"] == "AVAILABLE",
        )

    def test_07_stale_update_plan_loses_to_installer_revalidation(self):
        self.direct_install(self.v1)
        mutated = {"done": False}

        def stale_plan(*args, **kwargs):
            result = installer.plan_installation_transition(*args, **kwargs)
            if result.get("outcome") == "UPDATE" and not mutated["done"]:
                live_manifest = json.loads(
                    (self.project / ".reasoning-distiller/.installation/MANIFEST.json").read_text(encoding="utf-8")
                )
                victim = self.project / ".reasoning-distiller" / live_manifest["files"][0]["path"]
                victim.write_bytes(victim.read_bytes() + b"post-plan-drift")
                mutated["done"] = True
            return result

        surface = SimpleNamespace(
            INSTALLER_CONTRACT=installer.INSTALLER_CONTRACT,
            RELEASE_VERIFICATION_CONTRACT=installer.RELEASE_VERIFICATION_CONTRACT,
            TRANSITION_PLAN_CONTRACT=installer.TRANSITION_PLAN_CONTRACT,
            verify_release_bundle=installer.verify_release_bundle,
            plan_installation_transition=stale_plan,
            install=installer.install,
            recover_interrupted_transaction=installer.recover_interrupted_transaction,
        )
        with self.assertRaisesRegex(ValueError, "managed-file drift"):
            lifecycle.run_update_recovery_handoff(
                installer=surface,
                package=self.v2["archive"],
                manifest_path=self.v2["manifest"],
                transport_sha256=self.v2["transport_sha256"],
                target=self.project,
                bound_intent=update_intent(),
            )
        live = json.loads(
            (self.project / ".reasoning-distiller/.installation/MANIFEST.json").read_text(encoding="utf-8")
        )
        self.assertEqual(live["version"], "0.4.1")

    def test_08_available_legacy_steward_setup_is_never_an_authority_route(self):
        self.install_and_bootstrap()
        self.establish_root()
        legacy = SimpleNamespace(run=mock.Mock(side_effect=AssertionError("legacy path invoked")))
        with mock.patch.dict(sys.modules, {"rd_steward_setup": legacy}):
            self.authorize_scope("semantic_reconciliation")
        legacy.run.assert_not_called()
        source = (RUNTIME / "rupi_authority.py").read_text(encoding="utf-8")
        self.assertNotIn("rd_steward_setup", source)
        auth = steward.read_authorization(self.project)["authorization"]
        self.assertEqual(auth["assignments"]["semantic_reconciliation"], "steward:default")

    def test_09_candidate_after_setup_is_handed_off_not_reconciled_or_admitted(self):
        self.install_and_bootstrap()
        self.establish_root()
        self.authorize_scope("semantic_reconciliation")
        self.authorize_scope("admission")
        candidate = self.project / "project-knowledge/submissions/candidate.json"
        candidate.write_text("{}\n", encoding="utf-8")

        status = status_module.classify_status(self.project)
        self.assertEqual(status["dimensions"]["candidate"], "PENDING")
        self.assertEqual(status["next_action"], "PROVIDE_ACTIVATION_EVIDENCE")
        checkpoint = rupi.build_checkpoint(
            requested_goal="finish lifecycle setup",
            status_result=status,
            primitive_results=[{"action": "inspect_status", "result": status}],
        )
        control = rupi.control_return_from_checkpoint(checkpoint)
        self.assertEqual(control["boundary"], "ACTIVATION_EVIDENCE_REQUIRED")
        self.assertIn("PROVIDE_ACTIVATION_EVIDENCE", control["next_actions"])
        self.assertFalse((self.project / "project-knowledge/reconciliation").exists())
        self.assertFalse((self.project / "project-knowledge/admission").exists())
        self.assertFalse((self.project / "project-knowledge/canonical").exists())
        lifecycle_source = (RUNTIME / "rupi_lifecycle.py").read_text(encoding="utf-8")
        authority_source = (RUNTIME / "rupi_authority.py").read_text(encoding="utf-8")
        self.assertNotIn("ril_reconciliation", lifecycle_source + authority_source)
        self.assertNotIn("ril_admission", lifecycle_source + authority_source)

    def test_10_reinvocation_without_conversation_reconstructs_same_next_action(self):
        self.install_and_bootstrap()
        before = {
            p.relative_to(self.project).as_posix(): p.read_bytes()
            for p in self.project.rglob("*")
            if p.is_file()
        }
        first = rupi_authority.prepare_initial_root(self.project, operator_id="operator:human")
        second = rupi_authority.prepare_initial_root(self.project, operator_id="operator:human")
        after = {
            p.relative_to(self.project).as_posix(): p.read_bytes()
            for p in self.project.rglob("*")
            if p.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(first["status"], second["status"])
        self.assertEqual(first["outcome"], second["outcome"])
        self.assertEqual(first["proposal_reference"], second["proposal_reference"])
        self.assertEqual(first["checkpoint"]["status"], second["checkpoint"]["status"])

    def test_11_invalid_authoritative_history_surfaces_recovery_boundary_without_repair(self):
        self.install_and_bootstrap()
        self.establish_root()
        events_dir, _ = operators.operator_paths(self.project)
        event = sorted(events_dir.glob("*.json"))[0]
        event.write_text("{}\n", encoding="utf-8")
        before = {
            p.relative_to(self.project).as_posix(): p.read_bytes()
            for p in self.project.rglob("*")
            if p.is_file()
        }
        status = status_module.classify_status(self.project)
        self.assertEqual(status["dimensions"]["history_health"], "INVALID")
        self.assertEqual(status["next_action"], "REPAIR_HISTORY")
        self.assertEqual(status["blocker"]["code"], "AUTHORITATIVE_HISTORY_INVALID")
        checkpoint = rupi.build_checkpoint(
            requested_goal="resume lifecycle setup",
            status_result=status,
            primitive_results=[{"action": "inspect_status", "result": status}],
        )
        control = rupi.control_return_from_checkpoint(checkpoint)
        after = {
            p.relative_to(self.project).as_posix(): p.read_bytes()
            for p in self.project.rglob("*")
            if p.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(checkpoint["required_next"], ["REPAIR_HISTORY"])
        self.assertEqual(control["boundary"], "AUTHORITATIVE_HISTORY_INVALID")
        self.assertFalse(any(item["action"].startswith("repair") for item in checkpoint["completed_operations"]))

    def test_12_local_release_update_remains_deterministic_with_network_blocked(self):
        self.direct_install(self.v1)

        def network_forbidden(*args, **kwargs):
            raise AssertionError("network access attempted after local release assets were pinned")

        with mock.patch.object(socket, "create_connection", side_effect=network_forbidden), \
             mock.patch.object(urllib.request, "urlopen", side_effect=network_forbidden):
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
        live = json.loads(
            (self.project / ".reasoning-distiller/.installation/MANIFEST.json").read_text(encoding="utf-8")
        )
        self.assertEqual(live["version"], "0.4.2")


if __name__ == "__main__":
    unittest.main()
