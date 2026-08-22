import re
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (ROOT / "docs/design/CONTEXT_PACKAGING_SOURCE_IDENTITY_CONTRACT.md").read_text(encoding="utf-8")
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
SHA = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
CLASSES = {"repository_control", "package_control", "canonical_state", "operational_evidence"}
STATUSES = {"carried_unvalidated", "shape_and_digest_validated", "accepted_validation_result"}
A = "sha256:" + "a" * 64
B = "sha256:" + "b" * 64
C = "sha256:" + "c" * 64
D = "sha256:" + "d" * 64
E = "sha256:" + "e" * 64
F = "sha256:" + "f" * 64
C1 = "1" * 40
C2 = "2" * 40


def repo(logical="control", commit=C1, digest=A, ns="repository:loteque/reasoning-distiller", path="agents/engineer/DIRECTIVE.md"):
    return {"source_class":"repository_control","logical_namespace":ns,"logical_source_id":logical,"repository":"loteque/reasoning-distiller","commit":commit,"path":path,"raw_sha256":digest}


def package(snapshot="package:001"):
    return {"source_class":"package_control","logical_namespace":"project:reasoning-distiller","logical_source_id":"package-control","project_id":"reasoning-distiller","package_contract":"project-knowledge-package/1","immutable_package_snapshot_id":snapshot,"artifact_locator":"rules/context-profile.json","raw_sha256":A}


def standing(id="standing:001", digest=C):
    return {"contract":"canonical-standing-evidence/1","immutable_snapshot_id":id,"raw_sha256":digest}


def canonical(logical="canonical-pems", standing_items=None, relation=None, project="reasoning-distiller", snapshot="snapshot:001", digest=B):
    value = {"source_class":"canonical_state","logical_namespace":"project:reasoning-distiller","logical_source_id":logical,"project_id":project,"backend_type":"pems-cove","backend_contract":"project-canonical-backend/1","backend_config_identity":"config:immutable-001","immutable_snapshot_id":snapshot,"pems_semantic":"pems/2","serializer":"jcs/1","pems_sha256":digest,"standing_evidence":[standing()] if standing_items is None else standing_items}
    if relation is not None:
        value["repository_relationship"] = relation
    return value


def evidence(status="carried_unvalidated", result=None, ns="project:reasoning-distiller", logical="activation-artifact"):
    value = {"source_class":"operational_evidence","logical_namespace":ns,"logical_source_id":logical,"artifact_contract":"reasoning-distiller-role-activation/1","immutable_snapshot_id":"artifact:activation-001","raw_sha256":E,"validation_status":status}
    if result is not None:
        value["validation_result"] = result
    return value


def valid_result():
    return {"contract":"reasoning-distiller-operation-result/1","validator_contract":"reasoning-distiller-role-activation/1","immutable_snapshot_id":"validation:001","raw_sha256":F}


def key(b):
    return f'{b.get("logical_namespace","")}|{b.get("logical_source_id","")}'


def ref(b):
    return f'{b.get("source_class","")}|{key(b)}'


def fingerprint(b):
    if b["source_class"] == "repository_control":
        return (b.get("repository"), b.get("commit", "").lower(), b.get("path"), b.get("raw_sha256", "").lower())
    if b["source_class"] == "package_control":
        return (b.get("project_id"), b.get("package_contract"), b.get("immutable_package_snapshot_id"), b.get("artifact_locator"), b.get("raw_sha256", "").lower())
    if b["source_class"] == "canonical_state":
        proof = tuple(sorted((x.get("contract"), x.get("immutable_snapshot_id"), x.get("raw_sha256")) for x in b.get("standing_evidence", [])))
        return (b.get("project_id"), b.get("backend_type"), b.get("backend_contract"), b.get("backend_config_identity"), b.get("immutable_snapshot_id"), b.get("pems_semantic"), b.get("serializer"), b.get("pems_sha256", "").lower(), proof)
    r = b.get("validation_result")
    rid = None if r is None else (r.get("contract"), r.get("validator_contract"), r.get("immutable_snapshot_id"), r.get("raw_sha256", "").lower())
    return (b.get("artifact_contract"), b.get("immutable_snapshot_id"), b.get("raw_sha256", "").lower(), b.get("validation_status"), rid)


