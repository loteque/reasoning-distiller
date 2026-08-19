from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from rd_bootstrap import bootstrap  # noqa: E402
from ril_mutation import canonical_json_bytes  # noqa: E402
from ril_operators import (  # noqa: E402
    apply_initial_operator,
    approve_initial_operator,
    operator_paths,
    plan_initial_operator,
)
from ril_roles import (  # noqa: E402
    SUBMISSION_CONTRACT,
    apply_role_submission,
    approve_role_submission,
    plan_role_submission,
    role_paths,
)
from ril_status import classify_status  # noqa: E402
from ril_steward_authorization import (  # noqa: E402
    apply_authorization_change,
    approve_authorization_change,
    plan_authorization_change,
)


class StatusR9Tests(unittest.TestCase):
    def project(self, installed: bool = False, bootstrapped: bool = False) -> Path:
        root = Path(tempfile.mkdtemp())
        if installed or bootstrapped:
            (root / ".reasoning-distiller").mkdir()
        if bootstrapped:
            code, result = bootstrap(root)
            self.assertEqual(code, 0, result)
        return root

    def establish_root(self, root: Path, operator_id: str = "operator:owner") -> None:
        planned = plan_initial_operator(root, operator_id)
        approval = approve_initial_operator(planned["proposal"], operator_id)
        result = apply_initial_operator(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))

    def submit_roles(self, root: Path, roles: list[dict], mode: str = "incremental", scope=None) -> None:
        submission = {
            "contract": SUBMISSION_CONTRACT,
            "mode": mode,
            "source": "test-agent",
            "scope": scope,
            "roles": roles,
        }
        planned = plan_role_submission(root, submission)
        if planned["outcome"] == "NO_CHANGE":
            return
        approval = approve_role_submission(planned["proposal"], "operator:owner")
        result = apply_role_submission(root, planned["proposal"], approval)
        self.assertEqual(result["status"], "PASS", result)

    def authorize(self, root: Path, scope: str, role_id: str) -> None:
        planned = plan_authorization_change(root, "AUTHORIZE", scope, role_id)
        approval = approve_authorization_change(planned["proposal"], "operator:owner")
        result = apply_authorization_change(root, planned["proposal"], approval)
        self.assertEqual(result["status"], "PASS", result)

    def tree_fingerprint(self, root: Path) -> list[tuple[str, str, str]]:
        rows = []
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                rows.append((rel, "symlink", str(path.readlink())))
            elif path.is_dir():
                rows.append((rel, "dir", ""))
            elif path.is_file():
                rows.append((rel, "file", hashlib.sha256(path.read_bytes()).hexdigest()))
            else:
                rows.append((rel, "other", ""))
        return rows

    def test_empty_target_reports_uninstalled(self):
        root = self.project()
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["installation"], "MISSING")
        self.assertEqual(result["lifecycle"], "UNINSTALLED")
        self.assertEqual(result["next_action"], "INSTALL")
        self.assertEqual(result["blocker"]["precedence"], 1)

    def test_installed_unbootstrapped_reports_bootstrap(self):
        root = self.project(installed=True)
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["installation"], "VALID")
        self.assertEqual(result["dimensions"]["project_bootstrap"], "MISSING")
        self.assertEqual(result["lifecycle"], "INSTALLED")
        self.assertEqual(result["next_action"], "BOOTSTRAP_PROJECT")

    def test_bootstrapped_without_operator_reports_first_use_ceremony(self):
        root = self.project(bootstrapped=True)
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["operator"], "MISSING")
        self.assertEqual(result["next_action"], "ESTABLISH_INITIAL_OPERATOR")
        self.assertEqual(result["blocker"]["precedence"], 4)

    def test_invalid_history_outranks_projection_and_authority(self):
        root = self.project(bootstrapped=True)
        self.establish_root(root)
        events, _ = operator_paths(root)
        event = events / "00000001.json"
        event.write_text("not-json\n", encoding="utf-8")
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["history_health"], "INVALID")
        self.assertEqual(result["next_action"], "REPAIR_HISTORY")
        self.assertEqual(result["blocker"]["precedence"], 2)

    def test_projection_conflict_outranks_missing_authority(self):
        root = self.project(bootstrapped=True)
        self.establish_root(root)
        _, projection = operator_paths(root)
        projection.write_bytes(canonical_json_bytes({"bad": True}))
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["projection_health"], "CONFLICT")
        self.assertEqual(result["next_action"], "REPAIR_PROJECTION")
        self.assertEqual(result["blocker"]["precedence"], 3)

    def test_missing_projection_is_rebuildable_but_not_rebuilt(self):
        root = self.project(bootstrapped=True)
        self.establish_root(root)
        _, role_projection = role_paths(root)
        self.assertFalse(role_projection.exists())
        before = self.tree_fingerprint(root)
        result = classify_status(root)
        after = self.tree_fingerprint(root)
        self.assertEqual(result["dimensions"]["role_registry"], "REBUILDABLE")
        self.assertEqual(result["dimensions"]["projection_health"], "REBUILDABLE")
        self.assertFalse(role_projection.exists())
        self.assertEqual(before, after)

    def test_authorization_scopes_are_independent(self):
        root = self.project(bootstrapped=True)
        self.establish_root(root)
        self.authorize(root, "semantic_reconciliation", "steward:default")
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["reconciliation_authority"], "AVAILABLE")
        self.assertEqual(result["dimensions"]["admission_authority"], "UNASSIGNED")

    def test_disabled_authorized_target_has_no_fallback(self):
        root = self.project(bootstrapped=True)
        self.establish_root(root)
        role = {
            "role_id": "project:steward-a",
            "title": "Project Steward A",
            "description": "Project role",
            "capabilities": ["project:semantic-review"],
        }
        self.submit_roles(root, [role])
        self.authorize(root, "semantic_reconciliation", "project:steward-a")
        self.submit_roles(root, [], mode="snapshot", scope={"role_ids": ["project:steward-a"]})
        (root / "project-knowledge" / "submissions" / "candidate.json").write_text("{}\n", encoding="utf-8")
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["reconciliation_authority"], "TARGET_UNAVAILABLE")
        self.assertEqual(result["next_action"], "RESTORE_RECONCILIATION_ROLE")
        self.assertEqual(result["blocker"]["precedence"], 5)

    def test_candidate_with_available_authority_requires_activation(self):
        root = self.project(bootstrapped=True)
        self.establish_root(root)
        self.authorize(root, "semantic_reconciliation", "steward:default")
        (root / "project-knowledge" / "submissions" / "candidate.json").write_text("junk\n", encoding="utf-8")
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["candidate"], "PENDING")
        self.assertEqual(result["dimensions"]["reconciliation"], "REQUIRED")
        self.assertEqual(result["next_action"], "PROVIDE_ACTIVATION_EVIDENCE")
        self.assertEqual(result["blocker"]["precedence"], 6)
        self.assertNotIn("VALID_SUBMISSION", str(result))

    def test_evidence_and_candidate_presence_never_claim_semantic_validity(self):
        root = self.project(bootstrapped=True)
        self.establish_root(root)
        evidence = root / "project-knowledge" / "evidence" / "opaque.bin"
        evidence.write_bytes(b"not validated evidence")
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["evidence"], "AVAILABLE")
        self.assertEqual(result["dimensions"]["candidate"], "NONE")
        self.assertEqual(result["next_action"], "RUN_DISTILLER")
        self.assertNotIn("SELECTED", str(result))
        self.assertNotIn("VALID_SUBMISSION", str(result))

    def test_status_is_strictly_read_only(self):
        root = self.project(bootstrapped=True)
        self.establish_root(root)
        (root / "project-knowledge" / "evidence" / "x.txt").write_text("x", encoding="utf-8")
        before = self.tree_fingerprint(root)
        first = classify_status(root)
        second = classify_status(root)
        after = self.tree_fingerprint(root)
        self.assertEqual(first, second)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
