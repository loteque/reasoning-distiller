from __future__ import annotations

import dis
import json
from pathlib import Path
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]

import context_packaging.renderer as renderer

_SHA = "sha256:" + "0" * 64


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


def _profile(pack):
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
    return json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"), profile


def _nested_code(code):
    yield code
    for constant in code.co_consts:
        if isinstance(constant, types.CodeType):
            yield from _nested_code(constant)


def test_p9r2_bundle_registry_is_fresh_explicit_sorted_and_immutable():
    first = renderer._resolve_bundle()
    second = renderer._resolve_bundle()

    assert first is not second
    registry = first[0]
    ids = [member_id for member_id, _slot in registry]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    for root in (
        "member:render",
        "member:decode",
        "member:resolve_bundle",
    ):
        assert root in ids
    for constant in (
        "member:constant:renderer_contract",
        "member:constant:renderer_profile_contract",
        "member:constant:rendered_activation_contract",
        "member:constant:framing_contract",
        "member:constant:failure_contract",
        "member:constant:pack_contracts",
        "member:constant:plane_order",
        "member:constant:plane_keys",
        "member:constant:profile_keys",
        "member:constant:pack_keys",
        "member:constant:pack_required_keys",
        "member:constant:digest_magic",
    ):
        assert constant in ids
    assert isinstance(first[34], tuple)
    assert isinstance(first[35], tuple)
    assert isinstance(first[36], frozenset)
    assert isinstance(first[37], frozenset)
    assert isinstance(first[38], frozenset)
    assert isinstance(first, tuple)
    with pytest.raises(TypeError):
        first[0] = ()


def test_p9r2_registered_globals_resolve_inside_captured_bundle_and_execution_members_go_global_free():
    bundle = renderer._resolve_bundle()
    get_bound = bundle[69]
    captured = bundle
    bootstrap_members = {
        "member:render",
        "member:decode",
        "member:resolve_bundle",
        "member:jcs_bootstrap",
    }

    for member_id, slot in bundle[0]:
        member = get_bound(bundle, slot)
        if member_id.startswith("member:constant:") or member_id.startswith("member:type:") or member_id == "member:registry":
            continue
        assert member.__closure__ is None, member_id
        assert not any(
            isinstance(default, (list, dict, set))
            for default in (member.__defaults__ or ())
        ), member_id
        for code in _nested_code(member.__code__):
            globals_used = [
                ins.argval
                for ins in dis.get_instructions(code)
                if ins.opname in {"LOAD_GLOBAL", "STORE_GLOBAL", "DELETE_GLOBAL"}
            ]
            if member_id not in bootstrap_members:
                assert globals_used == [], (member_id, code.co_name, globals_used)
            else:
                for name in globals_used:
                    if name in member.__globals__:
                        target = member.__globals__[name]
                    else:
                        builtins_table = member.__builtins__
                        target = builtins_table[name] if isinstance(builtins_table, dict) else getattr(builtins_table, name)
                    assert any(target is value for value in captured), (member_id, name)

def test_p9r2_same_resolved_bundle_survives_post_resolution_global_substitution(monkeypatch):
    pack = _pack()
    profile_raw, profile = _profile(pack)
    bundle = renderer._resolve_bundle()
    baseline = bundle[1](bundle, pack, profile_raw, profile)
    assert baseline.ok, baseline.failure

    def forbidden(*_args, **_kwargs):
        raise AssertionError("post-resolution renderer reached a module-global dependency")

    for name in (
        "_get_bound",
        "_profile_bound",
        "_pack_bound",
        "_frames_bound",
        "_frame_bound",
        "_header_bound",
        "_decode_frames_bound",
        "_frame_raw_bound",
        "_pack_summary_bound",
        "_profile_id_bound",
        "_request_id_bound",
        "_component_bound",
        "_strict_json_bound",
        "_jcs_string_bound",
        "_jcs_float_bound",
        "_jcs_bound",
        "_norm_bound",
        "_need_bound",
        "_sha_bound",
        "_domain_bound",
        "_failure_bound",
        "_deepcopy_primitive",
        "_b64encode_primitive",
        "_b64decode_primitive",
        "_sha256_primitive",
        "_json_loads_primitive",
        "_BytesIO_primitive",
        "_isfinite_primitive",
        "RenderedActivationResult",
        "RenderedActivationDecodeResult",
        "_RF",
        "Mapping",
        "_MEMBER_REGISTRY",
    ):
        monkeypatch.setattr(renderer, name, forbidden)
    monkeypatch.setattr(renderer, "RENDERED_ACTIVATION_CONTRACT", "substituted-after-resolution")
    monkeypatch.setattr(renderer, "PLANE_ORDER", ("substituted",))
    monkeypatch.setattr(renderer, "PACK_CONTRACTS", ("substituted",))
    monkeypatch.setattr(renderer, "_PROFILE_KEYS", frozenset({"substituted"}))

    repeated = bundle[1](bundle, pack, profile_raw, profile)
    assert repeated.ok, repeated.failure
    assert repeated.serialized_activation == baseline.serialized_activation

    decoded = bundle[2](bundle, baseline.serialized_activation, profile_raw, profile)
    assert decoded.ok, decoded.failure
    assert decoded.pack == pack


def test_p9r2_public_render_decode_resolve_exactly_one_fresh_bundle_per_call(monkeypatch):
    pack = _pack()
    profile_raw, profile = _profile(pack)
    real_resolve = renderer._resolve_bundle
    resolved = []

    def counting_resolve():
        bundle = real_resolve()
        resolved.append(bundle)
        return bundle

    monkeypatch.setattr(renderer, "_resolve_bundle", counting_resolve)
    rendered = renderer.render_context_pack(pack, profile_raw, profile)
    assert rendered.ok, rendered.failure
    assert len(resolved) == 1

    decoded = renderer.decode_rendered_activation(
        rendered.serialized_activation, profile_raw, profile
    )
    assert decoded.ok, decoded.failure
    assert decoded.pack == pack
    assert len(resolved) == 2
    assert resolved[0] is not resolved[1]


def test_p9r2_preserves_v1_wire_family_and_stops_before_binding_implementation():
    assert renderer.RENDERER_CONTRACT == "reasoning-distiller-context-renderer/1"
    assert renderer.RENDERER_PROFILE_CONTRACT == "reasoning-distiller-context-renderer-profile/1"
    assert renderer.RENDERED_ACTIVATION_CONTRACT == "reasoning-distiller-context-rendered-activation/1"
    assert not hasattr(renderer, "describe_bundle")
    assert not hasattr(renderer, "derive_execution_binding")
    assert not hasattr(renderer, "compare_execution_binding")
