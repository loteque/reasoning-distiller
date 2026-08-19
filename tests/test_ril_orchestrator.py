from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_orchestrator import REQUEST_CONTRACT, orchestrate  # noqa: E402


class OrchestratorR15Tests(unittest.TestCase):
    def root(self) -> Path:
        return Path(tempfile.mkdtemp())

    def request(self, action: str, arguments: dict | None = None) -> dict:
        return {"contract": REQUEST_CONTRACT, "action": action, "arguments": arguments or {}}

    def snapshot(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def test_status_delegates_exactly_and_preserves_result(self):
        root = self.root()
        delegated = {"contract": "reasoning-distiller-status/1", "status": "PASS", "next_action": "INSTALL"}
        with patch("ril_orchestrator.classify_status", return_value=delegated) as primitive:
            result = orchestrate(root, self.request("STATUS"), ROOT)
        primitive.assert_called_once_with(root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["primitive"], "ril_status.classify_status")
        self.assertIs(result["result"], delegated)

    def test_read_only_route_creates_no_artifacts(self):
        root = self.root()
        before = self.snapshot(root)
        result = orchestrate(root, self.request("STATUS"), ROOT)
        after = self.snapshot(root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(before, after)

    def test_unknown_action_fails_without_calling_any_primitive(self):
        root = self.root()
        with patch("ril_orchestrator.classify_status") as status, patch("ril_orchestrator.verify_storage") as storage:
            result = orchestrate(root, self.request("MAKE_ME_STEWARD"), ROOT)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "UNKNOWN_ACTION"))
        status.assert_not_called()
        storage.assert_not_called()

    def test_request_shape_is_exact(self):
        root = self.root()
        request = self.request("STATUS")
        request["surprise"] = True
        result = orchestrate(root, request, ROOT)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "INVALID_ORCHESTRATOR_REQUEST"))

    def test_action_arguments_are_exact(self):
        root = self.root()
        result = orchestrate(root, self.request("STATUS", {"role_id": "steward:default"}), ROOT)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "INVALID_ACTION_ARGUMENTS"))

    def test_reconcile_forwards_user_supplied_authority_evidence_unchanged(self):
        root = self.root()
        activation = {"contract": "activation", "role_id": "role:user", "evidence": {"x": 1}}
        assessment = {"contract": "assessment", "semantic_status": "COMPATIBLE"}
        delegated = {"status": "FAIL", "outcome": "ACTIVATION_REJECTED"}
        args = {"candidate_path": "project-knowledge/submissions/c.json", "activation": activation, "assessment": assessment}
        with patch("ril_orchestrator.reconcile_candidate", return_value=delegated) as primitive:
            result = orchestrate(root, self.request("RECONCILE", args), ROOT)
        primitive.assert_called_once_with(root, Path(args["candidate_path"]), activation, assessment)
        self.assertIs(result["result"], delegated)
        self.assertEqual(result["result"]["status"], "FAIL")

    def test_admit_does_not_implicitly_verify_storage(self):
        root = self.root()
        delegated = {"status": "PASS", "outcome": "ADMITTED"}
        args = {"disposition_path": "project-knowledge/reconciliation/dispositions/d.json", "activation": {"a": 1}, "plan": {"p": 1}}
        with patch("ril_orchestrator.admit", return_value=delegated) as admission, patch("ril_orchestrator.verify_storage") as storage:
            result = orchestrate(root, self.request("ADMIT", args), ROOT)
        admission.assert_called_once_with(root, Path(args["disposition_path"]), args["activation"], args["plan"])
        storage.assert_not_called()
        self.assertIs(result["result"], delegated)

    def test_plan_approve_apply_are_separate_routes(self):
        root = self.root()
        proposal_result = {"status": "PASS", "outcome": "PLANNED", "proposal": {"x": 1}}
        with patch("ril_orchestrator.plan_initial_operator", return_value=proposal_result) as plan, patch("ril_orchestrator.approve_initial_operator") as approve, patch("ril_orchestrator.apply_initial_operator") as apply:
            result = orchestrate(root, self.request("INITIAL_OPERATOR_PLAN", {"operator_id": "operator:owner"}), ROOT)
        plan.assert_called_once_with(root, "operator:owner")
        approve.assert_not_called()
        apply.assert_not_called()
        self.assertIs(result["result"], proposal_result)

    def test_mutation_route_calls_selected_primitive_once_only(self):
        root = self.root()
        proposal = {"proposal": 1}
        approval = {"approval": 1}
        delegated = {"status": "PASS", "outcome": "APPLIED"}
        with patch("ril_orchestrator.apply_authorization_change", return_value=delegated) as selected, patch("ril_orchestrator.apply_role_submission") as other:
            result = orchestrate(root, self.request("STEWARD_AUTH_APPLY", {"proposal": proposal, "approval": approval}), ROOT)
        selected.assert_called_once_with(root, proposal, approval)
        other.assert_not_called()
        self.assertIs(result["result"], delegated)


if __name__ == "__main__":
    unittest.main()
