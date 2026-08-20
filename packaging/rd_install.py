#!/usr/bin/env python3
"""Deterministic, network-independent Reasoning Distiller installer.

The runner retrieves package artifacts. This program consumes only local files,
installs only the declared managed root, fails closed on drift/incompatibility,
and uses a durable project-local journal to recover interrupted activation or
restoration before any later installation is allowed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path

INSTALLER_CONTRACT = "reasoning-distiller-installer/1"
TRANSACTION_CONTRACT = "reasoning-distiller-install-transaction/1"
RELEASE_VERIFICATION_CONTRACT = "reasoning-distiller-release-verification/1"
TRANSITION_PLAN_CONTRACT = "reasoning-distiller-install-transition-plan/1"
DEFAULT_MANAGED_ROOT = ".reasoning-distiller"
DEFAULT_INSTALLED_AT = "1970-01-01T00:00:00Z"
JOURNAL_NAME = ".rd-install-transaction.json"
BACKUP_NAME = ".rd-install-backup"

HERE = Path(__file__).resolve().parent
VALIDATOR_PATH = HERE / "validate_install_package_contract.py"
spec = importlib.util.spec_from_file_location("rd_package_contract", VALIDATOR_PATH)
rd = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(rd)


class SimulatedInterruption(BaseException):
    """Test-only hard interruption used to pressure P4 recovery paths."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, value: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(canonical_json_bytes(value) + b"\n")
    os.replace(tmp, path)


def resolve_managed_root(target: Path, managed_root: str) -> Path:
    rd.validate_rel_path(managed_root, "managed_root")
    root = (target / managed_root).resolve()
    try:
        root.relative_to(target.resolve())
    except ValueError as exc:
        raise ValueError("managed root escapes target") from exc
    return root


def validate_transport(package: Path, expected_sha256: str, manifest: dict) -> None:
    if len(expected_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in expected_sha256):
        raise ValueError("transport sha256 must be 64 lowercase hex")
    actual = sha256_file(package)
    if actual != expected_sha256:
        raise ValueError(f"transport digest mismatch: expected {expected_sha256}, got {actual}")
    if manifest["transport_sha256"] != expected_sha256:
        raise ValueError("manifest transport_sha256 differs from expected transport digest")


def inspect_archive(package: Path, manifest: dict) -> dict[str, bytes]:
    expected = {item["path"]: item for item in manifest["files"]}
    payload: dict[str, bytes] = {}
    seen_casefold: set[str] = set()
    with tarfile.open(package, mode="r:gz") as tar:
        members = tar.getmembers()
        names = [member.name for member in members]
        if names != sorted(expected):
            raise ValueError("archive member order/content differs from manifest")
        if set(names) != set(expected) or len(names) != len(expected):
            raise ValueError("archive and manifest file sets differ")
        for member in members:
            rd.validate_rel_path(member.name, "archive member")
            folded = member.name.casefold()
            if folded in seen_casefold:
                raise ValueError(f"archive case-fold collision: {member.name}")
            seen_casefold.add(folded)
            if not member.isfile() or member.issym() or member.islnk():
                raise ValueError(f"archive contains non-regular file: {member.name}")
            if member.mode != int(expected[member.name]["mode"], 8):
                raise ValueError(f"archive mode mismatch: {member.name}")
            extracted = tar.extractfile(member)
            if extracted is None:
                raise ValueError(f"cannot read archive member: {member.name}")
            data = extracted.read()
            if sha256_bytes(data) != expected[member.name]["sha256"]:
                raise ValueError(f"archive digest mismatch: {member.name}")
            payload[member.name] = data
    return payload


def _verify_release_bundle_internal(
    package: Path,
    manifest_path: Path,
    transport_sha256: str,
) -> tuple[dict, dict[str, bytes], dict]:
    package = package.resolve()
    manifest_path = manifest_path.resolve()
    if not package.is_file() or not manifest_path.is_file():
        raise ValueError("package and manifest must be existing local files")
    manifest = rd.validate_manifest(manifest_path)
    validate_transport(package, transport_sha256, manifest)
    payload = inspect_archive(package, manifest)
    result = {
        "contract": RELEASE_VERIFICATION_CONTRACT,
        "status": "PASS",
        "outcome": "VERIFIED",
        "version": manifest["version"],
        "source_commit": manifest["source_commit"],
        "content_identity": manifest["content_identity"],
        "transport_sha256": transport_sha256,
        "file_count": len(manifest["files"]),
    }
    return manifest, payload, result


