import json
import re
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (ROOT / "docs/design/CONTEXT_PACKAGING_SOURCE_IDENTITY_CONTRACT.md").read_text(encoding="utf-8")
P0 = json.loads((ROOT / "tests/fixtures/context-packaging-pressure-cases-v1.json").read_text(encoding="utf-8"))
P0_BY_ID = {case["id"]: case for case in P0["cases"]}

HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
SHA = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
REPOSITORY = re.compile(r"^[^/]+/[^/]+$")
CLASSES = {"repository_control", "package_control", "canonical_state", "operational_evidence"}
STATUSES = {"carried_unvalidated", "shape_and_digest_validated", "accepted_validation_result"}
ACCEPTED_STANDING = "accepted_project_backend_canonical_standing"

A = "sha256:" + "a" * 64
B = "sha256:" + "b" * 64
C = "sha256:" + "c" * 64
D = "sha256:" + "d" * 64
E = "sha256:" + "e" * 64
F = "sha256:" + "f" * 64
C1 = "1" * 40
C2 = "2" * 40
C3 = "abcdef0123456789abcdef0123456789abcdef01"


def normalized_hex(value):
    return value.lower() if isinstance(value, str) else value


def upper_digest(value):
    return "sha256:" + value.split(":", 1)[1].upper()


def repo(logical="control", commit=C1, digest=A, ns="repository:loteque/reasoning-distiller", path="agents/engineer/DIRECTIVE.md"):
    return {
        "source_class": "repository_control",
        "logical_namespace": ns,
        "logical_source_id": logical,
        "repository": "loteque/reasoning-distiller",
        "commit": commit,
        "path": path,
        "raw_sha256": digest,
    }


def package(snapshot="package:001"):
    return {
        "source_class": "package_control",
        "logical_namespace": "project:reasoning-distiller",
        "logical_source_id": "package-control",
        "project_id": "reasoning-distiller",
        "package_contract": "project-knowledge-package/1",
        "immutable_package_snapshot_id": snapshot,
        "artifact_locator": "rules/context-profile.json",
        "raw_sha256": A,
    }


def standing(id="standing:001", digest=C):
    return {"contract": "canonical-standing-evidence/1", "immutable_snapshot_id": id, "raw_sha256": digest}


def cove(digest=D, cove_semantic="cove/1", pems_semantic="pems/2", serializer="jcs/1"):
    return {
        "cove_semantic": cove_semantic,
        "pems_semantic": pems_semantic,
        "serializer": serializer,
        "raw_sha256": digest,
    }


def canonical(
    logical="canonical-pems",
    standing_items=None,
    relation=None,
    project="reasoning-distiller",
    snapshot="snapshot:001",
    digest=B,
    cove_binding=None,
):
    value = {
        "source_class": "canonical_state",
        "logical_namespace": "project:reasoning-distiller",
        "logical_source_id": logical,
        "project_id": project,
        "backend_type": "pems-cove",
        "backend_contract": "project-canonical-backend/1",
        "backend_config_identity": "config:immutable-001",
        "immutable_snapshot_id": snapshot,
        "pems_semantic": "pems/2",
        "serializer": "jcs/1",
        "pems_sha256": digest,
        "standing_evidence": [standing()] if standing_items is None else standing_items,
    }
    if relation is not None:
        value["repository_relationship"] = relation
    if cove_binding is not None:
        value["cove"] = cove_binding
    return value


def evidence(status="carried_unvalidated", result=None, ns="project:reasoning-distiller", logical="activation-artifact"):
    value = {
        "source_class": "operational_evidence",
        "logical_namespace": ns,
        "logical_source_id": logical,
        "artifact_contract": "reasoning-distiller-role-activation/1",
        "immutable_snapshot_id": "artifact:activation-001",
        "raw_sha256": E,
        "validation_status": status,
    }
    if result is not None:
        value["validation_result"] = result
    return value


def valid_result(digest=F):
    return {
        "contract": "reasoning-distiller-operation-result/1",
        "validator_contract": "reasoning-distiller-role-activation/1",
        "immutable_snapshot_id": "validation:001",
        "raw_sha256": digest,
    }


