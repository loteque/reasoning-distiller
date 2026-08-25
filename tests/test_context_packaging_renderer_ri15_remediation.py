from __future__ import annotations

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
