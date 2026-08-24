"""P7 reproducibility gate for the closed P6 context-packaging candidate.

This suite perturbs only host-side representations and runtime ordering while
holding contracted semantic inputs and behavior identity fixed. It does not
add source discovery, persistence behavior, rendering, authority handling,
admission, canonical mutation, or production integration.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
P5_TEST = ROOT / "tests/test_context_packaging_pack_builder_p5.py"
sys.path.insert(0, str(ROOT))


def _load_p5_fixture_module():
    spec = importlib.util.spec_from_file_location("context_packaging_p5_fixture_p7", P5_TEST)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load closed P5 fixture module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reverse_mapping_insertion(value):
    """Change mapping insertion order without changing list/tuple semantics."""
    if isinstance(value, dict):
        return {
            key: _reverse_mapping_insertion(value[key])
            for key in reversed(tuple(value.keys()))
        }
    if isinstance(value, list):
        return [_reverse_mapping_insertion(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_reverse_mapping_insertion(item) for item in value)
    return value


def _apply_runtime_order_perturbation(p5, fx):
    fx["profile"] = _reverse_mapping_insertion(fx["profile"])
    fx["request"] = _reverse_mapping_insertion(fx["request"])
    fx["sources"] = [
        p5.ResolvedSource(
            _reverse_mapping_insertion(source.binding),
            source.content,
        )
        for source in reversed(fx["sources"])
    ]
    fx["projected"] = [
        p5.ProjectedKnowledge(
            canonical_snapshot_ref=_reverse_mapping_insertion(projected.canonical_snapshot_ref),
            pems=_reverse_mapping_insertion(projected.pems),
            causes=tuple(reversed(projected.causes)),
        )
        for projected in reversed(fx["projected"])
    ]
    fx["components"] = [
        _reverse_mapping_insertion(component)
        for component in reversed(fx["components"])
    ]


def _build_probe_payload():
    p5 = _load_p5_fixture_module()
    fx = p5._fixture(semantic_item=True)
    if os.environ.get("P7_ORDERING") == "reverse":
        _apply_runtime_order_perturbation(p5, fx)

    real_listdir = os.listdir
    real_iterdir = Path.iterdir
    if os.environ.get("P7_ENUM_ORDER") == "reverse":
        os.listdir = lambda path=".": list(reversed(real_listdir(path)))

        def reversed_iterdir(path):
            return iter(reversed(list(real_iterdir(path))))

        Path.iterdir = reversed_iterdir

    try:
        result = p5._build(fx)
    finally:
        os.listdir = real_listdir
        Path.iterdir = real_iterdir

    if not result.ok:
        raise RuntimeError(f"P7 probe build failed: {result.failure!r}")

    serialized = result.serialized_pack
    return {
        "serialized_pack_b64": base64.b64encode(serialized).decode("ascii"),
        "serialized_pack_sha256": "sha256:" + hashlib.sha256(serialized).hexdigest(),
        "pack_identity_sha256": result.pack["identity"]["pack_identity_sha256"],
        "host_path_separator": os.sep,
    }


def _run_probe(*, cwd: Path, tmpdir: Path, locale_name: str, timezone: str,
               unicode_host_text: str, python_utf8: str, ordering: str,
               enumeration: str):
    env = os.environ.copy()
    env.update(
        {
            "LC_ALL": locale_name,
            "LANG": locale_name,
            "TZ": timezone,
            "TMPDIR": str(tmpdir),
            "TMP": str(tmpdir),
            "TEMP": str(tmpdir),
            "P7_UNICODE_HOST_TEXT": unicode_host_text,
            "PYTHONUTF8": python_utf8,
            "P7_ORDERING": ordering,
            "P7_ENUM_ORDER": enumeration,
        }
    )
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--p7-probe"],
        cwd=cwd,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return json.loads(completed.stdout)


class P7ReproducibilityTests(unittest.TestCase):
    def test_pc29_pc46_host_perturbations_preserve_exact_pack_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cwd_nfc = root / "cwd-é-nfc"
            cwd_nfd = root / "cwd-e\u0301-nfd"
            tmp_nfc = root / "tmp-é-nfc"
            tmp_nfd = root / "tmp-e\u0301-nfd"
            for directory in (cwd_nfc, cwd_nfd, tmp_nfc, tmp_nfd):
                directory.mkdir()

            baseline = _run_probe(
                cwd=cwd_nfc,
                tmpdir=tmp_nfc,
                locale_name="C",
                timezone="UTC",
                unicode_host_text="é",
                python_utf8="0",
                ordering="native",
                enumeration="native",
            )
            perturbed = _run_probe(
                cwd=cwd_nfd,
                tmpdir=tmp_nfd,
                locale_name="C.UTF-8",
                timezone="America/Los_Angeles",
                unicode_host_text="e\u0301",
                python_utf8="1",
                ordering="reverse",
                enumeration="reverse",
            )

        self.assertEqual(
            perturbed["serialized_pack_b64"],
            baseline["serialized_pack_b64"],
        )
        self.assertEqual(
            perturbed["serialized_pack_sha256"],
            baseline["serialized_pack_sha256"],
        )
        self.assertEqual(
            perturbed["pack_identity_sha256"],
            baseline["pack_identity_sha256"],
        )

    def test_runtime_sequence_and_mapping_order_are_canonical(self):
        p5 = _load_p5_fixture_module()
        baseline_fx = p5._fixture(semantic_item=True)
        baseline = p5._build(baseline_fx)
        self.assertTrue(baseline.ok, baseline.failure)

        perturbed_fx = p5._fixture(semantic_item=True)
        _apply_runtime_order_perturbation(p5, perturbed_fx)
        perturbed = p5._build(perturbed_fx)
        self.assertTrue(perturbed.ok, perturbed.failure)

        self.assertEqual(perturbed.serialized_pack, baseline.serialized_pack)
        self.assertEqual(perturbed.pack["identity"], baseline.pack["identity"])
        self.assertEqual(perturbed.receipt, baseline.receipt)

    def test_host_paths_and_unicode_environment_do_not_leak_into_pack(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cwd = root / "cwd-e\u0301-backslash-\\-probe"
            tmpdir = root / "tmp-é-forward-slash-probe"
            cwd.mkdir()
            tmpdir.mkdir()
            probe = _run_probe(
                cwd=cwd,
                tmpdir=tmpdir,
                locale_name="C.UTF-8",
                timezone="Pacific/Honolulu",
                unicode_host_text="host-only-é-e\u0301-/\\",
                python_utf8="1",
                ordering="reverse",
                enumeration="reverse",
            )

        serialized = base64.b64decode(probe["serialized_pack_b64"], validate=True)
        for forbidden in (
            str(cwd).encode("utf-8"),
            str(tmpdir).encode("utf-8"),
            "host-only-é-e\u0301-/\\".encode("utf-8"),
        ):
            self.assertNotIn(forbidden, serialized)

    def test_toolchain_identity_change_is_visible_and_incompatible_change_fails(self):
        p5 = _load_p5_fixture_module()
        baseline = p5._build(p5._fixture(semantic_item=True))
        self.assertTrue(baseline.ok, baseline.failure)

        changed_fx = p5._fixture(semantic_item=True)
        validator = next(
            component
            for component in changed_fx["components"]
            if component["role"] == "pems_validator"
        )
        validator["immutable_identity"] = "git-blob:" + "0" * 40
        validator["raw_sha256"] = "sha256:" + "0" * 64
        changed = p5._build(changed_fx)
        self.assertTrue(changed.ok, changed.failure)
        self.assertNotEqual(changed.serialized_pack, baseline.serialized_pack)
        self.assertNotEqual(
            changed.pack["identity"]["manifest_sha256"],
            baseline.pack["identity"]["manifest_sha256"],
        )
        self.assertNotEqual(
            changed.pack["identity"]["pack_identity_sha256"],
            baseline.pack["identity"]["pack_identity_sha256"],
        )

        incompatible_fx = p5._fixture(semantic_item=True)
        closure = next(
            component
            for component in incompatible_fx["components"]
            if component["role"] == "closure_descriptor"
        )
        closure["immutable_identity"] = "git-blob:" + "f" * 40
        incompatible = p5._build(incompatible_fx)
        self.assertFalse(incompatible.ok)
        self.assertEqual(incompatible.failure["code"], "TOOLCHAIN_IDENTITY_MISMATCH")
        self.assertEqual(incompatible.failure["stage"], "toolchain")


if __name__ == "__main__":
    if "--p7-probe" in sys.argv:
        print(json.dumps(_build_probe_payload(), sort_keys=True))
    else:
        unittest.main()
