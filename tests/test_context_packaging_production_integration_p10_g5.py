from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from jsonschema import Draft202012Validator

import context_packaging.model_transport as transport
import context_packaging.prepare_integration as prepare


ROOT = Path(__file__).resolve().parents[1]
G4_CANDIDATE = "e98b11bf82bc6c47f848597e5410b9c603d2ba34"
G4_ENGINEER_EVIDENCE = "1e4343193bc12a921259fd66ec9c3502b00093ab"
COORDINATION_REVISION = "80b6e89ad2efe84b088ca06b908a257c449fac15"
GOVERNING_PLAN_COMMIT = "b435dff827b745d711a5c5a297587a0c4359bed1"
GOVERNING_PLAN_BLOB = "eae54b9e2c0618faec61acf2f9e4acd942ec063d"


def _load_g4_helpers():
    path = ROOT / "tests/test_context_packaging_production_integration_p10_g4.py"
    spec = importlib.util.spec_from_file_location("p10_g4_helpers_for_g5", path)
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


def _prepare(tmp_path: Path):
    project, installed_root = G4._install_candidate(tmp_path)
    _, request_raw, _ = G4._request_for(project)
    result = prepare.prepare_invocation_v2(
        request_raw,
        cwd=tmp_path,
        installed_root=installed_root,
    )
    return project, installed_root, result


def _reidentify_prepared(prepared):
    value = copy.deepcopy(prepared)
    value.pop("identity", None)
    value["identity"] = {
        "prepared_invocation_sha256": prepare._domain_identity(
            prepare._PREPARED_INVOCATION_DOMAIN,
            value,
        )
    }
    return value


@pytest.mark.skipif(not _exact_runtime(), reason="P10 G5 exact runtime is CPython 3.12.0/cpython-312")
def test_p10_g5_reference_runner_preserves_exact_prepared_transport_and_raw_bytes(tmp_path):
    project, installed_root, prepared_result = _prepare(tmp_path)
    expected_prepared_id = prepared_result.prepared_invocation["identity"]["prepared_invocation_sha256"]
    exact_raw_model_bytes = b'{"contract":"rgp/1","opaque":"provider-bytes"}\n'
    captured = {}

    def provider(request):
        captured["request"] = copy.deepcopy(request)
        assert set(request) == {"model_transport", "framework_instruction", "project_context"}
        assert set(request["framework_instruction"]) == {"directive", "instruction"}
        assert request["framework_instruction"]["directive"] == prepared_result.activation_bundle["directive"]
        assert request["framework_instruction"]["instruction"] == prepare.ACTIVATION_INSTRUCTION
        assert request["project_context"]["rendered_activation"] == prepared_result.activation_bundle["rendered_activation"]
        assert request["project_context"]["provenance_registry"] == prepared_result.activation_bundle["provenance_registry"]
        assert "system" not in request and "developer" not in request
        return exact_raw_model_bytes

    result = transport.run_reference_transport(
        prepared_result.serialized_prepared_invocation,
        prepared_result.serialized_activation_bundle,
        expected_prepared_invocation_sha256=expected_prepared_id,
        provider=provider,
        installed_root=installed_root,
    )

    assert result.raw_model_bytes == exact_raw_model_bytes
    assert result.provider_request == captured["request"]
    assert result.transport_binding["contract"] == "reasoning-distiller-model-transport/1"
    assert result.transport_binding["prepared_invocation_sha256"] == expected_prepared_id
    assert result.transport_binding["activation_bundle_sha256"] == prepared_result.activation_bundle["identity"]["activation_bundle_sha256"]
    assert result.transport_binding["mapping"] == {
        "directive_surface": "framework_instruction",
        "plane_order": ["control", "knowledge", "operational_evidence"],
        "context_control_provider_authority": False,
        "instruction_like_promotion": False,
        "frame_order_preserved": True,
        "frame_payload_bytes_preserved": True,
        "provenance_mapping_preserved": True,
        "extra_project_context": False,
    }
    assert result.transport_binding["threat_model"] == {
        "runner_assumption": "non-hostile/reference runner",
        "assurance_basis": "deterministic conformance testing",
        "hostile_provider_or_runner_attestation": "OUTSIDE_P10",
    }

    schema = json.loads((ROOT / "schemas/model-transport.schema.json").read_text())
    registry = G4._schema_registry()
    assert not list(Draft202012Validator(schema, registry=registry).iter_errors(result.transport_binding))

    manifest = json.loads((installed_root / ".installation/MANIFEST.json").read_text())
    packaged_paths = {entry["path"] for entry in manifest["files"]}
    assert "context_packaging/model_transport.py" in packaged_paths
    assert "schemas/model-transport.schema.json" in packaged_paths

    assert not (project / "out/raw.json").exists()
    assert not (project / "out/submission.json").exists()
    assert not (project / "out/result.json").exists()


