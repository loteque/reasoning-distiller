from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from context_packaging.pems_projection import project_pems  # noqa: E402
from context_packaging.source_resolver import ResolvedSource  # noqa: E402
from rd_bootstrap import build_project_config, canonical_json  # noqa: E402
from ril_activation import make_explicit_activation  # noqa: E402
from ril_admission import (  # noqa: E402
    PLAN_CONTRACT as ADMISSION_PLAN_CONTRACT,
    RECEIPT_CONTRACT,
    admit,
    encode_cove,
    first_admission_base,
    jcs,
    sha256_bytes,
)
from ril_canonical_recovery_approval import RECOVERY_CONFIRMATION, ROOT_APPROVAL_CONTRACT  # noqa: E402
from ril_canonical_recovery_executor import apply_mode_a_recovery  # noqa: E402
from ril_canonical_recovery_planner import build_mode_a_recovery_plan  # noqa: E402
from ril_canonical_recovery_recipe import git_blob_sha1  # noqa: E402
from ril_canonical_store import (  # noqa: E402
    BARRIER_CONTRACT,
    CanonicalStoreSession,
    exclusive_canonical_store,
    shared_canonical_store,
)
from ril_mutation import ContractError, canonical_json_bytes  # noqa: E402
from ril_operators import apply_initial_operator, approve_initial_operator, plan_initial_operator  # noqa: E402
from ril_reconciliation import ASSESSMENT_CONTRACT, reconcile_candidate  # noqa: E402
from ril_steward_authorization import (  # noqa: E402
    apply_authorization_change,
    approve_authorization_change,
    plan_authorization_change,
)
from ril_storage_verification import verify_storage  # noqa: E402


