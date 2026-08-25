from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator

import context_packaging.finalize_integration as finalize
import context_packaging.model_transport as transport
import context_packaging.prepare_integration as prepare
import context_packaging.renderer as renderer


ROOT = Path(__file__).resolve().parents[1]
G5_CANDIDATE = "22127c82608d8bd23562a29a4f63703ccb872565"
G5_ENGINEER_EVIDENCE = "4c03957b48bec1a7df60afe3dce1dedfb9a47320"
COORDINATION_REVISION = "80b6e89ad2efe84b088ca06b908a257c449fac15"
GOVERNING_PLAN_COMMIT = "b435dff827b745d711a5c5a297587a0c4359bed1"
GOVERNING_PLAN_BLOB = "eae54b9e2c0618faec61acf2f9e4acd942ec063d"


def _load_g4_helpers():
    path = ROOT / "tests/test_context_packaging_production_integration_p10_g4.py"
    spec = importlib.util.spec_from_file_location("p10_g4_helpers_for_g6", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


G4 = _load_g4_helpers()


def _exact_runtime() -> bool:
    return (
        sys.implementation.name == "cpython"
        and sys.version_info[:3] == (3, 12, 0)
        and sys.implementation.cache_tag == "cpython-312"
    )


def _graph(source_id: str):
    return {
        "records": [
            {
                "temp_id": "r1",
                "kind": "observation",
                "statement": "The sealed source was presented to the model.",
                "provenance": {"primary": [source_id]},
            }
        ]
    }


def _prepare_and_transport(tmp_path: Path, graph=None):
    project, installed_root = G4._install_candidate(tmp_path)
    request, request_raw, request_path = G4._request_for(project)
    prepared = prepare.prepare_invocation_v2(
        request_raw,
        cwd=tmp_path,
        installed_root=installed_root,
    )
    source_id = prepared.provenance_registry["sources"][0]["source_id"]
    candidate = _graph(source_id) if graph is None else graph
    raw = renderer._jcs(candidate)
    run = transport.run_reference_transport(
        prepared.serialized_prepared_invocation,
        prepared.serialized_activation_bundle,
        expected_prepared_invocation_sha256=prepared.prepared_invocation["identity"][
            "prepared_invocation_sha256"
        ],
        provider=lambda _request: raw,
        installed_root=installed_root,
    )
    return (
        project,
        installed_root,
        request,
        request_raw,
        request_path,
        prepared,
        run,
        raw,
    )


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G6 exact runtime is CPython 3.12.0/cpython-312",
)
def test_p10_g6_finalizes_exact_g5_run_and_persists_companion_chain(tmp_path):
    (
        project,
        installed_root,
        request,
        request_raw,
        _,
        prepared,
        run,
        raw,
    ) = _prepare_and_transport(tmp_path)

    result = finalize.finalize_invocation_v2(
        request_raw,
        run.raw_model_bytes,
        run.serialized_transport_binding,
        cwd=tmp_path,
        installed_root=installed_root,
    )

    assert (project / request["output"]["raw_candidate_path"]).read_bytes() == raw
    assert (
        project / request["output"]["submission_path"]
    ).read_bytes() == result.serialized_submission
    assert (
        project / request["output"]["result_path"]
    ).read_bytes() == result.serialized_result

    assert result.result["contract"] == "reasoning-distiller-invocation-result/2"
    assert result.result["status"] == "PASS"
    assert result.result["raw_candidate"] == {
        "locator": request["output"]["raw_candidate_path"],
        "raw_sha256": finalize._sha256(raw),
        "identity_sha256": finalize._semantic_sha256(json.loads(raw)),
    }
    assert result.result["prepared_invocation"] == {
        "locator": request["output"]["prepared_invocation_path"],
        "raw_sha256": finalize._sha256(prepared.serialized_prepared_invocation),
        "identity_sha256": prepared.prepared_invocation["identity"][
            "prepared_invocation_sha256"
        ],
    }
    assert result.result["provenance_registry"] == {
        "locator": request["output"]["provenance_registry_path"],
        "raw_sha256": finalize._sha256(prepared.serialized_provenance_registry),
        "identity_sha256": prepared.provenance_registry["identity"]["registry_sha256"],
    }

    schema = json.loads((ROOT / "schemas/invocation-result-v2.schema.json").read_text())
    registry = G4._schema_registry()
    assert not list(
        Draft202012Validator(schema, registry=registry).iter_errors(result.result)
    )

    submission = result.submission
    assert submission["rgp_version"] == "rgp/1"
    assert submission["status"] == "candidate"
    assert submission["candidate_graph"] == json.loads(raw)
    assert submission["producer"] == {
        "role": "reasoning-distiller",
        "instance": request["invocation_id"],
    }
    assert submission["validation"] == {
        "status": "passed",
        "validator": "rgp-validator/1",
        "validated_at": request["created_at"],
    }


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G6 exact runtime is CPython 3.12.0/cpython-312",
)
def test_p10_g6_finalize_does_not_reopen_sealed_inputs_or_original_sources(tmp_path):
    (
        project,
        installed_root,
        _request,
        request_raw,
        _,
        _prepared,
        run,
        _raw,
    ) = _prepare_and_transport(tmp_path)

    for path in (
        project / "artifacts/pack.json",
        project / "artifacts/renderer-profile.json",
        project / "artifacts/eligibility.json",
    ):
        path.unlink()

    assert not (project / "evidence/original-control.json").exists()

    result = finalize.finalize_invocation_v2(
        request_raw,
        run.raw_model_bytes,
        run.serialized_transport_binding,
        cwd=tmp_path,
        installed_root=installed_root,
    )
    assert result.result["status"] == "PASS"


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G6 exact runtime is CPython 3.12.0/cpython-312",
)
def test_p10_g6_raw_bytes_persist_before_parse_and_provenance_rejection(tmp_path):
    (
        project,
        installed_root,
        request,
        request_raw,
        _,
        prepared,
        _run,
        _raw,
    ) = _prepare_and_transport(tmp_path)

    invalid_raw = b'{"records":'
    invalid_run = transport.run_reference_transport(
        prepared.serialized_prepared_invocation,
        prepared.serialized_activation_bundle,
        expected_prepared_invocation_sha256=prepared.prepared_invocation["identity"][
            "prepared_invocation_sha256"
        ],
        provider=lambda _request: invalid_raw,
        installed_root=installed_root,
    )
    with pytest.raises(finalize.FinalizeFailure) as parse_exc:
        finalize.finalize_invocation_v2(
            request_raw,
            invalid_run.raw_model_bytes,
            invalid_run.serialized_transport_binding,
            cwd=tmp_path,
            installed_root=installed_root,
        )
    assert parse_exc.value.stage == "parse"
    assert parse_exc.value.reason_code == "RAW_CANDIDATE_PARSE_FAILED"
    assert (project / request["output"]["raw_candidate_path"]).read_bytes() == invalid_raw
    assert not (project / request["output"]["submission_path"]).exists()
    assert not (project / request["output"]["result_path"]).exists()

    second = tmp_path / "second"
    second.mkdir()
    (
        project2,
        installed_root2,
        request2,
        request_raw2,
        _,
        prepared2,
        _,
        _,
    ) = _prepare_and_transport(second)
    unknown_graph = _graph("src:ctx:" + "0" * 64)
    unknown_raw = renderer._jcs(unknown_graph)
    unknown_run = transport.run_reference_transport(
        prepared2.serialized_prepared_invocation,
        prepared2.serialized_activation_bundle,
        expected_prepared_invocation_sha256=prepared2.prepared_invocation["identity"][
            "prepared_invocation_sha256"
        ],
        provider=lambda _request: unknown_raw,
        installed_root=installed_root2,
    )
    with pytest.raises(finalize.FinalizeFailure) as provenance_exc:
        finalize.finalize_invocation_v2(
            request_raw2,
            unknown_run.raw_model_bytes,
            unknown_run.serialized_transport_binding,
            cwd=second,
            installed_root=installed_root2,
        )
    assert provenance_exc.value.stage == "validation"
    assert provenance_exc.value.reason_code == "UNRESOLVED_PROVENANCE"
    assert (
        project2 / request2["output"]["raw_candidate_path"]
    ).read_bytes() == unknown_raw
    assert not (project2 / request2["output"]["submission_path"]).exists()


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G6 exact runtime is CPython 3.12.0/cpython-312",
)
def test_p10_g6_rejects_prepared_registry_transport_and_toolchain_drift(tmp_path):
    registry_case = tmp_path / "registry"
    registry_case.mkdir()
    (
        project,
        installed_root,
        request,
        request_raw,
        _,
        _prepared,
        run,
        raw,
    ) = _prepare_and_transport(registry_case)
    registry_path = project / request["output"]["provenance_registry_path"]
    registry_path.write_bytes(registry_path.read_bytes() + b" ")
    with pytest.raises(finalize.FinalizeFailure) as registry_exc:
        finalize.finalize_invocation_v2(
            request_raw,
            run.raw_model_bytes,
            run.serialized_transport_binding,
            cwd=registry_case,
            installed_root=installed_root,
        )
    assert registry_exc.value.reason_code == "PROVENANCE_REGISTRY_MISMATCH"
    assert (project / request["output"]["raw_candidate_path"]).read_bytes() == raw

    prepared_case = tmp_path / "prepared"
    prepared_case.mkdir()
    (
        project,
        installed_root,
        request,
        request_raw,
        _,
        _prepared,
        run,
        raw,
    ) = _prepare_and_transport(prepared_case)
    prepared_path = project / request["output"]["prepared_invocation_path"]
    prepared_path.write_bytes(prepared_path.read_bytes() + b" ")
    with pytest.raises(finalize.FinalizeFailure) as prepared_exc:
        finalize.finalize_invocation_v2(
            request_raw,
            run.raw_model_bytes,
            run.serialized_transport_binding,
            cwd=prepared_case,
            installed_root=installed_root,
        )
    assert prepared_exc.value.reason_code == "PREPARED_INVOCATION_MISMATCH"
    assert (project / request["output"]["raw_candidate_path"]).read_bytes() == raw

    transport_case = tmp_path / "transport"
    transport_case.mkdir()
    (
        project,
        installed_root,
        request,
        request_raw,
        _,
        _prepared,
        run,
        raw,
    ) = _prepare_and_transport(transport_case)
    changed_transport = copy.deepcopy(run.transport_binding)
    changed_transport["mapping"]["extra_project_context"] = True
    with pytest.raises(finalize.FinalizeFailure) as transport_exc:
        finalize.finalize_invocation_v2(
            request_raw,
            run.raw_model_bytes,
            renderer._jcs(changed_transport),
            cwd=transport_case,
            installed_root=installed_root,
        )
    assert transport_exc.value.stage == "activation"
    assert transport_exc.value.reason_code == "MODEL_TRANSPORT_NONCONFORMING"
    assert (project / request["output"]["raw_candidate_path"]).read_bytes() == raw

    directive_case = tmp_path / "directive"
    directive_case.mkdir()
    (
        project,
        installed_root,
        request,
        request_raw,
        _,
        _prepared,
        run,
        raw,
    ) = _prepare_and_transport(directive_case)
    directive = installed_root / prepare.DIRECTIVE_RELATIVE_PATH
    directive.write_bytes(directive.read_bytes() + b"\nG6-DRIFT")
    with pytest.raises(finalize.FinalizeFailure) as directive_exc:
        finalize.finalize_invocation_v2(
            request_raw,
            run.raw_model_bytes,
            run.serialized_transport_binding,
            cwd=directive_case,
            installed_root=installed_root,
        )
    assert directive_exc.value.reason_code == "DISTILLER_DIRECTIVE_MISMATCH"
    assert (project / request["output"]["raw_candidate_path"]).read_bytes() == raw


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G6 exact runtime is CPython 3.12.0/cpython-312",
)
def test_p10_g6_cli_dispatches_v2_finalize_with_exact_transport_receipt(tmp_path):
    (
        project,
        installed_root,
        request,
        _request_raw,
        request_path,
        _prepared,
        run,
        raw,
    ) = _prepare_and_transport(tmp_path)

    raw_path = project / request["output"]["raw_candidate_path"]
    transport_path = project / "transport.json"
    raw_path.write_bytes(raw)
    transport_path.write_bytes(run.serialized_transport_binding)

    completed = subprocess.run(
        [
            sys.executable,
            str(installed_root / "runtime/rd_distill.py"),
            "finalize",
            "--request",
            str(request_path),
            "--raw-candidate",
            str(raw_path),
            "--transport-binding",
            str(transport_path),
        ],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    emitted = json.loads(completed.stdout)
    assert emitted["contract"] == "reasoning-distiller-invocation-result/2"
    assert emitted["status"] == "PASS"
    assert emitted["prepared_invocation"]["identity_sha256"].startswith("sha256:")
    assert emitted["provenance_registry"]["identity_sha256"].startswith("sha256:")


def test_p10_g6_is_bound_to_exact_g5_and_stops_before_g7():
    assert G5_CANDIDATE == "22127c82608d8bd23562a29a4f63703ccb872565"
    assert G5_ENGINEER_EVIDENCE == "4c03957b48bec1a7df60afe3dce1dedfb9a47320"
    assert COORDINATION_REVISION == "80b6e89ad2efe84b088ca06b908a257c449fac15"
    assert GOVERNING_PLAN_COMMIT == "b435dff827b745d711a5c5a297587a0c4359bed1"
    assert GOVERNING_PLAN_BLOB == "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
    assert not hasattr(finalize, "rollback")
    assert not hasattr(finalize, "downgrade")
    assert not hasattr(finalize, "reconcile")
    assert not hasattr(finalize, "admit")
