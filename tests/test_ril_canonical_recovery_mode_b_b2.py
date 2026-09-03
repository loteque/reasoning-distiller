from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_canonical_recovery_mode_b_analyzer import (  # noqa: E402
    EvidenceSpec,
    build_damage_artifacts,
)
from ril_mutation import ContractError  # noqa: E402


PEMS_PATH = "project-knowledge/canonical/pems2.jcs.json"
COVE_PATH = "project-knowledge/canonical/cove1.jcs.json"
SCHEMA_PATH = "backends/pems-cove/pems-v2.schema.json"
SOURCE_COMMIT = "95a65e2e036879ce1c7aadc22b19dd5da07106a3"
SOURCE_PATHS = (
    PEMS_PATH,
    COVE_PATH,
    "evaluation/relationship-discovery/benchmark-v1/baseline/A0-exhaustive/admission-manifest.json",
)
EVIDENCE = (
    EvidenceSpec("evaluation/context-packaging/blocker-evidence/2026-08-26-p3-pems-schema-invalid.json", "historical diagnosis; contradicted where immutable bytes differ"),
    EvidenceSpec("evaluation/context-packaging/canonical-recovery-rehearsal/2026-08-26-g8-blocked.json", "historical Mode A rehearsal"),
    EvidenceSpec("evaluation/context-packaging/canonical-recovery-rehearsal/2026-08-31-g8-corrected.json", "corrected immutable-pair rehearsal"),
    EvidenceSpec("project-knowledge/admission/receipts/35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json", "A0 admission receipt"),
    EvidenceSpec("evaluation/relationship-discovery/benchmark-v1/baseline/A0-exhaustive/admission-manifest.json", "A0 source materialization manifest"),
    EvidenceSpec("project-knowledge/admission/plans/61e6d5b80777269b06dc8aea669dbdbe05347acf8ed6f9fd6500fe7c4d75e4de.json", "A0 admission plan"),
    EvidenceSpec("project-knowledge/reconciliation/dispositions/35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json", "A0 reconciliation disposition"),
    EvidenceSpec("project-knowledge/submissions/35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json", "A0 immutable submission"),
)


