from __future__ import annotations

import copy
import inspect
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import _decode, encode_cove, jcs, sha256_bytes  # noqa: E402
from ril_canonical_recovery_recipe import (  # noqa: E402
    RECIPE_ID,
    build_missing_top_level_semantic_pems2,
    git_blob_sha1,
)
from ril_mutation import ContractError  # noqa: E402


class CanonicalRecoveryModeARecipeTests(unittest.TestCase):
    def valid_pems(self) -> dict:
        return {
            "semantic": "pems/2",
            "project_id": "example-project",
            "records": [
                {
                    "id": "example-project",
                    "kind": "project",
                    "lifecycle": "current",
                    "data": {
                        "name": "Example Project",
                        "repository": "example/project",
                        "summary": "Mode A recovery fixture.",
                    },
                }
            ],
            "relations": [],
        }

    def prestate(self, doc: dict | None = None) -> tuple[dict, bytes, bytes]:
        repaired = copy.deepcopy(doc or self.valid_pems())
        source = copy.deepcopy(repaired)
        source.pop("semantic", None)
        pems_bytes = jcs(source)
        cove_bytes = jcs(encode_cove(source))
        return source, pems_bytes, cove_bytes

    def build(self, pems_bytes: bytes, cove_bytes: bytes, **overrides):
        kwargs = {
            "expected_project_id": "example-project",
            "expected_prestate_pems_sha256": sha256_bytes(pems_bytes),
            "expected_prestate_cove_sha256": sha256_bytes(cove_bytes),
            "expected_prestate_pems_git_blob": git_blob_sha1(pems_bytes),
            "expected_prestate_cove_git_blob": git_blob_sha1(cove_bytes),
            "package_root": ROOT,
        }
        kwargs.update(overrides)
        return build_missing_top_level_semantic_pems2(pems_bytes, cove_bytes, **kwargs)

    def assert_code(self, code: str, fn) -> ContractError:
        with self.assertRaises(ContractError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_exact_missing_semantic_recipe_produces_one_candidate_and_full_proof(self):
        source, pems_bytes, cove_bytes = self.prestate()
        result = self.build(pems_bytes, cove_bytes)
        expected = copy.deepcopy(source)
        expected["semantic"] = "pems/2"

        self.assertEqual(result.recipe_id, RECIPE_ID)
        self.assertEqual(result.candidate_pems_bytes, jcs(expected))
        cove = json.loads(result.candidate_cove_bytes.decode("utf-8"))
        self.assertEqual(_decode(cove["x"], cove["d"], cove["h"]), expected)
        self.assertEqual(result.candidate_pems_sha256, sha256_bytes(result.candidate_pems_bytes))
        self.assertEqual(result.candidate_cove_sha256, sha256_bytes(result.candidate_cove_bytes))
        self.assertEqual(result.equivalence_proof_sha256, sha256_bytes(result.equivalence_proof_bytes))

        proof = result.equivalence_proof
        self.assertEqual(proof["mode"], "A")
        self.assertEqual(proof["recipe_id"], RECIPE_ID)
        self.assertFalse(proof["semantic_judgment_required"])
        self.assertEqual(
            proof["semantic_delta"],
            {"operation": "insert_top_level_member", "key": "semantic", "value": "pems/2"},
        )
        self.assertEqual([item["id"] for item in proof["predicate_results"]], list(range(1, 16)))
        self.assertTrue(all(item["passed"] is True for item in proof["predicate_results"]))
        self.assertEqual(
            set(proof["identities"]),
            {"recipe", "schema", "validator", "normalizer", "serializer", "cove_codec"},
        )
        for identity in proof["identities"].values():
            self.assertEqual(len(identity["sha256"]), 64)

    def test_repeated_recipe_generation_is_byte_identical(self):
        _, pems_bytes, cove_bytes = self.prestate()
        first = self.build(pems_bytes, cove_bytes)
        second = self.build(pems_bytes, cove_bytes)
        self.assertEqual(first.candidate_pems_bytes, second.candidate_pems_bytes)
        self.assertEqual(first.candidate_cove_bytes, second.candidate_cove_bytes)
        self.assertEqual(first.equivalence_proof_bytes, second.equivalence_proof_bytes)

    def test_prestate_hash_or_blob_drift_is_rejected_before_recipe(self):
        _, pems_bytes, cove_bytes = self.prestate()
        self.assert_code(
            "CANONICAL_PRESTATE_MISMATCH",
            lambda: self.build(pems_bytes, cove_bytes, expected_prestate_pems_sha256="0" * 64),
        )
        self.assert_code(
            "CANONICAL_PRESTATE_MISMATCH",
            lambda: self.build(pems_bytes, cove_bytes, expected_prestate_pems_git_blob="0" * 40),
        )

    def test_existing_semantic_is_not_recovery_eligible(self):
        valid = self.valid_pems()
        pems_bytes = jcs(valid)
        cove_bytes = jcs(encode_cove(valid))
        self.assert_code("UNSUPPORTED_CANONICAL_DAMAGE", lambda: self.build(pems_bytes, cove_bytes))

    def test_extra_top_level_field_cannot_be_treated_as_missing_semantic_only(self):
        source, _, _ = self.prestate()
        source["profile"] = "pems/2"
        pems_bytes = jcs(source)
        cove_bytes = jcs(encode_cove(source))
        self.assert_code("UNSUPPORTED_CANONICAL_DAMAGE", lambda: self.build(pems_bytes, cove_bytes))

    def test_duplicate_json_member_is_rejected_by_strict_parser(self):
        pems_bytes = b'{"project_id":"example-project","project_id":"other","records":[],"relations":[]}'
        cove_bytes = jcs(encode_cove({"project_id": "example-project", "records": [], "relations": []}))
        self.assert_code("UNSUPPORTED_CANONICAL_DAMAGE", lambda: self.build(pems_bytes, cove_bytes))

    def test_project_identity_mismatch_is_prestate_mismatch(self):
        _, pems_bytes, cove_bytes = self.prestate()
        self.assert_code(
            "CANONICAL_PRESTATE_MISMATCH",
            lambda: self.build(pems_bytes, cove_bytes, expected_project_id="other-project"),
        )

    def test_normalization_that_reorders_graph_items_is_ineligible(self):
        valid = self.valid_pems()
        valid["records"] = [
            {
                "id": "z-source",
                "kind": "source",
                "lifecycle": "current",
                "data": {
                    "source_kind": "repository",
                    "authority": "repository_state",
                    "identity_locator": {"repository": "example/project"},
                },
            },
            valid["records"][0],
        ]
        _, pems_bytes, cove_bytes = self.prestate(valid)
        self.assert_code("UNSUPPORTED_CANONICAL_DAMAGE", lambda: self.build(pems_bytes, cove_bytes))

    def test_schema_invalid_candidate_fails_without_semantic_repair(self):
        valid = self.valid_pems()
        del valid["records"][0]["data"]["summary"]
        _, pems_bytes, cove_bytes = self.prestate(valid)
        self.assert_code("PEMS_RECOVERY_INVALID", lambda: self.build(pems_bytes, cove_bytes))

    def test_prestate_cove_disagreement_makes_mode_a_ineligible(self):
        source, pems_bytes, _ = self.prestate()
        other = copy.deepcopy(source)
        other["project_id"] = "different-project"
        cove_bytes = jcs(encode_cove(other))
        self.assert_code("COVE_PRESTATE_MISMATCH", lambda: self.build(pems_bytes, cove_bytes))

    def test_recipe_surface_has_no_transform_callback_or_dsl(self):
        params = set(inspect.signature(build_missing_top_level_semantic_pems2).parameters)
        self.assertEqual(
            params,
            {
                "prestate_pems_bytes",
                "prestate_cove_bytes",
                "expected_project_id",
                "expected_prestate_pems_sha256",
                "expected_prestate_cove_sha256",
                "expected_prestate_pems_git_blob",
                "expected_prestate_cove_git_blob",
                "package_root",
            },
        )
        self.assertFalse(any("callback" in name or "transform" in name or "dsl" in name for name in params))


if __name__ == "__main__":
    unittest.main()
