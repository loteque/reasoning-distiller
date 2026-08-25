from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

import context_packaging.prepare_integration as prepare
import context_packaging.renderer as renderer


ROOT = Path(__file__).resolve().parents[1]
G3_BASE = "48e272e35f902a9f6e0ee4111e6220cbcef1d7cd"
COORDINATION_REVISION = "80b6e89ad2efe84b088ca06b908a257c449fac15"
GOVERNING_PLAN_COMMIT = "b435dff827b745d711a5c5a297587a0c4359bed1"
GOVERNING_PLAN_BLOB = "eae54b9e2c0618faec61acf2f9e4acd942ec063d"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = _load_module("p10_g4_package_builder", ROOT / "packaging/build_release_package.py")
installer = _load_module("p10_g4_installer", ROOT / "packaging/rd_install.py")


def _raw(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _exact_runtime() -> bool:
    return (
        sys.implementation.name == "cpython"
        and sys.version_info[:3] == (3, 12, 0)
        and sys.implementation.cache_tag == "cpython-312"
    )


def _repository_binding():
    payload_raw = b"{}"
    return {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "repository_control",
        "logical_namespace": "repo",
        "logical_source_id": "sealed-control",
        "repository": "example/project",
        "commit": "a" * 40,
        # Deliberately absent from the temporary project. G4 must not reopen it.
        "path": "evidence/original-control.json",
        "raw_sha256": _sha(payload_raw),
    }


def _snapshot_ref(binding):
    return {
        key: binding[key]
        for key in (
            "source_class",
            "logical_namespace",
            "logical_source_id",
            "repository",
            "commit",
            "path",
            "raw_sha256",
        )
    }


def _sealed_inputs():
    binding = _repository_binding()
    pack_profile = {
        "profile_id": "pack-production",
        "profile_version": "2",
        "raw_sha256": "sha256:" + "1" * 64,
    }
    eligibility_summary = {
        "consumer_contract": "reasoning-distiller-production-consumer/1",
        "consumer_id": "rd-distill",
        "policy_evidence_snapshot_id": "policy-snapshot-1",
        "decision": "eligible",
    }
    pack = {
        "contract": "reasoning-distiller-context-pack/2",
        "profile": copy.deepcopy(pack_profile),
        "request": {
            "request_id": "pack-request-1",
            "raw_sha256": "sha256:" + "2" * 64,
        },
        "source_registry": [copy.deepcopy(binding)],
        "control_plane": {
            "items": [
                {
                    "source_ref": _snapshot_ref(binding),
                    "payload": {
                        "encoding": "base64",
                        "data": "e30=",
                        "raw_sha256": binding["raw_sha256"],
                    },
                }
            ]
        },
        "knowledge_plane": {"items": []},
        "operational_evidence_plane": {"items": []},
        "inclusion_ledger": [],
        "toolchain": {
            "components": [
                {
                    "role": "jcs_serializer",
                    "contract": "jcs/1",
                    "immutable_identity": "git-blob:" + "b" * 40,
                    "raw_sha256": "sha256:" + "3" * 64,
                }
            ]
        },
        "eligibility": eligibility_summary,
        "identity": {"pack_identity_sha256": "sha256:" + "6" * 64},
    }

    binding_actual = renderer.derive_execution_binding()
    renderer_profile = {
        "contract": "reasoning-distiller-context-renderer-profile/2",
        "profile_id": "prod-default",
        "profile_version": "2",
        "supported_pack_contracts": [
            "reasoning-distiller-context-pack/1",
            "reasoning-distiller-context-pack/2",
        ],
        "pack_profile": copy.deepcopy(pack_profile),
        "renderer_execution_binding": copy.deepcopy(binding_actual),
        "framing": {
            "contract": "reasoning-distiller-context-renderer-framing/1",
            "serializer": "jcs/1",
            "text_encoding": "utf-8",
            "item_encoding": "base64",
            "plane_order": ["control", "knowledge", "operational_evidence"],
        },
        "limits": {"max_activation_bytes": 500000},
    }
    renderer_profile_raw = _raw(renderer_profile)

    eligibility = {
        "contract": "reasoning-distiller-context-profile-eligibility/1",
        "consumer": {
            "consumer_contract": eligibility_summary["consumer_contract"],
            "consumer_id": eligibility_summary["consumer_id"],
            "immutable_policy_snapshot_id": "consumer-policy-1",
        },
        "profile": copy.deepcopy(pack_profile),
        "policy_evidence": {
            "contract": "reasoning-distiller-profile-policy-evidence/1",
            "immutable_snapshot_id": eligibility_summary["policy_evidence_snapshot_id"],
            "raw_sha256": "sha256:" + "4" * 64,
        },
        "decision": "eligible",
    }
    return pack, _raw(pack), renderer_profile, renderer_profile_raw, eligibility, _raw(eligibility)


def _install_candidate(tmp_path: Path) -> tuple[Path, Path]:
    release = builder.build(
        "0.0.0-p10-g4",
        "f" * 40,
        tmp_path / "release",
        root=ROOT,
    )
    project = tmp_path / "project"
    project.mkdir()
    result = installer.install(
        release["archive"],
        release["manifest"],
        release["transport_sha256"],
        project,
    )
    assert result["status"] == "PASS"
    return project, project / ".reasoning-distiller"


def _request_for(project: Path):
    pack, pack_raw, renderer_profile, renderer_profile_raw, eligibility, eligibility_raw = _sealed_inputs()
    artifacts = project / "artifacts"
    outputs = project / "out"
    artifacts.mkdir()
    outputs.mkdir()
    (artifacts / "pack.json").write_bytes(pack_raw)
    (artifacts / "renderer-profile.json").write_bytes(renderer_profile_raw)
    (artifacts / "eligibility.json").write_bytes(eligibility_raw)
    request = {
        "contract": "reasoning-distiller-invocation/2",
        "invocation_id": "p10-g4-test",
        "created_at": "2026-08-25T12:00:00-07:00",
        "project_root": "project",
        "context": {
            "pack": {
                "contract": "reasoning-distiller-context-pack/2",
                "locator": "artifacts/pack.json",
                "raw_sha256": _sha(pack_raw),
                "pack_identity_sha256": pack["identity"]["pack_identity_sha256"],
            },
            "renderer_profile": {
                "contract": "reasoning-distiller-context-renderer-profile/2",
                "locator": "artifacts/renderer-profile.json",
                "raw_sha256": _sha(renderer_profile_raw),
                "profile_id": renderer_profile["profile_id"],
                "profile_version": renderer_profile["profile_version"],
            },
            "profile_eligibility": {
                "contract": "reasoning-distiller-context-profile-eligibility/1",
                "locator": "artifacts/eligibility.json",
                "raw_sha256": _sha(eligibility_raw),
            },
        },
        "output": {
            "raw_candidate_path": "out/raw.json",
            "submission_path": "out/submission.json",
            "prepared_invocation_path": "out/prepared.json",
            "provenance_registry_path": "out/registry.json",
            "result_path": "out/result.json",
        },
    }
    request_raw = _raw(request)
    request_path = project / "request.json"
    request_path.write_bytes(request_raw)
    return request, request_raw, request_path


def _schema_registry():
    names = [
        "activation-bundle-v2.schema.json",
        "context-provenance-registry.schema.json",
        "context-rendered-activation-v2.schema.json",
        "renderer-execution-binding.schema.json",
        "prepared-invocation.schema.json",
    ]
    schemas = [json.loads((ROOT / "schemas" / name).read_text()) for name in names]
    return Registry().with_resources(
        [(schema["$id"], Resource.from_contents(schema)) for schema in schemas]
    )


@pytest.mark.skipif(not _exact_runtime(), reason="P10 G4 exact runtime is CPython 3.12.0/cpython-312")
def test_p10_g4_prepares_from_sealed_pack_only_and_persists_exact_companions(tmp_path):
    project, installed_root = _install_candidate(tmp_path)
    request, request_raw, _ = _request_for(project)

    # The original source named by the sealed pack intentionally does not exist.
    assert not (project / "evidence/original-control.json").exists()

    result = prepare.prepare_invocation_v2(
        request_raw,
        cwd=tmp_path,
        installed_root=installed_root,
    )
    assert result.invocation_id == request["invocation_id"]
    assert result.registry_persistence.status == "PERSISTED"
    assert result.prepared_persistence.status == "PERSISTED"
    assert (project / "out/registry.json").read_bytes() == renderer._jcs(result.provenance_registry)
    assert (project / "out/prepared.json").read_bytes() == result.serialized_prepared_invocation
    assert not (project / "out/raw.json").exists()
    assert not (project / "out/submission.json").exists()
    assert not (project / "out/result.json").exists()

    prepared = result.prepared_invocation
    assert prepared["contract"] == "reasoning-distiller-prepared-invocation/1"
    assert prepared["installed_package"]["content_identity"].startswith("sha256:")
    assert prepared["runtime_abi"] == {
        "implementation": "cpython",
        "major": 3,
        "minor": 12,
        "micro": 0,
        "cache_tag": "cpython-312",
        "binding_scheme": "python-closed-bundle/1",
    }
    assert prepared["model_transport"] == {
        "contract": "reasoning-distiller-model-transport/1",
        "adapter_id": "reference",
        "adapter_content_identity": prepared["installed_package"]["content_identity"],
    }
    assert prepared["activation_bundle"]["raw_sha256"] == _sha(result.serialized_activation_bundle)
    assert result.activation_bundle["directive"]["path"] == ".reasoning-distiller/agents/distiller/DIRECTIVE.md"
    assert result.activation_bundle["instruction"] == prepare.ACTIVATION_INSTRUCTION

    registry = _schema_registry()
    activation_schema = json.loads((ROOT / "schemas/activation-bundle-v2.schema.json").read_text())
    prepared_schema = json.loads((ROOT / "schemas/prepared-invocation.schema.json").read_text())
    assert not list(Draft202012Validator(activation_schema, registry=registry).iter_errors(result.activation_bundle))
    assert not list(Draft202012Validator(prepared_schema, registry=registry).iter_errors(prepared))

    replay = prepare.prepare_invocation_v2(
        request_raw,
        cwd=tmp_path,
        installed_root=installed_root,
    )
    assert replay.registry_persistence.status == "NO_CHANGE"
    assert replay.prepared_persistence.status == "NO_CHANGE"
    assert replay.serialized_activation_bundle == result.serialized_activation_bundle
    assert replay.serialized_prepared_invocation == result.serialized_prepared_invocation


@pytest.mark.skipif(not _exact_runtime(), reason="P10 G4 exact runtime is CPython 3.12.0/cpython-312")
def test_p10_g4_cli_dispatches_v2_without_changing_v1_core(tmp_path):
    project, installed_root = _install_candidate(tmp_path)
    _, request_raw, request_path = _request_for(project)
    installed_request = project / "request.json"
    assert installed_request.read_bytes() == request_raw

    completed = subprocess.run(
        [
            sys.executable,
            str(installed_root / "runtime/rd_distill.py"),
            "prepare",
            "--request",
            str(request_path),
        ],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    activation = json.loads(completed.stdout)
    assert activation["contract"] == "reasoning-distiller-activation-bundle/2"
    prepared = json.loads((project / "out/prepared.json").read_bytes())
    assert prepared["activation_bundle"]["raw_sha256"] == _sha(completed.stdout)

    # Legacy /1 implementation remains a separate core artifact; G4 does not rewrite it.
    assert (installed_root / "runtime/rd_distill_core.py").read_bytes() == (ROOT / "runtime/rd_distill_core.py").read_bytes()


@pytest.mark.skipif(not _exact_runtime(), reason="P10 G4 exact runtime is CPython 3.12.0/cpython-312")
def test_p10_g4_fails_closed_before_provider_boundary_on_sealed_input_and_eligibility_drift(tmp_path):
    project, installed_root = _install_candidate(tmp_path)
    request, request_raw, _ = _request_for(project)

    (project / "artifacts/pack.json").write_bytes(b"{}")
    with pytest.raises(prepare.PrepareFailure) as pack_exc:
        prepare.prepare_invocation_v2(request_raw, cwd=tmp_path, installed_root=installed_root)
    assert pack_exc.value.reason_code == "CONTEXT_PACK_DIGEST_MISMATCH"
    assert not (project / "out/prepared.json").exists()
    assert not (project / "out/registry.json").exists()

    # Restore pack and make the eligibility decision ineligible while updating the sealed digest.
    pack, pack_raw, _, _, eligibility, _ = _sealed_inputs()
    (project / "artifacts/pack.json").write_bytes(pack_raw)
    eligibility["decision"] = "ineligible"
    eligibility_raw = _raw(eligibility)
    (project / "artifacts/eligibility.json").write_bytes(eligibility_raw)
    mutated = copy.deepcopy(request)
    mutated["context"]["profile_eligibility"]["raw_sha256"] = _sha(eligibility_raw)
    with pytest.raises(prepare.PrepareFailure) as eligibility_exc:
        prepare.prepare_invocation_v2(_raw(mutated), cwd=tmp_path, installed_root=installed_root)
    assert eligibility_exc.value.reason_code == "PROFILE_INELIGIBLE"
    assert not (project / "out/prepared.json").exists()
    assert not (project / "out/registry.json").exists()


@pytest.mark.skipif(not _exact_runtime(), reason="P10 G4 exact runtime is CPython 3.12.0/cpython-312")
def test_p10_g4_package_tamper_and_immutable_collision_fail_closed(tmp_path):
    project, installed_root = _install_candidate(tmp_path)
    _, request_raw, _ = _request_for(project)

    directive = installed_root / "agents/distiller/DIRECTIVE.md"
    directive.write_bytes(directive.read_bytes() + b"\nTAMPER")
    with pytest.raises(prepare.PrepareFailure) as package_exc:
        prepare.prepare_invocation_v2(request_raw, cwd=tmp_path, installed_root=installed_root)
    assert package_exc.value.reason_code == "PACKAGE_CLOSURE_INCOMPLETE"

    # Fresh installation, then seed a conflicting exact prepared-output path.
    other = tmp_path / "other"
    other.mkdir()
    project2, installed_root2 = _install_candidate(other)
    _, request_raw2, _ = _request_for(project2)
    (project2 / "out/prepared.json").write_bytes(b"different")
    with pytest.raises(prepare.PrepareFailure) as collision_exc:
        prepare.prepare_invocation_v2(request_raw2, cwd=other, installed_root=installed_root2)
    assert collision_exc.value.reason_code == "IMMUTABLE_OUTPUT_COLLISION"


def test_p10_g4_is_bounded_to_exact_stage_and_does_not_implement_transport_or_finalize():
    assert COORDINATION_REVISION == "80b6e89ad2efe84b088ca06b908a257c449fac15"
    assert GOVERNING_PLAN_COMMIT == "b435dff827b745d711a5c5a297587a0c4359bed1"
    assert GOVERNING_PLAN_BLOB == "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
    assert G3_BASE == "48e272e35f902a9f6e0ee4111e6220cbcef1d7cd"

    source = (ROOT / "context_packaging/prepare_integration.py").read_text(encoding="utf-8")
    assert "provider execution" in source
    assert "REFERENCE_TRANSPORT_ADAPTER_ID" in source
    assert "requests." not in source
    assert "urllib" not in source
    assert "subprocess" not in source
    assert "finalize" not in {name for name in prepare.__dict__ if name.startswith("finalize")}
