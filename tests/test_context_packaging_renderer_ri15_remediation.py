from __future__ import annotations

import dis

import context_packaging.renderer as renderer
from tests.test_context_packaging_renderer_execution_binding_p9r3 import _pack, _profile_v2


def test_ri15_substituted_resolver_cannot_verify_one_bundle_and_execute_another(monkeypatch):
    monkeypatch.setattr(renderer, "_RUNTIME_ABI_CAPTURE", renderer._EXPECTED_RUNTIME_ABI)
    truthful_binding = renderer.derive_execution_binding()
    pack = _pack()
    profile_raw, profile = _profile_v2(pack, truthful_binding)

    baseline = renderer.render_context_pack_v2(pack, profile_raw, profile)
    assert baseline.ok, baseline.failure

    captured = renderer._resolve_bundle()
    monkeypatch.setattr(renderer, "_resolve_bundle", lambda: list(captured))

    rendered = renderer.render_context_pack_v2(pack, profile_raw, profile)
    assert not rendered.ok
    assert rendered.failure["code"] == "UNSUPPORTED_RENDERER"

    decoded = renderer.decode_rendered_activation_v2(
        baseline.serialized_activation, profile_raw, profile
    )
    assert not decoded.ok
    assert decoded.failure["code"] == "UNSUPPORTED_RENDERER"


def test_v2_entrypoints_capture_resolver_once_before_bundle_resolution():
    for entrypoint in (
        renderer.render_context_pack_v2,
        renderer.decode_rendered_activation_v2,
    ):
        instructions = list(dis.get_instructions(entrypoint, show_caches=False, adaptive=False))
        resolver_loads = [
            (index, instruction)
            for index, instruction in enumerate(instructions)
            if instruction.opname == "LOAD_GLOBAL" and instruction.argval == "_resolve_bundle"
        ]
        assert len(resolver_loads) == 1
        load_index = resolver_loads[0][0]
        assert any(
            instruction.opname == "STORE_FAST" and instruction.argval == "resolver"
            for instruction in instructions[load_index + 1 :]
        )
