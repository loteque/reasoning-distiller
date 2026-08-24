import importlib.util
from pathlib import Path

import pytest

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


def test_first_write_persists_exact_bytes_then_exact_replay_is_no_change(tmp_path):
    output_root = tmp_path / "derived"
    output_root.mkdir()
    artifact = b"{\"contract\":\"reasoning-distiller-context-pack/2\"}\n"

    first = persist_immutable_artifact(
        artifact,
        output_root=output_root,
        relative_path="pack.jcs.json",
    )
    target = output_root / "pack.jcs.json"
    assert first.status == PERSISTED
    assert first.changed is True
    assert first.byte_count == len(artifact)
    assert target.read_bytes() == artifact

    before_stat = target.stat()
    replay = persist_immutable_artifact(
        artifact,
        output_root=output_root,
        relative_path="pack.jcs.json",
    )
    after_stat = target.stat()
    assert replay.status == NO_CHANGE
    assert replay.changed is False
    assert replay == type(replay)(
        status=NO_CHANGE,
        raw_sha256=first.raw_sha256,
        byte_count=len(artifact),
    )
    assert after_stat.st_size == before_stat.st_size
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns
    assert target.read_bytes() == artifact


def test_different_existing_bytes_fail_collision_without_overwrite(tmp_path):
    output_root = tmp_path / "derived"
    output_root.mkdir()
    target = output_root / "pack.jcs.json"
    target.write_bytes(b"first")

    with pytest.raises(ImmutableOutputCollisionError) as excinfo:
        persist_immutable_artifact(
            b"different",
            output_root=output_root,
            relative_path="pack.jcs.json",
        )

    assert excinfo.value.code == IMMUTABLE_OUTPUT_COLLISION
    assert target.read_bytes() == b"first"


def test_target_cannot_escape_declared_output_root(tmp_path):
    output_root = tmp_path / "derived"
    output_root.mkdir()

    with pytest.raises(PersistenceBoundaryError):
        persist_immutable_artifact(
            b"artifact",
            output_root=output_root,
            relative_path="../escape.bin",
        )

    assert not (tmp_path / "escape.bin").exists()


def test_prohibited_lifecycle_store_is_rejected(tmp_path):
    lifecycle_root = tmp_path / "project-knowledge" / "canonical"
    lifecycle_root.mkdir(parents=True)

    with pytest.raises(PersistenceBoundaryError):
        persist_immutable_artifact(
            b"artifact",
            output_root=lifecycle_root,
            relative_path="pack.jcs.json",
            prohibited_roots=[lifecycle_root],
        )

    assert not (lifecycle_root / "pack.jcs.json").exists()


def test_path_name_does_not_create_semantic_standing(tmp_path):
    output_root = tmp_path / "derived"
    output_root.mkdir()

    result = persist_immutable_artifact(
        b"ordinary derived bytes",
        output_root=output_root,
        relative_path="canonical-authorized-activation-approved.jcs.json",
    )

    assert result.status == PERSISTED
    assert vars(result) == {
        "status": PERSISTED,
        "raw_sha256": result.raw_sha256,
        "byte_count": len(b"ordinary derived bytes"),
    }
    assert not any(
        token in vars(result)
        for token in (
            "authority",
            "authorized",
            "activation",
            "admission",
            "canonical_standing",
            "reconciliation",
            "role",
        )
    )


def test_non_bytes_are_rejected_before_any_write(tmp_path):
    output_root = tmp_path / "derived"
    output_root.mkdir()

    with pytest.raises(TypeError):
        persist_immutable_artifact(  # type: ignore[arg-type]
            "text would require an encoding decision",
            output_root=output_root,
            relative_path="pack.jcs.json",
        )

    assert list(output_root.iterdir()) == []


def test_missing_parent_is_not_created_as_an_extra_side_effect(tmp_path):
    output_root = tmp_path / "derived"
    output_root.mkdir()

    with pytest.raises(PersistenceBoundaryError):
        persist_immutable_artifact(
            b"artifact",
            output_root=output_root,
            relative_path="nested/pack.jcs.json",
        )

    assert not (output_root / "nested").exists()


def test_existing_output_presence_does_not_change_successful_p5_pack_bytes(
    tmp_path, monkeypatch
):
    p5 = _load_p5_fixture_module()
    baseline = p5._build(p5._fixture(semantic_item=True))
    assert baseline.ok, baseline.failure

    output_root = tmp_path / "derived"
    output_root.mkdir()
    persisted = persist_immutable_artifact(
        baseline.serialized_pack,
        output_root=output_root,
        relative_path="pack.jcs.json",
    )
    assert persisted.status == PERSISTED

    # Make the output location host-visible and current-working-directory visible.
    # P5 has no persistence/cache input and therefore must not discover it.
    monkeypatch.chdir(output_root)
    replay_build = p5._build(p5._fixture(semantic_item=True))
    assert replay_build.ok, replay_build.failure
    assert replay_build.serialized_pack == baseline.serialized_pack
    assert replay_build.pack == baseline.pack

    exact_replay = persist_immutable_artifact(
        replay_build.serialized_pack,
        output_root=output_root,
        relative_path="pack.jcs.json",
    )
    assert exact_replay.status == NO_CHANGE
