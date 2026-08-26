from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import context_packaging.finalize_integration as finalize
import context_packaging.model_transport as transport
import context_packaging.prepare_integration as prepare
import context_packaging.renderer as renderer

ROOT = Path.cwd()
CANDIDATE = "ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e"
CANDIDATE_TREE = "81178c5efdc8f1419a068c61a92c0571b28f69fc"
GOVERNING_PLAN = "b435dff827b745d711a5c5a297587a0c4359bed1"
DIRECT_IDS = {
    "PI-04", "PI-05", "PI-06", "PI-08", "PI-09", "PI-10", "PI-11",
    "PI-12", "PI-13", "PI-27", "PI-28", "PI-29", "PI-34", "PI-36",
    "PI-37", "PI-38", "PI-39", "PI-41", "PI-42", "PI-44", "PI-59",
}
RUNTIME_IDS = {"PI-14", "PI-52"}

PYTEST_WITNESSES = {
    "PI-01": "tests/test_context_packaging_production_integration_p10_g4.py::test_p10_g4_prepares_from_sealed_pack_only_and_persists_exact_companions",
    "PI-02": "tests/test_context_packaging_production_integration_p10_g4.py::test_p10_g4_prepares_from_sealed_pack_only_and_persists_exact_companions",
    "PI-03": "tests/test_context_packaging_production_integration_p10_g4.py::test_p10_g4_fails_closed_before_provider_boundary_on_sealed_input_and_eligibility_drift",
    "PI-07": "tests/test_context_packaging_production_integration_p10_g4.py::test_p10_g4_fails_closed_before_provider_boundary_on_sealed_input_and_eligibility_drift",
    "PI-15": "tests/test_context_packaging_production_integration_p10_g3.py::test_same_binding_is_stable_across_pack_local_positions",
    "PI-16": "tests/test_context_packaging_production_integration_p10_g3.py::test_different_immutable_snapshots_get_different_source_ids",
    "PI-17": "tests/test_context_packaging_production_integration_p10_g3.py::test_conflicting_stable_records_under_one_source_id_fail_closed",
    "PI-18": "tests/test_context_packaging_production_integration_p10_g3.py::test_unresolved_frame_source_fails_closed",
    "PI-19": "tests/test_context_packaging_production_integration_p10_g3.py::test_ambiguous_frame_source_fails_closed",
    "PI-20": "tests/test_context_packaging_production_integration_p10_g6.py::test_p10_g6_raw_bytes_persist_before_parse_and_provenance_rejection",
    "PI-21": "tests/test_context_packaging_production_integration_p10_g6.py::test_p10_g6_finalizes_exact_g5_run_and_persists_companion_chain",
    "PI-22": "tests/test_context_packaging_authority_memory_isolation_p8.py::P8AuthorityMemoryIsolationTests::test_authority_like_control_bytes_are_exact_data_not_role_state",
    "PI-23": "tests/test_context_packaging_authority_memory_isolation_p8.py::P8AuthorityMemoryIsolationTests::test_pc15_pc33_authority_like_knowledge_remains_knowledge_only",
    "PI-24": "tests/test_context_packaging_authority_memory_isolation_p8.py::P8AuthorityMemoryIsolationTests::test_pc24_pc25_pc43_operational_evidence_status_is_never_authority",
    "PI-25": "tests/test_context_packaging_deterministic_renderer_p9.py::test_pc44_activation_limit_fails_without_partial_output_or_content_reduction",
    "PI-26": "tests/test_context_packaging_authority_memory_isolation_p8.py::P8AuthorityMemoryIsolationTests::test_pc17_unselected_prior_candidate_cannot_enter_pack",
    "PI-30": "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_unsupported_provider_and_nonconforming_mapping_fail_closed",
    "PI-31": "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_unsupported_provider_and_nonconforming_mapping_fail_closed",
    "PI-32": "tests/test_context_packaging_production_integration_p10_g6.py::test_p10_g6_finalize_does_not_reopen_sealed_inputs_or_original_sources",
    "PI-33": "tests/test_context_packaging_production_integration_p10_g7.py::test_p10_g7_explicit_v2_selection_preserves_v1_and_contract_rollback",
    "PI-35": "tests/test_context_packaging_production_integration_p10_g6.py::test_p10_g6_raw_bytes_persist_before_parse_and_provenance_rejection",
    "PI-40": "tests/test_context_packaging_production_integration_p10_g7.py::test_p10_g7_true_v053_downgrade_restores_historical_manifest_and_bytes",
    "PI-43": "tests/test_context_packaging_production_integration_p10_g6.py::test_p10_g6_rejects_prepared_registry_transport_and_toolchain_drift",
    "PI-45": "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_runner_rejects_prepared_bundle_and_installed_package_drift_before_provider",
    "PI-46": "tests/test_context_packaging_production_integration_p10_g3.py::test_same_binding_is_stable_across_pack_local_positions",
    "PI-47": "tests/test_context_packaging_production_integration_p10_g3.py::test_conflicting_stable_records_under_one_source_id_fail_closed",
    "PI-48": "tests/test_context_packaging_production_integration_p10_g1.py::test_p10_g1_transport_and_handoff_boundaries_are_explicit",
    "PI-49": "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_unsupported_provider_and_nonconforming_mapping_fail_closed",
    "PI-50": "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_unsupported_provider_and_nonconforming_mapping_fail_closed",
    "PI-51": "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_reference_runner_preserves_exact_prepared_transport_and_raw_bytes",
    "PI-53": "tests/test_context_packaging_production_integration_p10_g7.py::test_p10_g7_true_v053_downgrade_restores_historical_manifest_and_bytes",
    "PI-54": "tests/test_context_packaging_production_integration_p10_g7.py::test_p10_g7_true_v053_downgrade_restores_historical_manifest_and_bytes",
    "PI-55": "tests/test_context_packaging_production_integration_p10_g7.py::test_p10_g7_explicit_v2_selection_preserves_v1_and_contract_rollback",
    "PI-56": "tests/test_context_packaging_production_integration_p10_g7.py::test_p10_g7_true_v053_downgrade_restores_historical_manifest_and_bytes",
    "PI-57": "tests/test_context_packaging_production_integration_p10_g6.py::test_p10_g6_raw_bytes_persist_before_parse_and_provenance_rejection",
    "PI-58": "tests/test_context_packaging_production_integration_p10_g6.py::test_p10_g6_rejects_prepared_registry_transport_and_toolchain_drift",
    "PI-60": "tests/test_context_packaging_production_integration_p10_g1.py::test_p10_g1_transport_and_handoff_boundaries_are_explicit",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


G4 = load_module(
    "p10_g9_witness_g4", ROOT / "tests/test_context_packaging_production_integration_p10_g4.py"
)
G0 = load_module(
    "p10_g9_witness_g0", ROOT / "tests/test_context_packaging_production_integration_p10_g0.py"
)


def raw(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def package_paths() -> tuple[Path, Path, dict[str, Any]]:
    version = os.environ["PACKAGE_VERSION"]
    manifest_path = Path(f"/tmp/package/reasoning-distiller-{version}.manifest.json")
    archive = Path(f"/tmp/package/reasoning-distiller-{version}.tar.gz")
    manifest = json.loads(manifest_path.read_text())
    assert manifest["source_commit"] == CANDIDATE
    return archive, manifest_path, manifest


def new_case(tag: str):
    archive, manifest_path, manifest = package_paths()
    base = Path("/tmp/pi-witness") / tag.lower().replace("-", "")
    if base.exists():
        shutil.rmtree(base)
    project = base / "project"
    project.mkdir(parents=True)
    installed = G4.installer.install(
        archive, manifest_path, manifest["transport_sha256"], project
    )
    assert installed["status"] == "PASS"
    request, request_raw, request_path = G4._request_for(project)
    return base, project, project / ".reasoning-distiller", request, request_raw, request_path


def prepare_cli(base: Path, project: Path, installed_root: Path, request_path: Path):
    return subprocess.run(
        [
            sys.executable,
            str(installed_root / "runtime/rd_distill.py"),
            "prepare",
            "--request",
            str(request_path),
        ],
        cwd=base,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def record_failure(case_id: str, completed, stage: str, reason: str, mechanism: str):
    assert completed.returncode != 0, completed.stderr.decode(errors="replace")
    value = json.loads(completed.stdout)
    assert value["status"] == "FAIL", value
    assert value["stage"] == stage, value
    assert value["reason_code"] == reason, value
    return {
        "id": case_id,
        "kind": "direct_installed_execution",
        "mechanism": mechanism,
        "observed_exit_code": completed.returncode,
        "observed_stage": stage,
        "observed_reason_code": reason,
    }


def assert_prepare_outputs_absent(project: Path):
    assert not (project / "out/prepared.json").exists()
    assert not (project / "out/registry.json").exists()


def direct_preflight(case_id: str, mutate, stage: str, reason: str, mechanism: str):
    base, project, installed_root, request, _, request_path = new_case(case_id)
    mutate(project, request)
    request_path.write_bytes(raw(request))
    completed = prepare_cli(base, project, installed_root, request_path)
    row = record_failure(case_id, completed, stage, reason, mechanism)
    assert_prepare_outputs_absent(project)
    return row


def prepare_transport(case_id: str, invocation_id: str | None = None, graph: dict | None = None):
    base, project, installed_root, request, _, request_path = new_case(case_id)
    if invocation_id is not None:
        request["invocation_id"] = invocation_id
        request_path.write_bytes(raw(request))
    request_raw = request_path.read_bytes()
    prepared = prepare.prepare_invocation_v2(
        request_raw, cwd=base, installed_root=installed_root
    )
    source_id = prepared.provenance_registry["sources"][0]["source_id"]
    if graph is None:
        graph = {
            "records": [
                {
                    "temp_id": "r1",
                    "kind": "observation",
                    "statement": "The sealed source was presented to the model.",
                    "provenance": {"primary": [source_id]},
                }
            ]
        }
    candidate_raw = renderer._jcs(graph)
    run = transport.run_reference_transport(
        prepared.serialized_prepared_invocation,
        prepared.serialized_activation_bundle,
        expected_prepared_invocation_sha256=prepared.prepared_invocation["identity"]["prepared_invocation_sha256"],
        provider=lambda _request: candidate_raw,
        installed_root=installed_root,
    )
    return base, project, installed_root, request, request_raw, request_path, prepared, run, candidate_raw


def finalization_failure(case_id: str, setup, expected_reason: str, mechanism: str):
    base, project, installed_root, request_raw, run, candidate_raw = setup
    with_exception = None
    try:
        finalize.finalize_invocation_v2(
            request_raw,
            candidate_raw,
            run.serialized_transport_binding,
            cwd=base,
            installed_root=installed_root,
        )
    except finalize.FinalizeFailure as exc:
        with_exception = exc
    assert with_exception is not None
    assert with_exception.stage == "validation", (with_exception.stage, with_exception.reason_code)
    assert with_exception.reason_code == expected_reason, with_exception.reason_code
    return {
        "id": case_id,
        "kind": "direct_candidate_package_execution",
        "mechanism": mechanism,
        "observed_stage": with_exception.stage,
        "observed_reason_code": with_exception.reason_code,
        "observed_exit_code": with_exception.exit_code,
    }


def run_direct() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def pi04(project, request):
        request["context"]["pack"]["pack_identity_sha256"] = "sha256:" + "0" * 64
    rows.append(direct_preflight("PI-04", pi04, "preflight", "CONTEXT_PACK_IDENTITY_MISMATCH", "request expected pack identity differs from sealed pack internal identity"))

    def pi05(project, request):
        path = project / request["context"]["renderer_profile"]["locator"]
        path.write_bytes(path.read_bytes() + b" ")
    rows.append(direct_preflight("PI-05", pi05, "preflight", "RENDERER_PROFILE_DIGEST_MISMATCH", "renderer-profile bytes drift while request digest remains frozen"))

    def pi06(project, request):
        (project / request["context"]["profile_eligibility"]["locator"]).unlink()
    rows.append(direct_preflight("PI-06", pi06, "preflight", "PROFILE_ELIGIBILITY_REQUIRED", "eligibility artifact is absent at installed /2 prepare boundary"))

    def pi08(project, request):
        path = project / request["context"]["profile_eligibility"]["locator"]
        value = json.loads(path.read_bytes())
        value["profile"]["profile_id"] = "different-pack-profile"
        data = raw(value)
        path.write_bytes(data)
        request["context"]["profile_eligibility"]["raw_sha256"] = sha(data)
    rows.append(direct_preflight("PI-08", pi08, "preflight", "PROFILE_ELIGIBILITY_MISMATCH", "eligibility artifact binds a different pack profile"))

    for field, wrong in (("consumer_contract", "reasoning-distiller-invocation/99"), ("consumer_id", "not-rd-distill")):
        base, project, installed_root, request, _, request_path = new_case("PI-09-" + field)
        pack_path = project / request["context"]["pack"]["locator"]
        eligibility_path = project / request["context"]["profile_eligibility"]["locator"]
        pack = json.loads(pack_path.read_bytes())
        eligibility = json.loads(eligibility_path.read_bytes())
        pack["eligibility"][field] = wrong
        eligibility["consumer"][field] = wrong
        pack_raw = raw(pack)
        eligibility_raw = raw(eligibility)
        pack_path.write_bytes(pack_raw)
        eligibility_path.write_bytes(eligibility_raw)
        request["context"]["pack"]["raw_sha256"] = sha(pack_raw)
        request["context"]["profile_eligibility"]["raw_sha256"] = sha(eligibility_raw)
        request_path.write_bytes(raw(request))
        completed = prepare_cli(base, project, installed_root, request_path)
        record_failure("PI-09", completed, "preflight", "PROFILE_ELIGIBILITY_MISMATCH", f"eligibility consumer {field} differs")
        assert_prepare_outputs_absent(project)
    rows.append({"id": "PI-09", "kind": "direct_installed_execution", "mechanism": "both consumer_contract and consumer_id mismatches reject through installed rd-distill", "observed_stage": "preflight", "observed_reason_code": "PROFILE_ELIGIBILITY_MISMATCH", "observed_exit_code": 2})

    def pi10(project, request):
        request["context"]["pack"]["contract"] = "reasoning-distiller-context-pack/1"
    rows.append(direct_preflight("PI-10", pi10, "preflight", "UNSUPPORTED_CONTEXT_PACK", "invocation/2 directly supplies context-pack/1"))

    def pi11(project, request):
        request["context"]["renderer_profile"]["contract"] = "reasoning-distiller-context-renderer-profile/1"
    rows.append(direct_preflight("PI-11", pi11, "preflight", "UNSUPPORTED_RENDERER_PROFILE", "invocation/2 directly supplies renderer-profile/1"))

    def pi12(project, request):
        path = project / request["context"]["renderer_profile"]["locator"]
        value = json.loads(path.read_bytes())
        value["pack_profile"]["profile_id"] = "different-pack-profile"
        data = raw(value)
        path.write_bytes(data)
        request["context"]["renderer_profile"]["raw_sha256"] = sha(data)
    rows.append(direct_preflight("PI-12", pi12, "preflight", "RENDERER_PROFILE_PACK_MISMATCH", "renderer profile pack-profile binding differs from sealed pack"))

    def pi13(project, request):
        path = project / request["context"]["renderer_profile"]["locator"]
        value = json.loads(path.read_bytes())
        binding = value["renderer_execution_binding"]
        if "runtime_abi" in binding:
            binding["runtime_abi"]["micro"] = 99
        else:
            binding["binding_sha256"] = "sha256:" + "0" * 64
        data = raw(value)
        path.write_bytes(data)
        request["context"]["renderer_profile"]["raw_sha256"] = sha(data)
    rows.append(direct_preflight("PI-13", pi13, "activation", "TOOLCHAIN_IDENTITY_MISMATCH", "stale renderer execution binding differs from exact executing bundle"))

    for case_id, field in (("PI-27", "source_context"), ("PI-28", "evidence"), ("PI-29", "source_registry")):
        def mutate(project, request, field=field):
            request[field] = {} if field != "evidence" else []
        rows.append(direct_preflight(case_id, mutate, "preflight", "INVALID_REQUEST", f"strict invocation/2 top-level shape rejects legacy/ambient field {field}"))

    base, project, installed_root, request, request_raw, _, prepared, run, candidate_raw = prepare_transport("PI-34")
    pack_path = project / request["context"]["pack"]["locator"]
    changed = pack_path.read_bytes() + b" "
    pack_path.write_bytes(changed)
    changed_request = copy.deepcopy(request)
    changed_request["context"]["pack"]["raw_sha256"] = sha(changed)
    rows.append(finalization_failure(
        "PI-34",
        (base, project, installed_root, raw(changed_request), run, candidate_raw),
        "SEALED_INPUT_MISMATCH",
        "post-prepare sealed pack and request binding change before finalize",
    ))

    invalid_graph = {"records": "not-a-list", "relations": []}
    base, project, installed_root, request, request_raw, _, prepared, run, candidate_raw = prepare_transport("PI-36", graph=invalid_graph)
    rows.append(finalization_failure(
        "PI-36",
        (base, project, installed_root, request_raw, run, candidate_raw),
        "RGP_VALIDATION_FAILED",
        "provider returns valid JSON that violates installed rgp-validator/1",
    ))
    assert (project / request["output"]["raw_candidate_path"]).read_bytes() == candidate_raw
    assert not (project / request["output"]["submission_path"]).exists()

    base, project, installed_root, request, request_raw, _, prepared, run, candidate_raw = prepare_transport("PI-37")
    raw_path = project / request["output"]["raw_candidate_path"]
    raw_path.write_bytes(b"existing-different-bytes")
    try:
        finalize.finalize_invocation_v2(request_raw, candidate_raw, run.serialized_transport_binding, cwd=base, installed_root=installed_root)
    except finalize.FinalizeFailure as exc:
        assert (exc.stage, exc.reason_code) == ("persistence", "IMMUTABLE_OUTPUT_COLLISION")
        assert raw_path.read_bytes() == b"existing-different-bytes"
        rows.append({"id": "PI-37", "kind": "direct_candidate_package_execution", "mechanism": "pre-existing raw-candidate bytes collide immutably", "observed_stage": exc.stage, "observed_reason_code": exc.reason_code, "observed_exit_code": exc.exit_code})
    else:
        raise AssertionError("PI-37 unexpectedly succeeded")

    base, project, installed_root, request, request_raw, _, prepared, run, candidate_raw = prepare_transport("PI-38")
    stores = {}
    for rel in ("project-knowledge/canonical-state.json", "admission-store/state.json", "role-store/state.json", "authority-store/state.json"):
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((rel + "\nUNCHANGED\n").encode())
        stores[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = finalize.finalize_invocation_v2(request_raw, candidate_raw, run.serialized_transport_binding, cwd=base, installed_root=installed_root)
    assert result.result["status"] == "PASS"
    assert stores == {rel: hashlib.sha256((project / rel).read_bytes()).hexdigest() for rel in stores}
    rows.append({"id": "PI-38", "kind": "direct_candidate_package_execution", "mechanism": "successful /2 finalization with canonical/admission/role/authority sentinel stores present preserves every sentinel byte", "observed_stage": "success", "observed_reason_code": None, "observed_exit_code": 0})

    outcomes = []
    for suffix, invocation_id in (("a", "p10-g9-pi39-a"), ("b", "p10-g9-pi39-b")):
        base, project, installed_root, request, request_raw, _, prepared, run, candidate_raw = prepare_transport("PI-39-" + suffix, invocation_id=invocation_id)
        result = finalize.finalize_invocation_v2(request_raw, candidate_raw, run.serialized_transport_binding, cwd=base, installed_root=installed_root)
        outcomes.append((prepared, result))
    assert outcomes[0][0].provenance_registry["identity"]["registry_sha256"] == outcomes[1][0].provenance_registry["identity"]["registry_sha256"]
    assert outcomes[0][0].prepared_invocation["context_pack"] == outcomes[1][0].prepared_invocation["context_pack"]
    assert outcomes[0][1].submission["submission_id"] != outcomes[1][1].submission["submission_id"]
    rows.append({"id": "PI-39", "kind": "direct_candidate_package_execution", "mechanism": "two invocation IDs over identical sealed context retain same registry/context identity and distinct submission IDs", "observed_stage": "success", "observed_reason_code": None, "observed_exit_code": 0})

    for case_id, rel, expected in (
        ("PI-41", "context_packaging/model_transport.py", "PACKAGE_IDENTITY_MISMATCH"),
        ("PI-42", "context_packaging/provenance_bridge.py", "PACKAGE_IDENTITY_MISMATCH"),
        ("PI-44", "validators/rgp_validator.py", "RGP_VALIDATOR_MISMATCH"),
    ):
        base, project, installed_root, request, request_raw, _, prepared, run, candidate_raw = prepare_transport(case_id)
        path = installed_root / rel
        path.write_bytes(path.read_bytes() + f"\n# {case_id} witness drift\n".encode())
        rows.append(finalization_failure(
            case_id,
            (base, project, installed_root, request_raw, run, candidate_raw),
            expected,
            f"post-prepare installed behavior drift at {rel}",
        ))

    base, project, installed_root, request, request_raw, _, prepared, run, candidate_raw = prepare_transport("PI-59")
    tracked = [
        project / request["context"]["pack"]["locator"],
        project / request["context"]["renderer_profile"]["locator"],
        project / request["context"]["profile_eligibility"]["locator"],
    ]
    originals = {path: path.read_bytes() for path in tracked}
    for path in tracked:
        path.write_bytes(path.read_bytes() + b"temporary-drift")
    for path, data in originals.items():
        path.write_bytes(data)
    result = finalize.finalize_invocation_v2(request_raw, candidate_raw, run.serialized_transport_binding, cwd=base, installed_root=installed_root)
    assert result.result["status"] == "PASS"
    rows.append({"id": "PI-59", "kind": "direct_candidate_package_execution", "mechanism": "pack/profile/eligibility bytes changed then restored exactly before finalize", "observed_stage": "success", "observed_reason_code": None, "observed_exit_code": 0})

    assert {row["id"] for row in rows} == DIRECT_IDS
    return sorted(rows, key=lambda row: row["id"])


def run_pytest_witnesses() -> dict[str, str]:
    selectors = sorted(set(PYTEST_WITNESSES.values()))
    env = os.environ.copy()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *selectors],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    Path("/tmp/pi-exact-pytest.txt").write_text(completed.stdout)
    if completed.returncode != 0:
        print(completed.stdout)
        raise SystemExit(completed.returncode)
    return PYTEST_WITNESSES


def build_ledger() -> dict[str, Any]:
    direct = {row["id"]: row for row in json.loads(Path("/tmp/pi-direct-witnesses.json").read_text())}
    runtime_log = Path("/tmp/pi-unsupported-runtime.txt").read_text()
    assert "P10_G9_UNSUPPORTED_RUNTIME_WITNESS_PASS" in runtime_log
    assert Path("/tmp/pi-exact-pytest.txt").is_file()

    frozen = {case[0]: case for case in G0.PRESSURE_CASES}
    expected_ids = [f"PI-{number:02d}" for number in range(1, 61)]
    assert list(frozen) == expected_ids
    assert set(direct) == DIRECT_IDS
    assert set(PYTEST_WITNESSES) | DIRECT_IDS | RUNTIME_IDS == set(expected_ids)

    rows = []
    for case_id in expected_ids:
        case = frozen[case_id]
        if case_id in direct:
            witness = direct[case_id]
        elif case_id in RUNTIME_IDS:
            witness = {
                "id": case_id,
                "kind": "exact_pytest_nodeid_unsupported_runtime",
                "witness_id": "tests/test_context_packaging_production_integration_p10_g7.py::test_p10_g7_v2_rejects_actual_unsupported_cpython_runtime",
                "execution_log": "/tmp/pi-unsupported-runtime.txt",
                "observed_stage": "preflight",
                "observed_reason_code": "RENDERER_RUNTIME_INCOMPATIBLE",
            }
        else:
            witness = {
                "id": case_id,
                "kind": "exact_pytest_nodeid",
                "witness_id": PYTEST_WITNESSES[case_id],
                "execution_log": "/tmp/pi-exact-pytest.txt",
            }
        rows.append({
            "id": case_id,
            "pressure_case": case[1],
            "required_outcome": case[2],
            "frozen_outcome": case[3],
            "failure_class": case[4],
            "witness": witness,
        })

    result = {
        "contract": "reasoning-distiller-p10-g9-pi-execution-ledger/2",
        "candidate": CANDIDATE,
        "candidate_tree": CANDIDATE_TREE,
        "governing_plan": GOVERNING_PLAN,
        "coverage": {
            "pressure_cases": 60,
            "direct_candidate_or_installed_execution": len(DIRECT_IDS),
            "unsupported_runtime_execution": len(RUNTIME_IDS),
            "exact_pytest_nodeid_mappings": len(PYTEST_WITNESSES),
        },
        "rows": rows,
    }
    Path("/tmp/pi-ledger.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    assert os.environ.get("CANDIDATE") == CANDIDATE
    assert os.environ.get("CANDIDATE_TREE") == CANDIDATE_TREE
    assert os.environ.get("GOVERNING_PLAN") == GOVERNING_PLAN
    if sys.argv[1:] == ["execute"]:
        direct = run_direct()
        Path("/tmp/pi-direct-witnesses.json").write_text(json.dumps(direct, indent=2, sort_keys=True) + "\n")
        run_pytest_witnesses()
        print(json.dumps(direct, indent=2, sort_keys=True))
        print("P10_G9_DIRECT_PI_WITNESSES_PASS")
        return
    if sys.argv[1:] == ["ledger"]:
        result = build_ledger()
        print(json.dumps(result, indent=2, sort_keys=True))
        print("P10_G9_PI01_PI60_EXACT_WITNESS_LEDGER_PASS")
        return
    raise SystemExit("usage: p10-g9-pi-witness-remediation.py execute|ledger")


if __name__ == "__main__":
    main()
