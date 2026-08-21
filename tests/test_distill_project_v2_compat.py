from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime" / "rd_distill.py"


def load_runtime():
    spec = importlib.util.spec_from_file_location("rd_distill_project_v2_test", RUNTIME_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rd = load_runtime()


class DistillProjectV2CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        (self.project / "project-knowledge").mkdir()
        (self.project / "docs").mkdir()
        (self.project / "docs" / "evidence.md").write_text("evidence\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def write_config(self, value):
        (self.project / "project-knowledge" / "project.json").write_text(
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def v2_config(self):
        return {
            "contract": "reasoning-distiller-project/2",
            "project": {
                "id": "example-project",
                "name": "Example Project",
                "repository": "example/project",
                "summary": "Explicit project-owned identity",
            },
            "paths": {
                "evidence": "project-knowledge/evidence",
                "invocations": "project-knowledge/invocations",
                "submissions": "project-knowledge/submissions",
            },
        }

    def test_v2_project_config_is_accepted_for_ingestion(self):
        self.write_config(self.v2_config())
        config = rd.load_project_config(self.project)
        result = rd.create_ingestion_artifacts(
            project_root=self.project,
            project_config=config,
            invocation_id="project-v2",
            created_at="2026-08-20T18:14:00-07:00",
            specs=["docs/evidence.md"],
            governed_specs=[],
            context="project v2 compatibility",
            refs=["contract:project-v2"],
            write=False,
        )
        self.assertEqual(result["request"]["invocation_id"], "project-v2")
        self.assertEqual(result["locators"], ["docs/evidence.md"])

    def test_legacy_v1_project_config_remains_accepted(self):
        self.write_config(
            {
                "contract": "reasoning-distiller-project/1",
                "paths": {
                    "evidence": "project-knowledge/evidence",
                    "invocations": "project-knowledge/invocations",
                    "submissions": "project-knowledge/submissions",
                },
            }
        )
        config = rd.load_project_config(self.project)
        self.assertEqual(config["contract"], "reasoning-distiller-project/1")

    def test_invalid_v2_identity_fails_closed(self):
        config = self.v2_config()
        config["project"]["summary"] = ""
        self.write_config(config)
        with self.assertRaises(rd.InvocationFailure) as caught:
            rd.load_project_config(self.project)
        self.assertEqual(caught.exception.reason_code, "PROJECT_CONFIG_INVALID")


if __name__ == "__main__":
    unittest.main()
