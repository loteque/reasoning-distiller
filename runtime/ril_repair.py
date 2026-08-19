#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.ril_mutation import (
    ContractError,
    canonical_json_bytes,
    digest,
    load_json,
    operation_result,
    replay,
    _write_replace,
)

REPAIR_RESULT_CONTRACT = "reasoning-distiller-repair-result/1"


def ordinary_repair(events_dir: Path, projection_path: Path, initial_state: Any | None = None) -> dict[str, Any]:
    """Validate authoritative history and regenerate derived projection only."""
    try:
        state, events = replay(events_dir, initial_state)
    except ContractError as exc:
        return {
            "contract": REPAIR_RESULT_CONTRACT,
            "status": "FAIL",
            "outcome": "HISTORY_INVALID",
            "reason_code": exc.code,
            "detail": exc.detail,
        }

    expected = canonical_json_bytes(state)
    expected_digest = digest(state)

    if projection_path.exists():
        if not projection_path.is_file() or projection_path.is_symlink():
            return {
                "contract": REPAIR_RESULT_CONTRACT,
                "status": "FAIL",
                "outcome": "PROJECTION_PATH_CONFLICT",
            }
        try:
            projection = load_json(projection_path)
            if digest(projection) == expected_digest:
                return {
                    "contract": REPAIR_RESULT_CONTRACT,
                    "status": "PASS",
                    "outcome": "NO_CHANGE",
                    "event_count": len(events),
                    "projection_digest": expected_digest,
                }
        except ContractError:
            # A malformed/conflicting projection is derived state and is repairable.
            pass

    try:
        _write_replace(projection_path, expected)
    except OSError as exc:
        return {
            "contract": REPAIR_RESULT_CONTRACT,
            "status": "FAIL",
            "outcome": "REPAIR_WRITE_FAILED",
            "detail": str(exc),
        }

    return {
        "contract": REPAIR_RESULT_CONTRACT,
        "status": "PASS",
        "outcome": "REBUILT",
        "event_count": len(events),
        "projection_digest": expected_digest,
    }