def validate(b):
    if b.get("source_class") not in CLASSES or not b.get("logical_namespace") or not b.get("logical_source_id"):
        return "SOURCE_IDENTITY_INVALID"
    if b["source_class"] == "repository_control":
        if not isinstance(b.get("commit"), str) or not HEX40.fullmatch(b["commit"]): return "IMMUTABLE_SNAPSHOT_UNAVAILABLE"
        if not b.get("repository") or "/" not in b["repository"] or not b.get("path") or b["path"].startswith("/"): return "CONTROL_SOURCE_INVALID"
        if not isinstance(b.get("raw_sha256"), str) or not SHA.fullmatch(b["raw_sha256"]): return "CONTROL_SOURCE_INVALID"
    elif b["source_class"] == "package_control":
        if not b.get("immutable_package_snapshot_id"): return "IMMUTABLE_SNAPSHOT_UNAVAILABLE"
        if not b.get("project_id") or not b.get("package_contract") or not b.get("artifact_locator") or not isinstance(b.get("raw_sha256"), str) or not SHA.fullmatch(b["raw_sha256"]): return "CONTROL_SOURCE_INVALID"
    elif b["source_class"] == "canonical_state":
        required = ("project_id","backend_type","backend_contract","backend_config_identity","immutable_snapshot_id","serializer")
        if any(not b.get(x) for x in required) or b.get("pems_semantic") != "pems/2" or not isinstance(b.get("pems_sha256"), str) or not SHA.fullmatch(b["pems_sha256"]): return "CANONICAL_BINDING_UNPROVEN"
        proof = b.get("standing_evidence")
        if not isinstance(proof, list) or not proof or any(not x.get("contract") or not x.get("immutable_snapshot_id") or not isinstance(x.get("raw_sha256"), str) or not SHA.fullmatch(x["raw_sha256"]) for x in proof): return "CANONICAL_BINDING_UNPROVEN"
        rel = b.get("repository_relationship")
        if rel is not None and (not rel.get("repository") or not isinstance(rel.get("commit"), str) or not HEX40.fullmatch(rel["commit"])): return "CANONICAL_BINDING_UNPROVEN"
    else:
        if not b.get("artifact_contract") or not b.get("immutable_snapshot_id") or not isinstance(b.get("raw_sha256"), str) or not SHA.fullmatch(b["raw_sha256"]): return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
        if b.get("validation_status") not in STATUSES: return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
        if b["validation_status"] == "accepted_validation_result":
            r = b.get("validation_result")
            if not isinstance(r, dict) or any(not r.get(x) for x in ("contract","validator_contract","immutable_snapshot_id")) or not isinstance(r.get("raw_sha256"), str) or not SHA.fullmatch(r["raw_sha256"]): return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
    return None


def evaluate(case):
    bindings = case["bindings"]
    by_key, by_ref = {}, {}
    for b in bindings:
        failure = validate(b)
        if failure: return failure
        by_key.setdefault(key(b), []).append(b)
        by_ref.setdefault(ref(b), []).append(b)
    required = case.get("requires_canonical_source")
    if required and not any(b["source_class"] == "canonical_state" and b["logical_source_id"] == required for b in bindings): return "CANONICAL_BINDING_UNPROVEN"
    allowed = set(case.get("allow_multiple_snapshots", []))
    for k, group in by_key.items():
        if len({b["source_class"] for b in group}) > 1: return "SOURCE_CLASS_CONFLICT"
        if len({fingerprint(b) for b in group}) > 1 and k not in allowed: return "LOGICAL_SOURCE_CONFLICT"
    for c in case.get("constraints", []):
        left, right = by_ref.get(c["left"], []), by_ref.get(c["right"], [])
        if len(left) != 1 or len(right) != 1: return "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
        left, right = left[0], right[0]
        if c["predicate"] == "same_project_identity":
            if not left.get("project_id") or left.get("project_id") != right.get("project_id"): return "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
        elif c["predicate"] == "canonical_declares_repository_snapshot":
            rel = left.get("repository_relationship")
            if left["source_class"] != "canonical_state" or right["source_class"] != "repository_control" or not isinstance(rel, dict) or rel.get("repository") != right.get("repository") or rel.get("commit", "").lower() != right.get("commit", "").lower(): return "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
        else: return "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
    return None


def case(id, bindings, expected=None, **extra):
    return {"id": id, "bindings": bindings, "failure_class": expected, **extra}


