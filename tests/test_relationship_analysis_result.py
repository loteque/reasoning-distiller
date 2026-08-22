import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "evaluation" / "relationship_analysis_result.py"
spec = importlib.util.spec_from_file_location("relationship_analysis_result", MODULE_PATH)
result_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(result_mod)


def record(record_id):
    return {"id": record_id, "kind": "proposition", "lifecycle": "current", "data": {"statement": record_id}}


class RelationshipAnalysisResultTests(unittest.TestCase):
    def batch(self):
        a = record("pems:proposition:a")
        b = record("pems:proposition:b")
        payload = {
            "contract": "reasoning-distiller-relationship-analysis-batch/1",
            "benchmark_id": "benchmark",
            "batch_id": "A0-B00-B00",
            "pems_sha256": "sha256:" + "0" * 64,
            "pair_mode": "unique_within",
            "pair_count": 1,
            "relation_hypotheses": [],
            "left_records": [a, b],
            "right_records": [a, b],
        }
        payload["batch_digest"] = result_mod.digest(payload)
        return payload

    def valid_result(self):
        batch = self.batch()
        records = {r["id"]: r for r in batch["left_records"]}
        payload = {
            "contract": result_mod.RESULT_CONTRACT,
            "benchmark_id": "benchmark",
            "algorithm_id": "A0-exhaustive/1",
            "batch_id": batch["batch_id"],
            "input_batch_digest": batch["batch_digest"],
            "analyzer": {"protocol": result_mod.ANALYZER_PROTOCOL, "model": "test", "authority": "none"},
            "assessed_pair_count": 1,
            "assessed_hypothesis_count": 7,
            "candidate_relations": [{
                "from_record_id": "pems:proposition:a",
                "from_record_digest": result_mod.candidate_record_digest(records["pems:proposition:a"]),
                "type": "supports",
                "to_record_id": "pems:proposition:b",
                "to_record_digest": result_mod.candidate_record_digest(records["pems:proposition:b"]),
                "rationale": "A strengthens B.",
            }],
            "status": "COMPLETE",
        }
        return batch, result_mod.finalize_result(payload)

    def test_valid_result(self):
        batch, result = self.valid_result()
        result_mod.validate_result(result, batch)

    def test_incomplete_pair_attestation_fails(self):
        batch, result = self.valid_result()
        result["assessed_pair_count"] = 0
        payload = dict(result)
        payload.pop("result_digest")
        result["result_digest"] = result_mod.digest(payload)
        with self.assertRaisesRegex(ValueError, "pair count"):
            result_mod.validate_result(result, batch)

    def test_endpoint_digest_mismatch_fails(self):
        batch, result = self.valid_result()
        result["candidate_relations"][0]["from_record_digest"] = "sha256:" + "f" * 64
        payload = dict(result)
        payload.pop("result_digest")
        result["result_digest"] = result_mod.digest(payload)
        with self.assertRaisesRegex(ValueError, "from_record_digest mismatch"):
            result_mod.validate_result(result, batch)

    def test_result_digest_mismatch_fails(self):
        batch, result = self.valid_result()
        result["result_digest"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(ValueError, "result_digest mismatch"):
            result_mod.validate_result(result, batch)


if __name__ == "__main__":
    unittest.main()
