from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "e" * 40
V1_SCHEMA_BLOB = "4b240a5698294ce1a217ad758b4031830740fc29"
PEMS_BLOB = "cd7683d704e8aef2842a0c1b25b453fb1dbc8030"
PEMS_RAW_SHA256 = "sha256:b08e592ab7c10092ff381fe8057cac63ccb7aaa077b52532f5ee609c6fd279c3"
REF_SHA256 = "sha256:5755f841b1a7866cad4cfc0ee268f98bdff5a15c909d00bc66a7b7e3c7299da2"
REGISTRY_REL = Path("schemas/resources/context-packaging-v1-resource-registry.json")
SCHEMA_REL = Path("schemas/context-pack.schema.json")
PEMS_REL = Path("backends/pems-cove/pems-v2.schema.json")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("p10_pems_builder", ROOT / "packaging/build_release_package.py")
installer = load_module("p10_pems_installer", ROOT / "packaging/rd_install.py")
auditor = load_module("p10_pems_auditor", ROOT / "packaging/audit_runtime_isolation.py")


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


class P10PackagedPemsRuntimeIsolationRemediation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        release = builder.build("0.0.0-p10-pems-remediation", SOURCE_COMMIT, base / "release", ROOT)
        project = base / "project"
        project.mkdir()
        result = installer.install(
            release["archive"],
            release["manifest"],
            release["transport_sha256"],
            project,
        )
        self.assertEqual(result["status"], "PASS")
        self.installed = project / ".reasoning-distiller"

    def tearDown(self):
        self.tmp.cleanup()

    def test_frozen_v1_ref_is_closed_over_exact_packaged_pems_bytes(self):
        audit = auditor.audit(self.installed)
        self.assertEqual(audit["status"], "PASS", audit)

        schema_bytes = (self.installed / SCHEMA_REL).read_bytes()
        pems_bytes = (self.installed / PEMS_REL).read_bytes()
        registry = json.loads((self.installed / REGISTRY_REL).read_text(encoding="utf-8"))
        schema = json.loads(schema_bytes)
        pems = json.loads(pems_bytes)
        ref = schema["$defs"]["knowledgeItem"]["properties"]["pems"]["$ref"]

        self.assertEqual(git_blob_sha(schema_bytes), V1_SCHEMA_BLOB)
        self.assertEqual(git_blob_sha(pems_bytes), PEMS_BLOB)
        self.assertEqual("sha256:" + hashlib.sha256(pems_bytes).hexdigest(), PEMS_RAW_SHA256)
        self.assertEqual(sha256_text(ref), REF_SHA256)
        self.assertFalse(registry["resources"][0]["network_resolution"])
        self.assertEqual(registry["resources"][0]["resolution"], "register_exact_blob_bytes_under_frozen_source_ref")

        def forbid_retrieval(uri: str):
            raise AssertionError(f"unexpected external schema retrieval: {uri}")

        resource_registry = Registry(retrieve=forbid_retrieval).with_resource(ref, Resource.from_contents(pems))
        wrapper = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$ref": ref}
        validator = Draft202012Validator(wrapper, registry=resource_registry)
        good = {"semantic": "pems/2", "project_id": "p", "records": [], "relations": []}
        bad = dict(good)
        bad["semantic"] = "pems/1"
        self.assertFalse(list(validator.iter_errors(good)))
        self.assertTrue(list(validator.iter_errors(bad)))

    def test_missing_packaged_registry_fails_closed(self):
        (self.installed / REGISTRY_REL).unlink()
        audit = auditor.audit(self.installed)
        self.assertEqual(audit["status"], "FAIL")
        self.assertTrue(any(item["path"] == SCHEMA_REL.as_posix() for item in audit["violations"]))

    def test_pems_byte_drift_fails_closed(self):
        path = self.installed / PEMS_REL
        path.write_bytes(path.read_bytes() + b"\n")
        audit = auditor.audit(self.installed)
        self.assertEqual(audit["status"], "FAIL")
        self.assertTrue(any(item["path"] == SCHEMA_REL.as_posix() for item in audit["violations"]))


if __name__ == "__main__":
    unittest.main()
