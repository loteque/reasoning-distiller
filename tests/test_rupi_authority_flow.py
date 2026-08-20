#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

rd_bootstrap = importlib.import_module("rd_bootstrap")
human_confirmation = importlib.import_module("ril_human_confirmation")
operators = importlib.import_module("ril_operators")
steward = importlib.import_module("ril_steward_authorization")
rupi_authority = importlib.import_module("rupi_authority")


def make_project() -> tuple[tempfile.TemporaryDirectory, Path]:
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / ".reasoning-distiller").mkdir()
    code, result = rd_bootstrap.bootstrap(root)
    assert code == 0 and result["status"] == "PASS"
    return td, root


def prepare_and_establish_root(root: Path, operator_id: str = "operator:human") -> dict:
    prepared = rupi_authority.prepare_initial_root(root, operator_id=operator_id)
    assert prepared["status"] == "STOPPED"
    return rupi_authority.confirm_initial_root(
        root,
        operator_id=operator_id,
        proposal_reference=prepared["proposal_reference"],
        confirmation="ESTABLISH_ROOT_OPERATOR",
    )


class RupiAuthorityR5Tests(unittest.TestCase):
    def test_protected_confirmation_is_exact_and_non_authoritative(self):
        ref = "proposal:" + "a" * 64
        for generic in ("yes", "proceed", "approve", "establish_root_operator"):
            result = human_confirmation.bind_exact_confirmation(
                generic,
                ceremony="ESTABLISH_ROOT_OPERATOR",
                proposal_reference=ref,
            )
            self.assertEqual(result["status"], "STOPPED")
            self.assertEqual(result["outcome"], "HUMAN_CONFIRMATION_REQUIRED")
        exact = human_confirmation.bind_exact_confirmation(
            "ESTABLISH_ROOT_OPERATOR",
            ceremony="ESTABLISH_ROOT_OPERATOR",
            proposal_reference=ref,
        )
        self.assertEqual(exact["status"], "PASS")
        self.assertEqual(exact["authority_effect"], "none")
        self.assertEqual(exact["proposal_reference"], ref)

    def test_root_operator_id_is_never_inferred(self):
        td, root = make_project()
        self.addCleanup(td.cleanup)
        result = rupi_authority.prepare_initial_root(root, operator_id=None)
        self.assertEqual(result["status"], "STOPPED")
        self.assertEqual(result["outcome"], "OPERATOR_ID_REQUIRED")
        events, projection = operators.operator_paths(root)
        self.assertFalse(events.exists())
        self.assertFalse(projection.exists())

    def test_root_prepare_is_non_mutating_and_returns_exact_protected_boundary(self):
        td, root = make_project()
        self.addCleanup(td.cleanup)
        before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
        result = rupi_authority.prepare_initial_root(root, operator_id="operator:human")
        after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
        self.assertEqual(before, after)
        self.assertEqual(result["outcome"], "INITIAL_ROOT_CONFIRMATION_REQUIRED")
        self.assertEqual(result["required_confirmation"], "ESTABLISH_ROOT_OPERATOR")
        self.assertEqual(result["ceremony_boundary"]["outcome"], "PROTECTED_CEREMONY_REQUIRED")
        self.assertEqual(result["proposal_presentation"]["proposal_reference"], result["proposal_reference"])

    def test_generic_yes_cannot_establish_root(self):
        td, root = make_project()
        self.addCleanup(td.cleanup)
        prepared = rupi_authority.prepare_initial_root(root, operator_id="operator:human")
        result = rupi_authority.confirm_initial_root(
            root,
            operator_id="operator:human",
            proposal_reference=prepared["proposal_reference"],
            confirmation="yes",
        )
        self.assertEqual(result["status"], "STOPPED")
        self.assertEqual(result["outcome"], "INITIAL_ROOT_CONFIRMATION_REQUIRED")
        state = operators.initial_required(root)
        self.assertEqual(state["status"], "FAIL")
        self.assertEqual(state["outcome"], "INITIAL_OPERATOR_REQUIRED")

    def test_root_confirmation_replans_exact_reference_and_establishes_once(self):
        td, root = make_project()
        self.addCleanup(td.cleanup)
        prepared = rupi_authority.prepare_initial_root(root, operator_id="operator:human")
        stale = rupi_authority.confirm_initial_root(
            root,
            operator_id="operator:human",
            proposal_reference="proposal:" + "0" * 64,
            confirmation="ESTABLISH_ROOT_OPERATOR",
        )
        self.assertEqual(stale["outcome"], "PROPOSAL_REFERENCE_MISMATCH")
        self.assertEqual(operators.initial_required(root)["outcome"], "INITIAL_OPERATOR_REQUIRED")

        applied = rupi_authority.confirm_initial_root(
            root,
            operator_id="operator:human",
            proposal_reference=prepared["proposal_reference"],
            confirmation="ESTABLISH_ROOT_OPERATOR",
        )
        self.assertEqual(applied["status"], "PASS")
        self.assertEqual(applied["outcome"], "INITIAL_ROOT_ESTABLISHED")
        self.assertEqual(applied["approval"]["operator_id"], "operator:human")
        evidence = applied["approval"]["authentication"]["evidence"]["protected_confirmation"]
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(evidence["proposal_reference"], prepared["proposal_reference"])

        events_dir, _ = operators.operator_paths(root)
        event_count = len(list(events_dir.glob("*.json")))
        replay = rupi_authority.confirm_initial_root(
            root,
            operator_id="operator:human",
            proposal_reference=prepared["proposal_reference"],
            confirmation="ESTABLISH_ROOT_OPERATOR",
        )
        self.assertEqual(replay["status"], "PASS")
        self.assertEqual(replay["outcome"], "INITIAL_ROOT_NOT_REQUIRED")
        self.assertEqual(len(list(events_dir.glob("*.json"))), event_count)

    def test_steward_target_is_explicit_and_generic_confirmation_cannot_apply(self):
        td, root = make_project()
        self.addCleanup(td.cleanup)
        self.assertEqual(prepare_and_establish_root(root)["status"], "PASS")

        missing = rupi_authority.prepare_steward_authorization(
            root,
            scope="semantic_reconciliation",
            role_id=None,
        )
        self.assertEqual(missing["status"], "STOPPED")
        self.assertEqual(missing["checkpoint"]["failed_operations"][-1]["outcome"], "ROLE_REQUIRED")

        prepared = rupi_authority.prepare_steward_authorization(
            root,
            scope="semantic_reconciliation",
            role_id="steward:default",
        )
        denied = rupi_authority.confirm_steward_authorization(
            root,
            scope="semantic_reconciliation",
            role_id="steward:default",
            approving_operator_id="operator:human",
            proposal_reference=prepared["proposal_reference"],
            confirmation="approve all",
        )
        self.assertEqual(denied["status"], "STOPPED")
        auth = steward.read_authorization(root)["authorization"]
        self.assertIsNone(auth["assignments"]["semantic_reconciliation"])
        self.assertIsNone(auth["assignments"]["admission"])

    def test_steward_scopes_are_independent_and_each_requires_its_own_ceremony(self):
        td, root = make_project()
        self.addCleanup(td.cleanup)
        self.assertEqual(prepare_and_establish_root(root)["status"], "PASS")

        recon_prepare = rupi_authority.prepare_steward_authorization(
            root,
            scope="semantic_reconciliation",
            role_id="steward:default",
        )
        recon = rupi_authority.confirm_steward_authorization(
            root,
            scope="semantic_reconciliation",
            role_id="steward:default",
            approving_operator_id="operator:human",
            proposal_reference=recon_prepare["proposal_reference"],
            confirmation="STEWARD_AUTHORIZATION_CHANGE",
        )
        self.assertEqual(recon["status"], "PASS")
        auth = steward.read_authorization(root)["authorization"]
        self.assertEqual(auth["assignments"]["semantic_reconciliation"], "steward:default")
        self.assertIsNone(auth["assignments"]["admission"])

        admission_prepare = rupi_authority.prepare_steward_authorization(
            root,
            scope="admission",
            role_id="steward:default",
        )
        self.assertNotEqual(admission_prepare["proposal_reference"], recon_prepare["proposal_reference"])
        admission = rupi_authority.confirm_steward_authorization(
            root,
            scope="admission",
            role_id="steward:default",
            approving_operator_id="operator:human",
            proposal_reference=admission_prepare["proposal_reference"],
            confirmation="STEWARD_AUTHORIZATION_CHANGE",
        )
        self.assertEqual(admission["status"], "PASS")
        auth = steward.read_authorization(root)["authorization"]
        self.assertEqual(auth["assignments"]["semantic_reconciliation"], "steward:default")
        self.assertEqual(auth["assignments"]["admission"], "steward:default")

    def test_unauthorized_approver_is_rejected_by_existing_steward_primitive(self):
        td, root = make_project()
        self.addCleanup(td.cleanup)
        self.assertEqual(prepare_and_establish_root(root)["status"], "PASS")
        prepared = rupi_authority.prepare_steward_authorization(
            root,
            scope="admission",
            role_id="steward:default",
        )
        result = rupi_authority.confirm_steward_authorization(
            root,
            scope="admission",
            role_id="steward:default",
            approving_operator_id="operator:not-authorized",
            proposal_reference=prepared["proposal_reference"],
            confirmation="STEWARD_AUTHORIZATION_CHANGE",
        )
        self.assertEqual(result["status"], "STOPPED")
        self.assertEqual(result["checkpoint"]["failed_operations"][-1]["outcome"], "APPROVER_NOT_AUTHORIZED")
        auth = steward.read_authorization(root)["authorization"]
        self.assertIsNone(auth["assignments"]["admission"])

    def test_authority_setup_never_creates_activation_or_semantic_state(self):
        td, root = make_project()
        self.addCleanup(td.cleanup)
        self.assertEqual(prepare_and_establish_root(root)["status"], "PASS")
        prepared = rupi_authority.prepare_steward_authorization(
            root,
            scope="semantic_reconciliation",
            role_id="steward:default",
        )
        result = rupi_authority.confirm_steward_authorization(
            root,
            scope="semantic_reconciliation",
            role_id="steward:default",
            approving_operator_id="operator:human",
            proposal_reference=prepared["proposal_reference"],
            confirmation="STEWARD_AUTHORIZATION_CHANGE",
        )
        self.assertEqual(result["status"], "PASS")
        forbidden = [
            "project-knowledge/canonical",
            "project-knowledge/reconciliation",
            "project-knowledge/admission",
            "project-knowledge/activations",
        ]
        for rel in forbidden:
            self.assertFalse((root / rel).exists(), rel)
        self.assertEqual(list((root / "project-knowledge/submissions").iterdir()), [])

    def test_rupi_authority_never_imports_legacy_steward_setup_or_creates_approval_semantics(self):
        source = (RUNTIME / "rupi_authority.py").read_text(encoding="utf-8")
        self.assertNotIn("rd_steward_setup", source)
        self.assertNotIn("make_approval(", source)
        self.assertNotIn("make_proposal(", source)
        self.assertNotIn("make_explicit_activation", source)
        self.assertIn("ril_operators.approve_initial_operator", source)
        self.assertIn("steward_authorization.approve_authorization_change", source)


if __name__ == "__main__":
    unittest.main()
