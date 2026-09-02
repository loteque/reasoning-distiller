#!/usr/bin/env python3
"""Materialize a realistic context-pack/2 and /2 preparation evidence.

Evaluation-only harness. It reads the explicitly bound repository control and
admitted canonical PEMS snapshot, uses the installed Reasoning Distiller v0.6.0
context-packaging implementation, and stops after ``rd-distill prepare``.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
INSTALLED_ROOT = ROOT / ".reasoning-distiller"
sys.path.insert(0, str(INSTALLED_ROOT))

import context_packaging  # noqa: E402
from context_packaging.pack_builder import build_context_pack  # noqa: E402
from context_packaging.pems_projection import project_pems  # noqa: E402
import context_packaging.renderer as renderer  # noqa: E402
from context_packaging.source_resolver import (  # noqa: E402
    AdapterResult,
    resolve_sources,
)

COORDINATION_REVISION = "d46300a54a444cc866717986c1f5b493de3ab13f"
ENGINEER_DIRECTIVE_BLOB = "93d2397c1a94c15307af4754c19f56bc2e16a0a9"
CANONICAL_PEMS_BLOB = "bb7c474e935243b45ff02a5778a94bbcdc654d72"
CANONICAL_PEMS_SHA256 = (
    "sha256:22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061"
)
CANONICAL_COVE_BLOB = "7ff52fb925a667c4cc1782da9b475dff831e45ef"
CANONICAL_COVE_SHA256 = (
    "sha256:ce1f6dd7fe8889ce1bf126f7ec161b08fdc19a1705a2d5be350ed80b7d197e24"
)
ADMISSION_RECEIPT_BLOB = "3d35dd4af7ab868262305a79a12cbe991d1d21ef"
ADMISSION_RECEIPT_PATH = (
    "project-knowledge/admission/receipts/"
    "35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json"
)
PROJECT_CONFIG_BLOB = "1a32563b50008955294a4958c0397c02051e0530"
P10_PLAN_BLOB = "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
P10_PLAN_PATH = (
    "docs/proposals/context-packaging/p10-production-integration/"
    "03-steward-final-plan.md"
)
EXPECTED_INSTALL_CONTENT_IDENTITY = (
    "sha256:38a4742c67e869f7bd33feba9b4ea4ff6f7558e1bbd13a24336e45145e7d8478"
)
README_CANARY = "flight recorder for collective reasoning"

SELECTED_RECORD_IDS = [
    # Production invocation preserves source isolation and canonical/authority bytes.
    "pems:proposition:17f5b1cfa9f51a7f6a7ec92e",
    # Greenfield first invocation reaches a fixed provider-boundary candidate.
    "pems:proposition:07ef7998a67cb0240858f7e2",
    # Accepted install package separates content and transport identity.
    "pems:proposition:1429c6189decbce4202e5cce",
    # Self-consumption executes from .reasoning-distiller with source roots unavailable.
    "pems:proposition:12a8976258a5e212a78b485c",
    # Engineer role is protocol/framework work without project canonical authority.
    "pems:proposition:092753f85a335f184608bb93",
]


def _jcs(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def _assert_file_identity(path: Path, *, blob: str, raw_sha256: str | None = None) -> bytes:
    raw = path.read_bytes()
    actual_blob = _git_blob(raw)
    if actual_blob != blob:
        raise RuntimeError(
            f"git blob mismatch for {path}: expected={blob} actual={actual_blob}"
        )
    if raw_sha256 is not None:
        actual_sha = _sha(raw)
        if actual_sha != raw_sha256:
            raise RuntimeError(
                f"raw sha mismatch for {path}: expected={raw_sha256} actual={actual_sha}"
            )
    return raw


def _snapshot_ref(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in binding.items()
        if key not in {"contract", "repository_relationship"}
    }


def _source_ref(binding: Mapping[str, Any]) -> dict[str, str]:
    return {
        "source_class": str(binding["source_class"]),
        "logical_namespace": str(binding["logical_namespace"]),
        "logical_source_id": str(binding["logical_source_id"]),
    }


def _artifact_component(
    installed_root: Path, role: str, contract: str, relative_path: str
) -> dict[str, str]:
    raw = (installed_root / relative_path).read_bytes()
    return {
        "role": role,
        "contract": contract,
        "immutable_identity": "git-blob:" + _git_blob(raw),
        "raw_sha256": _sha(raw),
    }


def _exact_runtime() -> bool:
    return (
        sys.implementation.name == "cpython"
        and sys.version_info[:3] == (3, 12, 0)
        and sys.implementation.cache_tag == "cpython-312"
    )


def _adapter(raw: bytes):
    def resolve(binding: Mapping[str, Any], byte_limit: int) -> AdapterResult:
        if len(raw) > byte_limit:
            return AdapterResult(
                status="limit_exceeded",
                binding=deepcopy(binding),
                diagnostics=(f"exact source bytes={len(raw)} limit={byte_limit}",),
            )
        return AdapterResult(
            status="resolved",
            binding=deepcopy(binding),
            content=raw,
        )

    return resolve


def _projection_profile(installed_root: Path) -> dict[str, Any]:
    descriptor_path = installed_root / "protocols/rgp/pems2-context-closure-v1.json"
    descriptor_raw = descriptor_path.read_bytes()
    descriptor = json.loads(descriptor_raw)
    return {
        "contract": "reasoning-distiller-context-profile/1",
        "source_requirements": {
            "control_slots": [
                {
                    "slot_id": "engineer-directive",
                    "source_classes": ["repository_control"],
                    "cardinality": "one_or_more",
                }
            ],
            "operational_evidence_slots": [],
            "consistency_rules": [],
        },
        "knowledge": {
            "required": True,
            "canonical_slot_id": "canonical",
            "selector_kinds": ["record_id", "relation_id"],
            "empty_result": "reject",
            "snapshot_multiplicity": "single",
            "closure_descriptor": {
                "contract": descriptor["contract"],
                "semantic": "pems/2",
                "immutable_snapshot_id": "git-blob:" + _git_blob(descriptor_raw),
                "raw_sha256": _sha(descriptor_raw),
            },
        },
        "limits": {
            "source_resolution": {
                "max_bindings": 8,
                "max_single_source_bytes": 1_000_000,
                "max_total_source_bytes": 2_000_000,
            },
            "projection": {
                "max_records": 100,
                "max_relations": 100,
                "max_depth": 20,
                "max_bytes": 400_000,
            },
        },
    }


def _standing_condition(canonical: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "canonical_ref": _source_ref(canonical),
        "condition": "accepted_project_backend_canonical_standing",
        "canonical_snapshot_address": deepcopy(dict(canonical)),
        "canonical_fingerprint": deepcopy(dict(canonical)),
    }


def _p2p3_request(
    repo_binding: Mapping[str, Any],
    canonical_binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "contract": "reasoning-distiller-context-pack-request/1",
        "source_bindings": [deepcopy(dict(repo_binding)), deepcopy(dict(canonical_binding))],
        "slot_bindings": [
            {
                "slot_id": "engineer-directive",
                "plane": "control",
                "source_ref": _snapshot_ref(repo_binding),
            }
        ],
        "multiple_snapshot_sources": [],
        "accepted_canonical_standing": [_standing_condition(canonical_binding)],
        "knowledge_selection": {
            "snapshots": [
                {
                    "canonical_snapshot_ref": _snapshot_ref(canonical_binding),
                    "record_ids": list(SELECTED_RECORD_IDS),
                    "relation_ids": [],
                }
            ]
        },
        "consistency_requirements": [],
    }


def _pack_profile(
    installed_root: Path,
    *,
    profile_id: str,
    profile_version: str,
) -> dict[str, Any]:
    base = _projection_profile(installed_root)
    return {
        "contract": "reasoning-distiller-context-profile/2",
        "profile_id": profile_id,
        "profile_version": profile_version,
        "contracts": {
            "request": "reasoning-distiller-context-pack-request/2",
            "pack": "reasoning-distiller-context-pack/2",
            "result": "reasoning-distiller-context-pack-result/2",
            "failure": "reasoning-distiller-context-pack-failure/1",
            "source_binding": "reasoning-distiller-context-source-binding/1",
            "eligibility": "reasoning-distiller-context-profile-eligibility/1",
            "receipt": "reasoning-distiller-context-pack-receipt/1",
        },
        "source_requirements": deepcopy(base["source_requirements"]),
        "knowledge": deepcopy(base["knowledge"]),
        "limits": {
            "source_resolution": deepcopy(base["limits"]["source_resolution"]),
            "projection": deepcopy(base["limits"]["projection"]),
            "canonical_pack": {
                "max_control_items": 8,
                "max_operational_evidence_items": 8,
                "max_bytes": 600_000,
            },
            "rendering": {"max_activation_bytes": 1_000_000},
        },
        "output": {
            "serializer": "jcs/1",
            "knowledge_encoding": "pems/2",
        },
    }


def _eligibility(
    profile_binding: Mapping[str, Any],
    *,
    policy_raw: bytes,
) -> dict[str, Any]:
    policy_snapshot = "git-blob:" + P10_PLAN_BLOB
    return {
        "contract": "reasoning-distiller-context-profile-eligibility/1",
        "consumer": {
            "consumer_contract": "reasoning-distiller-invocation/2",
            "consumer_id": "rd-distill",
            "immutable_policy_snapshot_id": policy_snapshot,
        },
        "profile": deepcopy(dict(profile_binding)),
        "policy_evidence": {
            "contract": "reasoning-distiller-profile-policy-evidence/1",
            "immutable_snapshot_id": policy_snapshot,
            "raw_sha256": _sha(policy_raw),
        },
        "decision": "eligible",
    }


def _pack_request(
    p2p3: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    profile_raw: bytes,
    eligibility: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "contract": "reasoning-distiller-context-pack-request/2",
        "request_id": "realistic-context-pack-py312-d46300a5",
        "profile": {
            "profile_id": profile["profile_id"],
            "profile_version": profile["profile_version"],
            "raw_sha256": _sha(profile_raw),
        },
        "source_bindings": deepcopy(p2p3["source_bindings"]),
        "slot_bindings": deepcopy(p2p3["slot_bindings"]),
        "multiple_snapshot_sources": [],
        "accepted_canonical_standing": deepcopy(p2p3["accepted_canonical_standing"]),
        "knowledge_selection": deepcopy(p2p3["knowledge_selection"]),
        "consistency_requirements": [],
        "eligibility": deepcopy(dict(eligibility)),
        "output": {
            "pack_contract": "reasoning-distiller-context-pack/2",
            "serializer": "jcs/1",
            "knowledge_encoding": "pems/2",
        },
    }


def _renderer_profile(
    pack_profile_binding: Mapping[str, Any],
    *,
    max_activation_bytes: int,
) -> dict[str, Any]:
    return {
        "contract": "reasoning-distiller-context-renderer-profile/2",
        "profile_id": "realistic-context-pack-production-trial",
        "profile_version": "1",
        "supported_pack_contracts": [
            "reasoning-distiller-context-pack/1",
            "reasoning-distiller-context-pack/2",
        ],
        "pack_profile": deepcopy(dict(pack_profile_binding)),
        "renderer_execution_binding": renderer.derive_execution_binding(),
        "framing": {
            "contract": "reasoning-distiller-context-renderer-framing/1",
            "serializer": "jcs/1",
            "text_encoding": "utf-8",
            "item_encoding": "base64",
            "plane_order": ["control", "knowledge", "operational_evidence"],
        },
        "limits": {"max_activation_bytes": max_activation_bytes},
    }


def _write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=".context-pack-trial")
    args = parser.parse_args()

    if not _exact_runtime():
        raise RuntimeError(
            "trial requires exact CPython 3.12.0 / cpython-312; "
            f"observed={sys.implementation.name} {sys.version_info[:3]} "
            f"{sys.implementation.cache_tag}"
        )

    package_path = Path(context_packaging.__file__).resolve()
    if not package_path.is_relative_to(INSTALLED_ROOT.resolve()):
        raise RuntimeError(
            f"context_packaging imported outside installed package: {package_path}"
        )

    out_dir = (ROOT / args.out).resolve()
    if not out_dir.is_relative_to(ROOT.resolve()):
        raise RuntimeError("output directory must remain inside project root")
    out_dir.mkdir(parents=True, exist_ok=True)
    output_dir = out_dir / "out"
    output_dir.mkdir(parents=True, exist_ok=True)

    installation_raw = (INSTALLED_ROOT / ".installation/INSTALLATION.json").read_bytes()
    installation = json.loads(installation_raw)
    if installation["content_identity"] != EXPECTED_INSTALL_CONTENT_IDENTITY:
        raise RuntimeError(
            "installed package content identity drifted: "
            f"{installation['content_identity']}"
        )

    engineer_raw = _assert_file_identity(
        ROOT / "agents/engineer/DIRECTIVE.md",
        blob=ENGINEER_DIRECTIVE_BLOB,
    )
    pems_raw = _assert_file_identity(
        ROOT / "project-knowledge/canonical/pems2.jcs.json",
        blob=CANONICAL_PEMS_BLOB,
        raw_sha256=CANONICAL_PEMS_SHA256,
    )
    cove_raw = _assert_file_identity(
        ROOT / "project-knowledge/canonical/cove1.jcs.json",
        blob=CANONICAL_COVE_BLOB,
        raw_sha256=CANONICAL_COVE_SHA256,
    )
    receipt_raw = _assert_file_identity(
        ROOT / ADMISSION_RECEIPT_PATH,
        blob=ADMISSION_RECEIPT_BLOB,
    )
    project_config_raw = _assert_file_identity(
        ROOT / "project-knowledge/project.json",
        blob=PROJECT_CONFIG_BLOB,
    )
    policy_raw = _assert_file_identity(
        ROOT / P10_PLAN_PATH,
        blob=P10_PLAN_BLOB,
    )

    receipt = json.loads(receipt_raw)
    if "sha256:" + receipt["admitted_pems_sha256"].removeprefix("sha256:") != CANONICAL_PEMS_SHA256:
        raise RuntimeError("admission receipt does not bind expected current PEMS")
    if "sha256:" + receipt["admitted_cove_sha256"].removeprefix("sha256:") != CANONICAL_COVE_SHA256:
        raise RuntimeError("admission receipt does not bind expected current COVE")

    repo_binding = {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "repository_control",
        "logical_namespace": "repo",
        "logical_source_id": "engineer-directive",
        "repository": "loteque/reasoning-distiller",
        "commit": COORDINATION_REVISION,
        "path": "agents/engineer/DIRECTIVE.md",
        "raw_sha256": _sha(engineer_raw),
    }
    canonical_binding = {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "canonical_state",
        "logical_namespace": "project-knowledge",
        "logical_source_id": "canonical-pems2",
        "project_id": "reasoning-distiller",
        "backend_type": "pems-cove",
        "backend_contract": "project-canonical-backend/1",
        "backend_config_identity": "git-blob:" + _git_blob(project_config_raw),
        "immutable_snapshot_id": (
            "pems-git-blob:"
            + CANONICAL_PEMS_BLOB
            + ":cove-git-blob:"
            + CANONICAL_COVE_BLOB
        ),
        "pems_semantic": "pems/2",
        "serializer": "jcs/1",
        "pems_sha256": _sha(pems_raw),
        "standing_evidence": [
            {
                "contract": receipt["contract"],
                "immutable_snapshot_id": "git-blob:" + ADMISSION_RECEIPT_BLOB,
                "raw_sha256": _sha(receipt_raw),
            }
        ],
        "cove": {
            "cove_semantic": "cove/1",
            "pems_semantic": "pems/2",
            "serializer": "jcs/1",
            "raw_sha256": _sha(cove_raw),
        },
    }

    projection_profile = _projection_profile(INSTALLED_ROOT)
    p2p3_request = _p2p3_request(repo_binding, canonical_binding)
    resolution = resolve_sources(
        p2p3_request,
        projection_profile,
        {
            "repository_control": _adapter(engineer_raw),
            "canonical_state": _adapter(pems_raw),
        },
    )
    if not resolution.ok:
        raise RuntimeError(f"source resolution failed: {resolution.failure}")

    projection = project_pems(
        p2p3_request,
        projection_profile,
        resolution.sources,
    )
    if not projection.ok:
        raise RuntimeError(f"PEMS projection failed: {projection.failure}")
    if len(projection.items) != 1:
        raise RuntimeError(f"expected one PEMS projection, got {len(projection.items)}")

    projected = projection.items[0]
    projected_record_ids = [item["id"] for item in projected.pems["records"]]
    missing_seeds = sorted(set(SELECTED_RECORD_IDS) - set(projected_record_ids))
    if missing_seeds:
        raise RuntimeError(f"selected record IDs missing from projection: {missing_seeds}")

    profile = _pack_profile(
        INSTALLED_ROOT,
        profile_id="realistic-canonical-pems-production",
        profile_version="2",
    )
    profile_raw = _jcs(profile)
    profile_binding = {
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
        "raw_sha256": _sha(profile_raw),
    }
    eligibility = _eligibility(profile_binding, policy_raw=policy_raw)
    eligibility_raw = _jcs(eligibility)
    pack_request = _pack_request(
        p2p3_request,
        profile=profile,
        profile_raw=profile_raw,
        eligibility=eligibility,
    )
    pack_request_raw = _jcs(pack_request)

    closure_path = INSTALLED_ROOT / "protocols/rgp/pems2-context-closure-v1.json"
    closure_raw = closure_path.read_bytes()
    closure = json.loads(closure_raw)
    components = [
        _artifact_component(
            INSTALLED_ROOT,
            "pems_schema",
            "pems/2",
            "backends/pems-cove/pems-v2.schema.json",
        ),
        _artifact_component(
            INSTALLED_ROOT,
            "pems_validator",
            "reasoning-distiller-pems-v2-validator/1",
            "backends/pems-cove/validate_pems2_contract.py",
        ),
        {
            "role": "closure_descriptor",
            "contract": closure["contract"],
            "immutable_identity": "git-blob:" + _git_blob(closure_raw),
            "raw_sha256": _sha(closure_raw),
        },
        _artifact_component(
            INSTALLED_ROOT,
            "jcs_serializer",
            "jcs/1",
            "context_packaging/pems_projection.py",
        ),
        _artifact_component(
            INSTALLED_ROOT,
            "pack_builder",
            "reasoning-distiller-context-pack-builder/2",
            "context_packaging/pack_builder.py",
        ),
    ]

    pack_result = build_context_pack(
        profile_raw,
        profile,
        pack_request_raw,
        pack_request,
        resolution.sources,
        projection.items,
        components,
    )
    if not pack_result.ok:
        raise RuntimeError(f"context pack build failed: {pack_result.failure}")
    assert pack_result.pack is not None
    assert pack_result.serialized_pack is not None
    assert pack_result.receipt is not None
    pack = pack_result.pack
    pack_raw = pack_result.serialized_pack

    if README_CANARY.encode("utf-8") in pack_raw:
        raise RuntimeError("README leakage canary unexpectedly appeared in sealed pack")

    renderer_profile = _renderer_profile(
        pack["profile"],
        max_activation_bytes=profile["limits"]["rendering"]["max_activation_bytes"],
    )
    renderer_profile_raw = _jcs(renderer_profile)

    pack_path = out_dir / "pack.json"
    profile_path = out_dir / "context-profile.json"
    pack_request_path = out_dir / "context-pack-request.json"
    pack_receipt_path = out_dir / "context-pack-receipt.json"
    renderer_profile_path = out_dir / "renderer-profile.json"
    eligibility_path = out_dir / "eligibility.json"
    invocation_request_path = out_dir / "invocation-request.json"

    _write(pack_path, pack_raw)
    _write(profile_path, profile_raw)
    _write(pack_request_path, pack_request_raw)
    _write(pack_receipt_path, _jcs(pack_result.receipt))
    _write(renderer_profile_path, renderer_profile_raw)
    _write(eligibility_path, eligibility_raw)

    invocation = {
        "contract": "reasoning-distiller-invocation/2",
        "invocation_id": "realistic-context-pack-py312-d46300a5",
        "created_at": "2026-08-26T12:16:08Z",
        "project_root": ".",
        "context": {
            "pack": {
                "contract": "reasoning-distiller-context-pack/2",
                "locator": _relative(pack_path),
                "raw_sha256": _sha(pack_raw),
                "pack_identity_sha256": pack["identity"]["pack_identity_sha256"],
            },
            "renderer_profile": {
                "contract": "reasoning-distiller-context-renderer-profile/2",
                "locator": _relative(renderer_profile_path),
                "raw_sha256": _sha(renderer_profile_raw),
                "profile_id": renderer_profile["profile_id"],
                "profile_version": renderer_profile["profile_version"],
            },
            "profile_eligibility": {
                "contract": "reasoning-distiller-context-profile-eligibility/1",
                "locator": _relative(eligibility_path),
                "raw_sha256": _sha(eligibility_raw),
            },
        },
        "output": {
            "raw_candidate_path": _relative(output_dir / "raw-candidate.json"),
            "submission_path": _relative(output_dir / "submission.json"),
            "prepared_invocation_path": _relative(output_dir / "prepared-invocation.json"),
            "provenance_registry_path": _relative(output_dir / "provenance-registry.json"),
            "result_path": _relative(output_dir / "result.json"),
        },
    }
    invocation_raw = _jcs(invocation)
    _write(invocation_request_path, invocation_raw)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(INSTALLED_ROOT)
    command = [
        sys.executable,
        str(INSTALLED_ROOT / "runtime/rd_distill.py"),
        "prepare",
        "--request",
        str(invocation_request_path),
    ]
    first = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if first.returncode != 0:
        raise RuntimeError(
            "rd-distill prepare failed: "
            + first.stdout.decode("utf-8", errors="replace")
            + "\n"
            + first.stderr.decode("utf-8", errors="replace")
        )

    prepared_path = output_dir / "prepared-invocation.json"
    registry_path = output_dir / "provenance-registry.json"
    if not prepared_path.is_file() or not registry_path.is_file():
        raise RuntimeError("prepare did not persist both required companion artifacts")

    first_prepared_raw = prepared_path.read_bytes()
    first_registry_raw = registry_path.read_bytes()
    first_activation_raw = first.stdout

    second = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if second.returncode != 0:
        raise RuntimeError(
            "rd-distill prepare replay failed: "
            + second.stdout.decode("utf-8", errors="replace")
            + "\n"
            + second.stderr.decode("utf-8", errors="replace")
        )

    prepared_raw = prepared_path.read_bytes()
    registry_raw = registry_path.read_bytes()
    if prepared_raw != first_prepared_raw:
        raise RuntimeError("prepared invocation changed on exact replay")
    if registry_raw != first_registry_raw:
        raise RuntimeError("provenance registry changed on exact replay")
    if second.stdout != first_activation_raw:
        raise RuntimeError("activation bundle changed on exact replay")

    prepared = json.loads(prepared_raw)
    registry = json.loads(registry_raw)
    activation = json.loads(first_activation_raw)

    expected_runtime = {
        "implementation": "cpython",
        "major": 3,
        "minor": 12,
        "micro": 0,
        "cache_tag": "cpython-312",
        "binding_scheme": "python-closed-bundle/1",
    }
    if prepared["runtime_abi"] != expected_runtime:
        raise RuntimeError(f"unexpected prepared runtime ABI: {prepared['runtime_abi']}")
    if prepared["installed_package"]["content_identity"] != EXPECTED_INSTALL_CONTENT_IDENTITY:
        raise RuntimeError("prepared invocation does not bind installed v0.6.0 content identity")
    if prepared["context_pack"]["pack_identity_sha256"] != pack["identity"]["pack_identity_sha256"]:
        raise RuntimeError("prepared invocation pack identity mismatch")
    if registry["pack_identity_sha256"] != pack["identity"]["pack_identity_sha256"]:
        raise RuntimeError("provenance registry pack identity mismatch")
    if activation["contract"] != "reasoning-distiller-activation-bundle/2":
        raise RuntimeError("prepare stdout is not an activation-bundle/2")

    forbidden_outputs = [
        output_dir / "raw-candidate.json",
        output_dir / "submission.json",
        output_dir / "result.json",
    ]
    unexpected = [_relative(path) for path in forbidden_outputs if path.exists()]
    if unexpected:
        raise RuntimeError(f"prepare crossed the provider/finalize boundary: {unexpected}")

    summary = {
        "contract": "reasoning-distiller-realistic-context-pack-preparation-evidence/1",
        "coordination_revision": COORDINATION_REVISION,
        "runtime": {
            "implementation": sys.implementation.name,
            "version": ".".join(map(str, sys.version_info[:3])),
            "cache_tag": sys.implementation.cache_tag,
        },
        "installed_package": {
            "version": installation["version"],
            "source_commit": installation["source_commit"],
            "content_identity": installation["content_identity"],
            "transport_sha256": installation["transport_sha256"],
            "installation_raw_sha256": _sha(installation_raw),
        },
        "canonical_snapshot": {
            "pems_path": "project-knowledge/canonical/pems2.jcs.json",
            "pems_git_blob": CANONICAL_PEMS_BLOB,
            "pems_raw_sha256": _sha(pems_raw),
            "cove_path": "project-knowledge/canonical/cove1.jcs.json",
            "cove_git_blob": CANONICAL_COVE_BLOB,
            "cove_raw_sha256": _sha(cove_raw),
            "admission_receipt_path": ADMISSION_RECEIPT_PATH,
            "admission_receipt_git_blob": ADMISSION_RECEIPT_BLOB,
            "admission_receipt_raw_sha256": _sha(receipt_raw),
        },
        "selection": {
            "seed_record_ids": list(SELECTED_RECORD_IDS),
            "projected_record_ids": projected_record_ids,
            "projected_relation_ids": [item["id"] for item in projected.pems["relations"]],
            "projected_record_count": len(projected.pems["records"]),
            "projected_relation_count": len(projected.pems["relations"]),
        },
        "leakage_canary": {
            "text": README_CANARY,
            "present_in_serialized_pack": False,
        },
        "pack": {
            "contract": pack["contract"],
            "serialized_bytes": len(pack_raw),
            "raw_sha256": _sha(pack_raw),
            "pack_identity_sha256": pack["identity"]["pack_identity_sha256"],
            "manifest_sha256": pack["identity"]["manifest_sha256"],
            "selected_pems_sha256": pack["identity"]["selected_pems_sha256"],
            "receipt": deepcopy(dict(pack_result.receipt)),
        },
        "renderer_profile": {
            "raw_sha256": _sha(renderer_profile_raw),
            "profile_id": renderer_profile["profile_id"],
            "profile_version": renderer_profile["profile_version"],
            "execution_binding_identity_sha256": renderer_profile[
                "renderer_execution_binding"
            ]["identity_sha256"],
        },
        "eligibility": {
            "raw_sha256": _sha(eligibility_raw),
            "decision": eligibility["decision"],
            "policy_evidence_snapshot_id": eligibility["policy_evidence"][
                "immutable_snapshot_id"
            ],
            "policy_evidence_raw_sha256": eligibility["policy_evidence"]["raw_sha256"],
        },
        "invocation": {
            "invocation_id": invocation["invocation_id"],
            "request_raw_sha256": _sha(invocation_raw),
        },
        "provenance_registry": {
            "raw_sha256": _sha(registry_raw),
            "registry_sha256": registry["identity"]["registry_sha256"],
            "source_count": len(registry["sources"]),
            "occurrence_count": len(registry["occurrences"]),
        },
        "prepared_invocation": {
            "raw_sha256": _sha(prepared_raw),
            "prepared_invocation_sha256": prepared["identity"][
                "prepared_invocation_sha256"
            ],
            "activation_bundle_raw_sha256": prepared["activation_bundle"]["raw_sha256"],
            "activation_bundle_identity_sha256": prepared["activation_bundle"][
                "identity_sha256"
            ],
            "rendered_activation_identity_sha256": prepared["rendered_activation"][
                "activation_identity_sha256"
            ],
            "runtime_abi": deepcopy(prepared["runtime_abi"]),
            "model_transport": deepcopy(prepared["model_transport"]),
        },
        "replay": {
            "activation_bundle_byte_identical": True,
            "prepared_invocation_byte_identical": True,
            "provenance_registry_byte_identical": True,
        },
        "boundary": {
            "raw_candidate_created": False,
            "submission_created": False,
            "result_created": False,
            "model_execution_performed": False,
            "finalize_performed": False,
            "admission_or_canonical_mutation_performed": False,
        },
    }
    summary_raw = _jcs(summary)
    _write(out_dir / "evidence-summary.json", summary_raw)
    _write(out_dir / "activation-bundle.json", first_activation_raw)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