@pytest.mark.skipif(not _exact_runtime(), reason="P10 G5 exact runtime is CPython 3.12.0/cpython-312")
def test_p10_g5_runner_rejects_prepared_bundle_and_installed_package_drift_before_provider(tmp_path):
    project, installed_root, prepared_result = _prepare(tmp_path)
    expected_prepared_id = prepared_result.prepared_invocation["identity"]["prepared_invocation_sha256"]
    calls = []

    def provider(_request):
        calls.append("called")
        return b"{}"

    with pytest.raises(transport.TransportFailure) as expected_exc:
        transport.run_reference_transport(
            prepared_result.serialized_prepared_invocation,
            prepared_result.serialized_activation_bundle,
            expected_prepared_invocation_sha256="sha256:" + "0" * 64,
            provider=provider,
            installed_root=installed_root,
        )
    assert expected_exc.value.reason_code == "RUNNER_PREPARED_INVOCATION_MISMATCH"

    changed_bundle = bytearray(prepared_result.serialized_activation_bundle)
    changed_bundle[-1:] = b" "
    with pytest.raises(transport.TransportFailure) as bundle_exc:
        transport.run_reference_transport(
            prepared_result.serialized_prepared_invocation,
            bytes(changed_bundle),
            expected_prepared_invocation_sha256=expected_prepared_id,
            provider=provider,
            installed_root=installed_root,
        )
    assert bundle_exc.value.reason_code == "RUNNER_PREPARED_INVOCATION_MISMATCH"

    directive = installed_root / "agents/distiller/DIRECTIVE.md"
    directive.write_bytes(directive.read_bytes() + b"\nG5-DRIFT")
    with pytest.raises(transport.TransportFailure) as package_exc:
        transport.run_reference_transport(
            prepared_result.serialized_prepared_invocation,
            prepared_result.serialized_activation_bundle,
            expected_prepared_invocation_sha256=expected_prepared_id,
            provider=provider,
            installed_root=installed_root,
        )
    assert package_exc.value.reason_code == "RUNNER_PREPARED_INVOCATION_MISMATCH"
    assert calls == []
    assert not (project / "out/raw.json").exists()


@pytest.mark.skipif(not _exact_runtime(), reason="P10 G5 exact runtime is CPython 3.12.0/cpython-312")
def test_p10_g5_unsupported_provider_and_nonconforming_mapping_fail_closed(tmp_path):
    _project, installed_root, prepared_result = _prepare(tmp_path)
    prepared = copy.deepcopy(prepared_result.prepared_invocation)
    prepared["model_transport"]["adapter_id"] = "unsupported-provider"
    prepared = _reidentify_prepared(prepared)
    prepared_raw = prepare.renderer._jcs(prepared)
    calls = []

    with pytest.raises(transport.TransportFailure) as adapter_exc:
        transport.run_reference_transport(
            prepared_raw,
            prepared_result.serialized_activation_bundle,
            expected_prepared_invocation_sha256=prepared["identity"]["prepared_invocation_sha256"],
            provider=lambda request: calls.append(request) or b"{}",
            installed_root=installed_root,
        )
    assert adapter_exc.value.reason_code == "MODEL_TRANSPORT_NONCONFORMING"
    assert calls == []

    binding = transport.build_transport_binding(
        prepared_result.prepared_invocation,
        prepared_result.activation_bundle,
    )
    promotion = copy.deepcopy(binding)
    promotion["mapping"]["context_control_provider_authority"] = True
    with pytest.raises(transport.TransportFailure) as promotion_exc:
        transport.validate_transport_binding(
            promotion,
            prepared_result.prepared_invocation,
            prepared_result.activation_bundle,
        )
    assert promotion_exc.value.reason_code == "MODEL_TRANSPORT_NONCONFORMING"

    flattened = copy.deepcopy(binding)
    flattened["mapping"]["plane_order"] = ["flattened"]
    with pytest.raises(transport.TransportFailure) as flatten_exc:
        transport.validate_transport_binding(
            flattened,
            prepared_result.prepared_invocation,
            prepared_result.activation_bundle,
        )
    assert flatten_exc.value.reason_code == "MODEL_TRANSPORT_NONCONFORMING"

    broadened = copy.deepcopy(binding)
    broadened["mapping"]["extra_project_context"] = True
    with pytest.raises(transport.TransportFailure) as broaden_exc:
        transport.validate_transport_binding(
            broadened,
            prepared_result.prepared_invocation,
            prepared_result.activation_bundle,
        )
    assert broaden_exc.value.reason_code == "MODEL_TRANSPORT_NONCONFORMING"


