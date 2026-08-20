#!/usr/bin/env python3
from __future__ import annotations

"""Static primitive map for the Rupi lifecycle adapter.

This module is intentionally non-executable and non-authoritative. It freezes the
allowed consequential Rupi action vocabulary and names the one accepted primitive
or shared-orchestration surface that governs each action.
"""

MAP_CONTRACT = "reasoning-distiller-rupi-primitive-map/1"

PRIMITIVE_MAP = {
    "inspect_status": {
        "kind": "read",
        "primitive": "ril_status.classify_status",
    },
    "verify_release_bundle": {
        "kind": "read",
        "primitive": "rd_install.verify_release_bundle",
    },
    "plan_install_transition": {
        "kind": "read",
        "primitive": "rd_install.plan_installation_transition",
    },
    "install_or_update": {
        "kind": "mutation",
        "primitive": "rd_install.install",
    },
    "recover_install_transaction": {
        "kind": "mutation",
        "primitive": "rd_install_recovery.recover_install_transaction",
    },
    "bootstrap_project": {
        "kind": "mutation",
        "primitive": "rd_bootstrap.bootstrap",
    },
    "plan_initial_operator": {
        "kind": "read",
        "primitive": "ril_operators.plan_initial_operator",
    },
    "bind_protected_confirmation": {
        "kind": "intent",
        "primitive": "ril_human_confirmation.bind_exact_confirmation",
    },
    "approve_initial_operator": {
        "kind": "authority",
        "primitive": "ril_operators.approve_initial_operator",
    },
    "apply_initial_operator": {
        "kind": "mutation",
        "primitive": "ril_operators.apply_initial_operator",
    },
    "plan_steward_authorization": {
        "kind": "read",
        "primitive": "ril_steward_authorization.plan_authorization_change",
    },
    "approve_steward_authorization": {
        "kind": "authority",
        "primitive": "ril_steward_authorization.approve_authorization_change",
    },
    "apply_steward_authorization": {
        "kind": "mutation",
        "primitive": "ril_steward_authorization.apply_authorization_change",
    },
    "create_activation": {
        "kind": "evidence",
        "primitive": "ril_activation.make_explicit_activation",
    },
    "validate_activation": {
        "kind": "read",
        "primitive": "ril_activation.validate_activation",
    },
    "repair_projection": {
        "kind": "mutation",
        "primitive": "ril_repair.repair_domain",
    },
    "repair_all_projections": {
        "kind": "mutation",
        "primitive": "ril_repair.repair_all",
    },
    "disclose_bounded_chain": {
        "kind": "presentation",
        "primitive": "ril_human_agent.disclose_bounded_chain",
    },
    "bind_contextual_intent": {
        "kind": "intent",
        "primitive": "ril_human_agent.bind_contextual_intent",
    },
    "present_proposal": {
        "kind": "presentation",
        "primitive": "ril_human_agent.present_proposal",
    },
    "protected_ceremony_boundary": {
        "kind": "presentation",
        "primitive": "ril_human_agent.protected_ceremony_boundary",
    },
    "control_return": {
        "kind": "presentation",
        "primitive": "ril_human_agent.control_return",
    },
}

LEGACY_FORBIDDEN_SURFACES = {
    "rd_steward_setup.run",
    "rd_steward_setup.proposed",
}


def primitive_map_document() -> dict:
    """Return a detached copy suitable for inspection/tests."""
    return {
        "contract": MAP_CONTRACT,
        "actions": {
            action: dict(spec)
            for action, spec in sorted(PRIMITIVE_MAP.items())
        },
        "legacy_forbidden_surfaces": sorted(LEGACY_FORBIDDEN_SURFACES),
    }