class ModeBB2DamageAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schemas = [
            json.loads((ROOT / "schemas/canonical-recovery-mode-b-common.schema.json").read_text()),
            json.loads((ROOT / "schemas/canonical-recovery-damage-analysis.schema.json").read_text()),
            json.loads((ROOT / "schemas/canonical-recovery-evidence-inventory.schema.json").read_text()),
        ]
        registry = Registry().with_resources(
            [(schema["$id"], Resource.from_contents(schema)) for schema in schemas]
        )
        cls.analysis_validator = Draft202012Validator(schemas[1], registry=registry)
        cls.inventory_validator = Draft202012Validator(schemas[2], registry=registry)

    def test_inventory_schema_is_valid_draft_2020_12(self):
        Draft202012Validator.check_schema(self.inventory_validator.schema)

    def build(self, pems_path: str = PEMS_PATH, cove_path: str = COVE_PATH):
        return build_damage_artifacts(
            ROOT,
            pems_path=pems_path,
            cove_path=cove_path,
            pems_schema_path=SCHEMA_PATH,
            semantic_validator_path="backends/pems-cove/validate_pems2_contract.py",
            normalizer_path="runtime/ril_admission.py",
            cove_codec_path="runtime/ril_admission.py",
            historical_evidence=EVIDENCE,
            source_defect_commit=SOURCE_COMMIT,
            source_defect_paths=SOURCE_PATHS,
        )

    def test_exact_incident_is_complete_deterministic_and_profile_eligible(self):
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        self.assertEqual([], list(self.analysis_validator.iter_errors(first.analysis)))
        self.assertEqual([], list(self.inventory_validator.iter_errors(first.inventory)))
        self.assertEqual(first.analysis["candidate_count"], 0)
        self.assertFalse(first.analysis["damage_set"]["additional_damage"])
        self.assertEqual(first.analysis["damage_set"]["relation_count"], 668)
        self.assertEqual(len(first.analysis["damage_set"]["defects"]), 1336)
        self.assertEqual(len(first.inventory["records"]), 802)
        self.assertEqual(len(first.inventory["relations"]), 668)
        self.assertEqual(
            [item["kind"] for item in first.inventory["relations"]].count("depends_on"),
            7,
        )
        self.assertTrue(all(item["key_set"] == ["from", "id", "kind", "to"] for item in first.inventory["relations"]))
        self.assertEqual(
            {item["status"] for item in first.inventory["checks"] if item["id"].startswith("relation_") and "semantics" in item["id"]},
            {"BLOCKED"},
        )
        self.assertEqual(first.inventory["normalization"]["record_order_changed"], False)
        self.assertEqual(first.inventory["normalization"]["relation_order_changed"], False)
        self.assertEqual(first.inventory["normalization"]["semantic_content_changed"], False)

    def test_committed_artifacts_are_exact_content_addressed_output(self):
        artifacts = self.build()
        self.assertEqual(artifacts.analysis_sha256, "286d18515e88fc013a6a41ed0bf8769fc2a143cce962abd8a359298532b99499")
        self.assertEqual(artifacts.inventory_sha256, "b196cedb426eb40f3418d14059fc6d40eb378fa3b02eef8f567d51cb39be2c32")
        analysis_path = ROOT / "project-knowledge/recovery/canonical-pems-cove-mode-b/damage-analyses" / f"{artifacts.analysis_sha256}.json"
        inventory_path = ROOT / "project-knowledge/recovery/canonical-pems-cove-mode-b/evidence-inventories" / f"{artifacts.inventory_sha256}.json"
        self.assertEqual(analysis_path.read_bytes(), artifacts.analysis_bytes)
        self.assertEqual(inventory_path.read_bytes(), artifacts.inventory_bytes)

    def test_every_closed_omission_has_stable_pointer_and_keyword(self):
        defects = self.build().analysis["damage_set"]["defects"]
        self.assertEqual(
            {(item["instance_path"], item["keyword"]) for item in defects},
            {
                (f"/relations/{index}/{field}", "required")
                for index in range(668)
                for field in ("data", "lifecycle")
            },
        )

    def test_analyzer_is_read_only_and_candidate_free(self):
        observed = [PEMS_PATH, COVE_PATH, SCHEMA_PATH, *(spec.path for spec in EVIDENCE)]
        before = {path: (ROOT / path).read_bytes() for path in observed}
        artifacts = self.build()
        self.assertNotIn("candidate", artifacts.analysis)
        self.assertNotIn("plan", artifacts.analysis)
        self.assertNotIn("disposition", artifacts.analysis)
        self.assertNotIn("lifecycle", artifacts.inventory["relations"][0])
        self.assertNotIn("data", artifacts.inventory["relations"][0])
        self.assertEqual(before, {path: (ROOT / path).read_bytes() for path in observed})

    def test_any_prestate_change_is_additional_damage(self):
        original = json.loads((ROOT / PEMS_PATH).read_text())
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            relative = Path(temporary).relative_to(ROOT) / "changed.json"
            changed = copy.deepcopy(original)
            changed["records"][0]["data"]["statement"] += " changed"
            (ROOT / relative).write_text(json.dumps(changed, sort_keys=True, separators=(",", ":")))
            artifacts = self.build(relative.as_posix(), COVE_PATH)
            self.assertTrue(artifacts.analysis["damage_set"]["additional_damage"])
            equality = next(item for item in artifacts.inventory["checks"] if item["id"] == "pems_cove_decode_equality")
            self.assertEqual(equality["status"], "FAIL")

    def test_additional_schema_damage_is_not_hidden_by_closed_omissions(self):
        original = json.loads((ROOT / PEMS_PATH).read_text())
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            relative = Path(temporary).relative_to(ROOT) / "damaged.json"
            changed = copy.deepcopy(original)
            del changed["relations"][0]["kind"]
            (ROOT / relative).write_text(json.dumps(changed, sort_keys=True, separators=(",", ":")))
            artifacts = self.build(relative.as_posix(), COVE_PATH)
            self.assertTrue(artifacts.analysis["damage_set"]["additional_damage"])
            self.assertIn(
                {"instance_path": "/relations/0/kind", "keyword": "required", "message": "required property absent"},
                artifacts.analysis["damage_set"]["defects"],
            )

    def test_multiple_integrity_defects_are_all_reported(self):
        original = json.loads((ROOT / PEMS_PATH).read_text())
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            relative = Path(temporary).relative_to(ROOT) / "integrity.json"
            changed = copy.deepcopy(original)
            changed["records"][1]["id"] = changed["records"][0]["id"]
            changed["relations"][1]["id"] = changed["relations"][0]["id"]
            changed["relations"][2]["to"] = "pems:missing:endpoint"
            changed["relations"][3]["unexpected"] = True
            (ROOT / relative).write_text(json.dumps(changed, sort_keys=True, separators=(",", ":")))
            artifacts = self.build(relative.as_posix(), COVE_PATH)
            checks = {item["id"]: item["status"] for item in artifacts.inventory["checks"]}
            self.assertTrue(artifacts.analysis["damage_set"]["additional_damage"])
            self.assertEqual(checks["record_ids_unique"], "FAIL")
            self.assertEqual(checks["relation_ids_unique"], "FAIL")
            self.assertEqual(checks["relation_endpoints"], "FAIL")
            self.assertEqual(checks["relation_exact_key_sets"], "FAIL")
            self.assertTrue(any(item["keyword"] == "additionalProperties" for item in artifacts.analysis["damage_set"]["defects"]))

    def test_strict_json_duplicate_keys_fail_before_analysis(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            relative = Path(temporary).relative_to(ROOT) / "duplicate.json"
            (ROOT / relative).write_bytes(b'{"semantic":"pems/2","semantic":"pems/2","project_id":"x","records":[],"relations":[]}')
            with self.assertRaises(ContractError) as caught:
                self.build(relative.as_posix(), COVE_PATH)
            self.assertEqual(caught.exception.code, "MODE_B_PRESTATE_INVALID")

    def test_unavailable_source_provenance_fails_closed(self):
        with self.assertRaises(ContractError) as caught:
            build_damage_artifacts(
                ROOT,
                pems_path=PEMS_PATH,
                cove_path=COVE_PATH,
                pems_schema_path=SCHEMA_PATH,
                semantic_validator_path="backends/pems-cove/validate_pems2_contract.py",
                normalizer_path="runtime/ril_admission.py",
                cove_codec_path="runtime/ril_admission.py",
                historical_evidence=EVIDENCE,
                source_defect_commit="0" * 40,
                source_defect_paths=SOURCE_PATHS,
            )
        self.assertEqual(caught.exception.code, "MODE_B_EVIDENCE_INVALID")


if __name__ == "__main__":
    unittest.main()