def verify_release_bundle(package: Path, manifest_path: Path, transport_sha256: str) -> dict:
    """Read-only verification of one exact local release bundle."""
    try:
        _, _, result = _verify_release_bundle_internal(package, manifest_path, transport_sha256)
        return result
    except Exception as exc:
        return {
            "contract": RELEASE_VERIFICATION_CONTRACT,
            "status": "FAIL",
            "outcome": "INVALID_RELEASE",
            "detail": str(exc),
        }


def read_previous_manifest(managed: Path) -> dict | None:
    manifest_path = managed / ".installation" / "MANIFEST.json"
    if not managed.exists():
        return None
    if not managed.is_dir() or managed.is_symlink():
        raise ValueError("managed root exists but is not a regular directory")
    if not manifest_path.is_file():
        raise ValueError("managed root exists without verified .installation/MANIFEST.json")
    previous = load_json(manifest_path)
    rd.validate_schema(previous, rd.MANIFEST_SCHEMA)
    rd.validate_manifest_semantics(previous)
    return previous


def scan_managed_payload(managed: Path, manifest: dict) -> set[str]:
    found: set[str] = set()
    for root in manifest["managed_roots"]:
        base = managed / root
        if not base.exists():
            continue
        if base.is_symlink() or not base.is_dir():
            found.add(root)
            continue
        for path in base.rglob("*"):
            if path.is_dir() and not path.is_symlink():
                continue
            found.add(path.relative_to(managed).as_posix())
    return found


def detect_drift(managed: Path, previous: dict | None) -> list[str]:
    if previous is None:
        return []
    expected = {item["path"]: item for item in previous["files"]}
    found = scan_managed_payload(managed, previous)
    drift: list[str] = []
    for path, item in expected.items():
        full = managed / path
        if not full.is_file() or full.is_symlink():
            drift.append(f"missing-or-nonregular:{path}")
        elif sha256_file(full) != item["sha256"]:
            drift.append(f"content:{path}")
        elif (full.stat().st_mode & 0o777) != int(item["mode"], 8):
            drift.append(f"mode:{path}")
    for extra in sorted(found - set(expected)):
        drift.append(f"unexpected:{extra}")
    return sorted(drift)


def validate_project_compatibility(project_package: Path | None, manifest: dict) -> dict | None:
    if project_package is None:
        return None
    project = load_json(project_package)
    if project.get("contract") not in manifest["compatibility"]["project_knowledge_package"]:
        raise ValueError(f"project package contract {project.get('contract')!r} is not supported by release")
    compatible = project.get("framework", {}).get("compatible_contracts", [])
    required = {manifest["contract"], INSTALLER_CONTRACT}
    missing = sorted(required - set(compatible))
    if missing:
        raise ValueError(f"project framework compatibility missing contracts: {missing}")
    backend = project.get("canonical_backend")
    if backend is not None and backend.get("type") not in manifest["compatibility"]["backends"]:
        raise ValueError(f"canonical backend {backend.get('type')!r} is not supported by release")
    return project


def numeric_version(value: str) -> tuple[int, ...] | None:
    parts = value.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def compare_release_identity(previous: dict | None, incoming: dict, allow_downgrade: bool) -> None:
    if previous is None:
        return
    if previous["version"] == incoming["version"]:
        if previous["content_identity"] != incoming["content_identity"]:
            raise ValueError("same release version has different content identity")
        return
    if not allow_downgrade:
        old = numeric_version(previous["version"])
        new = numeric_version(incoming["version"])
        if old is not None and new is not None and new < old:
            raise ValueError("downgrade rejected; pass --allow-downgrade for an explicit downgrade")


