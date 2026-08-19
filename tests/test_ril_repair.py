from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_mutation import canonical_json_bytes, projection_status  # noqa: E402
from ril_operators import (  # noqa: E402
    EMPTY_OPERATOR_STATE,
    apply_initial_operator,
    approve_initial_operator,
    operator_paths,
    plan_initial_operator,
)
from ril_repair import repair_all, repair_domain  # noqa: E402
from ril_roles import DEFAULT_ROLE_STATE, role_paths  # noqa: E402
from ril_steward_authorization import EMPTY_AUTH_STATE, authorization_paths  # noqa: E402


class OrdinaryRepairR10Tests(unittest.TestCase):
    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "project-knowledge").mkdir()
        return root

    def establish_operator(self, root: Path) -> None:
        planned = plan_initial_operator(root, "operator:owner")
        approval = approve_initial_operator(planned["proposal"], "operator:owner")
        result = apply_initial_operator(root, planned["proposal"], approval)
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "APPLIED"))

    def event_snapshot(self, events_dir: Path) -> dict[str, bytes]:
        if not events_dir.exists():
            return {}
        return {p.name: p.read_bytes() for p in sorted(events_dir.glob("*.json"))}

    def test_missing_projection_rebuilds_exactly_without_touching_history(self):
        root = self.project()
        self.establish_operator(root)
        events_dir, projection = operator_paths(root)
        before = self.event_snapshot(events_dir)
        projection.unlink()

        result = repair_domain(root, "operator_registry")

        self.assertEqual((result["status"], result["outcome"]), ("PASS", "REBUILT"))
        self.assertEqual(before, self.event_snapshot(events_dir))
        status = projection_status(events_dir, projection, EMPTY_OPERATOR_STATE)
        self.assertEqual(status["status"], "VALID")

    def test_stale_projection_is_repaired_from_history(self):
        root = self.project()
        self.establish_operator(root)
        events_dir, projection = operator_paths(root)
        before_events = self.event_snapshot(events_dir)
        projection.write_bytes(canonical_json_bytes({"stale": True}))

        result = repair_domain(root, "operator_registry")

        self.assertEqual((result["status"], result["outcome"]), ("PASS", "REPAIRED"))
        self.assertEqual(before_events, self.event_snapshot(events_dir))
        self.assertEqual(projection_status(events_dir, projection, EMPTY_OPERATOR_STATE)["status"], "VALID")

    def test_malformed_regular_projection_is_repairable(self):
        root = self.project()
        self.establish_operator(root)
        events_dir, projection = operator_paths(root)
        before_events = self.event_snapshot(events_dir)
        projection.write_bytes(b"not-json\n")

        result = repair_domain(root, "operator_registry")

        self.assertEqual((result["status"], result["outcome"]), ("PASS", "REPAIRED"))
        self.assertEqual(before_events, self.event_snapshot(events_dir))
        self.assertEqual(projection_status(events_dir, projection, EMPTY_OPERATOR_STATE)["status"], "VALID")

    def test_valid_projection_is_idempotent_no_change(self):
        root = self.project()
        self.establish_operator(root)
        events_dir, projection = operator_paths(root)
        before_events = self.event_snapshot(events_dir)
        before_projection = projection.read_bytes()

        result = repair_domain(root, "operator_registry")

        self.assertEqual((result["status"], result["outcome"]), ("PASS", "NO_CHANGE"))
        self.assertEqual(before_events, self.event_snapshot(events_dir))
        self.assertEqual(before_projection, projection.read_bytes())

    def test_invalid_history_requires_exceptional_recovery_and_does_not_mutate_projection(self):
        root = self.project()
        self.establish_operator(root)
        events_dir, projection = operator_paths(root)
        before_projection = projection.read_bytes()
        (events_dir / "00000002.json").write_bytes(canonical_json_bytes({}))
        before_events = self.event_snapshot(events_dir)

        result = repair_domain(root, "operator_registry")

        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "EXCEPTIONAL_RECOVERY_REQUIRED"))
        self.assertEqual(before_projection, projection.read_bytes())
        self.assertEqual(before_events, self.event_snapshot(events_dir))

    def test_unsafe_projection_path_fails_closed(self):
        root = self.project()
        self.establish_operator(root)
        events_dir, projection = operator_paths(root)
        before_events = self.event_snapshot(events_dir)
        projection.unlink()
        target = root / "outside.json"
        target.write_bytes(b"sentinel\n")
        try:
            projection.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")

        result = repair_domain(root, "operator_registry")

        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "PROJECTION_PATH_CONFLICT"))
        self.assertEqual(target.read_bytes(), b"sentinel\n")
        self.assertEqual(before_events, self.event_snapshot(events_dir))

    def test_repair_all_preflights_all_histories_before_mutation(self):
        root = self.project()
        self.establish_operator(root)
        operator_events, operator_projection = operator_paths(root)
        stale = canonical_json_bytes({"stale": True})
        operator_projection.write_bytes(stale)

        role_events, _ = role_paths(root)
        role_events.mkdir(parents=True, exist_ok=True)
        (role_events / "00000001.json").write_bytes(canonical_json_bytes({}))

        before_operator_events = self.event_snapshot(operator_events)
        before_role_events = self.event_snapshot(role_events)
        result = repair_all(root)

        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "EXCEPTIONAL_RECOVERY_REQUIRED"))
        self.assertEqual(result["failed_domain"], "role_registry")
        self.assertEqual(operator_projection.read_bytes(), stale)
        self.assertEqual(before_operator_events, self.event_snapshot(operator_events))
        self.assertEqual(before_role_events, self.event_snapshot(role_events))

    def test_repair_all_rebuilds_all_missing_projections_deterministically(self):
        root = self.project()
        operator_events, operator_projection = operator_paths(root)
        role_events, role_projection = role_paths(root)
        auth_events, auth_projection = authorization_paths(root)
        self.assertFalse(operator_events.exists())
        self.assertFalse(role_events.exists())
        self.assertFalse(auth_events.exists())

        result = repair_all(root)

        self.assertEqual((result["status"], result["outcome"], result["domain"]), ("PASS", "REBUILT", "all"))
        self.assertEqual(operator_projection.read_bytes(), canonical_json_bytes(EMPTY_OPERATOR_STATE))
        self.assertEqual(role_projection.read_bytes(), canonical_json_bytes(DEFAULT_ROLE_STATE))
        self.assertEqual(auth_projection.read_bytes(), canonical_json_bytes(EMPTY_AUTH_STATE))
        self.assertFalse(operator_events.exists())
        self.assertFalse(role_events.exists())
        self.assertFalse(auth_events.exists())

    def test_repair_does_not_create_authority_or_protocol_state(self):
        root = self.project()
        result = repair_all(root)
        self.assertEqual(result["status"], "PASS")
        forbidden = [
            root / "project-knowledge" / "pems",
            root / "project-knowledge" / "cove",
            root / "project-knowledge" / "canonical",
            root / "project-knowledge" / "reconciliation",
            root / "project-knowledge" / "admission",
        ]
        self.assertTrue(all(not path.exists() for path in forbidden))


if __name__ == "__main__":
    unittest.main()