class CanonicalRecoveryG7AdversarialTests(unittest.TestCase):
    """Stage 3 Section 14 adversarial conformance on the exact G6 bundle."""

    BEHAVIOR_DEPENDENCIES = (
        "runtime/ril_canonical_recovery_approval.py",
        "runtime/ril_mutation.py",
        "runtime/ril_operators.py",
        "runtime/ril_storage_verification.py",
    )

    SECTION14_CASES = {
        1: "test_case01_valid_canonical_state_never_enters_recovery",
        2: "test_case02_prestate_hash_and_blob_drift_fail_before_mutation",
        3: "test_case03_wrong_or_missing_protected_root_fails",
        4: "test_case04_approval_replay_against_another_generation_fails",
        5: "test_case05_any_consequential_plan_or_implementation_identity_drift_fails",
        6: "test_case06_semantic_delta_beyond_discriminator_insertion_is_unsupported",
        7: "test_case07_prestate_cove_disagreement_is_ineligible",
        8: "test_case08_missing_or_malformed_recovered_provenance_blocks_verification",
        9: "test_case09_recovery_does_not_create_or_rewrite_ordinary_receipts",
        10: "test_case10_recovery_does_not_mutate_r7_r8_authority_state",
        11: "test_case11_crash_before_pems_publication_keeps_exact_prestate",
        12: "test_case12_crash_between_pems_and_cove_is_barrier_blocked_and_exactly_resumable",
        13: "test_case13_crash_after_pair_publication_before_completion_remains_blocked",
        14: "test_case14_crash_after_completion_before_barrier_clear_finishes_only_same_transaction",
        15: "test_case15_publication_failure_rolls_back_exact_raw_prestate",
        16: "test_case16_rollback_hash_mismatch_leaves_indeterminate_barrier",
        17: "test_case17_exact_successful_retry_is_no_change_only_for_identical_evidence",
        18: "test_case18_same_generation_with_different_plan_or_poststate_conflicts",
        19: "test_case19_corrupted_preserved_evidence_blocks_resume",
        20: "test_case20_shared_reader_lock_blocks_recovery",
        21: "test_case21_exclusive_recovery_lock_blocks_new_reader",
        22: "test_case22_crash_releases_lock_but_barrier_still_blocks_readers",
        23: "test_case23_r13_and_recovery_share_exclusive_mutation_boundary",
        24: "test_case24_static_package_scan_rejects_direct_fixed_canonical_reader",
        25: "test_case25_context_snapshot_acquisition_blocks_during_recovery_and_downstream_is_immutable",
    }

    def valid_pems(self) -> dict:
        return {
            "semantic": "pems/2",
            "project_id": "example-project",
            "records": [
                {
                    "id": "example-project",
                    "kind": "project",
                    "lifecycle": "current",
                    "data": {
                        "name": "Example Project",
                        "repository": "example/project",
                        "summary": "G7 adversarial recovery fixture.",
                    },
                }
            ],
            "relations": [],
        }

    def prestate(self) -> tuple[bytes, bytes]:
        source = self.valid_pems()
        source.pop("semantic")
        return jcs(source), jcs(encode_cove(source))

    def project(self, *, establish_root: bool = True) -> tuple[tempfile.TemporaryDirectory, Path]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        if establish_root:
            proposal = plan_initial_operator(root, "operator:root")["proposal"]
            approval = approve_initial_operator(proposal, "operator:root")
            self.assertEqual(apply_initial_operator(root, proposal, approval)["status"], "PASS")
        canonical = root / "project-knowledge" / "canonical"
        canonical.mkdir(parents=True, exist_ok=True)
        pems, cove = self.prestate()
        (canonical / "pems2.jcs.json").write_bytes(pems)
        (canonical / "cove1.jcs.json").write_bytes(cove)

        evidence = root / "project-knowledge" / "evidence"
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / "historical.json").write_bytes(b'{"historical":true}')

        receipts = root / "project-knowledge" / "admission" / "receipts"
        receipts.mkdir(parents=True, exist_ok=True)
        historical_receipt = {
            "contract": RECEIPT_CONTRACT,
            "candidate_digest": "sha256:" + "1" * 64,
            "disposition_digest": "sha256:" + "2" * 64,
            "activation_digest": "sha256:" + "3" * 64,
            "plan_digest": "sha256:" + "4" * 64,
            "role_id": "steward:default",
            "invocation_id": "invocation:historical",
            "base_pems_sha256": "5" * 64,
            "admitted_pems_sha256": "6" * 64,
            "admitted_cove_sha256": "7" * 64,
        }
        (receipts / "historical.json").write_bytes(canonical_json_bytes(historical_receipt))
        return td, root

    def planned(self, root: Path, generation: str = "g7-fixture-0001"):
        pems, cove = self.prestate()
        return build_mode_a_recovery_plan(
            pems,
            cove,
            project_root=root,
            expected_project_id="example-project",
            generation=generation,
            expected_prestate_pems_sha256=sha256_bytes(pems),
            expected_prestate_cove_sha256=sha256_bytes(cove),
            expected_prestate_pems_git_blob=git_blob_sha1(pems),
            expected_prestate_cove_git_blob=git_blob_sha1(cove),
            selected_evidence_paths=(
                "project-knowledge/admission/receipts/historical.json",
                "project-knowledge/evidence/historical.json",
            ),
            behavior_dependency_paths=self.BEHAVIOR_DEPENDENCIES,
            package_root=ROOT,
        )

    def approval_for(self, plan: dict, *, root_id: str = "operator:root", evidence=None) -> bytes:
        authentication = {
            "method": "human_confirmation",
            "confirmation": RECOVERY_CONFIRMATION,
        }
        if evidence is not None:
            authentication["evidence"] = evidence
        return jcs(
            {
                "contract": ROOT_APPROVAL_CONTRACT,
                "project_id": plan["project_id"],
                "generation": plan["generation"],
                "recovery_plan_sha256": sha256_bytes(jcs(plan)),
                "protected_root_id": root_id,
                "authentication": authentication,
            }
        )

    def apply(self, root: Path, planned, *, plan_bytes: bytes | None = None, approval_bytes: bytes | None = None):
        raw_plan = plan_bytes or planned.plan_bytes
        parsed_plan = json.loads(raw_plan.decode("utf-8"))
        raw_approval = approval_bytes or self.approval_for(parsed_plan)
        return apply_mode_a_recovery(
            root,
            raw_plan,
            raw_approval,
            planned.preserved_evidence_inventory_bytes,
            package_root=ROOT,
        )

    def canonical_bytes(self, root: Path) -> tuple[bytes, bytes]:
        canonical = root / "project-knowledge" / "canonical"
        return (canonical / "pems2.jcs.json").read_bytes(), (canonical / "cove1.jcs.json").read_bytes()

    def barrier_path(self, root: Path) -> Path:
        return root / "project-knowledge" / "recovery" / "canonical-pems-cove" / "active.json"

    def generation_root(self, root: Path, generation: str = "g7-fixture-0001") -> Path:
        return root / "project-knowledge" / "recovery" / "canonical-pems-cove" / "generations" / generation

    def recovery_namespace(self, root: Path) -> Path:
        return root / "project-knowledge" / "recovery"

    def auxiliary_state(self, root: Path) -> dict[str, bytes]:
        knowledge = root / "project-knowledge"
        out: dict[str, bytes] = {}
        if not knowledge.exists():
            return out
        for path in sorted(knowledge.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(knowledge).as_posix()
            if rel.startswith("canonical/") or rel.startswith("recovery/"):
                continue
            out[rel] = path.read_bytes()
        return out

    def mutate_hex(self, value: str) -> str:
        return ("0" if value[0] != "0" else "1") + value[1:]

    def crash_between_pair_members(self, root: Path, planned) -> None:
        real_replace = os.replace
        calls = {"count": 0}

        def crash_second_replace(src, dst):
            calls["count"] += 1
            if calls["count"] == 2:
                raise KeyboardInterrupt("simulated process loss between canonical members")
            return real_replace(src, dst)

        with self.assertRaises(KeyboardInterrupt):
            with patch("ril_canonical_store.os.replace", side_effect=crash_second_replace):
                self.apply(root, planned)

    def authorize_scope(self, root: Path, scope: str) -> None:
        proposal = plan_authorization_change(root, "AUTHORIZE", scope, "steward:default")["proposal"]
        approval = approve_authorization_change(proposal, "operator:root")
        self.assertEqual(apply_authorization_change(root, proposal, approval)["status"], "PASS")

    def admission_ready(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        submissions = root / "project-knowledge" / "submissions"
        submissions.mkdir(parents=True)
        identity = {
            "id": "example-project",
            "name": "Example Project",
            "repository": "example/project",
            "summary": "G7 admission lock fixture.",
        }
        (root / "project-knowledge" / "project.json").write_bytes(canonical_json(build_project_config(identity)))
        proposal = plan_initial_operator(root, "operator:root")["proposal"]
        approval = approve_initial_operator(proposal, "operator:root")
        self.assertEqual(apply_initial_operator(root, proposal, approval)["status"], "PASS")
        self.authorize_scope(root, "semantic_reconciliation")
        candidate = submissions / "candidate.json"
        candidate.write_bytes(canonical_json_bytes({"contract": "test-candidate/1", "claim": "x"}))
        activation = make_explicit_activation("steward:default", "invocation:g7-reconcile", "test")
        assessment = {
            "contract": ASSESSMENT_CONTRACT,
            "semantic_status": "COMPATIBLE",
            "admission_recommendation": "RECOMMEND",
            "rationale": "G7 lock fixture",
        }
        reconciled = reconcile_candidate(root, candidate, activation, assessment)
        self.assertEqual(reconciled["status"], "PASS")
        self.authorize_scope(root, "admission")
        base = first_admission_base(root)
        plan = {
            "contract": ADMISSION_PLAN_CONTRACT,
            "expected_base_sha256": sha256_bytes(jcs(base)),
            "reuse_record_ids": [],
            "record_updates": [],
            "new_records": [
                {
                    "id": "record:g7",
                    "kind": "proposition",
                    "lifecycle": "current",
                    "data": {
                        "statement": "G7",
                        "proposition_kind": "claim",
                        "epistemic_role": "asserted",
                    },
                }
            ],
            "new_relations": [],
        }
        return td, root, Path(reconciled["disposition_path"]), make_explicit_activation(
            "steward:default", "invocation:g7-admit", "test"
        ), plan

    def test_section14_inventory_is_complete(self):
        self.assertEqual(set(self.SECTION14_CASES), set(range(1, 26)))
        for case, method in self.SECTION14_CASES.items():
            with self.subTest(case=case, method=method):
                self.assertTrue(callable(getattr(self, method, None)))

    def test_case01_valid_canonical_state_never_enters_recovery(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            canonical = root / "project-knowledge" / "canonical"
            canonical.joinpath("pems2.jcs.json").write_bytes(planned.recipe_candidate.candidate_pems_bytes)
            canonical.joinpath("cove1.jcs.json").write_bytes(planned.recipe_candidate.candidate_cove_bytes)
            before = self.auxiliary_state(root)
            result = self.apply(root, planned)
            self.assertEqual((result["status"], result["outcome"]), ("FAIL", "RECOVERY_NOT_REQUIRED"))
            self.assertFalse(self.recovery_namespace(root).exists())
            self.assertEqual(self.auxiliary_state(root), before)

    def test_case02_prestate_hash_and_blob_drift_fail_before_mutation(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            pems_path = root / "project-knowledge" / "canonical" / "pems2.jcs.json"
            pems_path.write_bytes(pems_path.read_bytes() + b" ")
            result = self.apply(root, planned)
            self.assertEqual(result["outcome"], "CANONICAL_PRESTATE_MISMATCH")
            self.assertFalse(self.recovery_namespace(root).exists())

        td, root = self.project()
        with td:
            planned = self.planned(root)
            changed = copy.deepcopy(planned.plan)
            changed["prestate"]["pems_git_blob"] = self.mutate_hex(changed["prestate"]["pems_git_blob"])
            changed_bytes = jcs(changed)
            result = self.apply(root, planned, plan_bytes=changed_bytes, approval_bytes=self.approval_for(changed))
            self.assertEqual(result["outcome"], "CANONICAL_PRESTATE_MISMATCH")
            self.assertFalse(self.recovery_namespace(root).exists())

    def test_case03_wrong_or_missing_protected_root_fails(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            wrong = self.approval_for(planned.plan, root_id="operator:delegate")
            result = self.apply(root, planned, approval_bytes=wrong)
            self.assertEqual(result["outcome"], "ROOT_RECOVERY_APPROVAL_MISMATCH")
            self.assertFalse(self.recovery_namespace(root).exists())

        td, root = self.project(establish_root=False)
        with td:
            planned = self.planned(root)
            result = self.apply(root, planned)
            self.assertEqual(result["outcome"], "ROOT_RECOVERY_APPROVAL_REQUIRED")
            self.assertFalse(self.recovery_namespace(root).exists())

    def test_case04_approval_replay_against_another_generation_fails(self):
        td, root = self.project()
        with td:
            first = self.planned(root, "g7-generation-a")
            replayed = self.approval_for(first.plan)
            second = self.planned(root, "g7-generation-b")
            result = self.apply(root, second, approval_bytes=replayed)
            self.assertEqual(result["outcome"], "ROOT_RECOVERY_APPROVAL_MISMATCH")
            self.assertFalse(self.recovery_namespace(root).exists())

    def test_case05_any_consequential_plan_or_implementation_identity_drift_fails(self):
        mutations = {
            "plan": lambda p: p["canonical_paths"].__setitem__("pems", "other"),
            "recipe": lambda p: p.__setitem__("recipe_id", "other-recipe/1"),
            "candidate": lambda p: p["candidate"].__setitem__("pems_sha256", self.mutate_hex(p["candidate"]["pems_sha256"])),
            "executor": lambda p: p["implementation_closure"]["recovery_executor"].__setitem__("sha256", self.mutate_hex(p["implementation_closure"]["recovery_executor"]["sha256"])),
            "schema": lambda p: p["implementation_closure"]["schema"].__setitem__("sha256", self.mutate_hex(p["implementation_closure"]["schema"]["sha256"])),
            "validator": lambda p: p["implementation_closure"]["validator"].__setitem__("sha256", self.mutate_hex(p["implementation_closure"]["validator"]["sha256"])),
            "serializer": lambda p: p["implementation_closure"]["serializer"].__setitem__("sha256", self.mutate_hex(p["implementation_closure"]["serializer"]["sha256"])),
            "codec": lambda p: p["implementation_closure"]["cove_codec"].__setitem__("sha256", self.mutate_hex(p["implementation_closure"]["cove_codec"]["sha256"])),
            "dependency": lambda p: p["implementation_closure"]["behavior_dependencies"][0].__setitem__("sha256", self.mutate_hex(p["implementation_closure"]["behavior_dependencies"][0]["sha256"])),
        }
        allowed = {"RECOVERY_PLAN_MISMATCH", "MIGRATION_RECIPE_MISMATCH", "EXECUTOR_CLOSURE_MISMATCH"}
        for label, mutate in mutations.items():
            td, root = self.project()
            with td, self.subTest(identity=label):
                planned = self.planned(root)
                changed = copy.deepcopy(planned.plan)
                mutate(changed)
                result = self.apply(root, planned, plan_bytes=jcs(changed), approval_bytes=self.approval_for(changed))
                self.assertIn(result["outcome"], allowed)
                self.assertFalse(self.recovery_namespace(root).exists())

    def test_case06_semantic_delta_beyond_discriminator_insertion_is_unsupported(self):
        td, root = self.project()
        with td:
            source = self.valid_pems()
            source.pop("semantic")
            source["inferred_repair"] = True
            pems = jcs(source)
            cove = jcs(encode_cove(source))
            with self.assertRaises(ContractError) as caught:
                build_mode_a_recovery_plan(
                    pems,
                    cove,
                    project_root=root,
                    expected_project_id="example-project",
                    generation="g7-extra-delta",
                    expected_prestate_pems_sha256=sha256_bytes(pems),
                    expected_prestate_cove_sha256=sha256_bytes(cove),
                    expected_prestate_pems_git_blob=git_blob_sha1(pems),
                    expected_prestate_cove_git_blob=git_blob_sha1(cove),
                    selected_evidence_paths=(),
                    behavior_dependency_paths=self.BEHAVIOR_DEPENDENCIES,
                    package_root=ROOT,
                )
            self.assertEqual(caught.exception.code, "UNSUPPORTED_CANONICAL_DAMAGE")
            self.assertFalse(self.recovery_namespace(root).exists())

    def test_case07_prestate_cove_disagreement_is_ineligible(self):
        td, root = self.project()
        with td:
            pems, _ = self.prestate()
            wrong = {"project_id": "different", "records": [], "relations": []}
            cove = jcs(encode_cove(wrong))
            with self.assertRaises(ContractError) as caught:
                build_mode_a_recovery_plan(
                    pems,
                    cove,
                    project_root=root,
                    expected_project_id="example-project",
                    generation="g7-cove-mismatch",
                    expected_prestate_pems_sha256=sha256_bytes(pems),
                    expected_prestate_cove_sha256=sha256_bytes(cove),
                    expected_prestate_pems_git_blob=git_blob_sha1(pems),
                    expected_prestate_cove_git_blob=git_blob_sha1(cove),
                    selected_evidence_paths=(),
                    behavior_dependency_paths=self.BEHAVIOR_DEPENDENCIES,
                    package_root=ROOT,
                )
            self.assertEqual(caught.exception.code, "COVE_PRESTATE_MISMATCH")

    def test_case08_missing_or_malformed_recovered_provenance_blocks_verification(self):
        for mode in ("missing", "malformed"):
            td, root = self.project()
            with td, self.subTest(mode=mode):
                planned = self.planned(root)
                self.assertEqual(self.apply(root, planned)["outcome"], "RECOVERED")
                completion = self.generation_root(root) / "completion.json"
                if mode == "missing":
                    completion.unlink()
                else:
                    completion.write_bytes(b"{")
                result = verify_storage(root, ROOT)
                self.assertEqual(result["status"], "FAIL")
                self.assertTrue(result["outcome"].startswith("RECOVERY_PROVENANCE_"))

    def test_case09_recovery_does_not_create_or_rewrite_ordinary_receipts(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            receipts = root / "project-knowledge" / "admission" / "receipts"
            before = {p.name: p.read_bytes() for p in receipts.glob("*.json")}
            self.assertEqual(self.apply(root, planned)["outcome"], "RECOVERED")
            after = {p.name: p.read_bytes() for p in receipts.glob("*.json")}
            self.assertEqual(after, before)
            self.assertEqual(set(after), {"historical.json"})

    def test_case10_recovery_does_not_mutate_r7_r8_authority_state(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            before = self.auxiliary_state(root)
            self.assertEqual(self.apply(root, planned)["outcome"], "RECOVERED")
            after = self.auxiliary_state(root)
            self.assertEqual(after, before)

    def test_case11_crash_before_pems_publication_keeps_exact_prestate(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            before = self.canonical_bytes(root)
            real_replace = os.replace
            calls = {"count": 0}

            def crash_first_replace(src, dst):
                calls["count"] += 1
                if calls["count"] == 1:
                    raise KeyboardInterrupt("simulated crash before PEMS publication")
                return real_replace(src, dst)

            with self.assertRaises(KeyboardInterrupt):
                with patch("ril_canonical_store.os.replace", side_effect=crash_first_replace):
                    self.apply(root, planned)
            self.assertEqual(self.canonical_bytes(root), before)
            self.assertTrue(self.barrier_path(root).is_file())
            self.assertEqual(verify_storage(root, ROOT)["outcome"], "CANONICAL_RECOVERY_ACTIVE")
            self.assertEqual(self.apply(root, planned)["outcome"], "RECOVERED")

    def test_case12_crash_between_pems_and_cove_is_barrier_blocked_and_exactly_resumable(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            before_pems, before_cove = self.canonical_bytes(root)
            self.crash_between_pair_members(root, planned)
            now_pems, now_cove = self.canonical_bytes(root)
            self.assertNotEqual(now_pems, before_pems)
            self.assertEqual(now_pems, planned.recipe_candidate.candidate_pems_bytes)
            self.assertEqual(now_cove, before_cove)
            self.assertTrue(self.barrier_path(root).exists())
            self.assertEqual(verify_storage(root, ROOT)["outcome"], "CANONICAL_RECOVERY_ACTIVE")
            resumed = self.apply(root, planned)
            self.assertEqual(resumed["outcome"], "RECOVERED")
            self.assertEqual(
                self.canonical_bytes(root),
                (planned.recipe_candidate.candidate_pems_bytes, planned.recipe_candidate.candidate_cove_bytes),
            )

    def test_case13_crash_after_pair_publication_before_completion_remains_blocked(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            import ril_canonical_recovery_executor as executor

            real_write = executor._write_immutable

            def crash_completion(path, data):
                if path.name == "completion.json":
                    raise KeyboardInterrupt("simulated crash before completion creation")
                return real_write(path, data)

            with self.assertRaises(KeyboardInterrupt):
                with patch("ril_canonical_recovery_executor._write_immutable", side_effect=crash_completion):
                    self.apply(root, planned)
            self.assertEqual(
                self.canonical_bytes(root),
                (planned.recipe_candidate.candidate_pems_bytes, planned.recipe_candidate.candidate_cove_bytes),
            )
            self.assertTrue(self.barrier_path(root).exists())
            self.assertFalse((self.generation_root(root) / "completion.json").exists())
            self.assertEqual(verify_storage(root, ROOT)["outcome"], "CANONICAL_RECOVERY_ACTIVE")
            self.assertEqual(self.apply(root, planned)["outcome"], "RECOVERED")

    def test_case14_crash_after_completion_before_barrier_clear_finishes_only_same_transaction(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            original_clear = CanonicalStoreSession.clear_recovery_barrier
            calls = {"count": 0}

            def crash_clear(store, expected):
                calls["count"] += 1
                if calls["count"] == 1:
                    raise KeyboardInterrupt("simulated crash after completion")
                return original_clear(store, expected)

            with self.assertRaises(KeyboardInterrupt):
                with patch.object(CanonicalStoreSession, "clear_recovery_barrier", crash_clear):
                    self.apply(root, planned)
            self.assertTrue((self.generation_root(root) / "completion.json").is_file())
            self.assertTrue(self.barrier_path(root).is_file())

            changed_approval = self.approval_for(planned.plan, evidence={"attempt": "different"})
            conflict = self.apply(root, planned, approval_bytes=changed_approval)
            self.assertEqual(conflict["outcome"], "RECOVERY_CONFLICT")
            self.assertTrue(self.barrier_path(root).is_file())

            resumed = self.apply(root, planned)
            self.assertEqual(resumed["outcome"], "RECOVERED")
            self.assertFalse(self.barrier_path(root).exists())

    def test_case15_publication_failure_rolls_back_exact_raw_prestate(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            before = self.canonical_bytes(root)
            real_replace = os.replace
            calls = {"count": 0}

            def fail_second_replace(src, dst):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("fixture COVE publication failure")
                return real_replace(src, dst)

            with patch("ril_canonical_store.os.replace", side_effect=fail_second_replace):
                result = self.apply(root, planned)
            self.assertEqual(result["outcome"], "RECOVERY_PUBLICATION_FAILED_ROLLED_BACK")
            self.assertEqual(self.canonical_bytes(root), before)
            self.assertFalse(self.barrier_path(root).exists())

    def test_case16_rollback_hash_mismatch_leaves_indeterminate_barrier(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            real_replace = os.replace
            calls = {"count": 0}

            def corrupt_then_fail_second_replace(src, dst):
                calls["count"] += 1
                if calls["count"] == 2:
                    preserved = self.generation_root(root) / "prestate" / "pems2.raw"
                    preserved.write_bytes(b"corrupted-prestate")
                    raise OSError("fixture publication failure with corrupted rollback source")
                return real_replace(src, dst)

            with patch("ril_canonical_store.os.replace", side_effect=corrupt_then_fail_second_replace):
                result = self.apply(root, planned)
            self.assertEqual(result["outcome"], "CANONICAL_RECOVERY_INDETERMINATE")
            self.assertTrue(self.barrier_path(root).is_file())
            self.assertEqual(verify_storage(root, ROOT)["outcome"], "CANONICAL_RECOVERY_ACTIVE")

    def test_case17_exact_successful_retry_is_no_change_only_for_identical_evidence(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            self.assertEqual(self.apply(root, planned)["outcome"], "RECOVERED")
            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            retry = self.apply(root, planned)
            after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual((retry["status"], retry["outcome"]), ("PASS", "NO_CHANGE"))
            self.assertEqual(after, before)

            different_approval = self.approval_for(planned.plan, evidence={"retry": "different"})
            conflict = self.apply(root, planned, approval_bytes=different_approval)
            self.assertEqual(conflict["outcome"], "RECOVERY_CONFLICT")

    def test_case18_same_generation_with_different_plan_or_poststate_conflicts(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            self.assertEqual(self.apply(root, planned)["outcome"], "RECOVERED")
            changed = copy.deepcopy(planned.plan)
            changed["candidate"]["pems_sha256"] = self.mutate_hex(changed["candidate"]["pems_sha256"])
            changed_bytes = jcs(changed)
            conflict = self.apply(root, planned, plan_bytes=changed_bytes, approval_bytes=self.approval_for(changed))
            self.assertEqual(conflict["outcome"], "RECOVERY_CONFLICT")

    def test_case19_corrupted_preserved_evidence_blocks_resume(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            self.crash_between_pair_members(root, planned)
            copied = self.generation_root(root) / "evidence" / "project-knowledge" / "evidence" / "historical.json"
            self.assertTrue(copied.is_file())
            copied.write_bytes(b'{"historical":"corrupted"}')
            result = self.apply(root, planned)
            self.assertIn(result["outcome"], {"RECOVERY_CONFLICT", "CANONICAL_RECOVERY_INDETERMINATE"})
            self.assertTrue(self.barrier_path(root).is_file())

    def test_case20_shared_reader_lock_blocks_recovery(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            with shared_canonical_store(root):
                result = self.apply(root, planned)
            self.assertEqual(result["outcome"], "CANONICAL_RECOVERY_BUSY")
            self.assertFalse(self.recovery_namespace(root).exists())

    def test_case21_exclusive_recovery_lock_blocks_new_reader(self):
        td, root = self.project()
        with td:
            with exclusive_canonical_store(root):
                result = verify_storage(root, ROOT)
            self.assertEqual((result["status"], result["outcome"]), ("FAIL", "CANONICAL_RECOVERY_BUSY"))

    def test_case22_crash_releases_lock_but_barrier_still_blocks_readers(self):
        td, root = self.project()
        with td:
            planned = self.planned(root)
            self.crash_between_pair_members(root, planned)
            with exclusive_canonical_store(root):
                pass
            self.assertTrue(self.barrier_path(root).is_file())
            self.assertEqual(verify_storage(root, ROOT)["outcome"], "CANONICAL_RECOVERY_ACTIVE")

    def test_case23_r13_and_recovery_share_exclusive_mutation_boundary(self):
        td, root, disposition, activation, plan = self.admission_ready()
        with td:
            with exclusive_canonical_store(root):
                result = admit(root, disposition, activation, plan)
            self.assertEqual((result["status"], result["outcome"]), ("FAIL", "CANONICAL_RECOVERY_BUSY"))
            self.assertFalse((root / "project-knowledge" / "canonical").exists())

    def test_case24_static_package_scan_rejects_direct_fixed_canonical_reader(self):
        forbidden = ("pems2.jcs.json", "cove1.jcs.json", "project-knowledge/canonical")
        allowed = {Path("runtime/ril_canonical_store.py")}
        offenders: list[str] = []
        for source_root in (ROOT / "runtime", ROOT / "context_packaging"):
            for path in sorted(source_root.rglob("*.py")):
                rel = path.relative_to(ROOT)
                if rel in allowed:
                    continue
                text = path.read_text(encoding="utf-8")
                if any(token in text for token in forbidden):
                    offenders.append(rel.as_posix())
        self.assertEqual(offenders, [])

    def _p3_valid_doc(self) -> dict:
        validator = ROOT / "backends" / "pems-cove" / "validate_pems2_contract.py"
        spec = importlib.util.spec_from_file_location("g7_p3_validator", validator)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        valid, _invalid = module.structural_smoke_documents()
        return copy.deepcopy(valid)

    def _raw_sha(self, data: bytes) -> str:
        return "sha256:" + hashlib.sha256(data).hexdigest()

    def _blob_sha(self, data: bytes) -> str:
        return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

    def _p3_binding(self, data: bytes) -> dict:
        return {
            "contract": "reasoning-distiller-context-source-binding/1",
            "source_class": "canonical_state",
            "logical_namespace": "project:test",
            "logical_source_id": "canonical",
            "project_id": "test",
            "backend_type": "pems-cove",
            "backend_contract": "project-canonical-backend/1",
            "backend_config_identity": "config:g7",
            "immutable_snapshot_id": "snapshot:g7",
            "pems_semantic": "pems/2",
            "serializer": "jcs/1",
            "pems_sha256": self._raw_sha(data),
            "standing_evidence": [
                {
                    "contract": "canonical-standing-evidence/1",
                    "immutable_snapshot_id": "standing:g7",
                    "raw_sha256": self._raw_sha(b"standing"),
                }
            ],
        }

    def _p3_profile(self) -> dict:
        descriptor = ROOT / "protocols" / "rgp" / "pems2-context-closure-v1.json"
        raw = descriptor.read_bytes()
        return {
            "contract": "reasoning-distiller-context-profile/1",
            "knowledge": {
                "required": True,
                "canonical_slot_id": "canonical",
                "selector_kinds": ["record_id", "relation_id"],
                "empty_result": "allow",
                "snapshot_multiplicity": "single",
                "closure_descriptor": {
                    "contract": "reasoning-distiller-pems2-closure-descriptor/1",
                    "semantic": "pems/2",
                    "immutable_snapshot_id": "git-blob:" + self._blob_sha(raw),
                    "raw_sha256": self._raw_sha(raw),
                },
            },
            "limits": {
                "projection": {
                    "max_records": 100,
                    "max_relations": 100,
                    "max_depth": 20,
                    "max_bytes": 1_000_000,
                }
            },
        }

    def test_case25_context_snapshot_acquisition_blocks_during_recovery_and_downstream_is_immutable(self):
        root = Path(tempfile.mkdtemp())
        canonical = root / "project-knowledge" / "canonical"
        canonical.mkdir(parents=True)
        doc = self._p3_valid_doc()
        data = jcs(doc)
        (canonical / "pems2.jcs.json").write_bytes(data)
        (canonical / "cove1.jcs.json").write_bytes(jcs(encode_cove(doc)))

        with shared_canonical_store(root) as store:
            snapshot = store.snapshot()
        self.assertEqual(snapshot.state, "PRESENT")
        captured = snapshot.pems_bytes
        self.assertEqual(captured, data)

        barrier = root / "project-knowledge" / "recovery" / "canonical-pems-cove" / "active.json"
        barrier.parent.mkdir(parents=True)
        barrier.write_bytes(jcs({"contract": BARRIER_CONTRACT, "transaction_state": "ACTIVE"}))
        with self.assertRaises(ContractError) as caught:
            with shared_canonical_store(root) as store:
                store.snapshot()
        self.assertEqual(caught.exception.code, "CANONICAL_RECOVERY_ACTIVE")

        self.assertIsNotNone(captured)
        binding = self._p3_binding(captured)
        snapshot_ref = {k: copy.deepcopy(v) for k, v in binding.items() if k not in {"contract", "repository_relationship"}}
        request = {
            "contract": "reasoning-distiller-context-pack-request/1",
            "knowledge_selection": {
                "snapshots": [
                    {
                        "canonical_snapshot_ref": snapshot_ref,
                        "record_ids": ["pems:proposition:a"],
                        "relation_ids": [],
                    }
                ]
            },
        }
        result = project_pems(request, self._p3_profile(), [ResolvedSource(binding, captured)])
        self.assertTrue(result.ok)
        self.assertEqual(result.items[0].canonical_snapshot_ref, snapshot_ref)

        canonical.joinpath("pems2.jcs.json").write_bytes(b"corrupted-live-canon-after-snapshot")
        repeated = project_pems(request, self._p3_profile(), [ResolvedSource(binding, captured)])
        self.assertTrue(repeated.ok)
        self.assertEqual(repeated.items, result.items)


if __name__ == "__main__":
    unittest.main()
