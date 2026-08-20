#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib
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

rupi = importlib.import_module("rupi")
human_agent = importlib.import_module("ril_human_agent")


def status_result(**overrides):
    dimensions = {
        "installation": "VALID",
        "project_bootstrap": "VALID",
        "operator": "MISSING",
        "role_registry": "VALID",
        "reconciliation_authority": "UNASSIGNED",
        "admission_authority": "UNASSIGNED",
        "projection_health": "VALID",
        "history_health": "VALID",
        "evidence": "NONE",
        "candidate": "NONE",
        "reconciliation": "NOT_REQUIRED",
        "admission": "NOT_READY",
    }
    value = {
        "contract": "reasoning-distiller-status/1",
        "status": "PASS",
        "dimensions": dimensions,
        "blocker": {
            "precedence": 4,
            "code": "INITIAL_OPERATOR_REQUIRED",
            "dimension": "operator",
        },
        "next_action": "ESTABLISH_INITIAL_OPERATOR",
        "lifecycle": "INITIALIZED",
        "domain_health": {},
    }
    for key, item in overrides.items():
        if key == "dimensions":
            dimensions.update(item)
        else:
            value[key] = item
    return value


class RupiCheckpointR3Tests(unittest.TestCase):
    def test_checkpoint_is_deterministic_and_does_not_mutate_inputs(self):
        status = status_result()
        primitive_results = [
            {
                "action": "bootstrap_project",
                "result": {
                    "contract": "reasoning-distiller-project-bootstrap-result/1",
                    "status": "PASS",
                    "outcome": "CREATED",
                },
            }
        ]
        status_before = copy.deepcopy(status)
        results_before = copy.deepcopy(primitive_results)
        kwargs = dict(
            requested_goal="complete project setup",
            status_result=status,
            primitive_results=primitive_results,
            capability_required=[{"capability": "semantic_reconciliation", "action": "AUTHORIZE_RECONCILIATION_STEWARD"}],
            optional_later=["configure admission authority"],
            durable_artifacts=["project-knowledge/project.json"],
            not_completed=["authority initialization"],
        )
        first = rupi.build_checkpoint(**kwargs)
        second = rupi.build_checkpoint(**kwargs)
        self.assertEqual(first, second)
        self.assertEqual(status, status_before)
        self.assertEqual(primitive_results, results_before)
        self.assertFalse(first["authoritative"])

    def test_completion_claim_requires_primitive_pass(self):
        checkpoint = rupi.build_checkpoint(
            requested_goal="install",
            status_result=status_result(),
            primitive_results=[
                {
                    "action": "verify_release_bundle",
                    "result": {
                        "contract": "reasoning-distiller-release-verification/1",
                        "status": "PASS",
                    },
                },
                {
                    "action": "install_or_update",
                    "result": {
                        "installer_contract": "reasoning-distiller-installer/1",
                        "status": "FAIL",
                        "reason_code": "MANAGED_DRIFT",
                    },
                },
            ],
        )
        self.assertEqual([item["action"] for item in checkpoint["completed_operations"]], ["verify_release_bundle"])
        self.assertEqual([item["action"] for item in checkpoint["failed_operations"]], ["install_or_update"])
        self.assertEqual(checkpoint["failed_operations"][0]["reason_code"], "MANAGED_DRIFT")

    def test_status_blocker_and_next_action_are_preserved_exactly(self):
        status = status_result()
        checkpoint = rupi.build_checkpoint(
            requested_goal="complete setup",
            status_result=status,
            primitive_results=[],
        )
        self.assertEqual(checkpoint["status"]["blocker"], status["blocker"])
        self.assertEqual(checkpoint["status"]["next_action"], "ESTABLISH_INITIAL_OPERATOR")
        self.assertEqual(checkpoint["required_next"], ["ESTABLISH_INITIAL_OPERATOR"])
        self.assertNotIn("READY", checkpoint["readiness_labels"])

    def test_readiness_labels_are_only_direct_dimension_projections(self):
        checkpoint = rupi.build_checkpoint(
            requested_goal="inspect readiness",
            status_result=status_result(dimensions={
                "operator": "VALID",
                "reconciliation_authority": "AVAILABLE",
                "admission_authority": "AVAILABLE",
            }, blocker=None, next_action="READY", lifecycle="INITIALIZED"),
            primitive_results=[],
        )
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
        self.assertEqual(checkpoint["required_next"], [])
        self.assertNotIn("READY", checkpoint["readiness_labels"])

    def test_no_percentage_progress_field_exists_anywhere(self):
        checkpoint = rupi.build_checkpoint(
            requested_goal="setup",
            status_result=status_result(),
            primitive_results=[],
        )

        def walk(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    self.assertNotIn("percent", key.lower())
                    self.assertNotIn("percentage", key.lower())
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(checkpoint)

    def test_unknown_or_malformed_primitive_observation_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown Rupi primitive action"):
            rupi.build_checkpoint(
                requested_goal="setup",
                status_result=status_result(),
                primitive_results=[{"action": "invent_authority", "result": {"status": "PASS"}}],
            )
        with self.assertRaisesRegex(ValueError, "status is required"):
            rupi.build_checkpoint(
                requested_goal="setup",
                status_result=status_result(),
                primitive_results=[{"action": "bootstrap_project", "result": {}}],
            )

    def test_non_pass_status_cannot_be_repackaged_as_checkpoint_success(self):
        status = status_result(status="FAIL")
        with self.assertRaisesRegex(ValueError, "must be a PASS result"):
            rupi.build_checkpoint(
                requested_goal="setup",
                status_result=status,
                primitive_results=[],
            )

    def test_control_return_routes_through_existing_human_agent_primitive(self):
        checkpoint = rupi.build_checkpoint(
            requested_goal="complete setup",
            status_result=status_result(),
            primitive_results=[{
                "action": "bootstrap_project",
                "result": {"contract": "reasoning-distiller-project-bootstrap-result/1", "status": "PASS", "outcome": "CREATED"},
            }],
            optional_later=["configure admission authority"],
            not_completed=["root operator setup"],
        )
        with mock.patch.object(rupi.human_agent, "control_return", wraps=human_agent.control_return) as routed:
            result = rupi.control_return_from_checkpoint(checkpoint)
        routed.assert_called_once()
        self.assertEqual(result["contract"], "reasoning-distiller-ril-human-agent-control-return/1")
        self.assertEqual(result["completed_work"], ["bootstrap_project"])
        self.assertEqual(result["boundary"], "INITIAL_OPERATOR_REQUIRED")
        self.assertIn("ESTABLISH_INITIAL_OPERATOR", result["next_actions"])

    def test_checkpoint_and_control_return_have_no_filesystem_effect(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sentinel = root / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")
            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            checkpoint = rupi.build_checkpoint(
                requested_goal="inspect",
                status_result=status_result(),
                primitive_results=[],
            )
            rupi.control_return_from_checkpoint(checkpoint)
            after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_r3_adapter_contains_no_mutation_primitive_calls(self):
        source = (RUNTIME / "rupi.py").read_text(encoding="utf-8")
        forbidden = [
            "rd_install.install(",
            "recover_interrupted_transaction(",
            "rd_bootstrap.bootstrap(",
            "apply_initial_operator(",
            "apply_authorization_change(",
            "ril_repair.repair_domain(",
            "ril_repair.repair_all(",
            "rd_steward_setup",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