def write_stage(stage: Path, payload: dict[str, bytes], manifest: dict, installation: dict) -> None:
    for item in manifest["files"]:
        destination = stage / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload[item["path"]])
        os.chmod(destination, int(item["mode"], 8))
    metadata = stage / ".installation"
    metadata.mkdir(parents=True, exist_ok=True)
    (metadata / "MANIFEST.json").write_bytes(canonical_json_bytes(manifest) + b"\n")
    (metadata / "INSTALLATION.json").write_bytes(canonical_json_bytes(installation) + b"\n")


def validate_installed_tree(managed: Path, manifest: dict) -> None:
    for item in manifest["files"]:
        path = managed / item["path"]
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"installed file missing/nonregular: {item['path']}")
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"installed file digest mismatch: {item['path']}")
        if (path.stat().st_mode & 0o777) != int(item["mode"], 8):
            raise ValueError(f"installed file mode mismatch: {item['path']}")
    stored = load_json(managed / ".installation" / "MANIFEST.json")
    if stored != manifest:
        raise ValueError("stored manifest differs from verified release manifest")


def manifest_identity_at(managed: Path) -> str | None:
    try:
        manifest = read_previous_manifest(managed)
    except Exception:
        return None
    return manifest["content_identity"] if manifest else None


def journal_paths(target: Path) -> tuple[Path, Path]:
    return target / JOURNAL_NAME, target / BACKUP_NAME


def write_journal(path: Path, journal: dict, state: str) -> None:
    updated = dict(journal)
    updated["state"] = state
    atomic_write_json(path, updated)
    journal.clear()
    journal.update(updated)


def validate_journal(journal: dict, managed_root: str) -> None:
    required = {"contract", "managed_root", "state", "previous_exists", "previous_content_identity", "incoming_content_identity"}
    if set(journal) != required:
        raise ValueError("invalid installer recovery journal fields")
    if journal["contract"] != TRANSACTION_CONTRACT or journal["managed_root"] != managed_root:
        raise ValueError("installer recovery journal contract/root mismatch")
    if journal["state"] not in {"PREPARED", "BACKUP_PENDING", "ACTIVATE_PENDING", "VALIDATE_PENDING", "RESTORE_PENDING", "COMMITTED"}:
        raise ValueError("invalid installer recovery journal state")
    if not isinstance(journal["previous_exists"], bool):
        raise ValueError("invalid installer recovery journal previous_exists")


def _transition_result(outcome: str, incoming: dict, **extra: object) -> dict:
    result = {
        "contract": TRANSITION_PLAN_CONTRACT,
        "status": "PASS",
        "outcome": outcome,
        "incoming_version": incoming["version"],
        "incoming_content_identity": incoming["content_identity"],
    }
    result.update(extra)
    return result


