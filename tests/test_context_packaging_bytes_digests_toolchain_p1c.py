import base64
import copy
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/context-packaging-bytes-digests-toolchain-p1c.json"
MAGIC = b"reasoning-distiller-context-digest/1\x00"

SOURCE_CLASS_RANK = {"repository_control":0,"package_control":1,"canonical_state":2,"operational_evidence":3}
PLANE_RANK = {"control":0,"knowledge":1,"operational_evidence":2}
CAUSE_RANK = {"profile_slot":0,"request_selector":1,"pems_closure":2}
TOOLCHAIN_RANK = {"pems_schema":0,"pems_validator":1,"closure_descriptor":2,"cove_adapter":3,"jcs_serializer":4,"pack_builder":5}

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def raw_sha256(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()

def git_blob_sha(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()

def jcs_bytes(value):
    # Fixture values avoid floating point; the normative contract is RFC 8785.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",",":"), allow_nan=False).encode("utf-8")

def digest_preimage(domain, body):
    d = domain.encode("ascii")
    if len(d) > 0xffff:
        raise ValueError("domain too long")
    return MAGIC + len(d).to_bytes(2,"big") + d + len(body).to_bytes(8,"big") + body

def domain_sha256(domain, value):
    body = value if isinstance(value, bytes) else jcs_bytes(value)
    return raw_sha256(digest_preimage(domain, body))

def b64encode(data):
    return base64.b64encode(data).decode("ascii")

def b64decode(text):
    if not isinstance(text, str) or any(ord(c) > 127 for c in text):
        raise ValueError("base64 must be ASCII")
    try:
        raw = base64.b64decode(text, validate=True)
    except Exception as exc:
        raise ValueError("invalid base64") from exc
    if b64encode(raw) != text:
        raise ValueError("non-canonical base64")
    return raw

def canonical_binding(binding):
    out = copy.deepcopy(binding)
    if "standing_evidence" in out:
        unique = {jcs_bytes(v):v for v in out["standing_evidence"]}
        out["standing_evidence"] = [unique[k] for k in sorted(unique)]
    return out

def canonicalize_pack(pack):
    out = copy.deepcopy(pack)
    for b in out["source_registry"]:
        if b.get("source_class") == "canonical_state":
            b.update(canonical_binding(b))
    out["source_registry"].sort(key=lambda b:(SOURCE_CLASS_RANK[b["source_class"]], jcs_bytes(b)))
    out["control_plane"]["items"].sort(key=lambda x:jcs_bytes(x["source_ref"]))
    out["knowledge_plane"]["items"].sort(key=lambda x:jcs_bytes(x["canonical_snapshot_ref"]))
    out["operational_evidence_plane"]["items"].sort(key=lambda x:jcs_bytes(x["source_ref"]))
    for e in out["inclusion_ledger"]:
        e["causes"].sort(key=lambda c:(CAUSE_RANK[c["kind"]], c["cause_id"].encode("utf-8")))
    out["inclusion_ledger"].sort(key=lambda e:(PLANE_RANK[e["plane"]], jcs_bytes(e["subject"])))
    out["toolchain"]["components"].sort(key=lambda c:(TOOLCHAIN_RANK[c["role"]], jcs_bytes(c)))
    return out

def canonical_snapshot_ref(binding):
    keys = (
        "source_class","logical_namespace","logical_source_id","project_id","backend_type",
        "backend_contract","backend_config_identity","immutable_snapshot_id","pems_semantic",
        "serializer","pems_sha256","standing_evidence","cove"
    )
    return canonical_binding({k:binding[k] for k in keys if k in binding})

def canonical_binding_digests(pack):
    by_ref = {}
    for b in pack["source_registry"]:
        if b["source_class"] == "canonical_state":
            by_ref[jcs_bytes(canonical_snapshot_ref(b))] = domain_sha256("canonical-state-binding", canonical_binding(b))
    result = []
    for item in pack["knowledge_plane"]["items"]:
        key = jcs_bytes(canonical_binding(item["canonical_snapshot_ref"]))
        if key not in by_ref:
            raise ValueError("knowledge item has no exact canonical binding")
        result.append(by_ref[key])
    return result

def selected_pems_view(pack):
    return {"contract":"reasoning-distiller-selected-pems-projection/1","items":[
        {"canonical_snapshot_ref":x["canonical_snapshot_ref"],"semantic":x["semantic"],"serializer":x["serializer"],"pems":x["pems"]}
        for x in pack["knowledge_plane"]["items"]
    ]}

def cove_view(pack):
    return {"contract":"reasoning-distiller-cove-payload-set/1","items":[
        {"canonical_snapshot_ref":x["canonical_snapshot_ref"],"cove_payload":x["cove_payload"]}
        for x in pack["knowledge_plane"]["items"] if "cove_payload" in x
    ]}

def manifest_view(pack):
    out = copy.deepcopy(pack)
    out.pop("identity", None)
    for x in out["control_plane"]["items"]:
        x["payload"].pop("data", None)
    for x in out["knowledge_plane"]["items"]:
        x.pop("pems", None)
        if "cove_payload" in x:
            x["cove_payload"].pop("data", None)
    for x in out["operational_evidence_plane"]["items"]:
        x["payload"].pop("data", None)
    return out

def payload_view(pack):
    return {
        "contract":"reasoning-distiller-context-pack-payload-set/1",
        "control":[{"source_ref":x["source_ref"],"payload":x["payload"]} for x in pack["control_plane"]["items"]],
        "knowledge":[{"canonical_snapshot_ref":x["canonical_snapshot_ref"],"pems":x["pems"],**({"cove_payload":x["cove_payload"]} if "cove_payload" in x else {})} for x in pack["knowledge_plane"]["items"]],
        "operational_evidence":[{"source_ref":x["source_ref"],"payload":x["payload"]} for x in pack["operational_evidence_plane"]["items"]],
    }

def build_identity(profile, request, pack):
    pack = canonicalize_pack(pack)
    ident = {
        "profile_sha256":domain_sha256("context-profile", profile),
        "request_sha256":domain_sha256("context-pack-request", request),
        "canonical_state_binding_sha256s":canonical_binding_digests(pack),
        "selected_pems_sha256":domain_sha256("selected-pems-projection", selected_pems_view(pack)),
    }
    cv = cove_view(pack)
    if cv["items"]:
        ident["cove_payload_sha256"] = domain_sha256("cove-payload-set", cv)
    ident["manifest_sha256"] = domain_sha256("context-pack-manifest", manifest_view(pack))
    ident["payload_set_sha256"] = domain_sha256("context-pack-payload-set", payload_view(pack))
    pre = {"contract":"reasoning-distiller-context-pack-identity-preimage/1", **ident}
    ident["pack_identity_sha256"] = domain_sha256("context-pack-identity", pre)
    return pack, ident

def validate_toolchain(profile, pack):
    comps = pack["toolchain"]["components"]
    roles = [c["role"] for c in comps]
    if len(roles) != len(set(roles)):
        return False
    required = {"pems_schema","pems_validator","closure_descriptor","jcs_serializer","pack_builder"}
    if any("cove_payload" in x for x in pack["knowledge_plane"]["items"]):
        required.add("cove_adapter")
    if set(roles) != required:
        return False
    by = {c["role"]:c for c in comps}
    closure = profile["knowledge"]["closure_descriptor"]
    cc = by["closure_descriptor"]
    return (
        cc["contract"] == closure["contract"] and
        cc["immutable_identity"] == closure["immutable_snapshot_id"] and
        cc["raw_sha256"] == closure["raw_sha256"] and
        by["jcs_serializer"]["contract"] == "jcs/1"
    )

class P1c(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = load(FIXTURE)
        cls.sample = cls.fx["sample"]

    def test_scope_and_p1b_basis(self):
        self.assertEqual(self.fx["gate"], "P1c")
        self.assertEqual(self.fx["scope"]["authorized"], "P1C_BYTES_DIGESTS_TOOLCHAIN_ONLY")
        self.assertFalse(self.fx["scope"]["p1b_schema_semantics_changed"])
        self.assertFalse(self.fx["scope"]["resolver_implemented"])
        self.assertFalse(self.fx["scope"]["later_gates_implemented"])
        for rel, expected in self.fx["p1b_basis"]["schema_blobs"].items():
            self.assertEqual(git_blob_sha((ROOT / rel).read_bytes()), expected, rel)

    def test_p1b_identity_shape_is_not_reinterpreted(self):
        schema = load(ROOT / "schemas/context-pack.schema.json")
        req = schema["$defs"]["packIdentity"]["required"]
        self.assertEqual(req, [
            "profile_sha256","request_sha256","canonical_state_binding_sha256s",
            "selected_pems_sha256","manifest_sha256","payload_set_sha256","pack_identity_sha256"
        ])
        roles = schema["$defs"]["toolchainComponent"]["properties"]["role"]["enum"]
        self.assertEqual(roles, [
            "pems_schema","pems_validator","closure_descriptor","cove_adapter","jcs_serializer","pack_builder"
        ])

    def test_base64(self):
        for v in self.fx["base64_vectors"]:
            raw = base64.b64decode(v["raw_b64"], validate=True)
            self.assertEqual(b64encode(raw), v["b64"])
            self.assertEqual(b64decode(v["b64"]), raw)
        for text in self.fx["base64_reject"]:
            with self.assertRaises(ValueError):
                b64decode(text)

    def test_raw_bytes_distinguish_newlines(self):
        self.assertNotEqual(raw_sha256(b"line\n"), raw_sha256(b"line\r\n"))
        self.assertNotEqual(b64encode(b"line\n"), b64encode(b"line\r\n"))

    def test_jcs_vectors(self):
        for v in self.fx["jcs_vectors"]:
            self.assertEqual(jcs_bytes(v["value"]).decode("utf-8"), v["expected"])

    def test_domain_vectors(self):
        seen = set()
        for v in self.fx["domain_vectors"]:
            body = base64.b64decode(v["body_b64"], validate=True)
            p = digest_preimage(v["domain"], body)
            self.assertEqual(p.hex(), v["expected_preimage_hex"])
            d = raw_sha256(p)
            self.assertEqual(d, v["expected_sha256"])
            seen.add(d)
        self.assertEqual(len(seen), len(self.fx["domain_vectors"]))

    def test_raw_and_canonical_profile_request_identities(self):
        for name, domain in (("profile","context-profile"),("request","context-pack-request")):
            raw = b64decode(self.sample[name + "_raw_b64"])
            self.assertEqual(raw_sha256(raw), self.sample[name + "_raw_sha256"])
            canonical = domain_sha256(domain, self.sample[name])
            self.assertEqual(canonical, self.sample["expected_identity"][name + "_sha256"])
            self.assertNotEqual(canonical, self.sample[name + "_raw_sha256"])

    def test_frozen_pack_vector(self):
        pack, ident = build_identity(self.sample["profile"], self.sample["request"], self.sample["pack_without_identity"])
        self.assertTrue(validate_toolchain(self.sample["profile"], pack))
        self.assertEqual(ident, self.sample["expected_identity"])
        final = copy.deepcopy(pack)
        final["identity"] = ident
        self.assertEqual(raw_sha256(jcs_bytes(final)), self.sample["expected_serialized_pack_sha256"])
        self.assertEqual(self.sample["expected_receipt"]["pack_identity_sha256"], ident["pack_identity_sha256"])
        self.assertEqual(self.sample["expected_receipt"]["serialized_pack_sha256"], raw_sha256(jcs_bytes(final)))
        self.assertNotIn("receipt", final)

    def test_pack_identity_preimage_is_non_circular(self):
        _, ident = build_identity(self.sample["profile"], self.sample["request"], self.sample["pack_without_identity"])
        pre = {"contract":"reasoning-distiller-context-pack-identity-preimage/1", **{k:v for k,v in ident.items() if k != "pack_identity_sha256"}}
        self.assertNotIn("pack_identity_sha256", pre)
        self.assertEqual(domain_sha256("context-pack-identity", pre), ident["pack_identity_sha256"])

    def test_array_order_is_canonical(self):
        a = copy.deepcopy(self.sample["pack_without_identity"])
        b = copy.deepcopy(a)
        b["source_registry"].reverse()
        b["inclusion_ledger"].reverse()
        b["toolchain"]["components"].reverse()
        ca, ia = build_identity(self.sample["profile"], self.sample["request"], a)
        cb, ib = build_identity(self.sample["profile"], self.sample["request"], b)
        self.assertEqual(jcs_bytes(ca), jcs_bytes(cb))
        self.assertEqual(ia, ib)

    def test_standing_evidence_is_p1a_set(self):
        p = copy.deepcopy(self.sample["pack_without_identity"])
        canonical = next(x for x in p["source_registry"] if x["source_class"] == "canonical_state")
        ev = copy.deepcopy(canonical["standing_evidence"][0])
        canonical["standing_evidence"] = [ev, copy.deepcopy(ev)]
        item = p["knowledge_plane"]["items"][0]["canonical_snapshot_ref"]
        item["standing_evidence"] = [copy.deepcopy(ev), copy.deepcopy(ev)]
        _, ident = build_identity(self.sample["profile"], self.sample["request"], p)
        self.assertEqual(ident["canonical_state_binding_sha256s"], self.sample["expected_identity"]["canonical_state_binding_sha256s"])

    def test_payload_and_manifest_domains_are_separate(self):
        p = copy.deepcopy(self.sample["pack_without_identity"])
        _, before = build_identity(self.sample["profile"], self.sample["request"], p)
        p["control_plane"]["items"][0]["payload"]["data"] = b64encode(b"other")
        _, after = build_identity(self.sample["profile"], self.sample["request"], p)
        self.assertEqual(before["manifest_sha256"], after["manifest_sha256"])
        self.assertNotEqual(before["payload_set_sha256"], after["payload_set_sha256"])
        self.assertNotEqual(before["pack_identity_sha256"], after["pack_identity_sha256"])

    def test_toolchain_change_is_visible(self):
        p = copy.deepcopy(self.sample["pack_without_identity"])
        _, before = build_identity(self.sample["profile"], self.sample["request"], p)
        for c in p["toolchain"]["components"]:
            if c["role"] == "pems_validator":
                c["immutable_identity"] = "blob:changed"
                c["raw_sha256"] = raw_sha256(b"changed")
        _, after = build_identity(self.sample["profile"], self.sample["request"], p)
        self.assertEqual(before["payload_set_sha256"], after["payload_set_sha256"])
        self.assertNotEqual(before["manifest_sha256"], after["manifest_sha256"])
        self.assertNotEqual(before["pack_identity_sha256"], after["pack_identity_sha256"])

    def test_toolchain_exact_roles_and_cove_rule(self):
        p = copy.deepcopy(self.sample["pack_without_identity"])
        self.assertTrue(validate_toolchain(self.sample["profile"], p))
        p["toolchain"]["components"].append(copy.deepcopy(p["toolchain"]["components"][0]))
        self.assertFalse(validate_toolchain(self.sample["profile"], p))

        p = copy.deepcopy(self.sample["pack_without_identity"])
        p["knowledge_plane"]["items"][0]["cove_payload"] = {
            "cove_semantic":"cove/1","pems_semantic":"pems/2","serializer":"jcs/1",
            "encoding":"base64","data":b64encode(b"cove"),"raw_sha256":raw_sha256(b"cove")
        }
        self.assertFalse(validate_toolchain(self.sample["profile"], p))
        p["toolchain"]["components"].append({
            "role":"cove_adapter","contract":"cove-adapter/1","immutable_identity":"blob:cove",
            "raw_sha256":raw_sha256(b"cove-adapter")
        })
        self.assertTrue(validate_toolchain(self.sample["profile"], p))
        _, ident = build_identity(self.sample["profile"], self.sample["request"], p)
        self.assertIn("cove_payload_sha256", ident)

if __name__ == "__main__":
    unittest.main()
