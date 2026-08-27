#!/usr/bin/env python3
from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
from typing import Any

from ril_mutation import ContractError

PEMS_RELATIVE_PATH = Path("project-knowledge/canonical/pems2.jcs.json")
COVE_RELATIVE_PATH = Path("project-knowledge/canonical/cove1.jcs.json")
BARRIER_RELATIVE_PATH = Path("project-knowledge/recovery/canonical-pems-cove/active.json")
BARRIER_CONTRACT = "reasoning-distiller-canonical-recovery-barrier/1"
BARRIER_ACTIVE_STATE = "ACTIVE"


@dataclass(frozen=True)
class CanonicalPairSnapshot:
    state: str
    pems_bytes: bytes | None = None
    cove_bytes: bytes | None = None
    pems_sha256: str | None = None
    cove_sha256: str | None = None


class CanonicalStoreSession(AbstractContextManager["CanonicalStoreSession"]):
    """One held shared/exclusive lock over package-owned canonical I/O.

    The lock uses the already-existing project-root directory inode, so a
    read-only verifier never creates a lock file or any other filesystem node.
    All package canonical readers/writers use the same inode and therefore the
    same advisory synchronization boundary.
    """

    def __init__(self, project_root: Path, exclusive: bool) -> None:
        self.root = project_root.resolve()
        self.exclusive = exclusive
        self._lock_fd: int | None = None

    @property
    def pems_path(self) -> Path:
        return self.root / PEMS_RELATIVE_PATH

    @property
    def cove_path(self) -> Path:
        return self.root / COVE_RELATIVE_PATH

    @property
    def barrier_path(self) -> Path:
        return self.root / BARRIER_RELATIVE_PATH

    def __enter__(self) -> "CanonicalStoreSession":
        if not self.root.exists() or not self.root.is_dir():
            raise ContractError("CANONICAL_PATH_CONFLICT", str(self.root))
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
        try:
            fd = os.open(self.root, flags)
            mode = fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH
            fcntl.flock(fd, mode | fcntl.LOCK_NB)
        except OSError as exc:
            if "fd" in locals():
                os.close(fd)
            if exc.errno in {errno.EACCES, errno.EAGAIN}:
                raise ContractError("CANONICAL_RECOVERY_BUSY", "canonical-store lock is held") from exc
            raise ContractError("CANONICAL_PATH_CONFLICT", str(exc)) from exc
        self._lock_fd = fd
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(self._lock_fd)
                self._lock_fd = None
        return None

    def snapshot(self) -> CanonicalPairSnapshot:
        """Read one immutable pair snapshot for an ordinary consumer."""
        self._require_locked()
        barrier = self._validated_barrier()
        if barrier is not None:
            raise ContractError("CANONICAL_RECOVERY_ACTIVE", str(self.barrier_path))
        return self._read_pair_unchecked()

    def internal_verification_snapshot(self) -> CanonicalPairSnapshot:
        """Read during a recovery transaction without bypassing its barrier.

        This is an internal verification seam only. It requires the exclusive
        store lock and a syntactically valid ACTIVE V1 barrier. It does not
        authorize recovery, publication, barrier mutation, or root approval.
        """
        self._require_exclusive()
        barrier = self._validated_barrier()
        if barrier is None:
            raise ContractError("CANONICAL_RECOVERY_BARRIER_INVALID", "active recovery barrier is absent")
        return self._read_pair_unchecked()

    def publish_pair(self, pems_bytes: bytes, cove_bytes: bytes) -> CanonicalPairSnapshot:
        """Durably replace the ordinary canonical pair under an exclusive lock."""
        self._require_exclusive()
        if not isinstance(pems_bytes, bytes) or not isinstance(cove_bytes, bytes):
            raise ContractError("CANONICAL_PATH_CONFLICT", "canonical publication requires bytes")
        if self._validated_barrier() is not None:
            raise ContractError("CANONICAL_RECOVERY_ACTIVE", str(self.barrier_path))
        knowledge = self.root / "project-knowledge"
        canonical = knowledge / "canonical"
        self._ensure_directory(knowledge, self.root)
        self._ensure_directory(canonical, knowledge)
        self._durable_replace(self.pems_path, pems_bytes)
        self._durable_replace(self.cove_path, cove_bytes)
        snapshot = self._read_pair_unchecked()
        if snapshot.state != "PRESENT" or snapshot.pems_bytes != pems_bytes or snapshot.cove_bytes != cove_bytes:
            raise ContractError("CANONICAL_STATE_CONFLICT", "published canonical pair does not match requested bytes")
        return snapshot

    def _require_locked(self) -> None:
        if self._lock_fd is None:
            raise RuntimeError("canonical-store session is not entered")

    def _require_exclusive(self) -> None:
        self._require_locked()
        if not self.exclusive:
            raise ContractError("CANONICAL_RECOVERY_BUSY", "exclusive canonical-store session required")

    def _validated_barrier(self) -> dict[str, Any] | None:
        """Validate the G1 reader-facing portion of the V1 active barrier.

        Normal consumers need only one safe classification: absent, valid and
        active, or invalid. Full plan/journal/provenance binding remains the
        recovery executor's later apply-time responsibility, but no present
        barrier can ever be treated as absent here.
        """
        knowledge = self.root / "project-knowledge"
        recovery = knowledge / "recovery"
        namespace = recovery / "canonical-pems-cove"
        for directory in (knowledge, recovery, namespace):
            if not _lexists(directory):
                return None
            if directory.is_symlink() or not directory.is_dir():
                raise ContractError("CANONICAL_RECOVERY_BARRIER_INVALID", str(directory))
        if not _lexists(self.barrier_path):
            return None
        raw = _read_regular(self.barrier_path, "CANONICAL_RECOVERY_BARRIER_INVALID")
        try:
            value = _strict_json_object(raw)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ContractError("CANONICAL_RECOVERY_BARRIER_INVALID", str(exc)) from exc
        if _canonical_json(value) != raw:
            raise ContractError("CANONICAL_RECOVERY_BARRIER_INVALID", "active barrier is not canonical JSON")
        if value.get("contract") != BARRIER_CONTRACT:
            raise ContractError("CANONICAL_RECOVERY_BARRIER_INVALID", "unknown active barrier contract")
        if value.get("transaction_state") != BARRIER_ACTIVE_STATE:
            raise ContractError("CANONICAL_RECOVERY_BARRIER_INVALID", "unsupported active barrier transaction_state")
        return value

    def _read_pair_unchecked(self) -> CanonicalPairSnapshot:
        knowledge = self.root / "project-knowledge"
        canonical = knowledge / "canonical"
        for directory in (knowledge, canonical):
            if not _lexists(directory):
                return CanonicalPairSnapshot("ABSENT")
            if directory.is_symlink() or not directory.is_dir():
                raise ContractError("CANONICAL_PATH_CONFLICT", str(directory))

        pems_exists = _lexists(self.pems_path)
        cove_exists = _lexists(self.cove_path)
        if not pems_exists and not cove_exists:
            return CanonicalPairSnapshot("ABSENT")
        if pems_exists != cove_exists:
            if pems_exists:
                _read_regular(self.pems_path, "CANONICAL_PATH_CONFLICT")
            if cove_exists:
                _read_regular(self.cove_path, "CANONICAL_PATH_CONFLICT")
            return CanonicalPairSnapshot("INCOMPLETE")

        pems = _read_regular(self.pems_path, "CANONICAL_PATH_CONFLICT")
        cove = _read_regular(self.cove_path, "CANONICAL_PATH_CONFLICT")
        return CanonicalPairSnapshot(
            "PRESENT",
            pems_bytes=pems,
            cove_bytes=cove,
            pems_sha256=hashlib.sha256(pems).hexdigest(),
            cove_sha256=hashlib.sha256(cove).hexdigest(),
        )

    def _ensure_directory(self, path: Path, parent: Path) -> None:
        if _lexists(path):
            if path.is_symlink() or not path.is_dir():
                raise ContractError("CANONICAL_PATH_CONFLICT", str(path))
            return
        try:
            os.mkdir(path)
        except FileExistsError:
            if path.is_symlink() or not path.is_dir():
                raise ContractError("CANONICAL_PATH_CONFLICT", str(path))
        _fsync_directory(parent)

    def _durable_replace(self, path: Path, data: bytes) -> None:
        if _lexists(path) and (path.is_symlink() or not path.is_file()):
            raise ContractError("CANONICAL_PATH_CONFLICT", str(path))
        tmp = path.with_name(f".{path.name}.canonical-store.{os.getpid()}.{secrets.token_hex(8)}.tmp")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd: int | None = None
        try:
            fd = os.open(tmp, flags, 0o600)
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("short canonical temporary-file write")
                view = view[written:]
            os.fsync(fd)
            os.close(fd)
            fd = None
            os.replace(tmp, path)
            _fsync_directory(path.parent)
        finally:
            if fd is not None:
                os.close(fd)
            if _lexists(tmp) and not tmp.is_symlink():
                try:
                    tmp.unlink()
                except FileNotFoundError:
                    pass


def shared_canonical_store(project_root: Path) -> CanonicalStoreSession:
    return CanonicalStoreSession(project_root, exclusive=False)


def exclusive_canonical_store(project_root: Path) -> CanonicalStoreSession:
    return CanonicalStoreSession(project_root, exclusive=True)


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _read_regular(path: Path, code: str) -> bytes:
    if path.is_symlink():
        raise ContractError(code, str(path))
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ContractError(code, str(path)) from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ContractError(code, str(path))
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _strict_json_object(raw: bytes) -> dict[str, Any]:
    def pairs(items):
        out: dict[str, Any] = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate JSON member: {key}")
            out[key] = value
        return out

    def reject_constant(value: str):
        raise ValueError(f"non-finite JSON value: {value}")

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("active barrier must be a JSON object")
    return value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
