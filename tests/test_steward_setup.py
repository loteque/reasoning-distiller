#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "runtime" / "rd_steward_setup.py"


class StewardSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        (self.project / ".reasoning-distiller").mkdir()
        pk = self.project / "project-knowledge"
        pk.mkdir()
        (pk / "project.json").write_text(json.dumps({
            "contract": "reasoning-distiller-project/1",
            "paths": {
                "evidence": "project-knowledge/evidence",
                "invocations": "project-knowledge/invocations",
                "submissions": "project-knowledge/submissions"
            }
        }, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cmd(self, *args: str):
        cp = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False)
        payload = json.loads(cp.stdout)
        return cp.returncode, payload

    def test_plan_is_non_mutating(self):
        code, r = self.run_cmd("plan", "--target", str(self.project), "--authority-holder", "project:steward-primary", "--scope", "semantic_reconciliation")
        self.assertEqual(code, 0)
        self.assertEqual(r["outcome"], "PLAN")
        self.assertFalse((self.project / "project-knowledge/governance").exists())

    def test_apply_requires_explicit_confirmation(self):
        code, r = self.run_cmd("apply", "--target", str(self.project), "--authority-holder", "project:steward-primary", "--scope", "semantic_reconciliation")
        self.assertEqual(code, 2)
        self.assertEqual(r["reason_code"], "CONFIRMATION_REQUIRED")
        self.assertFalse((self.project / "project-knowledge/governance").exists())

    def test_apply_persists_only_explicit_scope(self):
        code, r = self.run_cmd("apply", "--target", str(self.project), "--authority-holder", "project:steward-primary", "--scope", "semantic_reconciliation", "--confirm", "AUTHORIZE_STEWARD")
        self.assertEqual(code, 0)
        self.assertEqual(r["outcome"], "CREATED")
        auth = json.loads((self.project / "project-knowledge/governance/steward-authorization.json").read_text())
        self.assertEqual(auth["authority_holder"], "project:steward-primary")
        self.assertEqual(auth["scopes"], ["semantic_reconciliation"])
        self.assertNotIn("admission", auth["scopes"])
        self.assertFalse((self.project / "project-knowledge/PEMS").exists())
        self.assertFalse((self.project / "project-knowledge/COVE").exists())

    def test_no_scope_default(self):
        code, r = self.run_cmd("plan", "--target", str(self.project), "--authority-holder", "project:steward-primary")
        self.assertEqual(code, 2)
        self.assertEqual(r["reason_code"], "SCOPE_REQUIRED")

    def test_unknown_scope_fails_closed(self):
        code, r = self.run_cmd("plan", "--target", str(self.project), "--authority-holder", "project:steward-primary", "--scope", "everything")
        self.assertEqual(code, 2)
        self.assertEqual(r["reason_code"], "UNKNOWN_SCOPE")

    def test_exact_replay_is_idempotent(self):
        args = ("apply", "--target", str(self.project), "--authority-holder", "project:steward-primary", "--scope", "semantic_reconciliation", "--confirm", "AUTHORIZE_STEWARD")
        self.assertEqual(self.run_cmd(*args)[0], 0)
        code, r = self.run_cmd(*args)
        self.assertEqual(code, 0)
        self.assertEqual(r["outcome"], "ALREADY_AUTHORIZED")

    def test_different_authorization_never_overwrites(self):
        args = ("apply", "--target", str(self.project), "--authority-holder", "project:steward-primary", "--scope", "semantic_reconciliation", "--confirm", "AUTHORIZE_STEWARD")
        self.run_cmd(*args)
        before = (self.project / "project-knowledge/governance/steward-authorization.json").read_bytes()
        code, r = self.run_cmd("apply", "--target", str(self.project), "--authority-holder", "project:other", "--scope", "admission", "--confirm", "AUTHORIZE_STEWARD")
        self.assertEqual(code, 2)
        self.assertEqual(r["reason_code"], "AUTHORIZATION_CONFLICT")
        self.assertEqual(before, (self.project / "project-knowledge/governance/steward-authorization.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
