#!/usr/bin/env python3
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


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


rd = load_module(RUNTIME_PATH, "rd_distill_ingest_test")


class DistillIngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
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
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (self.project / "docs").mkdir()
        (self.project / "docs" / "a.md").write_text("alpha\n", encoding="utf-8")
        (self.project / "docs" / "b.md").write_text("beta\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, specs=None, invocation_id="baseline"):
        config = rd.load_project_config(self.project)
        return rd.create_ingestion_artifacts(
            project_root=self.project,
            project_config=config,
            invocation_id=invocation_id,
            created_at="2026-08-20T09:37:00-07:00",
            specs=specs or ["docs/*.md"],
            context="first baseline",
            refs=["baseline:first"],
        )

    def test_ingest_builds_request_and_activation_bundle(self):
        result = self.build()
        request = json.loads(result["request_path"].read_text(encoding="utf-8"))
        bundle = json.loads(result["bundle_path"].read_text(encoding="utf-8"))
        self.assertEqual(request["contract"], "reasoning-distiller-invocation/1")
        self.assertEqual(bundle["contract"], "reasoning-distiller-activation-bundle/1")
        self.assertEqual([item["locator"] for item in request["evidence"]], ["docs/a.md", "docs/b.md"])
        self.assertEqual(request["evidence"], request["source_registry"])
        self.assertEqual(
            request["output"]["raw_candidate_path"],
            "project-knowledge/invocations/baseline.raw.json",
        )
        self.assertEqual(
            request["output"]["submission_path"],
            "project-knowledge/submissions/baseline.json",
        )

    def test_identical_inputs_are_byte_deterministic_and_idempotent(self):
        first = self.build()
        request_before = first["request_path"].read_bytes()
        bundle_before = first["bundle_path"].read_bytes()
        second = self.build()
        self.assertEqual(second["request_path"].read_bytes(), request_before)
        self.assertEqual(second["bundle_path"].read_bytes(), bundle_before)

    def test_source_ids_and_digests_are_automatic_and_stable(self):
        result = self.build(specs=["docs/a.md"])
        source = result["request"]["evidence"][0]
        expected_id = "src:file:" + hashlib.sha256(b"docs/a.md").hexdigest()[:24]
        expected_digest = "sha256:" + hashlib.sha256(
            (self.project / "docs/a.md").read_bytes()
        ).hexdigest()
        self.assertEqual(source["source_id"], expected_id)
        self.assertEqual(source["digest"], expected_digest)

    def test_directory_selection_recurses_and_sorts(self):
        nested = self.project / "docs" / "nested"
        nested.mkdir()
        (nested / "c.md").write_text("gamma\n", encoding="utf-8")
        locators = rd.expand_evidence_specs(self.project, ["docs"])
        self.assertEqual(locators, ["docs/a.md", "docs/b.md", "docs/nested/c.md"])

    def test_reserved_roots_are_excluded(self):
        (self.project / ".reasoning-distiller").mkdir()
        (self.project / ".reasoning-distiller" / "managed.txt").write_text(
            "managed\n", encoding="utf-8"
        )
        (self.project / "project-knowledge" / "old.json").write_text(
            "{}\n", encoding="utf-8"
        )
        locators = rd.expand_evidence_specs(self.project, ["**/*"])
        self.assertEqual(locators, ["docs/a.md", "docs/b.md"])
        with self.assertRaises(rd.InvocationFailure) as caught:
            rd.expand_evidence_specs(self.project, [".reasoning-distiller/**/*"])
        self.assertEqual(caught.exception.reason_code, "EVIDENCE_SPEC_EXCLUDED")

    def test_symlink_evidence_is_rejected(self):
        link = self.project / "docs" / "link.md"
        try:
            link.symlink_to(self.project / "docs" / "a.md")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(rd.InvocationFailure) as caught:
            rd.expand_evidence_specs(self.project, ["docs/link.md"])
        self.assertEqual(caught.exception.reason_code, "EVIDENCE_SYMLINK")

    def test_missing_project_config_fails_closed(self):
        (self.project / "project-knowledge" / "project.json").unlink()
        with self.assertRaises(rd.InvocationFailure) as caught:
            rd.load_project_config(self.project)
        self.assertEqual(caught.exception.reason_code, "PROJECT_NOT_BOOTSTRAPPED")

    def test_different_existing_ingestion_artifact_is_never_overwritten(self):
        first = self.build()
        original = first["request_path"].read_bytes()
        (self.project / "docs" / "a.md").write_text("changed\n", encoding="utf-8")
        with self.assertRaises(rd.InvocationFailure) as caught:
            self.build()
        self.assertEqual(caught.exception.reason_code, "INGESTION_OUTPUT_COLLISION")
        self.assertEqual(first["request_path"].read_bytes(), original)

    def test_dry_run_validates_without_writing(self):
        config = rd.load_project_config(self.project)
        result = rd.create_ingestion_artifacts(
            project_root=self.project,
            project_config=config,
            invocation_id="preview",
            created_at="2026-08-20T09:37:00-07:00",
            specs=["docs/a.md"],
            context=None,
            refs=[],
            write=False,
        )
        self.assertFalse(result["request_path"].exists())
        self.assertFalse(result["bundle_path"].exists())

    def test_scriptable_cli_requires_no_python_request_builder(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "ingest",
                "--project-root",
                str(self.project),
                "--evidence",
                "docs/*.md",
                "--invocation-id",
                "cli-baseline",
                "--created-at",
                "2026-08-20T09:37:00-07:00",
                "--context",
                "cli baseline",
                "--ref",
                "baseline:cli",
            ],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence_count"], 2)
        self.assertTrue(
            (self.project / "project-knowledge/invocations/cli-baseline.request.json").is_file()
        )
        self.assertTrue(
            (self.project / "project-knowledge/invocations/cli-baseline.bundle.json").is_file()
        )

    def test_scriptable_mode_requires_invocation_id(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "ingest",
                "--project-root",
                str(self.project),
                "--evidence",
                "docs/a.md",
            ],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, rd.EXIT_PREFLIGHT)
        result = json.loads(completed.stdout)
        self.assertEqual(result["reason_code"], "INVOCATION_ID_REQUIRED")

    def test_interactive_collection_supports_file_directory_and_glob(self):
        answers = iter(
            [
                "1", "docs/a.md",
                "2", "docs",
                "3", "docs/*.md",
                "4",
                "wizard",
                "2026-08-20T09:37:00-07:00",
                "wizard context",
                "baseline:wizard, contract:test",
            ]
        )
        specs, invocation_id, created_at, context, refs = rd.collect_interactive_inputs(
            input_fn=lambda _: next(answers),
        )
        self.assertEqual(specs, ["docs/a.md", "docs", "docs/*.md"])
        self.assertEqual(invocation_id, "wizard")
        self.assertEqual(created_at, "2026-08-20T09:37:00-07:00")
        self.assertEqual(context, "wizard context")
        self.assertEqual(refs, ["baseline:wizard", "contract:test"])


if __name__ == "__main__":
    unittest.main()
