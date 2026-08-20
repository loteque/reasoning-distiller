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
import ril_roles as roles
import ril_workflow as wf


class G10AutonomousWorkflowProofTests(unittest.TestCase):
    def establish_root(self, project: Path) -> None:
        planned = ops.plan_initial_operator(project, "operator:root")
        approval = ops.approve_initial_operator(planned["proposal"], "operator:root")
        applied = ops.apply_initial_operator(project, planned["proposal"], approval)
        self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))

    def add_operator(
        self,
        project: Path,
        operator_id: str,
        capabilities: list[str] | None = None,
    ) -> None:
        planned = opm.plan_operator_change(
            project,
            "ADD_OPERATOR",
            operator_id,
            capabilities or ["project:test"],
        )
        self.assertEqual(planned["status"], "PASS")
        approval = opm.approve_operator_change(planned["proposal"], "operator:root")
        applied = opm.apply_operator_change(project, planned["proposal"], approval)
        self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))

    def create_workflow(self, store: Path, operations: list[str]) -> str:
        payload = wf.workflow_payload(
            requester="operator:root",
            intent={
                "subject": "g10-autonomous-proof",
                "operations": list(operations),
            },
            execution_mode="auto-advance",
        )
        authentication = wf.make_workflow_auth(
            payload,
            "operator:root",
            confirmation="AUTO_ADVANCE",
        )
        definition = wf.make_workflow(payload, authentication)
        created = human.create_durable_workflow(
            store,
            definition,
            persistence_disclosed=True,
        )
        self.assertEqual((created["status"], created["outcome"]), ("PASS", "WORKFLOW_CREATED"))
        return created["workflow"]

    def create_combined_grant(
        self,
        project: Path,
        store: Path,
        workflow_ref: str,
        *,
        include_disable: bool = True,
    ) -> str:
        operations = [g4.ROLE_OPERATION_CLASS]
        targets = [
            {"field": "role_id", "match": "exact", "value": "alpha"},
        ]
        constraints = [
            {"field": "mutation_kinds", "predicate": "subset-of", "values": ["ADD"]},
        ]
        approvals_limit = 1
        if include_disable:
            operations.append(g4.OPERATOR_DISABLE_OPERATION_CLASS)
            targets.append(
                {"field": "operator_id", "match": "exact", "value": "operator:bob"}
            )
            constraints.append(
                {"field": "operation", "predicate": "eq", "value": "DISABLE_OPERATOR"}
            )
            approvals_limit = 2

        payload = grant.grant_payload(
            grantor="operator:root",
            workflow=workflow_ref,
            operations=operations,
            targets=targets,
            constraints=constraints,
            approvals_limit=approvals_limit,
        )
        definition = grant.make_grant(
            payload,
            grant.make_grant_auth(payload, "operator:root"),
        )
        created = human.create_authority_grant(
            project,
            store,
            definition,
            workflow_scope_confirmed=True,
            prospective_delegation_disclosed=True,
        )
        self.assertEqual(
            (created["status"], created["outcome"]),
            ("PASS", "AUTHORITY_GRANT_CREATED"),
        )
        return created["grant"]

    def plan_role_add(self, project: Path) -> dict:
        submission = {
            "contract": roles.SUBMISSION_CONTRACT,
            "mode": "incremental",
            "source": "g10-proof",
            "scope": None,
            "roles": [
                {
                    "role_id": "alpha",
                    "title": "Alpha",
                    "description": "G10 autonomous proof role",
                    "capabilities": ["project:test"],
                }
            ],
        }
        planned = roles.plan_role_submission(project, submission)
        self.assertEqual(planned["status"], "PASS")
        return planned["proposal"]

    def plan_disable_bob(self, project: Path) -> dict:
        planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")
        self.assertEqual(planned["status"], "PASS")
        return planned["proposal"]

    def role_exists(self, project: Path) -> bool:
        state, _ = roles._load_role_state(project)
        return "alpha" in state["roles"]

    def bob_status(self, project: Path) -> str:
        state, _ = opm._load_registry(project)
        return state["operators"]["operator:bob"]["status"]

    def assert_grant_derived(self, result: dict, grant_ref: str) -> None:
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "ADVANCED"))
        self.assertEqual(result["grant"], grant_ref)
        basis = result["approval"]["authority_basis"]
        self.assertEqual(basis["kind"], "authority-grant")
        self.assertEqual(basis["grant"], grant_ref)
        self.assertTrue(result["workflow_event"].startswith("workflow-event:"))
        self.assertTrue(result["result_reference"].startswith("mutation-event:"))

    def test_prospectively_authorized_chain_completes_without_human_interruption(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            wstore = root / "workflows"
            gstore = root / "grants"
            self.establish_root(project)
            self.add_operator(project, "operator:bob")

            workflow_ref = self.create_workflow(
                wstore,
                [g4.ROLE_OPERATION_CLASS, g4.OPERATOR_DISABLE_OPERATION_CLASS],
            )
            grant_ref = self.create_combined_grant(project, gstore, workflow_ref)

            role_result = human.continue_auto_workflow(
                project,
                wstore,
                gstore,
                workflow_ref,
                self.plan_role_add(project),
            )
            self.assert_grant_derived(role_result, grant_ref)
            self.assertTrue(self.role_exists(project))
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 1)

            disable_result = human.continue_auto_workflow(
                project,
                wstore,
                gstore,
                workflow_ref,
                self.plan_disable_bob(project),
            )
            self.assert_grant_derived(disable_result, grant_ref)
            self.assertEqual(self.bob_status(project), "disabled")
            self.assertEqual(grant.project_grant(gstore, grant_ref)["state"], "EXHAUSTED")

            # Completion is a non-proposal automatic workflow operation. The two
            # result-binding events above are also automatic, adapter-neutral D1
            # operations emitted only after successful independently authorized apply.
            completed = wf.complete_if(
                wstore,
                workflow_ref,
                {
                    "role_exists": self.role_exists(project),
                    "bob_status": self.bob_status(project),
                },
                lambda intent, results, state: (
                    intent["operations"]
                    == [g4.ROLE_OPERATION_CLASS, g4.OPERATOR_DISABLE_OPERATION_CLASS]
                    and len(results) == 2
                    and state["role_exists"]
                    and state["bob_status"] == "disabled"
                ),
            )
            self.assertIsNotNone(completed)

            projection = wf.project_workflow(wstore, workflow_ref)
            self.assertEqual(projection["lifecycle"], "COMPLETED")
            self.assertEqual(projection["bound_results"], [
                role_result["result_reference"],
                disable_result["result_reference"],
            ])
            events = wf.read_events(wstore, workflow_ref)
            self.assertEqual(
                [event["event_type"] for event in events],
                [
                    "core/operation-result-bound",
                    "core/operation-result-bound",
                    "core/completed",
                ],
            )

    def test_materiality_interrupts_exactly_before_next_consequential_stage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            wstore = root / "workflows"
            gstore = root / "grants"
            self.establish_root(project)
            self.add_operator(project, "operator:bob")
            workflow_ref = self.create_workflow(
                wstore,
                [g4.ROLE_OPERATION_CLASS, g4.OPERATOR_DISABLE_OPERATION_CLASS],
            )
            grant_ref = self.create_combined_grant(project, gstore, workflow_ref)

            first = human.continue_auto_workflow(
                project, wstore, gstore, workflow_ref, self.plan_role_add(project)
            )
            self.assert_grant_derived(first, grant_ref)
            pause_ref = wf.pause_materiality(
                wstore,
                workflow_ref,
                {"fact": "new material consequence before operator disable"},
                expected_normative_head=wf.project_workflow(wstore, workflow_ref)["normative_head"],
            )

            second = human.continue_auto_workflow(
                project, wstore, gstore, workflow_ref, self.plan_disable_bob(project)
            )

            self.assertEqual((second["status"], second["outcome"]), ("STOPPED", "MATERIALITY_PAUSE"))
            self.assertEqual(second["materiality_pause"], pause_ref)
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 1)
            self.assertEqual(self.bob_status(project), "active")
            projection = wf.project_workflow(wstore, workflow_ref)
            self.assertEqual(projection["condition"], "MATERIALITY_PAUSE")
            self.assertEqual(len(projection["bound_results"]), 1)

    def test_scope_expansion_interrupts_before_out_of_scope_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            wstore = root / "workflows"
            gstore = root / "grants"
            self.establish_root(project)
            self.add_operator(project, "operator:bob")
            workflow_ref = self.create_workflow(wstore, [g4.ROLE_OPERATION_CLASS])
            grant_ref = self.create_combined_grant(
                project,
                gstore,
                workflow_ref,
                include_disable=False,
            )

            first = human.continue_auto_workflow(
                project, wstore, gstore, workflow_ref, self.plan_role_add(project)
            )
            self.assert_grant_derived(first, grant_ref)

            expanded = human.continue_auto_workflow(
                project, wstore, gstore, workflow_ref, self.plan_disable_bob(project)
            )

            self.assertEqual(
                (expanded["status"], expanded["outcome"]),
                ("STOPPED", "WORKFLOW_SCOPE_BOUNDARY"),
            )
            self.assertEqual(self.bob_status(project), "active")
            self.assertEqual(len(wf.project_workflow(wstore, workflow_ref)["bound_results"]), 1)

    def test_protected_authority_interrupts_before_root_transfer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            wstore = root / "workflows"
            gstore = root / "grants"
            self.establish_root(project)
            self.add_operator(project, "operator:bob")
            self.add_operator(project, "operator:carol", list(ops.CORE_CAPABILITIES))
            workflow_ref = self.create_workflow(
                wstore,
                [g4.ROLE_OPERATION_CLASS, "operator-registry.transfer-root"],
            )
            grant_ref = self.create_combined_grant(
                project,
                gstore,
                workflow_ref,
                include_disable=False,
            )

            first = human.continue_auto_workflow(
                project, wstore, gstore, workflow_ref, self.plan_role_add(project)
            )
            self.assert_grant_derived(first, grant_ref)

            transfer = opm.plan_root_transfer(project, "operator:carol")
            self.assertEqual(transfer["status"], "PASS")
            stopped = human.continue_auto_workflow(
                project,
                wstore,
                gstore,
                workflow_ref,
                transfer["proposal"],
            )

            self.assertEqual((stopped["status"], stopped["outcome"]), ("STOPPED", "AWAITING_APPROVAL"))
            self.assertEqual(stopped["reason"], "NON_DELEGABLE")
            state, _ = opm._load_registry(project)
            self.assertEqual(state["root_operator_id"], "operator:root")
            self.assertEqual(len(wf.project_workflow(wstore, workflow_ref)["bound_results"]), 1)


if __name__ == "__main__":
    unittest.main()
