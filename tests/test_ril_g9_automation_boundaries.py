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
import ril_human_agent as human
import ril_operator_management as opm
import ril_operators as ops
import ril_shared_orchestration as shared
import ril_workflow as wf


class G9AutomationBoundaryTests(unittest.TestCase):
    def establish_root(self, project: Path) -> None:
        planned = ops.plan_initial_operator(project, "operator:root")
        approval = ops.approve_initial_operator(planned["proposal"], "operator:root")
        applied = ops.apply_initial_operator(project, planned["proposal"], approval)
        self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))

    def add_operator(self, project: Path, operator_id: str) -> None:
        planned = opm.plan_operator_change(project, "ADD_OPERATOR", operator_id, ["project:test"])
        self.assertEqual(planned["status"], "PASS")
        approval = opm.approve_operator_change(planned["proposal"], "operator:root")
        applied = opm.apply_operator_change(project, planned["proposal"], approval)
        self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))

    def make_workflow(
        self,
        store: Path,
        operations: list[str],
        *,
        extra_intent: dict | None = None,
    ) -> str:
        intent = {"subject": "g9", "operations": list(operations)}
        if extra_intent:
            intent.update(extra_intent)
        payload = wf.workflow_payload(
            requester="operator:root",
            intent=intent,
            execution_mode="auto-advance",
        )
        auth = wf.make_workflow_auth(payload, "operator:root", confirmation="AUTO_ADVANCE")
        return wf.create_workflow(store, wf.make_workflow(payload, auth))

    def make_disable_grant(
        self,
        project: Path,
        store: Path,
        workflow_ref: str,
        *,
        limit: int | None = 2,
        target: str = "operator:bob",
    ) -> str:
        payload = grant.grant_payload(
            grantor="operator:root",
            workflow=workflow_ref,
            operations=[g4.OPERATOR_DISABLE_OPERATION_CLASS],
            targets=[{"field": "operator_id", "match": "exact", "value": target}],
            constraints=[{"field": "operation", "predicate": "eq", "value": "DISABLE_OPERATOR"}],
            approvals_limit=limit,
        )
        definition = grant.make_grant(payload, grant.make_grant_auth(payload, "operator:root"))
        return g4.create_authorized_grant(
            project,
            store,
            definition,
            workflow_contains_grant_scope=True,
        )

    def plan_disable(self, project: Path) -> dict:
        planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")
        self.assertEqual(planned["status"], "PASS")
        return planned["proposal"]

    def bob_status(self, project: Path) -> str:
        state, _ = opm._load_registry(project)
        return state["operators"]["operator:bob"]["status"]

    def test_materiality_pause_cannot_be_bypassed_by_in_scope_grant(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            grant_ref = self.make_disable_grant(project, gstore, workflow_ref)
            proposal = self.plan_disable(project)
            pause_ref = wf.pause_materiality(
                wstore,
                workflow_ref,
                {"fact": "material-risk"},
                expected_normative_head=None,
            )

            result = human.continue_auto_workflow(project, wstore, gstore, workflow_ref, proposal)

            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "MATERIALITY_PAUSE"))
            self.assertEqual(result["materiality_pause"], pause_ref)
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 0)
            self.assertEqual(self.bob_status(project), "active")

    def test_materiality_race_is_revalidated_before_grant_consumption(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            grant_ref = self.make_disable_grant(project, gstore, workflow_ref)
            proposal = self.plan_disable(project)
            raced = False

            def scope_with_race(definition, exact_proposal, operation_class, authority_fields):
                nonlocal raced
                self.assertEqual(operation_class, g4.OPERATOR_DISABLE_OPERATION_CLASS)
                if not raced:
                    wf.pause_materiality(
                        wstore,
                        workflow_ref,
                        {"fact": "arrived-after-first-read"},
                        expected_normative_head=None,
                    )
                    raced = True
                return True

            result = human.continue_auto_workflow(
                project,
                wstore,
                gstore,
                workflow_ref,
                proposal,
                workflow_scope_validator=scope_with_race,
            )

            self.assertTrue(raced)
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "MATERIALITY_PAUSE"))
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 0)
            self.assertEqual(self.bob_status(project), "active")

    def test_competing_normative_workflow_transition_fails_exact_head(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            grant_ref = self.make_disable_grant(project, gstore, workflow_ref)
            proposal = self.plan_disable(project)
            raced = False

            def scope_with_race(definition, exact_proposal, operation_class, authority_fields):
                nonlocal raced
                if not raced:
                    wf.record_attempt_failure(
                        wstore,
                        workflow_ref,
                        "competing-transition",
                        expected_normative_head=None,
                    )
                    raced = True
                return True

            result = human.continue_auto_workflow(
                project,
                wstore,
                gstore,
                workflow_ref,
                proposal,
                workflow_scope_validator=scope_with_race,
            )

            self.assertTrue(raced)
            self.assertEqual(
                (result["status"], result["outcome"]),
                ("STOPPED", "WORKFLOW_NORMATIVE_HEAD_CONFLICT"),
            )
            self.assertIsNone(result["expected_normative_head"])
            self.assertTrue(result["actual_normative_head"].startswith("workflow-event:"))
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 0)
            self.assertEqual(self.bob_status(project), "active")

    def test_missing_activation_evidence_and_unresolved_conditions_stop_automation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            grant_ref = self.make_disable_grant(project, gstore, workflow_ref)
            proposal = self.plan_disable(project)

            for condition in ("AWAITING_ACTIVATION", "AWAITING_EVIDENCE", "UNRESOLVED"):
                with self.subTest(condition=condition):
                    result = human.continue_auto_workflow(
                        project,
                        wstore,
                        gstore,
                        workflow_ref,
                        proposal,
                        workflow_condition_resolver=lambda definition, projection, c=condition: c,
                    )
                    self.assertEqual((result["status"], result["outcome"]), ("STOPPED", condition))
                    self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 0)
                    self.assertEqual(self.bob_status(project), "active")

    def test_stale_state_stops_before_grant_consumption(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            grant_ref = self.make_disable_grant(project, gstore, workflow_ref)
            proposal = self.plan_disable(project)
            self.add_operator(project, "operator:carol")

            result = human.continue_auto_workflow(project, wstore, gstore, workflow_ref, proposal)

            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "PROPOSAL_STALE"))
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 0)
            self.assertEqual(self.bob_status(project), "active")

    def test_exhausted_grant_cannot_supply_fresh_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            grant_ref = self.make_disable_grant(project, gstore, workflow_ref, limit=1)
            proposal = self.plan_disable(project)

            issued = g4.issue_operator_disable_grant_approval(
                project,
                gstore,
                grant_ref,
                proposal,
                workflow_ref=workflow_ref,
                workflow_lifecycle="OPEN",
                workflow_condition="READY",
                workflow_contains_proposal=True,
                expected_grant_head=None,
            )
            self.assertEqual(issued["approval"]["authority_basis"]["grant"], grant_ref)
            self.assertEqual(grant.project_grant(gstore, grant_ref)["state"], "EXHAUSTED")

            result = human.continue_auto_workflow(project, wstore, gstore, workflow_ref, proposal)

            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "AWAITING_APPROVAL"))
            self.assertEqual(result["reason"], "NO_APPLICABLE_GRANT")
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 1)
            self.assertEqual(self.bob_status(project), "active")

    def test_revoked_grant_cannot_supply_fresh_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            grant_ref = self.make_disable_grant(project, gstore, workflow_ref)
            proposal = self.plan_disable(project)
            auth = {
                "operator_id": "operator:root",
                "method": "test-human",
                "subject": grant_ref,
                "confirmation": "REVOKE_AUTHORITY_GRANT",
            }
            grant.revoke_grant(
                gstore,
                grant_ref,
                "operator:root",
                auth,
                expected_normative_head=None,
            )
            self.assertEqual(grant.project_grant(gstore, grant_ref)["state"], "REVOKED")

            result = human.continue_auto_workflow(project, wstore, gstore, workflow_ref, proposal)

            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "AWAITING_APPROVAL"))
            self.assertEqual(result["reason"], "NO_APPLICABLE_GRANT")
            self.assertEqual(self.bob_status(project), "active")

    def test_grant_selection_ambiguity_never_lets_agent_choose(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            g1 = self.make_disable_grant(project, gstore, workflow_ref, limit=1)
            g2 = self.make_disable_grant(project, gstore, workflow_ref, limit=2)
            proposal = self.plan_disable(project)

            result = human.continue_auto_workflow(project, wstore, gstore, workflow_ref, proposal)

            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "GRANT_AUTHORITY_AMBIGUITY"))
            self.assertEqual(set(result["grants"]), {g1, g2})
            self.assertEqual(grant.project_grant(gstore, g1)["approvals_issued"], 0)
            self.assertEqual(grant.project_grant(gstore, g2)["approvals_issued"], 0)
            self.assertEqual(self.bob_status(project), "active")

    def test_wildcards_are_not_inferred_as_workflow_or_grant_authority(self):
        with self.assertRaises(grant.ContractError) as cm:
            grant.grant_payload(
                grantor="operator:root",
                workflow="workflow:w1",
                operations=["*"],
                targets=[],
                constraints=[],
            )
        self.assertEqual(cm.exception.code, "NON_DELEGABLE")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            wildcard_grant = self.make_disable_grant(project, gstore, workflow_ref, target="*")
            proposal = self.plan_disable(project)

            result = human.continue_auto_workflow(project, wstore, gstore, workflow_ref, proposal)
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "AWAITING_APPROVAL"))
            self.assertEqual(result["reason"], "NO_APPLICABLE_GRANT")
            self.assertEqual(grant.project_grant(gstore, wildcard_grant)["approvals_issued"], 0)
            self.assertEqual(self.bob_status(project), "active")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(
                wstore,
                [g4.OPERATOR_DISABLE_OPERATION_CLASS],
                extra_intent={"targets": "*"},
            )
            grant_ref = self.make_disable_grant(project, gstore, workflow_ref)
            proposal = self.plan_disable(project)

            result = human.continue_auto_workflow(project, wstore, gstore, workflow_ref, proposal)
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "WORKFLOW_SCOPE_BOUNDARY"))
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 0)
            self.assertEqual(self.bob_status(project), "active")

    def test_scope_expansion_requires_explicit_grant_creation_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project)
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            payload = grant.grant_payload(
                grantor="operator:root",
                workflow=workflow_ref,
                operations=[g4.OPERATOR_DISABLE_OPERATION_CLASS],
                targets=[{"field": "operator_id", "match": "one-of", "values": ["operator:bob", "operator:carol"]}],
                constraints=[{"field": "operation", "predicate": "eq", "value": "DISABLE_OPERATOR"}],
                approvals_limit=2,
            )
            definition = grant.make_grant(payload, grant.make_grant_auth(payload, "operator:root"))

            undisclosed = human.create_authority_grant(
                project,
                gstore,
                definition,
                workflow_scope_confirmed=True,
                prospective_delegation_disclosed=False,
            )
            self.assertEqual(
                (undisclosed["status"], undisclosed["outcome"]),
                ("STOPPED", "GRANT_PROSPECTIVE_DELEGATION_DISCLOSURE_REQUIRED"),
            )
            unconfirmed = human.create_authority_grant(
                project,
                gstore,
                definition,
                workflow_scope_confirmed=False,
                prospective_delegation_disclosed=True,
            )
            self.assertEqual(
                (unconfirmed["status"], unconfirmed["outcome"]),
                ("STOPPED", "GRANT_WORKFLOW_SCOPE_CONFIRMATION_REQUIRED"),
            )
            self.assertEqual(shared.list_grants(gstore), [])

    def test_unsupported_and_protected_operations_remain_non_delegable(self):
        operation_classes = [
            "operator-registry.initialize-root",
            "operator-registry.add",
            "operator-registry.update-capabilities",
            "operator-registry.reenable",
            "operator-registry.transfer-root",
            "steward-authorization.change",
            "exceptional-recovery",
            "authority-grant.create",
            "authority-grant.expand",
            "workflow.revise",
            "workflow.acknowledge-materiality",
        ]
        for operation_class in operation_classes:
            with self.subTest(operation_class=operation_class):
                with self.assertRaises(grant.ContractError) as cm:
                    grant.grant_payload(
                        grantor="operator:root",
                        workflow="workflow:w1",
                        operations=[operation_class],
                        targets=[],
                        constraints=[],
                    )
                self.assertEqual(cm.exception.code, "NON_DELEGABLE")

        for ceremony in ("root-transfer", "steward-authorization", "exceptional-recovery"):
            with self.subTest(ceremony=ceremony):
                intent = human.bind_contextual_intent("do it", [ceremony])
                self.assertEqual((intent["status"], intent["outcome"]), ("PASS", "BOUND_INTENT"))
                boundary = human.protected_ceremony_boundary(ceremony)
                self.assertEqual(
                    (boundary["status"], boundary["outcome"]),
                    ("STOPPED", "PROTECTED_CEREMONY_REQUIRED"),
                )

    def test_workflow_listing_non_delegable_operation_does_not_make_it_delegable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project)
            workflow_ref = self.make_workflow(wstore, ["operator-registry.add"])
            planned = opm.plan_operator_change(project, "ADD_OPERATOR", "operator:bob", ["project:test"])
            self.assertEqual(planned["status"], "PASS")

            result = human.continue_auto_workflow(
                project,
                wstore,
                gstore,
                workflow_ref,
                planned["proposal"],
            )

            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "AWAITING_APPROVAL"))
            self.assertEqual(result["reason"], "NON_DELEGABLE")
            state, _ = opm._load_registry(project)
            self.assertNotIn("operator:bob", state["operators"])


if __name__ == "__main__":
    unittest.main()