r2 = repo(commit=C2, digest=D)
rel1 = {"repository":"loteque/reasoning-distiller","commit":C1}
rel2 = {"repository":"loteque/reasoning-distiller","commit":C2}
repo_controls = repo(logical="controls")
can_ref = "canonical_state|project:reasoning-distiller|canonical-pems"
repo_ref = "repository_control|repository:loteque/reasoning-distiller|controls"
CASES = [
    case("SI-01", [repo()]),
    case("SI-02", [repo(commit="main")], "IMMUTABLE_SNAPSHOT_UNAVAILABLE"),
    case("SI-03", [{k:v for k,v in repo().items() if k != "raw_sha256"}], "CONTROL_SOURCE_INVALID"),
    case("SI-04", [canonical()]),
    case("SI-05", [canonical(standing_items=[])], "CANONICAL_BINDING_UNPROVEN"),
    case("SI-06", [repo(logical="looks-canonical", path="project-knowledge/canonical/pems2.jcs.json", digest=B)], "CANONICAL_BINDING_UNPROVEN", requires_canonical_source="looks-canonical"),
    case("SI-07", [repo(), r2], "LOGICAL_SOURCE_CONFLICT"),
    case("SI-08", [repo(), deepcopy(repo())]),
    case("SI-09", [repo(logical="control-a", path="controls/a.md"), repo(logical="control-b", path="controls/b.md")]),
    case("SI-10", [repo(), r2], allow_multiple_snapshots=[key(repo())]),
    case("SI-11", [evidence()]),
    case("SI-12", [evidence(status="accepted_validation_result")], "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"),
    case("SI-13", [evidence(status="accepted_validation_result", result=valid_result())]),
    case("SI-14", [evidence(status="trusted")], "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"),
    case("SI-15", [repo_controls, canonical(relation=rel1)], constraints=[{"predicate":"canonical_declares_repository_snapshot","left":can_ref,"right":repo_ref}]),
    case("SI-16", [repo_controls, canonical()], "CROSS_SOURCE_CONSISTENCY_UNPROVEN", constraints=[{"predicate":"canonical_declares_repository_snapshot","left":can_ref,"right":repo_ref}]),
    case("SI-17", [repo_controls, canonical(relation=rel2)], "CROSS_SOURCE_CONSISTENCY_UNPROVEN", constraints=[{"predicate":"canonical_declares_repository_snapshot","left":can_ref,"right":repo_ref}]),
    case("SI-18", [canonical(logical="canonical-a"), canonical(logical="canonical-b", snapshot="snapshot:002", digest=D, standing_items=[standing("standing:002", E)])], constraints=[{"predicate":"same_project_identity","left":"canonical_state|project:reasoning-distiller|canonical-a","right":"canonical_state|project:reasoning-distiller|canonical-b"}]),
    case("SI-19", [repo(logical="control-a", path="controls/a.md"), repo(logical="control-b", path="controls/b.md", digest=B)], "CROSS_SOURCE_CONSISTENCY_UNPROVEN", constraints=[{"predicate":"model_says_related","left":"repository_control|repository:loteque/reasoning-distiller|control-a","right":"repository_control|repository:loteque/reasoning-distiller|control-b"}]),
    case("SI-20", [repo(logical="")], "SOURCE_IDENTITY_INVALID"),
    case("SI-21", [package()]),
    case("SI-22", [package(snapshot="")], "IMMUTABLE_SNAPSHOT_UNAVAILABLE"),
    case("SI-23", [repo(ns="project:reasoning-distiller", logical="shared-source", path="controls/a.md"), evidence(ns="project:reasoning-distiller", logical="shared-source")], "SOURCE_CLASS_CONFLICT"),
]


class P1aSourceIdentityTests(unittest.TestCase):
    def test_frozen_plan_and_scope_markers(self):
        for text in ("0803bcca5343224d6feefa53c2f1b8baf1d4a8cd", "8474d2da42f863f0a190fd80292085176d3f97f0", "reasoning-distiller-context-source-identity/1", "P1a Source Identity only"):
            self.assertIn(text, CONTRACT)

    def test_23_machine_checkable_identity_cases(self):
        self.assertEqual(len(CASES), 23)
        self.assertEqual(len({c["id"] for c in CASES}), 23)
        for c in CASES:
            with self.subTest(case=c["id"]): self.assertEqual(evaluate(c), c["failure_class"])

    def test_required_semantics_are_frozen(self):
        for text in ("## 2. Logical source identity", "### 3.2 Package-bound control", "## 4. Canonical-state binding", "## 5. Operational-evidence identity", "## 7. Logical-source conflicts", "## 8. Cross-source consistency", "canonical_declares_repository_snapshot", "same_project_identity", "P1b owns the eventual runtime result/failure contracts", "MUST NOT create standing evidence"):
            self.assertIn(text, CONTRACT)

    def test_later_gates_and_authority_mutations_remain_out_of_scope(self):
        intro = CONTRACT.split("## 1. Core identity model", 1)[0]
        for text in ("does not freeze the P1b profile/request/pack/result/failure schemas", "a P2 resolver", "production `rd-distill` integration", "canonical mutation", "reconciliation", "admission", "role/authority state"):
            self.assertIn(text, intro)


if __name__ == "__main__":
    unittest.main()
