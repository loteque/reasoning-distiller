from __future__ import annotations

import inspect
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import encode_cove, jcs, sha256_bytes  # noqa: E402
from ril_canonical_recovery_planner import (  # noqa: E402
    BARRIER_CONTRACT,
    CANONICAL_COVE_PATH,
    CANONICAL_PEMS_PATH,
    PLAN_CONTRACT,
    RECOVERY_EXECUTOR_PATH,
    TERMINAL_PROVENANCE_CLASS,
    build_mode_a_recovery_plan,
)
from ril_canonical_recovery_recipe import RECIPE_ID, git_blob_sha1  # noqa: E402
from ril_mutation import ContractError  # noqa: E402


class CanonicalRecoveryReadOnlyPlannerTests(unittest.TestCase):
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
                        "summary": "G4 read-only planner fixture.",
                    },
                }
            ],
            "relations": [],
        }

    def prestate(self) -> tuple[bytes, bytes]:
        source = self.valid_pems()
        source.pop("semantic")
        return jcs(source), jcs(encode_cove(source))

    def project_root(self) -> Path:
        root = Path(tempfile.mkdtemp())
        evidence = root / "project-knowledge" / "admission" / "receipts"
        evidence.mkdir(parents=True)
        (evidence / "historical.json").write_bytes(b'{"historical":true}')
        (evidence / "secondary.json").write_bytes(b'{"secondary":true}')
        return root

    def package_fixture(self) -> Path:
        root = Path(tempfile.mkdtemp())
        copies = [
            "backends/pems-cove/validate_pems2_contract.py",
            "backends/pems-cove/pems-v2.schema.json",
            "runtime/ril_admission.py",
            "runtime/ril_canonical_recovery_planner.py",
            "runtime/ril_canonical_store.py",
            "runtime/ril_mutation.py",
            "packaging/package-build.json",
            "docs/operations/RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md",
            "docs/operations/RIL_STORAGE_VERIFICATION_CONTRACT.md",
        ]
        for relative in copies:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        executor = root / RECOVERY_EXECUTOR_PATH
        executor.parent.mkdir(parents=True, exist_ok=True)
        executor.write_text(
            "from ril_mutation import ContractError\n"
            "def apply_recovery_placeholder_for_g4_fixture():\n"
            "    raise ContractError('ROOT_RECOVERY_APPROVAL_REQUIRED', 'fixture only')\n",
            encoding="utf-8",
        )
        return root

    def build(self, *, project_root: Path | None = None, package_root: Path | None = None, **overrides):
        pems_bytes, cove_bytes = self.prestate()
        project = project_root or self.project_root()
        package = package_root or self.package_fixture()
        kwargs = {
            "project_root": project,
            "expected_project_id": "example-project",
            "generation": "fixture-generation-0001",
            "expected_prestate_pems_sha256": sha256_bytes(pems_bytes),
            "expected_prestate_cove_sha256": sha256_bytes(cove_bytes),
            "expected_prestate_pems_git_blob": git_blob_sha1(pems_bytes),
            "expected_prestate_cove_git_blob": git_blob_sha1(cove_bytes),
            "selected_evidence_paths": (
                "project-knowledge/admission/receipts/historical.json",
                "project-knowledge/admission/receipts/secondary.json",
            ),
            "behavior_dependency_paths": ("runtime/ril_mutation.py",),
            "package_root": package,
        }
        kwargs.update(overrides)
        return build_mode_a_recovery_plan(pems_bytes, cove_bytes, **kwargs)

    def assert_code(self, code: str, fn) -> ContractError:
        with self.assertRaises(ContractError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def file_snapshot(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def test_planner_emits_one_canonical_plan_with_complete_bound_inputs(self):
        result = self.build()
        plan = result.plan

        self.assertEqual(plan["contract"], PLAN_CONTRACT)
        self.assertEqual(plan["project_id"], "example-project")
        self.assertEqual(plan["generation"], "fixture-generation-0001")
        self.assertEqual(plan["canonical_paths"], {"pems": CANONICAL_PEMS_PATH, "cove": CANONICAL_COVE_PATH})
        self.assertEqual(plan["mode"], "A")
        self.assertEqual(plan["recipe_id"], RECIPE_ID)
        self.assertEqual(plan["expected_terminal_provenance_class"], TERMINAL_PROVENANCE_CLASS)
        self.assertEqual(plan["expected_barrier_identity"]["contract"], BARRIER_CONTRACT)
        self.assertEqual(plan["expected_barrier_identity"]["transaction_state"], "ACTIVE")

        self.assertEqual(plan["candidate"]["pems_sha256"], result.recipe_candidate.candidate_pems_sha256)
        self.assertEqual(plan["candidate"]["cove_sha256"], result.recipe_candidate.candidate_cove_sha256)
        self.assertEqual(plan["equivalence_proof_sha256"], result.recipe_candidate.equivalence_proof_sha256)
        self.assertEqual(plan["preserved_evidence_inventory_sha256"], result.preserved_evidence_inventory_sha256)
        self.assertEqual(result.plan_bytes, jcs(plan))
        self.assertEqual(result.plan_sha256, sha256_bytes(result.plan_bytes))
        self.assertFalse(result.plan_bytes.endswith(b"\n"))

        closure = plan["implementation_closure"]
        self.assertEqual(
            set(closure),
            {
                "recipe",
                "schema",
                "validator",
                "normalizer",
                "serializer",
                "cove_codec",
                "planner",
                "canonical_store",
                "recovery_executor",
                "behavior_dependencies",
                "package_build",
            },
        )
        self.assertEqual(closure["recovery_executor"]["path"], RECOVERY_EXECUTOR_PATH)
        self.assertEqual(
            closure["recipe"]["sha256"],
            result.recipe_candidate.equivalence_proof["identities"]["recipe"]["sha256"],
        )
        for role, identity in closure.items():
            if role == "behavior_dependencies":
                for dependency in identity:
                    self.assertEqual(len(dependency["sha256"]), 64)
                    self.assertEqual(len(dependency["git_blob"]), 40)
            else:
                self.assertEqual(len(identity["sha256"]), 64)
                self.assertEqual(len(identity["git_blob"]), 40)

        self.assertEqual(plan["recovery_contract_identity"]["path"], "docs/operations/RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md")
        self.assertEqual(plan["r14_v2_contract_identity"]["path"], "docs/operations/RIL_STORAGE_VERIFICATION_CONTRACT.md")
        self.assertTrue(plan["runtime_identity"]["python_version"])
        self.assertTrue(plan["runtime_identity"]["jsonschema_version"])

    def test_inventory_contains_exact_prestate_and_selected_evidence(self):
        result = self.build()
        entries = result.preserved_evidence_inventory["entries"]
        paths = [entry["path"] for entry in entries]
        self.assertEqual(
            paths,
            sorted(
                [
                    CANONICAL_PEMS_PATH,
                    CANONICAL_COVE_PATH,
                    "project-knowledge/admission/receipts/historical.json",
                    "project-knowledge/admission/receipts/secondary.json",
                ]
            ),
        )
        self.assertEqual(result.preserved_evidence_inventory_bytes, jcs(result.preserved_evidence_inventory))
        self.assertEqual(
            result.preserved_evidence_inventory_sha256,
            sha256_bytes(result.preserved_evidence_inventory_bytes),
        )
        self.assertTrue(all(entry["byte_length"] >= 0 for entry in entries))
        self.assertTrue(all(len(entry["sha256"]) == 64 for entry in entries))
        self.assertTrue(all(len(entry["git_blob"]) == 40 for entry in entries))

    def test_selected_evidence_order_does_not_change_plan_identity(self):
        project = self.project_root()
        package = self.package_fixture()
        first = self.build(project_root=project, package_root=package)
        second = self.build(
            project_root=project,
            package_root=package,
            selected_evidence_paths=(
                "project-knowledge/admission/receipts/secondary.json",
                "project-knowledge/admission/receipts/historical.json",
            ),
        )
        self.assertEqual(first.preserved_evidence_inventory_bytes, second.preserved_evidence_inventory_bytes)
        self.assertEqual(first.plan_bytes, second.plan_bytes)
        self.assertEqual(first.plan_sha256, second.plan_sha256)

    def test_planning_is_byte_for_byte_read_only_for_project_state(self):
        project = self.project_root()
        package = self.package_fixture()
        before = self.file_snapshot(project)
        self.build(project_root=project, package_root=package)
        after = self.file_snapshot(project)
        self.assertEqual(before, after)
        self.assertFalse((project / "project-knowledge/recovery").exists())
        self.assertFalse((project / "project-knowledge/canonical").exists())

    def test_missing_future_executor_blocks_plan_instead_of_inventing_identity(self):
        project = self.project_root()
        package = self.package_fixture()
        (package / RECOVERY_EXECUTOR_PATH).unlink()
        self.assert_code(
            "EXECUTOR_CLOSURE_MISMATCH",
            lambda: self.build(project_root=project, package_root=package),
        )

    def test_behavior_dependency_closure_is_required_and_must_not_alias_roles(self):
        project = self.project_root()
        package = self.package_fixture()
        self.assert_code(
            "EXECUTOR_CLOSURE_MISMATCH",
            lambda: self.build(project_root=project, package_root=package, behavior_dependency_paths=()),
        )
        self.assert_code(
            "EXECUTOR_CLOSURE_MISMATCH",
            lambda: self.build(
                project_root=project,
                package_root=package,
                behavior_dependency_paths=("runtime/ril_canonical_store.py",),
            ),
        )

    def test_prestate_cove_witness_is_verified_by_closed_recipe(self):
        pems_bytes, _ = self.prestate()
        wrong = {"project_id": "different", "records": [], "relations": []}
        cove_bytes = jcs(encode_cove(wrong))
        project = self.project_root()
        package = self.package_fixture()
        self.assert_code(
            "COVE_PRESTATE_MISMATCH",
            lambda: build_mode_a_recovery_plan(
                pems_bytes,
                cove_bytes,
                project_root=project,
                expected_project_id="example-project",
                generation="fixture-generation-0001",
                expected_prestate_pems_sha256=sha256_bytes(pems_bytes),
                expected_prestate_cove_sha256=sha256_bytes(cove_bytes),
                expected_prestate_pems_git_blob=git_blob_sha1(pems_bytes),
                expected_prestate_cove_git_blob=git_blob_sha1(cove_bytes),
                behavior_dependency_paths=("runtime/ril_mutation.py",),
                package_root=package,
            ),
        )

    def test_plan_digest_changes_when_generation_or_evidence_changes(self):
        project = self.project_root()
        package = self.package_fixture()
        first = self.build(project_root=project, package_root=package)
        second = self.build(
            project_root=project,
            package_root=package,
            generation="fixture-generation-0002",
        )
        self.assertNotEqual(first.plan_sha256, second.plan_sha256)

        evidence = project / "project-knowledge/admission/receipts/historical.json"
        evidence.write_bytes(b'{"historical":"changed"}')
        third = self.build(project_root=project, package_root=package)
        self.assertNotEqual(first.preserved_evidence_inventory_sha256, third.preserved_evidence_inventory_sha256)
        self.assertNotEqual(first.plan_sha256, third.plan_sha256)

    def test_inventory_rejects_duplicates_unsafe_paths_and_canonical_pair_aliases(self):
        project = self.project_root()
        package = self.package_fixture()
        self.assert_code(
            "RECOVERY_PLAN_MISMATCH",
            lambda: self.build(
                project_root=project,
                package_root=package,
                selected_evidence_paths=(
                    "project-knowledge/admission/receipts/historical.json",
                    "project-knowledge/admission/receipts/historical.json",
                ),
            ),
        )
        self.assert_code(
            "RECOVERY_PLAN_MISMATCH",
            lambda: self.build(
                project_root=project,
                package_root=package,
                selected_evidence_paths=("../outside.json",),
            ),
        )
        self.assert_code(
            "RECOVERY_PLAN_MISMATCH",
            lambda: self.build(
                project_root=project,
                package_root=package,
                selected_evidence_paths=(CANONICAL_PEMS_PATH,),
            ),
        )

    def test_planner_surface_contains_no_apply_approval_or_authority_input(self):
        params = set(inspect.signature(build_mode_a_recovery_plan).parameters)
        self.assertNotIn("approval", params)
        self.assertNotIn("activation", params)
        self.assertNotIn("authority", params)
        self.assertNotIn("apply", params)
        self.assertNotIn("executor", params)
        self.assertIn("behavior_dependency_paths", params)
        self.assertFalse(any("callback" in name or "transform" in name or "dsl" in name for name in params))


if __name__ == "__main__":
    unittest.main()
