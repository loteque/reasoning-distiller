#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime" / "rd_distill.py"
INVOCATION_ID = "first-normative-baseline-v2r1-20260820"
REQUEST = ROOT / "project-knowledge" / "invocations" / f"{INVOCATION_ID}.request.json"
BUNDLE = ROOT / "project-knowledge" / "invocations" / f"{INVOCATION_ID}.bundle.json"
RAW = ROOT / "project-knowledge" / "invocations" / f"{INVOCATION_ID}.raw.json"
SUBMISSION = ROOT / "project-knowledge" / "submissions" / f"{INVOCATION_ID}.json"


class FirstNormativeBaselineV2R1ReplayGate(unittest.TestCase):
    def test_real_ingest_and_finalize_are_byte_equivalent(self):
        expected_request = REQUEST.read_bytes()
        expected_raw = RAW.read_bytes()
        expected_submission = SUBMISSION.read_bytes()
        if BUNDLE.exists():
            BUNDLE.unlink()

        ingest = subprocess.run(
            [
                sys.executable,
                str(RUNTIME),
                "ingest",
                "--project-root", ".",
                "--evidence", ".github/workflows/promote-release-source.yml",
                "--evidence", ".github/workflows/release-source-guard.yml",
                "--evidence", "docs/design/RIL_R16_R18_IMPLEMENTATION_CONFORMANCE_PLAN.md",
                "--governed-evidence", "docs/design/RIL_CLI_DESIGN_CONTRACT.md",
                "--governed-evidence", "docs/design/RIL_HUMAN_AGENT_DESIGN_CONTRACT.md",
                "--governed-evidence", "docs/design/RIL_WORKFLOW_DESIGN_CONTRACT.md",
                "--governed-evidence", "docs/packaging/INSTALLER_RUNNER_CONTRACT.md",
                "--governed-evidence", "docs/packaging/INSTALL_PACKAGE_CONTRACT.md",
                "--invocation-id", INVOCATION_ID,
                "--created-at", "2026-08-20T11:47:00-07:00",
                "--context", "Reviewed normative baseline v2r1 for Reasoning Distiller",
                "--ref", "baseline:first-distillation:v2r1",
                "--ref", "review:approved-corrections-1-8",
                "--ref", "supersedes-review-candidate:first-normative-baseline-v2-20260820",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(ingest.returncode, 0, ingest.stdout + ingest.stderr)
        ingest_result = json.loads(ingest.stdout)
        self.assertEqual(ingest_result["status"], "PASS")
        self.assertEqual(ingest_result["evidence_count"], 8)
        self.assertEqual(REQUEST.read_bytes(), expected_request)
        self.assertTrue(BUNDLE.is_file())

        bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        registry = bundle["source_registry"]
        self.assertEqual(len(registry), 8)
        self.assertEqual(
            sum(item["type"] == "governed_artifact" for item in registry),
            5,
        )
        self.assertEqual(
            sum(item["type"] == "repository_file" for item in registry),
            3,
        )

        finalize = subprocess.run(
            [
                sys.executable,
                str(RUNTIME),
                "finalize",
                "--request", str(REQUEST),
                "--raw-candidate", str(RAW),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(finalize.returncode, 0, finalize.stdout + finalize.stderr)
        finalize_result = json.loads(finalize.stdout)
        self.assertEqual(finalize_result["status"], "PASS")
        self.assertEqual(RAW.read_bytes(), expected_raw)
        self.assertEqual(SUBMISSION.read_bytes(), expected_submission)

        BUNDLE.unlink()


if __name__ == "__main__":
    unittest.main()
