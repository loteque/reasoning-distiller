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
import ril_operator_management as opm
import ril_operators as ops
import ril_roles as roles
import ril_shared_orchestration as shared
import ril_workflow as wf


class G5SharedOrchestrationTests(unittest.TestCase):
    def establish_root(self, project: Path) -> None:
        planned = ops.plan_initial_operator(project, "operator:root")
        approval = ops.approve_initial_operator(planned["proposal"], "operator:root")
        applied = ops.apply_initial_operator(project, planned["proposal"], approval)
        self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))

    def add_operator(self, project: Path, operator_id: str, capabilities: list[str] | None = None) -> None:
        planned = opm.plan_operator_change(project, "ADD_OPERATOR", operator_id, capabilities or ["project:test"])
        self.assertEqual(planned["status"], "PASS")
        approval = opm.approve_operator_change(planned["proposal"], "operator:root")
        applied = opm.apply_operator_change(project, planned["proposal"], approval)
        self.assertEqual((applied["status"], applied["outcome"]), ("PASS", "APPLIED"))

    def make_workflow(self, store: Path, operations: list[str], *, mode: str = "auto-advance") -> str:
        payload = wf.workflow_payload(
            requester="operator:root",
            intent={"subject": "g5", "operations": operations},
            execution_mode=mode,
        )
        auth = wf.make_workflow_auth(
            payload,
            "operator:root",
            confirmation="AUTO_ADVANCE" if mode == "auto-advance" else None,
        )
        return wf.create_workflow(store, wf.make_workflow(payload, auth))

    def make_operator_disable_grant(
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
        obj = grant.make_grant(payload, grant.make_grant_auth(payload, "operator:root"))
        return g4.create_authorized_grant(project, store, obj, workflow_contains_grant_scope=True)

    def make_role_grant(self, project: Path, store: Path, workflow_ref: str, role_id: str) -> str:
        payload = grant.grant_payload(
            grantor="operator:root",
            workflow=workflow_ref,
            operations=[g4.ROLE_OPERATION_CLASS],
            targets=[{"field": "role_id", "match": "exact", "value": role_id}],
            constraints=[{"field": "mutation_kinds", "predicate": "subset-of", "values": ["ADD"]}],
            approvals_limit=1,
        )
        obj = grant.make_grant(payload, grant.make_grant_auth(payload, "operator:root"))
        return g4.create_authorized_grant(project, store, obj, workflow_contains_grant_scope=True)

    def test_operator_disable_auto_advances_and_binds_normative_result(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            grant_ref = self.make_operator_disable_grant(project, gstore, workflow_ref, limit=1)
            planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")

            result = shared.advance_auto_proposal(project, wstore, gstore, workflow_ref, planned["proposal"])

            self.assertEqual((result["status"], result["outcome"]), ("PASS", "ADVANCED"))
            self.assertEqual(result["grant"], grant_ref)
            self.assertEqual(result["approval"]["authority_basis"]["kind"], "authority-grant")
            self.assertTrue(result["result_reference"].startswith("mutation-event:"))
            self.assertTrue(result["workflow_event"].startswith("workflow-event:"))
            state, _ = opm._load_registry(project)
            self.assertEqual(state["operators"]["operator:bob"]["status"], "disabled")
            projection = wf.project_workflow(wstore, workflow_ref)
            self.assertEqual(projection["bound_results"], [result["result_reference"]])
            self.assertEqual(grant.project_grant(gstore, grant_ref)["state"], "EXHAUSTED")

    def test_role_change_uses_same_shared_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project)
            workflow_ref = self.make_workflow(wstore, [g4.ROLE_OPERATION_CLASS])
            self.make_role_grant(project, gstore, workflow_ref, "alpha")
            submission = {
                "contract": roles.SUBMISSION_CONTRACT,
                "mode": "incremental",
                "source": "g5-test",
                "scope": None,
                "roles": [{"role_id": "alpha", "title": "Alpha", "description": "test", "capabilities": ["project:test"]}],
            }
            planned = roles.plan_role_submission(project, submission)
            result = shared.advance_auto_proposal(project, wstore, gstore, workflow_ref, planned["proposal"])
            self.assertEqual((result["status"], result["outcome"]), ("PASS", "ADVANCED"))
            state, _ = roles._load_role_state(project)
            self.assertIn("alpha", state["roles"])

    def test_d3_stale_stops_before_grant_discovery_or_consumption(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")
            self.add_operator(project, "operator:carol")  # changes authoritative proposal basis
            # If grant discovery happened before D3 this malformed store would fail first.
            (gstore / "authority-grants").parent.mkdir(parents=True, exist_ok=True)
            (gstore / "authority-grants").write_text("not-a-directory", encoding="utf-8")

            result = shared.advance_auto_proposal(project, wstore, gstore, workflow_ref, planned["proposal"])
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "PROPOSAL_STALE"))

    def test_non_delegable_operation_returns_ordinary_approval_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project)
            workflow_ref = self.make_workflow(wstore, ["operator-registry.add"])
            planned = opm.plan_operator_change(project, "ADD_OPERATOR", "operator:bob", ["project:test"])
            result = shared.advance_auto_proposal(project, wstore, gstore, workflow_ref, planned["proposal"])
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "AWAITING_APPROVAL"))
            self.assertEqual(result["reason"], "NON_DELEGABLE")

    def test_no_applicable_grant_returns_awaiting_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")
            result = shared.advance_auto_proposal(project, wstore, gstore, workflow_ref, planned["proposal"])
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "AWAITING_APPROVAL"))
            self.assertEqual(result["reason"], "NO_APPLICABLE_GRANT")

    def test_materiality_pause_blocks_after_grant_discovery_without_consumption(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            grant_ref = self.make_operator_disable_grant(project, gstore, workflow_ref)
            planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")
            wf.pause_materiality(wstore, workflow_ref, {"fact": "new-risk"}, expected_normative_head=None)

            result = shared.advance_auto_proposal(project, wstore, gstore, workflow_ref, planned["proposal"])
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "MATERIALITY_PAUSE"))
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 0)

    def test_multiple_applicable_grants_fail_closed_as_ambiguity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS])
            g1 = self.make_operator_disable_grant(project, gstore, workflow_ref, limit=1)
            g2 = self.make_operator_disable_grant(project, gstore, workflow_ref, limit=2)
            planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")

            result = shared.advance_auto_proposal(project, wstore, gstore, workflow_ref, planned["proposal"])
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "GRANT_AUTHORITY_AMBIGUITY"))
            self.assertEqual(set(result["grants"]), {g1, g2})
            self.assertEqual(grant.project_grant(gstore, g1)["approvals_issued"], 0)
            self.assertEqual(grant.project_grant(gstore, g2)["approvals_issued"], 0)

    def test_operator_driven_workflow_does_not_auto_consume_grant(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.OPERATOR_DISABLE_OPERATION_CLASS], mode="operator-driven")
            grant_ref = self.make_operator_disable_grant(project, gstore, workflow_ref)
            planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")
            result = shared.advance_auto_proposal(project, wstore, gstore, workflow_ref, planned["proposal"])
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "CONTINUATION_REQUIRED"))
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 0)

    def test_workflow_scope_failure_cannot_be_reinterpreted_as_grant_authority(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / "project"; wstore = root / "workflows"; gstore = root / "grants"
            self.establish_root(project); self.add_operator(project, "operator:bob")
            workflow_ref = self.make_workflow(wstore, [g4.ROLE_OPERATION_CLASS])
            # Deliberately simulate a bad pre-G5 caller that claimed grant scope fit.
            grant_ref = self.make_operator_disable_grant(project, gstore, workflow_ref)
            planned = opm.plan_operator_change(project, "DISABLE_OPERATOR", "operator:bob")
            result = shared.advance_auto_proposal(project, wstore, gstore, workflow_ref, planned["proposal"])
            self.assertEqual((result["status"], result["outcome"]), ("STOPPED", "WORKFLOW_SCOPE_BOUNDARY"))
            self.assertEqual(grant.project_grant(gstore, grant_ref)["approvals_issued"], 0)


if __name__ == "__main__":
    unittest.main()
