import hashlib
import json
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = ROOT / "protocols/rgp/pems2-context-closure-v1.json"
FIXTURES = ROOT / "tests/fixtures/context-packaging-pems-closure-p1d.json"
P0 = ROOT / "tests/fixtures/context-packaging-pressure-cases-v1.json"
PEMS_SCHEMA = ROOT / "backends/pems-cove/pems-v2.schema.json"
PEMS_VALIDATOR = ROOT / "backends/pems-cove/validate_pems2_contract.py"
P1C_IDENTITY_FIXTURE = ROOT / "tests/fixtures/context-packaging-p1c-closure-descriptor-identity.json"

SCHEMA_BLOB = "cd7683d704e8aef2842a0c1b25b453fb1dbc8030"
VALIDATOR_BLOB = "d615bf2e95d3721b0ca312075cc0c39522f0a896"
ALLOWED_RULES = {"include_transitively", "preserve_external_reference", "reject"}

INTERNAL_RULE_IDS = {
    "pems2.root.project_id",
    "pems2.record.supersedes",
    "pems2.record.superseded_by",
    "pems2.record.provenance.primary",
    "pems2.record.provenance.corroborating",
    "pems2.record.provenance.context",
    "pems2.record.provenance.untyped",
    "pems2.chat.project_id",
    "pems2.chat.active_role_id",
    "pems2.role.directive_source_id",
    "pems2.database_column.table_id",
    "pems2.pull_request.head_branch_id",
    "pems2.validation.target_id",
    "pems2.continuation.chat_id",
    "pems2.continuation.active_role_id",
    "pems2.continuation.blocker_ids",
    "pems2.continuation.pending_owner_decision_ids",
    "pems2.continuation.high_value_record_ids",
    "pems2.source_observation.source_id",
    "pems2.proposition.about_ids",
    "pems2.relation.from",
    "pems2.relation.to",
    "pems2.relation.provenance.primary",
    "pems2.relation.provenance.corroborating",
    "pems2.relation.provenance.context",
    "pems2.relation.provenance.untyped",
    "pems2.relation.supersedes",
    "pems2.relation.superseded_by",
}

EXTERNAL_RULE_IDS = {
    "pems2.project.repository",
    "pems2.external_file.safe_locator",
    "pems2.module.path",
    "pems2.environment_variable.external_ref",
    "pems2.branch.repository",
    "pems2.branch.head_commit",
    "pems2.pull_request.repository",
    "pems2.pull_request.number",
    "pems2.adjustment.authority_target",
    "pems2.source.identity_locator.repository",
    "pems2.source.identity_locator.path",
    "pems2.source.identity_locator.branch",
    "pems2.source.identity_locator.owner_instruction_id",
    "pems2.source.identity_locator.artifact_path",
    "pems2.source.identity_locator.uri",
    "pems2.source_observation.evidence_locator.repository",
    "pems2.source_observation.evidence_locator.commit",
    "pems2.source_observation.evidence_locator.path",
    "pems2.source_observation.evidence_locator.note_id",
    "pems2.source_observation.evidence_locator.owner_instruction_id",
    "pems2.source_observation.evidence_locator.artifact_path",
    "pems2.source_observation.evidence_locator.uri",
    "pems2.source_observation.captured_fingerprint",
}

