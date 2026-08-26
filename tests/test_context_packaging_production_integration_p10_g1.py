from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
PROTOCOL = ROOT / "protocols/rgp/production-integration-v2.json"
FIXTURES = ROOT / "tests/fixtures/p10-g1-protocol-fixtures-v1.json"
G0 = ROOT / "tests/test_context_packaging_production_integration_p10_g0.py"

SCHEMAS = {
    "invocation": "invocation-request-v2.schema.json",
    "activation_bundle": "activation-bundle-v2.schema.json",
    "result": "invocation-result-v2.schema.json",
    "provenance_registry": "context-provenance-registry.schema.json",
    "prepared_invocation": "prepared-invocation.schema.json",
    "model_transport": "model-transport.schema.json",
}
EXTERNAL_SCHEMAS = [
    "context-source-binding.schema.json",
    "context-rendered-activation-v2.schema.json",
    "renderer-execution-binding.schema.json",
]


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _objects(value):
    if isinstance(value, dict):
        if value.get("type") == "object":
            yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


def _mutate(value, path, field, replacement):
    value = copy.deepcopy(value)
    target = value
    for part in path:
        target = target[part]
    target[field] = copy.deepcopy(replacement)
    return value


def _canonical_bytes(value):
    # G1 fixtures deliberately use only JSON types whose Python canonical
    # encoding is byte-identical to JCS. Runtime JCS implementation is later.
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _registry(all_schemas):
    resources = []
    for schema in all_schemas.values():
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def test_p10_g1_inventory_is_closed_world_and_draft_2020_12():
    own = {key: _json(SCHEMA_DIR / name) for key, name in SCHEMAS.items()}
    for name, schema in own.items():
        Draft202012Validator.check_schema(schema)
        for node in _objects(schema):
            assert node["additionalProperties"] is False, name

    protocol = _json(PROTOCOL)
    assert protocol["gate"] == "P10-G1"
    assert protocol["scope"] == {
        "authorized": "P10_G1_PROTOCOL_HANDOFF_FREEZE_ONLY",
        "runtime_implementation_authorized": False,
        "installed_package_closure_established": False,
        "provenance_bridge_implemented": False,
        "prepare_finalize_implemented": False,
        "provider_transport_implemented": False,
        "admission_or_canonical_mutation_authorized": False,
    }
    assert {
        key: value["schema"] for key, value in protocol["contracts"].items()
    } == {key: f"schemas/{name}" for key, name in SCHEMAS.items()}


def test_p10_g1_is_bound_to_exact_governance_and_g0_candidate():
    protocol = _json(PROTOCOL)
    assert protocol["governance"] == {
        "coordination_revision": "80b6e89ad2efe84b088ca06b908a257c449fac15",
        "semantic_base": "cc14721725949a560b52f0a5d80808e95c2d6ad0",
        "governing_plan": {
            "commit": "b435dff827b745d711a5c5a297587a0c4359bed1",
            "blob": "eae54b9e2c0618faec61acf2f9e4acd942ec063d",
        },
        "g0_candidate": "2b5c81a5b7b92c810be84f87f42524842ec308a7",
    }
    assert G0.exists()


def test_p10_g1_contract_family_and_compatibility_are_exact():
    protocol = _json(PROTOCOL)
    contracts = {k: v["contract"] for k, v in protocol["contracts"].items()}
    assert contracts == {
        "invocation": "reasoning-distiller-invocation/2",
        "activation_bundle": "reasoning-distiller-activation-bundle/2",
        "result": "reasoning-distiller-invocation-result/2",
        "provenance_registry": "reasoning-distiller-context-provenance-registry/1",
        "prepared_invocation": "reasoning-distiller-prepared-invocation/1",
        "model_transport": "reasoning-distiller-model-transport/1",
    }
    compatibility = protocol["compatibility"]
    assert compatibility["automatic_v1_to_v2_conversion"] is False
    assert compatibility["release_version"] == "NOT_DECIDED_AT_G1"
    assert compatibility["invocation_v2_requires"]["runtime_abi"] == {
        "implementation": "cpython",
        "major": 3,
        "minor": 12,
        "micro": 0,
        "cache_tag": "cpython-312",
    }
    assert compatibility["invocation_v2_requires"]["renderer_binding_scheme"] == (
        "python-closed-bundle/1"
    )
    assert compatibility["old_v1_only_runtime_receiving_v2"] == (
        "reject UNSUPPORTED_CONTRACT"
    )


def test_p10_g1_digest_domains_and_stable_source_id_are_frozen():
    protocol = _json(PROTOCOL)
    domains = protocol["canonicalization"]["domains"]
    assert domains["provenance_binding"]["ascii"] == (
        "reasoning-distiller-context-provenance-binding/1\\x00"
    )
    assert domains["prepared_invocation"]["ascii"] == (
        "reasoning-distiller-prepared-invocation/1\\x00"
    )
    assert domains["model_transport"]["ascii"] == (
        "reasoning-distiller-model-transport/1\\x00"
    )

    fixture = _json(FIXTURES)["positive"]["provenance_registry"]
    source = fixture["sources"][0]
    digest = hashlib.sha256(
        b"reasoning-distiller-context-provenance-binding/1\x00"
        + _canonical_bytes(source["binding"])
    ).hexdigest()
    assert source["binding_sha256"] == "sha256:" + digest
    assert source["source_id"] == "src:ctx:" + digest
    assert protocol["source_id"]["pack_ordinal_or_frame_index_is_identity_input"] is False


