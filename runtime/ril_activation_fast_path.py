#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import ril_activation as activation
import ril_mutation as mutation

FAST_PATH_CONTRACT = "reasoning-distiller-ril-activation-fast-path/1"


def run_activation(
    project_root: Path,
    role_id: str,
    scope: str,
    invocation_id: str,
    source: str,
) -> dict[str, Any]:
    """Construct and validate one explicit activation without persisting it."""
    artifact = activation.make_explicit_activation(role_id, invocation_id, source)
    validation = activation.validate_activation(project_root, scope, artifact)
    return {
        "contract": FAST_PATH_CONTRACT,
        "activation": artifact,
        "activation_digest": mutation.digest(artifact),
        "validation": validation,
    }
