#!/usr/bin/env python3
"""Audit an installed Reasoning Distiller tree for runtime isolation violations."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

AUDIT_CONTRACT = "reasoning-distiller-runtime-isolation-audit/1"
TEXT_SUFFIXES = {".py", ".json", ".md", ".yaml", ".yml", ".toml", ".txt", ".sh"}
FORBIDDEN_RUNTIME_TOKENS = (
    "github.com/loteque/reasoning-distiller",
    "raw.githubusercontent.com/loteque/reasoning-distiller",
    "api.github.com/repos/loteque/reasoning-distiller",
    "git@github.com:loteque/reasoning-distiller",
    "docs/distiller/",
    "docs/handoff/rgp/",
)
PROVENANCE_ROOT = ".installation"
INERT_JSON_KEYS = {"$id"}
V1_REGISTRY_PATH = "schemas/resources/context-packaging-v1-resource-registry.json"
V1_SCHEMA_PATH = "schemas/context-pack.schema.json"
V1_SCHEMA_BLOB = "4b240a5698294ce1a217ad758b4031830740fc29"
V1_PEMS_PATH = "backends/pems-cove/pems-v2.schema.json"
V1_PEMS_BLOB = "cd7683d704e8aef2842a0c1b25b453fb1dbc8030"
V1_PEMS_RAW_SHA256 = "sha256:b08e592ab7c10092ff381fe8057cac63ccb7aaa077b52532f5ee609c6fd279c3"
V1_REF_SHA256 = "sha256:5755f841b1a7866cad4cfc0ee268f98bdff5a15c909d00bc66a7b7e3c7299da2"
V1_REF_PATH = "$.$defs.knowledgeItem.properties.pems.$ref"
V1_REGISTRY_SCOPE = "context-packaging-v1-frozen-local-alias"
V1_RESOLUTION = "register_exact_blob_bytes_under_frozen_source_ref"


def _matching_token(value: str) -> str | None:
    lower = value.lower()
    for token in FORBIDDEN_RUNTIME_TOKENS:
        if token.lower() in lower:
            return token
    return None


def _git_blob_sha(data: bytes) -> str:
    prefix = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(prefix + data).hexdigest()


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _verified_v1_local_alias(root: Path) -> dict[tuple[str, str], str]:
    """Return the one frozen legacy alias only when its packaged closure proves exact."""
    registry_path = root / V1_REGISTRY_PATH
    schema_path = root / V1_SCHEMA_PATH
    pems_path = root / V1_PEMS_PATH
    if not registry_path.is_file() or not schema_path.is_file() or not pems_path.is_file():
        return {}
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        schema_bytes = schema_path.read_bytes()
        pems_bytes = pems_path.read_bytes()
        schema = json.loads(schema_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}

    if registry.get("contract") != "reasoning-distiller-context-schema-resource-registry/1":
        return {}
    if registry.get("scope") != V1_REGISTRY_SCOPE:
        return {}
    source = registry.get("source_schema")
    resources = registry.get("resources")
    if not isinstance(source, dict) or not isinstance(resources, list) or len(resources) != 1:
        return {}
    resource = resources[0]
    if not isinstance(resource, dict):
        return {}

    if source != {
        "path": V1_SCHEMA_PATH,
        "git_blob": V1_SCHEMA_BLOB,
        "resource_ref_sha256": V1_REF_SHA256,
    }:
        return {}
    if resource != {
        "semantic": "pems/2",
        "path": V1_PEMS_PATH,
        "git_blob": V1_PEMS_BLOB,
        "raw_sha256": V1_PEMS_RAW_SHA256,
        "resolution": V1_RESOLUTION,
        "network_resolution": False,
    }:
        return {}
    if _git_blob_sha(schema_bytes) != V1_SCHEMA_BLOB:
        return {}
    if _git_blob_sha(pems_bytes) != V1_PEMS_BLOB:
        return {}
    if "sha256:" + hashlib.sha256(pems_bytes).hexdigest() != V1_PEMS_RAW_SHA256:
        return {}

    try:
        ref = schema["$defs"]["knowledgeItem"]["properties"]["pems"]["$ref"]
    except (KeyError, TypeError):
        return {}
    if not isinstance(ref, str) or _sha256_text(ref) != V1_REF_SHA256:
        return {}
    return {(V1_SCHEMA_PATH, V1_REF_PATH): ref}


def _scan_json(
    value: Any,
    path: str = "$",
    *,
    rel: str | None = None,
    allowed_values: dict[tuple[str, str], str] | None = None,
) -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in INERT_JSON_KEYS:
                continue
            violations.extend(
                _scan_json(item, f"{path}.{key}", rel=rel, allowed_values=allowed_values)
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            violations.extend(
                _scan_json(item, f"{path}[{index}]", rel=rel, allowed_values=allowed_values)
            )
    elif isinstance(value, str):
        if rel is not None and allowed_values is not None and allowed_values.get((rel, path)) == value:
            return violations
        token = _matching_token(value)
        if token is not None:
            violations.append(f"{path}:{token}")
    return violations


def audit(installed_root: Path) -> dict:
    root = installed_root.resolve()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("installed root must be a regular directory")

    allowed_values = _verified_v1_local_alias(root)
    violations: list[dict[str, str]] = []
    scanned = 0
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            violations.append({"path": rel, "reason": "symlink-forbidden"})
            continue
        if path.is_dir():
            continue
        if rel == PROVENANCE_ROOT or rel.startswith(PROVENANCE_ROOT + "/"):
            continue
        scanned += 1
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if path.suffix.lower() == ".json":
            try:
                document = json.loads(text)
            except json.JSONDecodeError:
                document = None
            if document is not None:
                for detail in _scan_json(document, rel=rel, allowed_values=allowed_values):
                    violations.append({"path": rel, "reason": f"forbidden-runtime-reference:{detail}"})
                continue

        token = _matching_token(text)
        if token is not None:
            violations.append({"path": rel, "reason": f"forbidden-runtime-reference:{token}"})

    return {
        "contract": AUDIT_CONTRACT,
        "status": "PASS" if not violations else "FAIL",
        "scanned_files": scanned,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a local Reasoning Distiller install for runtime isolation")
    parser.add_argument("installed_root", type=Path)
    args = parser.parse_args()
    result = audit(args.installed_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
