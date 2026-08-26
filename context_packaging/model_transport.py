"""P10-G5 provider-neutral model transport conformance and reference runner.

This module consumes only the exact G4 prepared invocation and activation bundle.
It proves the frozen ``reasoning-distiller-model-transport/1`` logical mapping,
constructs one package-owned reference-provider representation, and returns exact
provider bytes unchanged. It performs no finalization, parsing, RGP validation,
persistence, submission, reconciliation, admission, canonical mutation, or
role/authority/activation mutation.
"""
from __future__ import annotations

import base64
import binascii
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from . import prepare_integration as prepare
from . import renderer
from .pems_projection import _strict_json

MODEL_TRANSPORT_CONTRACT = "reasoning-distiller-model-transport/1"
REFERENCE_ADAPTER_ID = "reference"
TRANSPORT_DOMAIN = b"reasoning-distiller-model-transport/1\x00"
EXIT_ACTIVATION = 3

PLANE_ORDER = ("control", "knowledge", "operational_evidence")
MAPPING = {
    "directive_surface": "framework_instruction",
    "plane_order": list(PLANE_ORDER),
    "context_control_provider_authority": False,
    "instruction_like_promotion": False,
    "frame_order_preserved": True,
    "frame_payload_bytes_preserved": True,
    "provenance_mapping_preserved": True,
    "extra_project_context": False,
}
THREAT_MODEL = {
    "runner_assumption": "non-hostile/reference runner",
    "assurance_basis": "deterministic conformance testing",
    "hostile_provider_or_runner_attestation": "OUTSIDE_P10",
}

_PREPARED_KEYS = {
    "contract",
    "invocation",
    "context_pack",
    "renderer_profile",
    "profile_eligibility",
    "installed_package",
    "distiller_directive",
    "rgp_validator",
    "provenance_registry",
    "rendered_activation",
    "renderer_execution_binding",
    "runtime_abi",
    "activation_bundle",
    "model_transport",
    "identity",
}
_ACTIVATION_KEYS = {
    "contract",
    "invocation_id",
    "directive",
    "instruction",
    "rendered_activation",
    "provenance_registry",
    "identity",
}
_RENDERED_KEYS = {
    "contract",
    "renderer_profile",
    "renderer_execution_binding",
    "pack",
    "framing",
    "frames",
    "identity",
}
_REGISTRY_KEYS = {
    "contract",
    "pack_identity_sha256",
    "rendered_activation_identity_sha256",
    "sources",
    "occurrences",
    "identity",
}


