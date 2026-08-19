#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mut = load("ril_mutation_g3", ROOT / "runtime" / "ril_mutation.py")
grant = load("ril_authority_grant_g3", ROOT / "runtime" / "ril_authority_grant.py")


class AuthorityGrantG3Tests(unittest.TestCase):
    def make_grant(self, store, *, limit=2, operations=None, targets=None, constraints=None):
        payload = grant.grant_payload(
            grantor="operator:owner",
            workflow="workflow:w1",
            operations=operations or ["operator-registry.disable"],
            targets=targets or [{"field": "operator_id", "match": "one-of", "values": ["operator:bob", "operator:carol"]}],
            constraints=constraints or [{"field": "operation", "predicate": "eq", "value": "DISABLE_OPERATOR"}],
            approvals_limit=limit,
        )
        auth = grant.make_grant_auth(payload, "operator:owner")
        obj = grant.make_grant(payload, auth)
        ref = grant.create_grant(store, obj)
        return ref, obj

    def make_proposal(self, current=None):
        state = {} if current is None else current
        return mut.make_proposal("operators", "DISABLE_OPERATOR", state, {"operator_id": "operator:bob"})

    def test_definition_is_immutable_content_addressed_and_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, obj = self.make_grant(store)
            self.assertTrue(ref.startswith("authority-grant:"))
            self.assertEqual(grant.create_grant(store, obj), ref)
            self.assertEqual(grant.load_grant(store, ref), obj)

    def test_non_delegable_operation_fails_closed_at_creation(self):
        with self.assertRaises(grant.ContractError) as cm:
            grant.grant_payload(
                grantor="operator:owner", workflow="workflow:w1",
                operations=["operator-registry.add"], targets=[], constraints=[]
            )
        self.assertEqual(cm.exception.code, "NON_DELEGABLE")

    def test_scope_wholly_contains_exact_proposal(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, _ = self.make_grant(store)
            p = self.make_proposal()
            result = grant.validate_scope(
                store, ref, p,
                operation_class="operator-registry.disable",
                authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR"},
                workflow_ref="workflow:w1", workflow_contains_proposal=True,
            )
            self.assertEqual(result["classification"], "WITHIN_GRANT")

    def test_scope_partial_or_unknown_effect_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, _ = self.make_grant(store)
            p = self.make_proposal()
            outside = grant.validate_scope(
                store, ref, p,
                operation_class="operator-registry.disable",
                authority_fields={"operator_id": "operator:mallory", "operation": "DISABLE_OPERATOR"},
                workflow_ref="workflow:w1", workflow_contains_proposal=True,
            )
            self.assertEqual(outside["classification"], "OUTSIDE_GRANT")
            unknown = grant.validate_scope(
                store, ref, p,
                operation_class="operator-registry.disable",
                authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR", "extra_effect": True},
                workflow_ref="workflow:w1", workflow_contains_proposal=True,
            )
            self.assertEqual(unknown["classification"], "OUTSIDE_GRANT")

    def test_workflow_mismatch_and_terminal_workflow_block(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, _ = self.make_grant(store)
            p = self.make_proposal()
            mismatch = grant.validate_scope(
                store, ref, p,
                operation_class="operator-registry.disable",
                authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR"},
                workflow_ref="workflow:other", workflow_contains_proposal=True,
            )
            self.assertEqual(mismatch["classification"], "WORKFLOW_MISMATCH")
            terminal = grant.validate_scope(
                store, ref, p,
                operation_class="operator-registry.disable",
                authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR"},
                workflow_ref="workflow:w1", workflow_lifecycle="COMPLETED", workflow_contains_proposal=True,
            )
            self.assertEqual(terminal["classification"], "GRANT_INACTIVE")

    def test_issue_approval_consumes_limit_at_issuance_and_exhausts(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, _ = self.make_grant(store, limit=1)
            p = self.make_proposal()
            issued = grant.issue_approval(
                store, ref, p,
                operation_class="operator-registry.disable",
                authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR"},
                workflow_ref="workflow:w1", workflow_lifecycle="OPEN", workflow_condition="READY",
                workflow_contains_proposal=True, current_state={}, expected_normative_head=None,
            )
            self.assertEqual(issued["approval"]["authority_basis"]["kind"], "authority-grant")
            self.assertEqual(issued["approval"]["authority_basis"]["grant"], ref)
            self.assertEqual(issued["approval"]["authority_basis"]["grant_event"], issued["grant_event"])
            projection = grant.project_grant(store, ref)
            self.assertEqual(projection["approvals_issued"], 1)
            self.assertEqual(projection["approvals_remaining"], 0)
            self.assertEqual(projection["state"], "EXHAUSTED")
            self.assertIsNotNone(issued["exhausted_event"])

    def test_d3_stale_blocks_before_consumption(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, _ = self.make_grant(store, limit=1)
            p = self.make_proposal()
            with self.assertRaises(grant.ContractError) as cm:
                grant.issue_approval(
                    store, ref, p,
                    operation_class="operator-registry.disable",
                    authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR"},
                    workflow_ref="workflow:w1", workflow_lifecycle="OPEN", workflow_condition="READY",
                    workflow_contains_proposal=True, current_state={"changed": True}, expected_normative_head=None,
                )
            self.assertEqual(cm.exception.code, "PROPOSAL_STALE")
            self.assertEqual(grant.project_grant(store, ref)["approvals_issued"], 0)

    def test_materiality_pause_blocks_before_consumption(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, _ = self.make_grant(store, limit=1)
            p = self.make_proposal()
            with self.assertRaises(grant.ContractError) as cm:
                grant.issue_approval(
                    store, ref, p,
                    operation_class="operator-registry.disable",
                    authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR"},
                    workflow_ref="workflow:w1", workflow_lifecycle="OPEN", workflow_condition="MATERIALITY_PAUSE",
                    workflow_contains_proposal=True, current_state={}, expected_normative_head=None,
                )
            self.assertEqual(cm.exception.code, "MATERIALITY_PAUSE")
            self.assertEqual(grant.project_grant(store, ref)["approvals_issued"], 0)

    def test_revocation_blocks_future_issuance_but_preserves_past_approval(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, _ = self.make_grant(store, limit=2)
            p = self.make_proposal()
            issued = grant.issue_approval(
                store, ref, p,
                operation_class="operator-registry.disable",
                authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR"},
                workflow_ref="workflow:w1", workflow_lifecycle="OPEN", workflow_condition="READY",
                workflow_contains_proposal=True, current_state={}, expected_normative_head=None,
            )
            head = grant.project_grant(store, ref)["normative_head"]
            auth = {"operator_id": "operator:owner", "method": "test-human", "subject": ref, "confirmation": "REVOKE_AUTHORITY_GRANT"}
            grant.revoke_grant(store, ref, "operator:owner", auth, expected_normative_head=head)
            self.assertEqual(grant.project_grant(store, ref)["state"], "REVOKED")
            mut.validate_approval(issued["approval"], p)
            with self.assertRaises(grant.ContractError):
                grant.issue_approval(
                    store, ref, p,
                    operation_class="operator-registry.disable",
                    authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR"},
                    workflow_ref="workflow:w1", workflow_lifecycle="OPEN", workflow_condition="READY",
                    workflow_contains_proposal=True, current_state={}, expected_normative_head=grant.project_grant(store, ref)["normative_head"],
                )

    def test_revocation_and_issuance_use_exact_head_concurrency(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, _ = self.make_grant(store, limit=2)
            p = self.make_proposal()
            issued = grant.issue_approval(
                store, ref, p,
                operation_class="operator-registry.disable",
                authority_fields={"operator_id": "operator:bob", "operation": "DISABLE_OPERATOR"},
                workflow_ref="workflow:w1", workflow_lifecycle="OPEN", workflow_condition="READY",
                workflow_contains_proposal=True, current_state={}, expected_normative_head=None,
            )
            auth = {"operator_id": "operator:owner", "method": "test-human", "subject": ref, "confirmation": "REVOKE_AUTHORITY_GRANT"}
            with self.assertRaises(grant.ContractError) as cm:
                grant.revoke_grant(store, ref, "operator:owner", auth, expected_normative_head=None)
            self.assertEqual(cm.exception.code, "GRANT_NORMATIVE_HEAD_CONFLICT")
            self.assertTrue(issued["grant_event"].startswith("authority-grant-event:"))

    def test_protected_root_can_revoke_with_stronger_ceremony(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, _ = self.make_grant(store)
            auth = {"operator_id": "operator:root", "method": "test-human", "subject": ref, "confirmation": "ROOT_REVOKE_AUTHORITY_GRANT"}
            ev = grant.revoke_grant(store, ref, "operator:root", auth, protected_root=True, expected_normative_head=None)
            self.assertTrue(ev.startswith("authority-grant-event:"))
            self.assertEqual(grant.project_grant(store, ref)["state"], "REVOKED")


if __name__ == "__main__":
    unittest.main()
