#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import re
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "packaging/package-build.json"
VALIDATOR_PATH = ROOT / "packaging/validate_install_package_contract.py"

spec = importlib.util.spec_from_file_location("rd_package_contract", VALIDATOR_PATH)
rd = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(rd)

SOURCE_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._+-]*$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_config(path: Path = CONFIG_PATH) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("contract") != "reasoning-distiller-package-build/1":
        raise ValueError("unsupported package build contract")
    roots = config.get("managed_roots")
    if not isinstance(roots, list) or not roots:
        raise ValueError("managed_roots must be a non-empty list")
    if roots != sorted(roots):
        raise ValueError("managed_roots must be lexicographically sorted")
    if len(set(roots)) != len(roots):
        raise ValueError("duplicate managed_root")
    for root in roots:
        rd.validate_rel_path(root, "managed_root")
        if "/" in root:
            raise ValueError("P2 managed_roots must be top-level directories")
    excluded = set(config.get("excluded_top_level", []))
    overlap = excluded.intersection(roots)
    if overlap:
        raise ValueError(f"managed/excluded root overlap: {sorted(overlap)}")
    if config.get("mode_policy", {}).get("default") not in {"0644", "0755"}:
        raise ValueError("mode_policy.default must be 0644 or 0755")
    return config


def assert_safe_source_tree(root: Path, config: dict) -> None:
    for managed_root in config["managed_roots"]:
        source = root / managed_root
        if not source.is_dir():
            raise ValueError(f"missing managed source root: {managed_root}")
        if source.is_symlink():
            raise ValueError(f"managed source root may not be a symlink: {managed_root}")

    for excluded in config.get("excluded_top_level", []):
        if excluded in config["managed_roots"]:
            raise ValueError(f"excluded root selected for package: {excluded}")


def collect_files(root: Path, config: dict) -> list[dict]:
    mode = config["mode_policy"]["default"]
    items: list[dict] = []
    seen_casefold: set[str] = set()

    for managed_root in config["managed_roots"]:
        source_root = root / managed_root
        for path in sorted(source_root.rglob("*"), key=lambda p: p.as_posix()):
            if path.is_symlink():
                raise ValueError(f"symlink forbidden in package source: {path.relative_to(root).as_posix()}")
            if path.is_dir():
                continue
            if not path.is_file():
                raise ValueError(f"unsupported source node: {path.relative_to(root).as_posix()}")
            rel = path.relative_to(root).as_posix()
            rd.validate_rel_path(rel, "file")
            folded = rel.casefold()
            if folded in seen_casefold:
                raise ValueError(f"case-fold collision in package source: {rel}")
            seen_casefold.add(folded)
            data = path.read_bytes()
            items.append({
                "path": rel,
                "mode": mode,
                "sha256": sha256_bytes(data),
                "data": data,
            })

    if not items:
        raise ValueError("package payload is empty")
    return items


def make_manifest(version: str, source_commit: str, config: dict, files: list[dict]) -> dict:
    manifest = {
        "contract": "reasoning-distiller-install-package/1",
        "version": version,
        "source_commit": source_commit,
        "content_identity": "sha256:" + "0" * 64,
        "transport_sha256": "0" * 64,
        "compatibility": config["compatibility"],
        "managed_roots": list(config["managed_roots"]),
        "files": [
            {"path": item["path"], "mode": item["mode"], "sha256": item["sha256"]}
            for item in files
        ],
    }
    manifest["content_identity"] = rd.compute_content_identity(manifest)
    return manifest


def build_tar_gz(files: list[dict]) -> bytes:
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for item in files:
            info = tarfile.TarInfo(name=item["path"])
            info.size = len(item["data"])
            info.mode = int(item["mode"], 8)
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.pax_headers = {}
            tar.addfile(info, io.BytesIO(item["data"]))
    tar_bytes = tar_buffer.getvalue()

    gzip_buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=gzip_buffer, mtime=0, compresslevel=9) as gz:
        gz.write(tar_bytes)
    return gzip_buffer.getvalue()


def verify_archive(archive_bytes: bytes, manifest: dict) -> None:
    expected = {item["path"]: item for item in manifest["files"]}
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        members = tar.getmembers()
        names = [member.name for member in members]
        if names != sorted(expected):
            raise ValueError("archive member order/content differs from canonical manifest order")
        if len(names) != len(set(names)):
            raise ValueError("archive contains duplicate paths")
        if set(names) != set(expected):
            raise ValueError("archive and manifest file sets differ")
        for member in members:
            if not member.isfile() or member.issym() or member.islnk():
                raise ValueError(f"archive contains non-regular file: {member.name}")
            rd.validate_rel_path(member.name, "archive member")
            if member.uid != 0 or member.gid != 0 or member.mtime != 0:
                raise ValueError(f"archive metadata is not normalized: {member.name}")
            expected_mode = int(expected[member.name]["mode"], 8)
            if member.mode != expected_mode:
                raise ValueError(f"archive mode mismatch: {member.name}")
            extracted = tar.extractfile(member)
            if extracted is None:
                raise ValueError(f"cannot read archive member: {member.name}")
            digest = sha256_bytes(extracted.read())
            if digest != expected[member.name]["sha256"]:
                raise ValueError(f"archive digest mismatch: {member.name}")


def build(version: str, source_commit: str, output_dir: Path, root: Path = ROOT) -> dict:
    if not VERSION_RE.fullmatch(version):
        raise ValueError("invalid release version")
    if not SOURCE_COMMIT_RE.fullmatch(source_commit):
        raise ValueError("source_commit must be 40 lowercase hex")

    config = load_config(root / "packaging/package-build.json")
    assert_safe_source_tree(root, config)
    files = collect_files(root, config)
    manifest = make_manifest(version, source_commit, config, files)
    archive_bytes = build_tar_gz(files)
    transport_sha = sha256_bytes(archive_bytes)
    manifest["transport_sha256"] = transport_sha

    # Transport digest is intentionally excluded from the content identity, so
    # setting it must not change the canonical package identity.
    if rd.compute_content_identity(manifest) != manifest["content_identity"]:
        raise AssertionError("transport digest changed canonical content identity")

    verify_archive(archive_bytes, manifest)
    rd.validate_schema(manifest, rd.MANIFEST_SCHEMA)
    rd.validate_manifest_semantics(manifest)

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"reasoning-distiller-{version}"
    archive_path = output_dir / f"{stem}.tar.gz"
    manifest_path = output_dir / f"{stem}.manifest.json"
    sha_path = output_dir / f"{stem}.sha256"

    archive_path.write_bytes(archive_bytes)
    manifest_path.write_bytes(canonical_json_bytes(manifest) + b"\n")
    sha_path.write_text(f"{transport_sha}  {archive_path.name}\n", encoding="utf-8", newline="\n")

    return {
        "archive": archive_path,
        "manifest": manifest_path,
        "sha256": sha_path,
        "content_identity": manifest["content_identity"],
        "transport_sha256": transport_sha,
        "file_count": len(files),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic Reasoning Distiller release package")
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    result = build(args.version, args.source_commit, args.output_dir)
    print(json.dumps({key: str(value) if isinstance(value, Path) else value for key, value in result.items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
