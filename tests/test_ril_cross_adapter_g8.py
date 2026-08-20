#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

import ril_authority_grant as grants
import ril_cli as cli
import ril_human_agent as human
import ril_mutation as mutation
import ril_operators as operator_registry
import ril_roles as roles
import ril_workflow as workflows


class G8CrossAdapterParityTests(unittest.TestCase):
    def write(self, path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(mutation.canonical_json_bytes(value))

    def workflow_definition(self, *, supersedes: str | None = None) -> dict:
        payload = workflows.workflow_payload(
            requester="operator:alice",
            intent={"subject": "roles", "operations": ["role-registry.change"]},
            execution_mode="operator-driven",
            supersedes=supersedes,
        )
        return workflows.make_workflow(
            payload,
            workflows.make_workflow_auth(payload, "operator:alice"),
        )

    def test_proposal_inspection_preserves_exact_normative_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proposal = mutation.make_proposal("example", "CHANGE", {}, {"x": 1})
            path = root / "project-knowledge/evidence/proposal.json"
            self.write(path, proposal)
            ref = human.proposal_reference(proposal)

            cli_view = cli.inspect_typed(root, ref, 0)
            agent_view = human.resume_proposal(ref, lambda requested: mutation.load_json(path))

            self.assertEqual(cli_view["reference"], ref)
            self.assertEqual(agent_view["proposal_reference"], ref)
            self.assertEqual(cli_view["artifact"], proposal)
            self.assertEqual(agent_view["proposal"], proposal)

    def test_direct_approval_artifact_and_d3_outcome_are_identical(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = {"version": 1}
            proposal = mutation.make_proposal("example", "CHANGE", state, {"version": 2})
            auth = {"method": "test-human"}
            proposal_path = root / "proposal.json"
            auth_path = root / "auth.json"
            self.write(proposal_path, proposal)
            self.write(auth_path, auth)

            original = cli.shared._descriptor
            try:
                cli.shared._descriptor = lambda project_root, value: {"current_state": state}
                ns = cli.parser().parse_args([
                    "--project", str(root),
                    "approve", str(proposal_path),
                    "--operator", "operator:alice",
                    "--auth", str(auth_path),
                ])
                cli_result = cli.execute(ns, root)
            finally:
                cli.shared._descriptor = original

            agent_result = human.direct_approve(
                proposal,
                "operator:alice",
                auth,
                lambda: state,
            )
            self.assertEqual(cli_result["status"], "PASS")
            self.assertEqual(agent_result["status"], "PASS")
            self.assertEqual(cli_result["value"], agent_result["approval"])
            self.assertEqual(cli_result["value"]["contract"], mutation.APPROVAL_V2_CONTRACT)
            self.assertEqual(
                cli_result["value"]["authority_basis"],
                {"kind": "direct-operator", "operator_id": "operator:alice", "authentication": auth},
            )

            stale_state = {"version": 99}
            original = cli.shared._descriptor
            try:
                cli.shared._descriptor = lambda project_root, value: {"current_state": stale_state}
                cli_stale = cli.execute(ns, root)
            finally:
                cli.shared._descriptor = original
            agent_stale = human.direct_approve(
                proposal,
                "operator:alice",
                auth,
                lambda: stale_state,
            )
            self.assertEqual(cli_stale["outcome"], "PROPOSAL_STALE")
            self.assertEqual(agent_stale["outcome"], "PROPOSAL_STALE")
            self.assertEqual(cli_stale["revalidation"], agent_stale["revalidation"])

    def test_workflow_creation_and_cancellation_emit_identical_references(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            cli_root = base / "cli"
            agent_root = base / "agent"
            definition = self.workflow_definition()
            definition_path = base / "workflow.json"
            self.write(definition_path, definition)

            cli_create = cli.execute(
                cli.parser().parse_args([
                    "--project", str(cli_root),
                    "workflow", "create", str(definition_path),
                ]),
                cli_root,
            )
            agent_create = human.create_durable_workflow(
                agent_root / ".reasoning-distiller/workflows",
                definition,
                persistence_disclosed=True,
            )
            self.assertEqual(cli_create["value"], agent_create["workflow"])
            ref = cli_create["value"]

            auth = {
                "operator_id": "operator:alice",
                "method": "human_confirmation",
                "confirmation": "CANCEL_WORKFLOW",
                "subject": ref,
            }
            auth_path = base / "cancel-auth.json"
            self.write(auth_path, auth)
            cli_cancel = cli.execute(
                cli.parser().parse_args([
                    "--project", str(cli_root),
                    "workflow", "cancel", ref,
                    "--operator", "operator:alice",
                    "--auth", str(auth_path),
                ]),
                cli_root,
            )
            agent_cancel = human.cancel_durable_workflow(
                agent_root / ".reasoning-distiller/workflows",
                ref,
                "operator:alice",
                auth,
            )
            self.assertEqual(cli_cancel["value"], agent_cancel)
            self.assertEqual(
                workflows.project_workflow(cli_root / ".reasoning-distiller/workflows", ref),
                workflows.project_workflow(agent_root / ".reasoning-distiller/workflows", ref),
            )

    def test_workflow_revision_and_materiality_acknowledgement_are_identical(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)

            # Revision parity.
            cli_root = base / "rev-cli"
            agent_root = base / "rev-agent"
            predecessor = self.workflow_definition()
            cli_store = cli_root / ".reasoning-distiller/workflows"
            agent_store = agent_root / ".reasoning-distiller/workflows"
            predecessor_ref = workflows.create_workflow(cli_store, predecessor)
            self.assertEqual(workflows.create_workflow(agent_store, predecessor), predecessor_ref)
            successor = self.workflow_definition(supersedes=predecessor_ref)
            successor_path = base / "successor.json"
            self.write(successor_path, successor)

            cli_revision = cli.execute(
                cli.parser().parse_args([
                    "--project", str(cli_root),
                    "workflow", "revise", predecessor_ref, str(successor_path),
                ]),
                cli_root,
            )
            agent_revision = human.revise_durable_workflow(
                agent_store,
                predecessor_ref,
                successor,
                expected_normative_head=None,
            )
            self.assertEqual(cli_revision["value"], agent_revision)
            self.assertEqual(
                workflows.project_workflow(cli_store, predecessor_ref),
                workflows.project_workflow(agent_store, predecessor_ref),
            )

            # Materiality acknowledgement parity.
            cli_root = base / "ack-cli"
            agent_root = base / "ack-agent"
            cli_store = cli_root / ".reasoning-distiller/workflows"
            agent_store = agent_root / ".reasoning-distiller/workflows"
            definition = self.workflow_definition()
            ref = workflows.create_workflow(cli_store, definition)
            self.assertEqual(workflows.create_workflow(agent_store, definition), ref)
            pause_cli = workflows.pause_materiality(
                cli_store,
                ref,
                {"fact": "material"},
                expected_normative_head=None,
            )
            pause_agent = workflows.pause_materiality(
                agent_store,
                ref,
                {"fact": "material"},
                expected_normative_head=None,
            )
            self.assertEqual(pause_cli, pause_agent)
            auth = {
                "operator_id": "operator:alice",
                "method": "human_confirmation",
                "confirmation": "ACKNOWLEDGE_MATERIALITY",
                "subject": pause_cli,
            }
            auth_path = base / "ack-auth.json"
            self.write(auth_path, auth)
            cli_ack = cli.execute(
                cli.parser().parse_args([
                    "--project", str(cli_root),
                    "workflow", "acknowledge", ref, pause_cli,
                    "--operator", "operator:alice",
                    "--auth", str(auth_path),
                ]),
                cli_root,
            )
            agent_ack = human.acknowledge_workflow_materiality(
                agent_store,
                ref,
                pause_agent,
                "operator:alice",
                auth,
            )
            self.assertEqual(cli_ack["value"], agent_ack)
            self.assertEqual(workflows.project_workflow(cli_store, ref), workflows.project_workflow(agent_store, ref))

    def test_workflow_continuation_uses_the_same_shared_orchestration_result(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            proposal = mutation.make_proposal("example", "CHANGE", {}, {"x": 1})
            proposal_path = base / "proposal.json"
            self.write(proposal_path, proposal)
            expected = {
                "contract": "reasoning-distiller-shared-orchestration-result/1",
                "status": "STOPPED",
                "outcome": "MATERIALITY_PAUSE",
                "materiality_pause": "workflow-event:pause",
            }
            calls: list[tuple] = []
            original = cli.shared.advance_auto_proposal
            try:
                def fake(*args, **kwargs):
                    calls.append((args, kwargs))
                    return expected

                cli.shared.advance_auto_proposal = fake
                cli_result = cli.execute(
                    cli.parser().parse_args([
                        "--project", str(base / "cli"),
                        "workflow", "continue", "workflow:w", str(proposal_path),
                        "--grant", "authority-grant:g",
                    ]),
                    base / "cli",
                )
                agent_result = human.continue_auto_workflow(
                    base / "agent",
                    base / "agent/.reasoning-distiller/workflows",
                    base / "agent/.reasoning-distiller/grants",
                    "workflow:w",
                    proposal,
                    grant_refs=["authority-grant:g"],
                )
            finally:
                cli.shared.advance_auto_proposal = original

            self.assertEqual(cli_result["value"], expected)
            self.assertEqual(agent_result, expected)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][0][3:], calls[1][0][3:])
            self.assertEqual(calls[0][1], calls[1][1])

    def test_authority_grant_creation_routes_identically_after_human_disclosure(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            definition = {"contract": grants.GRANT_CONTRACT, "payload": {}, "authentication": {}}
            definition_path = base / "grant.json"
            self.write(definition_path, definition)
            calls: list[tuple] = []
            original = cli.shared.g4.create_authorized_grant
            try:
                def fake(*args, **kwargs):
                    calls.append((args, kwargs))
                    return "authority-grant:canonical"

                cli.shared.g4.create_authorized_grant = fake
                cli_result = cli.execute(
                    cli.parser().parse_args([
                        "--project", str(base / "cli"),
                        "authority-grant", "create", str(definition_path),
                        "--workflow-scope-confirmed",
                    ]),
                    base / "cli",
                )
                agent_result = human.create_authority_grant(
                    base / "agent",
                    base / "agent/.reasoning-distiller/grants",
                    definition,
                    workflow_scope_confirmed=True,
                    prospective_delegation_disclosed=True,
                )
            finally:
                cli.shared.g4.create_authorized_grant = original

            self.assertEqual(cli_result["value"], "authority-grant:canonical")
            self.assertEqual(agent_result["grant"], "authority-grant:canonical")
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][0][2], calls[1][0][2])
            self.assertEqual(calls[0][1], calls[1][1])

            undisclosed = human.create_authority_grant(
                base / "agent",
                base / "agent/.reasoning-distiller/grants",
                definition,
                workflow_scope_confirmed=True,
                prospective_delegation_disclosed=False,
            )
            self.assertEqual(undisclosed["outcome"], "GRANT_PROSPECTIVE_DELEGATION_DISCLOSURE_REQUIRED")

    def test_authority_grant_revocation_emits_identical_event(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            cli_root = base / "cli"
            agent_root = base / "agent"
            cli_store = cli_root / ".reasoning-distiller/grants"
            agent_store = agent_root / ".reasoning-distiller/grants"
            payload = grants.grant_payload(
                grantor="operator:owner",
                workflow="workflow:w1",
                operations=["operator-registry.disable"],
                targets=[{"field": "operator_id", "match": "exact", "value": "operator:bob"}],
                constraints=[{"field": "operation", "predicate": "eq", "value": "DISABLE_OPERATOR"}],
                approvals_limit=2,
            )
            definition = grants.make_grant(payload, grants.make_grant_auth(payload, "operator:owner"))
            ref = grants.create_grant(cli_store, definition)
            self.assertEqual(grants.create_grant(agent_store, definition), ref)
            auth = {
                "operator_id": "operator:owner",
                "method": "human_confirmation",
                "subject": ref,
                "confirmation": "REVOKE_AUTHORITY_GRANT",
            }
            auth_path = base / "revoke-auth.json"
            self.write(auth_path, auth)

            cli_result = cli.execute(
                cli.parser().parse_args([
                    "--project", str(cli_root),
                    "authority-grant", "revoke", ref,
                    "--operator", "operator:owner",
                    "--auth", str(auth_path),
                ]),
                cli_root,
            )
            agent_result = human.revoke_authority_grant(
                agent_store,
                ref,
                "operator:owner",
                auth,
                expected_normative_head=None,
            )
            self.assertEqual(cli_result["value"], agent_result)
            self.assertEqual(grants.project_grant(cli_store, ref), grants.project_grant(agent_store, ref))

    def test_delegable_role_and_operator_apply_routes_match(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)

            role_proposal = mutation.make_proposal(roles.DOMAIN, roles.OPERATION, {}, {"changes": []})
            operator_proposal = mutation.make_proposal(
                operator_registry.DOMAIN,
                "DISABLE_OPERATOR",
                {},
                {"target_operator_id": "operator:bob"},
            )
            approval = {"sentinel": "approval"}

            cases = [
                (role_proposal, "role"),
                (operator_proposal, "operator-disable"),
            ]
            for proposal, marker in cases:
                calls: list[tuple] = []
                expected = {"contract": mutation.RESULT_CONTRACT, "status": "PASS", "outcome": marker}

                def fake_apply(*args):
                    calls.append(args)
                    return expected

                original_descriptor = human.shared._descriptor
                if marker == "role":
                    original_apply = cli.shared.g4.apply_role_submission_with_authority
                    cli.shared.g4.apply_role_submission_with_authority = fake_apply
                else:
                    original_apply = cli.shared.g4.apply_operator_change_with_authority
                    cli.shared.g4.apply_operator_change_with_authority = fake_apply
                try:
                    human.shared._descriptor = lambda project_root, value: {"apply": fake_apply}
                    cli_result = cli._universal_apply(base / "cli", base / "cli-grants", proposal, approval)
                    agent_result = human.apply_delegable_proposal(base / "agent", base / "agent-grants", proposal, approval)
                finally:
                    human.shared._descriptor = original_descriptor
                    if marker == "role":
                        cli.shared.g4.apply_role_submission_with_authority = original_apply
                    else:
                        cli.shared.g4.apply_operator_change_with_authority = original_apply

                self.assertEqual(cli_result, expected)
                self.assertEqual(agent_result, expected)
                self.assertEqual(len(calls), 2)
                self.assertEqual(calls[0][2:], calls[1][2:])


if __name__ == "__main__":
    unittest.main()
