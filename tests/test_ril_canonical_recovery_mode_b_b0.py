import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
SCHEMA_FILES = (
    "canonical-recovery-mode-b-common.schema.json",
    "canonical-recovery-damage-analysis.schema.json",
    "canonical-recovery-semantic-disposition.schema.json",
    "canonical-recovery-semantic-disposition-result.schema.json",
    "canonical-recovery-repair-proof.schema.json",
    "canonical-recovery-plan-v2.schema.json",
    "canonical-recovery-root-approval-v2.schema.json",
    "canonical-recovery-journal-v2.schema.json",
    "canonical-recovery-barrier-v2.schema.json",
    "canonical-recovery-completion-v2.schema.json",
    "canonical-recovery-result-v2.schema.json",
    "storage-verification-result-v3.schema.json",
)

SHA = "1" * 64
BLOB = "2" * 40
PROJECT = {"project_id": "reasoning-distiller"}
RAW_PEMS = {"path": "project-knowledge/canonical/pems2.jcs.json", "sha256": SHA, "git_blob": BLOB}
RAW_COVE = {"path": "project-knowledge/canonical/cove1.jcs.json", "sha256": SHA, "git_blob": BLOB}
PAIR = {"pems": RAW_PEMS, "cove": RAW_COVE}
REF = {"path": "project-knowledge/recovery/canonical-pems-cove-mode-b/evidence.json", "sha256": SHA}


