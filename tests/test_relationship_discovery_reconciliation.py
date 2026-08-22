import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
RUNTIME = ROOT / "runtime"
sys.path.insert(0, str(RUNTIME))

import ril_activation  # noqa: E402


ACTIVATION_DIGEST = "32e28aaee3d3ed0d22b858bd825643d2e557de85da519ab4ed9bd85d36b1b952"
ACTIVATION_PATH = (
    ROOT
    / "project-knowledge"
    / "reconciliation"
    / "activation-evidence"
    / f"{ACTIVATION_DIGEST}.json"
)
INVOCATION_ID = "reconcile-relationship-discovery-a0-v1-20260821"


class RelationshipDiscoveryReconciliationActivationTests(unittest.TestCase):
    def test_a0_reconciliation_activation_is_exact_and_authorized(self):
        raw = ACTIVATION_PATH.read_bytes()
        self.assertTrue(raw.endswith(b"\n"))
        artifact = json.loads(raw)
        self.assertEqual(
            hashlib.sha256(ril_activation.canonical_json_bytes(artifact)).hexdigest(),
            ACTIVATION_DIGEST,
        )
        self.assertEqual(artifact["role_id"], "steward:default")
        self.assertEqual(artifact["context"]["invocation_id"], INVOCATION_ID)

        before_pems = (ROOT / "project-knowledge" / "canonical" / "pems2.jcs.json").read_bytes()
        before_cove = (ROOT / "project-knowledge" / "canonical" / "cove1.jcs.json").read_bytes()
        result = ril_activation.validate_activation(ROOT, "semantic_reconciliation", artifact)
        after_pems = (ROOT / "project-knowledge" / "canonical" / "pems2.jcs.json").read_bytes()
        after_cove = (ROOT / "project-knowledge" / "canonical" / "cove1.jcs.json").read_bytes()

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["code"], "ACTIVATION_ACCEPTED")
        self.assertEqual(result["scope"], "semantic_reconciliation")
        self.assertEqual(result["role_id"], "steward:default")
        self.assertEqual(result["invocation_id"], INVOCATION_ID)
        self.assertEqual(result["activation_digest"], f"sha256:{ACTIVATION_DIGEST}")
        self.assertEqual(before_pems, after_pems)
        self.assertEqual(before_cove, after_cove)


if __name__ == "__main__":
    unittest.main()
