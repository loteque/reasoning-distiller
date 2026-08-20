#!/usr/bin/env python3
from __future__ import annotations

"""Exact Human confirmation binding for protected ceremonies.

This primitive is intentionally narrower than conversational intent binding.
Generic affirmations never satisfy a protected ceremony. The result records the
exact ceremony and exact proposal reference that the Human confirmation binds.
It creates no authority by itself.
"""

from typing import Any

CONFIRMATION_CONTRACT = "reasoning-distiller-protected-confirmation/1"
PROTECTED_CONFIRMATIONS = frozenset({
    "ESTABLISH_ROOT_OPERATOR",
    "STEWARD_AUTHORIZATION_CHANGE",
})


def bind_exact_confirmation(
    utterance: str,
    *,
    ceremony: str,
    proposal_reference: str,
) -> dict[str, Any]:
    if not isinstance(ceremony, str) or ceremony not in PROTECTED_CONFIRMATIONS:
        return {
            "contract": CONFIRMATION_CONTRACT,
            "status": "STOPPED",
            "outcome": "INVALID_PROTECTED_CEREMONY",
            "ceremony": ceremony,
        }
    if not isinstance(proposal_reference, str) or not proposal_reference.startswith("proposal:") or len(proposal_reference) <= len("proposal:"):
        return {
            "contract": CONFIRMATION_CONTRACT,
            "status": "STOPPED",
            "outcome": "INVALID_PROPOSAL_REFERENCE",
            "ceremony": ceremony,
        }
    if not isinstance(utterance, str) or utterance != ceremony:
        return {
            "contract": CONFIRMATION_CONTRACT,
            "status": "STOPPED",
            "outcome": "HUMAN_CONFIRMATION_REQUIRED",
            "ceremony": ceremony,
            "proposal_reference": proposal_reference,
            "expected_confirmation": ceremony,
        }
    return {
        "contract": CONFIRMATION_CONTRACT,
        "status": "PASS",
        "outcome": "BOUND_PROTECTED_CONFIRMATION",
        "ceremony": ceremony,
        "proposal_reference": proposal_reference,
        "confirmation": utterance,
        "authority_effect": "none",
    }
