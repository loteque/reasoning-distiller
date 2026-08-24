"""P6 immutable persistence adapter for derived context-pack artifacts.

The P5 builder remains pure and side-effect free. This module is a separate,
optional filesystem write boundary for bytes that have already been derived.
The caller selects an output root and a relative target path, and explicitly
supplies the complete set of project-specific lifecycle roots that must never
receive generated artifacts.

A storage path, filename, successful write, or replay result conveys no
canonical standing, authority, authorization, activation, reconciliation, or
admission semantics. Those meanings remain owned by their governing stores and
contracts outside this adapter.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
import errno
import hashlib
import os
from pathlib import Path
import stat
import sys
from typing import Sequence

PERSISTED = "PERSISTED"
NO_CHANGE = "NO_CHANGE"
IMMUTABLE_OUTPUT_COLLISION = "IMMUTABLE_OUTPUT_COLLISION"

# Linux openat2(2) supplies the kernel-enforced resolve-beneath primitive needed
# to make publication race-resistant. 437 is __NR_openat2 on the Linux syscall
# tables used by supported GitHub/Linux runners and asm-generic architectures.
_SYS_OPENAT2 = 437
_RESOLVE_NO_MAGICLINKS = 0x02
_RESOLVE_NO_SYMLINKS = 0x04
_RESOLVE_BENEATH = 0x08
_SECURE_RESOLVE = _RESOLVE_NO_MAGICLINKS | _RESOLVE_NO_SYMLINKS | _RESOLVE_BENEATH


class _OpenHow(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint64),
        ("mode", ctypes.c_uint64),
        ("resolve", ctypes.c_uint64),
    ]


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
    prohibited_roots: Sequence[str | os.PathLike[str]] | None = None,
) -> PersistenceResult:
    """Persist exact bytes without overwriting or inferring semantic standing.

    ``output_root`` is the caller-declared derived-artifact boundary.
    ``relative_path`` must stay beneath that root. ``prohibited_roots`` is the
    consuming project's explicit, complete set of canonical/lifecycle stores
    that this generic adapter must not write into. It must be supplied even
    when that complete set is empty; omission is unknown boundary evidence and
    fails closed. The adapter never discovers or infers lifecycle stores from
    path names.

    The target parent must already exist. Parent-directory creation is kept out
    of this primitive so the only successful mutation is publication of the
    requested artifact itself. Publication requires Linux ``openat2`` resolve
    constraints so path replacement cannot redirect the write outside the
    opened output boundary; platforms lacking that primitive fail closed.
    """
    if not isinstance(artifact_bytes, bytes):
        raise TypeError("artifact_bytes must be bytes")
    if prohibited_roots is None:
        raise PersistenceBoundaryError(
            "prohibited_roots must be supplied as complete lifecycle-boundary evidence"
        )

    root = _resolve_existing_directory(output_root, "output_root")
    relative = Path(relative_path)
    if relative.is_absolute() or relative == Path(".") or not relative.parts:
        raise PersistenceBoundaryError("relative_path must name a file under output_root")
    if any(part in ("", ".", "..") for part in relative.parts):
        raise PersistenceBoundaryError("relative_path must not contain traversal components")

    target = root.joinpath(*relative.parts)
    if target == root or not _is_within(target, root):
        raise PersistenceBoundaryError("target escapes output_root")

    for prohibited in prohibited_roots:
        prohibited_root = Path(prohibited).resolve(strict=False)
        if _is_within(target, prohibited_root):
            raise PersistenceBoundaryError("target is inside a prohibited lifecycle store")

    root_fd = _open_verified_root(root)
    try:
        relative_text = os.fspath(relative)
        return _publish_or_replay(root_fd, relative_text, artifact_bytes)
    finally:
        os.close(root_fd)


def _publish_or_replay(
    root_fd: int, relative_path: str, artifact_bytes: bytes
) -> PersistenceResult:
    create_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_CLOEXEC"):
        create_flags |= os.O_CLOEXEC

    for _attempt in range(2):
        try:
            fd = _open_beneath(root_fd, relative_path, create_flags, 0o644)
        except FileExistsError:
            try:
                return _replay_or_collision(root_fd, relative_path, artifact_bytes)
            except FileNotFoundError:
                # A concurrent actor removed the entry after the EEXIST result.
                # Retry the create exactly once without weakening the boundary.
                continue
        except OSError as exc:
            raise _boundary_error_for_open(exc, creating=True) from exc

        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(artifact_bytes)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            _cleanup_created_target(root_fd, relative_path)
            raise
        return _result(PERSISTED, artifact_bytes)

    raise PersistenceBoundaryError("target changed concurrently during immutable publication")


def _cleanup_created_target(root_fd: int, relative_path: str) -> None:
    """Best-effort cleanup without reintroducing pathname traversal."""
    relative = Path(relative_path)
    parent_text = os.fspath(relative.parent)
    name = relative.name
    parent_fd: int | None = None
    try:
        if parent_text in ("", "."):
            parent_fd = os.dup(root_fd)
        else:
            parent_flags = os.O_RDONLY
            if hasattr(os, "O_DIRECTORY"):
                parent_flags |= os.O_DIRECTORY
            if hasattr(os, "O_CLOEXEC"):
                parent_flags |= os.O_CLOEXEC
            parent_fd = _open_beneath(root_fd, parent_text, parent_flags, 0)
        os.unlink(name, dir_fd=parent_fd)
    except OSError:
        # If the parent was renamed, replaced, or otherwise cannot be reopened
        # beneath root, leaving the partial immutable target is safer than a
        # fallback pathname unlink that could traverse outside the boundary.
        pass
    finally:
        if parent_fd is not None:
            os.close(parent_fd)


def _replay_or_collision(
    root_fd: int, relative_path: str, artifact_bytes: bytes
) -> PersistenceResult:
    read_flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        read_flags |= os.O_CLOEXEC
    try:
        fd = _open_beneath(root_fd, relative_path, read_flags, 0)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise _boundary_error_for_open(exc, creating=False) from exc

    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise PersistenceBoundaryError("existing target is not a regular file")
        existing = handle.read()
    if existing != artifact_bytes:
        raise ImmutableOutputCollisionError()
    return _result(NO_CHANGE, artifact_bytes)


def _open_verified_root(root: Path) -> int:
    if sys.platform != "linux":
        raise PersistenceBoundaryError(
            "race-resistant persistence requires Linux openat2 support"
        )

    before = root.stat()
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        fd = os.open(root, flags)
    except OSError as exc:
        raise PersistenceBoundaryError("output_root cannot be opened safely") from exc

    after = os.fstat(fd)
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        os.close(fd)
        raise PersistenceBoundaryError("output_root changed during boundary verification")
    if not stat.S_ISDIR(after.st_mode):
        os.close(fd)
        raise PersistenceBoundaryError("output_root must be a directory")
    return fd


def _open_beneath(dir_fd: int, relative_path: str, flags: int, mode: int) -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    syscall = libc.syscall
    syscall.restype = ctypes.c_long
    how = _OpenHow(flags=flags, mode=mode, resolve=_SECURE_RESOLVE)
    path_bytes = os.fsencode(relative_path)
    result = syscall(
        ctypes.c_long(_SYS_OPENAT2),
        ctypes.c_int(dir_fd),
        ctypes.c_char_p(path_bytes),
        ctypes.byref(how),
        ctypes.c_size_t(ctypes.sizeof(how)),
    )
    if result < 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), relative_path)
    return int(result)


def _boundary_error_for_open(exc: OSError, *, creating: bool) -> PersistenceBoundaryError:
    if exc.errno in (errno.ENOSYS, errno.EINVAL):
        return PersistenceBoundaryError(
            "race-resistant persistence is unavailable on this kernel/filesystem"
        )
    if exc.errno == errno.ENOENT:
        return PersistenceBoundaryError("target parent must already exist")
    if exc.errno in (errno.ELOOP, errno.EXDEV, errno.EAGAIN):
        return PersistenceBoundaryError(
            "target escapes or traverses an unsafe persistence boundary"
        )
    if exc.errno in (errno.ENOTDIR, errno.EISDIR):
        return PersistenceBoundaryError(
            "target parent must be a directory"
            if creating
            else "existing target is not a regular file"
        )
    return PersistenceBoundaryError("persistence target cannot be opened safely")


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
