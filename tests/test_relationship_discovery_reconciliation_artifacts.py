import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
EVALUATION = ROOT / "evaluation"
sys.path.insert(0, str(EVALUATION))

recon_spec = importlib.util.spec_from_file_location(
    "relationship_discovery_reconciliation",
    EVALUATION / "relationship_discovery_reconciliation.py",
)
recon = importlib.util.module_from_spec(recon_spec)
assert recon_spec.loader is not None
recon_spec.loader.exec_module(recon)

materialize_spec = importlib.util.spec_from_file_location(
    "relationship_discovery_materialize_reconciliation",
    EVALUATION / "relationship_discovery_materialize_reconciliation.py",
)
materialize = importlib.util.module_from_spec(materialize_spec)
assert materialize_spec.loader is not None
materialize_spec.loader.exec_module(materialize)

BASE = EVALUATION / "relationship-discovery" / "benchmark-v1" / "baseline" / "A0-exhaustive"
ACTIVATION = (
    ROOT
    / "project-knowledge"
    / "reconciliation"
    / "activation-evidence"
    / "a81360a9a4ab349a377dd378b5ed55e7e4a28d45ca26f6de51888dfac477928b.json"
)
EXPECTED_PEMS = "sha256:217eaedc614420a904b1ccc637b46a7cefce5c4b54b98ae9d39615ad1af5be0e"
EXPECTED_BASELINE = "sha256:ab07f98f8e280a7008d60b12b31e0376eec3ea761b70979ffae32a39482b8efd"
EXPECTED_DISPOSITIONS = "sha256:6120a78291d48d4cda586dc7bbf6cb6fc2cff1e38f8373ad4c1c67a4b2ddbcd1"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class RelationshipDiscoveryReconciliationArtifactTests(unittest.TestCase):
    def test_persisted_reconciliation_is_complete_reproducible_and_bound_to_frozen_corpus(self):
        candidates = load(BASE / "candidates.json")
        self.assertEqual(candidates["pems_sha256"], EXPECTED_PEMS)

        activation = load(ACTIVATION)
        selection = load(BASE / "steward-selection.json")
        persisted = load(BASE / "steward-dispositions.json")
        raw_candidates = recon.aggregate_raw_candidates(candidates, result_dir=BASE / "batches")

        decisions = materialize.validate_selection(
            selection,
            candidates=candidates,
            raw_candidates=raw_candidates,
            activation=activation,
        )
        self.assertEqual(len(decisions), 1128)
        self.assertEqual(sum(decisions), 668)

        regenerated = materialize.build_dispositions(
            candidates=candidates,
            raw_candidates=raw_candidates,
            activation=activation,
            selection=selection,
        )
        self.assertEqual(regenerated, persisted)
        self.assertEqual(persisted["reviewed_candidate_count"], 1128)
        self.assertEqual(persisted["recommended_relation_count"], 668)
        self.assertEqual(persisted["recommended_relations_digest"], EXPECTED_BASELINE)
        self.assertEqual(persisted["dispositions_digest"], EXPECTED_DISPOSITIONS)
        self.assertEqual(
            persisted["counts_by_relation_type"],
            {
                "supports": {"recommended": 661, "rejected": 460},
                "depends_on": {"recommended": 7, "rejected": 0},
                "supersedes": {"recommended": 0, "rejected": 0},
                "contradicts": {"recommended": 0, "rejected": 0},
            },
        )

        report = load(BASE / "report.json")
        recon.bench.validate_report(report)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["metrics"]["baseline_relations"], {"status": "measured", "value": 668})
        self.assertEqual(report["metrics"]["baseline_relations_missed"], {"status": "derived", "value": 0})
        self.assertEqual(
            report["metrics"]["baseline_recall_percent"],
            {"status": "derived", "unit": "%", "value": 100.0},
        )
        self.assertEqual(
            recon.bench.render_report(report),
            (BASE / "report.md").read_text(encoding="utf-8"),
        )

    def test_selection_mutation_fails_closed(self):
        candidates = load(BASE / "candidates.json")
        activation = load(ACTIVATION)
        selection = load(BASE / "steward-selection.json")
        raw_candidates = recon.aggregate_raw_candidates(candidates, result_dir=BASE / "batches")
        damaged = copy.deepcopy(selection)
        damaged["decisions"] = "X" + damaged["decisions"][1:]
        with self.assertRaisesRegex(ValueError, "selection_digest mismatch"):
            materialize.validate_selection(
                damaged,
                candidates=candidates,
                raw_candidates=raw_candidates,
                activation=activation,
            )


if __name__ == "__main__":
    unittest.main()
