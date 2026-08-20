#!/usr/bin/env python3
from __future__ import annotations

"""Shared result adapter for the standalone installer recovery primitive.

The standalone P4 recovery primitive predates the framework-wide PASS/outcome
result convention and returns its successful outcome in ``status``. This adapter
does not inspect journals, choose recovery behavior, or mutate state itself. It
delegates exactly once to the supplied accepted recovery primitive and normalizes
a successful Python return into the common result shape used by lifecycle
orchestration and checkpoints.
"""

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

RECOVERY_RESULT_CONTRACT = "reasoning-distiller-install-recovery-result/1"


def recover_install_transaction(
    recovery_primitive: Callable[[Path, str], dict[str, Any]],
    target: Path,
    managed_root: str = ".reasoning-distiller",
) -> dict[str, Any]:
    """Invoke the accepted recovery primitive exactly once and normalize result shape."""
    if not callable(recovery_primitive):
        raise ValueError("recovery_primitive must be callable")
    raw = recovery_primitive(target, managed_root)
    if not isinstance(raw, dict):
        raise ValueError("recovery primitive result must be an object")
    outcome = raw.get("status")
    if not isinstance(outcome, str) or not outcome:
        raise ValueError("recovery primitive result status is required")
    return {
        "contract": RECOVERY_RESULT_CONTRACT,
        "status": "PASS",
        "outcome": outcome,
        "primitive": "rd_install.recover_interrupted_transaction",
        "primitive_result": deepcopy(raw),
    }
