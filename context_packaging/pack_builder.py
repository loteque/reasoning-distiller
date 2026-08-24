"""P5 pure deterministic context-pack builder with explicit /1 and /2 dispatch.

The closed /2 amendment supplies the lossless namespaced outer-ledger representation
needed by P5. This module keeps /1 as a legacy-compatible family, implements the
full P5 domain under /2, canonicalizes builder-owned SHA-256 spellings, and performs
no persistence, rendering, source discovery, admission, reconciliation, authority,
activation, or canonical mutation.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import pack_builder_v1 as _v1
from .cove_adapter import CoveAdapterError, encode_cove_pems
from .pems_projection import ProjectedKnowledge, _strict_json
from .source_resolver import ResolvedSource, _snapshot_key

PROFILE_CONTRACT_V1 = "reasoning-distiller-context-profile/1"
REQUEST_CONTRACT_V1 = "reasoning-distiller-context-pack-request/1"
PACK_CONTRACT_V1 = "reasoning-distiller-context-pack/1"
RESULT_CONTRACT_V1 = "reasoning-distiller-context-pack-result/1"
PACK_BUILDER_CONTRACT_V1 = "reasoning-distiller-context-pack-builder/1"

PROFILE_CONTRACT_V2 = "reasoning-distiller-context-profile/2"
REQUEST_CONTRACT_V2 = "reasoning-distiller-context-pack-request/2"
PACK_CONTRACT_V2 = "reasoning-distiller-context-pack/2"
RESULT_CONTRACT_V2 = "reasoning-distiller-context-pack-result/2"
PACK_BUILDER_CONTRACT_V2 = "reasoning-distiller-context-pack-builder/2"

PACK_CONTRACT = PACK_CONTRACT_V2
PACK_BUILDER_CONTRACT = PACK_BUILDER_CONTRACT_V2
RECEIPT_CONTRACT = _v1.RECEIPT_CONTRACT
FAILURE_CONTRACT = _v1.FAILURE_CONTRACT

ContextPackBuildResult = _v1.ContextPackBuildResult
_BuildFailure = _v1._BuildFailure

_PEMS_V2_BLOB = "cd7683d704e8aef2842a0c1b25b453fb1dbc8030"
_PEMS_V2_RAW_SHA256 = (
    "sha256:b08e592ab7c10092ff381fe8057cac63ccb7aaa077b52532f5ee609c6fd279c3"
)
_PACK_BUILDER_V1_BLOB = "b0e806e966598e6d819b6d52c643efa23cdb6ef9"


def build_context_pack(
    profile_raw: bytes,
    profile: Mapping[str, Any],
    request_raw: bytes,
    request: Mapping[str, Any],
    resolved_sources: Sequence[ResolvedSource],
    projected_knowledge: Sequence[ProjectedKnowledge],
    toolchain_components: Sequence[Mapping[str, Any]],
) -> ContextPackBuildResult:
    """Build one canonical /1 or /2 pack without side effects or family coercion."""
    try:
        family = _dispatch_family(profile, request)
    except _BuildFailure as exc:
        return ContextPackBuildResult(
            failure=_v1._failure(exc.code, exc.stage, exc.diagnostic, exc.source_ref)
        )

    if family == 1:
        legacy = _v1.build_context_pack(
            profile_raw,
            profile,
            request_raw,
            request,
            resolved_sources,
            projected_knowledge,
            toolchain_components,
        )
        if not legacy.ok:
            return legacy
        try:
            return _finalize_canonical_result(profile, request, legacy.pack)
        except _BuildFailure as exc:
            return ContextPackBuildResult(
                failure=_v1._failure(exc.code, exc.stage, exc.diagnostic, exc.source_ref)
            )
        except (KeyError, TypeError, ValueError, UnicodeError) as exc:
            return ContextPackBuildResult(
                failure=_v1._failure(
                    "INVALID_REQUEST",
                    "pack",
                    f"invalid P5 build input: {type(exc).__name__}",
                )
            )

    return _build_v2(
        profile_raw,
        profile,
        request_raw,
        request,
        resolved_sources,
        projected_knowledge,
        toolchain_components,
    )


def _dispatch_family(profile: Mapping[str, Any], request: Mapping[str, Any]) -> int:
    if not isinstance(profile, Mapping) or not isinstance(request, Mapping):
        raise _BuildFailure("INVALID_REQUEST", "profile/request must be mappings")
    profile_contract = profile.get("contract")
    request_contract = request.get("contract")
    if profile_contract == PROFILE_CONTRACT_V1 and request_contract == REQUEST_CONTRACT_V1:
        return 1
    if profile_contract == PROFILE_CONTRACT_V2 and request_contract == REQUEST_CONTRACT_V2:
        return 2
    if profile_contract in {PROFILE_CONTRACT_V1, PROFILE_CONTRACT_V2}:
        raise _BuildFailure("INVALID_REQUEST", "profile/request contract family mismatch")
    raise _BuildFailure("INVALID_PROFILE", "unsupported profile contract")


def _build_v2(
    profile_raw: bytes,
    profile: Mapping[str, Any],
    request_raw: bytes,
    request: Mapping[str, Any],
    resolved_sources: Sequence[ResolvedSource],
    projected_knowledge: Sequence[ProjectedKnowledge],
    toolchain_components: Sequence[Mapping[str, Any]],
) -> ContextPackBuildResult:
    try:
        _verify_pack_builder_v1_identity()
        _preflight_v2(profile_raw, profile, request_raw, request)
        source_index = _v1._index_resolved_sources(resolved_sources)
        control_items, control_ledger, control_bindings = _v1._build_control_plane(
            request, source_index
        )
        operational_items, operational_ledger, operational_bindings = (
            _v1._build_operational_plane(request, source_index)
        )
        knowledge_items, knowledge_ledger, knowledge_bindings = _build_knowledge_plane_v2(
            request, source_index, projected_knowledge
        )
        _v1._enforce_plane_separation(
            control_items, knowledge_items, operational_items
        )

        limits = profile["limits"]["canonical_pack"]
        if len(control_items) > limits["max_control_items"]:
            raise _BuildFailure(
                "PACK_LIMIT_EXCEEDED", "canonical_pack.max_control_items exceeded"
            )
        if len(operational_items) > limits["max_operational_evidence_items"]:
            raise _BuildFailure(
                "PACK_LIMIT_EXCEEDED",
                "canonical_pack.max_operational_evidence_items exceeded",
            )

        source_registry = _v1._canonical_source_registry(
            [*control_bindings, *knowledge_bindings, *operational_bindings]
        )
        components = _validate_toolchain_v2(
            profile, knowledge_items, toolchain_components
        )
        pack: dict[str, Any] = {
            "contract": PACK_CONTRACT_V2,
            "profile": {
                "profile_id": profile["profile_id"],
                "profile_version": profile["profile_version"],
                "raw_sha256": _v1._raw_sha256(profile_raw),
            },
            "request": {
                "request_id": request["request_id"],
                "raw_sha256": _v1._raw_sha256(request_raw),
            },
            "source_registry": source_registry,
            "control_plane": {"items": control_items},
            "knowledge_plane": {"items": knowledge_items},
            "operational_evidence_plane": {"items": operational_items},
            "inclusion_ledger": [
                *control_ledger,
                *knowledge_ledger,
                *operational_ledger,
            ],
            "toolchain": {"components": components},
        }
        eligibility = _v1._pack_eligibility(request)
        if eligibility is not None:
            pack["eligibility"] = eligibility
        return _finalize_canonical_result(profile, request, pack)
    except _BuildFailure as exc:
        return ContextPackBuildResult(
            failure=_v1._failure(exc.code, exc.stage, exc.diagnostic, exc.source_ref)
        )
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        return ContextPackBuildResult(
            failure=_v1._failure(
                "INVALID_REQUEST",
                "pack",
                f"invalid P5 build input: {type(exc).__name__}",
            )
        )


def _verify_pack_builder_v1_identity() -> None:
    source = getattr(_v1, "__file__", None)
    if not isinstance(source, str) or not source:
        raise _BuildFailure(
            "TOOLCHAIN_IDENTITY_MISMATCH",
            "pack_builder/2 dependency source is unavailable",
            stage="toolchain",
        )
    try:
        raw = Path(source).read_bytes()
    except OSError as exc:
        raise _BuildFailure(
            "TOOLCHAIN_IDENTITY_MISMATCH",
            "pack_builder/2 dependency source is unavailable",
            stage="toolchain",
        ) from exc
    actual = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    if actual != _PACK_BUILDER_V1_BLOB:
        raise _BuildFailure(
            "TOOLCHAIN_IDENTITY_MISMATCH",
            "pack_builder/2 dependency identity mismatch",
            stage="toolchain",
        )


def _preflight_v2(
    profile_raw: bytes,
    profile: Mapping[str, Any],
    request_raw: bytes,
    request: Mapping[str, Any],
) -> None:
    if not isinstance(profile_raw, bytes) or not isinstance(request_raw, bytes):
        raise _BuildFailure("INVALID_REQUEST", "profile/request raw inputs must be bytes")
    try:
        parsed_profile = _strict_json(profile_raw)
        parsed_request = _strict_json(request_raw)
    except Exception as exc:
        raise _BuildFailure(
            "INVALID_REQUEST", "profile/request raw bytes must be strict UTF-8 JSON"
        ) from exc
    if parsed_profile != dict(profile):
        raise _BuildFailure("INVALID_PROFILE", "profile raw bytes do not bind profile object")
    if parsed_request != dict(request):
        raise _BuildFailure("INVALID_REQUEST", "request raw bytes do not bind request object")
    if profile.get("contract") != PROFILE_CONTRACT_V2:
        raise _BuildFailure("INVALID_PROFILE", "unsupported profile contract")
    if request.get("contract") != REQUEST_CONTRACT_V2:
        raise _BuildFailure("INVALID_REQUEST", "unsupported request contract")

    contracts = profile.get("contracts")
    if not isinstance(contracts, Mapping):
        raise _BuildFailure("UNSUPPORTED_PROFILE", "profile contract bindings missing")
    expected = {
        "request": REQUEST_CONTRACT_V2,
        "pack": PACK_CONTRACT_V2,
        "result": RESULT_CONTRACT_V2,
        "failure": FAILURE_CONTRACT,
        "source_binding": "reasoning-distiller-context-source-binding/1",
        "eligibility": "reasoning-distiller-context-profile-eligibility/1",
        "receipt": RECEIPT_CONTRACT,
    }
    if any(contracts.get(key) != value for key, value in expected.items()):
        raise _BuildFailure(
            "UNSUPPORTED_PROFILE", "profile does not bind the exact /2 contract family"
        )
    if request.get("output", {}).get("pack_contract") != PACK_CONTRACT_V2:
        raise _BuildFailure("INVALID_REQUEST", "request does not bind context-pack/2")

    profile_raw_sha = _v1._raw_sha256(profile_raw)
    requested_profile = request.get("profile")
    if not isinstance(requested_profile, Mapping):
        raise _BuildFailure("INVALID_REQUEST", "request profile identity missing")
    if (
        requested_profile.get("profile_id") != profile.get("profile_id")
        or requested_profile.get("profile_version") != profile.get("profile_version")
        or _v1._normalize_sha256(requested_profile.get("raw_sha256")) != profile_raw_sha
    ):
        raise _BuildFailure("INVALID_REQUEST", "request profile identity mismatch")

    profile_output = profile.get("output")
    request_output = request.get("output")
    if not isinstance(profile_output, Mapping) or not isinstance(request_output, Mapping):
        raise _BuildFailure("INVALID_REQUEST", "output contract missing")
    if (
        profile_output.get("serializer") != "jcs/1"
        or request_output.get("serializer") != "jcs/1"
        or profile_output.get("knowledge_encoding")
        != request_output.get("knowledge_encoding")
        or profile_output.get("knowledge_encoding") not in {"pems/2", "cove/1"}
    ):
        raise _BuildFailure(
            "UNSUPPORTED_ENCODING_TUPLE",
            "profile/request output tuple mismatch",
            stage="encoding",
        )

    eligibility = request.get("eligibility")
    if eligibility is not None:
        if not isinstance(eligibility, Mapping):
            raise _BuildFailure(
                "PROFILE_INELIGIBLE",
                "eligibility binding is invalid",
                stage="eligibility",
            )
        if eligibility.get("decision") != "eligible":
            raise _BuildFailure(
                "PROFILE_INELIGIBLE",
                "profile eligibility is not eligible",
                stage="eligibility",
            )
        bound_profile = eligibility.get("profile")
        if (
            not isinstance(bound_profile, Mapping)
            or bound_profile.get("profile_id") != requested_profile.get("profile_id")
            or bound_profile.get("profile_version")
            != requested_profile.get("profile_version")
            or _v1._normalize_sha256(bound_profile.get("raw_sha256"))
            != profile_raw_sha
        ):
            raise _BuildFailure(
                "PROFILE_INELIGIBLE",
                "eligibility binding does not identify the exact /2 profile",
                stage="eligibility",
            )


def _build_knowledge_plane_v2(request, source_index, projected_knowledge):
    selections = request.get("knowledge_selection", {}).get("snapshots", [])
    selection_keys: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for item in selections:
        key = _snapshot_key(item["canonical_snapshot_ref"])
        if key in selection_keys:
            raise _BuildFailure(
                "INVALID_REQUEST",
                "duplicate canonical snapshot selection",
                item["canonical_snapshot_ref"],
            )
        selection_keys[key] = item

    seen: set[tuple[Any, ...]] = set()
    items: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    bindings: list[Mapping[str, Any]] = []
    encoding = request["output"]["knowledge_encoding"]

    for projected in projected_knowledge:
        if not hasattr(projected, "canonical_snapshot_ref") or not hasattr(projected, "pems"):
            raise _BuildFailure(
                "PEMS_SEMANTIC_INVALID",
                "invalid P3 projection input",
                stage="projection",
            )
        ref = _normalize_snapshot_ref(projected.canonical_snapshot_ref)
        key = _snapshot_key(ref)
        if key not in selection_keys or key in seen:
            raise _BuildFailure(
                "INVALID_REQUEST",
                "P3 projection does not correspond one-to-one with requested snapshot selection",
                ref,
            )
        seen.add(key)
        source = _v1._find_resolved(ref, source_index)
        if source.binding.get("source_class") != "canonical_state":
            raise _BuildFailure(
                "PLANE_CLASSIFICATION_CONFLICT",
                "non-canonical source classified into knowledge plane",
                ref,
            )

        binding = _normalize_source_identity(_v1._canonical_binding(source.binding))
        pems = deepcopy(projected.pems)
        if not isinstance(pems, Mapping) or pems.get("semantic") != "pems/2":
            raise _BuildFailure(
                "PEMS_SEMANTIC_INVALID",
                "P3 projection is not PEMS/2",
                ref,
                "projection",
            )
        item: dict[str, Any] = {
            "canonical_snapshot_ref": ref,
            "semantic": "pems/2",
            "serializer": "jcs/1",
            "pems": pems,
        }
        if encoding == "cove/1":
            try:
                raw_cove = encode_cove_pems(pems)
            except CoveAdapterError as exc:
                raise _BuildFailure(
                    "COVE_ROUNDTRIP_MISMATCH",
                    "P4 COVE adapter rejected selected PEMS projection",
                    ref,
                    "encoding",
                ) from exc
            item["cove_payload"] = {
                "cove_semantic": "cove/1",
                "pems_semantic": "pems/2",
                "serializer": "jcs/1",
                "encoding": "base64",
                "data": _v1._b64(raw_cove),
                "raw_sha256": _v1._raw_sha256(raw_cove),
            }
        items.append(item)
        bindings.append(binding)
        ledger.append(
            {
                "plane": "knowledge",
                "subject": {"source_ref": deepcopy(ref)},
                "causes": [
                    {
                        "kind": "request_selector",
                        "cause_id": str(ref["immutable_snapshot_id"]),
                    }
                ],
            }
        )

        semantic_ids = {
            "record": {
                str(record.get("id"))
                for record in pems.get("records", [])
                if isinstance(record, Mapping) and record.get("id") is not None
            },
            "relation": {
                str(relation.get("id"))
                for relation in pems.get("relations", [])
                if isinstance(relation, Mapping) and relation.get("id") is not None
            },
        }
        covered: set[tuple[str, str]] = set()
        by_semantic: dict[tuple[str, str], list[dict[str, str]]] = {}
        for cause in getattr(projected, "causes", ()):
            namespace = str(cause.namespace)
            semantic_id = str(cause.semantic_id)
            kind = str(cause.kind)
            if namespace not in semantic_ids or semantic_id not in semantic_ids[namespace]:
                raise _BuildFailure(
                    "PEMS_SEMANTIC_INVALID",
                    "P3 provenance names a semantic item absent from the projection",
                    ref,
                    "projection",
                )
            if kind not in {"request_selector", "pems_closure"}:
                raise _BuildFailure(
                    "UNKNOWN_SEMANTICS_FIELD",
                    "unsupported P3 selection-provenance cause kind",
                    ref,
                    "projection",
                )
            subject_key = (namespace, semantic_id)
            covered.add(subject_key)
            by_semantic.setdefault(subject_key, []).append(
                {"kind": kind, "cause_id": str(cause.cause_id)}
            )

        expected = {
            (namespace, semantic_id)
            for namespace, values in semantic_ids.items()
            for semantic_id in values
        }
        if covered != expected:
            raise _BuildFailure(
                "PEMS_SEMANTIC_INVALID",
                "P3 projection lacks deterministic provenance for one or more semantic items",
                ref,
                "projection",
            )
        for (namespace, semantic_id), semantic_causes in by_semantic.items():
            ledger.append(
                {
                    "plane": "knowledge",
                    "subject": {
                        "source_ref": deepcopy(ref),
                        "pems_ref": {"namespace": namespace, "id": semantic_id},
                    },
                    "causes": semantic_causes,
                }
            )

    if seen != set(selection_keys):
        raise _BuildFailure(
            "INVALID_REQUEST", "not every requested canonical snapshot has one P3 projection"
        )
    return items, ledger, bindings


def _validate_toolchain_v2(profile, knowledge_items, components):
    normalized = [deepcopy(dict(component)) for component in components]
    roles = [component.get("role") for component in normalized]
    if len(roles) != len(set(roles)):
        raise _BuildFailure(
            "TOOLCHAIN_IDENTITY_MISMATCH", "duplicate toolchain role", stage="toolchain"
        )
    required = {
        "pems_schema",
        "pems_validator",
        "closure_descriptor",
        "jcs_serializer",
        "pack_builder",
    }
    if any("cove_payload" in item for item in knowledge_items):
        required.add("cove_adapter")
    if set(roles) != required:
        raise _BuildFailure(
            "TOOLCHAIN_IDENTITY_MISMATCH",
            "toolchain roles do not exactly match behavior used by this build",
            stage="toolchain",
        )

    for component in normalized:
        if component.get("role") not in _v1._TOOLCHAIN_RANK:
            raise _BuildFailure(
                "TOOLCHAIN_IDENTITY_MISMATCH", "unknown toolchain role", stage="toolchain"
            )
        if not all(
            isinstance(component.get(field), str) and component.get(field)
            for field in ("contract", "immutable_identity", "raw_sha256")
        ):
            raise _BuildFailure(
                "TOOLCHAIN_IDENTITY_MISMATCH",
                "incomplete toolchain component",
                stage="toolchain",
            )
        component["raw_sha256"] = _v1._normalize_sha256(component["raw_sha256"])

    by_role = {component["role"]: component for component in normalized}
    closure = profile["knowledge"]["closure_descriptor"]
    actual = by_role["closure_descriptor"]
    if (
        actual["contract"] != closure["contract"]
        or actual["immutable_identity"] != closure["immutable_snapshot_id"]
        or actual["raw_sha256"] != _v1._normalize_sha256(closure["raw_sha256"])
        or by_role["jcs_serializer"]["contract"] != "jcs/1"
        or by_role["pack_builder"]["contract"] != PACK_BUILDER_CONTRACT_V2
    ):
        raise _BuildFailure(
            "TOOLCHAIN_IDENTITY_MISMATCH",
            "toolchain does not match profile closure/JCS/builder identity",
            stage="toolchain",
        )

    pems_schema = by_role["pems_schema"]
    if (
        pems_schema["contract"] != "pems/2"
        or pems_schema["immutable_identity"] != "git-blob:" + _PEMS_V2_BLOB
        or pems_schema["raw_sha256"] != _PEMS_V2_RAW_SHA256
    ):
        raise _BuildFailure(
            "TOOLCHAIN_IDENTITY_MISMATCH",
            "toolchain does not bind the immutable /2 PEMS schema resource bytes",
            stage="toolchain",
        )
    return sorted(
        normalized,
        key=lambda component: (
            _v1._TOOLCHAIN_RANK[component["role"]],
            _v1._jcs(component),
        ),
    )


def _finalize_canonical_result(profile, request, source_pack) -> ContextPackBuildResult:
    pack = _canonicalize_pack(source_pack)
    identity = _v1._build_identity(profile, request, pack)
    pack["identity"] = identity
    serialized = _v1._jcs(pack)
    limit = profile["limits"]["canonical_pack"]["max_bytes"]
    if len(serialized) > limit:
        raise _BuildFailure(
            "PACK_LIMIT_EXCEEDED",
            f"canonical_pack.max_bytes exceeded: actual={len(serialized)} limit={limit}",
        )

    replay = _canonicalize_pack(pack)
    replay["identity"] = _v1._build_identity(profile, request, replay)
    replay_bytes = _v1._jcs(replay)
    if replay_bytes != serialized:
        raise _BuildFailure(
            "NONDETERMINISTIC_OUTPUT",
            "canonical pack serialization was not a deterministic fixed point",
        )

    receipt = {
        "contract": RECEIPT_CONTRACT,
        "request_id": request["request_id"],
        "operation": "build",
        "result": "built",
        "pack_identity_sha256": identity["pack_identity_sha256"],
        "serialized_pack_sha256": _v1._raw_sha256(serialized),
    }
    return ContextPackBuildResult(
        pack=pack, serialized_pack=serialized, receipt=receipt
    )


def _canonicalize_pack(pack):
    out = deepcopy(dict(pack))
    out.pop("identity", None)

    normalized_registry: dict[bytes, dict[str, Any]] = {}
    for binding in out["source_registry"]:
        canonical = _normalize_source_identity(binding)
        normalized_registry[_v1._jcs(canonical)] = canonical
    out["source_registry"] = sorted(
        normalized_registry.values(),
        key=lambda binding: (
            _v1._SOURCE_CLASS_RANK[binding["source_class"]],
            _v1._jcs(binding),
        ),
    )

    for item in out["control_plane"]["items"]:
        item["source_ref"] = _normalize_source_identity(item["source_ref"])
        item["payload"]["raw_sha256"] = _v1._normalize_sha256(
            item["payload"]["raw_sha256"]
        )
    out["control_plane"]["items"].sort(
        key=lambda item: _v1._jcs(item["source_ref"])
    )

    for item in out["knowledge_plane"]["items"]:
        item["canonical_snapshot_ref"] = _normalize_source_identity(
            item["canonical_snapshot_ref"]
        )
        if "cove_payload" in item:
            item["cove_payload"]["raw_sha256"] = _v1._normalize_sha256(
                item["cove_payload"]["raw_sha256"]
            )
    out["knowledge_plane"]["items"].sort(
        key=lambda item: _v1._jcs(item["canonical_snapshot_ref"])
    )

    for item in out["operational_evidence_plane"]["items"]:
        item["source_ref"] = _normalize_source_identity(item["source_ref"])
        item["payload"]["raw_sha256"] = _v1._normalize_sha256(
            item["payload"]["raw_sha256"]
        )
        if "validation_result" in item:
            item["validation_result"]["raw_sha256"] = _v1._normalize_sha256(
                item["validation_result"]["raw_sha256"]
            )
    out["operational_evidence_plane"]["items"].sort(
        key=lambda item: _v1._jcs(item["source_ref"])
    )

    for entry in out["inclusion_ledger"]:
        entry["subject"]["source_ref"] = _normalize_source_identity(
            entry["subject"]["source_ref"]
        )
        entry["causes"].sort(
            key=lambda cause: (
                _v1._CAUSE_RANK[cause["kind"]],
                cause["cause_id"].encode("utf-8"),
            )
        )
    out["inclusion_ledger"].sort(
        key=lambda entry: (
            _v1._PLANE_RANK[entry["plane"]],
            _v1._jcs(entry["subject"]),
        )
    )

    for component in out["toolchain"]["components"]:
        component["raw_sha256"] = _v1._normalize_sha256(component["raw_sha256"])
    out["toolchain"]["components"].sort(
        key=lambda component: (
            _v1._TOOLCHAIN_RANK[component["role"]],
            _v1._jcs(component),
        )
    )
    return out


def _normalize_snapshot_ref(ref):
    return _normalize_source_identity(ref)


def _normalize_source_identity(value):
    out = deepcopy(dict(value))
    source_class = out.get("source_class")
    if source_class in {"repository_control", "package_control", "operational_evidence"}:
        if "raw_sha256" in out:
            out["raw_sha256"] = _v1._normalize_sha256(out["raw_sha256"])
    if source_class == "canonical_state":
        if "pems_sha256" in out:
            out["pems_sha256"] = _v1._normalize_sha256(out["pems_sha256"])
        if "cove" in out:
            cove = deepcopy(dict(out["cove"]))
            cove["raw_sha256"] = _v1._normalize_sha256(cove["raw_sha256"])
            out["cove"] = cove
        evidence = out.get("standing_evidence")
        if evidence is not None:
            unique: dict[bytes, dict[str, Any]] = {}
            for item in evidence:
                normalized = deepcopy(dict(item))
                normalized["raw_sha256"] = _v1._normalize_sha256(
                    normalized["raw_sha256"]
                )
                unique[_v1._jcs(normalized)] = normalized
            out["standing_evidence"] = [unique[key] for key in sorted(unique)]
    if source_class == "operational_evidence" and "validation_result" in out:
        result = deepcopy(dict(out["validation_result"]))
        result["raw_sha256"] = _v1._normalize_sha256(result["raw_sha256"])
        out["validation_result"] = result
    return out


_normalize_sha256 = _v1._normalize_sha256
_raw_sha256 = _v1._raw_sha256
_domain_sha256 = _v1._domain_sha256
_jcs = _v1._jcs
