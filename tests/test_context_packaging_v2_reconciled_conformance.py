import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from tests import test_context_packaging_protocol_schemas_v2 as schema_mod
from tests import test_context_packaging_v2_bytes_digests_toolchain as bytes_mod
from tests.support import context_packaging_p1c_reference as ref

R = Path(__file__).resolve().parents[1]

PROFILE_1 = "reasoning-distiller-context-profile/1"
REQUEST_1 = "reasoning-distiller-context-pack-request/1"
PACK_1 = "reasoning-distiller-context-pack/1"
RESULT_1 = "reasoning-distiller-context-pack-result/1"
PROFILE_2 = "reasoning-distiller-context-profile/2"
REQUEST_2 = "reasoning-distiller-context-pack-request/2"
PACK_2 = "reasoning-distiller-context-pack/2"
RESULT_2 = "reasoning-distiller-context-pack-result/2"


def _raw_json(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _dispatch_accepts(profile_contract, request_contract, requested_pack, success_pack):
    families = {
        PROFILE_1: (REQUEST_1, PACK_1),
        PROFILE_2: (REQUEST_2, PACK_2),
    }
    expected = families.get(profile_contract)
    if expected is None:
        return False
    expected_request, expected_pack = expected
    return (
        request_contract == expected_request
        and requested_pack == expected_pack
        and success_pack == expected_pack
    )


def _eligibility_binds_exact_profile(profile, profile_raw, eligibility):
    identity = eligibility["profile"]
    return (
        identity["profile_id"] == profile["profile_id"]
        and identity["profile_version"] == profile["profile_version"]
        and ref.normalize_sha256(identity["raw_sha256"])
        == ref.raw_sha256(profile_raw)
    )


class ContextPackagingV2ReconciledConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema_mod.ContextPackagingV2Schemas.setUpClass()
        bytes_mod.ContextPackagingV2BytesDigestsToolchain.setUpClass()
        cls.schema_case = schema_mod.ContextPackagingV2Schemas(
            "test_reconciled_pressure_case_inventory"
        )
        cls.bytes_case = bytes_mod.ContextPackagingV2BytesDigestsToolchain(
            "test_exact_successor_basis_blobs"
        )
        cls.pack_validator = cls.schema_case.validators["context-pack-v2.schema.json"]

    def test_sp02_sp03_and_sp14_preserve_causes_under_frozen_ordering(self):
        pack = self.schema_case._pack()
        target = next(
            entry
            for entry in pack["inclusion_ledger"]
            if entry["subject"].get("pems_ref") == {"namespace": "record", "id": "shared"}
        )
        target["causes"] = [
            {"kind": "pems_closure", "cause_id": "edge:shared"},
            {"kind": "request_selector", "cause_id": "root:shared"},
        ]
        self.assertFalse(list(self.pack_validator.iter_errors(pack)))
        canonical = ref.canonicalize_pack(pack)
        entry = next(
            item
            for item in canonical["inclusion_ledger"]
            if item["subject"].get("pems_ref") == {"namespace": "record", "id": "shared"}
        )
        self.assertEqual(
            entry["causes"],
            [
                {"kind": "request_selector", "cause_id": "root:shared"},
                {"kind": "pems_closure", "cause_id": "edge:shared"},
            ],
        )

        duplicate = copy.deepcopy(pack)
        target = next(
            item
            for item in duplicate["inclusion_ledger"]
            if item["subject"].get("pems_ref") == {"namespace": "record", "id": "shared"}
        )
        target["causes"] = [
            {"kind": "request_selector", "cause_id": "root:shared"},
            {"kind": "request_selector", "cause_id": "root:shared"},
            {"kind": "pems_closure", "cause_id": "edge:shared"},
        ]
        canonical = ref.canonicalize_pack(duplicate)
        entry = next(
            item
            for item in canonical["inclusion_ledger"]
            if item["subject"].get("pems_ref") == {"namespace": "record", "id": "shared"}
        )
        self.assertEqual(len(entry["causes"]), 3)
        self.assertEqual(entry["causes"][0], entry["causes"][1])

    def test_sp04_source_ref_is_part_of_namespaced_subject_identity(self):
        pack = self.schema_case._pack()
        first = copy.deepcopy(self.schema_case.fixture["examples"]["canonical_source"])
        second = copy.deepcopy(self.schema_case.fixture["examples"]["canonical_source_second"])
        first_ref = schema_mod.canonical_snapshot_ref(first)
        second_ref = schema_mod.canonical_snapshot_ref(second)
        minimal = copy.deepcopy(self.schema_case.fixture["examples"]["minimal_pems"])
        pack["source_registry"] = [first, second]
        pack["knowledge_plane"]["items"] = [
            {
                "canonical_snapshot_ref": first_ref,
                "semantic": "pems/2",
                "serializer": "jcs/1",
                "pems": copy.deepcopy(minimal),
            },
            {
                "canonical_snapshot_ref": second_ref,
                "semantic": "pems/2",
                "serializer": "jcs/1",
                "pems": copy.deepcopy(minimal),
            },
        ]
        pack["inclusion_ledger"] = [
            {
                "plane": "knowledge",
                "subject": {
                    "source_ref": first_ref,
                    "pems_ref": {"namespace": "record", "id": "same"},
                },
                "causes": [{"kind": "request_selector", "cause_id": "root:first"}],
            },
            {
                "plane": "knowledge",
                "subject": {
                    "source_ref": second_ref,
                    "pems_ref": {"namespace": "record", "id": "same"},
                },
                "causes": [{"kind": "request_selector", "cause_id": "root:second"}],
            },
        ]
        self.assertFalse(list(self.pack_validator.iter_errors(pack)))
        subjects = [entry["subject"] for entry in pack["inclusion_ledger"]]
        self.assertNotEqual(ref.jcs_bytes(subjects[0]), ref.jcs_bytes(subjects[1]))

    def test_sp05_opaque_ids_are_preserved_without_tag_or_delimiter_parsing(self):
        opaque_ids = [":", "/", "#", '{"json":true}', "record:shared", "relation:shared"]
        for opaque_id in opaque_ids:
            with self.subTest(opaque_id=opaque_id):
                pack = self.schema_case._pack()
                target = next(
                    entry
                    for entry in pack["inclusion_ledger"]
                    if entry["subject"].get("pems_ref", {}).get("namespace") == "record"
                )
                target["subject"]["pems_ref"]["id"] = opaque_id
                self.assertFalse(list(self.pack_validator.iter_errors(pack)))
                canonical = ref.canonicalize_pack(pack)
                found = next(
                    entry["subject"]["pems_ref"]["id"]
                    for entry in canonical["inclusion_ledger"]
                    if entry["subject"].get("pems_ref", {}).get("namespace") == "record"
                )
                self.assertEqual(found, opaque_id)

    def test_sp10_full_contract_dispatch_matrix_fails_closed(self):
        rows = [
            (PROFILE_1, REQUEST_1, PACK_1, PACK_1, True),
            (PROFILE_2, REQUEST_2, PACK_2, PACK_2, True),
            (PROFILE_1, REQUEST_2, PACK_1, PACK_1, False),
            (PROFILE_2, REQUEST_1, PACK_2, PACK_2, False),
            (PROFILE_2, REQUEST_2, PACK_1, PACK_1, False),
            (PROFILE_1, REQUEST_1, PACK_2, PACK_2, False),
            (PROFILE_2, REQUEST_2, PACK_2, PACK_1, False),
            (PROFILE_1, REQUEST_1, PACK_1, PACK_2, False),
        ]
        for profile, request, requested, success, expected in rows:
            with self.subTest(
                profile=profile,
                request=request,
                requested=requested,
                success=success,
            ):
                self.assertEqual(
                    _dispatch_accepts(profile, request, requested, success),
                    expected,
                )

        profile_contracts = self.schema_case.v2["context-profile-v2.schema.json"]["properties"]["contracts"]["properties"]
        self.assertEqual(profile_contracts["request"]["const"], REQUEST_2)
        self.assertEqual(profile_contracts["pack"]["const"], PACK_2)
        self.assertEqual(profile_contracts["result"]["const"], RESULT_2)
        request_output = self.schema_case.v2["context-pack-request-v2.schema.json"]["properties"]["output"]["properties"]
        self.assertEqual(request_output["pack_contract"]["const"], PACK_2)

    def test_v2_eligibility_is_exact_and_v1_decision_does_not_transfer(self):
        profile = copy.deepcopy(self.bytes_case.profile)
        profile_raw = self.bytes_case.profile_raw
        eligibility_schema = self.schema_case.shared["context-profile-eligibility.schema.json"]
        validator = Draft202012Validator(
            eligibility_schema,
            registry=self.schema_case.registry,
        )

        exact = copy.deepcopy(self.schema_case.fixture["examples"]["eligibility"])
        exact["profile"] = {
            "profile_id": profile["profile_id"],
            "profile_version": profile["profile_version"],
            "raw_sha256": ref.raw_sha256(profile_raw),
        }
        self.assertFalse(list(validator.iter_errors(exact)))
        self.assertTrue(_eligibility_binds_exact_profile(profile, profile_raw, exact))

        inherited_v1 = copy.deepcopy(self.schema_case.fixture["examples"]["eligibility"])
        self.assertFalse(list(validator.iter_errors(inherited_v1)))
        self.assertFalse(
            _eligibility_binds_exact_profile(profile, profile_raw, inherited_v1)
        )

    def test_sp11_digest_stability_and_versioned_preimage_churn(self):
        base_pack = self.bytes_case._pack()
        _, base_identity, base_bytes = self.bytes_case._build(base_pack)

        changed_profile = copy.deepcopy(self.bytes_case.profile)
        changed_profile["profile_version"] = "2.1"
        changed_profile_raw = _raw_json(changed_profile)
        changed_profile_raw_sha = ref.raw_sha256(changed_profile_raw)

        changed_request = copy.deepcopy(self.bytes_case.request)
        changed_request["profile"]["profile_version"] = "2.1"
        changed_request["profile"]["raw_sha256"] = changed_profile_raw_sha
        changed_request_raw = _raw_json(changed_request)
        changed_request_raw_sha = ref.raw_sha256(changed_request_raw)

        changed_pack = copy.deepcopy(base_pack)
        changed_pack["profile"]["profile_version"] = "2.1"
        changed_pack["profile"]["raw_sha256"] = changed_profile_raw_sha
        changed_pack["request"]["raw_sha256"] = changed_request_raw_sha

        canonical, changed_identity = ref.build_identity(
            changed_profile_raw,
            changed_profile,
            changed_request_raw,
            changed_request,
            changed_pack,
        )
        changed_output = copy.deepcopy(canonical)
        changed_output["identity"] = changed_identity
        changed_bytes = ref.jcs_bytes(changed_output)

        for field in (
            "canonical_state_binding_sha256s",
            "selected_pems_sha256",
            "payload_set_sha256",
        ):
            self.assertEqual(base_identity[field], changed_identity[field], field)

        for field in (
            "profile_sha256",
            "request_sha256",
            "manifest_sha256",
            "pack_identity_sha256",
        ):
            self.assertNotEqual(base_identity[field], changed_identity[field], field)
        self.assertNotEqual(ref.raw_sha256(base_bytes), ref.raw_sha256(changed_bytes))

    def test_canonical_v2_knowledge_subjects_never_emit_semantic_id(self):
        canonical = ref.canonicalize_pack(self.schema_case._pack())
        subjects = [
            entry["subject"]
            for entry in canonical["inclusion_ledger"]
            if entry["plane"] == "knowledge"
        ]
        self.assertTrue(subjects)
        for subject in subjects:
            self.assertNotIn("semantic_id", subject)
            self.assertEqual(
                set(subject),
                {"source_ref"} if "pems_ref" not in subject else {"source_ref", "pems_ref"},
            )

    def test_p5_runtime_implementation_is_unchanged_by_amendment(self):
        expected = "b0e806e966598e6d819b6d52c643efa23cdb6ef9"
        self.assertEqual(
            ref.git_blob_sha((R / "context_packaging/pack_builder.py").read_bytes()),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
