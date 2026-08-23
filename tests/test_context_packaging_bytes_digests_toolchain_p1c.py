import base64
import copy
import json
import struct
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "tests/support"
sys.path.insert(0, str(SUPPORT))

from context_packaging_p1c_reference import (  # noqa: E402
    JCSError,
    b64decode,
    b64encode,
    build_identity,
    canonicalize_pack,
    domain_sha256,
    digest_preimage,
    git_blob_sha,
    jcs_bytes,
    raw_sha256,
    validate_toolchain,
)

FIXTURE = ROOT / "tests/fixtures/context-packaging-bytes-digests-toolchain-p1c.json"

def snapshot_ref(binding, keys):
    return {key: copy.deepcopy(binding[key]) for key in keys if key in binding}

def materialize_pack(profile, request, toolchain_components, request_raw_sha):
    repo = next(x for x in request["source_bindings"] if x["source_class"] == "repository_control")
    canonical = next(x for x in request["source_bindings"] if x["source_class"] == "canonical_state")
    operational = next(x for x in request["source_bindings"] if x["source_class"] == "operational_evidence")
    control_ref = snapshot_ref(repo, ("source_class", "logical_namespace", "logical_source_id", "repository", "commit", "path", "raw_sha256"))
    canonical_ref = copy.deepcopy(request["knowledge_selection"]["snapshots"][0]["canonical_snapshot_ref"])
    operational_ref = snapshot_ref(operational, ("source_class", "logical_namespace", "logical_source_id", "artifact_contract", "immutable_snapshot_id", "raw_sha256", "validation_status", "validation_result"))
    components = copy.deepcopy(toolchain_components)
    return {
        "contract": "reasoning-distiller-context-pack/1",
        "profile": {"profile_id": profile["profile_id"], "profile_version": profile["profile_version"], "raw_sha256": request["profile"]["raw_sha256"]},
        "request": {"request_id": request["request_id"], "raw_sha256": request_raw_sha},
        "source_registry": copy.deepcopy(request["source_bindings"]),
        "control_plane": {"items": [{"source_ref": control_ref, "payload": {"encoding": "base64", "data": b64encode(b"a\r\n"), "raw_sha256": raw_sha256(b"a\r\n")}}]},
        "knowledge_plane": {"items": [{"canonical_snapshot_ref": canonical_ref, "semantic": "pems/2", "serializer": "jcs/1", "pems": {"semantic": "pems/2", "project_id": "p", "records": [], "relations": []}}]},
        "operational_evidence_plane": {"items": [{"source_ref": operational_ref, "validation_status": operational["validation_status"], "payload": {"encoding": "base64", "data": b64encode(b"\x00b\xff"), "raw_sha256": raw_sha256(b"\x00b\xff")}}]},
        "inclusion_ledger": [
            {"plane": "control", "subject": {"source_ref": control_ref}, "causes": [{"kind": "profile_slot", "cause_id": "c"}]},
            {"plane": "knowledge", "subject": {"source_ref": canonical_ref}, "causes": [{"kind": "request_selector", "cause_id": canonical_ref["immutable_snapshot_id"]}]},
            {"plane": "operational_evidence", "subject": {"source_ref": operational_ref}, "causes": [{"kind": "profile_slot", "cause_id": "o"}]},
        ],
        "toolchain": {"components": components},
    }


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def validators():
    names = [
        "context-profile.schema.json",
        "context-pack-request.schema.json",
        "context-source-binding.schema.json",
        "context-profile-eligibility.schema.json",
    ]
    schemas = {name: load(ROOT / "schemas" / name) for name in names}
    registry = Registry().with_resources(
        [(schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()]
    )
    return {
        name: Draft202012Validator(schema, registry=registry)
        for name, schema in schemas.items()
    }

class P1c(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = load(FIXTURE)
        cls.sample = cls.fx["sample"]
        cls.validators = validators()
        cls.profile_raw = (ROOT / cls.sample["profile_source_path"]).read_bytes()
        cls.request_raw = (ROOT / cls.sample["request_source_path"]).read_bytes()
        cls.profile = json.loads(cls.profile_raw.decode("utf-8"))
        cls.request = json.loads(cls.request_raw.decode("utf-8"))
        cls.pack = materialize_pack(cls.profile, cls.request, cls.fx["toolchain_components"], raw_sha256(cls.request_raw))

    def build(self, pack=None, profile=None, request=None, profile_raw=None, request_raw=None):
        return build_identity(
            self.profile_raw if profile_raw is None else profile_raw,
            self.profile if profile is None else profile,
            self.request_raw if request_raw is None else request_raw,
            self.request if request is None else request,
            self.pack if pack is None else pack,
        )

    def test_scope_and_p1b_basis(self):
        self.assertEqual(self.fx["gate"], "P1c")
        self.assertEqual(self.fx["scope"]["authorized"], "P1C_BYTES_DIGESTS_TOOLCHAIN_ONLY")
        self.assertFalse(self.fx["scope"]["p1b_schema_semantics_changed"])
        self.assertFalse(self.fx["scope"]["resolver_implemented"])
        self.assertFalse(self.fx["scope"]["later_gates_implemented"])
        self.assertEqual(self.fx["remediation"]["basis_candidate"], "356e926f6214a7ee13d55f7d6510af13fbfd69ef")
        self.assertEqual(self.fx["remediation"]["scope"], "FOUR_REVIEW_FINDINGS_ONLY")
        self.assertEqual(len(self.fx["remediation"]["findings"]), 4)
        for rel, expected in self.fx["p1b_basis"]["schema_blobs"].items():
            self.assertEqual(git_blob_sha((ROOT / rel).read_bytes()), expected, rel)

    def test_p1b_identity_shape_is_not_reinterpreted(self):
        schema = load(ROOT / "schemas/context-pack.schema.json")
        req = schema["$defs"]["packIdentity"]["required"]
        self.assertEqual(req, [
            "profile_sha256", "request_sha256", "canonical_state_binding_sha256s",
            "selected_pems_sha256", "manifest_sha256", "payload_set_sha256",
            "pack_identity_sha256",
        ])
        roles = schema["$defs"]["toolchainComponent"]["properties"]["role"]["enum"]
        self.assertEqual(roles, [
            "pems_schema", "pems_validator", "closure_descriptor", "cove_adapter",
            "jcs_serializer", "pack_builder",
        ])

    def test_raw_profile_request_bytes_are_the_validated_objects(self):
        profile = json.loads(self.profile_raw.decode("utf-8"))
        request = json.loads(self.request_raw.decode("utf-8"))
        self.assertEqual(profile, self.profile)
        self.assertEqual(request, self.request)
        self.assertFalse(list(self.validators["context-profile.schema.json"].iter_errors(profile)))
        self.assertFalse(list(self.validators["context-pack-request.schema.json"].iter_errors(request)))
        self.assertEqual(raw_sha256(self.profile_raw), self.sample["profile_raw_sha256"])
        self.assertEqual(raw_sha256(self.request_raw), self.sample["request_raw_sha256"])
        self.assertEqual(self.pack["profile"]["raw_sha256"], self.sample["profile_raw_sha256"])
        self.assertEqual(self.pack["request"]["raw_sha256"], self.sample["request_raw_sha256"])
        self.assertEqual(request["profile"]["raw_sha256"], self.sample["profile_raw_sha256"])

    def test_raw_object_mismatch_fails_before_identity(self):
        bad_profile_raw = self.profile_raw.replace(b'"profile_id": "p1"', b'"profile_id": "other"', 1)
        with self.assertRaisesRegex(ValueError, "profile raw bytes"):
            self.build(profile_raw=bad_profile_raw)
        bad_request_raw = self.request_raw.replace(b'"request_id": "r1"', b'"request_id": "other"', 1)
        with self.assertRaisesRegex(ValueError, "request raw bytes"):
            self.build(request_raw=bad_request_raw)

    def test_base64(self):
        for vector in self.fx["base64_vectors"]:
            raw = base64.b64decode(vector["raw_b64"], validate=True)
            self.assertEqual(b64encode(raw), vector["b64"])
            self.assertEqual(b64decode(vector["b64"]), raw)
        for text in self.fx["base64_reject"]:
            with self.assertRaises(ValueError):
                b64decode(text)

    def test_raw_bytes_distinguish_newlines(self):
        self.assertNotEqual(raw_sha256(b"line\n"), raw_sha256(b"line\r\n"))
        self.assertNotEqual(b64encode(b"line\n"), b64encode(b"line\r\n"))

    def test_rfc8785_vectors(self):
        for vector in self.fx["jcs_vectors"]:
            self.assertEqual(jcs_bytes(vector["value"]).decode("utf-8"), vector["expected"])
        for vector in self.fx["jcs_ieee754_vectors"]:
            value = struct.unpack(">d", bytes.fromhex(vector["ieee754"]))[0]
            self.assertEqual(jcs_bytes(value).decode("ascii"), vector["expected"], vector["ieee754"])

    def test_rfc8785_rejects_nonfinite_and_lone_surrogate(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(JCSError):
                jcs_bytes(value)
        with self.assertRaises(JCSError):
            jcs_bytes("\ud800")

    def test_domain_vectors(self):
        seen = set()
        for vector in self.fx["domain_vectors"]:
            body = base64.b64decode(vector["body_b64"], validate=True)
            preimage = digest_preimage(vector["domain"], body)
            self.assertEqual(preimage.hex(), vector["expected_preimage_hex"])
            digest = raw_sha256(preimage)
            self.assertEqual(digest, vector["expected_sha256"])
            seen.add(digest)
        self.assertEqual(len(seen), len(self.fx["domain_vectors"]))

    def test_raw_and_canonical_profile_request_identities(self):
        pack, ident = self.build()
        for name, domain, raw in (
            ("profile", "context-profile", self.profile_raw),
            ("request", "context-pack-request", self.request_raw),
        ):
            self.assertEqual(raw_sha256(raw), self.sample[name + "_raw_sha256"])
            canonical = domain_sha256(domain, self.profile if name == "profile" else self.request)
            self.assertEqual(canonical, self.sample["expected_identity"][name + "_sha256"])
            self.assertNotEqual(canonical, self.sample[name + "_raw_sha256"])
        self.assertEqual(ident, self.sample["expected_identity"])
        self.assertTrue(validate_toolchain(self.profile, pack))

    def test_toolchain_components_bind_exact_behavior_artifacts(self):
        components = {
            component["role"]: component
            for component in self.pack["toolchain"]["components"]
        }
        self.assertEqual(set(components), set(self.fx["toolchain_artifacts"]))
        for role, rel in self.fx["toolchain_artifacts"].items():
            data = (ROOT / rel).read_bytes()
            component = components[role]
            self.assertEqual(component["immutable_identity"], "git-blob:" + git_blob_sha(data), role)
            self.assertEqual(component["raw_sha256"], raw_sha256(data), role)
        self.assertNotEqual(components["pems_schema"]["immutable_identity"], "ps")
        self.assertNotEqual(components["pems_validator"]["immutable_identity"], "pv")
        self.assertNotEqual(components["jcs_serializer"]["immutable_identity"], "jcs")
        self.assertNotEqual(components["pack_builder"]["immutable_identity"], "pb")

    def test_frozen_pack_vector(self):
        pack, ident = self.build()
        self.assertTrue(validate_toolchain(self.profile, pack))
        self.assertEqual(ident, self.sample["expected_identity"])
        final = copy.deepcopy(pack)
        final["identity"] = ident
        serialized_sha = raw_sha256(jcs_bytes(final))
        self.assertEqual(serialized_sha, self.sample["expected_serialized_pack_sha256"])
        self.assertEqual(self.sample["expected_receipt"]["pack_identity_sha256"], ident["pack_identity_sha256"])
        self.assertEqual(self.sample["expected_receipt"]["serialized_pack_sha256"], serialized_sha)
        self.assertNotIn("receipt", final)

    def test_pack_identity_preimage_is_non_circular(self):
        _, ident = self.build()
        preimage = {
            "contract": "reasoning-distiller-context-pack-identity-preimage/1",
            **{k: v for k, v in ident.items() if k != "pack_identity_sha256"},
        }
        self.assertNotIn("pack_identity_sha256", preimage)
        self.assertEqual(domain_sha256("context-pack-identity", preimage), ident["pack_identity_sha256"])

    def test_array_order_is_canonical(self):
        a = copy.deepcopy(self.pack)
        b = copy.deepcopy(a)
        b["source_registry"].reverse()
        b["inclusion_ledger"].reverse()
        b["toolchain"]["components"].reverse()
        ca, ia = self.build(pack=a)
        cb, ib = self.build(pack=b)
        self.assertEqual(jcs_bytes(ca), jcs_bytes(cb))
        self.assertEqual(ia, ib)

    def test_standing_evidence_normalizes_p1a_hex_before_set_canonicalization(self):
        baseline_pack, baseline_identity = self.build()
        mutated = copy.deepcopy(self.pack)
        canonical = next(x for x in mutated["source_registry"] if x["source_class"] == "canonical_state")
        evidence = copy.deepcopy(canonical["standing_evidence"][0])
        upper = copy.deepcopy(evidence)
        upper["raw_sha256"] = "sha256:" + upper["raw_sha256"][7:].upper()
        canonical["standing_evidence"] = [upper, evidence]
        item_ref = mutated["knowledge_plane"]["items"][0]["canonical_snapshot_ref"]
        item_ref["standing_evidence"] = [copy.deepcopy(upper), copy.deepcopy(evidence)]
        ledger_ref = next(x for x in mutated["inclusion_ledger"] if x["plane"] == "knowledge")["subject"]["source_ref"]
        ledger_ref["standing_evidence"] = [copy.deepcopy(upper), copy.deepcopy(evidence)]

        canonical_pack, identity = self.build(pack=mutated)
        self.assertEqual(identity, baseline_identity)
        self.assertEqual(jcs_bytes(canonical_pack), jcs_bytes(baseline_pack))
        normalized = next(x for x in canonical_pack["source_registry"] if x["source_class"] == "canonical_state")["standing_evidence"]
        self.assertEqual(normalized, [evidence])

    def test_payload_and_manifest_domains_are_separate(self):
        pack = copy.deepcopy(self.pack)
        _, before = self.build(pack=pack)
        pack["control_plane"]["items"][0]["payload"]["data"] = b64encode(b"other")
        _, after = self.build(pack=pack)
        self.assertEqual(before["manifest_sha256"], after["manifest_sha256"])
        self.assertNotEqual(before["payload_set_sha256"], after["payload_set_sha256"])
        self.assertNotEqual(before["pack_identity_sha256"], after["pack_identity_sha256"])

    def test_toolchain_change_is_visible(self):
        pack = copy.deepcopy(self.pack)
        _, before = self.build(pack=pack)
        for component in pack["toolchain"]["components"]:
            if component["role"] == "pems_validator":
                component["immutable_identity"] = "git-blob:" + "0" * 40
                component["raw_sha256"] = "sha256:" + "0" * 64
        _, after = self.build(pack=pack)
        self.assertEqual(before["payload_set_sha256"], after["payload_set_sha256"])
        self.assertNotEqual(before["manifest_sha256"], after["manifest_sha256"])
        self.assertNotEqual(before["pack_identity_sha256"], after["pack_identity_sha256"])

    def test_toolchain_exact_roles_and_cove_requirement(self):
        pack = copy.deepcopy(self.pack)
        self.assertTrue(validate_toolchain(self.profile, pack))
        pack["toolchain"]["components"].append(copy.deepcopy(pack["toolchain"]["components"][0]))
        self.assertFalse(validate_toolchain(self.profile, pack))

        pack = copy.deepcopy(self.pack)
        pack["knowledge_plane"]["items"][0]["cove_payload"] = {
            "cove_semantic": "cove/1",
            "pems_semantic": "pems/2",
            "serializer": "jcs/1",
            "encoding": "base64",
            "data": b64encode(b"cove"),
            "raw_sha256": raw_sha256(b"cove"),
        }
        self.assertFalse(validate_toolchain(self.profile, pack))

if __name__ == "__main__":
    unittest.main()
