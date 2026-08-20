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

import ril_cli as cli
import ril_mutation as mut
import ril_roles as roles


class G6FinalCliSurfaceTests(unittest.TestCase):
    def write(self, path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(mut.canonical_json_bytes(value))

    def test_final_resource_families_parse(self):
        p = cli.parser()
        cases = [
            ["candidate", "list"],
            ["candidate", "show", "candidate:abc"],
            ["proposal", "list"],
            ["approval", "list"],
            ["reconciliation", "run", "candidate:abc", "--activation", "a.json", "--assessment", "s.json"],
            ["admission", "run", "candidate:abc", "--activation", "a.json", "--plan", "p.json"],
            ["apply", "proposal.json", "--approval", "approval.json"],
            ["history"],
            ["history", "show", "workflow-event:abc"],
            ["role", "submission", "list"],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                self.assertIsNotNone(p.parse_args(argv).resource)

    def test_candidate_proposal_approval_inventories_are_type_specific(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            candidate = {"semantic": "rgp/1", "nodes": [], "edges": []}
            proposal = mut.make_proposal("x", "Y", {}, {"z": 1})
            approval = mut.make_approval(proposal, "operator:a")
            self.write(root / "project-knowledge/submissions/candidate.json", candidate)
            self.write(root / "project-knowledge/evidence/proposal.json", proposal)
            self.write(root / "project-knowledge/evidence/approval.json", approval)

            candidates = cli._inventory(root, "candidate")
            proposals = cli._inventory(root, "proposal")
            approvals = cli._inventory(root, "approval")
            self.assertEqual(len(candidates), 1)
            self.assertEqual(len(proposals), 1)
            self.assertEqual(len(approvals), 1)
            self.assertTrue(candidates[0]["reference"].startswith("candidate:"))
            self.assertTrue(proposals[0]["reference"].startswith("proposal:"))
            self.assertTrue(approvals[0]["reference"].startswith("approval:"))

            wrong = "proposal:" + candidates[0]["reference"].split(":", 1)[1]
            with self.assertRaises(ValueError):
                cli.inspect_typed(root, wrong, 0)

    def test_generic_show_for_content_artifact_is_depth_zero_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proposal = mut.make_proposal("x", "Y", {}, {"z": 1})
            self.write(root / "project-knowledge/evidence/proposal.json", proposal)
            ref = "proposal:" + mut.digest(proposal).split(":", 1)[1]
            shown = cli.inspect_typed(root, ref, 0)
            self.assertEqual(shown["reference"], ref)
            self.assertEqual(shown["maximum_supported_depth"], 0)
            with self.assertRaises(ValueError):
                cli.inspect_typed(root, ref, 1)

    def test_aggregate_history_refuses_global_chronology(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            event1 = {"contract": mut.EVENT_CONTRACT, "sequence": 1, "domain": "a", "operation": "X", "proposal_digest": "p", "approval_digest": "a", "basis_digest": "b", "result_digest": "r", "result_state": {}}
            event2 = {"contract": mut.EVENT_CONTRACT, "sequence": 1, "domain": "b", "operation": "Y", "proposal_digest": "p2", "approval_digest": "a2", "basis_digest": "b2", "result_digest": "r2", "result_state": {}}
            self.write(root / "project-knowledge/a/events/00000001.json", event1)
            self.write(root / "project-knowledge/b/events/00000001.json", event2)
            wf_store, grant_store = cli._stores(root)
            value = cli._history(root, wf_store, grant_store)
            self.assertEqual(value["ordering"], "domain-local-only")
            self.assertIsNone(value["global_sequence"])
            histories = {x["history"] for x in value["histories"]}
            self.assertIn("project-knowledge/a/events", histories)
            self.assertIn("project-knowledge/b/events", histories)

    def test_universal_apply_routes_role_through_grant_aware_boundary(self):
        original = cli.shared.g4.apply_role_submission_with_authority
        try:
            cli.shared.g4.apply_role_submission_with_authority = lambda root, store, proposal, approval: {"status": "PASS", "outcome": "ROUTED"}
            proposal = {"domain": roles.DOMAIN, "operation": roles.OPERATION}
            result = cli._universal_apply(Path("/tmp/project"), Path("/tmp/grants"), proposal, {})
            self.assertEqual(result["outcome"], "ROUTED")
        finally:
            cli.shared.g4.apply_role_submission_with_authority = original


if __name__ == "__main__":
    unittest.main()
