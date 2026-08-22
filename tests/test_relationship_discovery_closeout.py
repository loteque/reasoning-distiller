import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
EVALUATION = ROOT / "evaluation"
sys.path.insert(0, str(EVALUATION))

bench_spec = importlib.util.spec_from_file_location(
    "relationship_discovery_benchmark", EVALUATION / "relationship_discovery_benchmark.py"
)
bench = importlib.util.module_from_spec(bench_spec)
assert bench_spec.loader is not None
bench_spec.loader.exec_module(bench)

analysis_spec = importlib.util.spec_from_file_location(
    "relationship_analysis_result", EVALUATION / "relationship_analysis_result.py"
)
analysis = importlib.util.module_from_spec(analysis_spec)
assert analysis_spec.loader is not None
analysis_spec.loader.exec_module(analysis)

closeout_spec = importlib.util.spec_from_file_location(
    "relationship_discovery_closeout", EVALUATION / "relationship_discovery_closeout.py"
)
closeout = importlib.util.module_from_spec(closeout_spec)
assert closeout_spec.loader is not None
closeout_spec.loader.exec_module(closeout)


class RelationshipDiscoveryCloseoutTests(unittest.TestCase):
    def synthetic_pems(self, n=4):
        return bench.canonical_json_bytes(
            {
                "semantic": "pems/2",
                "project_id": "x",
                "records": [
                    {
                        "id": f"pems:proposition:{i:024x}",
                        "kind": "proposition",
                        "lifecycle": "current",
                        "data": {"statement": f"statement {i}"},
                    }
                    for i in range(n)
                ],
                "relations": [],
            }
        )

    def make_fixture(self, root: Path):
        pems_bytes = self.synthetic_pems()
        coverage = bench.build_coverage(
            pems_bytes,
            benchmark_id="b",
            repository_commit="c",
            expected_pems_sha256=hashlib.sha256(pems_bytes).hexdigest(),
            block_size=2,
        )
        batch_dir = root / "inputs"
        result_dir = root / "results"
        batch_dir.mkdir()
        result_dir.mkdir()
        for batch_meta in coverage["batches"]:
            batch = bench.materialize_batch(pems_bytes, coverage, batch_meta["batch_id"])
            (batch_dir / f"{batch_meta['batch_id']}.json").write_bytes(bench.canonical_json_bytes(batch) + b"\n")
            relations = []
            if batch_meta["batch_id"] == "A0-B00-B01":
                source = batch["left_records"][0]
                target = batch["right_records"][0]
                relations.append(
                    {
                        "from_record_id": source["id"],
                        "from_record_digest": analysis.candidate_record_digest(source),
                        "type": "supports",
                        "to_record_id": target["id"],
                        "to_record_digest": analysis.candidate_record_digest(target),
                        "rationale": "synthetic support",
                    }
                )
            result = analysis.finalize_result(
                {
                    "contract": analysis.RESULT_CONTRACT,
                    "benchmark_id": "b",
                    "batch_id": batch["batch_id"],
                    "input_batch_digest": batch["batch_digest"],
                    "algorithm_id": "A0-exhaustive/1",
                    "status": "COMPLETE",
                    "analyzer": {
                        "protocol": analysis.ANALYZER_PROTOCOL,
                        "model": "test-model",
                        "authority": "none",
                    },
                    "assessed_pair_count": batch["pair_count"],
                    "assessed_hypothesis_count": batch["pair_count"] * 7,
                    "candidate_relations": relations,
                }
            )
            (result_dir / f"{batch_meta['batch_id']}.result.json").write_bytes(
                bench.canonical_json_bytes(result) + b"\n"
            )
        return coverage, batch_dir, result_dir

    def report_template(self):
        return {
            "contract": bench.REPORT_CONTRACT,
            "identity": {
                "algorithm_id": "A0-exhaustive",
                "algorithm_version": "1",
                "implementation_digest": "sha256:x",
                "benchmark_id": "b",
                "benchmark_digest": "sha256:y",
                "execution_id": "e",
            },
            "hypothesis": {
                "algorithm_summary": "pre-result summary",
                "selection_rationale": "pre-result rationale",
                "expected_behavior": "pre-result expected behavior",
            },
            "method": {"summary": "exhaustive"},
            "metrics": {
                "baseline_recall_percent": {"status": "pending"},
                "baseline_relations": {"status": "pending"},
                "baseline_relations_covered": {"status": "pending"},
                "baseline_relations_missed": {"status": "pending"},
            },
            "misses": [],
            "notes": ["pre-result note"],
            "verdict": "INCOMPLETE",
        }

    def test_aggregate_requires_complete_exact_result_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage, batch_dir, result_dir = self.make_fixture(root)
            (result_dir / "A0-B00-B00.result.json").unlink()
            with self.assertRaisesRegex(ValueError, "exact complete result set"):
                closeout.aggregate_candidates(coverage, batch_dir=batch_dir, result_dir=result_dir)

    def test_aggregate_preserves_candidate_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage, batch_dir, result_dir = self.make_fixture(root)
            candidates = closeout.aggregate_candidates(coverage, batch_dir=batch_dir, result_dir=result_dir)
            self.assertEqual(3, candidates["source_result_count"])
            self.assertEqual(6, candidates["assessed_pair_count"])
            self.assertEqual(42, candidates["assessed_hypothesis_count"])
            self.assertEqual(1, candidates["candidate_relation_count"])
            relation = candidates["candidate_relations"][0]
            self.assertEqual("A0-B00-B01", relation["source_batch_id"])
            self.assertTrue(relation["source_result_digest"].startswith("sha256:"))
            closeout.validate_candidate_set(candidates, coverage)

    def test_finalize_report_preserves_pre_result_hypothesis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage, batch_dir, result_dir = self.make_fixture(root)
            candidates = closeout.aggregate_candidates(coverage, batch_dir=batch_dir, result_dir=result_dir)
            template = self.report_template()
            before = json.loads(json.dumps(template["hypothesis"]))
            report = closeout.finalize_report(template, coverage, candidates)
            self.assertEqual(before, report["hypothesis"])
            self.assertEqual("INCOMPLETE", report["verdict"])
            self.assertEqual(1, report["metrics"]["raw_candidate_relations"]["value"])
            self.assertEqual("pending", report["metrics"]["baseline_relations"]["status"])
            self.assertIn("fresh Steward semantic reconciliation", " ".join(report["notes"]))


if __name__ == "__main__":
    unittest.main()
