import hashlib
import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = ROOT / "protocols/rgp/pems2-context-closure-v1.json"
FIXTURES = ROOT / "tests/fixtures/context-packaging-pems-closure-p1d.json"
P0 = ROOT / "tests/fixtures/context-packaging-pressure-cases-v1.json"
PEMS_SCHEMA = ROOT / "backends/pems-cove/pems-v2.schema.json"
PEMS_VALIDATOR = ROOT / "backends/pems-cove/validate_pems2_contract.py"
P1C_FIXTURE = ROOT / "tests/fixtures/context-packaging-p1c-closure-descriptor-identity.json"

SCHEMA_BLOB = "cd7683d704e8aef2842a0c1b25b453fb1dbc8030"
VALIDATOR_BLOB = "d615bf2e95d3721b0ca312075cc0c39522f0a896"
ALLOWED_RULES = {"include_transitively", "preserve_external_reference", "reject"}
EXTERNAL_NAMES = {"repository", "path", "branch", "commit", "uri", "number"}
EXTERNAL_FRAGMENTS = {"locator", "fingerprint", "external_ref", "authority_target", "head_commit"}
STRUCTURAL_NAMES = {"from", "to"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha1(path):
    body = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()


def load_validator():
    spec = importlib.util.spec_from_file_location("pems2_bound_validator", PEMS_VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load bound PEMS/2 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def index_rules(descriptor):
    return {rule["rule_id"]: rule for rule in descriptor["reference_rules"]}


def classify(descriptor, scope, path, record_kind=None):
    found = []
    for rule in descriptor["reference_rules"]:
        if rule["scope"] != scope or rule["path"] != path:
            continue
        kinds = rule.get("record_kinds")
        if kinds is None or record_kind in kinds:
            found.append(rule)
    if len(found) > 1:
        raise AssertionError(f"ambiguous rule {(scope, path, record_kind)}")
    if not found:
        return descriptor["undefined_reference_policy"], descriptor["undefined_reference_failure_code"]
    rule = found[0]
    failure = None
    if rule["rule"] == "reject":
        failure = rule.get("failure_code", descriptor["undefined_reference_failure_code"])
    return rule["rule"], failure


def ref_name(node):
    ref = node.get("$ref")
    return ref.rsplit("/", 1)[-1] if ref else None


def object_ref(schema, node):
    name = ref_name(node)
    target = schema.get("$defs", {}).get(name) if name else None
    return name if isinstance(target, dict) and isinstance(target.get("properties"), dict) else None


def reference_leaf(schema, name, node):
    if object_ref(schema, node):
        return False
    if ref_name(node) == "idArray" or name.endswith("_id") or name.endswith("_ids"):
        return True
    if name in STRUCTURAL_NAMES or name in EXTERNAL_NAMES or name.endswith("_path"):
        return True
    return any(fragment in name for fragment in EXTERNAL_FRAGMENTS)


def rule_key(rule):
    return rule["scope"], rule["path"], tuple(sorted(rule.get("record_kinds", ())))


def discover_reference_keys(schema):
    found = set()

    def walk(properties, scope, prefix="", kinds=(), ancestors=()):
        for name, node in properties.items():
            path = f"{prefix}.{name}" if prefix else name
            if reference_leaf(schema, name, node):
                found.add((scope, path, tuple(sorted(kinds))))
            target_name = object_ref(schema, node)
            if target_name and target_name not in ancestors:
                walk(
                    schema["$defs"][target_name]["properties"],
                    scope,
                    path,
                    kinds,
                    ancestors + (target_name,),
                )

    for name, node in schema["properties"].items():
        if reference_leaf(schema, name, node):
            found.add(("root", name, ()))

    walk(schema["$defs"]["record"]["properties"], "record")
    walk(schema["$defs"]["relation"]["properties"], "relation")

    data_kinds = {}
    for clause in schema["$defs"]["record"]["allOf"]:
        kind = clause["if"]["properties"]["kind"]["const"]
        data_def = clause["then"]["properties"]["data"]["$ref"].rsplit("/", 1)[-1]
        data_kinds.setdefault(data_def, set()).add(kind)
    for data_def, kinds in sorted(data_kinds.items()):
        walk(
            schema["$defs"][data_def]["properties"],
            "record",
            "data",
            tuple(sorted(kinds)),
            (data_def,),
        )
    return found


def set_path(item, path, value):
    node = item
    parts = path.split(".")
    for part in parts[:-1]:
        node = node[part]
    node[parts[-1]] = value


class P1dClosureFreeze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = load(DESCRIPTOR)
        cls.f = load(FIXTURES)
        cls.p0 = load(P0)
        cls.schema = load(PEMS_SCHEMA)
        cls.rules = index_rules(cls.d)
        cls.validator = load_validator()
        cls.schema_validator = Draft202012Validator(cls.schema)

    def valid_doc(self):
        valid, _invalid = self.validator.structural_smoke_documents()
        return deepcopy(valid)

    def validate(self, doc):
        return self.validator.validate_candidate_document(doc, self.schema_validator)

    def test_gate_basis_and_bound_artifacts(self):
        self.assertEqual(self.d["contract"], "reasoning-distiller-pems2-closure-descriptor/1")
        self.assertEqual(self.d["semantic"], "pems/2")
        self.assertEqual(self.d["scope"], "P1D_CLOSURE_SEMANTICS_ONLY")
        self.assertEqual(self.d["governing_plan"]["commit"], "0803bcca5343224d6feefa53c2f1b8baf1d4a8cd")
        self.assertEqual(self.d["p1c_basis"]["candidate_commit"], "ec5fe4c6c7e8678c3ead0ac629d97d04022b914c")
        self.assertEqual(self.d["p1c_basis"]["execution_disposition"], "P1C_CONFORMANCE_EXECUTION_PASS")
        self.assertEqual(self.d["p1c_basis"]["evidence_manifest_blob"], "0f50bb7b7e96a13311e86c881cdf74a92df44479")
        self.assertEqual(blob_sha1(PEMS_SCHEMA), SCHEMA_BLOB)
        self.assertEqual(blob_sha1(PEMS_VALIDATOR), VALIDATOR_BLOB)
        self.assertEqual(self.d["pems_basis"]["schema_git_blob_sha1"], SCHEMA_BLOB)
        self.assertEqual(self.d["pems_basis"]["validator_git_blob_sha1"], VALIDATOR_BLOB)

    def test_schema_discovery_is_independent_and_exhaustive(self):
        discovered = discover_reference_keys(self.schema)
        declared = {rule_key(rule) for rule in self.d["reference_rules"]}
        self.assertEqual(discovered, declared)
        self.assertEqual(len(declared), len(self.d["reference_rules"]))
        self.assertNotIn(("record", "id", ()), discovered)
        self.assertNotIn(("relation", "id", ()), discovered)
        self.assertEqual(
            self.d["identifier_definitions"],
            [
                {"scope": "record", "path": "id", "namespace": "record"},
                {"scope": "relation", "path": "id", "namespace": "relation"},
            ],
        )

    def test_rule_vocabulary_and_namespace_shape_are_closed(self):
        self.assertEqual(set(self.d["rule_vocabulary"]), ALLOWED_RULES)
        keys = []
        for rule in self.d["reference_rules"]:
            self.assertIn(rule["rule"], ALLOWED_RULES)
            keys.append(rule_key(rule))
            if rule["rule"] == "include_transitively":
                self.assertIn(rule.get("target_namespace"), {"record", "relation"})
            else:
                self.assertNotIn("target_namespace", rule)
            if rule["rule"] == "reject":
                self.assertEqual(rule.get("failure_code"), "UNDEFINED_CLOSURE_RULE")
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(
            {rule["rule_id"] for rule in self.d["reference_rules"] if rule["rule"] == "include_transitively"},
            {
                "pems2.root.project_id",
                "pems2.record.provenance.primary",
                "pems2.record.provenance.corroborating",
                "pems2.record.provenance.context",
                "pems2.record.provenance.untyped",
                "pems2.source_observation.source_id",
                "pems2.relation.from",
                "pems2.relation.to",
                "pems2.relation.provenance.primary",
                "pems2.relation.provenance.corroborating",
                "pems2.relation.provenance.context",
                "pems2.relation.provenance.untyped",
            },
        )

    def test_validator_grounds_relation_endpoints_and_provenance(self):
        for field in ("from", "to"):
            self.validate(self.valid_doc())
            doc = self.valid_doc()
            doc["relations"][0][field] = doc["relations"][0]["id"]
            with self.assertRaises(AssertionError):
                self.validate(doc)
            self.assertEqual(self.rules[f"pems2.relation.{field}"]["target_namespace"], "record")

        for scope in ("record", "relation"):
            doc = self.valid_doc()
            target = doc["records"][-1] if scope == "record" else doc["relations"][0]
            target["provenance"] = {"untyped": [doc["relations"][0]["id"]]}
            with self.assertRaises(AssertionError):
                self.validate(doc)

        for rid in (
            "pems2.record.provenance.primary",
            "pems2.record.provenance.corroborating",
            "pems2.record.provenance.context",
            "pems2.record.provenance.untyped",
            "pems2.relation.provenance.primary",
            "pems2.relation.provenance.corroborating",
            "pems2.relation.provenance.context",
            "pems2.relation.provenance.untyped",
        ):
            self.assertEqual(self.rules[rid]["target_namespace"], "record")
            self.assertEqual(self.rules[rid]["target_kind"], "source_observation")

    def test_validator_grounds_root_and_source_constraints(self):
        doc = self.valid_doc()
        doc["project_id"] = doc["relations"][0]["id"]
        with self.assertRaises(AssertionError):
            self.validate(doc)
        self.assertEqual(self.rules["pems2.root.project_id"]["target_namespace"], "record")
        self.assertEqual(self.rules["pems2.root.project_id"]["target_kind"], "project")

        doc = self.valid_doc()
        observation = next(r for r in doc["records"] if r["kind"] == "source_observation")
        observation["data"]["source_id"] = doc["relations"][0]["id"]
        with self.assertRaises(AssertionError):
            self.validate(doc)
        self.assertEqual(self.rules["pems2.source_observation.source_id"]["target_namespace"], "record")
        self.assertEqual(self.rules["pems2.source_observation.source_id"]["target_kind"], "source")

    def test_validator_unestablished_namespaces_are_rejected(self):
        for scope, field in (("record", "supersedes"), ("record", "superseded_by")):
            for target_namespace in ("record", "relation"):
                doc = self.valid_doc()
                target = doc["records"][0]["id"] if target_namespace == "record" else doc["relations"][0]["id"]
                doc["records"][0][field] = [target]
                self.validate(doc)
            rule = self.rules[f"pems2.{scope}.{field}"]
            self.assertEqual(rule["rule"], "reject")
            self.assertNotIn("target_namespace", rule)

        for field in ("supersedes", "superseded_by"):
            for target_namespace in ("record", "relation"):
                doc = self.valid_doc()
                target = doc["records"][0]["id"] if target_namespace == "record" else doc["relations"][0]["id"]
                doc["relations"][0][field] = [target]
                self.validate(doc)
            rule = self.rules[f"pems2.relation.{field}"]
            self.assertEqual(rule["rule"], "reject")
            self.assertNotIn("target_namespace", rule)

        probes = [
            ("pems2.chat.project_id", "chat", "data.project_id", "scalar", {"project_id": "pems:project:p", "title": "Probe", "summary": "Probe", "started_at": "2026-08-15T00:00:00Z"}),
            ("pems2.chat.active_role_id", "chat", "data.active_role_id", "scalar", {"project_id": "pems:project:p", "title": "Probe", "summary": "Probe", "started_at": "2026-08-15T00:00:00Z", "active_role_id": "pems:project:p"}),
            ("pems2.role.directive_source_id", "role", "data.directive_source_id", "scalar", {"name": "Probe", "responsibility": "Probe", "directive_source_id": "pems:project:p"}),
            ("pems2.database_column.table_id", "database_column", "data.table_id", "scalar", {"table_id": "pems:project:p", "name": "c", "data_type": "text", "nullable": False}),
            ("pems2.pull_request.head_branch_id", "pull_request", "data.head_branch_id", "scalar", {"repository": "o/r", "number": "1", "title": "Probe", "pull_request_state": "open", "head_branch_id": "pems:project:p"}),
            ("pems2.validation.target_id", "validation", "data.target_id", "scalar", {"summary": "Probe", "validation_state": "planned", "target_id": "pems:project:p"}),
            ("pems2.continuation.chat_id", "continuation", "data.chat_id", "scalar", {"chat_id": "pems:project:p", "active_role_id": "pems:project:p", "current_focus": "Probe", "blocker_ids": [], "pending_owner_decision_ids": [], "high_value_record_ids": []}),
            ("pems2.continuation.active_role_id", "continuation", "data.active_role_id", "scalar", {"chat_id": "pems:project:p", "active_role_id": "pems:project:p", "current_focus": "Probe", "blocker_ids": [], "pending_owner_decision_ids": [], "high_value_record_ids": []}),
            ("pems2.continuation.blocker_ids", "continuation", "data.blocker_ids", "array", {"chat_id": "pems:project:p", "active_role_id": "pems:project:p", "current_focus": "Probe", "blocker_ids": [], "pending_owner_decision_ids": [], "high_value_record_ids": []}),
            ("pems2.continuation.pending_owner_decision_ids", "continuation", "data.pending_owner_decision_ids", "array", {"chat_id": "pems:project:p", "active_role_id": "pems:project:p", "current_focus": "Probe", "blocker_ids": [], "pending_owner_decision_ids": [], "high_value_record_ids": []}),
            ("pems2.continuation.high_value_record_ids", "continuation", "data.high_value_record_ids", "array", {"chat_id": "pems:project:p", "active_role_id": "pems:project:p", "current_focus": "Probe", "blocker_ids": [], "pending_owner_decision_ids": [], "high_value_record_ids": []}),
            ("pems2.proposition.about_ids", "proposition", "data.about_ids", "array", {"statement": "Probe", "proposition_kind": "claim", "epistemic_role": "asserted", "about_ids": []}),
        ]
        for index, (rule_id, kind, path, shape, base_data) in enumerate(probes):
            for target_namespace in ("record", "relation"):
                doc = self.valid_doc()
                target = doc["records"][0]["id"] if target_namespace == "record" else doc["relations"][0]["id"]
                record = {"id": f"pems:{kind}:namespace-probe-{index}", "kind": kind, "lifecycle": "current", "data": deepcopy(base_data)}
                set_path(record, path, [target] if shape == "array" else target)
                doc["records"].append(record)
                self.validate(doc)
            rule = self.rules[rule_id]
            self.assertEqual(rule["rule"], "reject", rule_id)
            self.assertEqual(rule["failure_code"], "UNDEFINED_CLOSURE_RULE", rule_id)
            self.assertNotIn("target_namespace", rule, rule_id)

    def test_negative_fixtures_and_fail_closed_behavior(self):
        for case in self.f["cases"]:
            if case["id"] == "supported-rule-omission-is-undefined":
                continue
            if case.get("expected_failure") != "UNDEFINED_CLOSURE_RULE" or "path" not in case:
                continue
            self.assertEqual(
                classify(self.d, case["scope"], case["path"], case.get("record_kind")),
                (case["expected_rule"], case["expected_failure"]),
                case["id"],
            )

        omission = next(c for c in self.f["cases"] if c["id"] == "supported-rule-omission-is-undefined")
        altered = deepcopy(self.d)
        altered["reference_rules"] = [
            rule for rule in altered["reference_rules"]
            if rule["rule_id"] != omission["simulate_descriptor_without_rule_id"]
        ]
        self.assertEqual(
            classify(altered, omission["scope"], omission["path"], omission["record_kind"]),
            ("reject", "UNDEFINED_CLOSURE_RULE"),
        )

    def test_grounded_internal_external_and_missing_target_contracts(self):
        self.assertEqual(
            classify(self.d, "record", "data.source_id", "source_observation")[0],
            "include_transitively",
        )
        self.assertEqual(
            classify(self.d, "record", "data.evidence_locator.commit", "source_observation")[0],
            "preserve_external_reference",
        )
        self.assertEqual(self.d["traversal"]["external_resolution"], "forbidden_by_closure")

        missing = next(c for c in self.f["cases"] if c["id"] == "missing-internal-source-target")
        self.assertEqual(
            classify(self.d, missing["scope"], missing["path"], missing["record_kind"])[0],
            "include_transitively",
        )
        self.assertEqual(self.d["missing_target_failure_code"], missing["expected_failure"])

    def test_structural_rule_and_traversal_are_bounded(self):
        structural = self.d["structural_rules"]
        self.assertEqual(len(structural), 1)
        self.assertEqual(structural[0]["rule_id"], "pems2.derived_proposition.premise_relations")
        self.assertEqual(structural[0]["relation_match"], {"kind": "derived_from", "from": "$trigger_record.id"})
        self.assertEqual(structural[0]["multiplicity"], "all_matching_relations")
        self.assertEqual(structural[0]["on_zero_matches"], "reject")
        t = self.d["traversal"]
        self.assertEqual(t["visited_identity"], "(namespace,id) where namespace is record or relation")
        self.assertIn("visited", t["cycles"])
        self.assertIn("include an item once", t["multiple_causes"])
        self.assertEqual(t["model_judgment"], "forbidden")
        self.assertEqual(t["reverse_relation_discovery"], "none_except_pems2.derived_proposition.premise_relations")

    def test_p0_pressure_cases_remain_frozen(self):
        cases = {case["id"]: case for case in self.p0["cases"]}
        expected = {
            "PC-09": ("PASS", None), "PC-10": ("PASS", None),
            "PC-11": ("PASS", None), "PC-12": ("FAIL", "UNDEFINED_CLOSURE_RULE"),
            "PC-19": ("PASS", None), "PC-20": ("FAIL", "CLOSURE_LIMIT_EXCEEDED"),
            "PC-36": ("FAIL", "TOOLCHAIN_IDENTITY_MISMATCH"),
            "PC-38": ("FAIL", "UNKNOWN_SEMANTICS_FIELD"),
        }
        for case_id, outcome in expected.items():
            self.assertEqual(
                (cases[case_id]["expected_result"], cases[case_id]["failure_class"]),
                outcome,
            )

    def test_p1c_is_unchanged_and_later_gates_are_excluded(self):
        p1c = load(P1C_FIXTURE)
        self.assertEqual(p1c["contract"], "reasoning-distiller-p1c-closure-descriptor-identity-fixture/1")
        self.assertFalse(p1c["p1d_closure_rules_included"])
        self.assertEqual(p1c["scope"], "P1C_TOOLCHAIN_IDENTITY_ONLY")
        exclusions = " ".join(self.d["scope_exclusions"]).lower()
        for word in (
            "source resolution", "projection engine", "profile eligibility", "cove",
            "persistence", "rendering", "production integration", "canonical mutation",
            "reconciliation", "admission", "authorization", "activation",
        ):
            self.assertIn(word, exclusions)


if __name__ == "__main__":
    unittest.main()
