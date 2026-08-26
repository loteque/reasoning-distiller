"""P10-G6 deterministic finalization for sealed-context production invocations.

This module consumes only the invocation/2 request metadata, the exact persisted
prepared invocation and provenance registry produced by G4, the exact G5
transport receipt, the provider's raw model bytes, and the installed package
behavior needed to validate the candidate. It never reopens the sealed pack,
renderer profile, eligibility artifact, original project evidence, canonical
state, or ambient project context.

It preserves provider bytes before parse or validation, emits the existing
ordinary RGP candidate submission unchanged in semantics, persists the
invocation-result/2 companion links, and stops before reconciliation, admission,
canonical mutation, or role/authority/activation mutation.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

from . import model_transport
from . import prepare_integration as prepare
from . import provenance_bridge
from . import renderer
from .pems_projection import _strict_json
from .persistence_adapter import (
    ImmutableOutputCollisionError,
    PersistenceBoundaryError,
    PersistenceResult,
    persist_immutable_artifact,
)

RESULT_CONTRACT = "reasoning-distiller-invocation-result/2"
RGP_VERSION = "rgp/1"
EXIT_INTERNAL = 1
EXIT_PREFLIGHT = 2
EXIT_ACTIVATION = 3
EXIT_PARSE = 4
EXIT_VALIDATION = 5
EXIT_PERSISTENCE = 6


class FinalizeFailure(ValueError):
    """One frozen invocation/2 finalization failure."""

    def __init__(
        self,
        stage: str,
        reason_code: str,
        detail: str,
        exit_code: int,
    ) -> None:
        super().__init__(detail)
        self.stage = stage
        self.reason_code = reason_code
        self.detail = detail
        self.exit_code = exit_code


@dataclass(frozen=True)
class FinalizeResult:
    invocation_id: str
    result: Mapping[str, Any]
    serialized_result: bytes
    submission: Mapping[str, Any]
    serialized_submission: bytes
    raw_persistence: PersistenceResult
    submission_persistence: PersistenceResult
    result_persistence: PersistenceResult


def _fail(
    stage: str, reason_code: str, detail: str, exit_code: int
) -> FinalizeFailure:
    return FinalizeFailure(stage, reason_code, detail, exit_code)


def failure_result(
    invocation_id: str,
    failure: FinalizeFailure,
    *,
    raw_candidate: Mapping[str, str] | None = None,
    prepared_invocation: Mapping[str, str] | None = None,
    provenance_registry: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "invocation_id": (
            invocation_id if prepare._valid_invocation_id(invocation_id) else "unknown"
        ),
        "status": "FAIL",
        "stage": failure.stage,
        "reason_code": failure.reason_code,
        "detail": failure.detail,
    }
    if raw_candidate is not None:
        value["raw_candidate"] = dict(raw_candidate)
    if prepared_invocation is not None:
        value["prepared_invocation"] = dict(prepared_invocation)
    if provenance_registry is not None:
        value["provenance_registry"] = dict(provenance_registry)
    return value


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _semantic_sha256(value: object) -> str:
    """Hash canonical artifact semantics for result-link identity_sha256."""
    return _sha256(renderer._jcs(value))


def _canonical_submission_bytes(value: object) -> bytes:
    # Preserve the existing ordinary RGP Submission Protocol serialization.
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        + b"\n"
    )


def _persist_exact(raw: bytes, target: Path) -> PersistenceResult:
    try:
        return persist_immutable_artifact(
            raw,
            output_root=target.parent,
            relative_path=target.name,
            prohibited_roots=[],
        )
    except (ImmutableOutputCollisionError, PersistenceBoundaryError) as exc:
        raise _fail(
            "persistence",
            "IMMUTABLE_OUTPUT_COLLISION",
            f"immutable output collision: {target.name}",
            EXIT_PERSISTENCE,
        ) from exc


def _read_exact(path: Path, label: str, reason_code: str) -> bytes:
    try:
        if path.is_symlink() or not path.is_file():
            raise OSError("not a regular file")
        return path.read_bytes()
    except OSError as exc:
        raise _fail(
            "validation",
            reason_code,
            f"{label} is unavailable: {path.name}",
            EXIT_VALIDATION,
        ) from exc


def _load_request(request_raw: bytes) -> dict[str, Any]:
    try:
        value = _strict_json(request_raw)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise _fail(
            "preflight",
            "INVALID_REQUEST",
            "invocation request must be strict UTF-8 JSON",
            EXIT_PREFLIGHT,
        ) from exc
    if not isinstance(value, dict):
        raise _fail(
            "preflight",
            "INVALID_REQUEST",
            "invocation request must be a JSON object",
            EXIT_PREFLIGHT,
        )
    try:
        prepare._validate_request(value)
    except prepare.PrepareFailure as exc:
        raise _fail(exc.stage, exc.reason_code, exc.detail, exc.exit_code) from exc
    return value


def _load_prepared(prepared_raw: bytes) -> dict[str, Any]:
    try:
        parsed = _strict_json(prepared_raw)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise _fail(
            "validation",
            "PREPARED_INVOCATION_MISMATCH",
            "prepared invocation must be strict UTF-8 JSON",
            EXIT_VALIDATION,
        ) from exc
    if not isinstance(parsed, dict) or renderer._jcs(parsed) != prepared_raw:
        raise _fail(
            "validation",
            "PREPARED_INVOCATION_MISMATCH",
            "prepared invocation is not exact canonical JCS bytes",
            EXIT_VALIDATION,
        )
    identity = parsed.get("identity")
    expected = (
        identity.get("prepared_invocation_sha256")
        if isinstance(identity, Mapping)
        else None
    )
    try:
        verified = model_transport._verify_prepared(prepared_raw, expected)
    except model_transport.TransportFailure as exc:
        reason = (
            "MODEL_TRANSPORT_NONCONFORMING"
            if exc.reason_code == "MODEL_TRANSPORT_NONCONFORMING"
            else "PREPARED_INVOCATION_MISMATCH"
        )
        stage = "activation" if reason == "MODEL_TRANSPORT_NONCONFORMING" else "validation"
        code = EXIT_ACTIVATION if stage == "activation" else EXIT_VALIDATION
        raise _fail(stage, reason, exc.detail, code) from exc
    return verified


def _verify_request_binding(
    request: Mapping[str, Any],
    prepared: Mapping[str, Any],
) -> None:
    invocation = prepared["invocation"]
    if invocation["invocation_id"] != request["invocation_id"]:
        raise _fail(
            "validation",
            "PREPARED_INVOCATION_MISMATCH",
            "prepared invocation ID differs from invocation/2",
            EXIT_VALIDATION,
        )
    expected_request_identity = prepare._domain_identity(
        prepare._REQUEST_DOMAIN, request
    )
    if invocation["request_sha256"] != expected_request_identity:
        raise _fail(
            "validation",
            "SEALED_INPUT_MISMATCH",
            "invocation/2 metadata differs from the request frozen at prepare",
            EXIT_VALIDATION,
        )

    context = request["context"]
    if prepared.get("context_pack") != context["pack"]:
        raise _fail(
            "validation",
            "SEALED_INPUT_MISMATCH",
            "context-pack binding differs from the prepared invocation",
            EXIT_VALIDATION,
        )
    if prepared.get("renderer_profile") != context["renderer_profile"]:
        raise _fail(
            "validation",
            "SEALED_INPUT_MISMATCH",
            "renderer-profile binding differs from the prepared invocation",
            EXIT_VALIDATION,
        )
    eligibility = prepared.get("profile_eligibility")
    expected_eligibility = context["profile_eligibility"]
    if (
        not isinstance(eligibility, Mapping)
        or eligibility.get("contract") != expected_eligibility["contract"]
        or eligibility.get("locator") != expected_eligibility["locator"]
        or eligibility.get("raw_sha256") != expected_eligibility["raw_sha256"]
        or eligibility.get("decision") != "eligible"
    ):
        raise _fail(
            "validation",
            "SEALED_INPUT_MISMATCH",
            "profile-eligibility binding differs from the prepared invocation",
            EXIT_VALIDATION,
        )


def _verify_registry(
    registry_raw: bytes,
    prepared: Mapping[str, Any],
    request: Mapping[str, Any],
) -> dict[str, Any]:
    binding = prepared["provenance_registry"]
    if binding["locator"] != request["output"]["provenance_registry_path"]:
        raise _fail(
            "validation",
            "PREPARED_INVOCATION_MISMATCH",
            "prepared provenance-registry locator differs from invocation/2",
            EXIT_VALIDATION,
        )
    if _sha256(registry_raw) != binding["raw_sha256"]:
        raise _fail(
            "validation",
            "PROVENANCE_REGISTRY_MISMATCH",
            "persisted provenance registry bytes differ from prepared invocation",
            EXIT_VALIDATION,
        )
    try:
        value = provenance_bridge._validate_registry_bytes(registry_raw)
    except Exception as exc:
        raise _fail(
            "validation",
            "PROVENANCE_REGISTRY_MISMATCH",
            "persisted provenance registry is invalid",
            EXIT_VALIDATION,
        ) from exc
    identity = value["identity"]["registry_sha256"]
    if identity != binding["registry_sha256"]:
        raise _fail(
            "validation",
            "PROVENANCE_REGISTRY_MISMATCH",
            "persisted provenance registry identity differs from prepared invocation",
            EXIT_VALIDATION,
        )
    return dict(value)


def _verify_transport_receipt(
    transport_raw: bytes,
    prepared: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        value = _strict_json(transport_raw)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "model-transport receipt must be strict UTF-8 JSON",
            EXIT_ACTIVATION,
        ) from exc
    expected_keys = {
        "contract",
        "prepared_invocation_sha256",
        "activation_bundle_sha256",
        "adapter",
        "mapping",
        "threat_model",
        "identity",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "model-transport receipt shape is invalid",
            EXIT_ACTIVATION,
        )
    if renderer._jcs(value) != transport_raw:
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "model-transport receipt is not exact canonical JCS bytes",
            EXIT_ACTIVATION,
        )
    if value.get("contract") != model_transport.MODEL_TRANSPORT_CONTRACT:
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "model-transport receipt contract is unsupported",
            EXIT_ACTIVATION,
        )
    expected_prepared = prepared["identity"]["prepared_invocation_sha256"]
    expected_activation = prepared["activation_bundle"]["identity_sha256"]
    adapter = value.get("adapter")
    if (
        value.get("prepared_invocation_sha256") != expected_prepared
        or value.get("activation_bundle_sha256") != expected_activation
        or not isinstance(adapter, Mapping)
        or set(adapter) != {"adapter_id", "content_identity"}
        or adapter.get("adapter_id") != prepared["model_transport"]["adapter_id"]
        or adapter.get("content_identity")
        != prepared["model_transport"]["adapter_content_identity"]
    ):
        raise _fail(
            "activation",
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "model-transport receipt is bound to a different prepared invocation",
            EXIT_ACTIVATION,
        )
    if value.get("mapping") != model_transport.MAPPING:
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "model-transport mapping differs from the frozen provider-neutral mapping",
            EXIT_ACTIVATION,
        )
    if value.get("threat_model") != model_transport.THREAT_MODEL:
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "model-transport threat boundary differs from the frozen G5 contract",
            EXIT_ACTIVATION,
        )
    identity = value.get("identity")
    if not isinstance(identity, Mapping) or set(identity) != {"transport_sha256"}:
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "model-transport receipt identity is invalid",
            EXIT_ACTIVATION,
        )
    preimage = deepcopy(value)
    preimage.pop("identity")
    expected_identity = model_transport._domain_identity(
        model_transport.TRANSPORT_DOMAIN, preimage
    )
    if identity.get("transport_sha256") != expected_identity:
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "model-transport receipt identity does not match its frozen semantics",
            EXIT_ACTIVATION,
        )
    return value


def _verify_toolchain(
    installed_root: Path,
    prepared: Mapping[str, Any],
) -> None:
    expected_runtime = {
        "implementation": sys.implementation.name,
        "major": sys.version_info.major,
        "minor": sys.version_info.minor,
        "micro": sys.version_info.micro,
        "cache_tag": sys.implementation.cache_tag,
        "binding_scheme": prepare.BINDING_SCHEME,
    }
    if expected_runtime != prepared["runtime_abi"]:
        raise _fail(
            "validation",
            "PREPARED_INVOCATION_MISMATCH",
            "finalize runtime differs from the exact prepared runtime ABI",
            EXIT_VALIDATION,
        )

    directive_raw = _read_exact(
        installed_root / prepare.DIRECTIVE_RELATIVE_PATH,
        "installed Distiller directive",
        "DISTILLER_DIRECTIVE_MISMATCH",
    )
    if _sha256(directive_raw) != prepared["distiller_directive"]["sha256"]:
        raise _fail(
            "validation",
            "DISTILLER_DIRECTIVE_MISMATCH",
            "installed Distiller directive differs from prepared invocation",
            EXIT_VALIDATION,
        )

    validator_binding = prepared.get("rgp_validator")
    if (
        not isinstance(validator_binding, Mapping)
        or set(validator_binding) != {"contract", "sha256"}
        or validator_binding.get("contract") != prepare.RGP_VALIDATOR_CONTRACT
    ):
        raise _fail(
            "validation",
            "PREPARED_INVOCATION_MISMATCH",
            "prepared RGP validator binding is invalid",
            EXIT_VALIDATION,
        )
    validator_raw = _read_exact(
        installed_root / prepare.VALIDATOR_RELATIVE_PATH,
        "installed RGP validator",
        "RGP_VALIDATOR_MISMATCH",
    )
    if _sha256(validator_raw) != validator_binding["sha256"]:
        raise _fail(
            "validation",
            "RGP_VALIDATOR_MISMATCH",
            "installed RGP validator differs from prepared invocation",
            EXIT_VALIDATION,
        )

    try:
        _, current_identity = prepare._validate_installed_package(installed_root)
    except prepare.PrepareFailure as exc:
        raise _fail(
            "validation",
            "PACKAGE_IDENTITY_MISMATCH",
            f"installed package no longer matches prepared closure: {exc.detail}",
            EXIT_VALIDATION,
        ) from exc
    if (
        current_identity != prepared["installed_package"]["content_identity"]
        or prepared["model_transport"]["adapter_content_identity"] != current_identity
    ):
        raise _fail(
            "validation",
            "PACKAGE_IDENTITY_MISMATCH",
            "installed package identity differs from prepared invocation",
            EXIT_VALIDATION,
        )


def _load_validator(installed_root: Path):
    path = installed_root / prepare.VALIDATOR_RELATIVE_PATH
    spec = importlib.util.spec_from_file_location("rd_p10_g6_rgp_validator", path)
    if spec is None or spec.loader is None:
        raise _fail(
            "validation",
            "VALIDATOR_LOAD_FAILED",
            "cannot load exact installed RGP validator",
            EXIT_VALIDATION,
        )
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise _fail(
            "validation",
            "VALIDATOR_LOAD_FAILED",
            "exact installed RGP validator failed to load",
            EXIT_VALIDATION,
        ) from exc
    return module


def _referenced_provenance(graph: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for record in graph.get("records", []) or []:
        if not isinstance(record, Mapping):
            continue
        provenance = record.get("provenance")
        if isinstance(provenance, Mapping):
            for values in provenance.values():
                if isinstance(values, list):
                    refs.update(item for item in values if isinstance(item, str))
    for relation in graph.get("relations", []) or []:
        if not isinstance(relation, Mapping):
            continue
        provenance = relation.get("provenance")
        if isinstance(provenance, Mapping):
            for values in provenance.values():
                if isinstance(values, list):
                    refs.update(item for item in values if isinstance(item, str))
    return refs


def _submission_id(invocation_id: str, graph: Mapping[str, Any]) -> str:
    seed = (
        invocation_id.encode("utf-8")
        + b"\0"
        + json.dumps(
            graph,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )
    return "RGP-" + hashlib.sha256(seed).hexdigest()[:32].upper()


def _make_submission(
    request: Mapping[str, Any],
    graph: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "submission_id": _submission_id(request["invocation_id"], graph),
        "producer": {
            "role": "reasoning-distiller",
            "instance": request["invocation_id"],
        },
        "created_at": request["created_at"],
        "rgp_version": RGP_VERSION,
        "status": "candidate",
        "candidate_graph": deepcopy(graph),
        "validation": {
            "status": "passed",
            "validator": "rgp-validator/1",
            "validated_at": request["created_at"],
        },
    }


def finalize_invocation_v2(
    request_raw: bytes,
    raw_model_bytes: bytes,
    transport_binding_raw: bytes,
    *,
    cwd: str | os.PathLike[str] | None = None,
    installed_root: str | os.PathLike[str] | None = None,
) -> FinalizeResult:
    """Finalize one invocation/2 without reopening sealed project evidence."""
    if not isinstance(raw_model_bytes, bytes):
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "provider result must be exact raw bytes",
            EXIT_ACTIVATION,
        )
    if not isinstance(transport_binding_raw, bytes):
        raise _fail(
            "activation",
            "MODEL_TRANSPORT_NONCONFORMING",
            "model-transport receipt must be exact raw bytes",
            EXIT_ACTIVATION,
        )

    request = _load_request(request_raw)
    invocation_id = request["invocation_id"]
    project_root = prepare._project_root(Path(cwd or Path.cwd()), request["project_root"])
    outputs = request["output"]

    targets = {
        name: prepare._output_target(project_root, outputs[name], f"output.{name}")
        for name in (
            "raw_candidate_path",
            "submission_path",
            "prepared_invocation_path",
            "provenance_registry_path",
            "result_path",
        )
    }

    # Provider output exists at this boundary. Preserve it before any parse,
    # RGP, provenance, prepared-invocation, registry, or toolchain rejection.
    raw_persistence = _persist_exact(
        raw_model_bytes, targets["raw_candidate_path"]
    )

    prepared_raw = _read_exact(
        targets["prepared_invocation_path"],
        "prepared invocation",
        "PREPARED_INVOCATION_MISMATCH",
    )
    prepared = _load_prepared(prepared_raw)
    _verify_request_binding(request, prepared)
    _verify_transport_receipt(transport_binding_raw, prepared)

    registry_raw = _read_exact(
        targets["provenance_registry_path"],
        "provenance registry",
        "PROVENANCE_REGISTRY_MISMATCH",
    )
    registry = _verify_registry(registry_raw, prepared, request)

    root = (
        Path(installed_root)
        if installed_root is not None
        else Path(__file__).resolve().parents[1]
    )
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        raise _fail(
            "validation",
            "PACKAGE_IDENTITY_MISMATCH",
            "installed package root is unavailable",
            EXIT_VALIDATION,
        ) from exc
    _verify_toolchain(root, prepared)

    try:
        graph = _strict_json(raw_model_bytes)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise _fail(
            "parse",
            "RAW_CANDIDATE_PARSE_FAILED",
            "raw provider bytes are not strict UTF-8 JSON",
            EXIT_PARSE,
        ) from exc
    if not isinstance(graph, dict):
        raise _fail(
            "parse",
            "RAW_CANDIDATE_PARSE_FAILED",
            "raw provider JSON must be an RGP object",
            EXIT_PARSE,
        )

    validator = _load_validator(root)
    try:
        errors = validator.validate(graph)
    except Exception as exc:
        raise _fail(
            "validation",
            "RGP_VALIDATION_FAILED",
            "installed RGP validator failed while validating candidate",
            EXIT_VALIDATION,
        ) from exc
    if errors:
        raise _fail(
            "validation",
            "RGP_VALIDATION_FAILED",
            "; ".join(str(item) for item in errors),
            EXIT_VALIDATION,
        )

    registry_ids = {
        record["source_id"]
        for record in registry["sources"]
        if isinstance(record, Mapping) and isinstance(record.get("source_id"), str)
    }
    unknown = sorted(_referenced_provenance(graph) - registry_ids)
    if unknown:
        raise _fail(
            "validation",
            "UNRESOLVED_PROVENANCE",
            f"candidate references source ids absent from exact provenance registry: {unknown}",
            EXIT_VALIDATION,
        )

    submission = _make_submission(request, graph)
    submission_raw = _canonical_submission_bytes(submission)
    submission_persistence = _persist_exact(
        submission_raw, targets["submission_path"]
    )

    result: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "invocation_id": invocation_id,
        "status": "PASS",
        "raw_candidate": {
            "locator": outputs["raw_candidate_path"],
            "raw_sha256": _sha256(raw_model_bytes),
            "identity_sha256": _semantic_sha256(graph),
        },
        "submission": {
            "locator": outputs["submission_path"],
            "raw_sha256": _sha256(submission_raw),
            "identity_sha256": _semantic_sha256(submission),
        },
        "prepared_invocation": {
            "locator": outputs["prepared_invocation_path"],
            "raw_sha256": _sha256(prepared_raw),
            "identity_sha256": prepared["identity"]["prepared_invocation_sha256"],
        },
        "provenance_registry": {
            "locator": outputs["provenance_registry_path"],
            "raw_sha256": _sha256(registry_raw),
            "identity_sha256": registry["identity"]["registry_sha256"],
        },
    }
    result_raw = renderer._jcs(result)
    result_persistence = _persist_exact(result_raw, targets["result_path"])

    return FinalizeResult(
        invocation_id=invocation_id,
        result=result,
        serialized_result=result_raw,
        submission=submission,
        serialized_submission=submission_raw,
        raw_persistence=raw_persistence,
        submission_persistence=submission_persistence,
        result_persistence=result_persistence,
    )
