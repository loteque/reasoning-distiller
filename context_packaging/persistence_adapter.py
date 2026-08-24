"""P6 immutable persistence adapter for derived context-pack artifacts.

The P5 builder remains pure and side-effect free. This module is a separate,
optional filesystem write boundary for bytes that have already been derived.
The caller selects an output root and a relative target path, and supplies any
project-specific lifecycle roots that must never receive generated artifacts.

A storage path, filename, successful write, or replay result conveys no
canonical standing, authority, authorization, activation, reconciliation, or
admission semantics. Those meanings remain owned by their governing stores and
contracts outside this adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
from typing import Sequence

PERSISTED = "PERSISTED"
NO_CHANGE = "NO_CHANGE"
IMMUTABLE_OUTPUT_COLLISION = "IMMUTABLE_OUTPUT_COLLISION"


@dataclass(frozen=True)
class PersistenceResult:
    """Out-of-band result of an immutable derived-artifact write."""

    status: str
    raw_sha256: str
    byte_count: int

    @property
    def changed(self) -> bool:
        return self.status == PERSISTED


class PersistenceBoundaryError(ValueError):
    """The caller-selected target violates the declared persistence boundary."""


class ImmutableOutputCollisionError(FileExistsError):
    """Existing target bytes differ from the requested immutable artifact."""

    code = IMMUTABLE_OUTPUT_COLLISION

    def __init__(self) -> None:
        super().__init__(IMMUTABLE_OUTPUT_COLLISION)


def persist_immutable_artifact(
    artifact_bytes: bytes,
    *,
    output_root: str | os.PathLike[str],
    relative_path: str | os.PathLike[str],
    prohibited_roots: Sequence[str | os.PathLike[str]] = (),
) -> PersistenceResult:
    """Persist exact bytes without overwriting or inferring semantic standing.

    ``output_root`` is the caller-declared derived-artifact boundary.
    ``relative_path`` must stay beneath that root. ``prohibited_roots`` is the
    consuming project's explicit set of canonical/lifecycle stores that this
    generic adapter must not write into. The adapter never discovers or infers
    those stores from path names.

    The target parent must already exist. Parent-directory creation is kept out
    of this primitive so the only successful mutation is publication of the
    requested artifact itself.
    """
    if not isinstance(artifact_bytes, bytes):
        raise TypeError("artifact_bytes must be bytes")

    root = _resolve_existing_directory(output_root, "output_root")
    relative = Path(relative_path)
    if relative.is_absolute() or relative == Path(".") or not relative.parts:
        raise PersistenceBoundaryError("relative_path must name a file under output_root")

    lexical_target = root / relative
    try:
        parent = lexical_target.parent.resolve(strict=True)
    except FileNotFoundError as exc:
        raise PersistenceBoundaryError("target parent must already exist") from exc
    if not parent.is_dir():
        raise PersistenceBoundaryError("target parent must be a directory")
    if not _is_within(parent, root):
        raise PersistenceBoundaryError("target escapes output_root")

    target = parent / lexical_target.name
    if target == root or not _is_within(target, root):
        raise PersistenceBoundaryError("target escapes output_root")

    for prohibited in prohibited_roots:
        prohibited_root = Path(prohibited).resolve(strict=False)
        if _is_within(target, prohibited_root):
            raise PersistenceBoundaryError("target is inside a prohibited lifecycle store")

    if target.is_symlink():
        raise PersistenceBoundaryError("symlink targets are not writable persistence artifacts")
    if target.exists():
        return _replay_or_collision(target, artifact_bytes)

    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        # Another writer published the path after the existence check. Preserve
        # immutable semantics by treating that race as replay or collision.
        return _replay_or_collision(target, artifact_bytes)

    created = True
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(artifact_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        created = False
    finally:
        if created:
            try:
                target.unlink()
            except FileNotFoundError:
                pass

    return _result(PERSISTED, artifact_bytes)


def _replay_or_collision(target: Path, artifact_bytes: bytes) -> PersistenceResult:
    if not target.is_file():
        raise PersistenceBoundaryError("existing target is not a regular file")
    existing = target.read_bytes()
    if existing != artifact_bytes:
        raise ImmutableOutputCollisionError()
    return _result(NO_CHANGE, artifact_bytes)


def _result(status: str, artifact_bytes: bytes) -> PersistenceResult:
    return PersistenceResult(
        status=status,
        raw_sha256="sha256:" + hashlib.sha256(artifact_bytes).hexdigest(),
        byte_count=len(artifact_bytes),
    )


def _resolve_existing_directory(
    value: str | os.PathLike[str], label: str
) -> Path:
    try:
        resolved = Path(value).resolve(strict=True)
    except FileNotFoundError as exc:
        raise PersistenceBoundaryError(f"{label} must already exist") from exc
    if not resolved.is_dir():
        raise PersistenceBoundaryError(f"{label} must be a directory")
    return resolved


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