def logical_key(binding):
    return (binding.get("logical_namespace"), binding.get("logical_source_id"))


def source_ref(binding):
    return (binding.get("source_class"), binding.get("logical_namespace"), binding.get("logical_source_id"))


def standing_identity(item):
    return (item.get("contract"), item.get("immutable_snapshot_id"), normalized_hex(item.get("raw_sha256")))


def standing_identity_set(binding):
    return tuple(sorted({standing_identity(item) for item in binding.get("standing_evidence", [])}))


def cove_identity(binding):
    item = binding.get("cove")
    if item is None:
        return None
    return (
        item.get("cove_semantic"),
        item.get("pems_semantic"),
        item.get("serializer"),
        normalized_hex(item.get("raw_sha256")),
    )


def fingerprint(binding):
    source_class = binding["source_class"]
    if source_class == "repository_control":
        return (
            binding.get("repository"),
            normalized_hex(binding.get("commit")),
            binding.get("path"),
            normalized_hex(binding.get("raw_sha256")),
        )
    if source_class == "package_control":
        return (
            binding.get("project_id"),
            binding.get("package_contract"),
            binding.get("immutable_package_snapshot_id"),
            binding.get("artifact_locator"),
            normalized_hex(binding.get("raw_sha256")),
        )
    if source_class == "canonical_state":
        return (
            binding.get("project_id"),
            binding.get("backend_type"),
            binding.get("backend_contract"),
            binding.get("backend_config_identity"),
            binding.get("immutable_snapshot_id"),
            binding.get("pems_semantic"),
            binding.get("serializer"),
            normalized_hex(binding.get("pems_sha256")),
            cove_identity(binding),
            standing_identity_set(binding),
        )
    result = binding.get("validation_result")
    result_identity = None
    if result is not None:
        result_identity = (
            result.get("contract"),
            result.get("validator_contract"),
            result.get("immutable_snapshot_id"),
            normalized_hex(result.get("raw_sha256")),
        )
    return (
        binding.get("artifact_contract"),
        binding.get("immutable_snapshot_id"),
        normalized_hex(binding.get("raw_sha256")),
        binding.get("validation_status"),
        result_identity,
    )


def accepted_standing(binding, fingerprint_override=None):
    return {
        "condition": ACCEPTED_STANDING,
        "canonical_ref": source_ref(binding),
        "project_id": binding.get("project_id"),
        "backend_type": binding.get("backend_type"),
        "backend_contract": binding.get("backend_contract"),
        "backend_config_identity": binding.get("backend_config_identity"),
        "canonical_fingerprint": fingerprint(binding) if fingerprint_override is None else fingerprint_override,
    }


