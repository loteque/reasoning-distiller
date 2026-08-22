import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
EVALUATION = ROOT / "evaluation"
RUNTIME = ROOT / "runtime"
sys.path.insert(0, str(EVALUATION))
sys.path.insert(0, str(RUNTIME))

spec = importlib.util.spec_from_file_location(
    "relationship_discovery_admission",
    EVALUATION / "relationship_discovery_admission.py",
)
admission = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(admission)

from ril_activation import validate_activation  # noqa: E402
from ril_admission import apply_plan, normalize_pems  # noqa: E402
from ril_mutation import digest  # noqa: E402


class RelationshipDiscoveryAdmissionTests(unittest.TestCase):
    def test_materialized_admission_is_exact_and_record_preserving(self):
        manifest = admission.validate_materialized()
        self.assertEqual(manifest["record_count"], 802)
        self.assertEqual(manifest["relation_count"], 668)
        self.assertEqual(
            manifest["counts_by_relation_type"],
            {"depends_on": 7, "supports": 661},
        )
        self.assertEqual(
            manifest["recommended_relations_digest"],
            admission.EXPECTED_RECOMMENDED_DIGEST,
        )

        candidate_path = (
            ROOT
            / "project-knowledge"
            / "submissions"
            / f"{manifest['candidate_digest'].split(':', 1)[1]}.json"
        )
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        self.assertEqual(candidate["source_pems_sha256"], f"sha256:{admission.EXPECTED_BASE_PEMS_SHA256}")
        self.assertEqual(candidate["source_cove_sha256"], f"sha256:{admission.EXPECTED_BASE_COVE_SHA256}")
        self.assertEqual(candidate["recommended_relation_count"], 668)
        self.assertEqual(candidate["recommended_relations_digest"], admission.EXPECTED_RECOMMENDED_DIGEST)

        plan_path = (
            ROOT
            / "project-knowledge"
            / "admission"
            / "plans"
            / f"{manifest['plan_digest'].split(':', 1)[1]}.json"
        )
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["new_records"], [])
        self.assertEqual(plan["record_updates"], [])
        self.assertEqual(plan["reuse_record_ids"], [])
        self.assertEqual(len(plan["new_relations"]), 668)
        self.assertEqual(len({item["id"] for item in plan["new_relations"]}), 668)
        self.assertTrue(all(set(item) == {"id", "from", "kind", "to"} for item in plan["new_relations"]))

    def test_admission_activation_is_exact_and_authorized(self):
        manifest = admission.validate_materialized()
        activation_path = (
            ROOT
            / "project-knowledge"
            / "admission"
            / "activation-evidence"
            / f"{manifest['admission_activation_digest'].split(':', 1)[1]}.json"
        )
        activation = json.loads(activation_path.read_text(encoding="utf-8"))
        self.assertEqual(digest(activation), admission.EXPECTED_ADMISSION_ACTIVATION_DIGEST)
        self.assertEqual(activation["role_id"], admission.ADMISSION_ROLE_ID)
        self.assertEqual(activation["context"]["invocation_id"], admission.ADMISSION_INVOCATION_ID)
        self.assertEqual(activation["context"]["source"], admission.ADMISSION_SOURCE)
        result = validate_activation(ROOT, "admission", activation)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "ACTIVATION_ACCEPTED"))

    def test_plan_is_stale_against_admitted_canon(self):
        manifest = admission.validate_materialized()
        plan_path = (
            ROOT
            / "project-knowledge"
            / "admission"
            / "plans"
            / f"{manifest['plan_digest'].split(':', 1)[1]}.json"
        )
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        current = normalize_pems(
            json.loads((ROOT / "project-knowledge/canonical/pems2.jcs.json").read_text(encoding="utf-8"))
        )
        with self.assertRaisesRegex(ValueError, "plan not built against current canonical PEMS"):
            apply_plan(current, plan)

    def test_approved_relation_mutation_breaks_candidate_identity(self):
        manifest = admission.validate_materialized()
        candidate_path = (
            ROOT
            / "project-knowledge"
            / "submissions"
            / f"{manifest['candidate_digest'].split(':', 1)[1]}.json"
        )
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        damaged = copy.deepcopy(candidate)
        damaged["approved_relations"][0]["type"] = "depends_on"
        self.assertNotEqual(digest(damaged), manifest["candidate_digest"])


if __name__ == "__main__":
    unittest.main()