class ModeBB0ProtocolFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = {
            name: json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
            for name in SCHEMA_FILES
        }
        cls.registry = Registry().with_resources(
            [
                (schema["$id"], Resource.from_contents(schema))
                for schema in cls.schemas.values()
            ]
        )
        cls.validators = {
            name: Draft202012Validator(schema, registry=cls.registry)
            for name, schema in cls.schemas.items()
        }

    def validate(self, schema_name, instance):
        errors = sorted(
            self.validators[schema_name].iter_errors(instance),
            key=lambda error: list(error.absolute_path),
        )
        self.assertEqual([], errors, [error.message for error in errors])

    def reject(self, schema_name, instance):
        self.assertTrue(list(self.validators[schema_name].iter_errors(instance)))

    def examples(self):
        damage = {
            "contract": "reasoning-distiller-canonical-recovery-damage-analysis/1",
            "project": PROJECT,
            "prestate": PAIR,
            "semantic": "pems/2",
            "toolchain": {
                "pems_schema_sha256": SHA,
                "semantic_validator_sha256": SHA,
                "normalizer_sha256": SHA,
                "cove_codec_sha256": SHA,
            },
            "damage_set": {
                "profile_id": "reasoning-distiller-project-a0-missing-relation-fields/1",
                "relation_count": 1,
                "ordered_relation_set_sha256": SHA,
                "defects": [{"instance_path": "/relations/0/lifecycle", "keyword": "required", "message": "required field absent"}],
                "additional_damage": False,
            },
            "integrity": {"pems_cove_decode_equal": True, "duplicate_relation_ids": False, "endpoints_valid": True},
            "blocked_checks": ["relation lifecycle validation"],
            "evidence_inventory": REF,
            "candidate_count": 0,
        }
        disposition = {
            "contract": "reasoning-distiller-canonical-recovery-semantic-disposition/1",
            "project": PROJECT,
            "prestate": PAIR,
            "damage_analysis": REF,
            "ordered_relation_set_sha256": SHA,
            "activation": {"role_id": "steward:default", "invocation_id": "example", "requested_scope": "semantic_reconciliation", "artifact": REF},
            "outcome": "DEFER_REPAIR",
            "rationale": "No incident value is selected by this structural example.",
            "uncertainty_treatment": "Unresolved values remain blocked.",
            "values": [{
                "relation_id": "pems:relation:example",
                "from": "pems:proposition:a",
                "to": "pems:proposition:b",
                "kind": "supports",
                "lifecycle": "current",
                "data": {},
                "evidence": [REF],
                "rationale": "Every outcome records a complete per-relation judgment.",
            }],
        }
        repair_proof = {
            "contract": "reasoning-distiller-canonical-recovery-repair-proof/1",
            "project": PROJECT,
            "prestate": PAIR,
            "candidate": PAIR,
            "damage_analysis": REF,
            "disposition": REF,
            "recipe_id": "reasoning-distiller-project-a0-missing-relation-fields/1",
            "insertion_set_sha256": SHA,
            "verified_predicates": [{"id": "closed-insertion", "passed": True}],
        }
        plan = {
            "contract": "reasoning-distiller-canonical-recovery-plan/2",
            "protocol_generation": 2,
            "mode": "B",
            "project": PROJECT,
            "generation": "example-generation",
            "prestate": PAIR,
            "candidate": PAIR,
            "damage_analysis": REF,
            "disposition": REF,
            "repair_proof": REF,
            "recipe_id": "reasoning-distiller-project-a0-missing-relation-fields/1",
            "executable_closure_sha256": SHA,
            "expected_provenance_class": "MODE_B_RECOVERY",
        }
        approval = {
            "contract": "reasoning-distiller-canonical-recovery-root-approval/2",
            "protocol_generation": 2,
            "mode": "B",
            "project": PROJECT,
            "generation": "example-generation",
            "plan_sha256": SHA,
            "protected_root_sha256": SHA,
            "authentication_method": "human_confirmation",
            "confirmation": "AUTHORIZE_CANONICAL_PEMS_COVE_MODE_B_RECOVERY",
            "principal": "example-principal",
        }
        journal = {"contract": "reasoning-distiller-canonical-recovery-journal/2", "protocol_generation": 2, "mode": "B", "generation": "example-generation", "plan_sha256": SHA, "step": "PREPARED", "observed_pair": PAIR}
        barrier = {"contract": "reasoning-distiller-canonical-recovery-barrier/2", "protocol_generation": 2, "mode": "B", "project": PROJECT, "generation": "example-generation", "plan_sha256": SHA, "prestate": PAIR, "poststate": PAIR, "transaction_state": "ACTIVE", "journal": REF}
        completion = {"contract": "reasoning-distiller-canonical-recovery-completion/2", "protocol_generation": 2, "mode": "B", "project": PROJECT, "generation": "example-generation", "plan_sha256": SHA, "prestate": PAIR, "poststate": PAIR, "approval": REF, "damage_analysis": REF, "disposition": REF, "repair_proof": REF, "completion_journal": REF, "provenance_class": "MODE_B_RECOVERY"}
        result = {"contract": "reasoning-distiller-canonical-recovery-result/2", "protocol_generation": 2, "mode": "B", "status": "PASS", "outcome": "RECOVERED", "project": PROJECT, "generation": "example-generation", "plan_sha256": SHA, "pair": PAIR, "completion": REF}
        verification = {"contract": "reasoning-distiller-storage-verification-result/3", "status": "PASS", "outcome": "VERIFIED_RECOVERED", "project": PROJECT, "current_pair": PAIR, "protocol_generation": 2, "provenance_class": "MODE_B_RECOVERY", "completion": REF, "semantic_disposition": REF, "repair_proof": REF}
        disposition_result = {"contract": "reasoning-distiller-canonical-recovery-semantic-disposition-result/1", "status": "FAIL", "outcome": "SEMANTIC_DISPOSITION_DEFERRED", "project": PROJECT, "disposition": REF, "candidate_count": 0}
        return {
            "canonical-recovery-damage-analysis.schema.json": damage,
            "canonical-recovery-semantic-disposition.schema.json": disposition,
            "canonical-recovery-semantic-disposition-result.schema.json": disposition_result,
            "canonical-recovery-repair-proof.schema.json": repair_proof,
            "canonical-recovery-plan-v2.schema.json": plan,
            "canonical-recovery-root-approval-v2.schema.json": approval,
            "canonical-recovery-journal-v2.schema.json": journal,
            "canonical-recovery-barrier-v2.schema.json": barrier,
            "canonical-recovery-completion-v2.schema.json": completion,
            "canonical-recovery-result-v2.schema.json": result,
            "storage-verification-result-v3.schema.json": verification,
        }

    def test_all_schemas_are_valid_draft_2020_12(self):
        for name, schema in self.schemas.items():
            with self.subTest(name=name):
                Draft202012Validator.check_schema(schema)

    def test_frozen_positive_examples_validate(self):
        for name, example in self.examples().items():
            with self.subTest(name=name):
                self.validate(name, example)

    def test_unknown_members_are_rejected_at_artifact_boundary(self):
        for name, example in self.examples().items():
            hostile = copy.deepcopy(example)
            hostile["unexpected"] = True
            with self.subTest(name=name):
                self.reject(name, hostile)

    def test_v2_family_rejects_mode_a_and_mixed_generation(self):
        for name, example in self.examples().items():
            if example.get("protocol_generation") != 2:
                continue
            hostile = copy.deepcopy(example)
            hostile["protocol_generation"] = 1
            with self.subTest(name=name, attack="generation"):
                self.reject(name, hostile)
            if "mode" in example:
                hostile = copy.deepcopy(example)
                hostile["mode"] = "A"
                with self.subTest(name=name, attack="mode"):
                    self.reject(name, hostile)

    def test_disposition_is_candidate_free_and_scope_is_exact(self):
        disposition = self.examples()["canonical-recovery-semantic-disposition.schema.json"]
        hostile = copy.deepcopy(disposition)
        hostile["candidate"] = PAIR
        self.reject("canonical-recovery-semantic-disposition.schema.json", hostile)
        hostile = copy.deepcopy(disposition)
        hostile["activation"]["requested_scope"] = "admission"
        self.reject("canonical-recovery-semantic-disposition.schema.json", hostile)

    def test_disposition_rows_freeze_current_pems_relation_vocabularies(self):
        disposition = self.examples()["canonical-recovery-semantic-disposition.schema.json"]
        row = {
            "relation_id": "pems:relation:example",
            "from": "pems:proposition:a",
            "to": "pems:proposition:b",
            "kind": "depends_on",
            "lifecycle": "current",
            "data": {"dependency_kind": "structural"},
            "evidence": [REF],
            "rationale": "Structural example only; not incident evidence.",
        }
        accepted = copy.deepcopy(disposition)
        accepted["outcome"] = "ACCEPT_REPAIR"
        accepted["values"] = [row]
        self.validate("canonical-recovery-semantic-disposition.schema.json", accepted)
        for field, value in (("lifecycle", "unknown"), ("kind", "invented")):
            hostile = copy.deepcopy(accepted)
            hostile["values"][0][field] = value
            self.reject("canonical-recovery-semantic-disposition.schema.json", hostile)
        hostile = copy.deepcopy(accepted)
        hostile["values"][0]["data"] = {}
        self.reject("canonical-recovery-semantic-disposition.schema.json", hostile)
        hostile = copy.deepcopy(accepted)
        hostile["values"][0]["kind"] = "supports"
        self.reject("canonical-recovery-semantic-disposition.schema.json", hostile)

    def test_every_disposition_outcome_requires_a_complete_nonempty_value_table(self):
        disposition = self.examples()["canonical-recovery-semantic-disposition.schema.json"]
        for outcome in ("ACCEPT_REPAIR", "REJECT_REPAIR", "DEFER_REPAIR"):
            hostile = copy.deepcopy(disposition)
            hostile["outcome"] = outcome
            hostile["values"] = []
            with self.subTest(outcome=outcome):
                self.reject("canonical-recovery-semantic-disposition.schema.json", hostile)

    def test_provenance_class_is_distinct_from_verification_outcome(self):
        examples = self.examples()
        plan = copy.deepcopy(examples["canonical-recovery-plan-v2.schema.json"])
        plan["expected_provenance_class"] = "VERIFIED_RECOVERED"
        self.reject("canonical-recovery-plan-v2.schema.json", plan)
        completion = copy.deepcopy(examples["canonical-recovery-completion-v2.schema.json"])
        completion["provenance_class"] = "VERIFIED_RECOVERED"
        self.reject("canonical-recovery-completion-v2.schema.json", completion)

    def test_result_status_outcome_and_required_references_are_coherent(self):
        examples = self.examples()
        disposition_result = examples["canonical-recovery-semantic-disposition-result.schema.json"]
        hostile = copy.deepcopy(disposition_result)
        hostile["status"] = "PASS"
        self.reject("canonical-recovery-semantic-disposition-result.schema.json", hostile)
        hostile = copy.deepcopy(disposition_result)
        hostile["outcome"] = "ACCEPT_REPAIR"
        self.reject("canonical-recovery-semantic-disposition-result.schema.json", hostile)

        recovery_result = examples["canonical-recovery-result-v2.schema.json"]
        hostile = copy.deepcopy(recovery_result)
        hostile["status"] = "FAIL"
        self.reject("canonical-recovery-result-v2.schema.json", hostile)
        hostile = copy.deepcopy(recovery_result)
        del hostile["completion"]
        self.reject("canonical-recovery-result-v2.schema.json", hostile)
        hostile = copy.deepcopy(recovery_result)
        hostile["status"] = "FAIL"
        hostile["outcome"] = "MODE_B_CANDIDATE_INVALID"
        self.reject("canonical-recovery-result-v2.schema.json", hostile)

    def test_storage_verification_combinations_are_exact(self):
        verification = self.examples()["storage-verification-result-v3.schema.json"]
        admitted = copy.deepcopy(verification)
        admitted.update({"outcome": "VERIFIED_ADMITTED", "protocol_generation": 1, "provenance_class": "ADMISSION"})
        for field in ("completion", "semantic_disposition", "repair_proof"):
            del admitted[field]
        self.validate("storage-verification-result-v3.schema.json", admitted)
        mode_a = copy.deepcopy(verification)
        mode_a.update({"protocol_generation": 1, "provenance_class": "MODE_A_RECOVERY"})
        del mode_a["semantic_disposition"]
        del mode_a["repair_proof"]
        self.validate("storage-verification-result-v3.schema.json", mode_a)

        attacks = []
        hostile = copy.deepcopy(verification)
        hostile["status"] = "FAIL"
        attacks.append(hostile)
        hostile = copy.deepcopy(verification)
        hostile["provenance_class"] = "ADMISSION"
        hostile["protocol_generation"] = 1
        attacks.append(hostile)
        hostile = copy.deepcopy(verification)
        hostile["provenance_class"] = "MODE_A_RECOVERY"
        hostile["protocol_generation"] = 1
        attacks.append(hostile)
        hostile = copy.deepcopy(verification)
        del hostile["semantic_disposition"]
        attacks.append(hostile)
        hostile = copy.deepcopy(admitted)
        hostile["completion"] = REF
        attacks.append(hostile)
        hostile = copy.deepcopy(mode_a)
        hostile["semantic_disposition"] = REF
        attacks.append(hostile)
        for index, hostile in enumerate(attacks):
            with self.subTest(index=index):
                self.reject("storage-verification-result-v3.schema.json", hostile)

    def test_mode_a_runtime_and_contract_are_not_modified_by_b0(self):
        mode_a_contract = (ROOT / "docs/operations/RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("Status: **Normative Mode A V1 contract**", mode_a_contract)
        runtime_files = (
            "runtime/ril_canonical_recovery_planner.py",
            "runtime/ril_canonical_recovery_approval.py",
            "runtime/ril_canonical_recovery_executor.py",
            "runtime/ril_canonical_store.py",
            "runtime/ril_storage_verification.py",
        )
        for relative in runtime_files:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn('canonical-recovery-plan/2', text)
            self.assertNotIn('canonical-recovery-result/2', text)
            self.assertNotIn('storage-verification-result/3', text)


if __name__ == "__main__":
    unittest.main()