def test_p10_g1_positive_examples_validate_against_exact_schema_family():
    own = {key: _json(SCHEMA_DIR / name) for key, name in SCHEMAS.items()}
    external = {
        name: _json(SCHEMA_DIR / name) for name in EXTERNAL_SCHEMAS
    }
    registry = _registry({**own, **external})
    examples = _json(FIXTURES)["positive"]
    for key, schema in own.items():
        errors = list(
            Draft202012Validator(schema, registry=registry).iter_errors(examples[key])
        )
        assert not errors, (key, [error.message for error in errors])


def test_p10_g1_negative_schema_fixtures_reject_and_classify_exactly():
    own = {key: _json(SCHEMA_DIR / name) for key, name in SCHEMAS.items()}
    external = {
        name: _json(SCHEMA_DIR / name) for name in EXTERNAL_SCHEMAS
    }
    registry = _registry({**own, **external})
    fixture = _json(FIXTURES)
    protocol = _json(PROTOCOL)
    owner = {
        code: stage
        for stage, codes in protocol["failure_ownership"].items()
        for code in codes
    }

    for case in fixture["negative_schema_cases"]:
        mutated = _mutate(
            fixture["positive"][case["target"]],
            case["path"],
            case["field"],
            case["value"],
        )
        errors = list(
            Draft202012Validator(
                own[case["target"]], registry=registry
            ).iter_errors(mutated)
        )
        assert errors, case["id"]
        assert owner[case["expected_reason"]] == case["expected_stage"], case["id"]


def test_p10_g1_result_reason_codes_have_one_exact_failure_owner():
    protocol = _json(PROTOCOL)
    result = _json(SCHEMA_DIR / SCHEMAS["result"])
    owned = [
        code
        for codes in protocol["failure_ownership"].values()
        for code in codes
    ]
    assert len(owned) == len(set(owned))
    result_codes = set(result["oneOf"][1]["properties"]["reason_code"]["enum"])
    assert set(owned) == result_codes
    assert protocol["downstream_handoff"]["incomplete_reason"] == (
        "INCOMPLETE_PROVENANCE_HANDOFF"
    )
    assert protocol["downstream_handoff"]["incomplete_failure_class"] == (
        "reconciliation_handoff"
    )


def test_p10_g1_transport_and_handoff_boundaries_are_explicit():
    protocol = _json(PROTOCOL)
    transport = protocol["model_transport"]
    assert transport["provider_neutral"] is True
    assert transport["threat_model"] == {
        "runner_assumption": "non-hostile/reference runner",
        "assurance_basis": "deterministic conformance testing",
        "hostile_provider_or_runner_attestation": "OUTSIDE_P10",
    }
    assert "no extra project context is added" in transport["logical_rules"]
    assert "context control does not acquire provider system authority" in (
        transport["logical_rules"]
    )

    handoff = protocol["downstream_handoff"]
    assert handoff["successful_tuple"] == [
        "ordinary immutable RGP submission",
        "reasoning-distiller-invocation-result/2",
        "reasoning-distiller-prepared-invocation/1",
        "reasoning-distiller-context-provenance-registry/1",
    ]
    assert handoff["result_must_reference"] == [
        "submission",
        "raw candidate",
        "prepared invocation",
        "provenance registry",
    ]
    assert "ambient file search is forbidden" in handoff["steward_rule"]


def test_p10_g1_semantic_negative_cases_preserve_g0_boundaries():
    fixture = _json(FIXTURES)
    cases = {case["id"]: case for case in fixture["semantic_cases"]}
    assert cases["PI-47"]["expected_reason"] == "PROVENANCE_SOURCE_COLLISION"
    assert cases["PI-47"]["expected_stage"] == "activation"
    assert cases["PI-48"]["expected_reason"] == "INCOMPLETE_PROVENANCE_HANDOFF"
    assert cases["PI-48"]["expected_stage"] == "reconciliation_handoff"
    assert cases["PI-60"]["expected_reason"] == "OUTSIDE_P10"
    assert cases["PI-60"]["expected_stage"] == "threat_boundary"


def test_p10_g1_exact_protocol_bytes_disable_checkout_text_conversion():
    attrs = {
        line
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    }
    paths = [
        "protocols/rgp/production-integration-v2.json",
        "tests/fixtures/p10-g1-protocol-fixtures-v1.json",
        *[f"schemas/{name}" for name in SCHEMAS.values()],
    ]
    for path in paths:
        assert f"{path} -text" in attrs
