import unittest

from context_packaging.source_resolver import resolve_sources
from tests.test_context_packaging_source_resolution_p2 import (
    C_BYTES,
    Registry,
    accepted,
    canonical,
    profile,
    repo,
    request,
    snapshot_ref,
    source_ref,
)


class P2RelationshipAndMultiplicityRegressions(unittest.TestCase):
    def _relationship_ambiguity(self, canonical_order):
        repository = repo()
        req = request([repository, *canonical_order])
        req["consistency_requirements"] = [
            {
                "predicate": "canonical_declares_repository_snapshot",
                "left_snapshot_ref": snapshot_ref(canonical_order[0]),
                "right_snapshot_ref": snapshot_ref(repository),
            }
        ]
        registry = Registry(
            {"repository_control": b"alpha-control\n", "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(
            result.failure["code"], "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
        )
        self.assertEqual(registry.calls, [])

    def test_conflicting_relationship_fails_good_then_bad(self):
        repository = repo()
        good = canonical(
            relation={
                "repository": repository["repository"],
                "commit": repository["commit"],
            }
        )
        bad = canonical(
            relation={"repository": repository["repository"], "commit": "2" * 40}
        )
        self._relationship_ambiguity([good, bad])

    def test_conflicting_relationship_fails_bad_then_good(self):
        repository = repo()
        good = canonical(
            relation={
                "repository": repository["repository"],
                "commit": repository["commit"],
            }
        )
        bad = canonical(
            relation={"repository": repository["repository"], "commit": "2" * 40}
        )
        self._relationship_ambiguity([bad, good])

    def test_single_snapshot_intent_rejects_other_accepted_standing(self):
        repository = repo()
        first = canonical(logical="standing-multi", snapshot="snapshot:a")
        second = canonical(logical="standing-multi", snapshot="snapshot:b")
        req = request([repository, first])
        req["accepted_canonical_standing"].append(accepted(second))
        registry = Registry(
            {"repository_control": b"alpha-control\n", "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "CANONICAL_BINDING_CONFLICT")
        self.assertEqual(registry.calls, [])

    def test_explicit_multi_snapshot_intent_accepts_distinct_standing(self):
        repository = repo()
        first = canonical(logical="standing-multi", snapshot="snapshot:a")
        second = canonical(logical="standing-multi", snapshot="snapshot:b")
        req = request([repository, first, second])
        req["multiple_snapshot_sources"] = [source_ref(first)]
        prof = profile()
        prof["knowledge"]["snapshot_multiplicity"] = "explicit_request"
        registry = Registry(
            {"repository_control": b"alpha-control\n", "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, prof, registry.adapters())
        self.assertTrue(result.ok)
        self.assertEqual(len(result.sources), 3)
        self.assertEqual(len(registry.calls), 3)


if __name__ == "__main__":
    unittest.main()
