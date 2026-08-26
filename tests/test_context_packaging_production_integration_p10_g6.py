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
    return project, installed_root, request, request_raw, request_path, prepared, run, raw


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G6 exact runtime is CPython 3.12.0/cpython-312",
)
def test_p10_g6_finalizes_exact_g5_run_and_persists_companion_chain(tmp_path):
    project, installed_root, request, request_raw, _, prepared, run, raw = (
        _prepare_and_transport(tmp_path)
    )

    result = finalize.finalize_invocation_v2(
        request_raw,
        run.raw_model_bytes,
        run.serialized_transport_binding,
        cwd=tmp_path,
        installed_root=installed_root,
    )

    raw_path = project / request["output"]["raw_candidate_path"]
    submission_path = project / request["output"]["submission_path"]
    result_path = project / request["output"]["result_path"]
    registry_path = project / request["output"]["provenance_registry_path"]

    assert raw_path.read_bytes() == raw
    assert submission_path.read_bytes() == result.serialized_submission
    assert result_path.read_bytes() == result.serialized_result
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
        "raw_sha256": finalize._sha256(registry_path.read_bytes()),
        "identity_sha256": prepared.provenance_registry["identity"]["registry_sha256"],
    }

    schema = json.loads((ROOT / "schemas/invocation-result-v2.schema.json").read_text())
    assert not list(
        Draft202012Validator(schema, registry=G4._schema_registry()).iter_errors(
            result.result
        )
    )
    assert result.submission["rgp_version"] == "rgp/1"
    assert result.submission["status"] == "candidate"
    assert result.submission["candidate_graph"] == json.loads(raw)
    assert result.submission["producer"] == {
        "role": "reasoning-distiller",
        "instance": request["invocation_id"],
    }
    assert result.submission["validation"] == {
        "status": "passed",
        "validator": "rgp-validator/1",
        "validated_at": request["created_at"],
    }


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G6 exact runtime is CPython 3.12.0/cpython-312",
)
def test_p10_g6_finalize_does_not_reopen_sealed_inputs_or_original_sources(tmp_path):
    project, installed_root, _, request_raw, _, _, run, _ = _prepare_and_transport(
        tmp_path
    )
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
    project, installed_root, request, request_raw, _, prepared, _, _ = (
        _prepare_and_transport(tmp_path)
    )
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
    assert (parse_exc.value.stage, parse_exc.value.reason_code) == (
        "parse",
        "RAW_CANDIDATE_PARSE_FAILED",
    )
    assert (project / request["output"]["raw_candidate_path"]).read_bytes() == invalid_raw
    assert not (project / request["output"]["submission_path"]).exists()
    assert not (project / request["output"]["result_path"]).exists()

    second = tmp_path / "second"
    second.mkdir()
    project2, installed_root2, request2, request_raw2, _, prepared2, _, _ = (
        _prepare_and_transport(second)
    )
    unknown_raw = renderer._jcs(_graph("src:ctx:" + "0" * 64))
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
    cases = ["registry", "prepared", "transport", "directive"]
    for name in cases:
        root = tmp_path / name
        root.mkdir()
        project, installed_root, request, request_raw, _, _, run, raw = (
            _prepare_and_transport(root)
        )
        transport_raw = run.serialized_transport_binding
        if name == "registry":
            path = project / request["output"]["provenance_registry_path"]
            path.write_bytes(path.read_bytes() + b" ")
            expected = "PROVENANCE_REGISTRY_MISMATCH"
        elif name == "prepared":
            path = project / request["output"]["prepared_invocation_path"]
            path.write_bytes(path.read_bytes() + b" ")
            expected = "PREPARED_INVOCATION_MISMATCH"
        elif name == "transport":
            changed = copy.deepcopy(run.transport_binding)
            changed["mapping"]["extra_project_context"] = True
            transport_raw = renderer._jcs(changed)
            expected = "MODEL_TRANSPORT_NONCONFORMING"
        else:
            path = installed_root / prepare.DIRECTIVE_RELATIVE_PATH
            path.write_bytes(path.read_bytes() + b"\nG6-DRIFT")
            expected = "DISTILLER_DIRECTIVE_MISMATCH"

        with pytest.raises(finalize.FinalizeFailure) as exc:
            finalize.finalize_invocation_v2(
                request_raw,
                run.raw_model_bytes,
                transport_raw,
                cwd=root,
                installed_root=installed_root,
            )
        assert exc.value.reason_code == expected
        assert (project / request["output"]["raw_candidate_path"]).read_bytes() == raw


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G6 exact runtime is CPython 3.12.0/cpython-312",
)
def test_p10_g6_cli_dispatches_v2_finalize_with_exact_transport_receipt(tmp_path):
    project, installed_root, request, _, request_path, _, run, raw = (
        _prepare_and_transport(tmp_path)
    )
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
