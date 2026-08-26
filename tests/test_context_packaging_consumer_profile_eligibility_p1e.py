import hashlib
import inspect
import json
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from tests.support.context_packaging_p1e_reference import (
    ELIGIBILITY_BINDING_MISSING,
    PROFILE_INELIGIBLE,
    evaluate_profile_eligibility,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/context-packaging-consumer-profile-eligibility-p1e.json"
SCHEMA_DIR = ROOT / "schemas"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


class P1eConsumerProfileEligibilityFreeze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load(FIXTURE)
        cls.eligibility_schema = load(SCHEMA_DIR / "context-profile-eligibility.schema.json")
        cls.request_schema = load(SCHEMA_DIR / "context-pack-request.schema.json")
        cls.failure_schema = load(SCHEMA_DIR / "context-pack-failure.schema.json")
        cls.validator = Draft202012Validator(cls.eligibility_schema)

    def test_gate_basis_scope_and_frozen_p1b_blobs(self):
        self.assertEqual(self.fixture["gate"], "P1e")
        self.assertEqual(
            self.fixture["scope"]["authorized"],
            "P1E_CONSUMER_PROFILE_ELIGIBILITY_ONLY",
        )
        self.assertFalse(self.fixture["scope"]["p1b_schema_bytes_changed"])
        self.assertFalse(self.fixture["scope"]["resolver_implemented"])
        self.assertFalse(self.fixture["scope"]["later_gates_implemented"])
        self.assertFalse(self.fixture["scope"]["production_integration_authorized"])

        for relative_path, expected_blob in self.fixture["frozen_p1b_blobs"].items():
            self.assertEqual(git_blob_sha(ROOT / relative_path), expected_blob, relative_path)

        self.assertEqual(
            self.fixture["p1d_basis"]["candidate_commit"],
            "945ff72ccee87310642ff78c4b4c8e01c46fb551",
        )
        self.assertEqual(self.fixture["p1d_basis"]["execution_run"], 32631944866)
        self.assertEqual(self.fixture["p1d_basis"]["observed_tests"], 11)
        self.assertEqual(self.fixture["p1d_basis"]["observed_outcome"], "PASS")

    def test_p1b_wire_boundary_remains_structural_and_optional(self):
        Draft202012Validator.check_schema(self.eligibility_schema)
        self.assertFalse(
            list(self.validator.iter_errors(self.fixture["examples"]["eligibility"]))
        )
        self.assertNotIn("eligibility", self.request_schema["required"])
        self.assertEqual(
            self.request_schema["properties"]["eligibility"]["$ref"],
            "https://reasoning-distiller.local/schemas/context-profile-eligibility.schema.json",
        )
        self.assertIn(
            ELIGIBILITY_BINDING_MISSING,
            self.failure_schema["properties"]["code"]["enum"],
        )
        self.assertIn(PROFILE_INELIGIBLE, self.failure_schema["properties"]["code"]["enum"])
        self.assertIn("eligibility", self.failure_schema["properties"]["stage"]["enum"])

    def test_all_semantic_cases(self):
        for case in self.fixture["cases"]:
            binding = case["eligibility_binding"]
            if binding is not None:
                self.assertFalse(
                    list(self.validator.iter_errors(binding)),
                    case["id"],
                )

            inputs = (
                deepcopy(case["requested_profile"]),
                deepcopy(binding),
                deepcopy(case["expected_consumer"]),
                deepcopy(case["required_policy_evidence"]),
            )
            before = deepcopy(inputs)
            actual = evaluate_profile_eligibility(*inputs)
            self.assertEqual(actual, case["expected"], case["id"])
            self.assertEqual(inputs, before, case["id"])

    def test_missing_binding_and_ineligible_decision_are_distinct(self):
        examples = self.fixture["examples"]
        self.assertEqual(
            evaluate_profile_eligibility(
                examples["requested_profile"],
                None,
                examples["expected_consumer"],
                examples["required_policy_evidence"],
            ),
            ELIGIBILITY_BINDING_MISSING,
        )
        denied = deepcopy(examples["eligibility"])
        denied["decision"] = "ineligible"
        self.assertEqual(
            evaluate_profile_eligibility(
                examples["requested_profile"],
                denied,
                examples["expected_consumer"],
                examples["required_policy_evidence"],
            ),
            PROFILE_INELIGIBLE,
        )

    def test_reason_code_is_non_authoritative(self):
        examples = self.fixture["examples"]
        denied = deepcopy(examples["eligibility"])
        denied["decision"] = "ineligible"
        denied["reason_code"] = "PROFILE_ALLOWED"
        self.assertEqual(
            evaluate_profile_eligibility(
                examples["requested_profile"],
                denied,
                examples["expected_consumer"],
                examples["required_policy_evidence"],
            ),
            PROFILE_INELIGIBLE,
        )

        wrong_consumer = deepcopy(examples["eligibility"])
        wrong_consumer["consumer"]["consumer_id"] = "consumer:other"
        wrong_consumer["reason_code"] = "PROFILE_ALLOWED"
        self.assertEqual(
            evaluate_profile_eligibility(
                examples["requested_profile"],
                wrong_consumer,
                examples["expected_consumer"],
                examples["required_policy_evidence"],
            ),
            PROFILE_INELIGIBLE,
        )

    def test_inference_like_fields_are_structurally_rejected(self):
        for field in self.fixture["closed_world_forbidden_fields"]:
            candidate = deepcopy(self.fixture["examples"]["eligibility"])
            candidate[field] = "not-an-eligibility-input"
            self.assertTrue(list(self.validator.iter_errors(candidate)), field)

    def test_reference_operation_has_only_explicit_p1e_inputs(self):
        signature = inspect.signature(evaluate_profile_eligibility)
        self.assertEqual(
            list(signature.parameters),
            [
                "requested_profile",
                "eligibility_binding",
                "expected_consumer",
                "required_policy_evidence",
            ],
        )
        source = inspect.getsource(evaluate_profile_eligibility)
        for forbidden in self.fixture["forbidden_reference_inputs"]:
            self.assertNotIn(forbidden, signature.parameters, forbidden)
        self.assertNotIn("open(", source)
        self.assertNotIn("Path(", source)
        self.assertNotIn("requests.", source)
        self.assertNotIn("subprocess", source)

    def test_sha256_case_normalization_only(self):
        examples = self.fixture["examples"]
        upper = deepcopy(examples["eligibility"])
        upper["profile"]["raw_sha256"] = "sha256:" + "A" * 64
        upper["policy_evidence"]["raw_sha256"] = "sha256:" + "B" * 64
        self.assertEqual(
            evaluate_profile_eligibility(
                examples["requested_profile"],
                upper,
                examples["expected_consumer"],
                examples["required_policy_evidence"],
            ),
            "eligible",
        )

        opaque_case_change = deepcopy(examples["eligibility"])
        opaque_case_change["profile"]["profile_id"] = "Context:engineer-task"
        self.assertEqual(
            evaluate_profile_eligibility(
                examples["requested_profile"],
                opaque_case_change,
                examples["expected_consumer"],
                examples["required_policy_evidence"],
            ),
            PROFILE_INELIGIBLE,
        )


if __name__ == "__main__":
    unittest.main()
