#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


rupi_map = load_module("rupi_primitive_map_test", ROOT / "runtime/rupi_primitive_map.py")


class RupiPrimitiveInventoryTests(unittest.TestCase):
    def test_required_action_surface_is_frozen(self):
        required = {
            "inspect_status",
            "verify_release_bundle",
            "plan_install_transition",
            "install_or_update",
            "recover_install_transaction",
            "bootstrap_project",
            "plan_initial_operator",
            "approve_initial_operator",
            "apply_initial_operator",
            "plan_steward_authorization",
            "approve_steward_authorization",
            "apply_steward_authorization",
            "create_activation",
            "validate_activation",
            "repair_projection",
            "repair_all_projections",
            "disclose_bounded_chain",
            "bind_contextual_intent",
            "present_proposal",
            "protected_ceremony_boundary",
            "control_return",
        }
        self.assertEqual(set(rupi_map.PRIMITIVE_MAP), required)

    def test_every_action_names_exactly_one_governing_primitive(self):
        for action, spec in rupi_map.PRIMITIVE_MAP.items():
            self.assertEqual(set(spec), {"kind", "primitive"}, action)
            self.assertIsInstance(spec["primitive"], str)
            self.assertIn(".", spec["primitive"])
            self.assertNotEqual(spec["primitive"].split(".", 1)[0], "rupi", action)

    def test_rupi_does_not_route_authority_through_legacy_steward_setup(self):
        mapped = {spec["primitive"] for spec in rupi_map.PRIMITIVE_MAP.values()}
        self.assertTrue(mapped.isdisjoint(rupi_map.LEGACY_FORBIDDEN_SURFACES))
        self.assertNotIn("rd_steward_setup.run", mapped)

    def test_primitive_map_document_is_deterministic_and_detached(self):
        first = rupi_map.primitive_map_document()
        second = rupi_map.primitive_map_document()
        self.assertEqual(first, second)
        first["actions"]["inspect_status"]["primitive"] = "changed"
        self.assertEqual(
            rupi_map.PRIMITIVE_MAP["inspect_status"]["primitive"],
            "ril_status.classify_status",
        )

    def test_only_known_action_kinds_are_used(self):
        allowed = {"read", "mutation", "authority", "evidence", "presentation", "intent"}
        self.assertTrue({spec["kind"] for spec in rupi_map.PRIMITIVE_MAP.values()} <= allowed)


if __name__ == "__main__":
    unittest.main()
