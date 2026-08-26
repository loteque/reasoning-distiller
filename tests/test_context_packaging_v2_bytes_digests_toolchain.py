import copy
import json
import unittest
from pathlib import Path

from tests.support import context_packaging_p1c_reference as ref

R = Path(__file__).resolve().parents[1]
F = R / "tests/fixtures/context-packaging-v2-bytes-digests-toolchain.json"


def load(path):
    return json.loads(path.read_text())


class ContextPackagingV2BytesDigestsToolchain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load(F)
        sample = cls.fixture["sample"]
        cls.profile_raw = (R / sample["profile_source"]).read_bytes()
        cls.request_raw = (R / sample["request_source"]).read_bytes()
        cls.profile = ref.strict_json_object(cls.profile_raw)
        cls.request = ref.strict_json_object(cls.request_raw)

    def _pack(self):
        canonical = copy.deepcopy(self.request["source_bindings"][0])
        snapshot_ref = copy.deepcopy(self.request["knowledge_selection"]["snapshots"][0]["canonical_snapshot_ref"])
        pems = {
            "semantic": "pems/2",
            "project_id": "reasoning-distiller",
            "records": [{
                "id": "shared", "kind": "proposition", "lifecycle": "current",
                "data": {"statement": "record shared", "proposition_kind": "observation", "epistemic_role": "asserted"},
            }],
            "relations": [{
                "id": "shared", "kind": "references", "from": "shared", "to": "shared",
                "lifecycle": "current", "data": {},
            }],
        }
        return {
            "contract": "reasoning-distiller-context-pack/2",
            "profile": {
                "profile_id": self.profile["profile_id"],
                "profile_version": self.profile["profile_version"],
                "raw_sha256": self.fixture["sample"]["expected_profile_raw_sha256"],
            },
            "request": {
                "request_id": self.request["request_id"],
                "raw_sha256": self.fixture["sample"]["expected_request_raw_sha256"],
            },
            "source_registry": [canonical],
            "control_plane": {"items": []},
            "knowledge_plane": {"items": [{
                "canonical_snapshot_ref": snapshot_ref,
                "semantic": "pems/2",
                "serializer": "jcs/1",
                "pems": pems,
            }]},
            "operational_evidence_plane": {"items": []},
            "inclusion_ledger": [
                {"plane": "knowledge", "subject": {"source_ref": copy.deepcopy(snapshot_ref), "pems_ref": {"namespace": "relation", "id": "shared"}}, "causes": [{"kind": "pems_closure", "cause_id": "edge:shared"}]},
                {"plane": "knowledge", "subject": {"source_ref": copy.deepcopy(snapshot_ref)}, "causes": [{"kind": "request_selector", "cause_id": "snapshot:v2-vector"}]},
                {"plane": "knowledge", "subject": {"source_ref": copy.deepcopy(snapshot_ref), "pems_ref": {"namespace": "record", "id": "shared"}}, "causes": [{"kind": "request_selector", "cause_id": "record:shared"}]},
            ],
            "toolchain": {"components": [
                {"role": "pack_builder", "contract": "reasoning-distiller-context-pack-builder/2", "immutable_identity": "git-blob:f037625990497bd4eb491238367516a4c61b4e0c", "raw_sha256": "sha256:b99020add18a9ab64cb0e42c3450a02807cb5b080127fe0f9a49eac4588fc7ed"},
                {"role": "jcs_serializer", "contract": "jcs/1", "immutable_identity": "git-blob:04f64f873f7b9f7b62a2f4d24fb554e734b2af36", "raw_sha256": "sha256:c43c5f6b6b1894446364134344d7d8e446d6304140bc52c385bc9887b32a40f4"},
                {"role": "closure_descriptor", "contract": "reasoning-distiller-p1c-closure-descriptor-identity-fixture/1", "immutable_identity": "git-blob:804ff749cd543d7d634492cb90761175f445710b", "raw_sha256": "sha256:894763b9af93ded33b9e6ce605c72013ade39c2e6b2927fccfdbeb62eff86381"},
                {"role": "pems_validator", "contract": "reasoning-distiller-pems-v2-validator/1", "immutable_identity": "git-blob:d615bf2e95d3721b0ca312075cc0c39522f0a896", "raw_sha256": "sha256:50cb0d10168a47f7ff377b3194d9e086712cd38e22f6f868ddbab7e9538ac8d8"},
                {"role": "pems_schema", "contract": "pems/2", "immutable_identity": "git-blob:cd7683d704e8aef2842a0c1b25b453fb1dbc8030", "raw_sha256": "sha256:b08e592ab7c10092ff381fe8057cac63ccb7aaa077b52532f5ee609c6fd279c3"},
            ]},
        }

    def _build(self, pack):
        canonical, identity = ref.build_identity(
            self.profile_raw, self.profile,
            self.request_raw, self.request,
            pack,
        )
        output = copy.deepcopy(canonical)
        output["identity"] = identity
        serialized = ref.jcs_bytes(output)
        return canonical, identity, serialized

    def test_exact_successor_basis_blobs(self):
        for mapping_name in ("schema_basis", "shared_v1_basis"):
            for path, expected in self.fixture[mapping_name].items():
                self.assertEqual(ref.git_blob_sha((R / path).read_bytes()), expected, path)
        self.assertEqual(ref.git_blob_sha((R / "docs/design/CONTEXT_PACKAGING_V2_BUILDER_BEHAVIOR_CONTRACT.md").read_bytes()), self.fixture["contracts"]["pack_builder_behavior_blob"])
        self.assertEqual(ref.git_blob_sha((R / "docs/design/CONTEXT_PACKAGING_BYTES_DIGESTS_TOOLCHAIN_V2_CONTRACT.md").read_bytes()), self.fixture["contracts"]["bytes_digests_toolchain_blob"])
        self.assertEqual(ref.git_blob_sha((R / "schemas/resources/context-packaging-v2-resource-registry.json").read_bytes()), self.fixture["pems_resource"]["registry_blob"])

    def test_raw_document_bindings_and_exact_digest_vector(self):
        self.assertEqual(ref.raw_sha256(self.profile_raw), self.fixture["sample"]["expected_profile_raw_sha256"])
        self.assertEqual(ref.raw_sha256(self.request_raw), self.fixture["sample"]["expected_request_raw_sha256"])
        canonical, identity, serialized = self._build(self._pack())
        self.assertEqual(identity, self.fixture["sample"]["expected_identity"])
        self.assertEqual(ref.raw_sha256(serialized), self.fixture["sample"]["expected_serialized_pack_sha256"])
        kinds = []
        for entry in canonical["inclusion_ledger"]:
            pems_ref = entry["subject"].get("pems_ref")
            kinds.append(pems_ref["namespace"] if pems_ref else "snapshot")
        self.assertEqual(kinds, self.fixture["sample"]["expected_canonical_ledger_subject_kinds"])

    def test_host_iteration_variation_is_byte_identical(self):
        first = self._pack()
        second = copy.deepcopy(first)
        second["inclusion_ledger"].reverse()
        second["toolchain"]["components"].reverse()
        _, identity_a, bytes_a = self._build(first)
        _, identity_b, bytes_b = self._build(second)
        self.assertEqual(identity_a, identity_b)
        self.assertEqual(bytes_a, bytes_b)

    def test_identity_preimage_v1_reuse_is_explicitly_bounded(self):
        self.assertEqual(self.fixture["contracts"]["identity_preimage"], "reasoning-distiller-context-pack-identity-preimage/1")
        self.assertEqual(self.fixture["identity_preimage_reuse_requires"], [
            "member_set_unchanged",
            "member_meanings_unchanged",
            "canonical_serialization_and_framing_unchanged",
            "hash_algorithm_and_framing_unchanged",
            "domain_semantics_unchanged",
        ])
        self.assertFalse(self.fixture["digest_expectations"]["new_domain_for_pems_ref"])

    def test_builder_behavior_is_v2_without_claiming_p5_implementation(self):
        self.assertEqual(self.fixture["contracts"]["pack_builder"], "reasoning-distiller-context-pack-builder/2")
        behavior = (R / "docs/design/CONTEXT_PACKAGING_V2_BUILDER_BEHAVIOR_CONTRACT.md").read_text()
        self.assertIn("does not claim that `context_packaging/pack_builder.py` implements `/2`", behavior)
        self.assertIn("There is no canonical public `/1` to `/2` adapter", behavior)


if __name__ == "__main__":
    unittest.main()
