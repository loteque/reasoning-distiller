#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA = ROOT / "schemas/install-package-manifest.schema.json"
INSTALL_SCHEMA = ROOT / "schemas/installation-record.schema.json"
RESERVED_GENERATED = {
    "VERSION",
    ".installation/MANIFEST.json",
    ".installation/INSTALLATION.json",
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def identity_payload(manifest: dict) -> dict:
    return {
        "contract": manifest["contract"],
        "version": manifest["version"],
        "source_commit": manifest["source_commit"],
        "compatibility": manifest["compatibility"],
        "managed_roots": sorted(manifest["managed_roots"]),
        "files": sorted(
            [
                {
                    "path": item["path"],
                    "mode": item["mode"],
                    "sha256": item["sha256"],
                }
                for item in manifest["files"]
            ],
            key=lambda item: item["path"],
        ),
    }


def compute_content_identity(manifest: dict) -> str:
    digest = hashlib.sha256(canonical_bytes(identity_payload(manifest))).hexdigest()
    return f"sha256:{digest}"


def validate_rel_path(value: str, label: str) -> None:
    if "\\" in value or "\x00" in value:
        raise ValueError(f"{label}: backslash/NUL forbidden: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError(f"{label}: absolute path forbidden: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"{label}: invalid path component: {value!r}")
    if str(path) != value:
        raise ValueError(f"{label}: path is not normalized: {value!r}")


def under_root(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def validate_manifest_semantics(manifest: dict) -> None:
    roots = manifest["managed_roots"]
    for root in roots:
        validate_rel_path(root, "managed_root")

    if len({r.casefold() for r in roots}) != len(roots):
        raise ValueError("managed_roots contain case-fold collision")

    paths = [item["path"] for item in manifest["files"]]
    for path in paths:
        validate_rel_path(path, "file")

    if len(set(paths)) != len(paths):
        raise ValueError("duplicate file path")
    if len({p.casefold() for p in paths}) != len(paths):
        raise ValueError("file paths contain case-fold collision")

    for path in paths:
        if path in RESERVED_GENERATED:
            raise ValueError(f"release manifest must not include generated installation metadata: {path}")
        if not any(under_root(path, root) for root in roots):
            raise ValueError(f"file outside managed_roots: {path}")

    expected = compute_content_identity(manifest)
    if manifest["content_identity"] != expected:
        raise ValueError(
            f"content_identity mismatch: expected {expected}, got {manifest['content_identity']}"
        )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(instance: dict, schema_path: Path) -> None:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
        key=lambda e: list(e.absolute_path),
    )
    if errors:
        raise ValueError("; ".join(error.message for error in errors))


def validate_manifest(path: Path) -> dict:
    manifest = load_json(path)
    validate_schema(manifest, MANIFEST_SCHEMA)
    validate_manifest_semantics(manifest)
    return manifest


def validate_installation(path: Path) -> dict:
    installation = load_json(path)
    validate_schema(installation, INSTALL_SCHEMA)
    validate_rel_path(installation["managed_root"], "managed_root")
    return installation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--installation", type=Path)
    parser.add_argument("--print-content-identity", type=Path)
    args = parser.parse_args()

    if not any((args.manifest, args.installation, args.print_content_identity)):
        parser.error("at least one validation/identity argument is required")

    if args.manifest:
        validate_manifest(args.manifest)
        print(f"PASS manifest {args.manifest}")
    if args.installation:
        validate_installation(args.installation)
        print(f"PASS installation {args.installation}")
    if args.print_content_identity:
        manifest = load_json(args.print_content_identity)
        validate_schema(manifest, MANIFEST_SCHEMA)
        # Identity calculation is useful while authoring a manifest, so this mode
        # intentionally does not require the stored content_identity to match.
        print(compute_content_identity(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
