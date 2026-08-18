#!/usr/bin/env python3
"""Deterministic, network-independent Reasoning Distiller installer.

The runner retrieves package artifacts. This program consumes only local files,
installs only the declared managed root, fails closed on drift/incompatibility,
and restores the previous installation when post-activation validation fails.

P4 adds crash-journal recovery pressure beyond this P3 transactional baseline.
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
DEFAULT_MANAGED_ROOT = ".reasoning-distiller"
DEFAULT_INSTALLED_AT = "1970-01-01T00:00:00Z"

HERE = Path(__file__).resolve().parent
VALIDATOR_PATH = HERE / "validate_install_package_contract.py"
spec = importlib.util.spec_from_file_location("rd_package_contract", VALIDATOR_PATH)
rd = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(rd)


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


def resolve_managed_root(target: Path, managed_root: str) -> Path:
    rd.validate_rel_path(managed_root, "managed_root")
    root = (target / managed_root).resolve()
    target_resolved = target.resolve()
    try:
        root.relative_to(target_resolved)
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
            continue
        if sha256_file(full) != item["sha256"]:
            drift.append(f"content:{path}")
            continue
        actual_mode = full.stat().st_mode & 0o777
        if actual_mode != int(item["mode"], 8):
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
    if backend is not None:
        backend_type = backend.get("type")
        if backend_type not in manifest["compatibility"]["backends"]:
            raise ValueError(f"canonical backend {backend_type!r} is not supported by release")
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


def make_installation_record(
    manifest: dict,
    transport_sha256: str,
    managed_root: str,
    installed_at: str,
    runner_id: str | None,
    source_repository: str | None,
    source_locator: str | None,
    update_locator: str | None,
) -> dict:
    record = {
        "contract": "reasoning-distiller-installation/1",
        "package_contract": manifest["contract"],
        "installer": {
            "contract": INSTALLER_CONTRACT,
            "entrypoint": "rd_install.py",
            "runtime": "python3",
        },
        "version": manifest["version"],
        "source_commit": manifest["source_commit"],
        "content_identity": manifest["content_identity"],
        "transport_sha256": transport_sha256,
        "managed_root": managed_root,
        "installed_at": installed_at,
        "compatibility": manifest["compatibility"],
    }
    if runner_id is not None:
        record["runner"] = {"kind": "agent-runner", "invocation_id": runner_id}
    optional = {
        "source_repository": source_repository,
        "source_locator": source_locator,
        "update_locator": update_locator,
    }
    record.update({key: value for key, value in optional.items() if value is not None})
    rd.validate_schema(record, rd.INSTALL_SCHEMA)
    return record


def install(
    package: Path,
    manifest_path: Path,
    transport_sha256: str,
    target: Path,
    *,
    managed_root: str = DEFAULT_MANAGED_ROOT,
    project_package: Path | None = None,
    allow_downgrade: bool = False,
    installed_at: str = DEFAULT_INSTALLED_AT,
    runner_id: str | None = None,
    source_repository: str | None = None,
    source_locator: str | None = None,
    update_locator: str | None = None,
) -> dict:
    package = package.resolve()
    manifest_path = manifest_path.resolve()
    target = target.resolve()
    if not package.is_file() or not manifest_path.is_file():
        raise ValueError("package and manifest must be existing local files")
    if not target.is_dir():
        raise ValueError("target must be an existing project directory")

    manifest = rd.validate_manifest(manifest_path)
    validate_transport(package, transport_sha256, manifest)
    payload = inspect_archive(package, manifest)
    validate_project_compatibility(project_package.resolve() if project_package else None, manifest)

    managed = resolve_managed_root(target, managed_root)
    previous = read_previous_manifest(managed)
    drift = detect_drift(managed, previous)
    if drift:
        raise ValueError("managed-file drift detected: " + ", ".join(drift))
    compare_release_identity(previous, manifest, allow_downgrade)

    installation = make_installation_record(
        manifest,
        transport_sha256,
        managed_root,
        installed_at,
        runner_id,
        source_repository,
        source_locator,
        update_locator,
    )

    stage_parent = Path(tempfile.mkdtemp(prefix=".rd-stage-", dir=target))
    stage = stage_parent / DEFAULT_MANAGED_ROOT
    backup = target / ".rd-install-backup"
    activated = False
    try:
        stage.mkdir()
        write_stage(stage, payload, manifest, installation)
        validate_installed_tree(stage, manifest)

        if backup.exists():
            raise ValueError("stale .rd-install-backup exists; P4 recovery required before install")
        if managed.exists():
            managed.rename(backup)
        stage.rename(managed)
        activated = True
        validate_installed_tree(managed, manifest)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if activated and managed.exists():
            shutil.rmtree(managed)
        if backup.exists():
            backup.rename(managed)
        raise
    finally:
        if stage_parent.exists():
            shutil.rmtree(stage_parent, ignore_errors=True)

    return {
        "status": "PASS",
        "installer_contract": INSTALLER_CONTRACT,
        "version": manifest["version"],
        "content_identity": manifest["content_identity"],
        "transport_sha256": transport_sha256,
        "managed_root": managed_root,
        "previous_version": previous["version"] if previous else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install a verified Reasoning Distiller package into a project workspace.")
    parser.add_argument("--package", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--transport-sha256")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--managed-root", default=DEFAULT_MANAGED_ROOT)
    parser.add_argument("--project-package", type=Path)
    parser.add_argument("--allow-downgrade", action="store_true")
    parser.add_argument("--installed-at", default=DEFAULT_INSTALLED_AT)
    parser.add_argument("--runner-id")
    parser.add_argument("--source-repository")
    parser.add_argument("--source-locator")
    parser.add_argument("--update-locator")
    parser.add_argument("--version", action="store_true", help="print installer contract and exit")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(INSTALLER_CONTRACT)
        return 0
    required = {
        "--package": args.package,
        "--manifest": args.manifest,
        "--transport-sha256": args.transport_sha256,
        "--target": args.target,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        parser.error("missing required arguments: " + ", ".join(missing))
    result = install(
        args.package,
        args.manifest,
        args.transport_sha256,
        args.target,
        managed_root=args.managed_root,
        project_package=args.project_package,
        allow_downgrade=args.allow_downgrade,
        installed_at=args.installed_at,
        runner_id=args.runner_id,
        source_repository=args.source_repository,
        source_locator=args.source_locator,
        update_locator=args.update_locator,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
