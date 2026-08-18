#!/usr/bin/env python3
"""Deterministic validator for reasoning-distiller output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

KINDS = {"observation", "decision", "assumption", "uncertainty", "claim"}
PROVENANCE_ROLES = {"primary", "corroborating", "context"}
RELATIONS = {"supports", "contradicts", "depends_on", "supersedes"}

RECORD_KEYS = {"temp_id", "kind", "statement", "premise", "provenance"}
RELATION_KEYS = {"from", "type", "to", "provenance"}
TOP_KEYS = {"records", "relations"}


def _error(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_string_list(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, list) or not value:
        _error(errors, path, "must be a non-empty array")
        return False
    if any(not _nonempty_string(item) for item in value):
        _error(errors, path, "must contain only non-empty strings")
        return False
    if len(value) != len(set(value)):
        _error(errors, path, "must not contain duplicates")
        return False
    return True


def _validate_provenance(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, dict) or not value:
        _error(errors, path, "must be a non-empty object")
        return False
    unknown = set(value) - PROVENANCE_ROLES
    if unknown:
        _error(errors, path, f"unknown fields: {sorted(unknown)}")
    ok = not unknown
    for role, refs in value.items():
        if role in PROVENANCE_ROLES:
            ok = _validate_string_list(refs, f"{path}.{role}", errors) and ok
    return ok


def validate(document: Any) -> list[str]:
    errors: list[str] = []

    if not isinstance(document, dict):
        return ["$: must be an object"]

    unknown = set(document) - TOP_KEYS
    if unknown:
        _error(errors, "$", f"unknown fields: {sorted(unknown)}")

    records = document.get("records")
    if not isinstance(records, list) or not records:
        _error(errors, "$.records", "must be a non-empty array")
        return errors

    relations = document.get("relations")
    if relations is not None and (not isinstance(relations, list) or not relations):
        _error(errors, "$.relations", "must be omitted or be a non-empty array")
        relations = []

    record_by_id: dict[str, dict[str, Any]] = {}

    for index, record in enumerate(records):
        path = f"$.records[{index}]"
        if not isinstance(record, dict):
            _error(errors, path, "must be an object")
            continue

        unknown = set(record) - RECORD_KEYS
        if unknown:
            _error(errors, path, f"unknown fields: {sorted(unknown)}")

        for required in ("temp_id", "kind", "statement"):
            if required not in record:
                _error(errors, path, f"missing required field '{required}'")

        temp_id = record.get("temp_id")
        if not _nonempty_string(temp_id):
            _error(errors, f"{path}.temp_id", "must be a non-empty string")
        elif temp_id in record_by_id:
            _error(errors, f"{path}.temp_id", f"duplicate record id '{temp_id}'")
        else:
            record_by_id[temp_id] = record

        kind = record.get("kind")
        if kind not in KINDS:
            _error(errors, f"{path}.kind", f"must be one of {sorted(KINDS)}")

        if not _nonempty_string(record.get("statement")):
            _error(errors, f"{path}.statement", "must be a non-empty string")

        premise = record.get("premise")
        if premise is not None:
            _validate_string_list(premise, f"{path}.premise", errors)

        provenance = record.get("provenance")
        if provenance is not None:
            _validate_provenance(provenance, f"{path}.provenance", errors)

        if kind == "observation" and premise is None:
            if not isinstance(provenance, dict) or "primary" not in provenance:
                _error(errors, path, "non-derived observations require provenance.primary")

    premise_graph: dict[str, list[str]] = {}
    for record_id, record in record_by_id.items():
        premise = record.get("premise")
        if isinstance(premise, list):
            premise_graph[record_id] = []
            for premise_id in premise:
                if premise_id == record_id:
                    _error(errors, f"record:{record_id}.premise", "must not reference itself")
                elif premise_id not in record_by_id:
                    _error(errors, f"record:{record_id}.premise", f"unknown premise record '{premise_id}'")
                else:
                    premise_graph[record_id].append(premise_id)

    state: dict[str, int] = {}

    def visit(record_id: str, stack: list[str]) -> None:
        mark = state.get(record_id, 0)
        if mark == 1:
            cycle_start = stack.index(record_id) if record_id in stack else 0
            cycle = stack[cycle_start:] + [record_id]
            _error(errors, "premise_graph", f"cycle detected: {' -> '.join(cycle)}")
            return
        if mark == 2:
            return
        state[record_id] = 1
        for premise_id in premise_graph.get(record_id, []):
            if premise_id in premise_graph:
                visit(premise_id, stack + [record_id])
        state[record_id] = 2

    for record_id in premise_graph:
        visit(record_id, [])

    for index, relation in enumerate(relations or []):
        path = f"$.relations[{index}]"
        if not isinstance(relation, dict):
            _error(errors, path, "must be an object")
            continue

        unknown = set(relation) - RELATION_KEYS
        if unknown:
            _error(errors, path, f"unknown fields: {sorted(unknown)}")

        for required in ("from", "type", "to"):
            if required not in relation:
                _error(errors, path, f"missing required field '{required}'")

        source = relation.get("from")
        target = relation.get("to")
        relation_type = relation.get("type")

        if source not in record_by_id:
            _error(errors, f"{path}.from", f"unknown record '{source}'")
        if target not in record_by_id:
            _error(errors, f"{path}.to", f"unknown record '{target}'")
        if source == target and source in record_by_id:
            _error(errors, path, "self-referential relations are forbidden")
        if relation_type not in RELATIONS:
            _error(errors, f"{path}.type", f"must be one of {sorted(RELATIONS)}")

        provenance = relation.get("provenance")
        if provenance is not None:
            _validate_provenance(provenance, f"{path}.provenance", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for path in args.paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            failed = True
            continue

        errors = validate(document)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
