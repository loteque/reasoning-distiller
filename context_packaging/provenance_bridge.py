"""P10-G3 deterministic provenance bridge.

This module derives the frozen ``reasoning-distiller-context-provenance-registry/1``
sidecar from an exact context-pack/2 plus its exact rendered-activation/2. It
does not prepare an invocation, invoke a provider, finalize model output,
reconcile semantics, admit knowledge, or mutate canonical/authority state.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from .pack_builder import _jcs, _normalize_source_identity
from .pems_projection import _strict_json
from .persistence_adapter import PersistenceResult, persist_immutable_artifact

PROVENANCE_REGISTRY_CONTRACT = "reasoning-distiller-context-provenance-registry/1"
SOURCE_BINDING_CONTRACT = "reasoning-distiller-context-source-binding/1"
PACK_CONTRACT = "reasoning-distiller-context-pack/2"
RENDERED_ACTIVATION_CONTRACT = "reasoning-distiller-context-rendered-activation/2"
FAILURE_CONTRACT = "reasoning-distiller-context-pack-failure/1"

PROVENANCE_BRIDGE_INVALID = "PROVENANCE_BRIDGE_INVALID"
PROVENANCE_SOURCE_COLLISION = "PROVENANCE_SOURCE_COLLISION"

_BINDING_DOMAIN = b"reasoning-distiller-context-provenance-binding/1\x00"
_REGISTRY_DOMAIN = b"reasoning-distiller-context-provenance-registry/1\x00"
_PLANE_ORDER = ("control", "knowledge", "operational_evidence")
_PLANE_KEYS = {
    "control": "control_plane",
    "knowledge": "knowledge_plane",
    "operational_evidence": "operational_evidence_plane",
}
_SNAPSHOT_FIELDS = {
    "repository_control": (
        "source_class",
        "logical_namespace",
        "logical_source_id",
        "repository",
        "commit",
        "path",
        "raw_sha256",
    ),
    "package_control": (
        "source_class",
        "logical_namespace",
        "logical_source_id",
        "project_id",
        "package_contract",
        "immutable_package_snapshot_id",
        "artifact_locator",
        "raw_sha256",
    ),
    "canonical_state": (
        "source_class",
        "logical_namespace",
        "logical_source_id",
        "project_id",
        "backend_type",
        "backend_contract",
        "backend_config_identity",
        "immutable_snapshot_id",
        "pems_semantic",
        "serializer",
        "pems_sha256",
        "standing_evidence",
        "cove",
    ),
    "operational_evidence": (
        "source_class",
        "logical_namespace",
        "logical_source_id",
        "artifact_contract",
        "immutable_snapshot_id",
        "raw_sha256",
        "validation_status",
        "validation_result",
    ),
}


@dataclass(frozen=True)
class ProvenanceRegistryResult:
    registry: Mapping[str, Any] | None = None
    serialized_registry: bytes | None = None
    raw_sha256: str | None = None
    failure: Mapping[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.failure is None


class _BridgeFailure(ValueError):
    def __init__(self, code: str, diagnostic: str) -> None:
        super().__init__(diagnostic)
        self.code = code
        self.diagnostic = diagnostic


def derive_context_source_id(binding: Mapping[str, Any]) -> str:
    """Derive the frozen stable source ID from one complete canonical binding."""
    canonical = _canonical_binding(binding)
    digest = _binding_digest(_jcs(canonical))
    return "src:ctx:" + digest


def derive_provenance_registry(
    pack: Mapping[str, Any],
    rendered_activation: Mapping[str, Any],
) -> ProvenanceRegistryResult:
    """Derive one deterministic registry without persistence or ambient lookup."""
    try:
        pack_identity = _pack_identity(pack)
        activation_identity = _activation_identity(rendered_activation, pack_identity)
        records, by_snapshot = _source_records(pack)
        occurrences = _occurrences(
            pack,
            rendered_activation,
            pack_identity,
            by_snapshot,
        )

        used = {occurrence["source_id"] for occurrence in occurrences}
        if used != set(records):
            raise _BridgeFailure(
                PROVENANCE_BRIDGE_INVALID,
                "pack source registry and model-visible frame source set differ",
            )

        registry: dict[str, Any] = {
            "contract": PROVENANCE_REGISTRY_CONTRACT,
            "pack_identity_sha256": pack_identity,
            "rendered_activation_identity_sha256": activation_identity,
            "sources": [records[source_id] for source_id in sorted(records)],
            "occurrences": occurrences,
        }
        registry["identity"] = {
            "registry_sha256": _sha256_label(
                _REGISTRY_DOMAIN + _jcs(registry)
            )
        }
        serialized = _jcs(registry)
        _validate_registry_bytes(serialized)
        return ProvenanceRegistryResult(
            registry=registry,
            serialized_registry=serialized,
            raw_sha256=_sha256_label(serialized),
        )
    except _BridgeFailure as exc:
        return ProvenanceRegistryResult(failure=_failure(exc.code, exc.diagnostic))
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        return ProvenanceRegistryResult(
            failure=_failure(
                PROVENANCE_BRIDGE_INVALID,
                f"invalid provenance bridge input: {type(exc).__name__}",
            )
        )


def persist_provenance_registry(
    serialized_registry: bytes,
    *,
    output_root: str | Path,
    relative_path: str | Path,
    prohibited_roots: Sequence[str | Path] | None,
) -> PersistenceResult:
    """Persist exact validated registry bytes through the immutable P6 boundary."""
    _validate_registry_bytes(serialized_registry)
    return persist_immutable_artifact(
        serialized_registry,
        output_root=output_root,
        relative_path=relative_path,
        prohibited_roots=prohibited_roots,
    )


def _pack_identity(pack: Mapping[str, Any]) -> str:
    if not isinstance(pack, Mapping) or pack.get("contract") != PACK_CONTRACT:
        raise _BridgeFailure(PROVENANCE_BRIDGE_INVALID, "unsupported context pack")
    identity = pack.get("identity")
    if not isinstance(identity, Mapping):
        raise _BridgeFailure(PROVENANCE_BRIDGE_INVALID, "pack identity is missing")
    return _normalize_sha256(identity.get("pack_identity_sha256"))


def _activation_identity(
    activation: Mapping[str, Any], pack_identity: str
) -> str:
    if (
        not isinstance(activation, Mapping)
        or activation.get("contract") != RENDERED_ACTIVATION_CONTRACT
    ):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "unsupported rendered activation"
        )
    summary = activation.get("pack")
    if (
        not isinstance(summary, Mapping)
        or summary.get("contract") != PACK_CONTRACT
        or _normalize_sha256(summary.get("pack_identity_sha256")) != pack_identity
    ):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID,
            "rendered activation does not bind the exact pack identity",
        )
    identity = activation.get("identity")
    if not isinstance(identity, Mapping):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "rendered activation identity is missing"
        )
    return _normalize_sha256(identity.get("activation_identity_sha256"))


def _source_records(
    pack: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[bytes, list[str]]]:
    source_registry = pack.get("source_registry")
    if not isinstance(source_registry, list) or not source_registry:
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "pack source registry is missing"
        )

    records: dict[str, dict[str, Any]] = {}
    by_snapshot: dict[bytes, list[str]] = {}
    seen_binding_bytes: set[bytes] = set()

    for raw_binding in source_registry:
        canonical = _canonical_binding(raw_binding)
        binding_bytes = _jcs(canonical)
        if binding_bytes in seen_binding_bytes:
            raise _BridgeFailure(
                PROVENANCE_BRIDGE_INVALID,
                "pack source registry contains a duplicate canonical binding",
            )
        seen_binding_bytes.add(binding_bytes)

        digest = _binding_digest(binding_bytes)
        binding_sha256 = "sha256:" + digest
        source_id = "src:ctx:" + digest
        record = {
            "source_id": source_id,
            "binding_sha256": binding_sha256,
            "source_class": canonical["source_class"],
            "payload_sha256": _payload_sha256(canonical),
            "binding": canonical,
        }

        previous = records.get(source_id)
        if previous is not None and _jcs(previous) != _jcs(record):
            raise _BridgeFailure(
                PROVENANCE_SOURCE_COLLISION,
                "one source_id maps to conflicting stable source records",
            )
        records[source_id] = record

        snapshot_key = _jcs(_snapshot_ref(canonical))
        by_snapshot.setdefault(snapshot_key, []).append(source_id)

    return records, by_snapshot


def _occurrences(
    pack: Mapping[str, Any],
    activation: Mapping[str, Any],
    pack_identity: str,
    by_snapshot: Mapping[bytes, list[str]],
) -> list[dict[str, Any]]:
    frames = activation.get("frames")
    if not isinstance(frames, list) or not frames:
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "rendered activation frames are missing"
        )

    first = frames[0]
    if (
        not isinstance(first, Mapping)
        or first.get("frame_index") != 0
        or first.get("kind") != "metadata"
    ):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "rendered metadata frame is invalid"
        )

    expected: list[tuple[str, int, Mapping[str, Any]]] = []
    for plane in _PLANE_ORDER:
        box = pack.get(_PLANE_KEYS[plane])
        items = box.get("items") if isinstance(box, Mapping) else None
        if not isinstance(items, list):
            raise _BridgeFailure(
                PROVENANCE_BRIDGE_INVALID, f"{plane} pack plane is invalid"
            )
        for item_index, item in enumerate(items):
            if not isinstance(item, Mapping):
                raise _BridgeFailure(
                    PROVENANCE_BRIDGE_INVALID, f"{plane} pack item is invalid"
                )
            expected.append((plane, item_index, item))

    if len(frames) != len(expected) + 1:
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID,
            "rendered plane-frame count does not match the exact pack",
        )

    occurrences: list[dict[str, Any]] = []
    for frame_index, (plane, item_index, item) in enumerate(expected, start=1):
        frame = frames[frame_index]
        if (
            not isinstance(frame, Mapping)
            or frame.get("frame_index") != frame_index
            or frame.get("kind") != "plane_item"
            or frame.get("plane") != plane
            or frame.get("item_index") != item_index
        ):
            raise _BridgeFailure(
                PROVENANCE_BRIDGE_INVALID,
                "rendered frame order or pack-local occurrence identity is invalid",
            )
        _verify_frame_payload(frame, item)

        ref = _item_source_ref(plane, item)
        key = _jcs(ref)
        candidates = by_snapshot.get(key, [])
        if len(candidates) != 1:
            diagnostic = (
                "rendered plane item source reference is unresolved"
                if not candidates
                else "rendered plane item source reference is ambiguous"
            )
            raise _BridgeFailure(PROVENANCE_BRIDGE_INVALID, diagnostic)

        occurrences.append(
            {
                "pack_identity_sha256": pack_identity,
                "frame_index": frame_index,
                "plane": plane,
                "item_index": item_index,
                "source_id": candidates[0],
            }
        )
    return occurrences


def _verify_frame_payload(
    frame: Mapping[str, Any], item: Mapping[str, Any]
) -> None:
    if frame.get("encoding") != "base64" or not isinstance(frame.get("data"), str):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "rendered frame encoding is invalid"
        )
    try:
        raw = base64.b64decode(frame["data"].encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as exc:
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "rendered frame base64 is invalid"
        ) from exc
    expected = _jcs(deepcopy(dict(item)))
    if raw != expected or _normalize_sha256(frame.get("raw_sha256")) != _sha256_label(raw):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID,
            "rendered frame payload does not exactly match the sealed pack item",
        )


def _item_source_ref(plane: str, item: Mapping[str, Any]) -> dict[str, Any]:
    key = "canonical_snapshot_ref" if plane == "knowledge" else "source_ref"
    value = item.get(key)
    if not isinstance(value, Mapping):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, f"{plane} item source reference is missing"
        )
    normalized = _normalize_source_identity(value)
    if normalized != dict(value):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID,
            f"{plane} item source reference is not canonical",
        )
    return normalized


def _canonical_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(binding, Mapping):
        raise _BridgeFailure(PROVENANCE_BRIDGE_INVALID, "source binding is invalid")
    canonical = _normalize_source_identity(binding)
    if canonical != dict(binding):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "source binding is not canonical"
        )
    if canonical.get("contract") != SOURCE_BINDING_CONTRACT:
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "source binding contract is unsupported"
        )
    source_class = canonical.get("source_class")
    fields = _SNAPSHOT_FIELDS.get(source_class)
    if fields is None:
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "source binding class is unsupported"
        )
    required = set(fields) | {"contract"}
    optional = {
        "canonical_state": {"cove", "repository_relationship"},
        "operational_evidence": {"validation_result"},
    }.get(source_class, set())
    # Optional fields are present in ``fields`` only when they belong in the
    # snapshot projection; remove them from the mandatory set.
    required -= {"cove", "validation_result"}
    if set(canonical) - (required | optional):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "source binding contains unsupported fields"
        )
    if not required.issubset(canonical):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "source binding is incomplete"
        )
    if (
        not isinstance(canonical.get("logical_namespace"), str)
        or not canonical["logical_namespace"]
        or not isinstance(canonical.get("logical_source_id"), str)
        or not canonical["logical_source_id"]
    ):
        raise _BridgeFailure(
            PROVENANCE_BRIDGE_INVALID, "source binding logical identity is invalid"
        )
    _payload_sha256(canonical)
    return deepcopy(canonical)


def _snapshot_ref(binding: Mapping[str, Any]) -> dict[str, Any]:
    fields = _SNAPSHOT_FIELDS[binding["source_class"]]
    ref = {field: deepcopy(binding[field]) for field in fields if field in binding}
    normalized = _normalize_source_identity(ref)
    return normalized


def _payload_sha256(binding: Mapping[str, Any]) -> str:
    field = "pems_sha256" if binding.get("source_class") == "canonical_state" else "raw_sha256"
    return _normalize_sha256(binding.get(field))


def _binding_digest(binding_bytes: bytes) -> str:
    return hashlib.sha256(_BINDING_DOMAIN + binding_bytes).hexdigest()


def _normalize_sha256(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        raise _BridgeFailure(PROVENANCE_BRIDGE_INVALID, "invalid sha256 identity")
    body = value[7:]
    if any(ch not in "0123456789abcdefABCDEF" for ch in body):
        raise _BridgeFailure(PROVENANCE_BRIDGE_INVALID, "invalid sha256 identity")
    return "sha256:" + body.lower()


def _sha256_label(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _validate_registry_structure(value: Mapping[str, Any]) -> None:
    if set(value) != {
        "contract",
        "pack_identity_sha256",
        "rendered_activation_identity_sha256",
        "sources",
        "occurrences",
        "identity",
    }:
        raise ValueError("provenance registry fields are invalid")
    pack_identity = _normalize_sha256(value.get("pack_identity_sha256"))
    _normalize_sha256(value.get("rendered_activation_identity_sha256"))

    sources = value.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("provenance registry sources are invalid")
    source_ids: list[str] = []
    for record in sources:
        if not isinstance(record, Mapping) or set(record) != {
            "source_id",
            "binding_sha256",
            "source_class",
            "payload_sha256",
            "binding",
        }:
            raise ValueError("provenance source record is invalid")
        canonical = _canonical_binding(record["binding"])
        binding_digest = _binding_digest(_jcs(canonical))
        source_id = "src:ctx:" + binding_digest
        if record.get("source_id") != source_id:
            raise ValueError("provenance source id mismatch")
        if _normalize_sha256(record.get("binding_sha256")) != "sha256:" + binding_digest:
            raise ValueError("provenance binding digest mismatch")
        if record.get("source_class") != canonical["source_class"]:
            raise ValueError("provenance source class mismatch")
        if _normalize_sha256(record.get("payload_sha256")) != _payload_sha256(canonical):
            raise ValueError("provenance payload digest mismatch")
        source_ids.append(source_id)
    if source_ids != sorted(source_ids) or len(source_ids) != len(set(source_ids)):
        raise ValueError("provenance source records are not canonical")

    occurrences = value.get("occurrences")
    if not isinstance(occurrences, list) or not occurrences:
        raise ValueError("provenance occurrences are invalid")
    for expected_index, occurrence in enumerate(occurrences, start=1):
        if not isinstance(occurrence, Mapping) or set(occurrence) != {
            "pack_identity_sha256",
            "frame_index",
            "plane",
            "item_index",
            "source_id",
        }:
            raise ValueError("provenance occurrence is invalid")
        if _normalize_sha256(occurrence.get("pack_identity_sha256")) != pack_identity:
            raise ValueError("provenance occurrence pack identity mismatch")
        if occurrence.get("frame_index") != expected_index:
            raise ValueError("provenance occurrence frame order is invalid")
        if occurrence.get("plane") not in _PLANE_ORDER:
            raise ValueError("provenance occurrence plane is invalid")
        item_index = occurrence.get("item_index")
        if not isinstance(item_index, int) or isinstance(item_index, bool) or item_index < 0:
            raise ValueError("provenance occurrence item index is invalid")
        if occurrence.get("source_id") not in source_ids:
            raise ValueError("provenance occurrence source is unresolved")


def _validate_registry_bytes(raw: bytes) -> Mapping[str, Any]:
    if not isinstance(raw, bytes):
        raise TypeError("serialized_registry must be bytes")
    try:
        value = _strict_json(raw)
    except Exception as exc:
        raise ValueError("provenance registry must be strict UTF-8 JSON") from exc
    if not isinstance(value, Mapping) or _jcs(dict(value)) != raw:
        raise ValueError("provenance registry must be canonical JCS bytes")
    if value.get("contract") != PROVENANCE_REGISTRY_CONTRACT:
        raise ValueError("unsupported provenance registry contract")
    _validate_registry_structure(value)
    identity = value.get("identity")
    if not isinstance(identity, Mapping) or set(identity) != {"registry_sha256"}:
        raise ValueError("provenance registry identity is invalid")
    preimage = deepcopy(dict(value))
    preimage.pop("identity")
    expected = _sha256_label(_REGISTRY_DOMAIN + _jcs(preimage))
    if _normalize_sha256(identity.get("registry_sha256")) != expected:
        raise ValueError("provenance registry identity mismatch")
    return value


def _failure(code: str, diagnostic: str) -> Mapping[str, Any]:
    return {
        "contract": FAILURE_CONTRACT,
        "code": code,
        "stage": "activation",
        "diagnostics": [diagnostic],
    }
