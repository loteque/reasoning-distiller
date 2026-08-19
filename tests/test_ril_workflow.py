#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ril_workflow_g2", ROOT / "runtime" / "ril_workflow.py")
wf = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(wf)


def make(store: Path, *, mode="operator-driven", continuation=None, materiality=None, supersedes=None):
    payload = wf.workflow_payload(
        requester="operator:alice",
        intent={"subject": "roles", "operations": ["role-registry.change"]},
        execution_mode=mode,
        continuation_policy=continuation,
        materiality_policy=materiality,
        plan=[{"advisory": "inspect"}],
        supersedes=supersedes,
    )
    auth = wf.make_workflow_auth(
        payload,
        "operator:alice",
        confirmation="AUTO_ADVANCE" if mode == "auto-advance" else None,
    )
    obj = wf.make_workflow(payload, auth)
    return wf.create_workflow(store, obj), obj


class G2WorkflowTests(unittest.TestCase):
    def test_definition_identity_binds_intent_and_authentication(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            ref, obj = make(store)
            self.assertTrue(ref.startswith("workflow:"))
            self.assertEqual(wf.workflow_reference(obj), ref)
            self.assertEqual(wf.load_workflow(store, ref), obj)

    def test_auto_advance_requires_explicit_prospective_confirmation(self):
        payload = wf.workflow_payload(
            requester="operator:alice", intent={"subject": "roles"}, execution_mode="auto-advance"
        )
        auth = wf.make_workflow_auth(payload, "operator:alice")
        with self.assertRaises(wf.ContractError) as cm:
            wf.make_workflow(payload, auth)
        self.assertEqual(cm.exception.code, "AUTO_ADVANCE_CONFIRMATION_REQUIRED")

    def test_extension_event_advances_history_not_normative_head(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); ref, _ = make(store)
            core = wf.record_attempt_failure(store, ref, "boom", expected_normative_head=None)
            info = wf.append_extension_event(store, ref, "test/diagnostic", {"note": "x"})
            p = wf.project_workflow(store, ref)
            self.assertEqual(p["normative_head"], core)
            self.assertEqual(p["history_head"], info)
            self.assertEqual(p["condition"], "EXECUTION_FAILED")

    def test_informational_append_does_not_invalidate_normative_transition(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); ref, _ = make(store)
            first = wf.record_attempt_failure(store, ref, "boom", expected_normative_head=None)
            wf.append_extension_event(store, ref, "test/diagnostic", {"note": "later"})
            second = wf.pause_materiality(store, ref, {"fact": "material"}, expected_normative_head=first)
            p = wf.project_workflow(store, ref)
            self.assertEqual(p["normative_head"], second)
            self.assertEqual(p["condition"], "MATERIALITY_PAUSE")

    def test_competing_normative_transition_fails_stale_head(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); ref, _ = make(store)
            first = wf.record_attempt_failure(store, ref, "one", expected_normative_head=None)
            with self.assertRaises(wf.ContractError) as cm:
                wf.pause_materiality(store, ref, {"fact": "two"}, expected_normative_head=None)
            self.assertEqual(cm.exception.code, "WORKFLOW_NORMATIVE_HEAD_CONFLICT")
            self.assertEqual(wf.project_workflow(store, ref)["normative_head"], first)

    def test_materiality_acknowledgement_binds_exact_pause(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); ref, _ = make(store)
            pause = wf.pause_materiality(store, ref, {"fact": "material"}, expected_normative_head=None)
            bad_auth = {"operator_id": "operator:alice", "method": "human_confirmation", "confirmation": "ACKNOWLEDGE_MATERIALITY", "subject": "workflow-event:wrong"}
            with self.assertRaises(wf.ContractError):
                wf.acknowledge_materiality(store, ref, pause, "operator:alice", bad_auth)
            auth = {"operator_id": "operator:alice", "method": "human_confirmation", "confirmation": "ACKNOWLEDGE_MATERIALITY", "subject": pause}
            ack = wf.acknowledge_materiality(store, ref, pause, "operator:alice", auth)
            p = wf.project_workflow(store, ref)
            self.assertEqual(p["normative_head"], ack)
            self.assertEqual(p["condition"], "READY")
            self.assertIsNone(p["materiality_pause"])

    def test_materiality_pause_suspends_continuation(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); ref, _ = make(store, continuation={"kind": "any-enabled-operator"})
            self.assertTrue(wf.continuation_permitted(store, ref, "operator:bob"))
            wf.pause_materiality(store, ref, {"fact": "material"}, expected_normative_head=None)
            self.assertFalse(wf.continuation_permitted(store, ref, "operator:bob"))

    def test_result_binding_requires_explicit_in_scope_validation(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); ref, _ = make(store)
            with self.assertRaises(wf.ContractError) as cm:
                wf.bind_operation_result(store, ref, "receipt:abc", expected_normative_head=None, in_scope=lambda intent, result: False)
            self.assertEqual(cm.exception.code, "WORKFLOW_RESULT_OUT_OF_SCOPE")
            event = wf.bind_operation_result(store, ref, "receipt:abc", expected_normative_head=None, in_scope=lambda intent, result: True)
            p = wf.project_workflow(store, ref)
            self.assertEqual(p["normative_head"], event)
            self.assertEqual(p["bound_results"], ["receipt:abc"])

    def test_completion_is_primitive_proved_and_terminal(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); ref, _ = make(store)
            bound = wf.bind_operation_result(store, ref, "receipt:abc", expected_normative_head=None, in_scope=lambda i, r: True)
            self.assertIsNone(wf.complete_if(store, ref, {}, lambda intent, results, state: False))
            completed = wf.complete_if(store, ref, {"ok": True}, lambda intent, results, state: results == ["receipt:abc"] and state["ok"])
            self.assertIsNotNone(completed)
            self.assertEqual(wf.project_workflow(store, ref)["lifecycle"], "COMPLETED")
            with self.assertRaises(wf.ContractError) as cm:
                wf.record_attempt_failure(store, ref, "late", expected_normative_head=completed)
            self.assertEqual(cm.exception.code, "WORKFLOW_TERMINAL")
            self.assertEqual(wf.project_workflow(store, ref)["normative_head"], completed)
            self.assertNotEqual(bound, completed)

    def test_cancel_requester_and_root_override_only(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); ref, _ = make(store)
            auth_bob = {"operator_id": "operator:bob", "method": "human_confirmation", "confirmation": "CANCEL_WORKFLOW", "subject": ref}
            with self.assertRaises(wf.ContractError) as cm:
                wf.cancel_workflow(store, ref, "operator:bob", auth_bob)
            self.assertEqual(cm.exception.code, "WORKFLOW_CANCEL_NOT_PERMITTED")
            cancel = wf.cancel_workflow(store, ref, "operator:bob", auth_bob, protected_root=True)
            self.assertEqual(wf.project_workflow(store, ref)["lifecycle"], "CANCELLED")
            self.assertEqual(wf.project_workflow(store, ref)["normative_head"], cancel)

    def test_revision_creates_successor_and_seals_predecessor(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); old_ref, _ = make(store)
            payload = wf.workflow_payload(
                requester="operator:alice",
                intent={"subject": "roles", "operations": ["role-registry.change"], "limit": 2},
                supersedes=old_ref,
            )
            successor = wf.make_workflow(payload, wf.make_workflow_auth(payload, "operator:alice"))
            new_ref = wf.revise_workflow(store, old_ref, successor, expected_normative_head=None)
            self.assertNotEqual(old_ref, new_ref)
            self.assertEqual(wf.project_workflow(store, old_ref)["lifecycle"], "SUPERSEDED")
            self.assertEqual(wf.load_workflow(store, new_ref)["payload"]["supersedes"], old_ref)

    def test_revision_fails_closed_on_changed_normative_head(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); old_ref, _ = make(store)
            wf.record_attempt_failure(store, old_ref, "changed", expected_normative_head=None)
            payload = wf.workflow_payload(requester="operator:alice", intent={"subject": "roles", "limit": 2}, supersedes=old_ref)
            successor = wf.make_workflow(payload, wf.make_workflow_auth(payload, "operator:alice"))
            with self.assertRaises(wf.ContractError) as cm:
                wf.revise_workflow(store, old_ref, successor, expected_normative_head=None)
            self.assertEqual(cm.exception.code, "WORKFLOW_NORMATIVE_HEAD_CONFLICT")
            self.assertEqual(wf.project_workflow(store, old_ref)["lifecycle"], "OPEN")

    def test_condition_resolver_cannot_invent_unknown_condition(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td); ref, _ = make(store)
            p = wf.project_workflow(store, ref, condition_resolver=lambda definition, projection: "AWAITING_ACTIVATION")
            self.assertEqual(p["condition"], "AWAITING_ACTIVATION")
            with self.assertRaises(wf.ContractError):
                wf.project_workflow(store, ref, condition_resolver=lambda definition, projection: "MAGIC")


if __name__ == "__main__":
    unittest.main()
