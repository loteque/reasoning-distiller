from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime" / "rd_distill.py"


def load_runtime():
    spec = importlib.util.spec_from_file_location("rd_distill_governed_test", RUNTIME_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rd = load_runtime()


class GovernedIngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        (self.project / "project-knowledge").mkdir()
        (self.project / "project-knowledge" / "project.json").write_text(
            json.dumps(
                {
                    "contract": "reasoning-distiller-project/1",
                    "paths": {
                        "evidence": "project-knowledge/evidence",
                        "invocations": "project-knowledge/invocations",
                        "submissions": "project-knowledge/submissions",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (self.project / "docs").mkdir()
        (self.project / "docs" / "a.md").write_text("ordinary\n", encoding="utf-8")
        (self.project / "docs" / "b.md").write_text("governed\n", encoding="utf-8")
        (self.project / "docs" / "NORMATIVE_CONTRACT.md").write_text(
            "normative by filename only\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def create(self, *, specs=None, governed_specs=None, invocation_id="typed"):
        return rd.create_ingestion_artifacts(
            project_root=self.project,
            project_config=rd.load_project_config(self.project),
            invocation_id=invocation_id,
            created_at="2026-08-20T11:17:00-07:00",
            specs=list(specs or []),
            governed_specs=list(governed_specs or []),
            context="governed ingestion test",
            refs=["test:governed-ingestion"],
        )

    def test_explicit_governed_evidence_is_typed_and_stable(self):
        result = self.create(specs=["docs/a.md"], governed_specs=["docs/b.md"])
        by_locator = {
            item["locator"]: item for item in result["request"]["evidence"]
        }
        self.assertEqual(by_locator["docs/a.md"]["type"], "repository_file")
        self.assertEqual(by_locator["docs/b.md"]["type"], "governed_artifact")
        expected_regular = (
            "src:file:" + hashlib.sha256(b"docs/a.md").hexdigest()[:24]
        )
        expected_governed = (
            "src:governed:" + hashlib.sha256(b"docs/b.md").hexdigest()[:24]
        )
        self.assertEqual(by_locator["docs/a.md"]["source_id"], expected_regular)
        self.assertEqual(by_locator["docs/b.md"]["source_id"], expected_governed)

    def test_filename_does_not_infer_governed_authority(self):
        result = self.create(specs=["docs/NORMATIVE_CONTRACT.md"], invocation_id="name")
        source = result["request"]["evidence"][0]
        self.assertEqual(source["type"], "repository_file")
        self.assertTrue(source["source_id"].startswith("src:file:"))

    def test_conflicting_source_types_fail_closed(self):
        with self.assertRaises(rd.InvocationFailure) as caught:
            self.create(
                specs=["docs/a.md"],
                governed_specs=["docs/a.md"],
                invocation_id="conflict",
            )
        self.assertEqual(
            caught.exception.reason_code,
            "EVIDENCE_SOURCE_TYPE_CONFLICT",
        )

    def test_scriptable_cli_supports_governed_evidence(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "ingest",
                "--project-root",
                str(self.project),
                "--evidence",
                "docs/a.md",
                "--governed-evidence",
                "docs/b.md",
                "--invocation-id",
                "cli-governed",
                "--created-at",
                "2026-08-20T11:17:00-07:00",
            ],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        request_path = (
            self.project
            / "project-knowledge/invocations/cli-governed.request.json"
        )
        request = json.loads(request_path.read_text(encoding="utf-8"))
        by_locator = {item["locator"]: item for item in request["evidence"]}
        self.assertEqual(by_locator["docs/a.md"]["type"], "repository_file")
        self.assertEqual(by_locator["docs/b.md"]["type"], "governed_artifact")

    def test_cli_rejects_same_locator_with_both_types(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "ingest",
                "--project-root",
                str(self.project),
                "--evidence",
                "docs/a.md",
                "--governed-evidence",
                "docs/a.md",
                "--invocation-id",
                "cli-conflict",
                "--created-at",
                "2026-08-20T11:17:00-07:00",
            ],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, rd.EXIT_PREFLIGHT)
        result = json.loads(completed.stdout)
        self.assertEqual(result["reason_code"], "EVIDENCE_SOURCE_TYPE_CONFLICT")


if __name__ == "__main__":
    unittest.main()
