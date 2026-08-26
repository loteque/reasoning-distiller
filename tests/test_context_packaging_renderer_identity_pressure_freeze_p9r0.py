from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESSURE_CASES = ROOT / "tests/fixtures/p9-renderer-identity-pressure-cases-v1.json"

EXPECTED_IDS = [f"RI-{index:02d}" for index in range(1, 25)]
EXPECTED_STAGE1 = {f"RI-{index:02d}" for index in range(1, 17)}
EXPECTED_STAGE2 = {f"RI-{index:02d}" for index in range(17, 25)}
ALLOWED_RESULTS = {"success", "fail_closed", "composite"}
ALLOWED_FAILURE_CLASSES = {
    None,
    "TOOLCHAIN_IDENTITY_MISMATCH",
    "UNSUPPORTED_RENDERER",
    "TOOLCHAIN_IDENTITY_MISMATCH|RENDER_LIMIT_EXCEEDED",
}


def _fixture():
    return json.loads(PRESSURE_CASES.read_text(encoding="utf-8"))


def test_p9r0_pressure_fixture_binds_exact_governing_evidence_and_candidate():
    fixture = _fixture()
    assert fixture["contract"] == "reasoning-distiller-p9-renderer-identity-pressure-cases/1"
    assert fixture["gate"] == "P9R0"
    assert fixture["repository"] == "loteque/reasoning-distiller"
    assert fixture["blocked_candidate"] == "e961eb83d2c5dd1719b986c89a8915c102e395c3"
    assert fixture["governing_plan"] == {
        "commit": "0803bcca5343224d6feefa53c2f1b8baf1d4a8cd",
        "blob": "8474d2da42f863f0a190fd80292085176d3f97f0",
    }
    assert fixture["stage3_renderer_identity_amendment"] == {
        "commit": "373667be85521e6f0f83bf19fed3378357e51118",
        "blob": "90142ffe6b6652faceb3e8347f33fa71c8dc3ed9",
        "disposition": "P9_RENDERER_IDENTITY_STAGE3_RECONCILED_ACCEPTED_WITH_GATES",
    }


def test_p9r0_materializes_exactly_ri01_through_ri24_in_order():
    cases = _fixture()["cases"]
    ids = [case["id"] for case in cases]
    assert ids == EXPECTED_IDS
    assert len(ids) == len(set(ids)) == 24

    assert {case["id"] for case in cases if case["origin"] == "stage1"} == EXPECTED_STAGE1
    assert {case["id"] for case in cases if case["origin"] == "stage2"} == EXPECTED_STAGE2


def test_p9r0_every_case_has_stable_outcome_and_failure_class():
    for case in _fixture()["cases"]:
        assert case["slug"].strip()
        assert case["required_outcome"].strip()
        assert case["expected_result"] in ALLOWED_RESULTS
        assert case["failure_class"] in ALLOWED_FAILURE_CLASSES

        if case["expected_result"] == "success":
            assert case["failure_class"] is None
        elif case["expected_result"] == "fail_closed":
            assert case["failure_class"] in {
                "TOOLCHAIN_IDENTITY_MISMATCH",
                "UNSUPPORTED_RENDERER",
            }
        else:
            assert case["id"] == "RI-14"
            assert case["failure_class"] == (
                "TOOLCHAIN_IDENTITY_MISMATCH|RENDER_LIMIT_EXCEEDED"
            )


def test_p9r0_freezes_required_identity_attack_coverage():
    by_id = {case["id"]: case for case in _fixture()["cases"]}

    assert by_id["RI-02"]["slug"] == "stale_render_entrypoint"
    assert by_id["RI-03"]["slug"] == "stale_behavior_helper"
    assert by_id["RI-04"]["slug"] == "stale_behavior_constant"
    assert by_id["RI-08"]["slug"] == "false_caller_binding"
    assert by_id["RI-09"]["slug"] == "v1_profile_reuse"
    assert by_id["RI-15"]["slug"] == "verify_one_execute_another"
    assert by_id["RI-16"]["slug"] == "unenumerated_repository_dependency"
    assert by_id["RI-17"]["slug"] == "binding_verifier_mutation"
    assert by_id["RI-18"]["slug"] == "post_resolution_global_substitution"
    assert by_id["RI-19"]["slug"] == "mutable_closure_or_default"
    assert by_id["RI-20"]["slug"] == "runtime_micro_mismatch"
    assert by_id["RI-21"]["slug"] == "runtime_primitive_substitution"
    assert by_id["RI-22"]["slug"] == "unsupported_interpreter_family"
    assert by_id["RI-23"]["slug"] == "descriptor_noise_stability"
    assert by_id["RI-24"]["slug"] == "no_discovery_identity_validation"


def test_p9r0_does_not_claim_behavior_implementation():
    fixture = _fixture()
    assert "implementation" not in fixture
    assert "derived_binding" not in fixture
    assert "runtime_abi" not in fixture
