import json
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
FIXTURE_PATH = ROOT / "tests/fixtures/context-packaging-protocol-schema-p1b.json"
P0_PATH = ROOT / "tests/fixtures/context-packaging-pressure-cases-v1.json"
PEMS_PATH = ROOT / "backends/pems-cove/pems-v2.schema.json"

SCHEMA_FILES = [
    "context-profile.schema.json",
    "context-pack-request.schema.json",
    "context-pack.schema.json",
    "context-pack-result.schema.json",
    "context-pack-failure.schema.json",
    "context-profile-eligibility.schema.json",
    "context-source-binding.schema.json",
    "context-pack-receipt.schema.json",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_ref(binding):
    return {k: binding[k] for k in ("source_class", "logical_namespace", "logical_source_id")}


def canonical_address(binding):
    return {k: binding[k] for k in ("project_id", "backend_type", "backend_contract", "backend_config_identity", "immutable_snapshot_id")}


def canonical_fingerprint(binding):
    value = {k: binding[k] for k in (
        "project_id", "backend_type", "backend_contract", "backend_config_identity",
        "immutable_snapshot_id", "pems_semantic", "serializer", "pems_sha256", "standing_evidence"
    )}
    if "cove" in binding:
        value["cove"] = binding["cove"]
    return value


def property_keys(schema):
    found = set()
    if isinstance(schema, dict):
        props = schema.get("properties")
        if isinstance(props, dict):
            found.update(props)
        for value in schema.values():
            found.update(property_keys(value))
    elif isinstance(schema, list):
        for value in schema:
            found.update(property_keys(value))
    return found


def object_schemas(schema):
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            yield schema
        for value in schema.values():
            yield from object_schemas(value)
    elif isinstance(schema, list):
        for value in schema:
            yield from object_schemas(value)


def mutate(instance, spec):
    value = deepcopy(instance)
    target = value
    for part in spec["path"]:
        target = target[part]
    if "delete_field" in spec:
        target.pop(spec["delete_field"], None)
    else:
        target[spec["field"]] = spec["value"]
    return value


class ContextPackagingProtocolSchemasP1bTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = {name: load_json(SCHEMA_DIR / name) for name in SCHEMA_FILES}
        cls.pems = load_json(PEMS_PATH)
        cls.fixture = load_json(FIXTURE_PATH)
        cls.p0 = load_json(P0_PATH)
        resources = [*cls.schemas.values(), cls.pems]
        cls.registry = Registry().with_resources(
            [(schema["$id"], Resource.from_contents(schema)) for schema in resources]
        )
        cls.validators = {
            name: Draft202012Validator(schema, registry=cls.registry)
            for name, schema in cls.schemas.items()
        }
        cls.examples = cls.fixture["examples"]
        cls.instances = cls._build_instances()

    @classmethod
    def _build_instances(cls):
        e = cls.examples
        repo = deepcopy(e["repository_source"])
        canonical = deepcopy(e["canonical_source"])
        operational = deepcopy(e["operational_source"])
        profile = deepcopy(e["profile"])
        eligibility = deepcopy(e["eligibility"])
        request = {
            "contract": "reasoning-distiller-context-pack-request/1",
            "request_id": "request:001",
            "profile": {"profile_id": profile["profile_id"], "profile_version": profile["profile_version"], "raw_sha256": "sha256:" + "2" * 64},
            "eligibility": eligibility,
            "source_bindings": [repo, canonical, operational],
            "slot_bindings": [
                {"slot_id": "engineer_directive", "plane": "control", "source_ref": source_ref(repo)},
                {"slot_id": "activation", "plane": "operational_evidence", "source_ref": source_ref(operational)},
            ],
            "multiple_snapshot_sources": [],
            "accepted_canonical_standing": [{
                "condition": "accepted_project_backend_canonical_standing",
                "canonical_ref": source_ref(canonical),
                "canonical_snapshot_address": canonical_address(canonical),
                "canonical_fingerprint": canonical_fingerprint(canonical),
            }],
            "knowledge_selection": {"canonical_source_ref": source_ref(canonical), "record_ids": [], "relation_ids": []},
            "consistency_requirements": [{
                "predicate": "canonical_declares_repository_snapshot",
                "left_source_ref": source_ref(canonical),
                "right_source_ref": source_ref(repo),
            }],
            "output": {"pack_contract": "reasoning-distiller-context-pack/1", "serializer": "jcs/1", "knowledge_encoding": "pems/2"},
        }
        pack = {
            "contract": "reasoning-distiller-context-pack/1",
            "profile": request["profile"],
            "request": {"request_id": request["request_id"], "raw_sha256": "sha256:" + "a" * 64},
            "eligibility": {
                "consumer_contract": eligibility["consumer"]["consumer_contract"],
                "consumer_id": eligibility["consumer"]["consumer_id"],
                "policy_evidence_snapshot_id": eligibility["policy_evidence"]["immutable_snapshot_id"],
                "decision": eligibility["decision"],
            },
            "source_registry": [repo, canonical, operational],
            "control_plane": {"items": [{"source_ref": source_ref(repo), "payload": {"encoding": "base64", "data": "Y29udHJvbA==", "raw_sha256": repo["raw_sha256"], "media_type": "text/markdown"}}]},
            "knowledge_plane": {"canonical_source_ref": source_ref(canonical), "semantic": "pems/2", "serializer": "jcs/1", "pems": deepcopy(e["minimal_pems"])},
            "operational_evidence_plane": {"items": [{
                "source_ref": source_ref(operational),
                "validation_status": operational["validation_status"],
                "validation_result": operational["validation_result"],
                "payload": {"encoding": "base64", "data": "ZXZpZGVuY2U=", "raw_sha256": operational["raw_sha256"], "media_type": "application/json"},
            }]},
            "inclusion_ledger": [
                {"plane": "control", "subject": {"source_ref": source_ref(repo)}, "causes": [{"kind": "profile_slot", "cause_id": "engineer_directive"}]},
                {"plane": "knowledge", "subject": {"source_ref": source_ref(canonical)}, "causes": [{"kind": "request_selector", "cause_id": "explicit-empty-selection"}]},
                {"plane": "operational_evidence", "subject": {"source_ref": source_ref(operational)}, "causes": [{"kind": "profile_slot", "cause_id": "activation"}]},
            ],
            "identity": {
                "profile_sha256": "sha256:" + "2" * 64,
                "request_sha256": "sha256:" + "a" * 64,
                "canonical_state_binding_sha256s": ["sha256:" + "b" * 64],
                "selected_pems_sha256": canonical["pems_sha256"],
                "manifest_sha256": "sha256:" + "c" * 64,
                "payload_set_sha256": "sha256:" + "e" * 64,
                "pack_identity_sha256": "sha256:" + "f" * 64,
            },
            "toolchain": {"components": [{"role": "pems_schema", "contract": "pems/2", "immutable_identity": "blob:cd7683d7", "raw_sha256": "sha256:" + "a" * 64}]},
        }
        result_success = {"contract": "reasoning-distiller-context-pack-result/1", "request_id": request["request_id"], "status": "success", "pack": {"contract": "reasoning-distiller-context-pack/1", "pack_identity_sha256": pack["identity"]["pack_identity_sha256"]}}
        result_failure = {"contract": "reasoning-distiller-context-pack-result/1", "request_id": request["request_id"], "status": "failure", "failure": deepcopy(e["failure"])}
        return {
            "repository_source": repo,
            "package_source": deepcopy(e["package_source"]),
            "canonical_source": canonical,
            "operational_source": operational,
            "profile": profile,
            "eligibility": eligibility,
            "request": request,
            "pack": pack,
            "failure": deepcopy(e["failure"]),
            "result_success": result_success,
            "result_failure": result_failure,
            "receipt": deepcopy(e["receipt"]),
        }

    def validate(self, schema_name, instance):
        return list(self.validators[schema_name].iter_errors(instance))

    def test_schema_meta_validity(self):
        for name, schema in self.schemas.items():
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema", name)
            Draft202012Validator.check_schema(schema)

    def test_gate_scope_and_contract_inventory(self):
        self.assertEqual(self.fixture["gate"], "P1b")
        self.assertEqual(self.fixture["scope"]["authorized"], "P1B_PROTOCOL_SCHEMAS_ONLY")
        self.assertFalse(self.fixture["scope"]["resolver_implemented"])
        self.assertFalse(self.fixture["scope"]["later_gates_implemented"])
        self.assertFalse(self.fixture["scope"]["production_integration_authorized"])
        self.assertEqual({item["file"] for item in self.fixture["schemas"]}, set(SCHEMA_FILES))

    def test_semantics_bearing_objects_are_closed_world(self):
        for name, schema in self.schemas.items():
            for obj in object_schemas(schema):
                self.assertIs(obj.get("additionalProperties"), False, name)

    def test_valid_examples_validate(self):
        mapping = {
            "repository_source": "context-source-binding.schema.json",
            "package_source": "context-source-binding.schema.json",
            "canonical_source": "context-source-binding.schema.json",
            "operational_source": "context-source-binding.schema.json",
            "profile": "context-profile.schema.json",
            "eligibility": "context-profile-eligibility.schema.json",
            "request": "context-pack-request.schema.json",
            "pack": "context-pack.schema.json",
            "failure": "context-pack-failure.schema.json",
            "result_success": "context-pack-result.schema.json",
            "result_failure": "context-pack-result.schema.json",
            "receipt": "context-pack-receipt.schema.json",
        }
        for key, schema_name in mapping.items():
            self.assertEqual(self.validate(schema_name, self.instances[key]), [], key)

    def test_negative_fixtures_fail_closed(self):
        schema_for = {
            "profile": "context-profile.schema.json",
            "request": "context-pack-request.schema.json",
            "repository_source": "context-source-binding.schema.json",
            "operational_source": "context-source-binding.schema.json",
            "pack": "context-pack.schema.json",
            "failure": "context-pack-failure.schema.json",
            "result_success": "context-pack-result.schema.json",
            "receipt": "context-pack-receipt.schema.json",
            "eligibility": "context-profile-eligibility.schema.json",
        }
        failure_codes = set(self.schemas["context-pack-failure.schema.json"]["properties"]["code"]["enum"])
        for case in self.fixture["negative_cases"]:
            instance = mutate(self.instances[case["target"]], case["mutation"])
            self.assertTrue(self.validate(schema_for[case["target"]], instance), case["id"])
            self.assertIn(case["expected_failure_code"], failure_codes, case["id"])

    def test_pc38_is_preserved_exactly(self):
        pc38 = next(case for case in self.p0["cases"] if case["id"] == "PC-38")
        binding = self.fixture["pressure_case_bindings"][0]
        self.assertEqual(binding["source_pressure_case"], pc38["source_pressure_case"])
        self.assertEqual(binding["required_outcome"], pc38["required_outcome"])
        self.assertEqual(binding["schema_cases"], ["PS-13", "PS-14", "PS-15"])

    def test_runtime_failure_schema_covers_p0_taxonomy(self):
        p0_codes = set(self.p0["failure_classes"])
        runtime_codes = set(self.schemas["context-pack-failure.schema.json"]["properties"]["code"]["enum"])
        self.assertLessEqual(p0_codes, runtime_codes)

    def test_source_schema_preserves_p1a_frozen_axes(self):
        text = json.dumps(self.schemas["context-source-binding.schema.json"], sort_keys=True)
        for value in ("repository_control", "package_control", "canonical_state", "operational_evidence", "carried_unvalidated", "shape_and_digest_validated", "accepted_validation_result", "accepted_project_backend_canonical_standing"):
            self.assertIn(value, text)

    def test_no_authority_or_ambient_escape_hatch_property(self):
        banned = {"trusted", "authorized", "activated", "ambient_memory", "assistant_memory", "hidden_reasoning", "semantic_query"}
        keys = set().union(*(property_keys(schema) for schema in self.schemas.values()))
        self.assertFalse(keys & banned)

    def test_result_and_receipt_have_no_wall_clock_fields(self):
        for name in ("context-pack-result.schema.json", "context-pack-receipt.schema.json"):
            keys = property_keys(self.schemas[name])
            self.assertNotIn("timestamp", keys)
            self.assertNotIn("created_at", keys)


if __name__ == "__main__":
    unittest.main()
