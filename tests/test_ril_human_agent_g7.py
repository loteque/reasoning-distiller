#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

import ril_human_agent as human
import ril_mutation as mutation


class G7HumanAgentAdapterTests(unittest.TestCase):
    def test_context_bound_affirmations_fail_closed(self):
        one = human.bind_contextual_intent("Proceed", ["approve proposal:abc"])
        self.assertEqual(one["status"], "PASS")
        self.assertEqual(one["outcome"], "BOUND_INTENT")

        ambiguous = human.bind_contextual_intent("yes", ["approve proposal:a", "apply proposal:a"], closed_set=True)
        self.assertEqual(ambiguous["status"], "STOPPED")
        self.assertEqual(ambiguous["outcome"], "AMBIGUOUS_INTENT")

        closed = human.bind_contextual_intent("approve all", ["approve proposal:a", "approve proposal:b"], closed_set=True)
        self.assertEqual(closed["status"], "PASS")
        self.assertEqual(closed["outcome"], "BOUND_INTENT_SET")

        broad = human.bind_contextual_intent("take care of everything", ["approve proposal:a"])
        self.assertEqual(broad["outcome"], "NO_AUTHORITY")

        revised = human.bind_contextual_intent("yes", ["approve proposal:a"], material_modification=True)
        self.assertEqual(revised["outcome"], "REVISION_REQUEST")

    def test_proposal_presentation_exposes_exact_immutable_reference(self):
        state = {"value": 1}
        proposal = mutation.make_proposal("example", "CHANGE", state, {"value": 2})
        shown = human.present_proposal(
            proposal,
            material_effect="Change value from 1 to 2.",
            authority_implications=["Creates direct approval only after explicit assent."],
            application_prospectively_disclosed=False,
        )
        expected = "proposal:" + mutation.digest(proposal).split(":", 1)[1]
        self.assertEqual(shown["proposal_reference"], expected)
        self.assertEqual(shown["complete_normative_proposal"], proposal)
        self.assertFalse(shown["application_prospectively_disclosed"])

    def test_direct_approval_runs_d3_immediately_before_creation(self):
        state = {"version": 1}
        proposal = mutation.make_proposal("example", "CHANGE", state, {"version": 2})
        calls: list[str] = []

        def current_state():
            calls.append("load")
            return state

        approved = human.direct_approve(
            proposal,
            "operator:alice",
            {"method": "test"},
            current_state,
        )
        self.assertEqual(calls, ["load"])
        self.assertEqual(approved["status"], "PASS")
        self.assertEqual(approved["outcome"], "APPROVED")
        self.assertEqual(approved["revalidation"]["classification"], "APPLICABLE")
        self.assertEqual(approved["approval"]["contract"], mutation.APPROVAL_V2_CONTRACT)
        mutation.validate_approval(approved["approval"], proposal)

        stale = human.direct_approve(
            proposal,
            "operator:alice",
            {"method": "test"},
            lambda: {"version": 99},
        )
        self.assertEqual(stale["status"], "STOPPED")
        self.assertEqual(stale["outcome"], "PROPOSAL_STALE")
        self.assertNotIn("approval", stale)

        blocked = human.direct_approve(
            proposal,
            "operator:alice",
            {"method": "test"},
            lambda: state,
            blocked_reasons=["MISSING_EVIDENCE"],
        )
        self.assertEqual(blocked["outcome"], "PROPOSAL_BLOCKED")
        self.assertNotIn("approval", blocked)

    def test_auto_advance_is_a_thin_g5_peer_adapter(self):
        original = human.shared.advance_auto_proposal
        calls: list[tuple] = []
        expected = {
            "contract": "reasoning-distiller-shared-orchestration-result/1",
            "status": "STOPPED",
            "outcome": "MATERIALITY_PAUSE",
        }
        try:
            def fake(*args, **kwargs):
                calls.append((args, kwargs))
                return expected

            human.shared.advance_auto_proposal = fake
            proposal = mutation.make_proposal("example", "CHANGE", {}, {"x": 1})
            result = human.continue_auto_workflow(
                Path("/project"),
                Path("/workflow-store"),
                Path("/grant-store"),
                "workflow:abc",
                proposal,
                grant_refs=["authority-grant:def"],
            )
            self.assertIs(result, expected)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0][3], "workflow:abc")
            self.assertEqual(calls[0][0][4], proposal)
            self.assertEqual(calls[0][1]["grant_refs"], ["authority-grant:def"])
        finally:
            human.shared.advance_auto_proposal = original

    def test_cross_session_resume_reconstructs_from_durable_reference(self):
        proposal = mutation.make_proposal("example", "CHANGE", {}, {"x": 1})
        ref = human.proposal_reference(proposal)
        loaded: list[str] = []

        def loader(requested: str):
            loaded.append(requested)
            return proposal

        resumed = human.resume_proposal(ref, loader)
        self.assertEqual(resumed["status"], "PASS")
        self.assertEqual(resumed["outcome"], "PROPOSAL_RECONSTRUCTED")
        self.assertEqual(loaded, [ref])

        different = mutation.make_proposal("example", "CHANGE", {}, {"x": 2})
        mismatch = human.resume_proposal(ref, lambda _: different)
        self.assertEqual(mismatch["outcome"], "DURABLE_REFERENCE_MISMATCH")

    def test_protected_ceremony_and_control_return_are_explicit(self):
        boundary = human.protected_ceremony_boundary("TRANSFER_ROOT")
        self.assertEqual(boundary["status"], "STOPPED")
        self.assertEqual(boundary["outcome"], "PROTECTED_CEREMONY_REQUIRED")

        proposal = mutation.make_proposal("example", "CHANGE", {}, {"x": 1})
        approval = mutation.make_direct_approval_v2(proposal, "operator:alice", {"method": "test"})
        returned = human.control_return(
            requested_work=["change x"],
            completed_work=["proposal approved"],
            not_completed_work=["change x was not applied"],
            durable_artifacts=[human.proposal_reference(proposal), human.approval_reference(approval, proposal)],
            approvals=[approval],
            boundary="AWAITING_APPLICATION",
            next_actions=["apply the exact approved proposal"],
        )
        self.assertEqual(returned["completed_work"], ["proposal approved"])
        self.assertEqual(returned["not_completed_work"], ["change x was not applied"])
        self.assertEqual(returned["approval_authority"], [{"kind": "direct", "operator": "operator:alice"}])
        self.assertEqual(returned["boundary"], "AWAITING_APPLICATION")

        grant_approval = mutation.make_grant_approval_v2(
            proposal,
            "authority-grant:g",
            "authority-grant-event:e",
        )
        self.assertEqual(human.approval_authority(grant_approval)["kind"], "grant-derived")


if __name__ == "__main__":
    unittest.main()
