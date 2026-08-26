import hashlib
import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

from context_packaging.pems_projection import project_pems
from context_packaging.source_resolver import ResolvedSource

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = ROOT / "protocols/rgp/pems2-context-closure-v1.json"
VALIDATOR = ROOT / "backends/pems-cove/validate_pems2_contract.py"


def raw_sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def load_validator():
    spec = importlib.util.spec_from_file_location("p3_test_pems_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def valid_doc():
    valid, _invalid = load_validator().structural_smoke_documents()
    return deepcopy(valid)


def encode(doc):
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def binding(data, snapshot="snapshot:001", logical="canonical"):
    return {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "canonical_state",
        "logical_namespace": "project:test",
        "logical_source_id": logical,
        "project_id": "test",
        "backend_type": "pems-cove",
        "backend_contract": "project-canonical-backend/1",
        "backend_config_identity": "config:001",
        "immutable_snapshot_id": snapshot,
        "pems_semantic": "pems/2",
        "serializer": "jcs/1",
        "pems_sha256": raw_sha(data),
        "standing_evidence": [
            {
                "contract": "canonical-standing-evidence/1",
                "immutable_snapshot_id": "standing:001",
                "raw_sha256": raw_sha(b"standing"),
            }
        ],
    }


def snapshot_ref(value):
    return {key: deepcopy(item) for key, item in value.items() if key not in {"contract", "repository_relationship"}}


def profile(**limits):
    descriptor_raw = DESCRIPTOR.read_bytes()
    projection = {
        "max_records": 100,
        "max_relations": 100,
        "max_depth": 20,
        "max_bytes": 1_000_000,
    }
    projection.update(limits)
    return {
        "contract": "reasoning-distiller-context-profile/1",
        "knowledge": {
            "required": True,
            "canonical_slot_id": "canonical",
            "selector_kinds": ["record_id", "relation_id"],
            "empty_result": "allow",
            "snapshot_multiplicity": "single",
            "closure_descriptor": {
                "contract": "reasoning-distiller-pems2-closure-descriptor/1",
                "semantic": "pems/2",
                "immutable_snapshot_id": "git-blob:" + blob_sha(descriptor_raw),
                "raw_sha256": raw_sha(descriptor_raw),
            },
        },
        "limits": {"projection": projection},
    }


def request(value, record_ids=(), relation_ids=()):
    return {
        "contract": "reasoning-distiller-context-pack-request/1",
        "knowledge_selection": {
            "snapshots": [
                {
                    "canonical_snapshot_ref": snapshot_ref(value),
                    "record_ids": list(record_ids),
                    "relation_ids": list(relation_ids),
                }
            ]
        },
    }


def run(doc, record_ids=(), relation_ids=(), prof=None):
    data = encode(doc)
    value = binding(data)
    return project_pems(
        request(value, record_ids, relation_ids),
        profile() if prof is None else prof,
        [ResolvedSource(value, data)],
    )


class P3ProjectionTests(unittest.TestCase):
    def test_exact_selection_excludes_unselected_but_closes_provenance(self):
        doc = valid_doc()
        asserted = next(r for r in doc["records"] if r["id"] == "pems:proposition:a")
        result = run(doc, record_ids=[asserted["id"]])
        self.assertTrue(result.ok)
        item = result.items[0]
        ids = [record["id"] for record in item.pems["records"]]
        self.assertEqual(
            ids,
            ["pems:project:p", "pems:source:s", "pems:source_observation:o", "pems:proposition:a"],
        )
        self.assertEqual(item.pems["relations"], [])
        self.assertNotIn("pems:proposition:b", ids)
        projected_a = next(r for r in item.pems["records"] if r["id"] == asserted["id"])
        self.assertEqual(projected_a, asserted)

    def test_derived_proposition_includes_all_required_premise_structure(self):
        doc = valid_doc()
        result = run(doc, record_ids=["pems:proposition:b"])
        self.assertTrue(result.ok)
        item = result.items[0]
        self.assertEqual([r["id"] for r in item.pems["relations"]], ["pems:relation:r"])
        self.assertEqual(
            {r["id"] for r in item.pems["records"]},
            {r["id"] for r in doc["records"]},
        )

    def test_selected_relation_closes_endpoints_and_preserves_multiple_causes(self):
        doc = valid_doc()
        result = run(
            doc,
            record_ids=["pems:proposition:b"],
            relation_ids=["pems:relation:r"],
        )
        self.assertTrue(result.ok)
        relation_causes = [
            cause for cause in result.items[0].causes
            if cause.namespace == "relation" and cause.semantic_id == "pems:relation:r"
        ]
        self.assertEqual({cause.kind for cause in relation_causes}, {"request_selector", "pems_closure"})
        self.assertEqual(len({cause.cause_id for cause in relation_causes}), 2)

    def test_request_order_does_not_change_projection_or_causes(self):
        doc = valid_doc()
        data = encode(doc)
        value = binding(data)
        first = project_pems(
            request(value, ["pems:proposition:a", "pems:project:p"]),
            profile(),
            [ResolvedSource(value, data)],
        )
        second = project_pems(
            request(value, ["pems:project:p", "pems:proposition:a"]),
            profile(),
            [ResolvedSource(value, data)],
        )
        self.assertEqual(first.items[0].pems, second.items[0].pems)
        self.assertEqual(first.items[0].causes, second.items[0].causes)

    def test_missing_selected_id_fails_without_fuzzy_substitution(self):
        result = run(valid_doc(), record_ids=["pems:proposition:missing"])
        self.assertEqual(result.failure["code"], "SELECTED_SEMANTIC_ID_MISSING")
        self.assertEqual(result.failure["stage"], "projection")

    def test_explicit_reject_rule_fails_closed(self):
        doc = valid_doc()
        project = next(r for r in doc["records"] if r["kind"] == "project")
        project["supersedes"] = ["pems:source:s"]
        result = run(doc, record_ids=[project["id"]])
        self.assertEqual(result.failure["code"], "UNDEFINED_CLOSURE_RULE")

    def test_cycle_terminates_by_namespace_identity(self):
        doc = valid_doc()
        source = next(r for r in doc["records"] if r["kind"] == "source")
        source["provenance"] = {"primary": ["pems:source_observation:o"]}
        result = run(doc, record_ids=[source["id"]])
        self.assertTrue(result.ok)
        causes = [
            cause for cause in result.items[0].causes
            if cause.namespace == "record" and cause.semantic_id == source["id"]
        ]
        self.assertEqual({cause.kind for cause in causes}, {"request_selector", "pems_closure"})

    def test_projection_limits_fail_without_truncation(self):
        result = run(valid_doc(), record_ids=["pems:proposition:b"], prof=profile(max_depth=2))
        self.assertEqual(result.failure["code"], "CLOSURE_LIMIT_EXCEEDED")
        self.assertIn("projection.max_depth", result.failure["diagnostics"][0])

        result = run(valid_doc(), record_ids=["pems:proposition:a"], prof=profile(max_records=3))
        self.assertEqual(result.failure["code"], "CLOSURE_LIMIT_EXCEEDED")
        self.assertIn("projection.max_records", result.failure["diagnostics"][0])

        result = run(valid_doc(), record_ids=["pems:proposition:a"], prof=profile(max_bytes=10))
        self.assertEqual(result.failure["code"], "CLOSURE_LIMIT_EXCEEDED")
        self.assertIn("projection.max_bytes", result.failure["diagnostics"][0])

    def test_empty_selector_policy_is_explicit(self):
        allowed = run(valid_doc())
        self.assertTrue(allowed.ok)
        self.assertEqual([r["kind"] for r in allowed.items[0].pems["records"]], ["project"])

        prof = profile()
        prof["knowledge"]["empty_result"] = "reject"
        rejected = run(valid_doc(), prof=prof)
        self.assertEqual(rejected.failure["code"], "EMPTY_RESULT_DISALLOWED")

    def test_package_owned_schema_and_semantic_validation_are_both_enforced(self):
        schema_bad = valid_doc()
        schema_bad["unexpected"] = True
        result = run(schema_bad, record_ids=["pems:project:p"])
        self.assertEqual(result.failure["code"], "PEMS_SCHEMA_INVALID")

        semantic_bad = valid_doc()
        semantic_bad["relations"] = []
        result = run(semantic_bad, record_ids=["pems:proposition:b"])
        self.assertEqual(result.failure["code"], "PEMS_SEMANTIC_INVALID")

    def test_profile_must_bind_exact_package_closure_descriptor(self):
        prof = profile()
        prof["knowledge"]["closure_descriptor"]["raw_sha256"] = raw_sha(b"different")
        result = run(valid_doc(), record_ids=["pems:project:p"], prof=prof)
        self.assertEqual(result.failure["code"], "TOOLCHAIN_IDENTITY_MISMATCH")
        self.assertEqual(result.failure["stage"], "toolchain")

    def test_profile_selector_vocabulary_is_enforced(self):
        prof = profile()
        prof["knowledge"]["selector_kinds"] = ["record_id"]
        result = run(valid_doc(), relation_ids=["pems:relation:r"], prof=prof)
        self.assertEqual(result.failure["code"], "INVALID_REQUEST")

    def test_p3_has_no_cove_pack_persistence_or_mutation_surface(self):
        doc = valid_doc()
        before = deepcopy(doc)
        result = run(doc, record_ids=["pems:proposition:a"])
        self.assertTrue(result.ok)
        self.assertEqual(doc, before)
        public = set(vars(__import__("context_packaging.pems_projection", fromlist=["*"])))
        self.assertNotIn("encode_cove", public)
        self.assertNotIn("build_pack", public)
        self.assertNotIn("persist", public)
        self.assertNotIn("render", public)


if __name__ == "__main__":
    unittest.main()
