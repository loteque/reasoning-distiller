import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

from context_packaging.persistence_adapter import (
    IMMUTABLE_OUTPUT_COLLISION,
    NO_CHANGE,
    PERSISTED,
    ImmutableOutputCollisionError,
    PersistenceBoundaryError,
    persist_immutable_artifact,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_p5_fixture_module():
    path = ROOT / "tests/test_context_packaging_pack_builder_p5.py"
    spec = importlib.util.spec_from_file_location("_p5_fixture_for_p6", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class P6PersistenceAdapterTests(unittest.TestCase):
    def test_first_write_persists_exact_bytes_then_exact_replay_is_no_change(self):
        with tempfile.TemporaryDirectory() as td:
            output_root = Path(td) / "derived"
            output_root.mkdir()
            artifact = b'{"contract":"reasoning-distiller-context-pack/2"}\n'

            first = persist_immutable_artifact(
                artifact,
                output_root=output_root,
                relative_path="pack.jcs.json",
            )
            target = output_root / "pack.jcs.json"
            self.assertEqual(first.status, PERSISTED)
            self.assertTrue(first.changed)
            self.assertEqual(first.byte_count, len(artifact))
            self.assertEqual(target.read_bytes(), artifact)

            before_stat = target.stat()
            replay = persist_immutable_artifact(
                artifact,
                output_root=output_root,
                relative_path="pack.jcs.json",
            )
            after_stat = target.stat()
            self.assertEqual(replay.status, NO_CHANGE)
            self.assertFalse(replay.changed)
            self.assertEqual(
                replay,
                type(replay)(
                    status=NO_CHANGE,
                    raw_sha256=first.raw_sha256,
                    byte_count=len(artifact),
                ),
            )
            self.assertEqual(after_stat.st_size, before_stat.st_size)
            self.assertEqual(after_stat.st_mtime_ns, before_stat.st_mtime_ns)
            self.assertEqual(target.read_bytes(), artifact)

    def test_different_existing_bytes_fail_collision_without_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            output_root = Path(td) / "derived"
            output_root.mkdir()
            target = output_root / "pack.jcs.json"
            target.write_bytes(b"first")

            with self.assertRaises(ImmutableOutputCollisionError) as caught:
                persist_immutable_artifact(
                    b"different",
                    output_root=output_root,
                    relative_path="pack.jcs.json",
                )

            self.assertEqual(caught.exception.code, IMMUTABLE_OUTPUT_COLLISION)
            self.assertEqual(target.read_bytes(), b"first")

    def test_target_cannot_escape_declared_output_root(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            output_root = tmp_path / "derived"
            output_root.mkdir()

            with self.assertRaises(PersistenceBoundaryError):
                persist_immutable_artifact(
                    b"artifact",
                    output_root=output_root,
                    relative_path="../escape.bin",
                )

            self.assertFalse((tmp_path / "escape.bin").exists())

    def test_prohibited_lifecycle_store_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            lifecycle_root = Path(td) / "project-knowledge" / "canonical"
            lifecycle_root.mkdir(parents=True)

            with self.assertRaises(PersistenceBoundaryError):
                persist_immutable_artifact(
                    b"artifact",
                    output_root=lifecycle_root,
                    relative_path="pack.jcs.json",
                    prohibited_roots=[lifecycle_root],
                )

            self.assertFalse((lifecycle_root / "pack.jcs.json").exists())

    def test_path_name_does_not_create_semantic_standing(self):
        with tempfile.TemporaryDirectory() as td:
            output_root = Path(td) / "derived"
            output_root.mkdir()

            result = persist_immutable_artifact(
                b"ordinary derived bytes",
                output_root=output_root,
                relative_path="canonical-authorized-activation-approved.jcs.json",
            )

            self.assertEqual(result.status, PERSISTED)
            self.assertEqual(
                vars(result),
                {
                    "status": PERSISTED,
                    "raw_sha256": result.raw_sha256,
                    "byte_count": len(b"ordinary derived bytes"),
                },
            )
            for token in (
                "authority",
                "authorized",
                "activation",
                "admission",
                "canonical_standing",
                "reconciliation",
                "role",
            ):
                self.assertNotIn(token, vars(result))

    def test_non_bytes_are_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as td:
            output_root = Path(td) / "derived"
            output_root.mkdir()

            with self.assertRaises(TypeError):
                persist_immutable_artifact(
                    "text would require an encoding decision",  # type: ignore[arg-type]
                    output_root=output_root,
                    relative_path="pack.jcs.json",
                )

            self.assertEqual(list(output_root.iterdir()), [])

    def test_missing_parent_is_not_created_as_an_extra_side_effect(self):
        with tempfile.TemporaryDirectory() as td:
            output_root = Path(td) / "derived"
            output_root.mkdir()

            with self.assertRaises(PersistenceBoundaryError):
                persist_immutable_artifact(
                    b"artifact",
                    output_root=output_root,
                    relative_path="nested/pack.jcs.json",
                )

            self.assertFalse((output_root / "nested").exists())

    def test_existing_output_presence_does_not_change_successful_p5_pack_bytes(self):
        p5 = _load_p5_fixture_module()
        baseline = p5._build(p5._fixture(semantic_item=True))
        self.assertTrue(baseline.ok, baseline.failure)

        with tempfile.TemporaryDirectory() as td:
            output_root = Path(td) / "derived"
            output_root.mkdir()
            persisted = persist_immutable_artifact(
                baseline.serialized_pack,
                output_root=output_root,
                relative_path="pack.jcs.json",
            )
            self.assertEqual(persisted.status, PERSISTED)

            # Make the output location host-visible and current-working-directory
            # visible. P5 has no persistence/cache input and must not discover it.
            previous_cwd = Path.cwd()
            try:
                os.chdir(output_root)
                replay_build = p5._build(p5._fixture(semantic_item=True))
            finally:
                os.chdir(previous_cwd)

            self.assertTrue(replay_build.ok, replay_build.failure)
            self.assertEqual(replay_build.serialized_pack, baseline.serialized_pack)
            self.assertEqual(replay_build.pack, baseline.pack)

            exact_replay = persist_immutable_artifact(
                replay_build.serialized_pack,
                output_root=output_root,
                relative_path="pack.jcs.json",
            )
            self.assertEqual(exact_replay.status, NO_CHANGE)


if __name__ == "__main__":
    unittest.main()