def validate(binding):
    source_class = binding.get("source_class")
    if not source_class or not binding.get("logical_namespace") or not binding.get("logical_source_id"):
        return "SOURCE_IDENTITY_INVALID"
    if source_class not in CLASSES:
        return "UNSUPPORTED_SOURCE_CLASS"

    if source_class == "repository_control":
        if not isinstance(binding.get("commit"), str) or not HEX40.fullmatch(binding["commit"]):
            return "IMMUTABLE_SNAPSHOT_UNAVAILABLE"
        if not isinstance(binding.get("repository"), str) or not REPOSITORY.fullmatch(binding["repository"]):
            return "CONTROL_SOURCE_INVALID"
        if not binding.get("path") or binding["path"].startswith("/"):
            return "CONTROL_SOURCE_INVALID"
        if not isinstance(binding.get("raw_sha256"), str) or not SHA.fullmatch(binding["raw_sha256"]):
            return "CONTROL_SOURCE_INVALID"

    elif source_class == "package_control":
        if not binding.get("immutable_package_snapshot_id"):
            return "IMMUTABLE_SNAPSHOT_UNAVAILABLE"
        if (
            not binding.get("project_id")
            or not binding.get("package_contract")
            or not binding.get("artifact_locator")
            or not isinstance(binding.get("raw_sha256"), str)
            or not SHA.fullmatch(binding["raw_sha256"])
        ):
            return "CONTROL_SOURCE_INVALID"

    elif source_class == "canonical_state":
        required = ("project_id", "backend_type", "backend_contract", "backend_config_identity", "immutable_snapshot_id", "serializer")
        if any(not binding.get(field) for field in required):
            return "CANONICAL_BINDING_UNPROVEN"
        if binding.get("pems_semantic") != "pems/2":
            return "CANONICAL_BINDING_UNPROVEN"
        if not isinstance(binding.get("pems_sha256"), str) or not SHA.fullmatch(binding["pems_sha256"]):
            return "CANONICAL_BINDING_UNPROVEN"
        proof = binding.get("standing_evidence")
        if not isinstance(proof, list) or not proof:
            return "CANONICAL_BINDING_UNPROVEN"
        for item in proof:
            if (
                not isinstance(item, dict)
                or not item.get("contract")
                or not item.get("immutable_snapshot_id")
                or not isinstance(item.get("raw_sha256"), str)
                or not SHA.fullmatch(item["raw_sha256"])
            ):
                return "CANONICAL_BINDING_UNPROVEN"
        cove_binding = binding.get("cove")
        if cove_binding is not None:
            if not isinstance(cove_binding, dict):
                return "CANONICAL_BINDING_UNPROVEN"
            if (
                cove_binding.get("cove_semantic") != "cove/1"
                or cove_binding.get("pems_semantic") != "pems/2"
                or cove_binding.get("serializer") != "jcs/1"
                or not isinstance(cove_binding.get("raw_sha256"), str)
                or not SHA.fullmatch(cove_binding["raw_sha256"])
            ):
                return "CANONICAL_BINDING_UNPROVEN"
        relation = binding.get("repository_relationship")
        if relation is not None and (
            not isinstance(relation, dict)
            or not relation.get("repository")
            or not isinstance(relation.get("commit"), str)
            or not HEX40.fullmatch(relation["commit"])
        ):
            return "CANONICAL_BINDING_UNPROVEN"

    else:
        if (
            not binding.get("artifact_contract")
            or not binding.get("immutable_snapshot_id")
            or not isinstance(binding.get("raw_sha256"), str)
            or not SHA.fullmatch(binding["raw_sha256"])
        ):
            return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
        if binding.get("validation_status") not in STATUSES:
            return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
        if binding["validation_status"] == "accepted_validation_result":
            result = binding.get("validation_result")
            if (
                not isinstance(result, dict)
                or any(not result.get(field) for field in ("contract", "validator_contract", "immutable_snapshot_id"))
                or not isinstance(result.get("raw_sha256"), str)
                or not SHA.fullmatch(result["raw_sha256"])
            ):
                return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
    return None


def canonical_standing_failure(binding, conditions):
    relevant = [condition for condition in conditions if condition.get("canonical_ref") == source_ref(binding)]
    if not relevant:
        return "CANONICAL_BINDING_UNPROVEN"
    for condition in relevant:
        if (
            condition.get("condition") == ACCEPTED_STANDING
            and condition.get("project_id") == binding.get("project_id")
            and condition.get("backend_type") == binding.get("backend_type")
            and condition.get("backend_contract") == binding.get("backend_contract")
            and condition.get("backend_config_identity") == binding.get("backend_config_identity")
            and condition.get("canonical_fingerprint") == fingerprint(binding)
        ):
            return None
    return "CANONICAL_BINDING_CONFLICT"


