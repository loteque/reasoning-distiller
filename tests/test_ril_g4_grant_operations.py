#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

import ril_authority_grant as grant
import ril_grant_operations as g4
import ril_mutation as mut
import ril_operator_management as opm
import ril_operators as ops
import ril_roles as roles


class G4GrantOperationIntegrationTests(unittest.TestCase):
    def establish_root(self, project: Path, operator_id: str = "operator:root") -> None:
        planned = ops.plan_initial_operator(project, operator_id)
        self.assertEqual(planned["status"], "PASS")
        approval = ops.approve_initial_operator(planned["proposal"], operator_id)
        applied = ops.apply_initial_operator(project, planned["proposal"], approval)
        self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))

    def add_operator(self, project: Path, operator_id: str, capabilities: list[str]) -> None:
        planned = opm.plan_operator_change(project, "ADD_OPERATOR", operator_id, capabilities)
        self.assertEqual(planned["status"], "PASS")
        approval = opm.approve_operator_change(planned["proposal"], "operator:root")
        applied = opm.apply_operator_change(project, planned["proposal"], approval)
        self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))

    def make_grant(
        self,
        project: Path,
        store: Path,
        *,
        operation: str,
        targets: list[dict],
        constraints: list[dict],
        grantor: str = "operator:root",
        limit: int | None = 3,
    ) -> str:
        payload = grant.grant_payload(
            grantor=grantor,
            workflow="workflow:w1",
            operations=[operation],
            targets=targets,
            constraints=constraints,
            approvals_limit=limit,
        )
        auth = grant.make_grant_auth(payload, grantor)
        obj = grant.make_grant(payload, auth)
        return g4.create_authorized_grant(
            project,
            store,
            obj,
            workflow_contains_grant_scope=True,
        )

    def role_submission(self, role_ids: list[str]) -> dict:
        return {
            "contract": roles.SUBMISSION_CONTRACT,
            "mode": "incremental",
            "source": "g4-test",
            "scope": None,
            "roles": [
                {
                    "role_id": role_id,
                    "title": role_id.replace("-", " ").title(),
                    "description": "G4 test role",
                    "capabilities": ["project:test"],
                }
                for role_id in role_ids
            ],
        }

    def test_role_multi_target_one_of_grant_issues_and_applies(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project, store = root / "project", root / "grants"
            self.establish_root(project)
            planned = roles.plan_role_submission(project, self.role_submission(["alpha", "beta"]))
            self.assertEqual(planned["outcome"], "PLANNED")
            grant_ref = self.make_grant(
                project,
                store,
                operation=g4.ROLE_OPERATION_CLASS,
                targets=[{"field": "role_id", "match": "one-of", "values": ["alpha", "beta"]}],
                constraints=[
                    {"field": "mutation_kinds", "predicate": "subset-of", "values": ["ADD"]},
                    {"field": "role_ids", "predicate": "max-count", "value": 2},
                    {"field": "submission_mode", "predicate": "eq", "value": "incremental"},
                ],
            )
            issued = g4.issue_role_grant_approval(
                project,
                store,
                grant_ref,
                planned["proposal"],
                workflow_ref="workflow:w1",
                workflow_lifecycle="OPEN",
                workflow_condition="READY",
                workflow_contains_proposal=True,
                expected_grant_head=None,
            )
            applied = g4.apply_role_submission_with_authority(
                project, store, planned["proposal"], issued["approval"]
            )
            self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))
            state, _ = roles._load_role_state(project)
            self.assertEqual(state["roles"]["alpha"]["status"], "available")
            self.assertEqual(state["roles"]["beta"]["status"], "available")

    def test_role_proposal_with_one_ungranted_target_is_wholly_outside(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project, store = root / "project", root / "grants"
            self.establish_root(project)
            planned = roles.plan_role_submission(project, self.role_submission(["alpha", "mallory"]))
            grant_ref = self.make_grant(
                project,
                store,
                operation=g4.ROLE_OPERATION_CLASS,
                targets=[{"field": "role_id", "match": "one-of", "values": ["alpha"]}],
                constraints=[],
            )
            with self.assertRaises(grant.ContractError) as cm:
                g4.issue_role_grant_approval(
                    project, store, grant_ref, planned["proposal"],
                    workflow_ref="workflow:w1", workflow_lifecycle="OPEN",
                    workflow_condition="READY", workflow_contains_proposal=True,
                    expected_grant_head=None,
                )
            self.assertEqual(cm.exception.code, "OUTSIDE_GRANT")
            state, _ = roles._load_role_state(project)
            self.assertNotIn("alpha", state["roles"])
            self.assertNotIn("mallory", state["roles"])

    def test_role_constraints_are_optional_but_when_present_narrow_scope(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project, store = root / "project", root / "grants"
            self.establish_root(project)
            planned = roles.plan_role_submission(project, self.role_submission(["alpha", "beta"]))
            grant_ref = self.make_grant(
                project,
                store,
                operation=g4.ROLE_OPERATION_CLASS,
                targets=[{"field": "role_id", "match": "one-of", "values": ["alpha", "beta"]}],
                constraints=[{"field": "role_ids", "predicate": "max-count", "value": 1}],
            )
            with self.assertRaises(grant.ContractError) as cm:
                g4.issue_role_grant_approval(
                    project, store, grant_ref, planned["proposal"],
                    workflow_ref="workflow:w1", workflow_lifecycle="OPEN",
                    workflow_condition="READY", workflow_contains_proposal=True,
                    expected_grant_head=None,
                )
            self.assertEqual(cm.exception.code, "OUTSIDE_GRANT")

    def test_operator_disable_grant_issues_and_applies_without_fresh_assent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project, store = root / "project", root / "grants"
            self.establish_root(project)
            self.add_operator(project, "operator:bob", ["project:test"])
            planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")
            grant_ref = self.make_grant(
                project,
                store,
                operation=g4.OPERATOR_DISABLE_OPERATION_CLASS,
                targets=[{"field": "operator_id", "match": "exact", "value": "operator:bob"}],
                constraints=[{"field": "operation", "predicate": "eq", "value": "DISABLE_OPERATOR"}],
                limit=1,
            )
            issued = g4.issue_operator_disable_grant_approval(
                project, store, grant_ref, planned["proposal"],
                workflow_ref="workflow:w1", workflow_lifecycle="OPEN",
                workflow_condition="READY", workflow_contains_proposal=True,
                expected_grant_head=None,
            )
            applied = g4.apply_operator_change_with_authority(
                project, store, planned["proposal"], issued["approval"]
            )
            self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))
            state, _ = opm._load_registry(project)
            self.assertEqual(state["operators"]["operator:bob"]["status"], "disabled")
            self.assertEqual(grant.project_grant(store, grant_ref)["state"], "EXHAUSTED")

    def test_operator_disable_cannot_target_protected_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project, store = root / "project", root / "grants"
            self.establish_root(project)
            state, _ = opm._load_registry(project)
            proposal = mut.make_proposal(
                ops.DOMAIN,
                "DISABLE_OPERATOR",
                state,
                {"target_operator_id": "operator:root"},
            )
            grant_ref = self.make_grant(
                project,
                store,
                operation=g4.OPERATOR_DISABLE_OPERATION_CLASS,
                targets=[{"field": "operator_id", "match": "exact", "value": "operator:root"}],
                constraints=[{"field": "operation", "predicate": "eq", "value": "DISABLE_OPERATOR"}],
            )
            with self.assertRaises(grant.ContractError) as cm:
                g4.issue_operator_disable_grant_approval(
                    project, store, grant_ref, proposal,
                    workflow_ref="workflow:w1", workflow_lifecycle="OPEN",
                    workflow_condition="READY", workflow_contains_proposal=True,
                    expected_grant_head=None,
                )
            self.assertEqual(cm.exception.code, "ROOT_PROTECTED")
            self.assertEqual(grant.project_grant(store, grant_ref)["approvals_issued"], 0)

    def test_non_delegable_operator_operations_cannot_use_disable_grant(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project, store = root / "project", root / "grants"
            self.establish_root(project)
            grant_ref = self.make_grant(
                project,
                store,
                operation=g4.OPERATOR_DISABLE_OPERATION_CLASS,
                targets=[{"field": "operator_id", "match": "exact", "value": "operator:bob"}],
                constraints=[{"field": "operation", "predicate": "eq", "value": "DISABLE_OPERATOR"}],
            )
            for operation, caps in [
                ("ADD_OPERATOR", ["project:test"]),
                ("UPDATE_CAPABILITIES", ["project:test"]),
                ("REENABLE_OPERATOR", None),
            ]:
                if operation != "ADD_OPERATOR":
                    if "operator:bob" not in opm._load_registry(project)[0]["operators"]:
                        self.add_operator(project, "operator:bob", ["project:test"])
                planned = opm.plan_operator_change(project, operation, "operator:bob", caps)
                if planned["status"] != "PASS":
                    continue
                with self.assertRaises(grant.ContractError) as cm:
                    g4.issue_operator_disable_grant_approval(
                        project, store, grant_ref, planned["proposal"],
                        workflow_ref="workflow:w1", workflow_lifecycle="OPEN",
                        workflow_condition="READY", workflow_contains_proposal=True,
                        expected_grant_head=grant.project_grant(store, grant_ref)["normative_head"],
                    )
                self.assertEqual(cm.exception.code, "NON_DELEGABLE")

    def test_grant_creation_requires_operation_specific_grantor_capability(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project, store = root / "project", root / "grants"
            self.establish_root(project)
            self.add_operator(project, "operator:limited", ["project:test"])
            payload = grant.grant_payload(
                grantor="operator:limited",
                workflow="workflow:w1",
                operations=[g4.ROLE_OPERATION_CLASS],
                targets=[{"field": "role_id", "match": "exact", "value": "alpha"}],
                constraints=[],
            )
            obj = grant.make_grant(payload, grant.make_grant_auth(payload, "operator:limited"))
            with self.assertRaises(grant.ContractError) as cm:
                g4.create_authorized_grant(
                    project, store, obj, workflow_contains_grant_scope=True
                )
            self.assertEqual(cm.exception.code, "GRANTOR_NOT_AUTHORIZED")

    def test_apply_validates_immutable_grant_issuance_evidence_and_stale_basis(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project, store = root / "project", root / "grants"
            self.establish_root(project)
            self.add_operator(project, "operator:bob", ["project:test"])
            planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")
            grant_ref = self.make_grant(
                project,
                store,
                operation=g4.OPERATOR_DISABLE_OPERATION_CLASS,
                targets=[{"field": "operator_id", "match": "exact", "value": "operator:bob"}],
                constraints=[{"field": "operation", "predicate": "eq", "value": "DISABLE_OPERATOR"}],
            )
            fake = mut.make_grant_approval_v2(
                planned["proposal"], grant_ref, "authority-grant-event:missing"
            )
            bad = g4.apply_operator_change_with_authority(project, store, planned["proposal"], fake)
            self.assertEqual((bad["status"], bad["outcome"]), ("FAIL", "GRANT_ISSUANCE_EVIDENCE_MISSING"))

            issued = g4.issue_operator_disable_grant_approval(
                project, store, grant_ref, planned["proposal"],
                workflow_ref="workflow:w1", workflow_lifecycle="OPEN",
                workflow_condition="READY", workflow_contains_proposal=True,
                expected_grant_head=None,
            )
            direct = opm.approve_operator_change(planned["proposal"], "operator:root")
            changed = opm.apply_operator_change(project, planned["proposal"], direct)
            self.assertEqual(changed["outcome"], "APPLIED")
            stale = g4.apply_operator_change_with_authority(
                project, store, planned["proposal"], issued["approval"]
            )
            self.assertEqual((stale["status"], stale["outcome"]), ("FAIL", "STALE_BASIS"))


if __name__ == "__main__":
    unittest.main()
