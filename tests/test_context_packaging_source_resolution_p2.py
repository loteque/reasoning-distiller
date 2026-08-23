import hashlib
import unittest
from copy import deepcopy

from context_packaging.source_resolver import AdapterResult, resolve_sources

CONTRACT = "reasoning-distiller-context-source-binding/1"
A_BYTES = b"alpha-control\n"
B_BYTES = b"beta-package\n"
C_BYTES = b'{"records":[],"relations":[]}\n'
E_BYTES = b"activation-evidence\n"


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def repo(data=A_BYTES, logical="repo-control", commit="1" * 40, path="controls/a.md"):
    return {
        "contract": CONTRACT,
        "source_class": "repository_control",
        "logical_namespace": "project:test",
        "logical_source_id": logical,
        "repository": "loteque/reasoning-distiller",
        "commit": commit,
        "path": path,
        "raw_sha256": digest(data),
    }


def package(data=B_BYTES, logical="package-control", snapshot="package:001"):
    return {
        "contract": CONTRACT,
        "source_class": "package_control",
        "logical_namespace": "project:test",
        "logical_source_id": logical,
        "project_id": "test",
        "package_contract": "project-knowledge-package/1",
        "immutable_package_snapshot_id": snapshot,
        "artifact_locator": "rules/context-profile.json",
        "raw_sha256": digest(data),
    }


def canonical(data=C_BYTES, logical="canonical", snapshot="snapshot:001", relation=None):
    value = {
        "contract": CONTRACT,
        "source_class": "canonical_state",
        "logical_namespace": "project:test",
        "logical_source_id": logical,
        "project_id": "test",
        "backend_type": "pems-cove",
        "backend_contract": "project-canonical-backend/1",
        "backend_config_identity": "config:001",
        "immutable_snapshot_id": snapshot,
        "pems_semantic": "pems/2",
        "serializer": "jcs/1",
        "pems_sha256": digest(data),
        "standing_evidence": [
            {
                "contract": "canonical-standing-evidence/1",
                "immutable_snapshot_id": "standing:001",
                "raw_sha256": digest(b"standing"),
            }
        ],
    }
    if relation:
        value["repository_relationship"] = relation
    return value


def evidence(data=E_BYTES):
    return {
        "contract": CONTRACT,
        "source_class": "operational_evidence",
        "logical_namespace": "project:test",
        "logical_source_id": "activation",
        "artifact_contract": "reasoning-distiller-role-activation/1",
        "immutable_snapshot_id": "artifact:001",
        "raw_sha256": digest(data),
        "validation_status": "shape_and_digest_validated",
    }


def source_ref(binding):
    return {
        key: binding[key]
        for key in ("source_class", "logical_namespace", "logical_source_id")
    }


def snapshot_ref(binding):
    value = deepcopy(binding)
    value.pop("contract", None)
    value.pop("repository_relationship", None)
    return value


def accepted(binding):
    fingerprint = {
        key: deepcopy(binding[key])
        for key in (
            "project_id",
            "backend_type",
            "backend_contract",
            "backend_config_identity",
            "immutable_snapshot_id",
            "pems_semantic",
            "serializer",
            "pems_sha256",
            "standing_evidence",
        )
    }
    if "cove" in binding:
        fingerprint["cove"] = deepcopy(binding["cove"])
    address = {
        key: binding[key]
        for key in (
            "project_id",
            "backend_type",
            "backend_contract",
            "backend_config_identity",
            "immutable_snapshot_id",
        )
    }
    return {
        "condition": "accepted_project_backend_canonical_standing",
        "canonical_ref": source_ref(binding),
        "canonical_snapshot_address": address,
        "canonical_fingerprint": fingerprint,
    }


def profile():
    return {
        "contract": "reasoning-distiller-context-profile/1",
        "source_requirements": {
            "control_slots": [
                {
                    "slot_id": "primary-control",
                    "source_classes": ["repository_control"],
                    "cardinality": "exactly_one",
                }
            ],
            "operational_evidence_slots": [
                {
                    "slot_id": "activation",
                    "cardinality": "zero_or_more",
                    "accepted_statuses": ["shape_and_digest_validated"],
                }
            ],
            "consistency_rules": [],
        },
        "knowledge": {"snapshot_multiplicity": "single"},
        "limits": {
            "source_resolution": {
                "max_bindings": 8,
                "max_single_source_bytes": 4096,
                "max_total_source_bytes": 8192,
            }
        },
    }