def evaluate(case):
    bindings = case["bindings"]
    by_key = {}
    by_ref = {}

    for binding in bindings:
        failure = validate(binding)
        if failure:
            return failure
        by_key.setdefault(logical_key(binding), []).append(binding)
        by_ref.setdefault(source_ref(binding), []).append(binding)

    allowed = set(case.get("allow_multiple_snapshots", []))
    for key, group in by_key.items():
        if len({binding["source_class"] for binding in group}) > 1:
            return "SOURCE_CLASS_CONFLICT"
        if len({fingerprint(binding) for binding in group}) > 1 and key not in allowed:
            return "LOGICAL_SOURCE_CONFLICT"

    required = case.get("requires_canonical_source")
    if required and not any(
        binding["source_class"] == "canonical_state" and logical_key(binding) == required for binding in bindings
    ):
        return "CANONICAL_BINDING_UNPROVEN"

    conditions = case.get("accepted_canonical_standing", [])
    for binding in bindings:
        if binding["source_class"] == "canonical_state":
            failure = canonical_standing_failure(binding, conditions)
            if failure:
                return failure

    for constraint in case.get("constraints", []):
        left_group = by_ref.get(constraint["left"], [])
        right_group = by_ref.get(constraint["right"], [])
        if len(left_group) != 1 or len(right_group) != 1:
            return "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
        left, right = left_group[0], right_group[0]
        if constraint["predicate"] == "same_project_identity":
            if not left.get("project_id") or left.get("project_id") != right.get("project_id"):
                return "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
        elif constraint["predicate"] == "canonical_declares_repository_snapshot":
            relation = left.get("repository_relationship")
            if (
                left["source_class"] != "canonical_state"
                or right["source_class"] != "repository_control"
                or not isinstance(relation, dict)
                or relation.get("repository") != right.get("repository")
                or normalized_hex(relation.get("commit")) != normalized_hex(right.get("commit"))
            ):
                return "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
        else:
            return "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
    return None


def case(id, bindings, expected=None, **extra):
    return {"id": id, "bindings": bindings, "failure_class": expected, **extra}


rel1 = {"repository": "loteque/reasoning-distiller", "commit": C1}
rel2 = {"repository": "loteque/reasoning-distiller", "commit": C2}
rel3_upper = {"repository": "loteque/reasoning-distiller", "commit": C3.upper()}
repo_controls = repo(logical="controls")
repo_controls_c3 = repo(logical="controls-c3", commit=C3)
canon = canonical()
canon_relation = canonical(relation=rel1)
canon_relation_c3 = canonical(logical="canonical-c3", relation=rel3_upper)
canon_a = canonical(logical="canonical-a")
canon_b = canonical(logical="canonical-b", snapshot="snapshot:002", digest=D, standing_items=[standing("standing:002", E)])
can_ref = source_ref(canon)
repo_ref = source_ref(repo_controls)

same_standing_a = canonical(logical="normalized-canonical", standing_items=[standing("standing:001", C), standing("standing:002", D)])
same_standing_b = canonical(
    logical="normalized-canonical",
    digest=upper_digest(B),
    standing_items=[standing("standing:002", upper_digest(D)), standing("standing:001", upper_digest(C))],
)
duplicate_standing = canonical(
    logical="duplicate-standing",
    standing_items=[standing("standing:001", C), standing("standing:001", upper_digest(C))],
)
single_standing = canonical(logical="duplicate-standing", standing_items=[standing("standing:001", C)])

cove_a = canonical(logical="cove-source", cove_binding=cove(D))
cove_b = canonical(logical="cove-source", cove_binding=cove(E))
cove_tuple_changed = canonical(logical="cove-source-invalid", cove_binding=cove(D, serializer="other/1"))

alias_a = repo(ns="a|b", logical="c", path="controls/a.md")
alias_b = repo(ns="a", logical="b|c", path="controls/b.md", digest=B)

unknown_source = {"source_class": "ambient_session_memory", "logical_namespace": "session", "logical_source_id": "memory"}

conflicting_acceptance_target = canonical(logical="conflicting-standing")
conflicting_fp = list(fingerprint(conflicting_acceptance_target))
conflicting_fp[4] = "snapshot:other"
conflicting_fp = tuple(conflicting_fp)

same_content_control = repo(logical="same-content-control", path="controls/same.txt", digest=B)
same_content_knowledge = canonical(logical="same-content-knowledge", digest=B)

