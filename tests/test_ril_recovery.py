import copy
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))

from ril_mutation import canonical_json_bytes, ContractError
from ril_operators import plan_initial_operator, approve_initial_operator, apply_initial_operator, operator_paths
from ril_recovery import plan_recovery, approve_recovery, apply_recovery, replay_recovered_domain
from ril_roles import role_paths, DEFAULT_ROLE_STATE


class RecoveryTests(unittest.TestCase):
    def root_project(self):
        td = tempfile.TemporaryDirectory(); root = Path(td.name)
        p = plan_initial_operator(root, "operator:root")["proposal"]
        a = approve_initial_operator(p, "operator:root")
        self.assertEqual(apply_initial_operator(root, p, a)["status"], "PASS")
        return td, root

    def damage_roles(self, root):
        events, _ = role_paths(root)
        events.mkdir(parents=True, exist_ok=True)
        (events / "00000001.json").write_bytes(b"not-json\n")
        return events

    def test_valid_history_cannot_be_recovered(self):
        td, root = self.root_project()
        with td:
            with self.assertRaises(ContractError) as cm:
                plan_recovery(root, "role_registry", DEFAULT_ROLE_STATE, {"method":"inspection","damage":"none"})
            self.assertEqual(cm.exception.code, "RECOVERY_NOT_REQUIRED")

    def test_root_only_evidence_backed_recovery_and_idempotence(self):
        td, root = self.root_project()
        with td:
            events = self.damage_roles(root); before = (events / "00000001.json").read_bytes()
            continuation = copy.deepcopy(DEFAULT_ROLE_STATE)
            p = plan_recovery(root, "role_registry", continuation, {"method":"manual_inspection","damage":{"file":"00000001.json"}})["proposal"]
            a = approve_recovery(root, p)
            r = apply_recovery(root, p, a)
            self.assertEqual((r["status"], r["outcome"]), ("PASS", "RECOVERED"))
            self.assertEqual((events / "00000001.json").read_bytes(), before)
            self.assertEqual(replay_recovered_domain(root, "role_registry"), continuation)
            self.assertEqual(apply_recovery(root, p, a)["outcome"], "NO_CHANGE")

    def test_delegated_operator_cannot_approve(self):
        td, root = self.root_project()
        with td:
            self.damage_roles(root)
            p = plan_recovery(root, "role_registry", DEFAULT_ROLE_STATE, {"method":"inspection","damage":"bad json"})["proposal"]
            a = approve_recovery(root, p); a["operator_id"] = "operator:delegate"
            self.assertEqual(apply_recovery(root, p, a)["outcome"], "ROOT_APPROVAL_REQUIRED")

    def test_changed_damage_after_approval_fails_closed(self):
        td, root = self.root_project()
        with td:
            events = self.damage_roles(root)
            p = plan_recovery(root, "role_registry", DEFAULT_ROLE_STATE, {"method":"inspection","damage":"bad json"})["proposal"]
            a = approve_recovery(root, p)
            (events / "00000001.json").write_bytes(b"different-damage\n")
            self.assertEqual(apply_recovery(root, p, a)["outcome"], "DAMAGED_HISTORY_CHANGED")

    def test_operator_recovery_requires_root_from_valid_prefix(self):
        td = tempfile.TemporaryDirectory(); root = Path(td.name)
        with td:
            events, _ = operator_paths(root); events.mkdir(parents=True)
            (events / "00000001.json").write_bytes(b"broken\n")
            p = plan_recovery(root, "operator_registry", {}, {"method":"inspection","damage":"first event broken"})["proposal"]
            with self.assertRaises(ContractError) as cm:
                approve_recovery(root, p)
            self.assertEqual(cm.exception.code, "ROOT_IDENTITY_UNAVAILABLE")

    def test_recovery_record_detects_later_damage_mutation(self):
        td, root = self.root_project()
        with td:
            events = self.damage_roles(root)
            p = plan_recovery(root, "role_registry", DEFAULT_ROLE_STATE, {"method":"inspection","damage":"bad json"})["proposal"]
            a = approve_recovery(root, p); self.assertEqual(apply_recovery(root, p, a)["status"], "PASS")
            (events / "00000002.json").write_bytes(b"new bytes\n")
            with self.assertRaises(ContractError) as cm:
                replay_recovered_domain(root, "role_registry")
            self.assertEqual(cm.exception.code, "DAMAGED_HISTORY_CHANGED")


if __name__ == "__main__": unittest.main()
