import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "evaluation" / "relationship_discovery_benchmark.py"
spec = importlib.util.spec_from_file_location("relationship_discovery_benchmark", MODULE_PATH)
bench = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bench)


class RelationshipDiscoveryBenchmarkTests(unittest.TestCase):
    def synthetic_pems(self, n=368):
        records = [
            {
                "id": f"pems:proposition:{i:024x}",
                "kind": "proposition",
                "lifecycle": "current",
                "data": {"statement": f"statement {i}"},
            }
            for i in range(n)
        ]
        records.append({"id": "source:x", "kind": "source", "lifecycle": "current", "data": {}})
        return bench.canonical_json_bytes({"semantic": "pems/2", "project_id": "x", "records": records, "relations": []})

    def test_a0_coverage_exact_counts(self):
        pems_bytes = self.synthetic_pems()
        digest = hashlib.sha256(pems_bytes).hexdigest()
        coverage = bench.build_coverage(
            pems_bytes,
            benchmark_id="b",
            repository_commit="c",
            expected_pems_sha256=digest,
            block_size=32,
        )
        self.assertEqual(368, coverage["eligible_propositions"])
        self.assertEqual(67528, coverage["expected_pair_count"])
        self.assertEqual(472696, coverage["expected_hypothesis_count"])
        self.assertEqual(12, len(coverage["blocks"]))
        self.assertEqual(78, len(coverage["batches"]))
        self.assertEqual([32] * 11 + [16], [block["count"] for block in coverage["blocks"]])
        bench.verify_coverage(coverage)

    def test_digest_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            bench.build_coverage(
                self.synthetic_pems(3),
                benchmark_id="b",
                repository_commit="c",
                expected_pems_sha256="0" * 64,
                block_size=32,
            )

    def test_duplicate_batch_fails_closed(self):
        pems_bytes = self.synthetic_pems(4)
        coverage = bench.build_coverage(
            pems_bytes,
            benchmark_id="b",
            repository_commit="c",
            expected_pems_sha256=hashlib.sha256(pems_bytes).hexdigest(),
            block_size=2,
        )
        coverage["batches"].append(dict(coverage["batches"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            bench.verify_coverage(coverage)

    def test_materialized_batch_binds_digest(self):
        pems_bytes = self.synthetic_pems(4)
        coverage = bench.build_coverage(
            pems_bytes,
            benchmark_id="b",
            repository_commit="c",
            expected_pems_sha256=hashlib.sha256(pems_bytes).hexdigest(),
            block_size=2,
        )
        payload = bench.materialize_batch(pems_bytes, coverage, "A0-B00-B01")
        self.assertEqual(4, payload["pair_count"])
        self.assertEqual(2, len(payload["left_records"]))
        self.assertEqual(2, len(payload["right_records"]))
        self.assertTrue(payload["batch_digest"].startswith("sha256:"))

    def test_report_requires_hypothesis(self):
        report = {
            "contract": bench.REPORT_CONTRACT,
            "identity": {
                "algorithm_id": "A0-exhaustive",
                "algorithm_version": "1",
                "implementation_digest": "sha256:x",
                "benchmark_id": "b",
                "benchmark_digest": "sha256:y",
                "execution_id": "e",
            },
            "hypothesis": {},
            "method": {"summary": "m"},
            "metrics": {"eligible_propositions": {"status": "measured", "value": 1}},
            "misses": [],
            "verdict": "INCOMPLETE",
        }
        with self.assertRaisesRegex(ValueError, "hypothesis.algorithm_summary"):
            bench.validate_report(report)

    def test_persisted_a0_report_is_bound_and_reproducible(self):
        report_path = ROOT / "evaluation" / "relationship-discovery" / "benchmark-v1" / "baseline" / "A0-exhaustive" / "report.json"
        markdown_path = report_path.with_suffix(".md")
        benchmark_path = ROOT / "evaluation" / "relationship-discovery" / "benchmark-v1" / "benchmark.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        bench.validate_report(report)
        implementation_digest = "sha256:" + hashlib.sha256(MODULE_PATH.read_bytes()).hexdigest()
        benchmark_digest = "sha256:" + hashlib.sha256(benchmark_path.read_bytes()).hexdigest()
        self.assertEqual(implementation_digest, report["identity"]["implementation_digest"])
        self.assertEqual(benchmark_digest, report["identity"]["benchmark_digest"])
        self.assertEqual(bench.render_report(report), markdown_path.read_text(encoding="utf-8"))

    def test_frozen_repository_corpus_matches_benchmark(self):
        pems_path = ROOT / "project-knowledge" / "canonical" / "pems2.jcs.json"
        if not pems_path.exists():
            self.skipTest("full repository PEMS is not present in this isolated test copy")
        benchmark_path = ROOT / "evaluation" / "relationship-discovery" / "benchmark-v1" / "benchmark.json"
        benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
        coverage = bench.build_coverage(
            pems_path.read_bytes(),
            benchmark_id=benchmark["benchmark_id"],
            repository_commit=benchmark["repository_commit"],
            expected_pems_sha256=benchmark["pems_sha256"],
            block_size=benchmark["a0"]["block_size"],
        )
        self.assertEqual(benchmark["expected"]["eligible_propositions"], coverage["eligible_propositions"])
        self.assertEqual(benchmark["expected"]["unordered_pairs"], coverage["expected_pair_count"])
        self.assertEqual(benchmark["expected"]["relationship_hypotheses"], coverage["expected_hypothesis_count"])
        self.assertEqual(78, len(coverage["batches"]))

    def test_report_render_preserves_hypothesis(self):
        report = {
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
                "algorithm_summary": "summary h",
                "selection_rationale": "rationale h",
                "expected_behavior": "expected h",
            },
            "method": {"summary": "method"},
            "metrics": {
                "pair_space_reduction_percent": {"status": "derived", "value": 0, "unit": "%"},
                "baseline_recall_percent": {"status": "pending"},
            },
            "misses": [],
            "verdict": "INCOMPLETE",
        }
        text = bench.render_report(report)
        self.assertIn("## Hypothesis", text)
        self.assertIn("summary h", text)
        self.assertIn("rationale h", text)
        self.assertIn("expected h", text)


if __name__ == "__main__":
    unittest.main()