CASES = [
    case("SI-01", [repo()]),
    case("SI-02", [repo(commit="main")], "IMMUTABLE_SNAPSHOT_UNAVAILABLE"),
    case("SI-03", [{key: value for key, value in repo().items() if key != "raw_sha256"}], "CONTROL_SOURCE_INVALID"),
    case("SI-04", [canon], accepted_canonical_standing=[accepted_standing(canon)]),
    case("SI-05", [canonical(standing_items=[])], "CANONICAL_BINDING_UNPROVEN"),
    case(
        "SI-06",
        [repo(logical="looks-canonical", path="project-knowledge/canonical/pems2.jcs.json", digest=B)],
        "CANONICAL_BINDING_UNPROVEN",
        requires_canonical_source=("repository:loteque/reasoning-distiller", "looks-canonical"),
    ),
    case("SI-07", [repo(), repo(commit=C2, digest=D)], "LOGICAL_SOURCE_CONFLICT"),
    case("SI-08", [repo(), deepcopy(repo())]),
    case("SI-09", [repo(logical="control-a", path="controls/a.md"), repo(logical="control-b", path="controls/b.md")]),
    case("SI-10", [repo(), repo(commit=C2, digest=D)], allow_multiple_snapshots=[logical_key(repo())]),
    case("SI-11", [evidence()]),
    case("SI-12", [evidence(status="accepted_validation_result")], "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"),
    case("SI-13", [evidence(status="accepted_validation_result", result=valid_result())]),
    case("SI-14", [evidence(status="trusted")], "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"),
    case(
        "SI-15",
        [repo_controls, canon_relation],
        accepted_canonical_standing=[accepted_standing(canon_relation)],
        constraints=[{"predicate": "canonical_declares_repository_snapshot", "left": source_ref(canon_relation), "right": repo_ref}],
    ),
    case(
        "SI-16",
        [repo_controls, canon],
        "CROSS_SOURCE_CONSISTENCY_UNPROVEN",
        accepted_canonical_standing=[accepted_standing(canon)],
        constraints=[{"predicate": "canonical_declares_repository_snapshot", "left": can_ref, "right": repo_ref}],
    ),
    case(
        "SI-17",
        [repo_controls, canonical(relation=rel2)],
        "CROSS_SOURCE_CONSISTENCY_UNPROVEN",
        accepted_canonical_standing=[accepted_standing(canonical(relation=rel2))],
        constraints=[{"predicate": "canonical_declares_repository_snapshot", "left": source_ref(canonical(relation=rel2)), "right": repo_ref}],
    ),
    case(
        "SI-18",
        [canon_a, canon_b],
        accepted_canonical_standing=[accepted_standing(canon_a), accepted_standing(canon_b)],
        constraints=[{"predicate": "same_project_identity", "left": source_ref(canon_a), "right": source_ref(canon_b)}],
    ),
    case(
        "SI-19",
        [repo(logical="control-a", path="controls/a.md"), repo(logical="control-b", path="controls/b.md", digest=B)],
        "CROSS_SOURCE_CONSISTENCY_UNPROVEN",
        constraints=[
            {
                "predicate": "model_says_related",
                "left": source_ref(repo(logical="control-a", path="controls/a.md")),
                "right": source_ref(repo(logical="control-b", path="controls/b.md", digest=B)),
            }
        ],
    ),
    case("SI-20", [repo(logical="")], "SOURCE_IDENTITY_INVALID"),
    case("SI-21", [package()]),
    case("SI-22", [package(snapshot="")], "IMMUTABLE_SNAPSHOT_UNAVAILABLE"),
    case(
        "SI-23",
        [repo(ns="project:reasoning-distiller", logical="shared-source", path="controls/a.md"), evidence(ns="project:reasoning-distiller", logical="shared-source")],
        "SOURCE_CLASS_CONFLICT",
    ),
    case("SI-24", [unknown_source], "UNSUPPORTED_SOURCE_CLASS"),
    case("SI-25", [alias_a, alias_b]),
    case("SI-26", [canonical(logical="unproven-standing")], "CANONICAL_BINDING_UNPROVEN"),
    case(
        "SI-27",
        [conflicting_acceptance_target],
        "CANONICAL_BINDING_CONFLICT",
        accepted_canonical_standing=[accepted_standing(conflicting_acceptance_target, fingerprint_override=conflicting_fp)],
    ),
    case(
        "SI-28",
        [same_standing_a, same_standing_b],
        accepted_canonical_standing=[accepted_standing(same_standing_a)],
    ),
    case(
        "SI-29",
        [duplicate_standing, single_standing],
        accepted_canonical_standing=[accepted_standing(single_standing)],
    ),
    case(
        "SI-30",
        [cove_a, cove_b],
        "LOGICAL_SOURCE_CONFLICT",
        accepted_canonical_standing=[accepted_standing(cove_a), accepted_standing(cove_b)],
    ),
    case("SI-31", [cove_tuple_changed], "CANONICAL_BINDING_UNPROVEN"),
    case("SI-32", [cove_a], accepted_canonical_standing=[accepted_standing(cove_a)]),
    case("SI-33", [repo(commit=C3.upper(), digest=upper_digest(A)), repo(commit=C3, digest=A)]),
    case(
        "SI-34",
        [repo_controls_c3, canon_relation_c3],
        accepted_canonical_standing=[accepted_standing(canon_relation_c3)],
        constraints=[
            {
                "predicate": "canonical_declares_repository_snapshot",
                "left": source_ref(canon_relation_c3),
                "right": source_ref(repo_controls_c3),
            }
        ],
    ),
    case(
        "SI-35",
        [same_content_control, same_content_knowledge],
        accepted_canonical_standing=[accepted_standing(same_content_knowledge)],
    ),
]

