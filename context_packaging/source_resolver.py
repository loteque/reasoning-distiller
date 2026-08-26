"""P2 read-only immutable source resolution for context packaging.

This module is deliberately separate from production ``rd-distill`` invocation.
It consumes only explicit P1 bindings and caller-supplied exact-address adapters.
It performs no source discovery, canonical admission, projection, pack building,
persistence, rendering, or model-driven relevance selection.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Any, Callable, Mapping, Sequence

BINDING_CONTRACT = "reasoning-distiller-context-source-binding/1"
FAILURE_CONTRACT = "reasoning-distiller-context-pack-failure/1"
REQUEST_CONTRACT = "reasoning-distiller-context-pack-request/1"
PROFILE_CONTRACT = "reasoning-distiller-context-profile/1"

SOURCE_CLASSES = {
    "repository_control",
    "package_control",
    "canonical_state",
    "operational_evidence",
}
CONTROL_CLASSES = {"repository_control", "package_control"}
VALIDATION_STATUSES = {
    "carried_unvalidated",
    "shape_and_digest_validated",
    "accepted_validation_result",
}
ADAPTER_STATUSES = {
    "resolved",
    "missing",
    "unsafe",
    "mutable",
    "ambiguous",
    "limit_exceeded",
}

_HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
_SHA256 = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_REPOSITORY = re.compile(r"^[^/\s]+/[^/\s]+$")


@dataclass(frozen=True)
class AdapterResult:
    """Result returned by a class-specific immutable-source adapter.

    ``binding`` must echo the exact requested binding (hex fields may differ
    only in case). ``content`` is required only for ``status == "resolved"``.
    """

    status: str
    binding: Mapping[str, Any] | None = None
    content: bytes | None = None
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolvedSource:
    binding: Mapping[str, Any]
    content: bytes


@dataclass(frozen=True)
class SourceResolutionResult:
    sources: tuple[ResolvedSource, ...] = ()
    failure: Mapping[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.failure is None


SourceAdapter = Callable[[Mapping[str, Any], int], AdapterResult]


def resolve_sources(
    request: Mapping[str, Any],
    profile: Mapping[str, Any],
    adapters: Mapping[str, SourceAdapter],
) -> SourceResolutionResult:
    """Resolve explicit immutable source bindings without discovery.

    Adapters receive only the complete requested binding and an upper byte
    bound. They must address that exact immutable source. The resolver verifies
    the returned binding and raw bytes before exposing them to later gates.
    """

    failure = _preflight(request, profile)
    if failure:
        return SourceResolutionResult(failure=failure)

    bindings = list(request["source_bindings"])
    limits = profile["limits"]["source_resolution"]

    if len(bindings) > limits["max_bindings"]:
        return SourceResolutionResult(
            failure=_failure(
                "PACK_LIMIT_EXCEEDED",
                diagnostics=(
                    _limit_diagnostic(
                        "max_bindings", len(bindings), limits["max_bindings"]
                    ),
                ),
            )
        )

    failure = _validate_binding_set(request, profile, bindings)
    if failure:
        return SourceResolutionResult(failure=failure)

    failure = _validate_request_references(request, profile, bindings)
    if failure:
        return SourceResolutionResult(failure=failure)

    # Semantically equivalent complete bindings are one immutable source
    # acquisition. Snapshot-reference equality alone is insufficient because a
    # canonical binding can carry consistency semantics outside its P1a
    # immutable fingerprint (currently repository_relationship).
    unique: list[Mapping[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for binding in bindings:
        key = _complete_binding_key(binding)
        if key not in seen:
            seen.add(key)
            unique.append(binding)

    resolved: list[ResolvedSource] = []
    total_bytes = 0
    for binding in unique:
        remaining = limits["max_total_source_bytes"] - total_bytes
        byte_limit = min(limits["max_single_source_bytes"], max(remaining, 0))
        if byte_limit <= 0:
            return SourceResolutionResult(
                failure=_failure(
                    "PACK_LIMIT_EXCEEDED",
                    binding,
                    (
                        _limit_diagnostic(
                            "max_total_source_bytes",
                            total_bytes,
                            limits["max_total_source_bytes"],
                        ),
                    ),
                )
            )

        adapter = adapters.get(binding["source_class"])
        if adapter is None:
            return SourceResolutionResult(
                failure=_failure(
                    "IMMUTABLE_SNAPSHOT_UNAVAILABLE",
                    binding,
                    ("no exact-address adapter supplied for source_class",),
                )
            )

        requested_binding = deepcopy(binding)
        try:
            adapter_result = adapter(deepcopy(requested_binding), byte_limit)
        except Exception as exc:  # adapter is an external read-only boundary
            return SourceResolutionResult(
                failure=_failure(
                    "IMMUTABLE_SNAPSHOT_UNAVAILABLE",
                    binding,
                    (f"adapter failed closed: {type(exc).__name__}",),
                )
            )

        if (
            isinstance(adapter_result, AdapterResult)
            and adapter_result.status == "limit_exceeded"
        ):
            metric = (
                "max_single_source_bytes"
                if limits["max_single_source_bytes"] <= remaining
                else "max_total_source_bytes"
            )
            return SourceResolutionResult(
                failure=_failure(
                    "PACK_LIMIT_EXCEEDED",
                    requested_binding,
                    (
                        f"source_resolution.{metric}: source exceeds effective byte_limit={byte_limit}",
                        *adapter_result.diagnostics,
                    ),
                )
            )

        failure = _validate_adapter_result(requested_binding, adapter_result)
        if failure:
            return SourceResolutionResult(failure=failure)

        assert adapter_result.content is not None
        content = adapter_result.content
        if len(content) > limits["max_single_source_bytes"]:
            return SourceResolutionResult(
                failure=_failure(
                    "PACK_LIMIT_EXCEEDED",
                    binding,
                    (
                        _limit_diagnostic(
                            "max_single_source_bytes",
                            len(content),
                            limits["max_single_source_bytes"],
                        ),
                    ),
                )
            )
        if total_bytes + len(content) > limits["max_total_source_bytes"]:
            return SourceResolutionResult(
                failure=_failure(
                    "PACK_LIMIT_EXCEEDED",
                    binding,
                    (
                        _limit_diagnostic(
                            "max_total_source_bytes",
                            total_bytes + len(content),
                            limits["max_total_source_bytes"],
                        ),
                    ),
                )
            )

        expected = (
            binding["pems_sha256"]
            if binding["source_class"] == "canonical_state"
            else binding["raw_sha256"]
        ).lower()
        actual = "sha256:" + sha256(content).hexdigest()
        if actual != expected:
            code = (
                "CANONICAL_STATE_STALE"
                if binding["source_class"] == "canonical_state"
                else "SOURCE_DIGEST_MISMATCH"
            )
            return SourceResolutionResult(
                failure=_failure(
                    code,
                    binding,
                    (f"expected_digest={expected}", f"actual_digest={actual}"),
                )
            )

        total_bytes += len(content)
        resolved.append(ResolvedSource(binding=binding, content=content))

    return SourceResolutionResult(sources=tuple(resolved))


def _preflight(
    request: Mapping[str, Any], profile: Mapping[str, Any]
) -> Mapping[str, Any] | None:
    if request.get("contract") != REQUEST_CONTRACT:
        return _failure(
            "SOURCE_IDENTITY_INVALID", diagnostics=("invalid request contract",)
        )
    if profile.get("contract") != PROFILE_CONTRACT:
        return _failure(
            "SOURCE_IDENTITY_INVALID", diagnostics=("invalid profile contract",)
        )
    if (
        not isinstance(request.get("source_bindings"), list)
        or not request["source_bindings"]
    ):
        return _failure(
            "SOURCE_IDENTITY_INVALID",
            diagnostics=("source_bindings must be non-empty",),
        )
    try:
        limits = profile["limits"]["source_resolution"]
        for name in (
            "max_bindings",
            "max_single_source_bytes",
            "max_total_source_bytes",
        ):
            if (
                not isinstance(limits[name], int)
                or isinstance(limits[name], bool)
                or limits[name] < 1
            ):
                return _failure(
                    "SOURCE_IDENTITY_INVALID",
                    diagnostics=(f"invalid source-resolution limit: {name}",),
                )
    except (KeyError, TypeError):
        return _failure(
            "SOURCE_IDENTITY_INVALID",
            diagnostics=("source-resolution limits missing",),
        )
    return None


def _validate_binding_set(
    request: Mapping[str, Any],
    profile: Mapping[str, Any],
    bindings: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    by_key: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    canonical_by_address: dict[tuple[Any, ...], tuple[Any, ...]] = {}
    complete_by_snapshot: dict[tuple[Any, ...], Mapping[str, Any]] = {}

    for binding in bindings:
        code = _validate_binding(binding)
        if code:
            return _failure(code, binding)
        key = _logical_key(binding)
        by_key.setdefault(key, []).append(binding)

        snapshot_key = _snapshot_key(binding)
        prior_complete = complete_by_snapshot.setdefault(snapshot_key, binding)
        if prior_complete is not binding and not _same_binding(prior_complete, binding):
            return _failure(
                "CROSS_SOURCE_CONSISTENCY_UNPROVEN",
                binding,
                ("non-equivalent complete bindings share one snapshot reference",),
            )

        if binding["source_class"] == "canonical_state":
            address = _canonical_address(binding)
            fingerprint = _fingerprint(binding)
            prior = canonical_by_address.setdefault(address, fingerprint)
            if prior != fingerprint:
                return _failure("CANONICAL_BINDING_CONFLICT", binding)

    multiple_enabled = (
        profile["knowledge"].get("snapshot_multiplicity") == "explicit_request"
    )
    allowed = (
        {
            _source_ref_tuple(ref)
            for ref in request.get("multiple_snapshot_sources", [])
            if isinstance(ref, Mapping)
        }
        if multiple_enabled
        else set()
    )

    for group in by_key.values():
        classes = {item["source_class"] for item in group}
        if len(classes) > 1:
            return _failure("SOURCE_CLASS_CONFLICT", group[0])
        source_ref = _source_ref_tuple(group[0])
        if (
            len({_fingerprint(item) for item in group}) > 1
            and source_ref not in allowed
        ):
            return _failure("LOGICAL_SOURCE_CONFLICT", group[0])

    for binding in bindings:
        if binding["source_class"] != "canonical_state":
            continue
        failure = _canonical_standing_failure(
            binding,
            request.get("accepted_canonical_standing", []),
            allow_multiple=(_source_ref_tuple(binding) in allowed),
        )
        if failure:
            return failure
    return None


def _validate_request_references(
    request: Mapping[str, Any],
    profile: Mapping[str, Any],
    bindings: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    slot_bindings = request.get("slot_bindings", [])
    if not isinstance(slot_bindings, list):
        return _failure(
            "SOURCE_IDENTITY_INVALID", diagnostics=("slot_bindings must be an array",)
        )

    control_slots = {
        slot["slot_id"]: slot
        for slot in profile["source_requirements"].get("control_slots", [])
    }
    evidence_slots = {
        slot["slot_id"]: slot
        for slot in profile["source_requirements"].get(
            "operational_evidence_slots", []
        )
    }

    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for item in slot_bindings:
        if not isinstance(item, Mapping):
            return _failure(
                "SOURCE_IDENTITY_INVALID",
                diagnostics=("slot binding is not an object",),
            )
        plane = item.get("plane")
        slot_id = item.get("slot_id")
        if plane not in {"control", "operational_evidence"} or not isinstance(
            slot_id, str
        ):
            return _failure(
                "SOURCE_IDENTITY_INVALID", diagnostics=("invalid slot binding",)
            )
        grouped.setdefault((plane, slot_id), []).append(item)

    for slot_id, slot in control_slots.items():
        entries = grouped.get(("control", slot_id), [])
        failure = _cardinality_failure(
            entries, slot["cardinality"], "MISSING_REQUIRED_CONTROL"
        )
        if failure:
            return failure
        for entry in entries:
            binding = _find_binding(entry.get("source_ref"), bindings)
            if binding is None or binding["source_class"] not in set(
                slot["source_classes"]
            ):
                return _failure("CONTROL_SOURCE_INVALID")
    for (plane, slot_id), entries in grouped.items():
        if plane == "control" and slot_id not in control_slots and entries:
            return _failure(
                "CONTROL_SOURCE_INVALID",
                diagnostics=(f"unknown control slot_id={slot_id}",),
            )

    for slot_id, slot in evidence_slots.items():
        entries = grouped.get(("operational_evidence", slot_id), [])
        failure = _cardinality_failure(
            entries,
            slot["cardinality"],
            "MISSING_REQUIRED_OPERATIONAL_EVIDENCE",
        )
        if failure:
            return failure
        accepted = set(slot["accepted_statuses"])
        for entry in entries:
            binding = _find_binding(entry.get("source_ref"), bindings)
            if (
                binding is None
                or binding["source_class"] != "operational_evidence"
                or binding.get("validation_status") not in accepted
            ):
                return _failure("OPERATIONAL_EVIDENCE_IDENTITY_INVALID")
    for (plane, slot_id), entries in grouped.items():
        if (
            plane == "operational_evidence"
            and slot_id not in evidence_slots
            and entries
        ):
            return _failure(
                "OPERATIONAL_EVIDENCE_IDENTITY_INVALID",
                diagnostics=(f"unknown operational evidence slot_id={slot_id}",),
            )

    selection = request.get("knowledge_selection", {})
    snapshots = (
        selection.get("snapshots", []) if isinstance(selection, Mapping) else []
    )
    for item in snapshots:
        if not isinstance(item, Mapping):
            return _failure("CANONICAL_BINDING_UNPROVEN")
        binding = _find_binding(item.get("canonical_snapshot_ref"), bindings)
        if binding is None or binding["source_class"] != "canonical_state":
            return _failure("CANONICAL_BINDING_UNPROVEN")

    for requirement in request.get("consistency_requirements", []):
        if not isinstance(requirement, Mapping):
            return _failure("CROSS_SOURCE_CONSISTENCY_UNPROVEN")
        left = _find_binding(requirement.get("left_snapshot_ref"), bindings)
        right = _find_binding(requirement.get("right_snapshot_ref"), bindings)
        if left is None or right is None:
            return _failure("CROSS_SOURCE_CONSISTENCY_UNPROVEN")
        predicate = requirement.get("predicate")
        if predicate == "same_project_identity":
            if (
                not left.get("project_id")
                or left.get("project_id") != right.get("project_id")
            ):
                return _failure("CROSS_SOURCE_CONSISTENCY_UNPROVEN")
        elif predicate == "canonical_declares_repository_snapshot":
            if (
                left["source_class"] != "canonical_state"
                or right["source_class"] != "repository_control"
            ):
                return _failure("CROSS_SOURCE_CONSISTENCY_UNPROVEN")
            relation = left.get("repository_relationship")
            if not isinstance(relation, Mapping):
                return _failure("CROSS_SOURCE_CONSISTENCY_UNPROVEN")
            if (
                relation.get("repository") != right.get("repository")
                or _lower_hex(relation.get("commit"))
                != _lower_hex(right.get("commit"))
            ):
                return _failure("CROSS_SOURCE_CONSISTENCY_UNPROVEN")
        else:
            return _failure("CROSS_SOURCE_CONSISTENCY_UNPROVEN")
    return None


def _validate_adapter_result(
    requested: Mapping[str, Any], result: Any
) -> Mapping[str, Any] | None:
    if not isinstance(result, AdapterResult) or result.status not in ADAPTER_STATUSES:
        return _failure(
            _invalid_resolution_code(requested),
            requested,
            ("invalid adapter result",),
        )

    if result.status in {"missing", "mutable"}:
        return _failure(
            "IMMUTABLE_SNAPSHOT_UNAVAILABLE",
            requested,
            result.diagnostics or (f"adapter_status={result.status}",),
        )
    if result.status in {"unsafe", "ambiguous"}:
        return _failure(
            _invalid_resolution_code(requested),
            requested,
            result.diagnostics or (f"adapter_status={result.status}",),
        )

    if result.binding is None or not _same_binding(requested, result.binding):
        return _failure(
            _invalid_resolution_code(requested),
            requested,
            ("adapter resolved a different binding",),
        )
    if not isinstance(result.content, bytes):
        return _failure(
            _invalid_resolution_code(requested),
            requested,
            ("adapter content must be raw bytes",),
        )
    return None


def _validate_binding(binding: Mapping[str, Any]) -> str | None:
    if not isinstance(binding, Mapping):
        return "SOURCE_IDENTITY_INVALID"
    if binding.get("contract") != BINDING_CONTRACT:
        return "SOURCE_IDENTITY_INVALID"
    source_class = binding.get("source_class")
    if source_class not in SOURCE_CLASSES:
        return "UNSUPPORTED_SOURCE_CLASS"
    if not _nonempty(binding.get("logical_namespace")) or not _nonempty(
        binding.get("logical_source_id")
    ):
        return "SOURCE_IDENTITY_INVALID"

    if source_class == "repository_control":
        if not isinstance(binding.get("commit"), str) or not _HEX40.fullmatch(
            binding["commit"]
        ):
            return "IMMUTABLE_SNAPSHOT_UNAVAILABLE"
        if not isinstance(binding.get("repository"), str) or not _REPOSITORY.fullmatch(
            binding["repository"]
        ):
            return "CONTROL_SOURCE_INVALID"
        path = binding.get("path")
        if (
            not _nonempty(path)
            or path.startswith("/")
            or "\\" in path
            or any(part == ".." for part in path.split("/"))
        ):
            return "CONTROL_SOURCE_INVALID"
        if not _valid_sha(binding.get("raw_sha256")):
            return "CONTROL_SOURCE_INVALID"

    elif source_class == "package_control":
        if not _nonempty(binding.get("immutable_package_snapshot_id")):
            return "IMMUTABLE_SNAPSHOT_UNAVAILABLE"
        if any(
            not _nonempty(binding.get(field))
            for field in ("project_id", "package_contract", "artifact_locator")
        ) or not _valid_sha(binding.get("raw_sha256")):
            return "CONTROL_SOURCE_INVALID"

    elif source_class == "canonical_state":
        required = (
            "project_id",
            "backend_type",
            "backend_contract",
            "backend_config_identity",
            "immutable_snapshot_id",
        )
        if any(not _nonempty(binding.get(field)) for field in required):
            return "CANONICAL_BINDING_UNPROVEN"
        if (
            binding.get("pems_semantic") != "pems/2"
            or binding.get("serializer") != "jcs/1"
        ):
            return "CANONICAL_BINDING_UNPROVEN"
        if not _valid_sha(binding.get("pems_sha256")):
            return "CANONICAL_BINDING_UNPROVEN"
        standing = binding.get("standing_evidence")
        if not isinstance(standing, list) or not standing:
            return "CANONICAL_BINDING_UNPROVEN"
        for item in standing:
            if (
                not isinstance(item, Mapping)
                or not _nonempty(item.get("contract"))
                or not _nonempty(item.get("immutable_snapshot_id"))
                or not _valid_sha(item.get("raw_sha256"))
            ):
                return "CANONICAL_BINDING_UNPROVEN"
        cove = binding.get("cove")
        if cove is not None and (
            not isinstance(cove, Mapping)
            or cove.get("cove_semantic") != "cove/1"
            or cove.get("pems_semantic") != "pems/2"
            or cove.get("serializer") != "jcs/1"
            or not _valid_sha(cove.get("raw_sha256"))
        ):
            return "CANONICAL_BINDING_UNPROVEN"
        relation = binding.get("repository_relationship")
        if relation is not None and (
            not isinstance(relation, Mapping)
            or not isinstance(relation.get("repository"), str)
            or not _REPOSITORY.fullmatch(relation["repository"])
            or not isinstance(relation.get("commit"), str)
            or not _HEX40.fullmatch(relation["commit"])
        ):
            return "CANONICAL_BINDING_UNPROVEN"

    else:
        if (
            not _nonempty(binding.get("artifact_contract"))
            or not _nonempty(binding.get("immutable_snapshot_id"))
            or not _valid_sha(binding.get("raw_sha256"))
            or binding.get("validation_status") not in VALIDATION_STATUSES
        ):
            return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
        result = binding.get("validation_result")
        if binding["validation_status"] == "accepted_validation_result":
            if (
                not isinstance(result, Mapping)
                or any(
                    not _nonempty(result.get(field))
                    for field in (
                        "contract",
                        "validator_contract",
                        "immutable_snapshot_id",
                    )
                )
                or not _valid_sha(result.get("raw_sha256"))
            ):
                return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
        elif result is not None:
            return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
    return None


def _canonical_standing_failure(
    binding: Mapping[str, Any],
    conditions: Sequence[Mapping[str, Any]],
    *,
    allow_multiple: bool,
) -> Mapping[str, Any] | None:
    relevant = [
        item
        for item in conditions
        if isinstance(item, Mapping)
        and _source_ref_tuple(item.get("canonical_ref", {}))
        == _source_ref_tuple(binding)
    ]
    if not relevant:
        return _failure("CANONICAL_BINDING_UNPROVEN", binding)

    address = _canonical_address(binding)
    fingerprint = _fingerprint(binding)
    exact = False
    for item in relevant:
        if item.get("condition") != "accepted_project_backend_canonical_standing":
            continue
        candidate_address = _canonical_address_from_object(
            item.get("canonical_snapshot_address")
        )
        if candidate_address == address:
            candidate_fingerprint = _canonical_fingerprint_from_object(
                item.get("canonical_fingerprint")
            )
            if candidate_fingerprint != fingerprint:
                return _failure("CANONICAL_BINDING_CONFLICT", binding)
            exact = True
        elif not allow_multiple:
            return _failure("CANONICAL_BINDING_CONFLICT", binding)
    return None if exact else _failure("CANONICAL_BINDING_CONFLICT", binding)


def _cardinality_failure(
    entries: Sequence[Mapping[str, Any]], cardinality: str, missing_code: str
) -> Mapping[str, Any] | None:
    if cardinality == "exactly_one":
        if len(entries) == 0:
            return _failure(missing_code)
        if len(entries) != 1:
            code = (
                "CONTROL_SOURCE_INVALID"
                if missing_code == "MISSING_REQUIRED_CONTROL"
                else "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
            )
            return _failure(code, diagnostics=("slot cardinality exceeded",))
    elif cardinality == "one_or_more" and len(entries) == 0:
        return _failure(missing_code)
    elif cardinality not in {"one_or_more", "zero_or_more"}:
        return _failure(
            "SOURCE_IDENTITY_INVALID", diagnostics=("invalid slot cardinality",)
        )
    return None


def _find_binding(
    snapshot_ref: Any, bindings: Sequence[Mapping[str, Any]]
) -> Mapping[str, Any] | None:
    if not isinstance(snapshot_ref, Mapping):
        return None
    try:
        wanted = _snapshot_key(snapshot_ref)
    except (KeyError, TypeError):
        return None
    matches = [item for item in bindings if _snapshot_key(item) == wanted]
    if not matches:
        return None
    if any(not _same_binding(matches[0], item) for item in matches[1:]):
        return None
    return matches[0]


def _snapshot_key(binding: Mapping[str, Any]) -> tuple[Any, ...]:
    return (_source_ref_tuple(binding), _fingerprint(binding))


def _complete_binding_key(binding: Mapping[str, Any]) -> tuple[Any, ...]:
    relation = None
    if binding.get("source_class") == "canonical_state":
        item = binding.get("repository_relationship")
        if isinstance(item, Mapping):
            relation = (item.get("repository"), _lower_hex(item.get("commit")))
    return (_snapshot_key(binding), relation)


def _logical_key(binding: Mapping[str, Any]) -> tuple[str, str]:
    return (binding["logical_namespace"], binding["logical_source_id"])


def _source_ref_tuple(binding: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    return (
        binding.get("source_class"),
        binding.get("logical_namespace"),
        binding.get("logical_source_id"),
    )


def _source_ref(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_class": binding.get("source_class"),
        "logical_namespace": binding.get("logical_namespace"),
        "logical_source_id": binding.get("logical_source_id"),
    }


def _canonical_address(binding: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        binding.get("project_id"),
        binding.get("backend_type"),
        binding.get("backend_contract"),
        binding.get("backend_config_identity"),
        binding.get("immutable_snapshot_id"),
    )


def _standing_identity_set(binding: Mapping[str, Any]) -> tuple[tuple[Any, ...], ...]:
    identities = {
        (
            item.get("contract"),
            item.get("immutable_snapshot_id"),
            _lower_hex(item.get("raw_sha256")),
        )
        for item in binding.get("standing_evidence", [])
    }
    return tuple(sorted(identities))


def _cove_identity(binding: Mapping[str, Any]) -> tuple[Any, ...] | None:
    item = binding.get("cove")
    if item is None:
        return None
    return (
        item.get("cove_semantic"),
        item.get("pems_semantic"),
        item.get("serializer"),
        _lower_hex(item.get("raw_sha256")),
    )


def _validation_result_identity(binding: Mapping[str, Any]) -> tuple[Any, ...] | None:
    item = binding.get("validation_result")
    if item is None:
        return None
    return (
        item.get("contract"),
        item.get("validator_contract"),
        item.get("immutable_snapshot_id"),
        _lower_hex(item.get("raw_sha256")),
    )


def _fingerprint(binding: Mapping[str, Any]) -> tuple[Any, ...]:
    source_class = binding["source_class"]
    if source_class == "repository_control":
        return (
            binding.get("repository"),
            _lower_hex(binding.get("commit")),
            binding.get("path"),
            _lower_hex(binding.get("raw_sha256")),
        )
    if source_class == "package_control":
        return (
            binding.get("project_id"),
            binding.get("package_contract"),
            binding.get("immutable_package_snapshot_id"),
            binding.get("artifact_locator"),
            _lower_hex(binding.get("raw_sha256")),
        )
    if source_class == "canonical_state":
        return (
            binding.get("project_id"),
            binding.get("backend_type"),
            binding.get("backend_contract"),
            binding.get("backend_config_identity"),
            binding.get("immutable_snapshot_id"),
            binding.get("pems_semantic"),
            binding.get("serializer"),
            _lower_hex(binding.get("pems_sha256")),
            _cove_identity(binding),
            _standing_identity_set(binding),
        )
    return (
        binding.get("artifact_contract"),
        binding.get("immutable_snapshot_id"),
        _lower_hex(binding.get("raw_sha256")),
        binding.get("validation_status"),
        _validation_result_identity(binding),
    )


def _same_binding(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if left.get("contract") != right.get("contract"):
        return False
    if _source_ref_tuple(left) != _source_ref_tuple(right):
        return False
    try:
        if _fingerprint(left) != _fingerprint(right):
            return False
    except (KeyError, TypeError):
        return False
    if left.get("source_class") == "canonical_state":
        left_relation = left.get("repository_relationship")
        right_relation = right.get("repository_relationship")
        if left_relation is None or right_relation is None:
            return left_relation is right_relation
        return (
            left_relation.get("repository") == right_relation.get("repository")
            and _lower_hex(left_relation.get("commit"))
            == _lower_hex(right_relation.get("commit"))
        )
    return True


def _canonical_address_from_object(value: Any) -> tuple[Any, ...] | None:
    if not isinstance(value, Mapping):
        return None
    return (
        value.get("project_id"),
        value.get("backend_type"),
        value.get("backend_contract"),
        value.get("backend_config_identity"),
        value.get("immutable_snapshot_id"),
    )


def _canonical_fingerprint_from_object(value: Any) -> tuple[Any, ...] | None:
    if not isinstance(value, Mapping):
        return None
    return (
        value.get("project_id"),
        value.get("backend_type"),
        value.get("backend_contract"),
        value.get("backend_config_identity"),
        value.get("immutable_snapshot_id"),
        value.get("pems_semantic"),
        value.get("serializer"),
        _lower_hex(value.get("pems_sha256")),
        _cove_identity(value),
        _standing_identity_set(value),
    )


def _invalid_resolution_code(binding: Mapping[str, Any]) -> str:
    source_class = binding.get("source_class")
    if source_class in CONTROL_CLASSES:
        return "CONTROL_SOURCE_INVALID"
    if source_class == "canonical_state":
        return "CANONICAL_BINDING_UNPROVEN"
    if source_class == "operational_evidence":
        return "OPERATIONAL_EVIDENCE_IDENTITY_INVALID"
    return "SOURCE_IDENTITY_INVALID"


def _failure(
    code: str,
    binding: Mapping[str, Any] | None = None,
    diagnostics: Sequence[str] = (),
) -> Mapping[str, Any]:
    value: dict[str, Any] = {
        "contract": FAILURE_CONTRACT,
        "code": code,
        "stage": "source_resolution",
    }
    if binding is not None and all(
        binding.get(field) is not None
        for field in ("source_class", "logical_namespace", "logical_source_id")
    ):
        value["source_ref"] = _source_ref(binding)
    if diagnostics:
        value["diagnostics"] = [str(item) for item in diagnostics]
    return value


def _limit_diagnostic(metric: str, actual: int, limit: int) -> str:
    return f"source_resolution.{metric}: actual={actual} limit={limit}"


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _lower_hex(value: Any) -> Any:
    return value.lower() if isinstance(value, str) else value
