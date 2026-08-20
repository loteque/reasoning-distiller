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
import ril_human_agent as human
import ril_mutation as mutation


class G8ApprovalCompatibilityTests(unittest.TestCase):
    def write(self, path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(mutation.canonical_json_bytes(value))

    def test_new_v2_parity_preserves_legacy_v1_validation_and_inventory(self):
        proposal = mutation.make_proposal("example", "CHANGE", {}, {"x": 1})
        auth = {"method": "test-human"}
        legacy = mutation.make_approval(proposal, "operator:alice", auth)
        current = mutation.make_direct_approval_v2(proposal, "operator:alice", auth)

        mutation.validate_approval(legacy, proposal)
        mutation.validate_approval(current, proposal)
        self.assertEqual(human.approval_authority(legacy), {"kind": "direct", "operator": "operator:alice"})
        self.assertEqual(human.approval_authority(current), {"kind": "direct", "operator": "operator:alice"})

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write(root / "project-knowledge/evidence/legacy.json", legacy)
            self.write(root / "project-knowledge/evidence/current.json", current)
            inventory = cli._inventory(root, "approval")
            contracts = {item["artifact"]["contract"] for item in inventory}
            self.assertEqual(contracts, {mutation.APPROVAL_CONTRACT, mutation.APPROVAL_V2_CONTRACT})


if __name__ == "__main__":
    unittest.main()