CASE_BY_ID = {case["id"]: case for case in CASES}

P0_P1A_PRESSURE = {
    "PC-03": (
        "An admitted PEMS/2 `chat` record contains information originally derived from a conversation",
        "It may be selected because it is admitted canonical PEMS state, not because ambient chat is trusted",
        "SI-04",
    ),
    "PC-06": (
        "Target branch moves between request creation and source resolution",
        "Builder either resolves the exact immutable commit required by the request or fails; no silent rebinding",
        "SI-01",
    ),
    "PC-07": (
        "A required control path is missing, symlinked, ambiguous, or digest-mismatched",
        "Fail closed before output",
        "SI-03",
    ),
    "PC-16": (
        "An Engineer/Steward directive is included as a control item",
        "Inclusion conveys exact directive bytes only; it does not establish a registered or activated role",
        "SI-01",
    ),
    "PC-22": (
        "Pack request attempts to name Project memory, assistant recollection, hidden reasoning, or an ungoverned conversation as a source",
        "Reject unsupported source class",
        "SI-24",
    ),
    "PC-24": (
        "Activation evidence is present",
        "The pack may carry the exact artifact/digest as operational evidence but does not convert it into authority; downstream RIL operation must revalidate it as required by its contract",
        "SI-13",
    ),
    "PC-27": (
        "Control repository commit and canonical snapshot come from separately identified immutable states",
        "Record both identities; if the selected profile requires a relationship that cannot be proven, fail",
        "SI-16",
    ),
    "PC-31": (
        "Request points to a schema-valid PEMS/2 file with correct digest that is not proven as admitted canonical state",
        "Reject as non-canonical/unproven canonical binding; path or request label is insufficient",
        "SI-26",
    ),
    "PC-32": (
        "Canonical PEMS bytes are present but the project/backend admission binding or receipt chain identifies a different snapshot",
        "Fail stale/conflicting canonical-state validation",
        "SI-27",
    ),
    "PC-42": (
        "Two source descriptors claim the same logical source but bind different immutable digests",
        "Reject conflict unless multi-snapshot semantics are explicitly part of the profile",
        "SI-07",
    ),
    "PC-43": (
        "Operational-evidence artifact has correct bytes/digest but is expired, invalidly bound, or otherwise not accepted by its RIL validator",
        "Pack records carried/validation status without inferring acceptance; authority-bearing downstream operation revalidates",
        "SI-11",
    ),
    "PC-45": (
        "Same semantic text appears in control and knowledge sources under different identities",
        "Preserve distinct source/plane identities; do not deduplicate by text similarity or content alone",
        "SI-35",
    ),
}


