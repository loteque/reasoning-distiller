import hashlib
import json
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

R = Path(__file__).resolve().parents[1]
S = R / "schemas"
P1B = R / "tests/fixtures/context-packaging-protocol-schema-p1b.json"
PRESSURE = R / "tests/fixtures/context-packaging-v2-pressure-cases.json"
RESOURCE_REGISTRY = S / "resources/context-packaging-v2-resource-registry.json"
PEMS_PATH = R / "backends/pems-cove/pems-v2.schema.json"
PEMS_RESOURCE_ID = "urn:reasoning-distiller:schema-resource:pems-v2:git-blob:cd7683d704e8aef2842a0c1b25b453fb1dbc8030"

V1_BLOBS = {
    "context-pack-failure.schema.json": "10195c52df81156a954eb9b5acee5a4f1b26f576",
    "context-pack-receipt.schema.json": "b8ef42aec266acd87c5a0b45740e7122c30114e5",
    "context-pack-request.schema.json": "602391284019ab680bd419c7d007e7af3cfeef53",
    "context-pack-result.schema.json": "7a3566b3b4db97119ea88d75c2b5622d151ba3a4",
    "context-pack.schema.json": "4b240a5698294ce1a217ad758b4031830740fc29",
    "context-profile-eligibility.schema.json": "ad8ba5839136fe7e1080d1d7e26ca351202864dc",
    "context-profile.schema.json": "8a363d376d20375de6c985c342437e856805a69b",
    "context-source-binding.schema.json": "e5d5bc005f7a3dcd4f2f788dd08d49f3b57d4a1e",
}
V2_FILES = [
    "context-profile-v2.schema.json",
    "context-pack-request-v2.schema.json",
    "context-pack-v2.schema.json",
    "context-pack-result-v2.schema.json",
]


def load(path):
    return json.loads(path.read_text())


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def canonical_snapshot_ref(binding):
    keys = (
        "source_class", "logical_namespace", "logical_source_id", "project_id",
        "backend_type", "backend_contract", "backend_config_identity",
        "immutable_snapshot_id", "pems_semantic", "serializer", "pems_sha256",
        "standing_evidence",
    )
    return {k: deepcopy(binding[k]) for k in keys}