def request(bindings):
    canonicals = [item for item in bindings if item["source_class"] == "canonical_state"]
    slots = (
        [
            {
                "slot_id": "primary-control",
                "plane": "control",
                "source_ref": snapshot_ref(bindings[0]),
            }
        ]
        if bindings and bindings[0]["source_class"] == "repository_control"
        else []
    )
    return {
        "contract": "reasoning-distiller-context-pack-request/1",
        "source_bindings": bindings,
        "slot_bindings": slots,
        "multiple_snapshot_sources": [],
        "accepted_canonical_standing": [accepted(item) for item in canonicals],
        "knowledge_selection": {
            "snapshots": [
                {
                    "canonical_snapshot_ref": snapshot_ref(item),
                    "record_ids": [],
                    "relation_ids": [],
                }
                for item in canonicals
            ]
        },
        "consistency_requirements": [],
    }


class Registry:
    def __init__(self, payloads, statuses=None, rebound=None):
        self.payloads = payloads
        self.statuses = statuses or {}
        self.rebound = rebound or {}
        self.calls = []

    def adapter(self, source_class):
        def read(binding, byte_limit):
            self.calls.append((source_class, deepcopy(binding), byte_limit))
            status = self.statuses.get(source_class, "resolved")
            if status != "resolved":
                return AdapterResult(
                    status,
                    diagnostics=(f"{source_class}:{status}",),
                )
            content = self.payloads[source_class]
            return AdapterResult(
                "resolved",
                self.rebound.get(source_class, binding),
                content,
            )

        return read

    def adapters(self):
        return {key: self.adapter(key) for key in self.payloads}


