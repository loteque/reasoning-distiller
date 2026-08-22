import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
RUNTIME = ROOT / "runtime"
EVALUATION = ROOT / "evaluation"
sys.path.insert(0, str(RUNTIME))
sys.path.insert(0, str(EVALUATION))

import ril_activation  # noqa: E402

recon_spec = importlib.util.spec_from_file_location(
    "relationship_discovery_reconciliation",
    EVALUATION / "relationship_discovery_reconciliation.py",
)
recon = importlib.util.module_from_spec(recon_spec)
assert recon_spec.loader is not None
recon_spec.loader.exec_module(recon)


ACTIVATION_DIGEST = "a81360a9a4ab349a377dd378b5ed55e7e4a28d45ca26f6de51888dfac477928b"
ACTIVATION_PATH = (
    ROOT
    / "project-knowledge"
    / "reconciliation"
    / "activation-evidence"
    / f"{ACTIVATION_DIGEST}.json"
)
INVOCATION_ID = "reconcile-relationship-discovery-a0-v1-20260821"


class RelationshipDiscoveryReconciliationTests(unittest.TestCase):
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
        self.assertEqual(result["outcome"], "ACTIVATION_ACCEPTED")
        self.assertEqual(result["scope"], "semantic_reconciliation")
        self.assertEqual(result["role_id"], "steward:default")
        self.assertEqual(result["invocation_id"], INVOCATION_ID)
        self.assertEqual(result["activation_digest"], f"sha256:{ACTIVATION_DIGEST}")
        self.assertEqual(before_pems, after_pems)
        self.assertEqual(before_cove, after_cove)

    def _synthetic_bundle(self, root: Path):
        result_dir = root / "results"
        result_dir.mkdir()
        raw_relations = [
            {
                "from_record_id": "pems:proposition:a",
                "from_record_digest": "sha256:a",
                "type": "supports",
                "to_record_id": "pems:proposition:b",
                "to_record_digest": "sha256:b",
                "rationale": "specific evidence strengthens the broader claim",
            },
            {
                "from_record_id": "pems:proposition:c",
                "from_record_digest": "sha256:c",
                "type": "depends_on",
                "to_record_id": "pems:proposition:d",
                "to_record_digest": "sha256:d",
                "rationale": "shared topic alone is not a dependency",
            },
        ]
        unsigned_result = {
            "candidate_relations": raw_relations,
            "batch_id": "A0-B00-B00",
        }
        result = dict(unsigned_result)
        result["result_digest"] = recon._digest(unsigned_result)
        (result_dir / "A0-B00-B00.result.json").write_text(
            json.dumps(result), encoding="utf-8"
        )

        aggregated = []
        for relation in raw_relations:
            item = dict(relation)
            item["source_batch_id"] = "A0-B00-B00"
            item["source_result_digest"] = result["result_digest"]
            aggregated.append(recon._candidate_identity(item))
        aggregated.sort(
            key=lambda relation: (
                relation["from_record_id"],
                relation["type"],
                relation["to_record_id"],
                relation["source_batch_id"],
            )
        )
        candidates = {
            "contract": recon.closeout.CANDIDATES_CONTRACT,
            "benchmark_id": "b",
            "algorithm_id": recon.A0_ALGORITHM_ID,
            "pems_sha256": "sha256:pems",
            "candidate_set_digest": "sha256:set",
            "candidate_relations_digest": recon._digest(aggregated),
            "candidate_relation_count": 2,
            "source_results": [
                {
                    "batch_id": "A0-B00-B00",
                    "result_digest": result["result_digest"],
                    "candidate_relation_count": 2,
                }
            ],
        }
        activation = {
            "contract": "reasoning-distiller-role-activation/1",
            "role_id": "steward:default",
            "method": "explicit_declaration",
            "context": {"invocation_id": "i", "source": "test"},
        }
        raw_candidates = recon.aggregate_raw_candidates(candidates, result_dir=result_dir)

        disposition_rows = []
        for index, candidate in enumerate(raw_candidates):
            recommended = index == 0
            assessment = {
                "semantic_status": "COMPATIBLE" if recommended else "INCOMPATIBLE",
                "admission_recommendation": "RECOMMEND" if recommended else "DO_NOT_RECOMMEND",
                "rationale": "synthetic final Steward judgment",
            }
            disposition_rows.append(
                {
                    "candidate_digest": recon.candidate_digest(candidate),
                    "relation": recon.relation_identity(candidate),
                    "assessment": assessment,
                }
            )

        recommended = [disposition_rows[0]["relation"]]
        payload = {
            "contract": recon.DISPOSITIONS_CONTRACT,
            "benchmark_id": "b",
            "algorithm_id": recon.A0_ALGORITHM_ID,
            "pems_sha256": "sha256:pems",
            "candidate_set_digest": "sha256:set",
            "candidate_relations_digest": candidates["candidate_relations_digest"],
            "activation": {
                "scope": "semantic_reconciliation",
                "role_id": "steward:default",
                "invocation_id": "i",
                "activation_digest": recon._activation_digest(activation),
            },
            "reviewed_candidate_count": 2,
            "dispositions": disposition_rows,
            "counts_by_relation_type": {
                "supports": {"recommended": 1, "rejected": 0},
                "depends_on": {"recommended": 0, "rejected": 1},
                "supersedes": {"recommended": 0, "rejected": 0},
                "contradicts": {"recommended": 0, "rejected": 0},
            },
            "recommended_relation_count": 1,
            "recommended_relations_digest": recon._digest(recommended),
        }
        payload["dispositions_digest"] = recon.dispositions_digest(payload)
        return candidates, activation, raw_candidates, payload

    def test_bundle_binds_every_candidate_and_derived_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidates, activation, raw_candidates, payload = self._synthetic_bundle(Path(tmp))
            recommended = recon.validate_dispositions(
                payload,
                candidates=candidates,
                raw_candidates=raw_candidates,
                activation=activation,
            )
            self.assertEqual(recommended, [payload["dispositions"][0]["relation"]])
            self.assertEqual(payload["reviewed_candidate_count"], 2)

    def test_missing_disposition_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidates, activation, raw_candidates, payload = self._synthetic_bundle(Path(tmp))
            payload["dispositions"].pop()
            payload["reviewed_candidate_count"] = 1
            payload["dispositions_digest"] = recon.dispositions_digest(payload)
            with self.assertRaisesRegex(ValueError, "every raw candidate"):
                recon.validate_dispositions(
                    payload,
                    candidates=candidates,
                    raw_candidates=raw_candidates,
                    activation=activation,
                )

    def test_disposition_does_not_mutate_canon(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidates, activation, raw_candidates, payload = self._synthetic_bundle(Path(tmp))
            before_pems = (ROOT / "project-knowledge" / "canonical" / "pems2.jcs.json").read_bytes()
            before_cove = (ROOT / "project-knowledge" / "canonical" / "cove1.jcs.json").read_bytes()
            recon.validate_dispositions(
                payload,
                candidates=candidates,
                raw_candidates=raw_candidates,
                activation=activation,
            )
            self.assertEqual(
                before_pems,
                (ROOT / "project-knowledge" / "canonical" / "pems2.jcs.json").read_bytes(),
            )
            self.assertEqual(
                before_cove,
                (ROOT / "project-knowledge" / "canonical" / "cove1.jcs.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
