from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]

RENDERER_V2 = ROOT / "protocols/rgp/context-renderer-v2.json"
EXECUTION_BINDING = ROOT / "protocols/rgp/renderer-execution-binding-v1.json"
CLOSED_BUNDLE = ROOT / "protocols/rgp/python-closed-bundle-v1.json"
PROFILE_V2_SCHEMA = ROOT / "schemas/context-renderer-profile-v2.schema.json"
ACTIVATION_V2_SCHEMA = ROOT / "schemas/context-rendered-activation-v2.schema.json"
BINDING_SCHEMA = ROOT / "schemas/renderer-execution-binding.schema.json"
DESCRIPTOR_SCHEMA = ROOT / "schemas/python-closed-bundle-descriptor.schema.json"
PRESSURE_CASES = ROOT / "tests/fixtures/p9-renderer-identity-pressure-cases-v1.json"

EXPECTED_RUNTIME = {
    "implementation": "cpython",
    "major": 3,
    "minor": 12,
    "micro": 0,
    "cache_tag": "cpython-312",
}


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
    ).hexdigest()


def test_p9r1_all_new_schemas_are_closed_world_valid_draft_2020_12():
    for path in (
        PROFILE_V2_SCHEMA,
        ACTIVATION_V2_SCHEMA,
        BINDING_SCHEMA,
        DESCRIPTOR_SCHEMA,
    ):
        schema = _json(path)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        Draft202012Validator.check_schema(schema)


def test_p9r1_freezes_honestly_versioned_v2_wire_family_and_v1_rejection():
    renderer = _json(RENDERER_V2)
    profile = _json(PROFILE_V2_SCHEMA)
    activation = _json(ACTIVATION_V2_SCHEMA)

    assert renderer["contract"] == "reasoning-distiller-context-renderer/2"
    assert profile["properties"]["contract"]["const"] == (
        "reasoning-distiller-context-renderer-profile/2"
    )
    assert activation["properties"]["contract"]["const"] == (
        "reasoning-distiller-context-rendered-activation/2"
    )
    assert "renderer_execution_binding" in profile["required"]
    assert "renderer_execution_binding" in activation["required"]
    assert "renderer_component" not in profile["properties"]
    assert "renderer_component" not in activation["properties"]

    migration = "\n".join(renderer["migration"])
    assert "profile/1 is unsupported" in migration
    assert "No /1 Git blob" in migration
    assert "deriving a new reasoning-distiller-renderer-execution-binding/1" in migration


def test_p9r1_freezes_exact_execution_binding_runtime_and_digest_domain():
    protocol = _json(EXECUTION_BINDING)
    schema = _json(BINDING_SCHEMA)

    assert protocol["contract"] == "reasoning-distiller-renderer-execution-binding/1"
    assert protocol["scheme"] == "python-closed-bundle/1"
    assert protocol["runtime_abi"] == EXPECTED_RUNTIME
    assert schema["properties"]["contract"]["const"] == protocol["contract"]
    assert schema["properties"]["scheme"]["const"] == protocol["scheme"]

    runtime_schema = schema["properties"]["runtime_abi"]["properties"]
    assert {
        "implementation": runtime_schema["implementation"]["const"],
        "major": runtime_schema["major"]["const"],
        "minor": runtime_schema["minor"]["const"],
        "micro": runtime_schema["micro"]["const"],
        "cache_tag": runtime_schema["cache_tag"]["const"],
    } == EXPECTED_RUNTIME

    assert protocol["digest"]["algorithm"] == "sha256"
    assert protocol["digest"]["domain_ascii"] == (
        "reasoning-distiller-renderer-execution-binding/1\\x00"
        "python-closed-bundle/1\\x00"
    )
    assert protocol["failure"]["binding_mismatch"] == "TOOLCHAIN_IDENTITY_MISMATCH"
    assert protocol["failure"]["unsupported_dependency_shape"] == "UNSUPPORTED_RENDERER"