# Exact schema locations whose referential/identifier semantics P1d accounts for.
# The bound schema blob makes this inventory version-specific rather than heuristic.
SCHEMA_FIELDS = {
    None: {"project_id"},
    "record": {"id", "supersedes", "superseded_by", "provenance"},
    "provenance": {"primary", "corroborating", "context", "untyped"},
    "chatData": {"project_id", "active_role_id"},
    "roleData": {"directive_source_id"},
    "projectData": {"repository"},
    "externalFileData": {"safe_locator"},
    "moduleData": {"path"},
    "environmentVariableData": {"external_ref"},
    "databaseColumnData": {"table_id"},
    "branchData": {"repository", "head_commit"},
    "pullRequestData": {"repository", "number", "head_branch_id"},
    "validationData": {"target_id"},
    "adjustmentData": {"authority_target"},
    "continuationData": {
        "chat_id",
        "active_role_id",
        "blocker_ids",
        "pending_owner_decision_ids",
        "high_value_record_ids",
    },
    "identityLocator": {
        "repository",
        "path",
        "branch",
        "owner_instruction_id",
        "artifact_path",
        "uri",
    },
    "sourceObservationData": {"source_id", "evidence_locator", "captured_fingerprint"},
    "evidenceLocator": {
        "repository",
        "commit",
        "path",
        "note_id",
        "owner_instruction_id",
        "artifact_path",
        "uri",
    },
    "propositionData": {"about_ids"},
    "relation": {"id", "from", "to", "provenance", "supersedes", "superseded_by"},
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha1(path):
    body = path.read_bytes()
    preimage = b"blob " + str(len(body)).encode("ascii") + b"\0" + body
    return hashlib.sha1(preimage).hexdigest()


def rule_index(descriptor):
    return {rule["rule_id"]: rule for rule in descriptor["reference_rules"]}


def classify(descriptor, scope, path, record_kind=None):
    candidates = []
    for rule in descriptor["reference_rules"]:
        if rule["scope"] != scope or rule["path"] != path:
            continue
        kinds = rule.get("record_kinds")
        if kinds is not None and record_kind not in kinds:
            continue
        candidates.append(rule)
    if len(candidates) > 1:
        raise AssertionError(f"ambiguous descriptor rules for {(scope, path, record_kind)}")
    if not candidates:
        return {
            "rule": descriptor["undefined_reference_policy"],
            "failure": descriptor["undefined_reference_failure_code"],
        }
    return {"rule": candidates[0]["rule"], "failure": None, "rule_id": candidates[0]["rule_id"]}


class P1dClosureFreeze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.descriptor = load(DESCRIPTOR)
        cls.fixtures = load(FIXTURES)
        cls.p0 = load(P0)
        cls.schema = load(PEMS_SCHEMA)
        cls.rules = rule_index(cls.descriptor)

    def test_gate_and_prerequisite_binding(self):
        d = self.descriptor
        self.assertEqual(d["contract"], "reasoning-distiller-pems2-closure-descriptor/1")
        self.assertEqual(d["semantic"], "pems/2")
        self.assertEqual(d["scope"], "P1D_CLOSURE_SEMANTICS_ONLY")
        self.assertEqual(
            d["governing_plan"]["commit"],
            "0803bcca5343224d6feefa53c2f1b8baf1d4a8cd",
        )
        self.assertEqual(
            d["p1c_basis"]["candidate_commit"],
            "ec5fe4c6c7e8678c3ead0ac629d97d04022b914c",
        )
        self.assertEqual(d["p1c_basis"]["execution_disposition"], "P1C_CONFORMANCE_EXECUTION_PASS")
        self.assertEqual(
            d["p1c_basis"]["evidence_manifest_blob"],
            "0f50bb7b7e96a13311e86c881cdf74a92df44479",
        )

    def test_bound_pems_artifacts_are_exact(self):
        self.assertEqual(git_blob_sha1(PEMS_SCHEMA), SCHEMA_BLOB)
        self.assertEqual(git_blob_sha1(PEMS_VALIDATOR), VALIDATOR_BLOB)
        self.assertEqual(self.descriptor["pems_basis"]["schema_git_blob_sha1"], SCHEMA_BLOB)
        self.assertEqual(self.descriptor["pems_basis"]["validator_git_blob_sha1"], VALIDATOR_BLOB)

    def test_bound_schema_contains_every_accounted_field(self):
        for def_name, fields in SCHEMA_FIELDS.items():
            props = self.schema["properties"] if def_name is None else self.schema["$defs"][def_name]["properties"]
            for field in fields:
                self.assertIn(field, props, f"{def_name or 'root'}.{field}")

    def test_identifier_definitions_do_not_create_edges(self):
        self.assertEqual(
            self.descriptor["identifier_definitions"],
            [
                {"scope": "record", "path": "id", "namespace": "record"},
                {"scope": "relation", "path": "id", "namespace": "relation"},
            ],
        )
        self.assertNotIn("pems2.record.id", self.rules)
        self.assertNotIn("pems2.relation.id", self.rules)

    def test_rule_vocabulary_is_closed_and_every_rule_is_valid(self):
        self.assertEqual(set(self.descriptor["rule_vocabulary"]), ALLOWED_RULES)
        self.assertEqual(self.descriptor["undefined_reference_policy"], "reject")
        keys = []
        for rule in self.descriptor["reference_rules"]:
            self.assertIn(rule["rule"], ALLOWED_RULES)
            key = (rule["scope"], rule["path"], tuple(rule.get("record_kinds", ())))
            keys.append(key)
        self.assertEqual(len(keys), len(set(keys)), "duplicate or ambiguous field rule")

    def test_internal_reference_inventory_is_exhaustive_for_bound_version(self):
        actual = {rid for rid, rule in self.rules.items() if rule["rule"] == "include_transitively"}
        self.assertEqual(actual, INTERNAL_RULE_IDS)

    def test_external_reference_inventory_is_exhaustive_for_bound_version(self):
        actual = {rid for rid, rule in self.rules.items() if rule["rule"] == "preserve_external_reference"}
        self.assertEqual(actual, EXTERNAL_RULE_IDS)

    def test_existing_validator_kind_constraints_are_preserved_not_broadened(self):
        self.assertEqual(self.rules["pems2.root.project_id"]["target_kind"], "project")
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
            self.assertEqual(self.rules[rid]["target_kind"], "source_observation")
        self.assertEqual(self.rules["pems2.source_observation.source_id"]["target_kind"], "source")
        # Fields not kind-checked by the bound validator remain reachability-only.
        for rid in (
            "pems2.chat.project_id",
            "pems2.chat.active_role_id",
            "pems2.role.directive_source_id",
            "pems2.database_column.table_id",
            "pems2.pull_request.head_branch_id",
            "pems2.validation.target_id",
            "pems2.proposition.about_ids",
        ):
            self.assertNotIn("target_kind", self.rules[rid])

    def test_p0_closure_pressure_cases_remain_frozen(self):
        cases = {case["id"]: case for case in self.p0["cases"]}
        expected = {
            "PC-09": ("PASS", None),
            "PC-10": ("PASS", None),
            "PC-11": ("PASS", None),
            "PC-12": ("FAIL", "UNDEFINED_CLOSURE_RULE"),
            "PC-19": ("PASS", None),
            "PC-20": ("FAIL", "CLOSURE_LIMIT_EXCEEDED"),
            "PC-36": ("FAIL", "TOOLCHAIN_IDENTITY_MISMATCH"),
            "PC-38": ("FAIL", "UNKNOWN_SEMANTICS_FIELD"),
        }
        for case_id, outcome in expected.items():
            self.assertIn(case_id, cases)
            self.assertEqual((cases[case_id]["expected_result"], cases[case_id]["failure_class"]), outcome)

    def test_known_internal_reference_traverses(self):
        result = classify(self.descriptor, "record", "data.about_ids", "proposition")
        self.assertEqual(result["rule"], "include_transitively")

    def test_known_external_reference_is_preserved_but_inert(self):
        result = classify(self.descriptor, "record", "data.evidence_locator.commit", "source_observation")
        self.assertEqual(result["rule"], "preserve_external_reference")
        self.assertEqual(self.descriptor["traversal"]["external_resolution"], "forbidden_by_closure")

    def test_unknown_reference_fails_closed(self):
        case = next(c for c in self.fixtures["cases"] if c["id"] == "undefined-future-record-reference")
        result = classify(self.descriptor, case["scope"], case["path"], case["record_kind"])
        self.assertEqual(result, {"rule": "reject", "failure": "UNDEFINED_CLOSURE_RULE"})

    def test_removing_supported_rule_turns_it_into_undefined_failure(self):
        case = next(c for c in self.fixtures["cases"] if c["id"] == "supported-rule-omission-is-undefined")
        altered = deepcopy(self.descriptor)
        altered["reference_rules"] = [
            r for r in altered["reference_rules"]
            if r["rule_id"] != case["simulate_descriptor_without_rule_id"]
        ]
        result = classify(altered, case["scope"], case["path"], case["record_kind"])
        self.assertEqual(result, {"rule": "reject", "failure": "UNDEFINED_CLOSURE_RULE"})

    def test_missing_internal_target_has_stable_failure(self):
        case = next(c for c in self.fixtures["cases"] if c["id"] == "missing-internal-validation-target")
        result = classify(self.descriptor, case["scope"], case["path"], case["record_kind"])
        self.assertEqual(result["rule"], "include_transitively")
        self.assertEqual(self.descriptor["missing_target_failure_code"], case["expected_failure"])

    def test_derived_proposition_has_only_explicit_inverse_rule(self):
        structural = self.descriptor["structural_rules"]
        self.assertEqual(len(structural), 1)
        rule = structural[0]
        self.assertEqual(rule["rule_id"], "pems2.derived_proposition.premise_relations")
        self.assertEqual(rule["rule"], "include_transitively")
        self.assertEqual(rule["relation_match"], {"kind": "derived_from", "from": "$trigger_record.id"})
        self.assertEqual(rule["multiplicity"], "all_matching_relations")
        self.assertEqual(rule["on_zero_matches"], "reject")
        self.assertEqual(
            self.descriptor["traversal"]["reverse_relation_discovery"],
            "none_except_pems2.derived_proposition.premise_relations",
        )

    def test_cycles_and_duplicate_causes_have_deterministic_contract(self):
        t = self.descriptor["traversal"]
        self.assertEqual(t["visited_identity"], "(namespace,id) where namespace is record or relation")
        self.assertIn("visited", t["cycles"])
        self.assertIn("include an item once", t["multiple_causes"])
        self.assertEqual(t["model_judgment"], "forbidden")

    def test_p1c_identity_fixture_is_not_reinterpreted(self):
        p1c = load(P1C_IDENTITY_FIXTURE)
        self.assertEqual(
            p1c["contract"],
            "reasoning-distiller-p1c-closure-descriptor-identity-fixture/1",
        )
        self.assertFalse(p1c["p1d_closure_rules_included"])
        self.assertEqual(p1c["scope"], "P1C_TOOLCHAIN_IDENTITY_ONLY")

    def test_scope_does_not_begin_later_gates(self):
        exclusions = " ".join(self.descriptor["scope_exclusions"]).lower()
        for word in (
            "source resolution",
            "projection engine",
            "profile eligibility",
            "cove",
            "persistence",
            "rendering",
            "production integration",
            "canonical mutation",
            "reconciliation",
            "admission",
            "authorization",
            "activation",
        ):
            self.assertIn(word, exclusions)


if __name__ == "__main__":
    unittest.main()
