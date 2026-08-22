#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/context-packaging-pressure-cases-v1.json"

EXPECTED_PLAN = {
    "repository": "loteque/reasoning-distiller",
    "commit": "0803bcca5343224d6feefa53c2f1b8baf1d4a8cd",
    "path": "docs/proposals/context-packaging/FINAL_PLAN.md",
    "blob": "8474d2da42f863f0a190fd80292085176d3f97f0",
}
EXPECTED_SOURCES = {
    "stage1": {
        "commit": "0030d502db2304e9d3a865372baba74d5910bf22",
        "path": "docs/proposals/context-packaging/01-engineer-proposal.md",
        "blob": "0561c42d0fa8a913d8e8665c21d4a79d74fb19ad",
        "case_range": "PC-01..PC-30",
    },
    "stage2": {
        "commit": "7c54f0f44f137e0ccda02ff3632eaefd235ac5af",
        "path": "docs/proposals/context-packaging/02-engineer-review-synthesis.md",
        "blob": "a9f44ed4107325db08ed186cbb9d1a58a1c8f4ee",
        "case_range": "PC-31..PC-46",
    },
}
REQUIRED_COVERAGE = {
    "authority",
    "canonical_standing",
    "byte_identity",
    "digest_circularity",
    "toolchain_variance",
    "source_conflicts",
    "side_effects",
    "renderer_isolation",
}
CASE_KEYS = {
    "id",
    "source_stage",
    "fixture_precondition",
    "expected_result",
    "failure_class",
    "coverage",
}
PRESSURE_ROW = re.compile(
    r"^\|\s*(PC-\d{2})\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$"
)


def pressure_rows(path: Path) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PRESSURE_ROW.match(line)
        if not match:
            continue
        case_id, scenario, required_outcome = match.groups()
        if case_id in rows:
            raise AssertionError(f"duplicate pressure case in {path}: {case_id}")
        rows[case_id] = (scenario, required_outcome)
    return rows


class ContextPackagingPressureSuiteP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_suite_is_bound_to_reconciled_plan_and_p0_only(self):
        self.assertEqual(
            self.suite["contract"],
            "reasoning-distiller-context-pack-pressure-suite/1",
        )
        self.assertEqual(self.suite["gate"], "P0")
        self.assertEqual(self.suite["authorized_scope"], "P0_ONLY")
        self.assertFalse(self.suite["production_integration_authorized"])
        self.assertEqual(self.suite["governing_plan"], EXPECTED_PLAN)

    def test_source_artifacts_are_immutable_and_cover_all_pressure_cases(self):
        actual = {
            source["stage"]: {
                key: source[key]
                for key in ("commit", "path", "blob", "case_range")
            }
            for source in self.suite["source_artifacts"]
        }
        self.assertEqual(actual, EXPECTED_SOURCES)

        stage1 = pressure_rows(ROOT / EXPECTED_SOURCES["stage1"]["path"])
        stage2 = pressure_rows(ROOT / EXPECTED_SOURCES["stage2"]["path"])
        self.assertEqual(set(stage1), {f"PC-{n:02d}" for n in range(1, 31)})
        self.assertEqual(set(stage2), {f"PC-{n:02d}" for n in range(31, 47)})
        for rows in (stage1, stage2):
            for case_id, (scenario, required_outcome) in rows.items():
                with self.subTest(case=case_id):
                    self.assertTrue(scenario.strip())
                    self.assertTrue(required_outcome.strip())

    def test_exactly_pc_01_through_pc_46_exist_in_order(self):
        cases = self.suite["cases"]
        self.assertEqual(len(cases), 46)
        self.assertEqual(
            [case["id"] for case in cases],
            [f"PC-{number:02d}" for number in range(1, 47)],
        )

    def test_case_shape_stage_and_machine_checkable_expectations(self):
        declared_failure_classes = set(self.suite["failure_classes"])
        self.assertEqual(
            self.suite["failure_classes"],
            sorted(declared_failure_classes),
            "failure_classes must be unique and canonically ordered",
        )

        for index, case in enumerate(self.suite["cases"], start=1):
            with self.subTest(case=case["id"]):
                self.assertEqual(set(case), CASE_KEYS)
                self.assertEqual(
                    case["source_stage"],
                    "stage1" if index <= 30 else "stage2",
                )
                self.assertTrue(case["fixture_precondition"].strip())
                self.assertIn(case["expected_result"], {"PASS", "FAIL"})
                self.assertIsInstance(case["coverage"], list)
                self.assertTrue(case["coverage"])

                if case["expected_result"] == "FAIL":
                    self.assertIn(case["failure_class"], declared_failure_classes)
                else:
                    self.assertIsNone(case["failure_class"])

    def test_every_declared_failure_class_is_exercised(self):
        declared = set(self.suite["failure_classes"])
        exercised = {
            case["failure_class"]
            for case in self.suite["cases"]
            if case["expected_result"] == "FAIL"
        }
        self.assertEqual(exercised, declared)

    def test_required_p0_coverage_is_explicit(self):
        self.assertEqual(set(self.suite["required_coverage"]), REQUIRED_COVERAGE)
        covered = {
            tag
            for case in self.suite["cases"]
            for tag in case["coverage"]
        }
        self.assertTrue(REQUIRED_COVERAGE <= covered)

    def test_p0_taxonomy_does_not_claim_runtime_failure_schema_freeze(self):
        scope = self.suite["semantics"]["failure_class_scope"]
        self.assertIn("P0 pressure-suite taxonomy", scope)
        self.assertIn("P1b owns runtime failure-schema freeze", scope)


if __name__ == "__main__":
    unittest.main()
