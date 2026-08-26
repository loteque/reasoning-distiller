from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
P5_TEST = ROOT / "tests/test_context_packaging_pack_builder_p5.py"
sys.path.insert(0, str(ROOT))

import context_packaging.pack_builder as pack_builder_v2


def _load_p5_fixture_module():
    spec = importlib.util.spec_from_file_location(
        "context_packaging_p5_fixture_p7_source_resolver", P5_TEST
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class P7SourceResolverDependencyIdentity(unittest.TestCase):
    def test_behavior_bearing_source_resolver_mutation_fails_closed(self):
        p5 = _load_p5_fixture_module()
        baseline_fx = p5._fixture(semantic_item=True)
        baseline = p5._build(baseline_fx)
        self.assertTrue(baseline.ok, baseline.failure)

        changed_fx = p5._fixture(semantic_item=True)
        recorded_builder = dict(
            next(
                component
                for component in changed_fx["components"]
                if component["role"] == "pack_builder"
            )
        )
        source_path = Path(pack_builder_v2._source_resolver.__file__)
        source_raw = source_path.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            mutated = Path(td) / "source_resolver.py"
            mutated.write_bytes(
                source_raw
                + b"\n# P7 adversarial behavior-bearing dependency mutation\n"
                + b"def _snapshot_key(binding):\n"
                + b"    return ('mutated-source-resolver',)\n"
            )
            with patch.object(
                pack_builder_v2._source_resolver, "__file__", str(mutated)
            ):
                changed = p5._build(changed_fx)

        self.assertFalse(changed.ok)
        self.assertEqual(changed.failure["code"], "TOOLCHAIN_IDENTITY_MISMATCH")
        self.assertEqual(changed.failure["stage"], "toolchain")
        self.assertIn(
            "source_resolver dependency identity mismatch",
            changed.failure["diagnostics"][0],
        )
        self.assertEqual(
            next(
                component
                for component in changed_fx["components"]
                if component["role"] == "pack_builder"
            ),
            recorded_builder,
        )


if __name__ == "__main__":
    unittest.main()
