#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime" / "rd_distill.py"
RGP_VALIDATOR_PATH = ROOT / "validators" / "rgp_validator.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


rd = load_module(RUNTIME_PATH, "rd_distill_test")
rgp = load_module(RGP_VALIDATOR_PATH, "rgp_validator_test")


class ProductionInvocationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        (self.project / "evidence").mkdir()
        (self.project / "project-knowledge" / "submissions").mkdir(parents=True)
        (self.project / "project-knowledge" / "invocations").mkdir(parents=True)
        self.evidence = self.project / "evidence" / "fact.txt"
        self.evidence.write_text("The pressure test passed.\n", encoding="utf-8")
        self.digest = "sha256:" + hashlib.sha256(self.evidence.read_bytes()).hexdigest()
        self.request = self.make_request("invocation-a", "a")
        self.candidate = {
            "records": [
                {
                    "temp_id": "r1",
                    "kind": "observation",
                    "statement": "The pressure test passed.",
                    "provenance": {"primary": ["src:test"]},
                }
            ]
        }

    def tearDown(self):
        self.tmp.cleanup()

    def make_request(self, invocation_id: str, suffix: str) -> dict:
        return {
            "contract": "reasoning-distiller-invocation/1",
            "invocation_id": invocation_id,
            "created_at": "2026-08-18T00:00:00-07:00",
            "project_root": ".",
            "evidence": [
                {
                    "source_id": "src:test",
                    "type": "repository_file",
                    "locator": "evidence/fact.txt",
                    "digest": self.digest,
                }
            ],
            "source_registry": [
                {
                    "source_id": "src:test",
                    "type": "repository_file",
                    "locator": "evidence/fact.txt",
                    "digest": self.digest,
                }
            ],
            "source_context": {"summary": "pressure test", "refs": ["case:1"]},
            "output": {
                "raw_candidate_path": f"project-knowledge/invocations/{suffix}.raw.json",
                "submission_path": f"project-knowledge/submissions/{suffix}.json",
            },
        }

    def write_request(self, request: dict, name: str = "request.json") -> Path:
        path = self.project / name
        path.write_text(json.dumps(request), encoding="utf-8")
        return path

    def raw_bytes(self, candidate: dict | None = None) -> bytes:
        value = self.candidate if candidate is None else candidate
        return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    def test_01_valid_fixed_evidence_persists_submission(self):
        request = rd.validate_request(self.request)
        result = rd.finalize(request, self.raw_bytes(), cwd=self.project)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue((self.project / result["raw_candidate_path"]).is_file())
        self.assertTrue((self.project / result["submission_path"]).is_file())

    def test_02_raw_candidate_is_preserved_without_posthoc_repair(self):
        raw = self.raw_bytes()
        result = rd.finalize(self.request, raw, cwd=self.project)
        stored_raw = (self.project / result["raw_candidate_path"]).read_bytes()
        self.assertEqual(stored_raw, raw)
        envelope = json.loads((self.project / result["submission_path"]).read_text(encoding="utf-8"))
        self.assertEqual(envelope["candidate_graph"], self.candidate)

    def test_03_invalid_rgp_is_preserved_but_not_submitted(self):
        invalid = {"records": [{"temp_id": "r1", "kind": "bogus", "statement": "bad"}]}
        with self.assertRaises(rd.InvocationFailure) as caught:
            rd.finalize(self.request, self.raw_bytes(invalid), cwd=self.project)
        self.assertEqual(caught.exception.stage, "validation")
        self.assertEqual(caught.exception.exit_code, 5)
        self.assertTrue((self.project / self.request["output"]["raw_candidate_path"]).is_file())
        self.assertFalse((self.project / self.request["output"]["submission_path"]).exists())

    def test_04_missing_evidence_fails_preflight(self):
        self.evidence.unlink()
        with self.assertRaises(rd.InvocationFailure) as caught:
            rd.preflight(self.request, cwd=self.project)
        self.assertEqual(caught.exception.stage, "preflight")
        self.assertEqual(caught.exception.reason_code, "EVIDENCE_UNRESOLVED")

    def test_05_digest_mismatch_fails_closed(self):
        self.evidence.write_text("changed\n", encoding="utf-8")
        with self.assertRaises(rd.InvocationFailure) as caught:
            rd.preflight(self.request, cwd=self.project)
        self.assertEqual(caught.exception.reason_code, "EVIDENCE_DIGEST_MISMATCH")

    def test_06_existing_output_collision_never_overwrites(self):
        first = rd.finalize(self.request, self.raw_bytes(), cwd=self.project)
        raw_path = self.project / first["raw_candidate_path"]
        original = raw_path.read_bytes()
        changed = {
            "records": [
                {
                    "temp_id": "r1",
                    "kind": "claim",
                    "statement": "A different candidate.",
                    "provenance": {"context": ["src:test"]},
                }
            ]
        }
        with self.assertRaises(rd.InvocationFailure) as caught:
            rd.finalize(self.request, self.raw_bytes(changed), cwd=self.project)
        self.assertEqual(caught.exception.stage, "persistence")
        self.assertEqual(raw_path.read_bytes(), original)

    def test_07_isolated_installed_runtime_has_no_source_repo_fallback(self):
        installed = self.project / ".reasoning-distiller"
        for rel in (
            "runtime/rd_distill.py",
            "runtime/rd_distill_core.py",
            "agents/distiller/DIRECTIVE.md",
            "validators/rgp_validator.py",
        ):
            source = ROOT / rel
            dest = installed / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        request_path = self.write_request(self.request)
        bundle_path = self.project / "bundle.json"
        completed = subprocess.run(
            [sys.executable, str(installed / "runtime" / "rd_distill.py"), "prepare", "--request", str(request_path), "--bundle-out", str(bundle_path)],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        self.assertEqual(bundle["contract"], "reasoning-distiller-activation-bundle/1")
        self.assertNotIn("github.com/loteque/reasoning-distiller", bundle_path.read_text(encoding="utf-8"))

    def test_08_project_owned_authority_and_canonical_bytes_are_unchanged(self):
        authority = self.project / "project-knowledge" / "authority.json"
        canonical = self.project / "project-knowledge" / "canonical.json"
        authority.write_bytes(b'{"steward":"project"}\n')
        canonical.write_bytes(b'{"records":[]}\n')
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (authority, canonical)}
        rd.finalize(self.request, self.raw_bytes(), cwd=self.project)
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (authority, canonical)}
        self.assertEqual(before, after)

    def test_09_independent_invocations_get_distinct_submission_identities(self):
        request_a = self.make_request("invocation-a", "a")
        request_b = self.make_request("invocation-b", "b")
        result_a = rd.finalize(request_a, self.raw_bytes(), cwd=self.project)
        result_b = rd.finalize(request_b, self.raw_bytes(), cwd=self.project)
        self.assertNotEqual(result_a["submission_id"], result_b["submission_id"])
        self.assertEqual(
            (self.project / result_a["raw_candidate_path"]).read_bytes(),
            (self.project / result_b["raw_candidate_path"]).read_bytes(),
        )

    def test_10_submission_is_consumable_by_rgp_submission_protocol_validator(self):
        result = rd.finalize(self.request, self.raw_bytes(), cwd=self.project)
        envelope = json.loads((self.project / result["submission_path"]).read_text(encoding="utf-8"))
        self.assertEqual(rgp.validate(envelope), [])
        self.assertEqual(envelope["producer"]["role"], "reasoning-distiller")
        self.assertEqual(envelope["status"], "candidate")

    def test_prepare_bundle_contains_only_fixed_evidence_and_registry(self):
        _, evidence = rd.preflight(self.request, cwd=self.project)
        bundle = rd.make_activation_bundle(self.request, evidence)
        self.assertEqual(len(bundle["evidence"]), 1)
        self.assertEqual(bundle["evidence"][0]["content"], "The pressure test passed.\n")
        self.assertEqual(bundle["source_registry"], self.request["source_registry"])

    def test_unregistered_candidate_provenance_is_rejected(self):
        candidate = {
            "records": [
                {
                    "temp_id": "r1",
                    "kind": "observation",
                    "statement": "Unknown source.",
                    "provenance": {"primary": ["src:unknown"]},
                }
            ]
        }
        with self.assertRaises(rd.InvocationFailure) as caught:
            rd.finalize(self.request, self.raw_bytes(candidate), cwd=self.project)
        self.assertEqual(caught.exception.reason_code, "UNRESOLVED_PROVENANCE")
        self.assertFalse((self.project / self.request["output"]["submission_path"]).exists())


if __name__ == "__main__":
    unittest.main()
