from __future__ import annotations

import context_packaging.renderer as renderer
import test_context_packaging_renderer_p9r4_external_execution as base


def _replace_string_constant(fn, old: str, new: str):
    constants = list(fn.__code__.co_consts)
    matches = [index for index, value in enumerate(constants) if value == old]
    assert len(matches) == 1, (old, matches)
    constants[matches[0]] = new
    return base._clone_function(fn, code=fn.__code__.replace(co_consts=tuple(constants)))


def _with_slot(slot: int, value):
    bundle = list(renderer._resolve_bundle())
    bundle[slot] = value
    return tuple(bundle)


def test_RI_02_stale_render_entrypoint_corrected():
    truthful_binding = renderer.derive_execution_binding()
    changed_entrypoint = _replace_string_constant(
        renderer._render_v2_bound,
        "activation_identity",
        "activation_identity:ri02-behavior-change",
    )
    bundle = _with_slot(103, changed_entrypoint)
    derived = bundle[108](bundle)
    assert derived != truthful_binding

    pack = base._pack()
    raw, profile = base._profile_v2(pack, truthful_binding)
    result = bundle[103](bundle, pack, raw, profile)
    assert base._failure_code(result) == "TOOLCHAIN_IDENTITY_MISMATCH"


def test_RI_17_binding_verifier_mutation_corrected():
    truthful_binding = renderer.derive_execution_binding()
    changed_verifier = _replace_string_constant(
        renderer._compare_execution_binding_bound,
        "renderer execution binding does not match independently derived bundle identity",
        "renderer execution binding does not match independently derived bundle identity [ri17 behavior change]",
    )
    bundle = _with_slot(109, changed_verifier)
    derived = bundle[108](bundle)
    assert derived != truthful_binding

    pack = base._pack()
    raw, profile = base._profile_v2(pack, truthful_binding)
    result = bundle[103](bundle, pack, raw, profile)
    assert base._failure_code(result) == "TOOLCHAIN_IDENTITY_MISMATCH"
