#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ril_mutation", ROOT / "runtime" / "ril_mutation.py")
rd = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(rd)


def set_value(state, change):
    result = dict(state)
    result[change["key"]] = change["value"]
    return result


class RilMutationTests(unittest.TestCase):
    def test_canonical_json_and_digest_are_deterministic(self):
        a = {"z": 1, "a": {"y": 2, "x": 3}}
        b = {"a": {"x": 3, "y": 2}, "z": 1}
        self.assertEqual(rd.canonical_json_bytes(a), rd.canonical_json_bytes(b))
        self.assertEqual(rd.digest(a), rd.digest(b))
        self.assertTrue(rd.canonical_json_bytes(a).endswith(b"\n"))

    def test_proposal_creation_has_no_filesystem_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            before = list(root.iterdir())
            proposal = rd.make_proposal("roles", "ADD", {}, {"key": "x", "value": 1})
            after = list(root.iterdir())
            self.assertEqual(before, after)
            self.assertEqual(proposal["contract"], rd.PROPOSAL_CONTRACT)

    def test_approval_binds_exact_proposal(self):
        p1 = rd.make_proposal("roles", "ADD", {}, {"key": "x", "value": 1})
        p2 = rd.make_proposal("roles", "ADD", {}, {"key": "x", "value": 2})
        approval = rd.make_approval(p1, "operator:owner", {"method": "test-human"})
        rd.validate_approval(approval, p1)
        with self.assertRaises(rd.ContractError) as cm:
            rd.validate_approval(approval, p2)
        self.assertEqual(cm.exception.code, "APPROVAL_MISMATCH")

    def test_apply_append_replay_and_idempotent_retry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            events = root / "events"
            current = root / "current.json"
            proposal = rd.make_proposal("roles", "ADD", {}, {"key": "role", "value": "steward"})
            approval = rd.make_approval(proposal, "operator:owner", {"method": "test-human"})

            first = rd.apply_transition(
                proposal=proposal,
                approval=approval,
                events_dir=events,
                projection_path=current,
                transition=set_value,
            )
            self.assertEqual((first["status"], first["outcome"]), ("PASS", "APPLIED"))
            self.assertEqual(len(list(events.glob("*.json"))), 1)
            replayed, history = rd.replay(events)
            self.assertEqual(replayed, {"role": "steward"})
            self.assertEqual(len(history), 1)
            self.assertEqual(rd.projection_status(events, current)["status"], "VALID")

            second = rd.apply_transition(
                proposal=proposal,
                approval=approval,
                events_dir=events,
                projection_path=current,
                transition=set_value,
            )
            self.assertEqual((second["status"], second["outcome"]), ("PASS", "NO_CHANGE"))
            self.assertEqual(len(list(events.glob("*.json"))), 1)

    def test_consumed_approval_cannot_authorize_later_transition(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            events = root / "events"
            current = root / "current.json"

            p1 = rd.make_proposal("roles", "ADD", {}, {"key": "x", "value": 1})
            a1 = rd.make_approval(p1, "operator:owner", {"method": "test-human"})
            self.assertEqual(rd.apply_transition(
                proposal=p1, approval=a1, events_dir=events, projection_path=current, transition=set_value
            )["outcome"], "APPLIED")

            state, _ = rd.replay(events)
            p2 = rd.make_proposal("roles", "UPDATE", state, {"key": "y", "value": 2})
            a2 = rd.make_approval(p2, "operator:owner", {"method": "test-human"})
            self.assertEqual(rd.apply_transition(
                proposal=p2, approval=a2, events_dir=events, projection_path=current, transition=set_value
            )["outcome"], "APPLIED")

            retry_old = rd.apply_transition(
                proposal=p1, approval=a1, events_dir=events, projection_path=current, transition=set_value
            )
            self.assertEqual((retry_old["status"], retry_old["outcome"]), ("FAIL", "APPROVAL_ALREADY_CONSUMED"))

    def test_stale_basis_fails_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            events = root / "events"
            current = root / "current.json"
            stale = rd.make_proposal("roles", "ADD", {}, {"key": "late", "value": 9})
            stale_approval = rd.make_approval(stale, "operator:owner", {"method": "test-human"})

            p1 = rd.make_proposal("roles", "ADD", {}, {"key": "x", "value": 1})
            a1 = rd.make_approval(p1, "operator:owner", {"method": "test-human"})
            rd.apply_transition(proposal=p1, approval=a1, events_dir=events, projection_path=current, transition=set_value)
            before = len(list(events.glob("*.json")))

            result = rd.apply_transition(
                proposal=stale, approval=stale_approval, events_dir=events, projection_path=current, transition=set_value
            )
            self.assertEqual((result["status"], result["outcome"]), ("FAIL", "STALE_BASIS"))
            self.assertEqual(len(list(events.glob("*.json"))), before)

    def test_missing_projection_is_rebuildable_and_rebuilt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            events = root / "events"
            current = root / "current.json"
            p = rd.make_proposal("roles", "ADD", {}, {"key": "x", "value": 1})
            a = rd.make_approval(p, "operator:owner", {"method": "test-human"})
            rd.apply_transition(proposal=p, approval=a, events_dir=events, projection_path=current, transition=set_value)
            current.unlink()
            self.assertEqual(rd.projection_status(events, current)["status"], "REBUILDABLE")
            rebuilt = rd.rebuild_projection(events, current)
            self.assertEqual((rebuilt["status"], rebuilt["outcome"]), ("PASS", "REBUILT"))
            self.assertEqual(rd.projection_status(events, current)["status"], "VALID")

    def test_conflicting_projection_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            events = root / "events"
            current = root / "current.json"
            p = rd.make_proposal("roles", "ADD", {}, {"key": "x", "value": 1})
            a = rd.make_approval(p, "operator:owner", {"method": "test-human"})
            rd.apply_transition(proposal=p, approval=a, events_dir=events, projection_path=current, transition=set_value)
            current.write_bytes(rd.canonical_json_bytes({"x": 999}))
            self.assertEqual(rd.projection_status(events, current)["status"], "CONFLICT")
            self.assertEqual(rd.rebuild_projection(events, current)["outcome"], "PROJECTION_CONFLICT")

    def test_event_chain_corruption_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            events = root / "events"
            current = root / "current.json"
            p = rd.make_proposal("roles", "ADD", {}, {"key": "x", "value": 1})
            a = rd.make_approval(p, "operator:owner", {"method": "test-human"})
            rd.apply_transition(proposal=p, approval=a, events_dir=events, projection_path=current, transition=set_value)
            event_path = events / "00000001.json"
            event = json.loads(event_path.read_text())
            event["result_digest"] = "sha256:" + "0" * 64
            event_path.write_bytes(rd.canonical_json_bytes(event))
            status = rd.projection_status(events, current)
            self.assertEqual(status["status"], "CONFLICT")
            self.assertEqual(status["reason_code"], "EVENT_CHAIN_CONFLICT")

    def test_event_files_are_exclusive_and_contiguous(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            events = root / "events"
            current = root / "current.json"
            events.mkdir()
            (events / "00000002.json").write_bytes(rd.canonical_json_bytes({"bad": True}))
            status = rd.projection_status(events, current)
            self.assertEqual(status["status"], "CONFLICT")
            self.assertEqual(status["reason_code"], "EVENT_SEQUENCE_CONFLICT")


if __name__ == "__main__":
    unittest.main()