class TransportFailure(ValueError):
    """One frozen G5 activation-bound transport failure."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.stage = "activation"
        self.reason_code = reason_code
        self.detail = detail
        self.exit_code = EXIT_ACTIVATION


@dataclass(frozen=True)
class TransportRunResult:
    transport_binding: Mapping[str, Any]
    serialized_transport_binding: bytes
    provider_request: Mapping[str, Any]
    raw_model_bytes: bytes


def _fail(code: str, detail: str) -> TransportFailure:
    return TransportFailure(code, detail)


def _sha256(raw: bytes) -> str:
    return prepare._sha256(raw)


def _domain_identity(domain: bytes, value: Mapping[str, Any]) -> str:
    return _sha256(domain + renderer._jcs(value))


def _load_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = _strict_json(raw)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            f"{label} must be strict UTF-8 JSON",
        ) from exc
    if not isinstance(value, dict):
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            f"{label} must be a JSON object",
        )
    return value


def _require_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            f"{label} has unknown or missing fields",
        )


def _sha_field(value: Any, label: str) -> str:
    try:
        return prepare._normalized_sha256(value)
    except ValueError as exc:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            f"{label} is not an exact SHA-256 identity",
        ) from exc


def _verify_prepared(
    prepared_raw: bytes,
    expected_prepared_invocation_sha256: str,
) -> dict[str, Any]:
    prepared = _load_object(prepared_raw, "prepared invocation")
    _require_keys(prepared, _PREPARED_KEYS, "prepared invocation")
    if prepared.get("contract") != prepare.PREPARED_INVOCATION_CONTRACT:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared invocation contract is unsupported",
        )

    identity = prepared.get("identity")
    if not isinstance(identity, Mapping) or set(identity) != {"prepared_invocation_sha256"}:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared invocation identity shape is invalid",
        )
    expected_identity = _sha_field(
        expected_prepared_invocation_sha256,
        "expected prepared invocation identity",
    )
    stored_identity = _sha_field(
        identity.get("prepared_invocation_sha256"),
        "prepared invocation identity",
    )
    identity_preimage = deepcopy(prepared)
    identity_preimage.pop("identity")
    calculated_identity = _domain_identity(prepare._PREPARED_INVOCATION_DOMAIN, identity_preimage)
    if stored_identity != calculated_identity or stored_identity != expected_identity:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared invocation does not match the exact runner-bound identity",
        )

    invocation = prepared.get("invocation")
    if (
        not isinstance(invocation, Mapping)
        or set(invocation) != {"contract", "invocation_id", "request_sha256"}
        or invocation.get("contract") != prepare.INVOCATION_CONTRACT
        or not prepare._valid_invocation_id(invocation.get("invocation_id"))
    ):
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared invocation invocation binding is invalid",
        )
    _sha_field(invocation.get("request_sha256"), "prepared request identity")

    package = prepared.get("installed_package")
    if not isinstance(package, Mapping) or set(package) != {"content_identity"}:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared installed-package binding is invalid",
        )
    _sha_field(package.get("content_identity"), "prepared package content identity")

    model_transport = prepared.get("model_transport")
    if (
        not isinstance(model_transport, Mapping)
        or set(model_transport) != {"contract", "adapter_id", "adapter_content_identity"}
        or model_transport.get("contract") != MODEL_TRANSPORT_CONTRACT
    ):
        raise _fail(
            "MODEL_TRANSPORT_NONCONFORMING",
            "prepared model-transport binding is invalid",
        )
    if model_transport.get("adapter_id") != REFERENCE_ADAPTER_ID:
        raise _fail(
            "MODEL_TRANSPORT_NONCONFORMING",
            f"unsupported provider adapter: {model_transport.get('adapter_id')!r}",
        )
    _sha_field(
        model_transport.get("adapter_content_identity"),
        "prepared transport-adapter identity",
    )

    activation = prepared.get("activation_bundle")
    if (
        not isinstance(activation, Mapping)
        or set(activation) != {"contract", "raw_sha256", "identity_sha256"}
        or activation.get("contract") != prepare.ACTIVATION_BUNDLE_CONTRACT
    ):
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared activation-bundle binding is invalid",
        )
    _sha_field(activation.get("raw_sha256"), "prepared activation-bundle raw digest")
    _sha_field(activation.get("identity_sha256"), "prepared activation-bundle identity")

    registry = prepared.get("provenance_registry")
    if not isinstance(registry, Mapping) or set(registry) != {"locator", "raw_sha256", "registry_sha256"}:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared provenance-registry binding is invalid",
        )
    _sha_field(registry.get("raw_sha256"), "prepared provenance-registry raw digest")
    _sha_field(registry.get("registry_sha256"), "prepared provenance-registry identity")

    rendered = prepared.get("rendered_activation")
    if not isinstance(rendered, Mapping) or set(rendered) != {"raw_sha256", "activation_identity_sha256"}:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared rendered-activation binding is invalid",
        )
    _sha_field(rendered.get("raw_sha256"), "prepared rendered-activation raw digest")
    _sha_field(rendered.get("activation_identity_sha256"), "prepared rendered-activation identity")

    directive = prepared.get("distiller_directive")
    if not isinstance(directive, Mapping) or set(directive) != {"sha256"}:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared Distiller directive binding is invalid",
        )
    _sha_field(directive.get("sha256"), "prepared Distiller directive digest")

    if prepared.get("runtime_abi") != {
        "implementation": "cpython",
        "major": 3,
        "minor": 12,
        "micro": 0,
        "cache_tag": "cpython-312",
        "binding_scheme": prepare.BINDING_SCHEME,
    }:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "prepared runtime ABI is outside the frozen P9/P10 tuple",
        )
    return prepared


def _verify_installed_package(
    prepared: Mapping[str, Any],
    installed_root: str | Path | None,
) -> tuple[Path, str]:
    root = Path(installed_root) if installed_root is not None else Path(__file__).resolve().parents[1]
    try:
        root = root.resolve(strict=True)
        _, current_identity = prepare._validate_installed_package(root)
    except (OSError, prepare.PrepareFailure) as exc:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "installed package no longer matches the prepared invocation",
        ) from exc

    prepared_identity = prepared["installed_package"]["content_identity"]
    adapter_identity = prepared["model_transport"]["adapter_content_identity"]
    if current_identity != prepared_identity or adapter_identity != prepared_identity:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "installed package or transport-adapter identity drifted after prepare",
        )
    return root, current_identity


def _verify_frame(frame: Any, expected_index: int) -> Mapping[str, Any]:
    if not isinstance(frame, Mapping):
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "rendered frame must be an object")
    if frame.get("frame_index") != expected_index or frame.get("encoding") != "base64":
        raise _fail(
            "MODEL_TRANSPORT_NONCONFORMING",
            "rendered frame order or encoding is not transport-conforming",
        )
    kind = frame.get("kind")
    expected_keys = {"frame_index", "kind", "encoding", "raw_sha256", "data"}
    if kind == "metadata":
        if expected_index != 0 or set(frame) != expected_keys:
            raise _fail("MODEL_TRANSPORT_NONCONFORMING", "metadata frame shape is invalid")
    elif kind == "plane_item":
        expected_keys |= {"plane", "item_index"}
        if set(frame) != expected_keys or frame.get("plane") not in PLANE_ORDER:
            raise _fail("MODEL_TRANSPORT_NONCONFORMING", "plane frame shape is invalid")
        if not isinstance(frame.get("item_index"), int) or frame["item_index"] < 0:
            raise _fail("MODEL_TRANSPORT_NONCONFORMING", "plane frame item index is invalid")
    else:
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "rendered frame kind is unsupported")

    data = frame.get("data")
    if not isinstance(data, str):
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "rendered frame payload is not base64 text")
    try:
        payload = base64.b64decode(data.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "rendered frame payload is invalid base64") from exc
    if _sha256(payload) != _sha_field(frame.get("raw_sha256"), "rendered frame payload digest"):
        raise _fail(
            "MODEL_TRANSPORT_NONCONFORMING",
            "rendered frame payload bytes do not match their frozen digest",
        )
    return frame


def _verify_activation_bundle(
    activation_bundle_raw: bytes,
    prepared: Mapping[str, Any],
) -> dict[str, Any]:
    if _sha256(activation_bundle_raw) != prepared["activation_bundle"]["raw_sha256"]:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "activation-bundle raw bytes do not match the prepared invocation",
        )
    bundle = _load_object(activation_bundle_raw, "activation bundle")
    _require_keys(bundle, _ACTIVATION_KEYS, "activation bundle")
    if bundle.get("contract") != prepare.ACTIVATION_BUNDLE_CONTRACT:
        raise _fail("RUNNER_PREPARED_INVOCATION_MISMATCH", "activation bundle contract is unsupported")
    if bundle.get("invocation_id") != prepared["invocation"]["invocation_id"]:
        raise _fail("RUNNER_PREPARED_INVOCATION_MISMATCH", "activation bundle invocation ID differs from prepared invocation")
    if bundle.get("instruction") != prepare.ACTIVATION_INSTRUCTION:
        raise _fail(
            "MODEL_TRANSPORT_NONCONFORMING",
            "activation instruction differs from the frozen framework instruction",
        )

    directive = bundle.get("directive")
    if (
        not isinstance(directive, Mapping)
        or set(directive) != {"path", "sha256", "encoding", "content"}
        or directive.get("path") != prepare.DIRECTIVE_BUNDLE_PATH
        or directive.get("encoding") != "utf-8"
        or not isinstance(directive.get("content"), str)
        or _sha256(directive["content"].encode("utf-8")) != directive.get("sha256")
        or directive.get("sha256") != prepared["distiller_directive"]["sha256"]
    ):
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "activation bundle directive differs from the prepared Distiller directive",
        )

    identity = bundle.get("identity")
    if not isinstance(identity, Mapping) or set(identity) != {"activation_bundle_sha256"}:
        raise _fail("RUNNER_PREPARED_INVOCATION_MISMATCH", "activation bundle identity shape is invalid")
    stored_identity = _sha_field(identity.get("activation_bundle_sha256"), "activation bundle identity")
    identity_preimage = deepcopy(bundle)
    identity_preimage.pop("identity")
    calculated_identity = _domain_identity(prepare._ACTIVATION_BUNDLE_DOMAIN, identity_preimage)
    if stored_identity != calculated_identity or stored_identity != prepared["activation_bundle"]["identity_sha256"]:
        raise _fail(
            "RUNNER_PREPARED_INVOCATION_MISMATCH",
            "activation bundle identity differs from the prepared invocation",
        )

    rendered = bundle.get("rendered_activation")
    if not isinstance(rendered, Mapping) or set(rendered) != _RENDERED_KEYS:
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "rendered activation shape is invalid")
    if rendered.get("contract") != renderer.RENDERED_ACTIVATION_CONTRACT_V2:
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "rendered activation contract is unsupported")
    framing = rendered.get("framing")
    if not isinstance(framing, Mapping) or framing.get("plane_order") != list(PLANE_ORDER):
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "rendered activation plane order is not preserved")
    frames = rendered.get("frames")
    if not isinstance(frames, list) or not frames:
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "rendered activation frames are missing")
    seen_plane_index = -1
    plane_keys: set[tuple[int, str, int]] = set()
    for expected_index, frame in enumerate(frames):
        verified = _verify_frame(frame, expected_index)
        if verified.get("kind") == "plane_item":
            plane = verified["plane"]
            plane_index = PLANE_ORDER.index(plane)
            if plane_index < seen_plane_index:
                raise _fail("MODEL_TRANSPORT_NONCONFORMING", "rendered frame plane order was flattened or reordered")
            seen_plane_index = plane_index
            plane_keys.add((verified["frame_index"], plane, verified["item_index"]))

    rendered_raw = renderer._jcs(rendered)
    if _sha256(rendered_raw) != prepared["rendered_activation"]["raw_sha256"]:
        raise _fail("RUNNER_PREPARED_INVOCATION_MISMATCH", "rendered activation raw bytes differ from prepared invocation")
    rendered_identity = rendered.get("identity")
    if (
        not isinstance(rendered_identity, Mapping)
        or rendered_identity.get("activation_identity_sha256") != prepared["rendered_activation"]["activation_identity_sha256"]
    ):
        raise _fail("RUNNER_PREPARED_INVOCATION_MISMATCH", "rendered activation identity differs from prepared invocation")

    registry = bundle.get("provenance_registry")
    if not isinstance(registry, Mapping) or set(registry) != _REGISTRY_KEYS:
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "provenance registry shape is invalid")
    registry_raw = renderer._jcs(registry)
    if _sha256(registry_raw) != prepared["provenance_registry"]["raw_sha256"]:
        raise _fail("RUNNER_PREPARED_INVOCATION_MISMATCH", "provenance registry raw bytes differ from prepared invocation")
    registry_identity = registry.get("identity")
    if (
        not isinstance(registry_identity, Mapping)
        or registry_identity.get("registry_sha256") != prepared["provenance_registry"]["registry_sha256"]
    ):
        raise _fail("RUNNER_PREPARED_INVOCATION_MISMATCH", "provenance registry identity differs from prepared invocation")
    if registry.get("rendered_activation_identity_sha256") != prepared["rendered_activation"]["activation_identity_sha256"]:
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "provenance registry no longer names the exact rendered activation")

    sources = registry.get("sources")
    occurrences = registry.get("occurrences")
    if not isinstance(sources, list) or not sources or not isinstance(occurrences, list):
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "provenance registry sources or occurrences are invalid")
    source_ids = {
        source.get("source_id")
        for source in sources
        if isinstance(source, Mapping) and isinstance(source.get("source_id"), str)
    }
    occurrence_keys: set[tuple[int, str, int]] = set()
    for occurrence in occurrences:
        if not isinstance(occurrence, Mapping) or set(occurrence) != {"pack_identity_sha256", "frame_index", "plane", "item_index", "source_id"}:
            raise _fail("MODEL_TRANSPORT_NONCONFORMING", "provenance occurrence shape is invalid")
        if occurrence.get("source_id") not in source_ids:
            raise _fail("MODEL_TRANSPORT_NONCONFORMING", "provenance occurrence refers to an unknown stable source")
        key = (occurrence.get("frame_index"), occurrence.get("plane"), occurrence.get("item_index"))
        if key in occurrence_keys:
            raise _fail("MODEL_TRANSPORT_NONCONFORMING", "provenance occurrence mapping is ambiguous")
        occurrence_keys.add(key)
    if occurrence_keys != plane_keys:
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "every model-visible plane frame must retain exactly one provenance mapping")
    return bundle


def build_transport_binding(
    prepared: Mapping[str, Any],
    activation_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    """Construct the exact frozen model-transport/1 binding for the reference adapter."""
    binding: dict[str, Any] = {
        "contract": MODEL_TRANSPORT_CONTRACT,
        "prepared_invocation_sha256": prepared["identity"]["prepared_invocation_sha256"],
        "activation_bundle_sha256": activation_bundle["identity"]["activation_bundle_sha256"],
        "adapter": {
            "adapter_id": REFERENCE_ADAPTER_ID,
            "content_identity": prepared["model_transport"]["adapter_content_identity"],
        },
        "mapping": deepcopy(MAPPING),
        "threat_model": deepcopy(THREAT_MODEL),
    }
    binding["identity"] = {
        "transport_sha256": _domain_identity(TRANSPORT_DOMAIN, binding)
    }
    return binding


def validate_transport_binding(
    binding: Mapping[str, Any],
    prepared: Mapping[str, Any],
    activation_bundle: Mapping[str, Any],
) -> None:
    """Fail closed if a provider mapping differs from the frozen G1/G5 mapping."""
    expected = build_transport_binding(prepared, activation_bundle)
    if binding != expected:
        raise _fail(
            "MODEL_TRANSPORT_NONCONFORMING",
            "provider transport binding differs from the frozen model-transport/1 mapping",
        )


def build_reference_provider_request(
    transport_binding: Mapping[str, Any],
    activation_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    """Map the exact activation into the package-owned reference provider shape."""
    if transport_binding.get("adapter", {}).get("adapter_id") != REFERENCE_ADAPTER_ID:
        raise _fail("MODEL_TRANSPORT_NONCONFORMING", "reference runner received an unsupported adapter")
    return {
        "model_transport": deepcopy(transport_binding),
        "framework_instruction": {
            "directive": deepcopy(activation_bundle["directive"]),
            "instruction": activation_bundle["instruction"],
        },
        "project_context": {
            "rendered_activation": deepcopy(activation_bundle["rendered_activation"]),
            "provenance_registry": deepcopy(activation_bundle["provenance_registry"]),
        },
    }


def run_reference_transport(
    prepared_invocation_raw: bytes,
    activation_bundle_raw: bytes,
    *,
    expected_prepared_invocation_sha256: str,
    provider: Callable[[Mapping[str, Any]], bytes],
    installed_root: str | Path | None = None,
) -> TransportRunResult:
    """Execute one non-hostile reference transport without crossing into G6 finalization."""
    prepared = _verify_prepared(
        prepared_invocation_raw,
        expected_prepared_invocation_sha256,
    )
    _verify_installed_package(prepared, installed_root)
    activation_bundle = _verify_activation_bundle(activation_bundle_raw, prepared)
    binding = build_transport_binding(prepared, activation_bundle)
    validate_transport_binding(binding, prepared, activation_bundle)
    provider_request = build_reference_provider_request(binding, activation_bundle)

    try:
        raw_model_bytes = provider(deepcopy(provider_request))
    except TransportFailure:
        raise
    except Exception as exc:
        raise _fail(
            "MODEL_TRANSPORT_NONCONFORMING",
            f"reference provider execution failed before a valid model result: {exc}",
        ) from exc
    if not isinstance(raw_model_bytes, bytes):
        raise _fail(
            "MODEL_TRANSPORT_NONCONFORMING",
            "reference provider must return exact raw model bytes",
        )

    return TransportRunResult(
        transport_binding=binding,
        serialized_transport_binding=renderer._jcs(binding),
        provider_request=provider_request,
        raw_model_bytes=raw_model_bytes,
    )
