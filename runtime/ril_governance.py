#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_SPEC = importlib.util.spec_from_file_location("ril_mutation_shared", Path(__file__).with_name("ril_mutation.py"))
_mut = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_mut)

ContractError = _mut.ContractError
canonical_json_bytes = _mut.canonical_json_bytes
digest = _mut.digest

PROVENANCE_CONTRACT = "reasoning-distiller-provenance/1"

# Fail-closed registry: absence means non-delegable.
DELEGATION_REGISTRY: dict[str, dict[str, Any]] = {
    "role-registry.change": {
        "delegable": True,
        "target_fields": ["role_id"],
        "selectors": {"role_id": ["exact", "one-of"]},
    },
    "operator-registry.disable": {
        "delegable": True,
        "target_fields": ["operator_id"],
        "selectors": {"operator_id": ["exact", "one-of"]},
        "constraints": {"operation": ["eq"]},
    },
}


def delegation_metadata(operation_class: str) -> dict[str, Any]:
    metadata = DELEGATION_REGISTRY.get(operation_class)
    if metadata is None:
        return {"operation_class": operation_class, "delegable": False}
    return {"operation_class": operation_class, **metadata}


def make_provenance(subject: str, *, producer: dict[str, Any], runtime: dict[str, Any] | None = None, software: dict[str, Any] | None = None, environment: dict[str, Any] | None = None, extensions: dict[str, Any] | None = None) -> dict[str, Any]:
    if not _typed_reference(subject):
        raise ContractError("INVALID_PROVENANCE_SUBJECT", "subject must be a canonical typed reference")
    value = {
        "contract": PROVENANCE_CONTRACT,
        "subject": subject,
        "producer": producer,
        "runtime": runtime or {},
        "software": software or {},
        "environment": environment or {},
        "extensions": extensions or {},
    }
    validate_provenance(value)
    return value


def validate_provenance(value: dict[str, Any]) -> None:
    required = {"contract", "subject", "producer", "runtime", "software", "environment", "extensions"}
    if not isinstance(value, dict) or set(value) != required or value.get("contract") != PROVENANCE_CONTRACT:
        raise ContractError("INVALID_PROVENANCE", "provenance fields do not match contract")
    if not _typed_reference(value["subject"]):
        raise ContractError("INVALID_PROVENANCE_SUBJECT", "invalid typed subject reference")
    producer = value["producer"]
    if not isinstance(producer, dict) or producer.get("kind") not in {"agent", "human-interface", "automation", "tool"}:
        raise ContractError("INVALID_PROVENANCE", "producer.kind is invalid")
    for key in ("runtime", "software", "environment", "extensions"):
        if not isinstance(value[key], dict):
            raise ContractError("INVALID_PROVENANCE", f"{key} must be an object")
    canonical_json_bytes(value)


def provenance_reference(value: dict[str, Any]) -> str:
    validate_provenance(value)
    return "provenance:" + digest(value).split(":", 1)[1]


def index_provenance(index: dict[str, list[str]], value: dict[str, Any]) -> dict[str, list[str]]:
    """Pure subject index update. It has no authority or subject-state effect."""
    ref = provenance_reference(value)
    result = {k: list(v) for k, v in index.items()}
    refs = result.setdefault(value["subject"], [])
    if ref not in refs:
        refs.append(ref)
        refs.sort()
    return result


def _typed_reference(value: Any) -> bool:
    if not isinstance(value, str) or ":" not in value:
        return False
    kind, ident = value.split(":", 1)
    return bool(kind) and bool(ident) and all(c.isalnum() or c in "-_" for c in kind)