def _plan_installation_transition_internal(
    manifest: dict,
    target: Path,
    *,
    managed_root: str = DEFAULT_MANAGED_ROOT,
    project_package: Path | None = None,
    allow_downgrade: bool = False,
) -> dict:
    target = target.resolve()
    if not target.is_dir():
        raise ValueError("target must be an existing project directory")

    journal_path, backup = journal_paths(target)
    if journal_path.exists():
        if not journal_path.is_file() or journal_path.is_symlink():
            return _transition_result(
                "INCOMPATIBLE",
                manifest,
                reason_code="RECOVERY_STATE_INVALID",
                detail="installer recovery journal is not a regular file",
            )
        try:
            journal = load_json(journal_path)
            validate_journal(journal, managed_root)
        except Exception as exc:
            return _transition_result(
                "INCOMPATIBLE",
                manifest,
                reason_code="RECOVERY_STATE_INVALID",
                detail=str(exc),
            )
        return _transition_result(
            "RECOVERY_REQUIRED",
            manifest,
            journal_state=journal["state"],
            previous_content_identity=journal["previous_content_identity"],
        )
    if backup.exists():
        return _transition_result(
            "INCOMPATIBLE",
            manifest,
            reason_code="ORPHAN_BACKUP",
            detail="orphan installer backup exists without recovery journal",
        )

    if project_package is not None:
        try:
            validate_project_compatibility(project_package.resolve(), manifest)
        except Exception as exc:
            return _transition_result(
                "INCOMPATIBLE",
                manifest,
                reason_code="PROJECT_INCOMPATIBLE",
                detail=str(exc),
            )

    managed = resolve_managed_root(target, managed_root)
    try:
        previous = read_previous_manifest(managed)
    except Exception as exc:
        return _transition_result(
            "INCOMPATIBLE",
            manifest,
            reason_code="MANAGED_STATE_INVALID",
            detail=str(exc),
        )

    drift = detect_drift(managed, previous)
    if drift:
        return _transition_result(
            "MANAGED_DRIFT",
            manifest,
            previous_version=previous["version"] if previous else None,
            drift=drift,
        )

    if previous is None:
        return _transition_result("FRESH_INSTALL", manifest, previous_version=None)

    previous_version = previous["version"]
    previous_identity = previous["content_identity"]
    if previous_version == manifest["version"]:
        if previous_identity != manifest["content_identity"]:
            return _transition_result(
                "IDENTITY_COLLISION",
                manifest,
                previous_version=previous_version,
                previous_content_identity=previous_identity,
            )
        return _transition_result(
            "NO_CHANGE",
            manifest,
            previous_version=previous_version,
            previous_content_identity=previous_identity,
        )

    old = numeric_version(previous_version)
    new = numeric_version(manifest["version"])
    if old is not None and new is not None and new < old:
        if not allow_downgrade:
            return _transition_result(
                "DOWNGRADE_REQUIRES_AUTHORIZATION",
                manifest,
                previous_version=previous_version,
                previous_content_identity=previous_identity,
            )
        return _transition_result(
            "DOWNGRADE",
            manifest,
            previous_version=previous_version,
            previous_content_identity=previous_identity,
        )

    return _transition_result(
        "UPDATE",
        manifest,
        previous_version=previous_version,
        previous_content_identity=previous_identity,
    )


def plan_installation_transition(
    manifest_path: Path,
    target: Path,
    *,
    managed_root: str = DEFAULT_MANAGED_ROOT,
    project_package: Path | None = None,
    allow_downgrade: bool = False,
) -> dict:
    """Read-only target transition classification for one locally pinned manifest."""
    try:
        manifest_path = manifest_path.resolve()
        if not manifest_path.is_file():
            raise ValueError("manifest must be an existing local file")
        manifest = rd.validate_manifest(manifest_path)
        return _plan_installation_transition_internal(
            manifest,
            target,
            managed_root=managed_root,
            project_package=project_package,
            allow_downgrade=allow_downgrade,
        )
    except Exception as exc:
        return {
            "contract": TRANSITION_PLAN_CONTRACT,
            "status": "FAIL",
            "outcome": "INVALID_INPUT",
            "detail": str(exc),
        }


def _raise_for_blocked_transition(plan: dict) -> None:
    outcome = plan["outcome"]
    if outcome == "MANAGED_DRIFT":
        raise ValueError("managed-file drift detected: " + ", ".join(plan["drift"]))
    if outcome == "IDENTITY_COLLISION":
        raise ValueError("same release version has different content identity")
    if outcome == "DOWNGRADE_REQUIRES_AUTHORIZATION":
        raise ValueError("downgrade rejected; pass --allow-downgrade for an explicit downgrade")
    if outcome == "INCOMPATIBLE":
        raise ValueError(plan.get("detail", "installation target is incompatible"))
    if outcome == "RECOVERY_REQUIRED":
        raise ValueError("installer recovery required before install")


