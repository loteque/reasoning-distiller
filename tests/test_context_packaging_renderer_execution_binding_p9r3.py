from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR_SCHEMA = ROOT / "schemas/python-closed-bundle-descriptor.schema.json"
BINDING_SCHEMA = ROOT / "schemas/renderer-execution-binding.schema.json"

import context_packaging.renderer as renderer

_SHA = "sha256:" + "0" * 64
_EXPECTED_RUNTIME = {
    "implementation": "cpython",
    "major": 3,
    "minor": 12,
    "micro": 0,
    "cache_tag": "cpython-312",
}
_FROZEN_PRIMITIVES = {
    "primitive:base64.b64decode",
    "primitive:base64.b64encode",
    "primitive:builtins.Exception",
    "primitive:builtins.KeyError",
    "primitive:builtins.TypeError",
    "primitive:builtins.UnicodeError",
    "primitive:builtins.ValueError",
    "primitive:builtins.all",
    "primitive:builtins.any",
    "primitive:builtins.bool",
    "primitive:builtins.bytearray",
    "primitive:builtins.bytes",
    "primitive:builtins.dict",
    "primitive:builtins.enumerate",
    "primitive:builtins.float",
    "primitive:builtins.int",
    "primitive:builtins.isinstance",
    "primitive:builtins.len",
    "primitive:builtins.list",
    "primitive:builtins.ord",
    "primitive:builtins.set",
    "primitive:builtins.sorted",
    "primitive:builtins.str",
    "primitive:builtins.super",
    "primitive:builtins.tuple",
    "primitive:collections.abc.Mapping",
    "primitive:copy.deepcopy",
    "primitive:dis.Bytecode",
    "primitive:dis.get_instructions",
    "primitive:hashlib.sha256",
    "primitive:io.BytesIO",
    "primitive:json.loads",
    "primitive:math.isfinite",
    "primitive:struct.pack",
    "primitive:types.CodeType",
    "primitive:types.FunctionType",
}


def _pack():
    return {
        "contract": "reasoning-distiller-context-pack/2",
        "profile": {"profile_id": "pack", "profile_version": "1", "raw_sha256": _SHA},
        "request": {"request_id": "req", "raw_sha256": _SHA},
        "source_registry": {},
        "control_plane": {"items": []},
        "knowledge_plane": {"items": []},
        "operational_evidence_plane": {"items": []},
        "inclusion_ledger": {},
        "toolchain": {"components": [{"role": "jcs_serializer", "contract": "jcs/1"}]},
        "identity": {"pack_identity_sha256": _SHA},
        "eligibility": {},
    }


def _profile_v1(pack):
    profile = {
        "contract": renderer.RENDERER_PROFILE_CONTRACT,
        "profile_id": "p9-provider-neutral",
        "profile_version": "1",
        "supported_pack_contracts": [
            "reasoning-distiller-context-pack/1",
            "reasoning-distiller-context-pack/2",
        ],
        "pack_profile": dict(pack["profile"]),
        "renderer_component": {
            "role": "renderer",
            "contract": renderer.RENDERER_CONTRACT,
            "immutable_identity": "git-blob:" + "0" * 40,
            "raw_sha256": _SHA,
        },
        "framing": {
            "contract": renderer.FRAMING_CONTRACT,
            "serializer": "jcs/1",
            "text_encoding": "utf-8",
            "item_encoding": "base64",
            "plane_order": ["control", "knowledge", "operational_evidence"],
        },
        "limits": {"max_activation_bytes": 500000},
    }
    return _raw(profile), profile


def _profile_v2(pack, binding):
    profile = {
        "contract": renderer.RENDERER_PROFILE_CONTRACT_V2,
        "profile_id": "p9-provider-neutral",
        "profile_version": "2",
        "supported_pack_contracts": [
            "reasoning-distiller-context-pack/1",
            "reasoning-distiller-context-pack/2",
        ],
        "pack_profile": dict(pack["profile"]),
        "renderer_execution_binding": json.loads(json.dumps(binding)),
        "framing": {
            "contract": renderer.FRAMING_CONTRACT,
            "serializer": "jcs/1",
            "text_encoding": "utf-8",
            "item_encoding": "base64",
            "plane_order": ["control", "knowledge", "operational_evidence"],
        },
        "limits": {"max_activation_bytes": 500000},
    }
    return _raw(profile), profile


