from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from rd_bootstrap import build_project_config, canonical_json  # noqa: E402
from ril_activation import make_explicit_activation  # noqa: E402
from ril_admission import (  # noqa: E402
    EMPTY_PEMS,
    PLAN_CONTRACT,
    _decode,
    admit,
    first_admission_base,
    jcs,
    sha256_bytes,
)
from ril_mutation import canonical_json_bytes  # noqa: E402
from ril_operators import apply_initial_operator, approve_initial_operator, plan_initial_operator  # noqa: E402
from ril_reconciliation import ASSESSMENT_CONTRACT, reconcile_candidate  # noqa: E402
from ril_steward_authorization import (  # noqa: E402
    apply_authorization_change,
    approve_authorization_change,
    plan_authorization_change,
)
from ril_storage_verification import verify_storage  # noqa: E402


class AdmissionR13Tests(unittest.TestCase):
    def identity(self) -> dict[str, str]:
        return {
            "id": "example-project",
            "name": "Example Project",
            "repository": "example/project",
            "summary": "Admission test project.",
        }

    def root(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "project-knowledge/submissions").mkdir(parents=True)
        (root / "project-knowledge/project.json").write_bytes(canonical_json(build_project_config(self.identity())))
        return root

    def establish(self, root: Path) -> None:
        plan = plan_initial_operator(root, "operator:owner")
        approval = approve_initial_operator(plan["proposal"], "operator:owner")
        self.assertEqual(apply_initial_operator(root, plan["proposal"], approval)["status"], "PASS")

    def auth(self, root: Path, scope: str) -> None:
        plan = plan_authorization_change(root, "AUTHORIZE", scope, "steward:default")
        approval = approve_authorization_change(plan["proposal"], "operator:owner")
        self.assertEqual(apply_authorization_change(root, plan["proposal"], approval)["status"], "PASS")

    def ready(self, recommendation: str = "RECOMMEND"):
        root = self.root()
        self.establish(root)
        self.auth(root, "semantic_reconciliation")
        candidate = root / "project-knowledge/submissions/candidate.json"
        candidate.write_bytes(canonical_json_bytes({"contract": "test-candidate/1", "claim": "x"}))
        reconciliation_activation = make_explicit_activation("steward:default", "invocation:reconcile", "test")
        assessment = {
            "contract": ASSESSMENT_CONTRACT,
            "semantic_status": "COMPATIBLE",
            "admission_recommendation": recommendation,
            "rationale": "reviewed",
        }
        result = reconcile_candidate(root, candidate, reconciliation_activation, assessment)
        self.assertEqual(result["status"], "PASS")
        return root, candidate, Path(result["disposition_path"])

    def plan(self, root: Path, base: dict | None = None, record_id: str = "record:1") -> dict:
        base = first_admission_base(root) if base is None else base
        return {
            "contract": PLAN_CONTRACT,
            "expected_base_sha256": sha256_bytes(jcs(base)),
            "reuse_record_ids": [],
            "record_updates": [],
            "new_records": [
                {
                    "id": record_id,
                    "kind": "proposition",
                    "lifecycle": "current",
                    "data": {
                        "statement": "x",
                        "proposition_kind": "claim",
                        "epistemic_role": "asserted",
                    },
                }
            ],
            "new_relations": [],
        }

    def activation(self):
        return make_explicit_activation("steward:default", "invocation:admit", "test")

    def test_independent_admission_authority_required(self):
        root, _, disposition = self.ready()
        result = admit(root, disposition, self.activation(), self.plan(root))
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "SCOPE_UNASSIGNED"))

    def test_recommendation_not_authority_and_defer_is_blocked(self):
        root, _, disposition = self.ready("DEFER")
        self.auth(root, "admission")
        result = admit(root, disposition, self.activation(), self.plan(root))
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "ADMISSION_NOT_RECOMMENDED"))

    def test_first_admission_requires_explicit_project_identity(self):
        root, _, disposition = self.ready()
        self.auth(root, "admission")
        (root / "project-knowledge/project.json").write_bytes(canonical_json({"contract": "reasoning-distiller-project/1", "paths": {"evidence": "project-knowledge/evidence", "invocations": "project-knowledge/invocations", "submissions": "project-knowledge/submissions"}}))
        result = admit(root, disposition, self.activation(), self.plan(root, EMPTY_PEMS))
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "PROJECT_IDENTITY_REQUIRED"))
        self.assertFalse((root / "project-knowledge/canonical").exists())

    def test_success_writes_schema_valid_project_seeded_pems_cove_and_evidence(self):
        root, _, disposition = self.ready()
        self.auth(root, "admission")
        result = admit(root, disposition, self.activation(), self.plan(root))
        self.assertEqual((result["status"], result["outcome"]), ("PASS", "ADMITTED"))
        pems = json.loads((root / result["pems_path"]).read_text())
        cove = json.loads((root / result["cove_path"]).read_text())
        self.assertEqual(_decode(cove["x"], cove["d"], cove["h"]), pems)
        self.assertEqual(pems["project_id"], self.identity()["id"])
        project_record = next(record for record in pems["records"] if record["id"] == pems["project_id"])
        self.assertEqual(project_record["kind"], "project")
        self.assertEqual(project_record["data"]["repository"], self.identity()["repository"])
        self.assertEqual(len(list((root / "project-knowledge/admission/receipts").glob("*.json"))), 1)
        self.assertEqual(len(list((root / "project-knowledge/admission/plans").glob("*.json"))), 1)
        verification = verify_storage(root, ROOT)
        self.assertEqual((verification["status"], verification["outcome"]), ("PASS", "VERIFIED"))

    def test_exact_retry_is_no_change(self):
        root, _, disposition = self.ready()
        self.auth(root, "admission")
        plan = self.plan(root)
        activation = self.activation()
        self.assertEqual(admit(root, disposition, activation, plan)["outcome"], "ADMITTED")
        self.assertEqual(admit(root, disposition, activation, plan)["outcome"], "NO_CHANGE")

    def test_candidate_change_after_reconciliation_is_rejected(self):
        root, candidate, disposition = self.ready()
        self.auth(root, "admission")
        candidate.write_bytes(canonical_json_bytes({"contract": "test-candidate/1", "claim": "changed"}))
        result = admit(root, disposition, self.activation(), self.plan(root))
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "CANDIDATE_CHANGED"))

    def test_stale_plan_is_rejected(self):
        root, _, disposition = self.ready()
        self.auth(root, "admission")
        (root / "project-knowledge/canonical").mkdir(parents=True)
        base = {"semantic": "pems/2", "records": [{"id": "existing", "kind": "observation", "data": {}}], "relations": []}
        (root / "project-knowledge/canonical/pems2.jcs.json").write_bytes(jcs(base))
        result = admit(root, disposition, self.activation(), self.plan(root))
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "BASE_MISMATCH"))

    def test_record_collision_is_rejected(self):
        root, _, disposition = self.ready()
        self.auth(root, "admission")
        base = {"semantic": "pems/2", "records": [{"id": "record:1", "kind": "observation", "data": {}}], "relations": []}
        canonical = root / "project-knowledge/canonical"
        canonical.mkdir(parents=True)
        (canonical / "pems2.jcs.json").write_bytes(jcs(base))
        plan = self.plan(root, base, "record:1")
        result = admit(root, disposition, self.activation(), plan)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "RECORD_ID_COLLISION"))

    def test_guarded_update_checks_before_state_and_kind(self):
        root, _, disposition = self.ready()
        self.auth(root, "admission")
        base = {"semantic": "pems/2", "records": [{"id": "record:1", "kind": "observation", "data": {"value": "old"}}], "relations": []}
        canonical = root / "project-knowledge/canonical"
        canonical.mkdir(parents=True)
        (canonical / "pems2.jcs.json").write_bytes(jcs(base))
        plan = {
            "contract": PLAN_CONTRACT,
            "expected_base_sha256": sha256_bytes(jcs(base)),
            "reuse_record_ids": ["record:1"],
            "record_updates": [
                {
                    "record_id": "record:1",
                    "expected_before_sha256": "0" * 64,
                    "replacement": {"id": "record:1", "kind": "observation", "data": {"value": "new"}},
                }
            ],
            "new_records": [],
            "new_relations": [],
        }
        result = admit(root, disposition, self.activation(), plan)
        self.assertEqual(result["outcome"], "RECORD_BEFORE_MISMATCH")

    def test_conflicting_second_admission_is_rejected(self):
        root, _, disposition = self.ready()
        self.auth(root, "admission")
        activation = self.activation()
        plan = self.plan(root)
        self.assertEqual(admit(root, disposition, activation, plan)["outcome"], "ADMITTED")
        changed = dict(plan)
        changed["new_records"] = [
            {
                "id": "record:2",
                "kind": "proposition",
                "lifecycle": "current",
                "data": {"statement": "y", "proposition_kind": "claim", "epistemic_role": "asserted"},
            }
        ]
        result = admit(root, disposition, activation, changed)
        self.assertEqual((result["status"], result["outcome"]), ("FAIL", "ADMISSION_CONFLICT"))


if __name__ == "__main__":
    unittest.main()
