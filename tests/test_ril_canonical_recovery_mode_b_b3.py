import copy
import hashlib
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_activation import make_explicit_activation
from ril_canonical_recovery_mode_b_disposition import apply_semantic_disposition

SHA = "1" * 64
BLOB = "2" * 40


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def put(root, relative, value):
    raw = compact(value) if not isinstance(value, bytes) else value
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}


class ModeBB3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        for name in ("canonical-recovery-mode-b-common.schema.json", "canonical-recovery-semantic-disposition.schema.json"):
            (self.root / "schemas" / name).write_bytes((ROOT / "schemas" / name).read_bytes())

        pems = b'{"relations":[]}'
        cove = b'{"relations":[]}'
        def identity(name, raw):
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            path = f"project-knowledge/canonical/{name}.jcs.json"
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_bytes(raw)
            return {"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "git_blob": blob}
        self.prestate = {"pems": identity("pems2", pems), "cove": identity("cove1", cove)}
        self.relations = [
            {"relation_id": "r:1", "from": "p:a", "to": "p:b", "kind": "supports"},
            {"relation_id": "r:2", "from": "p:b", "to": "p:c", "kind": "depends_on"},
        ]
        inventory = {"relations": [
            {"id": r["relation_id"], "from": r["from"], "to": r["to"], "kind": r["kind"], "index": i, "key_set": ["from","id","kind","to"]}
            for i, r in enumerate(self.relations)
        ]}
        inv_ref = put(self.root, "evidence/inventory.json", inventory)
        ordered = hashlib.sha256(compact(inventory["relations"]) + b"\n").hexdigest()
        damage = {
            "contract": "reasoning-distiller-canonical-recovery-damage-analysis/1",
            "project": {"project_id": "reasoning-distiller"},
            "prestate": self.prestate,
            "candidate_count": 0,
            "damage_set": {"additional_damage": False, "relation_count": 2, "ordered_relation_set_sha256": ordered},
            "evidence_inventory": inv_ref,
        }
        self.damage_ref = put(self.root, "evidence/damage.json", damage)
        self.evidence_ref = put(self.root, "evidence/source.json", b"source")
        self.activation = make_explicit_activation("steward:default", "b3-test", "test")
        self.activation_ref = put(self.root, "evidence/activation.json", self.activation)
        self.disposition = {
            "contract": "reasoning-distiller-canonical-recovery-semantic-disposition/1",
            "project": {"project_id": "reasoning-distiller"},
            "prestate": self.prestate,
            "damage_analysis": self.damage_ref,
            "ordered_relation_set_sha256": ordered,
            "activation": {"role_id": "steward:default", "invocation_id": "b3-test", "requested_scope": "semantic_reconciliation", "artifact": self.activation_ref},
            "outcome": "ACCEPT_REPAIR",
            "rationale": "Test judgment.",
            "uncertainty_treatment": "All values supported.",
            "values": [
                {**self.relations[0], "lifecycle": "current", "data": {}, "evidence": [self.evidence_ref], "rationale": "supported"},
                {**self.relations[1], "lifecycle": "historical", "data": {"dependency_kind": "structural"}, "evidence": [self.evidence_ref], "rationale": "supported"},
            ],
        }
        patcher = mock.patch("ril_canonical_recovery_mode_b_disposition.validate_activation", return_value={
            "status": "PASS", "outcome": "ACTIVATION_ACCEPTED",
            "activation_digest": "sha256:" + self.activation_ref["sha256"],
        })
        self.validate = patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def apply(self, value=None):
        return apply_semantic_disposition(self.root, self.disposition if value is None else value)

    def test_accept_is_recorded_and_identical_retry_is_no_change(self):
        first = self.apply()
        self.assertEqual(("PASS", "ACCEPT_REPAIR", 0), (first["status"], first["outcome"], first["candidate_count"]), first)
        path = self.root / first["disposition"]["path"]
        before = path.stat().st_mtime_ns
        second = self.apply()
        self.assertEqual(first, second)
        self.assertEqual(before, path.stat().st_mtime_ns)
        self.assertFalse((self.root / "project-knowledge/recovery/canonical-pems-cove-mode-b/active.json").exists())

    def test_reject_and_defer_are_persisted_failures_with_zero_candidates(self):
        for raw, expected in (("REJECT_REPAIR", "SEMANTIC_DISPOSITION_REJECTED"), ("DEFER_REPAIR", "SEMANTIC_DISPOSITION_DEFERRED")):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as td:
                value = copy.deepcopy(self.disposition)
                value["outcome"] = raw
                # Use distinct roots because conflict protection is intentionally strict.
                root = Path(td)
                import shutil
                shutil.copytree(self.root, root, dirs_exist_ok=True)
                result = apply_semantic_disposition(root, value)
                self.assertEqual(("FAIL", expected, 0), (result["status"], result["outcome"], result["candidate_count"]))

    def test_conflicting_second_disposition_fails_closed(self):
        self.assertEqual("PASS", self.apply()["status"])
        other = copy.deepcopy(self.disposition)
        other["rationale"] = "Conflicting judgment."
        result = self.apply(other)
        self.assertEqual(("FAIL", "SEMANTIC_DISPOSITION_MISMATCH", 0), (result["status"], result["outcome"], result["candidate_count"]))

    def test_synchronized_conflicting_dispositions_are_atomically_exclusive(self):
        other = copy.deepcopy(self.disposition)
        other["rationale"] = "Concurrent conflicting judgment."
        barrier = threading.Barrier(2)
        original = self.validate.side_effect

        def synchronized_validation(*args, **kwargs):
            barrier.wait(timeout=5)
            if original is not None:
                return original(*args, **kwargs)
            return self.validate.return_value

        self.validate.side_effect = synchronized_validation
        results = []

        def submit(value):
            results.append(self.apply(value))

        threads = [threading.Thread(target=submit, args=(value,)) for value in (self.disposition, other)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(["FAIL", "PASS"], sorted(result["status"] for result in results))
        self.assertEqual(
            ["ACCEPT_REPAIR", "SEMANTIC_DISPOSITION_MISMATCH"],
            sorted(result["outcome"] for result in results),
        )
        self.assertEqual(1, len(list((self.root / "project-knowledge/recovery/canonical-pems-cove-mode-b/semantic-dispositions").glob("*.json"))))

    def test_malformed_stored_disposition_identity_fails_closed(self):
        directory = self.root / "project-knowledge/recovery/canonical-pems-cove-mode-b/semantic-dispositions"
        directory.mkdir(parents=True)
        (directory / ("0" * 64 + ".json")).write_text("{}", encoding="utf-8")
        result = self.apply()
        self.assertEqual(("FAIL", "SEMANTIC_DISPOSITION_MISMATCH", 0), (result["status"], result["outcome"], result["candidate_count"]))
        self.assertEqual([], list((self.root / "project-knowledge/recovery/canonical-pems-cove-mode-b/semantic-disposition-results").glob("*.json")))

    def test_relation_coverage_order_identity_and_kind_are_exact(self):
        attacks = []
        for mutate in (
            lambda v: v["values"].pop(),
            lambda v: v["values"].reverse(),
            lambda v: v["values"].__setitem__(1, copy.deepcopy(v["values"][0])),
            lambda v: v["values"][0].__setitem__("from", "p:wrong"),
            lambda v: v.__setitem__("ordered_relation_set_sha256", "0" * 64),
        ):
            value = copy.deepcopy(self.disposition); mutate(value); attacks.append(value)
        for value in attacks:
            with self.subTest(value=value):
                self.assertEqual("MODE_B_DAMAGE_SET_MISMATCH", self.apply(value)["outcome"])

    def test_lifecycle_and_kind_specific_data_fail_closed(self):
        value = copy.deepcopy(self.disposition); value["values"][0]["lifecycle"] = "unknown"
        self.assertEqual("SEMANTIC_DISPOSITION_INVALID", self.apply(value)["outcome"])
        value = copy.deepcopy(self.disposition); value["values"][1]["data"] = {}
        self.assertEqual("SEMANTIC_DISPOSITION_INVALID", self.apply(value)["outcome"])
        value = copy.deepcopy(self.disposition); value["values"][0]["data"] = {"dependency_kind": "structural"}
        self.assertEqual("SEMANTIC_DISPOSITION_INVALID", self.apply(value)["outcome"])

    def test_prestate_damage_and_evidence_bindings_are_exact(self):
        value = copy.deepcopy(self.disposition); value["prestate"]["pems"]["sha256"] = "0" * 64
        self.assertEqual("SEMANTIC_DISPOSITION_MISMATCH", self.apply(value)["outcome"])
        value = copy.deepcopy(self.disposition); value["damage_analysis"]["sha256"] = "0" * 64
        self.assertEqual("SEMANTIC_DISPOSITION_MISMATCH", self.apply(value)["outcome"])
        value = copy.deepcopy(self.disposition); value["values"][0]["evidence"][0]["sha256"] = "0" * 64
        self.assertEqual("SEMANTIC_DISPOSITION_MISMATCH", self.apply(value)["outcome"])

    def test_r8_scope_role_invocation_and_activation_are_replayed(self):
        for field, wrong in (("requested_scope", "admission"), ("role_id", "other"), ("invocation_id", "other")):
            value = copy.deepcopy(self.disposition); value["activation"][field] = wrong
            self.assertIn(self.apply(value)["outcome"], {"SEMANTIC_DISPOSITION_INVALID", "SEMANTIC_ACTIVATION_INVALID"})
        self.validate.return_value = {"status": "FAIL", "outcome": "ROLE_UNAVAILABLE"}
        self.assertEqual("SEMANTIC_ACTIVATION_INVALID", self.apply()["outcome"])

    def test_unknown_fields_candidates_plans_and_empty_values_are_rejected(self):
        for field in ("candidate", "plan", "approval"):
            value = copy.deepcopy(self.disposition); value[field] = {}
            self.assertEqual("SEMANTIC_DISPOSITION_INVALID", self.apply(value)["outcome"])
        value = copy.deepcopy(self.disposition); value["values"] = []
        self.assertEqual("SEMANTIC_DISPOSITION_INVALID", self.apply(value)["outcome"])


if __name__ == "__main__":
    unittest.main()
