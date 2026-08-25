"""P10-G4 deterministic production prepare integration.

This module implements only the sealed-context ``reasoning-distiller-invocation/2``
prepare boundary. It validates the exact sealed inputs and installed package,
invokes the closed P9 renderer, derives and persists the closed G3 provenance
registry, constructs ``reasoning-distiller-activation-bundle/2``, and persists
``reasoning-distiller-prepared-invocation/1`` before any provider execution.

It does not build context packs, discover project evidence, execute a provider,
finalize model output, reconcile semantics, admit knowledge, mutate canonical
state, or mutate role/authority/activation state.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from typing import Any, Mapping, Sequence

from . import provenance_bridge, renderer
from .pems_projection import _strict_json
from .persistence_adapter import (
    ImmutableOutputCollisionError,
    PersistenceBoundaryError,
    PersistenceResult,
    persist_immutable_artifact,
)

INVOCATION_CONTRACT = "reasoning-distiller-invocation/2"
RESULT_CONTRACT = "reasoning-distiller-invocation-result/2"
PACK_CONTRACT = "reasoning-distiller-context-pack/2"
RENDERER_PROFILE_CONTRACT = "reasoning-distiller-context-renderer-profile/2"
ELIGIBILITY_CONTRACT = "reasoning-distiller-context-profile-eligibility/1"
ACTIVATION_BUNDLE_CONTRACT = "reasoning-distiller-activation-bundle/2"
PREPARED_INVOCATION_CONTRACT = "reasoning-distiller-prepared-invocation/1"
MODEL_TRANSPORT_CONTRACT = "reasoning-distiller-model-transport/1"
RGP_VALIDATOR_CONTRACT = "rgp-validator/1"
PACKAGE_MANIFEST_CONTRACT = "reasoning-distiller-install-package/1"
BINDING_SCHEME = "python-closed-bundle/1"

DIRECTIVE_RELATIVE_PATH = "agents/distiller/DIRECTIVE.md"
DIRECTIVE_BUNDLE_PATH = ".reasoning-distiller/agents/distiller/DIRECTIVE.md"
VALIDATOR_RELATIVE_PATH = "validators/rgp_validator.py"
MANIFEST_RELATIVE_PATH = ".installation/MANIFEST.json"

ACTIVATION_INSTRUCTION = (
    "Return only the raw rgp/1 candidate graph JSON required by the installed "
    "Distiller directive. Use only the supplied sealed context and provenance registry."
)
REFERENCE_TRANSPORT_ADAPTER_ID = "reference"

_REQUEST_DOMAIN = b"reasoning-distiller-invocation/2\x00"
_ELIGIBILITY_DOMAIN = b"reasoning-distiller-context-profile-eligibility-decision/1\x00"
_ACTIVATION_BUNDLE_DOMAIN = b"reasoning-distiller-activation-bundle/2\x00"
_PREPARED_INVOCATION_DOMAIN = b"reasoning-distiller-prepared-invocation/1\x00"

_EXPECTED_RUNTIME = {
    "implementation": "cpython",
    "major": 3,
    "minor": 12,
    "micro": 0,
    "cache_tag": "cpython-312",
}

# These are generated/runtime caches explicitly ignored by the G2 package contract.
_IGNORED_GENERATED_DIRS = frozenset({"__pycache__"})
_IGNORED_GENERATED_SUFFIXES = frozenset({".pyc", ".pyo"})
_RESERVED_PROJECT_ROOTS = frozenset({".git", ".reasoning-distiller", "project-knowledge"})

_REQUIRED_PACKAGE_FILES = frozenset(
    {
        DIRECTIVE_RELATIVE_PATH,
        VALIDATOR_RELATIVE_PATH,
        "context_packaging/prepare_integration.py",
        "context_packaging/provenance_bridge.py",
        "context_packaging/persistence_adapter.py",
        "context_packaging/renderer.py",
        "protocols/rgp/production-integration-v2.json",
        "protocols/rgp/python-closed-bundle-v1.json",
        "protocols/rgp/renderer-execution-binding-v1.json",
        "runtime/rd_distill.py",
        "runtime/rd_distill_core.py",
        "schemas/activation-bundle-v2.schema.json",
        "schemas/context-profile-eligibility.schema.json",
        "schemas/context-provenance-registry.schema.json",
        "schemas/context-rendered-activation-v2.schema.json",
        "schemas/context-renderer-profile-v2.schema.json",
        "schemas/invocation-request-v2.schema.json",
        "schemas/invocation-result-v2.schema.json",
        "schemas/prepared-invocation.schema.json",
        "schemas/renderer-execution-binding.schema.json",
    }
)


class PrepareFailure(ValueError):
    """One exact frozen /2 failure owned by the prepare boundary."""

    def __init__(self, stage: str, reason_code: str, detail: str, exit_code: int) -> None:
        super().__init__(detail)
        self.stage = stage
        self.reason_code = reason_code
        self.detail = detail
        self.exit_code = exit_code


@dataclass(frozen=True)
class PrepareResult:
    invocation_id: str
    activation_bundle: Mapping[str, Any]
    serialized_activation_bundle: bytes
    prepared_invocation: Mapping[str, Any]
    serialized_prepared_invocation: bytes
    provenance_registry: Mapping[str, Any]
    prepared_persistence: PersistenceResult
    registry_persistence: PersistenceResult


EXIT_INTERNAL = 1
EXIT_PREFLIGHT = 2
EXIT_ACTIVATION = 3
EXIT_PERSISTENCE = 6


def _fail(stage: str, code: str, detail: str, exit_code: int) -> PrepareFailure:
    return PrepareFailure(stage, code, detail, exit_code)


def failure_result(invocation_id: str, failure: PrepareFailure) -> dict[str, Any]:
    return {
        "contract": RESULT_CONTRACT,
        "invocation_id": invocation_id if _valid_invocation_id(invocation_id) else "unknown",
        "status": "FAIL",
        "stage": failure.stage,
        "reason_code": failure.reason_code,
        "detail": failure.detail,
    }


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _domain_identity(domain: bytes, value: Mapping[str, Any]) -> str:
    return _sha256(domain + renderer._jcs(value))


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _valid_invocation_id(value: Any) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        return False
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
    return value[0].isalnum() and all(ch in allowed for ch in value)


def _normalized_sha256(value: Any) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        raise ValueError("invalid sha256 identity")
    digest = value[7:]
    if any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("invalid sha256 identity")
    return value


def _validate_relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise _fail("preflight", "UNSAFE_PATH", f"{label} must be a normalized relative path", EXIT_PREFLIGHT)
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise _fail("preflight", "UNSAFE_PATH", f"{label} must be a normalized relative path", EXIT_PREFLIGHT)
    if str(path) != value:
        raise _fail("preflight", "UNSAFE_PATH", f"{label} must be a normalized relative path", EXIT_PREFLIGHT)
    return value


def _reject_symlink_components(path: Path, stop: Path) -> None:
    current = stop
    try:
        relative = path.relative_to(stop)
    except ValueError as exc:
        raise _fail("preflight", "PATH_ESCAPE", "path escapes its declared project root", EXIT_PREFLIGHT) from exc
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise _fail("preflight", "PATH_ESCAPE", "symlinked project input/output path is unsupported", EXIT_PREFLIGHT)
        except OSError as exc:
            raise _fail("preflight", "PATH_ESCAPE", "project path could not be inspected safely", EXIT_PREFLIGHT) from exc


def _project_root(cwd: Path, relative: str) -> Path:
    rel = _validate_relative_path(relative, "project_root")
    base = cwd.resolve(strict=True)
    candidate = base.joinpath(*PurePosixPath(rel).parts)
    _reject_symlink_components(candidate, base)
    try:
        root = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise _fail("preflight", "PROJECT_ROOT_MISSING", f"project root does not exist: {rel}", EXIT_PREFLIGHT) from exc
    if not root.is_dir():
        raise _fail("preflight", "PROJECT_ROOT_MISSING", f"project root is not a directory: {rel}", EXIT_PREFLIGHT)
    try:
        root.relative_to(base)
    except ValueError as exc:
        raise _fail("preflight", "PATH_ESCAPE", "project root escapes current workspace", EXIT_PREFLIGHT) from exc
    return root


def _input_file(project_root: Path, locator: str, label: str, unresolved_code: str) -> Path:
    rel = _validate_relative_path(locator, label)
    candidate = project_root.joinpath(*PurePosixPath(rel).parts)
    _reject_symlink_components(candidate, project_root)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise _fail("preflight", unresolved_code, f"{label} is unresolved: {locator}", EXIT_PREFLIGHT) from exc
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise _fail("preflight", "PATH_ESCAPE", f"{label} escapes project root", EXIT_PREFLIGHT) from exc
    if not resolved.is_file() or resolved.is_symlink():
        raise _fail("preflight", unresolved_code, f"{label} is not a regular file: {locator}", EXIT_PREFLIGHT)
    return resolved


def _output_target(project_root: Path, locator: str, label: str) -> Path:
    rel = _validate_relative_path(locator, label)
    parts = PurePosixPath(rel).parts
    if parts and parts[0] in _RESERVED_PROJECT_ROOTS:
        raise _fail("preflight", "UNSAFE_PATH", f"{label} targets a protected project/framework store", EXIT_PREFLIGHT)
    candidate = project_root.joinpath(*parts)
    parent = candidate.parent
    _reject_symlink_components(parent, project_root)
    try:
        parent_resolved = parent.resolve(strict=True)
    except FileNotFoundError as exc:
        raise _fail("preflight", "UNSAFE_PATH", f"{label} parent directory must already exist", EXIT_PREFLIGHT) from exc
    try:
        parent_resolved.relative_to(project_root)
    except ValueError as exc:
        raise _fail("preflight", "PATH_ESCAPE", f"{label} escapes project root", EXIT_PREFLIGHT) from exc
    if not parent_resolved.is_dir():
        raise _fail("preflight", "UNSAFE_PATH", f"{label} parent is not a directory", EXIT_PREFLIGHT)
    target = parent_resolved / candidate.name
    if target.exists() and target.is_symlink():
        raise _fail("preflight", "PATH_ESCAPE", f"{label} is a symlink", EXIT_PREFLIGHT)
    return target


def _load_strict_json(raw: bytes, label: str, code: str) -> dict[str, Any]:
    try:
        value = _strict_json(raw)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise _fail("preflight", code, f"{label} must be strict UTF-8 JSON", EXIT_PREFLIGHT) from exc
    if not isinstance(value, dict):
        raise _fail("preflight", code, f"{label} must be a JSON object", EXIT_PREFLIGHT)
    return value


def _validate_request(value: Mapping[str, Any]) -> None:
    required = {"contract", "invocation_id", "created_at", "project_root", "context", "output"}
    if set(value) != required:
        raise _fail("preflight", "INVALID_REQUEST", "invocation/2 has unknown or missing top-level fields", EXIT_PREFLIGHT)
    if value.get("contract") != INVOCATION_CONTRACT:
        raise _fail("preflight", "UNSUPPORTED_CONTRACT", f"expected {INVOCATION_CONTRACT}", EXIT_PREFLIGHT)
    if not _valid_invocation_id(value.get("invocation_id")):
        raise _fail("preflight", "INVALID_REQUEST", "invocation_id is invalid", EXIT_PREFLIGHT)
    created_at = value.get("created_at")
    if not isinstance(created_at, str):
        raise _fail("preflight", "INVALID_REQUEST", "created_at must be a date-time string", EXIT_PREFLIGHT)
    try:
        parsed_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _fail("preflight", "INVALID_REQUEST", "created_at must be RFC3339-compatible", EXIT_PREFLIGHT) from exc
    if parsed_time.tzinfo is None:
        raise _fail("preflight", "INVALID_REQUEST", "created_at must include an offset", EXIT_PREFLIGHT)
    _validate_relative_path(value.get("project_root"), "project_root")

    context = value.get("context")
    if not isinstance(context, Mapping) or set(context) != {"pack", "renderer_profile", "profile_eligibility"}:
        raise _fail("preflight", "INVALID_REQUEST", "context must contain exactly pack, renderer_profile, and profile_eligibility", EXIT_PREFLIGHT)

    pack = context.get("pack")
    if not isinstance(pack, Mapping) or set(pack) != {"contract", "locator", "raw_sha256", "pack_identity_sha256"}:
        raise _fail("preflight", "INVALID_REQUEST", "context.pack shape is invalid", EXIT_PREFLIGHT)
    if pack.get("contract") != PACK_CONTRACT:
        raise _fail("preflight", "UNSUPPORTED_CONTEXT_PACK", f"expected {PACK_CONTRACT}", EXIT_PREFLIGHT)
    _validate_relative_path(pack.get("locator"), "context.pack.locator")
    try:
        _normalized_sha256(pack.get("raw_sha256"))
        _normalized_sha256(pack.get("pack_identity_sha256"))
    except ValueError as exc:
        raise _fail("preflight", "INVALID_REQUEST", "context.pack SHA-256 fields are invalid", EXIT_PREFLIGHT) from exc

    profile = context.get("renderer_profile")
    if not isinstance(profile, Mapping) or set(profile) != {"contract", "locator", "raw_sha256", "profile_id", "profile_version"}:
        raise _fail("preflight", "INVALID_REQUEST", "context.renderer_profile shape is invalid", EXIT_PREFLIGHT)
    if profile.get("contract") != RENDERER_PROFILE_CONTRACT:
        raise _fail("preflight", "UNSUPPORTED_RENDERER_PROFILE", f"expected {RENDERER_PROFILE_CONTRACT}", EXIT_PREFLIGHT)
    _validate_relative_path(profile.get("locator"), "context.renderer_profile.locator")
    if not all(isinstance(profile.get(k), str) and profile[k] for k in ("profile_id", "profile_version")):
        raise _fail("preflight", "INVALID_REQUEST", "renderer profile identity is invalid", EXIT_PREFLIGHT)
    try:
        _normalized_sha256(profile.get("raw_sha256"))
    except ValueError as exc:
        raise _fail("preflight", "INVALID_REQUEST", "renderer profile raw_sha256 is invalid", EXIT_PREFLIGHT) from exc

    eligibility = context.get("profile_eligibility")
    if not isinstance(eligibility, Mapping) or set(eligibility) != {"contract", "locator", "raw_sha256"}:
        raise _fail("preflight", "INVALID_REQUEST", "context.profile_eligibility shape is invalid", EXIT_PREFLIGHT)
    if eligibility.get("contract") != ELIGIBILITY_CONTRACT:
        raise _fail("preflight", "INVALID_REQUEST", f"expected {ELIGIBILITY_CONTRACT}", EXIT_PREFLIGHT)
    _validate_relative_path(eligibility.get("locator"), "context.profile_eligibility.locator")
    try:
        _normalized_sha256(eligibility.get("raw_sha256"))
    except ValueError as exc:
        raise _fail("preflight", "INVALID_REQUEST", "profile eligibility raw_sha256 is invalid", EXIT_PREFLIGHT) from exc

    output = value.get("output")
    output_fields = {
        "raw_candidate_path", "submission_path", "prepared_invocation_path",
        "provenance_registry_path", "result_path",
    }
    if not isinstance(output, Mapping) or set(output) != output_fields:
        raise _fail("preflight", "INVALID_REQUEST", "output shape is invalid", EXIT_PREFLIGHT)
    normalized = [_validate_relative_path(output[name], f"output.{name}") for name in sorted(output_fields)]
    if len(set(normalized)) != len(normalized):
        raise _fail("preflight", "OUTPUT_PATH_COLLISION", "invocation/2 output paths must be pairwise distinct", EXIT_PREFLIGHT)
    inputs = {pack["locator"], profile["locator"], eligibility["locator"]}
    if inputs & set(normalized):
        raise _fail("preflight", "OUTPUT_PATH_COLLISION", "an output path collides with a sealed input path", EXIT_PREFLIGHT)


def _verify_runtime() -> Mapping[str, Any]:
    actual = {
        "implementation": sys.implementation.name,
        "major": sys.version_info.major,
        "minor": sys.version_info.minor,
        "micro": sys.version_info.micro,
        "cache_tag": sys.implementation.cache_tag,
    }
    if actual != _EXPECTED_RUNTIME:
        raise _fail(
            "preflight",
            "RENDERER_RUNTIME_INCOMPATIBLE",
            "invocation/2 requires exact CPython 3.12.0 / cpython-312",
            EXIT_PREFLIGHT,
        )
    return actual


def _validate_manifest_rel_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError(f"{label} path is invalid")
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")) or str(p) != value:
        raise ValueError(f"{label} path is invalid")
    return value


def _package_identity_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "contract": manifest["contract"],
        "version": manifest["version"],
        "source_commit": manifest["source_commit"],
        "compatibility": manifest["compatibility"],
        "managed_roots": sorted(manifest["managed_roots"]),
        "files": sorted(
            [
                {"path": item["path"], "mode": item["mode"], "sha256": item["sha256"]}
                for item in manifest["files"]
            ],
            key=lambda item: item["path"],
        ),
    }


def _validate_installed_package(installed_root: Path) -> tuple[Mapping[str, Any], str]:
    root = installed_root.resolve(strict=True)
    manifest_path = root / MANIFEST_RELATIVE_PATH
    try:
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise OSError("manifest is not a regular file")
        manifest = _strict_json(manifest_path.read_bytes())
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "installed package manifest is missing or invalid", EXIT_PREFLIGHT) from exc
    if not isinstance(manifest, Mapping):
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "installed package manifest must be an object", EXIT_PREFLIGHT)
    required = {"contract", "version", "source_commit", "content_identity", "transport_sha256", "compatibility", "managed_roots", "files"}
    if set(manifest) - (required | {"attestation"}) or not required.issubset(manifest):
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "installed package manifest fields are invalid", EXIT_PREFLIGHT)
    if manifest.get("contract") != PACKAGE_MANIFEST_CONTRACT:
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "unsupported installed package manifest contract", EXIT_PREFLIGHT)
    roots = manifest.get("managed_roots")
    files = manifest.get("files")
    if not isinstance(roots, list) or not roots or roots != sorted(roots) or len(roots) != len(set(roots)):
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "managed_roots are invalid", EXIT_PREFLIGHT)
    if not isinstance(files, list) or not files:
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "installed package file inventory is invalid", EXIT_PREFLIGHT)
    try:
        normalized_roots = [_validate_manifest_rel_path(item, "managed_root") for item in roots]
    except ValueError as exc:
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", str(exc), EXIT_PREFLIGHT) from exc
    if len({item.casefold() for item in normalized_roots}) != len(normalized_roots):
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "managed roots contain a case-fold collision", EXIT_PREFLIGHT)

    inventory: dict[str, Mapping[str, Any]] = {}
    for item in files:
        if not isinstance(item, Mapping) or set(item) != {"path", "mode", "sha256"}:
            raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "installed package file record is invalid", EXIT_PREFLIGHT)
        try:
            path = _validate_manifest_rel_path(item.get("path"), "file")
        except ValueError as exc:
            raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", str(exc), EXIT_PREFLIGHT) from exc
        if path in inventory or not any(path == managed or path.startswith(managed + "/") for managed in normalized_roots):
            raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "installed package inventory is duplicated or outside managed roots", EXIT_PREFLIGHT)
        if item.get("mode") not in {"0644", "0755"} or not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in item["sha256"]):
            raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", f"invalid package inventory record: {path}", EXIT_PREFLIGHT)
        inventory[path] = item

    missing_required = sorted(_REQUIRED_PACKAGE_FILES - set(inventory))
    if missing_required:
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", f"installed package lacks G4 behavior-bearing files: {missing_required}", EXIT_PREFLIGHT)

    try:
        expected_identity = _sha256(_canonical_json_bytes(_package_identity_payload(manifest)))
        stored_identity = _normalized_sha256(manifest.get("content_identity"))
    except (KeyError, TypeError, ValueError) as exc:
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "installed package content identity is invalid", EXIT_PREFLIGHT) from exc
    if stored_identity != expected_identity:
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "installed package content identity does not match manifest", EXIT_PREFLIGHT)

    for path, item in inventory.items():
        file_path = root.joinpath(*PurePosixPath(path).parts)
        try:
            if file_path.is_symlink() or not file_path.is_file():
                raise OSError("not a regular file")
            raw = file_path.read_bytes()
            mode = f"{stat.S_IMODE(file_path.stat().st_mode):04o}"
        except OSError as exc:
            raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", f"installed package file is missing or unsafe: {path}", EXIT_PREFLIGHT) from exc
        if hashlib.sha256(raw).hexdigest() != item["sha256"] or mode != item["mode"]:
            raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", f"installed package file identity mismatch: {path}", EXIT_PREFLIGHT)

    actual_paths: set[str] = set()
    for managed in normalized_roots:
        managed_path = root.joinpath(*PurePosixPath(managed).parts)
        if not managed_path.exists():
            raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", f"managed root is missing: {managed}", EXIT_PREFLIGHT)
        for item in managed_path.rglob("*"):
            if not item.is_file() or item.is_symlink():
                continue
            if any(part in _IGNORED_GENERATED_DIRS for part in item.parts) or item.suffix in _IGNORED_GENERATED_SUFFIXES:
                continue
            actual_paths.add(item.relative_to(root).as_posix())
    if actual_paths != set(inventory):
        raise _fail("preflight", "PACKAGE_CLOSURE_INCOMPLETE", "installed package file set differs from manifest closure", EXIT_PREFLIGHT)
    return manifest, stored_identity


def _validate_pack(raw: bytes, request_ref: Mapping[str, Any]) -> Mapping[str, Any]:
    if _sha256(raw) != request_ref["raw_sha256"]:
        raise _fail("preflight", "CONTEXT_PACK_DIGEST_MISMATCH", "context pack raw bytes do not match invocation/2", EXIT_PREFLIGHT)
    pack = _load_strict_json(raw, "context pack", "UNSUPPORTED_CONTEXT_PACK")
    if pack.get("contract") != PACK_CONTRACT:
        raise _fail("preflight", "UNSUPPORTED_CONTEXT_PACK", f"expected {PACK_CONTRACT}", EXIT_PREFLIGHT)
    identity = pack.get("identity")
    try:
        actual_identity = _normalized_sha256(identity.get("pack_identity_sha256") if isinstance(identity, Mapping) else None)
    except ValueError as exc:
        raise _fail("preflight", "CONTEXT_PACK_IDENTITY_MISMATCH", "context pack identity is invalid", EXIT_PREFLIGHT) from exc
    if actual_identity != request_ref["pack_identity_sha256"]:
        raise _fail("preflight", "CONTEXT_PACK_IDENTITY_MISMATCH", "context pack identity does not match invocation/2", EXIT_PREFLIGHT)
    return pack


def _validate_renderer_profile(raw: bytes, request_ref: Mapping[str, Any], pack: Mapping[str, Any], actual_binding: Mapping[str, Any]) -> Mapping[str, Any]:
    if _sha256(raw) != request_ref["raw_sha256"]:
        raise _fail("preflight", "RENDERER_PROFILE_DIGEST_MISMATCH", "renderer profile raw bytes do not match invocation/2", EXIT_PREFLIGHT)
    profile = _load_strict_json(raw, "renderer profile", "UNSUPPORTED_RENDERER_PROFILE")
    if profile.get("contract") != RENDERER_PROFILE_CONTRACT:
        raise _fail("preflight", "UNSUPPORTED_RENDERER_PROFILE", f"expected {RENDERER_PROFILE_CONTRACT}", EXIT_PREFLIGHT)
    if profile.get("profile_id") != request_ref["profile_id"] or profile.get("profile_version") != request_ref["profile_version"]:
        raise _fail("preflight", "UNSUPPORTED_RENDERER_PROFILE", "renderer profile identity does not match invocation/2", EXIT_PREFLIGHT)
    if profile.get("pack_profile") != pack.get("profile"):
        raise _fail("preflight", "RENDERER_PROFILE_PACK_MISMATCH", "renderer profile does not bind the exact sealed pack profile", EXIT_PREFLIGHT)
    try:
        renderer.compare_execution_binding(profile.get("renderer_execution_binding"), actual_binding)
    except Exception as exc:
        raise _fail("activation", "TOOLCHAIN_IDENTITY_MISMATCH", "renderer execution binding does not match the closed P9 bundle", EXIT_ACTIVATION) from exc
    return profile


def _validate_eligibility(raw: bytes, request_ref: Mapping[str, Any], pack: Mapping[str, Any]) -> tuple[Mapping[str, Any], str]:
    if _sha256(raw) != request_ref["raw_sha256"]:
        raise _fail("preflight", "PROFILE_ELIGIBILITY_DIGEST_MISMATCH", "profile eligibility raw bytes do not match invocation/2", EXIT_PREFLIGHT)
    eligibility = _load_strict_json(raw, "profile eligibility", "PROFILE_ELIGIBILITY_REQUIRED")
    required = {"contract", "consumer", "profile", "policy_evidence", "decision"}
    if set(eligibility) - (required | {"reason_code"}) or not required.issubset(eligibility):
        raise _fail("preflight", "PROFILE_ELIGIBILITY_MISMATCH", "profile eligibility shape is invalid", EXIT_PREFLIGHT)
    if eligibility.get("contract") != ELIGIBILITY_CONTRACT:
        raise _fail("preflight", "PROFILE_ELIGIBILITY_MISMATCH", "unsupported profile eligibility contract", EXIT_PREFLIGHT)
    if eligibility.get("decision") != "eligible":
        raise _fail("preflight", "PROFILE_INELIGIBLE", "sealed context profile is not eligible", EXIT_PREFLIGHT)
    if eligibility.get("profile") != pack.get("profile"):
        raise _fail("preflight", "PROFILE_ELIGIBILITY_MISMATCH", "eligibility profile does not match sealed pack profile", EXIT_PREFLIGHT)
    consumer = eligibility.get("consumer")
    evidence = eligibility.get("policy_evidence")
    if not isinstance(consumer, Mapping) or set(consumer) != {"consumer_contract", "consumer_id", "immutable_policy_snapshot_id"}:
        raise _fail("preflight", "PROFILE_ELIGIBILITY_MISMATCH", "eligibility consumer binding is invalid", EXIT_PREFLIGHT)
    if not isinstance(evidence, Mapping) or set(evidence) != {"contract", "immutable_snapshot_id", "raw_sha256"}:
        raise _fail("preflight", "PROFILE_ELIGIBILITY_MISMATCH", "eligibility policy evidence binding is invalid", EXIT_PREFLIGHT)
    try:
        _normalized_sha256(evidence.get("raw_sha256"))
    except ValueError as exc:
        raise _fail("preflight", "PROFILE_ELIGIBILITY_MISMATCH", "eligibility policy digest is invalid", EXIT_PREFLIGHT) from exc
    summary = pack.get("eligibility")
    expected_summary = {
        "consumer_contract": consumer.get("consumer_contract"),
        "consumer_id": consumer.get("consumer_id"),
        "policy_evidence_snapshot_id": evidence.get("immutable_snapshot_id"),
        "decision": "eligible",
    }
    if summary != expected_summary:
        raise _fail("preflight", "PROFILE_ELIGIBILITY_MISMATCH", "sealed pack eligibility summary does not match exact eligibility artifact", EXIT_PREFLIGHT)
    return eligibility, _domain_identity(_ELIGIBILITY_DOMAIN, eligibility)


def _persist_exact(raw: bytes, target: Path) -> PersistenceResult:
    try:
        return persist_immutable_artifact(
            raw,
            output_root=target.parent,
            relative_path=target.name,
            prohibited_roots=[],
        )
    except ImmutableOutputCollisionError as exc:
        raise _fail("persistence", "IMMUTABLE_OUTPUT_COLLISION", f"immutable output collision: {target.name}", EXIT_PERSISTENCE) from exc
    except PersistenceBoundaryError as exc:
        raise _fail("persistence", "IMMUTABLE_OUTPUT_COLLISION", f"immutable persistence boundary rejected output: {target.name}", EXIT_PERSISTENCE) from exc


def _read_installed_artifact(installed_root: Path, relative: str, label: str) -> bytes:
    path = installed_root.joinpath(*PurePosixPath(relative).parts)
    try:
        if path.is_symlink() or not path.is_file():
            raise OSError("not a regular file")
        return path.read_bytes()
    except OSError as exc:
        raise _fail("preflight", "FRAMEWORK_INCOMPLETE", f"installed {label} is unavailable", EXIT_PREFLIGHT) from exc


def prepare_invocation_v2(
    request_raw: bytes,
    *,
    cwd: str | os.PathLike[str] | None = None,
    installed_root: str | os.PathLike[str] | None = None,
) -> PrepareResult:
    """Prepare exactly one invocation/2 without provider execution or ambient evidence lookup."""
    request = _load_strict_json(request_raw, "invocation request", "INVALID_REQUEST")
    _validate_request(request)
    invocation_id = request["invocation_id"]
    project_root = _project_root(Path(cwd or Path.cwd()), request["project_root"])
    runtime_abi = _verify_runtime()

    root = Path(installed_root) if installed_root is not None else Path(__file__).resolve().parents[1]
    try:
        root = root.resolve(strict=True)
    except FileNotFoundError as exc:
        raise _fail("preflight", "FRAMEWORK_INCOMPLETE", "installed package root is missing", EXIT_PREFLIGHT) from exc
    _, package_content_identity = _validate_installed_package(root)

    context = request["context"]
    pack_path = _input_file(project_root, context["pack"]["locator"], "context.pack.locator", "CONTEXT_PACK_UNRESOLVED")
    profile_path = _input_file(project_root, context["renderer_profile"]["locator"], "context.renderer_profile.locator", "RENDERER_PROFILE_UNRESOLVED")
    eligibility_path = _input_file(project_root, context["profile_eligibility"]["locator"], "context.profile_eligibility.locator", "PROFILE_ELIGIBILITY_REQUIRED")

    pack_raw = pack_path.read_bytes()
    profile_raw = profile_path.read_bytes()
    eligibility_raw = eligibility_path.read_bytes()
    pack = _validate_pack(pack_raw, context["pack"])

    try:
        actual_binding = renderer.derive_execution_binding()
    except Exception as exc:
        raise _fail("activation", "TOOLCHAIN_IDENTITY_MISMATCH", "closed P9 execution binding could not be derived", EXIT_ACTIVATION) from exc
    profile = _validate_renderer_profile(profile_raw, context["renderer_profile"], pack, actual_binding)
    eligibility, eligibility_identity = _validate_eligibility(eligibility_raw, context["profile_eligibility"], pack)

    rendered = renderer.render_context_pack_v2(pack, profile_raw, profile)
    if not rendered.ok:
        failure = rendered.failure or {}
        code = failure.get("code", "TOOLCHAIN_IDENTITY_MISMATCH")
        if code not in {"TOOLCHAIN_IDENTITY_MISMATCH", "RENDER_LIMIT_EXCEEDED"}:
            code = "TOOLCHAIN_IDENTITY_MISMATCH"
        diagnostics = failure.get("diagnostics")
        detail = diagnostics[0] if isinstance(diagnostics, list) and diagnostics else "closed P9 rendering failed"
        raise _fail("activation", code, detail, EXIT_ACTIVATION)

    registry_result = provenance_bridge.derive_provenance_registry(pack, rendered.activation)
    if not registry_result.ok:
        failure = registry_result.failure or {}
        code = failure.get("code", "PROVENANCE_BRIDGE_INVALID")
        if code not in {"PROVENANCE_BRIDGE_INVALID", "PROVENANCE_SOURCE_COLLISION"}:
            code = "PROVENANCE_BRIDGE_INVALID"
        diagnostics = failure.get("diagnostics")
        detail = diagnostics[0] if isinstance(diagnostics, list) and diagnostics else "closed G3 provenance derivation failed"
        raise _fail("activation", code, detail, EXIT_ACTIVATION)

    directive_raw = _read_installed_artifact(root, DIRECTIVE_RELATIVE_PATH, "Distiller directive")
    validator_raw = _read_installed_artifact(root, VALIDATOR_RELATIVE_PATH, "RGP validator")
    try:
        directive_text = directive_raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise _fail("preflight", "FRAMEWORK_INCOMPLETE", "installed Distiller directive is not UTF-8", EXIT_PREFLIGHT) from exc
    directive_sha = _sha256(directive_raw)
    validator_sha = _sha256(validator_raw)

    activation_bundle: dict[str, Any] = {
        "contract": ACTIVATION_BUNDLE_CONTRACT,
        "invocation_id": invocation_id,
        "directive": {
            "path": DIRECTIVE_BUNDLE_PATH,
            "sha256": directive_sha,
            "encoding": "utf-8",
            "content": directive_text,
        },
        "instruction": ACTIVATION_INSTRUCTION,
        "rendered_activation": deepcopy(rendered.activation),
        "provenance_registry": deepcopy(registry_result.registry),
    }
    activation_bundle["identity"] = {
        "activation_bundle_sha256": _domain_identity(_ACTIVATION_BUNDLE_DOMAIN, activation_bundle)
    }
    activation_bundle_raw = renderer._jcs(activation_bundle)

    outputs = request["output"]
    registry_target = _output_target(project_root, outputs["provenance_registry_path"], "output.provenance_registry_path")
    prepared_target = _output_target(project_root, outputs["prepared_invocation_path"], "output.prepared_invocation_path")
    # Validate all remaining output destinations even though G4 must not write them.
    for name in ("raw_candidate_path", "submission_path", "result_path"):
        _output_target(project_root, outputs[name], f"output.{name}")

    registry_persistence = provenance_bridge.persist_provenance_registry(
        registry_result.serialized_registry,
        output_root=registry_target.parent,
        relative_path=registry_target.name,
        prohibited_roots=[],
    )

    runtime_record = {**runtime_abi, "binding_scheme": BINDING_SCHEME}
    prepared: dict[str, Any] = {
        "contract": PREPARED_INVOCATION_CONTRACT,
        "invocation": {
            "contract": INVOCATION_CONTRACT,
            "invocation_id": invocation_id,
            "request_sha256": _domain_identity(_REQUEST_DOMAIN, request),
        },
        "context_pack": deepcopy(context["pack"]),
        "renderer_profile": deepcopy(context["renderer_profile"]),
        "profile_eligibility": {
            "contract": ELIGIBILITY_CONTRACT,
            "locator": context["profile_eligibility"]["locator"],
            "raw_sha256": context["profile_eligibility"]["raw_sha256"],
            "decision": "eligible",
            "decision_identity_sha256": eligibility_identity,
        },
        "installed_package": {"content_identity": package_content_identity},
        "distiller_directive": {"sha256": directive_sha},
        "rgp_validator": {"contract": RGP_VALIDATOR_CONTRACT, "sha256": validator_sha},
        "provenance_registry": {
            "locator": outputs["provenance_registry_path"],
            "raw_sha256": registry_result.raw_sha256,
            "registry_sha256": registry_result.registry["identity"]["registry_sha256"],
        },
        "rendered_activation": {
            "raw_sha256": rendered.serialized_activation_sha256,
            "activation_identity_sha256": rendered.activation["identity"]["activation_identity_sha256"],
        },
        "renderer_execution_binding": deepcopy(actual_binding),
        "runtime_abi": runtime_record,
        "activation_bundle": {
            "contract": ACTIVATION_BUNDLE_CONTRACT,
            "raw_sha256": _sha256(activation_bundle_raw),
            "identity_sha256": activation_bundle["identity"]["activation_bundle_sha256"],
        },
        "model_transport": {
            "contract": MODEL_TRANSPORT_CONTRACT,
            "adapter_id": REFERENCE_TRANSPORT_ADAPTER_ID,
            "adapter_content_identity": package_content_identity,
        },
    }
    prepared["identity"] = {
        "prepared_invocation_sha256": _domain_identity(_PREPARED_INVOCATION_DOMAIN, prepared)
    }
    prepared_raw = renderer._jcs(prepared)
    prepared_persistence = _persist_exact(prepared_raw, prepared_target)

    return PrepareResult(
        invocation_id=invocation_id,
        activation_bundle=activation_bundle,
        serialized_activation_bundle=activation_bundle_raw,
        prepared_invocation=prepared,
        serialized_prepared_invocation=prepared_raw,
        provenance_registry=registry_result.registry,
        prepared_persistence=prepared_persistence,
        registry_persistence=registry_persistence,
    )


def read_request_contract(path: str | os.PathLike[str]) -> str | None:
    """Read only enough request structure for explicit /1 versus /2 dispatch."""
    try:
        raw = Path(path).read_bytes()
        value = _strict_json(raw)
    except (OSError, UnicodeError, ValueError, TypeError):
        return None
    return value.get("contract") if isinstance(value, Mapping) else None