class P1aSourceIdentityTests(unittest.TestCase):
    def test_frozen_plan_and_scope_markers(self):
        for text in (
            "0803bcca5343224d6feefa53c2f1b8baf1d4a8cd",
            "8474d2da42f863f0a190fd80292085176d3f97f0",
            "reasoning-distiller-context-source-identity/1",
            "P1a Source Identity only",
        ):
            self.assertIn(text, CONTRACT)

    def test_35_machine_checkable_identity_cases(self):
        self.assertEqual(len(CASES), 35)
        self.assertEqual(len(CASE_BY_ID), 35)
        for conformance_case in CASES:
            with self.subTest(case=conformance_case["id"]):
                self.assertEqual(evaluate(conformance_case), conformance_case["failure_class"])

    def test_structured_identity_is_collision_free_for_delimiter_contents(self):
        self.assertNotEqual(logical_key(alias_a), logical_key(alias_b))
        self.assertEqual(f'{alias_a["logical_namespace"]}|{alias_a["logical_source_id"]}', f'{alias_b["logical_namespace"]}|{alias_b["logical_source_id"]}')
        self.assertIsNone(evaluate(CASE_BY_ID["SI-25"]))

    def test_canonical_fingerprint_exact_components_and_normalization(self):
        self.assertEqual(fingerprint(same_standing_a), fingerprint(same_standing_b))
        self.assertEqual(fingerprint(duplicate_standing), fingerprint(single_standing))
        self.assertNotEqual(fingerprint(cove_a), fingerprint(cove_b))
        self.assertEqual(fingerprint(repo(commit=C3.upper(), digest=upper_digest(A))), fingerprint(repo(commit=C3, digest=A)))

    def test_shape_valid_standing_does_not_self_prove_acceptance(self):
        candidate = canonical(logical="shape-only")
        self.assertIsNone(validate(candidate))
        self.assertEqual(evaluate(case("shape-only", [candidate])), "CANONICAL_BINDING_UNPROVEN")
        self.assertIsNone(evaluate(case("accepted", [candidate], accepted_canonical_standing=[accepted_standing(candidate)])))

    def test_relevant_frozen_p0_pressure_cases_are_mechanically_preserved(self):
        self.assertEqual(P0["contract"], "reasoning-distiller-context-pack-pressure-suite/1")
        for pc_id, (pressure_case, required_outcome, si_id) in P0_P1A_PRESSURE.items():
            with self.subTest(p0=pc_id, p1a=si_id):
                frozen = P0_BY_ID[pc_id]
                self.assertEqual(frozen["source_pressure_case"], pressure_case)
                self.assertEqual(frozen["required_outcome"], required_outcome)
                result = evaluate(CASE_BY_ID[si_id])
                if frozen["expected_result"] == "PASS":
                    self.assertIsNone(result)
                else:
                    self.assertEqual(result, frozen["failure_class"])

    def test_required_semantics_are_frozen(self):
        for text in (
            "The tuple is the identity",
            "accepted project/backend standing condition",
            "optional_cove_tuple_and_sha256",
            "standing-evidence identity collections are sets",
            "UNSUPPORTED_SOURCE_CLASS",
            "CANONICAL_BINDING_CONFLICT",
            "## 13. P0 pressure-case preservation",
            "P1b owns the eventual runtime result/failure contracts",
            "MUST NOT create standing evidence",
        ):
            self.assertIn(text, CONTRACT)

    def test_later_gates_and_authority_mutations_remain_out_of_scope(self):
        intro = CONTRACT.split("## 1. Core identity model", 1)[0]
        for text in (
            "does not freeze the P1b profile/request/pack/result/failure schemas",
            "a P2 resolver",
            "production `rd-distill` integration",
            "canonical mutation",
            "reconciliation",
            "admission",
            "role/authority state",
        ):
            self.assertIn(text, intro)


if __name__ == "__main__":
    unittest.main()