class ContextPackagingV2Schemas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v2 = {name: load(S / name) for name in V2_FILES}
        cls.shared = {
            name: load(S / name)
            for name in (
                "context-pack-failure.schema.json",
                "context-pack-receipt.schema.json",
                "context-profile-eligibility.schema.json",
                "context-source-binding.schema.json",
            )
        }
        cls.pems = load(PEMS_PATH)
        cls.resource_registry = load(RESOURCE_REGISTRY)
        cls.fixture = load(P1B)
        cls.pressure = load(PRESSURE)
        resources = []
        for schema in [*cls.v2.values(), *cls.shared.values()]:
            resources.append((schema["$id"], Resource.from_contents(schema)))
        resources.append((PEMS_RESOURCE_ID, Resource.from_contents(cls.pems)))
        cls.registry = Registry().with_resources(resources)
        cls.validators = {
            name: Draft202012Validator(schema, registry=cls.registry)
            for name, schema in cls.v2.items()
        }

    def test_r4_resource_is_exact_local_blob_and_sha256(self):
        registry = self.resource_registry
        self.assertEqual(registry["contract"], "reasoning-distiller-context-schema-resource-registry/1")
        self.assertEqual(len(registry["resources"]), 1)
        item = registry["resources"][0]
        data = PEMS_PATH.read_bytes()
        self.assertEqual(item["resource_id"], PEMS_RESOURCE_ID)
        self.assertEqual(item["git_blob"], git_blob_sha(data))
        self.assertEqual(item["raw_sha256"], "sha256:" + hashlib.sha256(data).hexdigest())
        self.assertFalse(item["network_resolution"])
        self.assertEqual(item["resolution"], "register_exact_blob_bytes_under_resource_id")
        self.assertIn("/blob/main/", self.pems["$id"])
        pack_text = (S / "context-pack-v2.schema.json").read_text()
        self.assertIn(PEMS_RESOURCE_ID, pack_text)
        self.assertNotIn("github.com/loteque/reasoning-distiller/blob/main/backends/pems-cove/pems-v2.schema.json", pack_text)

    def test_accepted_v1_schema_blobs_are_unchanged(self):
        for name, expected in V1_BLOBS.items():
            self.assertEqual(git_blob_sha((S / name).read_bytes()), expected, name)

    def test_v2_schema_meta_and_contract_family(self):
        for schema in self.v2.values():
            Draft202012Validator.check_schema(schema)
        self.assertEqual(self.v2["context-profile-v2.schema.json"]["properties"]["contract"]["const"], "reasoning-distiller-context-profile/2")
        contracts = self.v2["context-profile-v2.schema.json"]["properties"]["contracts"]["properties"]
        self.assertEqual(contracts["request"]["const"], "reasoning-distiller-context-pack-request/2")
        self.assertEqual(contracts["pack"]["const"], "reasoning-distiller-context-pack/2")
        self.assertEqual(contracts["result"]["const"], "reasoning-distiller-context-pack-result/2")
        self.assertEqual(contracts["failure"]["const"], "reasoning-distiller-context-pack-failure/1")
        self.assertEqual(contracts["source_binding"]["const"], "reasoning-distiller-context-source-binding/1")
        self.assertEqual(contracts["eligibility"]["const"], "reasoning-distiller-context-profile-eligibility/1")
        self.assertEqual(contracts["receipt"]["const"], "reasoning-distiller-context-pack-receipt/1")
        self.assertEqual(self.v2["context-pack-request-v2.schema.json"]["properties"]["output"]["properties"]["pack_contract"]["const"], "reasoning-distiller-context-pack/2")

    def test_profile_v2_does_not_inherit_v1_eligibility_identity(self):
        profile = deepcopy(self.fixture["examples"]["profile"])
        profile["contract"] = "reasoning-distiller-context-profile/2"
        profile["profile_version"] = "2"
        profile["contracts"]["request"] = "reasoning-distiller-context-pack-request/2"
        profile["contracts"]["pack"] = "reasoning-distiller-context-pack/2"
        profile["contracts"]["result"] = "reasoning-distiller-context-pack-result/2"
        self.assertFalse(list(self.validators["context-profile-v2.schema.json"].iter_errors(profile)))
        legacy = deepcopy(profile)
        legacy["contract"] = "reasoning-distiller-context-profile/1"
        self.assertTrue(list(self.validators["context-profile-v2.schema.json"].iter_errors(legacy)))
        eligibility = self.fixture["examples"]["eligibility"]
        self.assertNotEqual((profile["profile_id"], profile["profile_version"]), (eligibility["profile"]["profile_id"], eligibility["profile"]["profile_version"]))

    def _pack(self):
        canonical = deepcopy(self.fixture["examples"]["canonical_source"])
        ref = canonical_snapshot_ref(canonical)
        h = "sha256:" + "a" * 64
        return {
            "contract": "reasoning-distiller-context-pack/2",
            "profile": {"profile_id": "context:engineer-task", "profile_version": "2", "raw_sha256": h},
            "request": {"request_id": "r2", "raw_sha256": h},
            "source_registry": [canonical],
            "control_plane": {"items": []},
            "knowledge_plane": {"items": [{"canonical_snapshot_ref": ref, "semantic": "pems/2", "serializer": "jcs/1", "pems": self.fixture["examples"]["minimal_pems"]}]},
            "operational_evidence_plane": {"items": []},
            "inclusion_ledger": [
                {"plane": "knowledge", "subject": {"source_ref": ref}, "causes": [{"kind": "request_selector", "cause_id": "snapshot"}]},
                {"plane": "knowledge", "subject": {"source_ref": ref, "pems_ref": {"namespace": "record", "id": "shared"}}, "causes": [{"kind": "request_selector", "cause_id": "record:root"}]},
                {"plane": "knowledge", "subject": {"source_ref": ref, "pems_ref": {"namespace": "relation", "id": "shared"}}, "causes": [{"kind": "pems_closure", "cause_id": "relation:edge"}]},
            ],
            "identity": {
                "profile_sha256": h, "request_sha256": h,
                "canonical_state_binding_sha256s": [h], "selected_pems_sha256": h,
                "manifest_sha256": h, "payload_set_sha256": h, "pack_identity_sha256": h,
            },
            "toolchain": {"components": [{"role": "pems_schema", "contract": "pems/2", "immutable_identity": "git-blob:cd7683d704e8aef2842a0c1b25b453fb1dbc8030", "raw_sha256": "sha256:b08e592ab7c10092ff381fe8057cac63ccb7aaa077b52532f5ee609c6fd279c3"}]},
        }

    def test_namespaced_same_string_subjects_and_snapshot_subject_validate(self):
        pack = self._pack()
        errors = list(self.validators["context-pack-v2.schema.json"].iter_errors(pack))
        self.assertFalse(errors, [e.message for e in errors])
        semantic = [e["subject"]["pems_ref"] for e in pack["inclusion_ledger"] if "pems_ref" in e["subject"]]
        self.assertEqual(semantic, [{"namespace": "record", "id": "shared"}, {"namespace": "relation", "id": "shared"}])

    def test_legacy_mixed_partial_and_unknown_pems_refs_fail_closed(self):
        base = self._pack()
        mutations = []
        legacy = deepcopy(base); legacy["inclusion_ledger"][1]["subject"] = {"source_ref": legacy["inclusion_ledger"][1]["subject"]["source_ref"], "semantic_id": "shared"}; mutations.append(legacy)
        mixed = deepcopy(base); mixed["inclusion_ledger"][1]["subject"]["semantic_id"] = "shared"; mutations.append(mixed)
        partial = deepcopy(base); partial["inclusion_ledger"][1]["subject"]["pems_ref"] = {"namespace": "record"}; mutations.append(partial)
        unknown = deepcopy(base); unknown["inclusion_ledger"][1]["subject"]["pems_ref"] = {"namespace": "other", "id": "shared"}; mutations.append(unknown)
        for value in mutations:
            self.assertTrue(list(self.validators["context-pack-v2.schema.json"].iter_errors(value)))

    def test_r4_alias_validates_pems_without_network_retrieval(self):
        pack = self._pack()
        pack["knowledge_plane"]["items"][0]["pems"] = {"semantic": "pems/2", "project_id": "p", "records": [], "relations": []}
        self.assertFalse(list(self.validators["context-pack-v2.schema.json"].iter_errors(pack)))
        pack["knowledge_plane"]["items"][0]["pems"]["semantic"] = "pems/1"
        self.assertTrue(list(self.validators["context-pack-v2.schema.json"].iter_errors(pack)))

    def test_result_v2_success_is_hard_bound_to_pack_v2(self):
        h = "sha256:" + "f" * 64
        good = {"contract": "reasoning-distiller-context-pack-result/2", "request_id": "r2", "status": "success", "pack": {"contract": "reasoning-distiller-context-pack/2", "pack_identity_sha256": h}}
        validator = self.validators["context-pack-result-v2.schema.json"]
        self.assertFalse(list(validator.iter_errors(good)))
        bad = deepcopy(good); bad["pack"]["contract"] = "reasoning-distiller-context-pack/1"
        self.assertTrue(list(validator.iter_errors(bad)))

    def test_reconciled_pressure_case_inventory(self):
        cases = {case["id"]: case for case in self.pressure["cases"]}
        self.assertEqual(set(cases), {f"SP-{i:02d}" for i in range(1, 15)})
        self.assertFalse(cases["SP-08"]["required_outcome"]["supported"])
        self.assertTrue(cases["SP-08"]["required_outcome"]["fresh_v2_rebuild_required"])
        self.assertFalse(cases["SP-09"]["required_outcome"]["namespace_guessing"])
        self.assertFalse(cases["SP-09"]["required_outcome"]["canonical_migration"])
        self.assertTrue(cases["SP-14"]["required_outcome"]["inherit_existing_frozen_cause_set_and_ordering"])
        self.assertFalse(cases["SP-14"]["required_outcome"]["introduce_new_dedup_rule"])


if __name__ == "__main__":
    unittest.main()