def _raw(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def _fake_binding(identity=None):
    return {
        "contract": renderer.EXECUTION_BINDING_CONTRACT,
        "scheme": renderer.BUNDLE_SCHEME,
        "runtime_abi": dict(_EXPECTED_RUNTIME),
        "identity_sha256": identity or _SHA,
    }


def _capture_exact_structural_runtime(monkeypatch):
    # Structural P9R3 implementation harness only. This does not establish
    # candidate-bound CPython 3.12.0 execution evidence.
    monkeypatch.setattr(renderer, "_RUNTIME_ABI_CAPTURE", renderer._EXPECTED_RUNTIME_ABI)
    return renderer._resolve_bundle()


def test_p9r3_registers_all_frozen_roots_without_broadening_primitive_allowlist():
    bundle = renderer._resolve_bundle()
    registry = dict(bundle[0])
    roots = {
        "member:render": renderer.render_context_pack_v2,
        "member:decode": renderer.decode_rendered_activation_v2,
        "member:resolve_bundle": renderer._resolve_bundle,
        "member:describe_bundle": renderer.describe_bundle,
        "member:derive_execution_binding": renderer.derive_execution_binding,
        "member:compare_execution_binding": renderer.compare_execution_binding,
    }
    for member_id, expected in roots.items():
        assert member_id in registry
        assert bundle[registry[member_id]] is expected

    primitive_ids = [spec[0] for spec in renderer._PRIMITIVE_REGISTRY]
    assert primitive_ids == sorted(primitive_ids)
    assert len(primitive_ids) == len(set(primitive_ids))
    assert set(primitive_ids) <= _FROZEN_PRIMITIVES
    assert "primitive:copy.deepcopy" in _FROZEN_PRIMITIVES
    assert "primitive:copy.deepcopy" not in primitive_ids
    assert "member:jcs_clone" in registry


def test_p9r3_descriptor_and_binding_are_deterministic_and_match_frozen_schemas(monkeypatch):
    bundle = _capture_exact_structural_runtime(monkeypatch)
    descriptor = bundle[107](bundle)
    binding = bundle[108](bundle)
    repeated = bundle[108](bundle)

    assert descriptor["contract"] == renderer.DESCRIPTOR_CONTRACT
    assert descriptor["scheme"] == renderer.BUNDLE_SCHEME
    assert descriptor["runtime_abi"] == _EXPECTED_RUNTIME
    assert binding == repeated
    assert binding["contract"] == renderer.EXECUTION_BINDING_CONTRACT
    assert binding["scheme"] == renderer.BUNDLE_SCHEME
    assert binding["runtime_abi"] == _EXPECTED_RUNTIME
    assert binding["identity_sha256"].startswith("sha256:")
    assert len(binding["identity_sha256"]) == 71

    ids = [member["id"] for member in descriptor["members"]]
    assert ids == sorted(ids, key=lambda value: value.encode("utf-8"))
    assert len(ids) == len(set(ids))
    for root in (
        "member:render",
        "member:decode",
        "member:resolve_bundle",
        "member:describe_bundle",
        "member:derive_execution_binding",
        "member:compare_execution_binding",
    ):
        assert root in ids

    if DESCRIPTOR_SCHEMA.exists() and BINDING_SCHEMA.exists():
        Draft202012Validator(json.loads(DESCRIPTOR_SCHEMA.read_text())).validate(descriptor)
        Draft202012Validator(json.loads(BINDING_SCHEMA.read_text())).validate(binding)


def test_p9r3_v2_rejects_v1_profile_and_runtime_mismatch_fails_closed(monkeypatch):
    pack = _pack()
    v1_raw, v1_profile = _profile_v1(pack)
    reused = renderer.render_context_pack_v2(pack, v1_raw, v1_profile)
    assert not reused.ok
    assert reused.failure["code"] == "UNSUPPORTED_RENDERER"

    wrong_runtime = ("cpython", 3, 12, 1, "cpython-312")
    monkeypatch.setattr(renderer, "_RUNTIME_ABI_CAPTURE", wrong_runtime)
    raw, profile = _profile_v2(pack, _fake_binding())
    mismatch = renderer.render_context_pack_v2(pack, raw, profile)
    assert not mismatch.ok
    assert mismatch.failure["code"] == "TOOLCHAIN_IDENTITY_MISMATCH"

    monkeypatch.setattr(renderer, "_RUNTIME_ABI_CAPTURE", ("pypy", 3, 12, 0, "pypy312"))
    unsupported = renderer.render_context_pack_v2(pack, raw, profile)
    assert not unsupported.ok
    assert unsupported.failure["code"] == "UNSUPPORTED_RENDERER"


def test_p9r3_truthful_binding_round_trips_and_false_binding_fails_structurally(monkeypatch):
    bundle = _capture_exact_structural_runtime(monkeypatch)
    actual = bundle[108](bundle)
    pack = _pack()
    profile_raw, profile = _profile_v2(pack, actual)

    rendered = renderer.render_context_pack_v2(pack, profile_raw, profile)
    assert rendered.ok, rendered.failure
    assert rendered.activation["contract"] == renderer.RENDERED_ACTIVATION_CONTRACT_V2
    assert rendered.activation["renderer_execution_binding"] == actual
    assert "renderer_component" not in rendered.activation

    decoded = renderer.decode_rendered_activation_v2(
        rendered.serialized_activation, profile_raw, profile
    )
    assert decoded.ok, decoded.failure
    assert decoded.pack == pack

    false_binding = json.loads(json.dumps(actual))
    false_binding["identity_sha256"] = _SHA
    assert false_binding != actual
    false_raw, false_profile = _profile_v2(pack, false_binding)
    failed = renderer.render_context_pack_v2(pack, false_raw, false_profile)
    assert not failed.ok
    assert failed.failure["code"] == "TOOLCHAIN_IDENTITY_MISMATCH"


def test_p9r3_same_resolved_bundle_measurement_and_execution_ignore_later_global_substitution(monkeypatch):
    bundle = _capture_exact_structural_runtime(monkeypatch)
    actual = bundle[108](bundle)
    pack = _pack()
    profile_raw, profile = _profile_v2(pack, actual)
    baseline = bundle[103](bundle, pack, profile_raw, profile)
    assert baseline.ok, baseline.failure

    def forbidden(*_args, **_kwargs):
        raise AssertionError("captured P9R3 bundle reached substituted module-global behavior")

    for name in (
        "_profile_v2_bound",
        "_derive_execution_binding_bound",
        "_compare_execution_binding_bound",
        "_descriptor_members_bound",
        "_global_dependencies_bound",
        "_jcs_bound",
        "_sha256_primitive",
        "_get_instructions_primitive",
        "_MEMBER_REGISTRY",
        "_BOOTSTRAP_DEPENDENCIES",
    ):
        monkeypatch.setattr(renderer, name, forbidden)
    monkeypatch.setattr(renderer, "RENDERER_CONTRACT_V2", "substituted-after-resolution")
    monkeypatch.setattr(renderer, "_RUNTIME_ABI_CAPTURE", ("cpython", 9, 9, 9, "substituted"))

    assert bundle[108](bundle) == actual
    repeated = bundle[103](bundle, pack, profile_raw, profile)
    assert repeated.ok, repeated.failure
    assert repeated.serialized_activation == baseline.serialized_activation
    decoded = bundle[104](bundle, baseline.serialized_activation, profile_raw, profile)
    assert decoded.ok, decoded.failure
    assert decoded.pack == pack


def test_p9r3_runtime_primitive_substitution_before_resolution_fails_toolchain_identity(monkeypatch):
    monkeypatch.setattr(renderer, "_RUNTIME_ABI_CAPTURE", renderer._EXPECTED_RUNTIME_ABI)
    monkeypatch.setattr(renderer, "_sha256_primitive", len)
    pack = _pack()
    profile_raw, profile = _profile_v2(pack, _fake_binding())
    failed = renderer.render_context_pack_v2(pack, profile_raw, profile)
    assert not failed.ok
    assert failed.failure["code"] == "TOOLCHAIN_IDENTITY_MISMATCH"


def test_p9r3_fresh_resolution_rederives_binding_without_cache(monkeypatch):
    _capture_exact_structural_runtime(monkeypatch)
    first = renderer._resolve_bundle()
    first_binding = first[108](first)
    second = renderer._resolve_bundle()
    second_binding = second[108](second)
    assert first is not second
    assert first_binding == second_binding

    pack = _pack()
    profile_raw, profile = _profile_v2(pack, first_binding)
    baseline = renderer.render_context_pack_v2(pack, profile_raw, profile)
    assert baseline.ok, baseline.failure

    monkeypatch.setattr(renderer, "RENDERER_CONTRACT_V2", "reasoning-distiller-context-renderer/2-mutated")
    changed = renderer._resolve_bundle()
    changed_binding = changed[108](changed)
    assert changed_binding != first_binding

    stale = renderer.render_context_pack_v2(pack, profile_raw, profile)
    assert not stale.ok
    assert stale.failure["code"] == "TOOLCHAIN_IDENTITY_MISMATCH"