def recover_interrupted_transaction(target: Path, managed_root: str = DEFAULT_MANAGED_ROOT) -> dict:
    """Recover any durable P4 journal before a new install may proceed."""
    target = target.resolve()
    managed = resolve_managed_root(target, managed_root)
    journal_path, backup = journal_paths(target)
    if not journal_path.exists():
        if backup.exists():
            raise ValueError("orphan installer backup exists without recovery journal")
        return {"status": "CLEAN"}
    if not journal_path.is_file() or journal_path.is_symlink():
        raise ValueError("installer recovery journal is not a regular file")
    journal = load_json(journal_path)
    validate_journal(journal, managed_root)

    if journal["state"] == "COMMITTED":
        if manifest_identity_at(managed) != journal["incoming_content_identity"]:
            raise ValueError("committed installer journal does not match live installation")
        if backup.exists():
            shutil.rmtree(backup)
        journal_path.unlink()
        return {"status": "COMMIT_FINALIZED"}

    write_journal(journal_path, journal, "RESTORE_PENDING")
    if journal["previous_exists"]:
        previous_id = journal["previous_content_identity"]
        if backup.exists():
            if managed.exists():
                shutil.rmtree(managed)
            backup.rename(managed)
        if not managed.exists() or manifest_identity_at(managed) != previous_id:
            raise ValueError("cannot recover previous verified installation from journal")
    else:
        if managed.exists():
            shutil.rmtree(managed)
        if backup.exists():
            shutil.rmtree(backup)

    if backup.exists():
        shutil.rmtree(backup)
    journal_path.unlink()
    return {"status": "RESTORED_PREVIOUS" if journal["previous_exists"] else "RESTORED_EMPTY"}


def make_installation_record(manifest: dict, transport_sha256: str, managed_root: str, installed_at: str,
                             runner_id: str | None, source_repository: str | None,
                             source_locator: str | None, update_locator: str | None) -> dict:
    record = {
        "contract": "reasoning-distiller-installation/1",
        "package_contract": manifest["contract"],
        "installer": {"contract": INSTALLER_CONTRACT, "entrypoint": "rd_install.py", "runtime": "python3"},
        "version": manifest["version"], "source_commit": manifest["source_commit"],
        "content_identity": manifest["content_identity"], "transport_sha256": transport_sha256,
        "managed_root": managed_root, "installed_at": installed_at, "compatibility": manifest["compatibility"],
    }
    if runner_id is not None:
        record["runner"] = {"kind": "agent-runner", "invocation_id": runner_id}
    for key, value in {"source_repository": source_repository, "source_locator": source_locator, "update_locator": update_locator}.items():
        if value is not None:
            record[key] = value
    rd.validate_schema(record, rd.INSTALL_SCHEMA)
    return record