class P2Tests(unittest.TestCase):
    def test_exact_immutable_resolution_passes_and_adapter_gets_commit(self):
        repository, state = repo(), canonical()
        req = request([repository, state])
        registry = Registry(
            {"repository_control": A_BYTES, "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertTrue(result.ok)
        self.assertEqual(len(result.sources), 2)
        self.assertEqual(registry.calls[0][1]["commit"], "1" * 40)

    def test_missing_source_fails_closed(self):
        repository = repo()
        req = request([repository])
        registry = Registry(
            {"repository_control": A_BYTES},
            {"repository_control": "missing"},
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "IMMUTABLE_SNAPSHOT_UNAVAILABLE")

    def test_unsafe_control_fails_closed(self):
        repository = repo()
        req = request([repository])
        registry = Registry(
            {"repository_control": A_BYTES},
            {"repository_control": "unsafe"},
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "CONTROL_SOURCE_INVALID")

    def test_mutable_source_is_not_rebound(self):
        repository = repo()
        req = request([repository])
        registry = Registry(
            {"repository_control": A_BYTES},
            {"repository_control": "mutable"},
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "IMMUTABLE_SNAPSHOT_UNAVAILABLE")

    def test_control_digest_mismatch_uses_frozen_digest_failure(self):
        repository = repo()
        repository["raw_sha256"] = digest(b"different")
        req = request([repository])
        registry = Registry({"repository_control": A_BYTES})
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "SOURCE_DIGEST_MISMATCH")

    def test_canonical_digest_mismatch_is_stale_state(self):
        repository, state = repo(), canonical()
        state["pems_sha256"] = digest(b"stale")
        req = request([repository, state])
        req["accepted_canonical_standing"] = [accepted(state)]
        registry = Registry(
            {"repository_control": A_BYTES, "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "CANONICAL_STATE_STALE")

    def test_logical_source_conflict_fails_before_acquisition(self):
        first = repo()
        second = repo(logical=first["logical_source_id"], commit="2" * 40)
        req = request([first, second])
        registry = Registry({"repository_control": A_BYTES})
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "LOGICAL_SOURCE_CONFLICT")
        self.assertEqual(registry.calls, [])

    def test_missing_required_control_does_not_discover_one(self):
        state = canonical()
        req = request([state])
        registry = Registry({"canonical_state": C_BYTES})
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "MISSING_REQUIRED_CONTROL")
        self.assertEqual(registry.calls, [])

    def test_reference_to_unlisted_source_does_not_trigger_discovery(self):
        repository = repo()
        req = request([repository])
        req["slot_bindings"][0]["source_ref"] = snapshot_ref(repo(commit="2" * 40))
        registry = Registry({"repository_control": A_BYTES})
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "CONTROL_SOURCE_INVALID")
        self.assertEqual(registry.calls, [])

    def test_adapter_rebinding_is_rejected(self):
        repository = repo()
        req = request([repository])
        rebound = repo(commit="2" * 40)
        registry = Registry(
            {"repository_control": A_BYTES},
            rebound={"repository_control": rebound},
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "CONTROL_SOURCE_INVALID")

    def test_cross_source_consistency_is_structural(self):
        repository = repo()
        state = canonical(
            relation={"repository": repository["repository"], "commit": "2" * 40}
        )
        req = request([repository, state])
        req["consistency_requirements"] = [
            {
                "predicate": "canonical_declares_repository_snapshot",
                "left_snapshot_ref": snapshot_ref(state),
                "right_snapshot_ref": snapshot_ref(repository),
            }
        ]
        registry = Registry(
            {"repository_control": A_BYTES, "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(
            result.failure["code"], "CROSS_SOURCE_CONSISTENCY_UNPROVEN"
        )
        self.assertEqual(registry.calls, [])

    def test_source_resolution_limits_are_separate_and_fail_closed(self):
        repository = repo()
        req = request([repository])
        prof = profile()
        prof["limits"]["source_resolution"]["max_single_source_bytes"] = 4
        registry = Registry({"repository_control": A_BYTES})
        result = resolve_sources(req, prof, registry.adapters())
        self.assertEqual(result.failure["code"], "PACK_LIMIT_EXCEEDED")
        self.assertIn(
            "source_resolution.max_single_source_bytes",
            result.failure["diagnostics"][0],
        )

    def test_identical_duplicate_binding_is_acquired_once(self):
        repository = repo()
        req = request([repository, deepcopy(repository)])
        registry = Registry({"repository_control": A_BYTES})
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertTrue(result.ok)
        self.assertEqual(len(registry.calls), 1)
        self.assertEqual(len(result.sources), 1)

    def test_package_and_operational_evidence_resolve_by_explicit_binding(self):
        package_control, operational, state = package(), evidence(), canonical()
        req = request([package_control, operational, state])
        req["slot_bindings"] = [
            {
                "slot_id": "primary-control",
                "plane": "control",
                "source_ref": snapshot_ref(package_control),
            },
            {
                "slot_id": "activation",
                "plane": "operational_evidence",
                "source_ref": snapshot_ref(operational),
            },
        ]
        prof = profile()
        prof["source_requirements"]["control_slots"][0]["source_classes"] = [
            "package_control"
        ]
        registry = Registry(
            {
                "package_control": B_BYTES,
                "operational_evidence": E_BYTES,
                "canonical_state": C_BYTES,
            }
        )
        result = resolve_sources(req, prof, registry.adapters())
        self.assertTrue(result.ok)
        self.assertEqual(
            [source.binding["source_class"] for source in result.sources],
            ["package_control", "operational_evidence", "canonical_state"],
        )

    def test_missing_canonical_standing_is_unproven(self):
        repository, state = repo(), canonical()
        req = request([repository, state])
        req["accepted_canonical_standing"] = []
        registry = Registry(
            {"repository_control": A_BYTES, "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "CANONICAL_BINDING_UNPROVEN")
        self.assertEqual(registry.calls, [])

    def test_canonical_standing_fingerprint_conflict_fails(self):
        repository, state = repo(), canonical()
        req = request([repository, state])
        req["accepted_canonical_standing"][0]["canonical_fingerprint"][
            "pems_sha256"
        ] = digest(b"other")
        registry = Registry(
            {"repository_control": A_BYTES, "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, profile(), registry.adapters())
        self.assertEqual(result.failure["code"], "CANONICAL_BINDING_CONFLICT")
        self.assertEqual(registry.calls, [])

    def test_max_bindings_is_a_source_resolution_limit(self):
        repository, state = repo(), canonical()
        req = request([repository, state])
        prof = profile()
        prof["limits"]["source_resolution"]["max_bindings"] = 1
        registry = Registry(
            {"repository_control": A_BYTES, "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, prof, registry.adapters())
        self.assertEqual(result.failure["code"], "PACK_LIMIT_EXCEEDED")
        self.assertIn(
            "source_resolution.max_bindings", result.failure["diagnostics"][0]
        )
        self.assertEqual(registry.calls, [])

    def test_max_total_source_bytes_is_enforced_across_sources(self):
        repository, state = repo(), canonical()
        req = request([repository, state])
        prof = profile()
        prof["limits"]["source_resolution"]["max_total_source_bytes"] = (
            len(A_BYTES) + len(C_BYTES) - 1
        )
        registry = Registry(
            {"repository_control": A_BYTES, "canonical_state": C_BYTES}
        )
        result = resolve_sources(req, prof, registry.adapters())
        self.assertEqual(result.failure["code"], "PACK_LIMIT_EXCEEDED")
        self.assertIn(
            "source_resolution.max_total_source_bytes",
            result.failure["diagnostics"][0],
        )

    def test_adapter_cannot_mutate_requested_binding_in_place(self):
        repository = repo()
        req = request([repository])

        def mutating_adapter(binding, byte_limit):
            binding["commit"] = "2" * 40
            return AdapterResult("resolved", binding, A_BYTES)

        result = resolve_sources(
            req,
            profile(),
            {"repository_control": mutating_adapter},
        )
        self.assertEqual(result.failure["code"], "CONTROL_SOURCE_INVALID")
        self.assertEqual(req["source_bindings"][0]["commit"], "1" * 40)


if __name__ == "__main__":
    unittest.main()
