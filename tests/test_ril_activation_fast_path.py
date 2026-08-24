from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

import ril_activation as activation  # noqa: E402
import ril_cli as cli  # noqa: E402
import ril_mutation as mutation  # noqa: E402
from ril_operators import (  # noqa: E402
    apply_initial_operator,
    approve_initial_operator,
    plan_initial_operator,
)
from ril_roles import (  # noqa: E402
    SUBMISSION_CONTRACT,
    apply_role_submission,
    approve_role_submission,
    plan_role_submission,
)
from ril_steward_authorization import (  # noqa: E402
    apply_authorization_change,
    approve_authorization_change,
    authorization_paths,
    plan_authorization_change,
)


class ActivationFastPathTests(unittest.TestCase):
    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "project-knowledge").mkdir()
        planned = plan_initial_operator(root, "operator:owner")
        approval = approve_initial_operator(planned["proposal"], "operator:owner")
        result = apply_initial_operator(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))
        return root

    def authorization_change(self, root: Path, operation: str, scope: str, role_id: str) -> None:
        planned = plan_authorization_change(root, operation, scope, role_id)
        self.assertEqual((planned["status"], planned["outcome"]), ("PASS", "PLANNED"))
        approval = approve_authorization_change(planned["proposal"], "operator:owner")
        result = apply_authorization_change(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))

    def apply_submission(self, root: Path, submission: dict) -> None:
        planned = plan_role_submission(root, submission)
        self.assertEqual(planned["status"], "PASS")
        if planned["outcome"] == "NO_CHANGE":
            return
        approval = approve_role_submission(planned["proposal"], "operator:owner")
        result = apply_role_submission(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))

    def argv(self, root: Path, *, scope: str = "semantic_reconciliation", quiet: bool = False) -> list[str]:
        args = ["--project", str(root)]
        if quiet:
            args.append("--quiet")
        args.extend([
            "activation",
            "run",
            "--role",
            "steward:default",
            "--scope",
            scope,
            "--invocation-id",
            "invocation-fast-path-1",
            "--source",
            "interactive-agent-session",
        ])
        return args

    def run_cli(self, root: Path, *, scope: str = "semantic_reconciliation", quiet: bool = False):
        ns = cli.parser().parse_args(self.argv(root, scope=scope, quiet=quiet))
        return ns, cli.execute(ns)

    def test_public_activation_run_parser_surface(self):
        root = self.project()
        ns = cli.parser().parse_args(self.argv(root))
        self.assertEqual((ns.resource, ns.verb), ("activation", "run"))
        self.assertEqual(ns.role, "steward:default")
        self.assertEqual(ns.scope, "semantic_reconciliation")

    def test_authorized_fast_path_promotes_activation_result_and_returns_exact_artifact(self):
        root = self.project()
        self.authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        _, result = self.run_cli(root)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "ACTIVATION_ACCEPTED"))
        value = result["value"]
        artifact = value["activation"]
        self.assertEqual(artifact["contract"], activation.ACTIVATION_CONTRACT)
        self.assertEqual(artifact["role_id"], "steward:default")
        self.assertEqual(artifact["method"], "explicit_declaration")
        self.assertEqual(artifact["context"], {
            "invocation_id": "invocation-fast-path-1",
            "source": "interactive-agent-session",
        })
        expected_digest = mutation.digest(artifact)
        self.assertEqual(value["activation_digest"], expected_digest)
        self.assertEqual(value["validation"]["activation_digest"], expected_digest)

    def test_fast_path_has_no_candidate_or_review_prerequisite(self):
        root = self.project()
        self.authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        self.assertFalse((root / "project-knowledge" / "submissions").exists())
        self.assertFalse((root / "project-knowledge" / "reconciliation").exists())
        _, result = self.run_cli(root)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "ACTIVATION_ACCEPTED"))

    def test_fast_path_is_deterministic_and_mutation_free(self):
        root = self.project()
        self.authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        _, first = self.run_cli(root)
        _, second = self.run_cli(root)
        after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        self.assertEqual(first, second)
        self.assertEqual(before, after)

    def test_scopes_remain_independent_and_failure_is_not_hidden_in_pass_ok(self):
        root = self.project()
        self.authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        _, accepted = self.run_cli(root, scope="semantic_reconciliation")
        _, blocked = self.run_cli(root, scope="admission")
        self.assertEqual((accepted["status"], accepted["outcome"]), ("PASS", "ACTIVATION_ACCEPTED"))
        self.assertEqual((blocked["status"], blocked["outcome"]), ("FAIL", "SCOPE_UNASSIGNED"))

    def test_unknown_scope_is_owned_by_activation_primitive(self):
        root = self.project()
        ns = cli.parser().parse_args(self.argv(root, scope="not-a-scope"))
        result = cli.execute(ns)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "UNKNOWN_SCOPE"))

    def test_projection_conflict_fails_closed_at_top_level(self):
        root = self.project()
        self.authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        _, projection = authorization_paths(root)
        projection.write_bytes(mutation.canonical_json_bytes({"bad": True}))
        _, result = self.run_cli(root)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "AUTHORIZATION_PROJECTION_CONFLICT"))

    def test_accepted_artifact_is_not_a_durable_authority_token(self):
        root = self.project()
        self.authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        _, accepted = self.run_cli(root)
        self.assertEqual((accepted["status"], accepted["outcome"]), ("PASS", "ACTIVATION_ACCEPTED"))
        artifact = accepted["value"]["activation"]

        self.apply_submission(root, {
            "contract": SUBMISSION_CONTRACT,
            "mode": "incremental",
            "source": "test",
            "scope": None,
            "roles": [{
                "role_id": "project-steward",
                "title": "Project Steward",
                "description": "Project supplied Steward.",
                "capabilities": [],
            }],
        })
        self.authorization_change(root, "REASSIGN", "semantic_reconciliation", "project-steward")

        revalidated = activation.validate_activation(root, "semantic_reconciliation", artifact)
        self.assertEqual((revalidated["status"], revalidated["outcome"]), ("FAIL", "ROLE_NOT_AUTHORIZED_FOR_SCOPE"))

    def test_quiet_mode_emits_activation_digest(self):
        root = self.project()
        self.authorization_change(root, "AUTHORIZE", "semantic_reconciliation", "steward:default")
        ns, result = self.run_cli(root, quiet=True)
        self.assertEqual(cli.render(result, ns), result["value"]["activation_digest"])


if __name__ == "__main__":
    unittest.main()
