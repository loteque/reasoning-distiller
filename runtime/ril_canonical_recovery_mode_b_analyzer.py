#!/usr/bin/env python3
"""Pure/read-only Mode B damage analysis and evidence inventory construction.

The analyzer reads an exact PEMS/COVE pair and immutable repository evidence.
It never constructs semantic values, a disposition, candidate, proof, plan, or
approval, and it has no persistence or canonical-store mutation entry point.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from ril_admission import _decode, encode_cove, jcs, normalize_pems
from ril_mutation import ContractError, canonical_json_bytes

ANALYSIS_CONTRACT = "reasoning-distiller-canonical-recovery-damage-analysis/1"
INVENTORY_CONTRACT = "reasoning-distiller-canonical-recovery-evidence-inventory/1"
PROFILE_ID = "reasoning-distiller-project-a0-missing-relation-fields/1"
_CLOSED_MISSING_FIELDS = frozenset({"lifecycle", "data"})
_RELATION_KEYS = frozenset({"id", "kind", "from", "to"})
_INCIDENT_PEMS_SHA256 = "22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061"
_INCIDENT_COVE_SHA256 = "ce1f6dd7fe8889ce1bf126f7ec161b08fdc19a1705a2d5be350ed80b7d197e24"
_INCIDENT_PROJECT_ID = "reasoning-distiller"
_INCIDENT_RECORD_COUNT = 802
_INCIDENT_RELATION_KINDS = {"supports": 661, "depends_on": 7}
_INCIDENT_SOURCE_COMMIT = "95a65e2e036879ce1c7aadc22b19dd5da07106a3"
_INCIDENT_SOURCE_PATH_BLOBS = (
    (
        "3516c8bd4c27c38b6eedd800ec125760d2df0306a02d0522db867436e1e12fc6",
        "bb7c474e935243b45ff02a5778a94bbcdc654d72",
    ),
    (
        "5cded72584ab98f7eb1d560c9160bf393fa3a29e57337e1fb08248f5ac1eb41b",
        "7ff52fb925a667c4cc1782da9b475dff831e45ef",
    ),
    (
        "5ee8f71a289b134c0064db792253da9ff5002f7d2dd1eed33fa397be70e4ddcd",
        "a760dba6e9daf4f7f6262ff5992cfb6bbdb178e2",
    ),
)
_BLOCKED_CHECKS = (
    "relation lifecycle vocabulary and lifecycle-dependent semantics",
    "relation data schema and kind-specific semantic values",
    "depends_on dependency_kind semantic validity",
)


@dataclass(frozen=True)
class EvidenceSpec:
    path: str
    provenance: str


@dataclass(frozen=True)
class ModeBDamageArtifacts:
    analysis: dict[str, Any]
    analysis_bytes: bytes
    analysis_sha256: str
    inventory: dict[str, Any]
    inventory_bytes: bytes
    inventory_sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _strict_json(data: bytes, label: str) -> Any:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError("MODE_B_PRESTATE_INVALID", f"{label}: invalid UTF-8: {exc}") from exc

    def pairs(pairs_: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs_:
            if key in result:
                raise ValueError(f"duplicate object key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-JSON constant: {value}")),
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ContractError("MODE_B_PRESTATE_INVALID", f"{label}: {exc}") from exc


def _ordinary_bytes(root: Path, relative: str) -> bytes:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise ContractError("MODE_B_EVIDENCE_INVALID", f"not an ordinary file: {relative}")
    return path.read_bytes()


def _tracked_blob(root: Path, data: bytes) -> str | None:
    identity = _git_blob(data)
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{identity}^{{blob}}"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return identity if completed.returncode == 0 else None


def _verify_source_defect(root: Path, commit: str, paths: tuple[str, ...]) -> None:
    if commit != _INCIDENT_SOURCE_COMMIT:
        raise ContractError("MODE_B_EVIDENCE_INVALID", "source defect commit is not the selected incident source")
    if not paths or len(paths) != len(set(paths)):
        raise ContractError("MODE_B_EVIDENCE_INVALID", "source defect paths must be nonempty and unique")
    path_digests = tuple(_sha256(path.encode("utf-8")) for path in paths)
    if path_digests != tuple(binding[0] for binding in _INCIDENT_SOURCE_PATH_BLOBS):
        raise ContractError(
            "MODE_B_EVIDENCE_INVALID",
            "source defect paths do not match the selected incident source",
        )
    for path, (_path_digest, expected_blob) in zip(paths, _INCIDENT_SOURCE_PATH_BLOBS, strict=True):
        raw = _ordinary_bytes(root, path)
        if _git_blob(raw) != expected_blob or _tracked_blob(root, raw) != expected_blob:
            raise ContractError(
                "MODE_B_EVIDENCE_INVALID",
                f"source-defect path/blob does not match the selected incident source: {path}",
            )


def _identity(root: Path, relative: str, data: bytes) -> dict[str, str]:
    result = {"path": relative, "sha256": _sha256(data)}
    blob = _tracked_blob(root, data)
    if blob is not None:
        result["git_blob"] = blob
    return result


def _pointer(parts: Iterable[Any]) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "" if not encoded else "/" + "/".join(encoded)


def _schema_defects(document: Any, validator: Draft202012Validator) -> list[dict[str, str]]:
    defects: set[tuple[str, str, str]] = set()
    for error in validator.iter_errors(document):
        if error.validator == "required" and isinstance(error.instance, dict):
            missing = sorted(set(error.validator_value) - set(error.instance))
            for name in missing:
                defects.add((_pointer([*error.absolute_path, name]), "required", "required property absent"))
        else:
            defects.add((_pointer(error.absolute_path), str(error.validator), error.message))
    return [
        {"instance_path": path, "keyword": keyword, "message": message}
        for path, keyword, message in sorted(defects)
    ]


def _check(check_id: str, passed: bool, detail: str) -> dict[str, str]:
    return {"id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail}


def _blocked(check_id: str, detail: str) -> dict[str, str]:
    return {"id": check_id, "status": "BLOCKED", "detail": detail}


def _load_schema_validator(root: Path, schema_path: str) -> tuple[Draft202012Validator, bytes]:
    schema_bytes = _ordinary_bytes(root, schema_path)
    schema = _strict_json(schema_bytes, schema_path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema), schema_bytes


def build_damage_artifacts(
    project_root: Path,
    *,
    pems_path: str,
    cove_path: str,
    pems_schema_path: str,
    semantic_validator_path: str,
    normalizer_path: str,
    cove_codec_path: str,
    historical_evidence: Iterable[EvidenceSpec],
    source_defect_commit: str,
    source_defect_paths: Iterable[str],
) -> ModeBDamageArtifacts:
    """Build deterministic artifacts without writing any file or state."""
    root = project_root.resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", source_defect_commit):
        raise ContractError("MODE_B_EVIDENCE_INVALID", "source defect commit must be an exact SHA")
    defect_paths = tuple(source_defect_paths)
    _verify_source_defect(root, source_defect_commit, defect_paths)

    pems_bytes = _ordinary_bytes(root, pems_path)
    cove_bytes = _ordinary_bytes(root, cove_path)
    pems = _strict_json(pems_bytes, pems_path)
    cove = _strict_json(cove_bytes, cove_path)
    if not isinstance(pems, dict) or not isinstance(cove, dict):
        raise ContractError("MODE_B_PRESTATE_INVALID", "PEMS and COVE must be JSON objects")

    validator, schema_bytes = _load_schema_validator(root, pems_schema_path)
    semantic_validator_bytes = _ordinary_bytes(root, semantic_validator_path)
    normalizer_bytes = _ordinary_bytes(root, normalizer_path)
    codec_bytes = _ordinary_bytes(root, cove_codec_path)
    defects = _schema_defects(pems, validator)

    try:
        decoded = _decode(cove["x"], cove["d"], cove["h"])
        tuple_valid = (
            set(cove) == {"c", "p", "s", "d", "h", "x"}
            and cove.get("c") == "cove/1"
            and cove.get("p") == "pems/2"
            and cove.get("s") == "jcs/1"
            and encode_cove(decoded) == cove
        )
        cove_canonical = jcs(cove) == cove_bytes
    except (KeyError, IndexError, TypeError, ValueError, ContractError):
        decoded, tuple_valid, cove_canonical = None, False, False
    decode_equal = tuple_valid and cove_canonical and decoded == pems

    records = pems.get("records") if isinstance(pems.get("records"), list) else []
    relations = pems.get("relations") if isinstance(pems.get("relations"), list) else []
    record_ids = [item.get("id") for item in records if isinstance(item, dict)]
    relation_ids = [item.get("id") for item in relations if isinstance(item, dict)]
    record_id_set = {item for item in record_ids if isinstance(item, str)}
    duplicate_records = len(record_ids) != len(set(record_ids))
    duplicate_relations = len(relation_ids) != len(set(relation_ids))
    endpoints_valid = all(
        isinstance(item, dict)
        and item.get("from") in record_id_set
        and item.get("to") in record_id_set
        and item.get("from") != item.get("to")
        for item in relations
    )
    project_id = pems.get("project_id")
    project_matches = sum(
        1 for item in records
        if isinstance(item, dict) and item.get("id") == project_id and item.get("kind") == "project"
    ) == 1
    exact_relation_keys = all(isinstance(item, dict) and set(item) == _RELATION_KEYS for item in relations)
    record_by_id = {
        item.get("id"): item for item in records
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    observation_ids = {
        item_id for item_id, item in record_by_id.items()
        if item.get("kind") == "source_observation"
    }
    source_observations_valid = all(
        item.get("kind") != "source_observation"
        or (
            isinstance(item.get("data"), dict)
            and isinstance(record_by_id.get(item["data"].get("source_id")), dict)
            and record_by_id[item["data"]["source_id"]].get("kind") == "source"
        )
        for item in records if isinstance(item, dict)
    )
    provenance_valid = True
    for item in [*records, *relations]:
        if not isinstance(item, dict):
            provenance_valid = False
            continue
        provenance = item.get("provenance", {})
        if not isinstance(provenance, dict):
            provenance_valid = False
            continue
        for refs in provenance.values():
            if not isinstance(refs, list) or any(ref not in observation_ids for ref in refs):
                provenance_valid = False
    derived_ids = {
        item_id for item_id, item in record_by_id.items()
        if item.get("kind") == "proposition"
        and isinstance(item.get("data"), dict)
        and item["data"].get("epistemic_role") == "derived"
    }
    derived_sources = {
        item.get("from") for item in relations
        if isinstance(item, dict) and item.get("kind") == "derived_from"
    }
    derived_integrity = derived_ids <= derived_sources
    contradiction_pairs: list[tuple[Any, Any]] = [
        (item.get("from"), item.get("to")) for item in relations
        if isinstance(item, dict) and item.get("kind") == "contradicts"
    ]
    contradiction_integrity = (
        all(left < right for left, right in contradiction_pairs if isinstance(left, str) and isinstance(right, str))
        and len(contradiction_pairs) == len(set(contradiction_pairs))
    )
    kind_counts: dict[str, int] = {}
    for item in relations:
        if isinstance(item, dict) and isinstance(item.get("kind"), str):
            kind_counts[item["kind"]] = kind_counts.get(item["kind"], 0) + 1

    try:
        normalized = normalize_pems(copy.deepcopy(pems))
        normalized_bytes = jcs(normalized)
        normalized_record_ids = [item.get("id") for item in normalized["records"]]
        normalized_relation_ids = [item.get("id") for item in normalized["relations"]]
        semantic_content_changed = sorted(records, key=lambda item: item.get("id", "")) != normalized["records"] or sorted(relations, key=lambda item: item.get("id", "")) != normalized["relations"]
    except (ContractError, TypeError, AttributeError):
        normalized_bytes = b""
        normalized_record_ids = []
        normalized_relation_ids = []
        semantic_content_changed = True

    evidence_rows = []
    evidence_specs = sorted(tuple(historical_evidence), key=lambda item: item.path)
    if len({item.path for item in evidence_specs}) != len(evidence_specs):
        raise ContractError("MODE_B_EVIDENCE_INVALID", "historical evidence paths must be unique")
    for spec in evidence_specs:
        raw = _ordinary_bytes(root, spec.path)
        row: dict[str, str] = {"path": spec.path, "sha256": _sha256(raw), "provenance": spec.provenance}
        blob = _tracked_blob(root, raw)
        if blob is not None:
            row["git_blob"] = blob
        evidence_rows.append(row)

    relation_inventory = [
        {
            "index": index,
            "id": item.get("id", "") if isinstance(item, dict) else "",
            "from": item.get("from", "") if isinstance(item, dict) else "",
            "to": item.get("to", "") if isinstance(item, dict) else "",
            "kind": item.get("kind", "") if isinstance(item, dict) else "",
            "key_set": sorted(item) if isinstance(item, dict) else [],
        }
        for index, item in enumerate(relations)
    ]
    record_inventory = [
        {
            "index": index,
            "id": item.get("id", "") if isinstance(item, dict) else "",
            "kind": item.get("kind", "") if isinstance(item, dict) else "",
            "key_set": sorted(item) if isinstance(item, dict) else [],
        }
        for index, item in enumerate(records)
    ]
    checks = [
        _check("strict_json", True, "PEMS and COVE parsed as strict UTF-8 JSON without duplicate keys or non-JSON constants."),
        _check("pems_cove_decode_equality", decode_equal, "COVE tuple, canonical encoding, and exact decoded PEMS equality were checked."),
        _check("record_ids_unique", not duplicate_records, f"observed {len(record_ids)} record IDs"),
        _check("relation_ids_unique", not duplicate_relations, f"observed {len(relation_ids)} relation IDs"),
        _check("relation_endpoints", endpoints_valid, "Every endpoint resolves to a record ID and no relation is self-referential."),
        _check("project_identity", project_matches, "project_id resolves exactly once to a project record."),
        _check("relation_exact_key_sets", exact_relation_keys, "Every relation has exactly id, kind, from, and to."),
        _check("source_observation_sources", source_observations_valid, "Every source_observation source_id resolves to a source record."),
        _check("provenance_references", provenance_valid, "Every typed provenance reference resolves to a source_observation record."),
        _check("derived_proposition_premises", derived_integrity, "Every derived proposition has a derived_from relation."),
        _check("contradiction_integrity", contradiction_integrity, "Contradictions use canonical endpoint order and unique endpoint pairs."),
        _blocked("relation_lifecycle_semantics", "All relation lifecycle values are absent; no value was inferred."),
        _blocked("relation_data_semantics", "All relation data values are absent; no value was inferred."),
        _blocked("depends_on_dependency_kind", "dependency_kind is absent for depends_on relations; no value was inferred."),
    ]

    prestate = {
        "pems": _identity(root, pems_path, pems_bytes),
        "cove": _identity(root, cove_path, cove_bytes),
    }
    inventory = {
        "contract": INVENTORY_CONTRACT,
        "project": {"project_id": project_id if isinstance(project_id, str) else ""},
        "prestate": prestate,
        "records": record_inventory,
        "relations": relation_inventory,
        "checks": checks,
        "normalization": {
            "pems_bytes_are_canonical_jcs": jcs(pems) == pems_bytes,
            "record_order_changed": record_ids != normalized_record_ids,
            "relation_order_changed": relation_ids != normalized_relation_ids,
            "semantic_content_changed": semantic_content_changed,
            "normalized_pems_sha256": _sha256(normalized_bytes),
        },
        "historical_evidence": evidence_rows,
        "source_defect_provenance": {
            "commit": source_defect_commit,
            "paths": list(defect_paths),
            "description": "The selected commit materialized relation objects without lifecycle and data; this records mechanism only and supplies no missing semantic value.",
        },
    }
    inventory_bytes = canonical_json_bytes(inventory)
    inventory_sha = _sha256(inventory_bytes)

    expected_defects = {
        (f"/relations/{index}/{field}", "required")
        for index, item in enumerate(relations)
        if isinstance(item, dict) and set(item) == _RELATION_KEYS
        for field in _CLOSED_MISSING_FIELDS
    }
    actual_defects = {(item["instance_path"], item["keyword"]) for item in defects}
    additional_damage = (
        _sha256(pems_bytes) != _INCIDENT_PEMS_SHA256
        or _sha256(cove_bytes) != _INCIDENT_COVE_SHA256
        or source_defect_commit != _INCIDENT_SOURCE_COMMIT
        or project_id != _INCIDENT_PROJECT_ID
        or len(records) != _INCIDENT_RECORD_COUNT
        or kind_counts != _INCIDENT_RELATION_KINDS
        or pems.get("semantic") != "pems/2"
        or not project_matches
        or not decode_equal
        or duplicate_records
        or duplicate_relations
        or not endpoints_valid
        or not exact_relation_keys
        or not source_observations_valid
        or not provenance_valid
        or not derived_integrity
        or not contradiction_integrity
        or actual_defects != expected_defects
    )
    ordered_relation_set_sha = _sha256(canonical_json_bytes(relation_inventory))
    analysis = {
        "contract": ANALYSIS_CONTRACT,
        "project": {"project_id": project_id if isinstance(project_id, str) else ""},
        "prestate": prestate,
        "semantic": pems.get("semantic"),
        "toolchain": {
            "pems_schema_sha256": _sha256(schema_bytes),
            "semantic_validator_sha256": _sha256(semantic_validator_bytes),
            "normalizer_sha256": _sha256(normalizer_bytes),
            "cove_codec_sha256": _sha256(codec_bytes),
        },
        "damage_set": {
            "profile_id": PROFILE_ID,
            "relation_count": len(relations),
            "ordered_relation_set_sha256": ordered_relation_set_sha,
            "defects": defects,
            "additional_damage": additional_damage,
        },
        "integrity": {
            "pems_cove_decode_equal": decode_equal,
            "duplicate_relation_ids": duplicate_relations,
            "endpoints_valid": endpoints_valid,
        },
        "blocked_checks": list(_BLOCKED_CHECKS),
        "evidence_inventory": {
            "path": f"project-knowledge/recovery/canonical-pems-cove-mode-b/evidence-inventories/{inventory_sha}.json",
            "sha256": inventory_sha,
        },
        "candidate_count": 0,
    }
    analysis_bytes = canonical_json_bytes(analysis)
    return ModeBDamageArtifacts(
        analysis=analysis,
        analysis_bytes=analysis_bytes,
        analysis_sha256=_sha256(analysis_bytes),
        inventory=inventory,
        inventory_bytes=inventory_bytes,
        inventory_sha256=inventory_sha,
    )
