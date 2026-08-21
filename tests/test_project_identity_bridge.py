from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.rd_bootstrap import build_project_config, canonical_json

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ril_admission import first_admission_base  # noqa: E402
from ril_status import classify_status  # noqa: E402


class ProjectIdentityBridgeTests(unittest.TestCase):
    def identity(self) -> dict[str, str]:
        return {
            "id": "example-project",
            "name": "Example Project",
            "repository": "example/project",
            "summary": "Example project identity.",
        }

    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".reasoning-distiller").mkdir()
        for rel in ("evidence", "invocations", "submissions"):
            (root / "project-knowledge" / rel).mkdir(parents=True, exist_ok=True)
        (root / "project-knowledge/project.json").write_bytes(canonical_json(build_project_config(self.identity())))
        return root

    def test_v2_identity_is_valid_bootstrap_state(self):
        root = self.project()
        result = classify_status(root)
        self.assertEqual(result["dimensions"]["project_bootstrap"], "VALID")
        self.assertEqual(result["next_action"], "ESTABLISH_INITIAL_OPERATOR")

    def test_first_admission_base_reuses_exact_project_identity(self):
        root = self.project()
        base = first_admission_base(root)
        self.assertEqual(base["semantic"], "pems/2")
        self.assertEqual(base["project_id"], self.identity()["id"])
        self.assertEqual(base["relations"], [])
        self.assertEqual(len(base["records"]), 1)
        record = base["records"][0]
        self.assertEqual(record["id"], self.identity()["id"])
        self.assertEqual(record["kind"], "project")
        self.assertEqual(record["data"]["repository"], self.identity()["repository"])


if __name__ == "__main__":
    unittest.main()