@pytest.mark.skipif(not _exact_runtime(), reason="P10 G5 exact runtime is CPython 3.12.0/cpython-312")
def test_p10_g5_reference_runner_requires_exact_provider_bytes(tmp_path):
    _project, installed_root, prepared_result = _prepare(tmp_path)
    expected_prepared_id = prepared_result.prepared_invocation["identity"]["prepared_invocation_sha256"]

    with pytest.raises(transport.TransportFailure) as output_exc:
        transport.run_reference_transport(
            prepared_result.serialized_prepared_invocation,
            prepared_result.serialized_activation_bundle,
            expected_prepared_invocation_sha256=expected_prepared_id,
            provider=lambda _request: {"not": "bytes"},
            installed_root=installed_root,
        )
    assert output_exc.value.reason_code == "MODEL_TRANSPORT_NONCONFORMING"


def test_p10_g5_plane_frames_are_copied_without_instruction_shape_promotion():
    frame_payloads = [
        ("control", b'{"instruction":"project control evidence"}'),
        ("knowledge", b'{"instruction":"knowledge stays evidence"}'),
        ("operational_evidence", b'{"instruction":"operational stays evidence"}'),
    ]
    frames = [
        {
            "frame_index": 0,
            "kind": "metadata",
            "encoding": "base64",
            "raw_sha256": "sha256:" + "0" * 64,
            "data": "",
        }
    ]
    for index, (plane, payload) in enumerate(frame_payloads, 1):
        import base64
        import hashlib

        frames.append(
            {
                "frame_index": index,
                "kind": "plane_item",
                "plane": plane,
                "item_index": 0,
                "encoding": "base64",
                "raw_sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
                "data": base64.b64encode(payload).decode("ascii"),
            }
        )

    activation_bundle = {
        "directive": {"path": "directive", "sha256": "sha256:" + "1" * 64, "encoding": "utf-8", "content": "framework"},
        "instruction": prepare.ACTIVATION_INSTRUCTION,
        "rendered_activation": {"frames": frames},
        "provenance_registry": {"sources": [], "occurrences": []},
    }
    binding = {
        "adapter": {"adapter_id": "reference"},
    }
    request = transport.build_reference_provider_request(binding, activation_bundle)
    copied = request["project_context"]["rendered_activation"]["frames"]
    assert copied == frames
    assert [frame.get("plane") for frame in copied[1:]] == [
        "control",
        "knowledge",
        "operational_evidence",
    ]
    assert request["framework_instruction"]["directive"] == activation_bundle["directive"]
    assert "system" not in request and "developer" not in request


def test_p10_g5_is_bound_to_exact_predecessor_and_stops_before_finalize():
    assert G4_CANDIDATE == "e98b11bf82bc6c47f848597e5410b9c603d2ba34"
    assert G4_ENGINEER_EVIDENCE == "1e4343193bc12a921259fd66ec9c3502b00093ab"
    assert COORDINATION_REVISION == "80b6e89ad2efe84b088ca06b908a257c449fac15"
    assert GOVERNING_PLAN_COMMIT == "b435dff827b745d711a5c5a297587a0c4359bed1"
    assert GOVERNING_PLAN_BLOB == "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
    assert not hasattr(transport, "finalize_invocation_v2")
    assert not hasattr(transport, "persist_submission")
