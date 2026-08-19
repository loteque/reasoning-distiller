#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mut = load("ril_mutation_g1", ROOT / "runtime" / "ril_mutation.py")
gov = load("ril_governance_g1", ROOT / "runtime" / "ril_governance.py")


class G1SubstrateTests(unittest.TestCase):
    def setUp(self):
        self.p = mut.make_proposal("roles", "ADD", {}, {"key": "x", "value": 1})

    def test_approval_v1_remains_valid(self):
        a = mut.make_approval(self.p, "operator:owner", {"method": "test-human"})
        mut.validate_approval(a, self.p)

    def test_approval_v2_direct_binds_exact_proposal(self):
        a = mut.make_direct_approval_v2(self.p, "operator:owner", {"method": "test-human"})
        mut.validate_approval(a, self.p)
        other = mut.make_proposal("roles", "ADD", {}, {"key": "x", "value": 2})
        with self.assertRaises(mut.ContractError):
            mut.validate_approval(a, other)

    def test_approval_v2_grant_basis_is_explicit(self):
        a = mut.make_grant_approval_v2(self.p, "authority-grant:abc", "authority-grant-event:def")
        mut.validate_approval(a, self.p)
        self.assertEqual(a["authority_basis"]["kind"], "authority-grant")

    def test_d3_classifies_current_and_stale(self):
        self.assertEqual(mut.revalidate_proposal(self.p, {})["classification"], "APPLICABLE")
        self.assertEqual(mut.revalidate_proposal(self.p, {"changed": True})["classification"], "STALE")
        self.assertEqual(mut.revalidate_proposal(self.p, {}, blocked_reasons=["MISSING_EVIDENCE"])["classification"], "BLOCKED")

    def test_delegation_registry_fails_closed(self):
        self.assertTrue(gov.delegation_metadata("role-registry.change")["delegable"])
        self.assertTrue(gov.delegation_metadata("operator-registry.disable")["delegable"])
        self.assertFalse(gov.delegation_metadata("operator-registry.add")["delegable"])
        self.assertFalse(gov.delegation_metadata("unknown.operation")["delegable"])

    def test_provenance_identity_includes_subject(self):
        kwargs = {"producer": {"kind": "tool", "identity": "test"}}
        p1 = gov.make_provenance("proposal:aaa", **kwargs)
        p2 = gov.make_provenance("proposal:bbb", **kwargs)
        self.assertNotEqual(gov.provenance_reference(p1), gov.provenance_reference(p2))

    def test_provenance_index_has_no_subject_authority_semantics(self):
        p = gov.make_provenance("proposal:aaa", producer={"kind": "automation"})
        idx = gov.index_provenance({}, p)
        self.assertEqual(list(idx), ["proposal:aaa"])
        self.assertEqual(idx["proposal:aaa"], [gov.provenance_reference(p)])
        self.assertNotIn("authority", p)


if __name__ == "__main__":
    unittest.main()