def install(package: Path, manifest_path: Path, transport_sha256: str, target: Path, *,
            managed_root: str = DEFAULT_MANAGED_ROOT, project_package: Path | None = None,
            allow_downgrade: bool = False, installed_at: str = DEFAULT_INSTALLED_AT,
            runner_id: str | None = None, source_repository: str | None = None,
            source_locator: str | None = None, update_locator: str | None = None,
            _simulate_interrupt_after: str | None = None) -> dict:
    package, manifest_path, target = package.resolve(), manifest_path.resolve(), target.resolve()
    if not package.is_file() or not manifest_path.is_file():
        raise ValueError("package and manifest must be existing local files")
    if not target.is_dir():
        raise ValueError("target must be an existing project directory")

    # Recovery remains a distinct mutation primitive. Preserve P4 behavior by
    # resolving transaction residue first, then independently verify and re-plan.
    recovery = recover_interrupted_transaction(target, managed_root)
    manifest, payload, _ = _verify_release_bundle_internal(package, manifest_path, transport_sha256)
    plan = _plan_installation_transition_internal(
        manifest,
        target,
        managed_root=managed_root,
        project_package=project_package,
        allow_downgrade=allow_downgrade,
    )
    _raise_for_blocked_transition(plan)

    managed = resolve_managed_root(target, managed_root)
    previous = read_previous_manifest(managed)
    installation = make_installation_record(manifest, transport_sha256, managed_root, installed_at,
                                            runner_id, source_repository, source_locator, update_locator)

    stage_parent = Path(tempfile.mkdtemp(prefix=".rd-stage-", dir=target))
    stage = stage_parent / "managed"
    journal_path, backup = journal_paths(target)
    journal = {
        "contract": TRANSACTION_CONTRACT,
        "managed_root": managed_root,
        "state": "PREPARED",
        "previous_exists": previous is not None,
        "previous_content_identity": previous["content_identity"] if previous else None,
        "incoming_content_identity": manifest["content_identity"],
    }
    interrupted = False
    try:
        stage.mkdir()
        write_stage(stage, payload, manifest, installation)
        validate_installed_tree(stage, manifest)
        if backup.exists() or journal_path.exists():
            raise ValueError("installer transaction residue appeared during staging")
        atomic_write_json(journal_path, journal)
        if _simulate_interrupt_after == "prepared":
            interrupted = True; raise SimulatedInterruption("prepared")

        write_journal(journal_path, journal, "BACKUP_PENDING")
        if managed.exists():
            managed.rename(backup)
        if _simulate_interrupt_after == "backup":
            interrupted = True; raise SimulatedInterruption("backup")

        write_journal(journal_path, journal, "ACTIVATE_PENDING")
        stage.rename(managed)
        if _simulate_interrupt_after == "activation":
            interrupted = True; raise SimulatedInterruption("activation")

        write_journal(journal_path, journal, "VALIDATE_PENDING")
        try:
            validate_installed_tree(managed, manifest)
        except Exception:
            write_journal(journal_path, journal, "RESTORE_PENDING")
            if managed.exists():
                shutil.rmtree(managed)
            if previous is not None and backup.exists():
                backup.rename(managed)
            raise

        write_journal(journal_path, journal, "COMMITTED")
        if _simulate_interrupt_after == "committed":
            interrupted = True; raise SimulatedInterruption("committed")
        if backup.exists():
            shutil.rmtree(backup)
        journal_path.unlink()
    finally:
        if stage_parent.exists():
            shutil.rmtree(stage_parent, ignore_errors=True)
        # A simulated hard interruption deliberately leaves durable journal/backup/live
        # state for the next invocation to recover. Ordinary exceptions are recovered
        # immediately through the same idempotent P4 routine.
        if not interrupted and journal_path.exists():
            recover_interrupted_transaction(target, managed_root)

    return {
        "status": "PASS", "installer_contract": INSTALLER_CONTRACT,
        "version": manifest["version"], "content_identity": manifest["content_identity"],
        "transport_sha256": transport_sha256, "managed_root": managed_root,
        "previous_version": previous["version"] if previous else None,
        "recovery_before_install": recovery["status"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install a verified Reasoning Distiller package into a project workspace.")
    parser.add_argument("--package", type=Path); parser.add_argument("--manifest", type=Path)
    parser.add_argument("--transport-sha256"); parser.add_argument("--target", type=Path)
    parser.add_argument("--managed-root", default=DEFAULT_MANAGED_ROOT); parser.add_argument("--project-package", type=Path)
    parser.add_argument("--allow-downgrade", action="store_true"); parser.add_argument("--installed-at", default=DEFAULT_INSTALLED_AT)
    parser.add_argument("--runner-id"); parser.add_argument("--source-repository"); parser.add_argument("--source-locator"); parser.add_argument("--update-locator")
    parser.add_argument("--recover-only", action="store_true", help="recover an interrupted local install and exit")
    parser.add_argument("--version", action="store_true", help="print installer contract and exit")
    return parser


def main() -> int:
    parser = build_parser(); args = parser.parse_args()
    if args.version:
        print(INSTALLER_CONTRACT); return 0
    if args.recover_only:
        if args.target is None: parser.error("--recover-only requires --target")
        print(json.dumps(recover_interrupted_transaction(args.target, args.managed_root), sort_keys=True)); return 0
    required = {"--package": args.package, "--manifest": args.manifest, "--transport-sha256": args.transport_sha256, "--target": args.target}
    missing = [name for name, value in required.items() if value is None]
    if missing: parser.error("missing required arguments: " + ", ".join(missing))
    result = install(args.package, args.manifest, args.transport_sha256, args.target,
                     managed_root=args.managed_root, project_package=args.project_package,
                     allow_downgrade=args.allow_downgrade, installed_at=args.installed_at,
                     runner_id=args.runner_id, source_repository=args.source_repository,
                     source_locator=args.source_locator, update_locator=args.update_locator)
    print(json.dumps(result, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())