def test_p9r1_freezes_closed_bundle_descriptor_dependency_and_same_bundle_rules():
    bundle = _json(CLOSED_BUNDLE)
    descriptor = _json(DESCRIPTOR_SCHEMA)

    assert bundle["contract"] == "reasoning-distiller-python-closed-bundle/1"
    assert bundle["scheme"] == "python-closed-bundle/1"
    assert bundle["runtime_abi"] == EXPECTED_RUNTIME
    assert descriptor["properties"]["contract"]["const"] == (
        "reasoning-distiller-python-closed-bundle-descriptor/1"
    )
    assert descriptor["properties"]["scheme"]["const"] == "python-closed-bundle/1"

    assert bundle["bundle_roots"] == [
        "member:render",
        "member:decode",
        "member:resolve_bundle",
        "member:describe_bundle",
        "member:derive_execution_binding",
        "member:compare_execution_binding",
    ]

    closure = "\n".join(bundle["dependency_closure"])
    assert "explicitly registered as a member" in closure
    assert "dynamic import" in closure
    assert "Mutable list/dict/set defaults" in closure
    assert "binding comparison are themselves behavior-bearing" in closure

    descriptor_text = json.dumps(bundle["descriptor"], sort_keys=True)
    assert "dis.get_instructions(code, show_caches=False, adaptive=False)" in descriptor_text
    assert "co_filename" in descriptor_text
    assert "co_firstlineno" in descriptor_text
    assert "co_linetable" in descriptor_text
    assert "marshal.dumps(code)" in descriptor_text

    same_bundle = "\n".join(bundle["same_bundle_execution"])
    assert "capturing all member and primitive references once" in same_bundle
    assert "no module-global behavior lookup is permitted" in same_bundle
    assert "No binding cache is permitted" in same_bundle


def test_p9r1_freezes_minimized_explicit_primitive_boundary_and_runtime_sources():
    bundle = _json(CLOSED_BUNDLE)
    boundary = bundle["runtime_primitive_boundary"]
    primitives = boundary["global_primitive_allowlist"]
    ids = [entry["id"] for entry in primitives]

    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    assert "primitive:hashlib.sha256" in ids
    assert "primitive:base64.b64encode" in ids
    assert "primitive:base64.b64decode" in ids
    assert "primitive:json.loads" in ids
    assert "primitive:dis.get_instructions" in ids
    assert "primitive:struct.pack" in ids

    assert boundary["runtime_information_sources"] == [
        "sys.implementation.name",
        "sys.version_info.major",
        "sys.version_info.minor",
        "sys.version_info.micro",
        "sys.implementation.cache_tag",
    ]
    assert all(entry["runtime_id"].startswith("cpython-3.12.0:") for entry in primitives)


def test_p9r1_preserves_p9r0_pressure_freeze():
    pressure = _json(PRESSURE_CASES)
    assert pressure["gate"] == "P9R0"
    assert [case["id"] for case in pressure["cases"]] == [
        f"RI-{index:02d}" for index in range(1, 25)
    ]


def test_p9r1_does_not_modify_renderer_or_historical_v1_protocol_bytes():
    assert _git_blob(ROOT / "context_packaging/renderer.py") == (
        "7d28edfa63302475343b2e8b10ef0309089429ff"
    )
    assert _git_blob(ROOT / "protocols/rgp/context-renderer-v1.json") == (
        "c8f18df390f92bfd25d6ac01c5932aeaf3ac396c"
    )
    assert _git_blob(ROOT / "schemas/context-renderer-profile.schema.json") == (
        "768bcae7051e2805594df6d45402d331dc43bda4"
    )
    assert _git_blob(ROOT / "schemas/context-rendered-activation.schema.json") == (
        "f52c6007be3e7aa84c7e65f5e0708641e6920367"
    )


def test_p9r1_exact_protocol_and_schema_bytes_disable_checkout_text_conversion():
    attrs = {
        line
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    }
    for path in (
        "protocols/rgp/context-renderer-v2.json",
        "protocols/rgp/renderer-execution-binding-v1.json",
        "protocols/rgp/python-closed-bundle-v1.json",
        "schemas/context-renderer-profile-v2.schema.json",
        "schemas/context-rendered-activation-v2.schema.json",
        "schemas/renderer-execution-binding.schema.json",
        "schemas/python-closed-bundle-descriptor.schema.json",
    ):
        assert f"{path} -text" in attrs
