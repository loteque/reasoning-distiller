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

import ril_authority_grant as grants
import ril_cli as cli
import ril_workflow as workflows


class G6CliTopologyTests(unittest.TestCase):
    def make_workflow(self, root: Path) -> str:
        store, _ = cli._stores(root)
        payload = workflows.workflow_payload(
            requester="operator:alice",
            intent={"operations": ["role-registry.change"]},
            execution_mode="auto-advance",
        )
        auth = workflows.make_workflow_auth(payload, "operator:alice", confirmation="AUTO_ADVANCE")
        return workflows.create_workflow(store, workflows.make_workflow(payload, auth))

    def make_grant(self, root: Path, workflow_ref: str) -> str:
        _, store = cli._stores(root)
        payload = grants.grant_payload(
            grantor="operator:alice",
            workflow=workflow_ref,
            operations=["role-registry.change"],
            targets=[{"field": "role_id", "match": "exact", "value": "alpha"}],
            constraints=[],
            approvals_limit=2,
        )
        auth = grants.make_grant_auth(payload, "operator:alice")
        return grants.create_grant(store, grants.make_grant(payload, auth))

    def test_parser_exposes_remaining_resource_families(self):
        cases = [
            ["status"], ["repair"], ["canon", "verify"],
            ["operator", "disable", "operator:bob"],
            ["operator", "transfer-root", "operator:bob"],
            ["role", "submission", "create", "roles.json"],
            ["steward", "clear-admission"],
            ["authority-grant", "list"],
            ["workflow", "list", "--all"],
        ]
        p = cli.parser()
        for argv in cases:
            with self.subTest(argv=argv):
                self.assertIsNotNone(p.parse_args(argv).resource)

    def test_workflow_list_defaults_open_and_all_includes_terminal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ref = self.make_workflow(root)
            store, _ = cli._stores(root)
            auth = {"operator_id": "operator:alice", "method": "human_confirmation", "confirmation": "CANCEL_WORKFLOW", "subject": ref}
            workflows.cancel_workflow(store, ref, "operator:alice", auth)
            open_only = cli.execute(cli.parser().parse_args(["--project", str(root), "workflow", "list"]), root)
            all_items = cli.execute(cli.parser().parse_args(["--project", str(root), "workflow", "list", "--all"]), root)
            self.assertEqual(open_only["value"], [])
            self.assertEqual(len(all_items["value"]), 1)
            self.assertEqual(all_items["value"][0]["lifecycle"], "CANCELLED")

    def test_grant_view_uses_state_not_workflow_lifecycle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wf = self.make_workflow(root)
            ref = self.make_grant(root, wf)
            view = cli._grant_view(cli._stores(root)[1], ref, 0)
            self.assertEqual(view["state"], "ACTIVE")
            self.assertNotIn("lifecycle", view)

    def test_generic_show_supports_workflow_and_grant_events(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wf = self.make_workflow(root)
            wstore, gstore = cli._stores(root)
            wev = workflows.record_attempt_failure(wstore, wf, "test", expected_normative_head=None)
            wview = cli.inspect_typed(root, wev, 1)
            self.assertEqual(wview["reference"], wev)
            self.assertEqual(wview["parent"]["reference"], wf)

            grant_ref = self.make_grant(root, wf)
            auth = {"operator_id": "operator:alice", "method": "human_confirmation", "subject": grant_ref, "confirmation": "REVOKE_AUTHORITY_GRANT"}
            gev = grants.revoke_grant(gstore, grant_ref, "operator:alice", auth, expected_normative_head=None)
            gview = cli.inspect_typed(root, gev, 1)
            self.assertEqual(gview["reference"], gev)
            self.assertEqual(gview["parent"]["reference"], grant_ref)

    def test_generic_show_never_infers_bare_type(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                cli.inspect_typed(Path(td), "abc123", 0)

    def test_quiet_expanded_depth_fails_before_inspection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ns = cli.parser().parse_args(["--project", str(root), "--quiet", "show", "workflow:missing", "--depth=1"])
            result = cli.execute(ns, root)
            self.assertEqual((result["status"], result["outcome"]), ("FAIL", "QUIET_DEPTH_CONFLICT"))


if __name__ == "__main__":
    unittest.main()
