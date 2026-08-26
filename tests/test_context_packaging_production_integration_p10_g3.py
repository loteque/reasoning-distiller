from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import sys

import pytest

import context_packaging.provenance_bridge as bridge
from context_packaging.persistence_adapter import ImmutableOutputCollisionError

COORDINATION_REVISION = "80b6e89ad2efe84b088ca06b908a257c449fac15"
GOVERNING_PLAN_COMMIT = "b435dff827b745d711a5c5a297587a0c4359bed1"
GOVERNING_PLAN_BLOB = "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
G2_CANDIDATE = "95eac1148744d90b9074cbdfce82edfe4751f87a"

PACK_ID_A = "sha256:" + "6" * 64
PACK_ID_B = "sha256:" + "8" * 64
ACT_ID_A = "sha256:" + "7" * 64
ACT_ID_B = "sha256:" + "9" * 64


def repo_binding(name="engineer-directive", digit="4"):
    return {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "repository_control",
        "logical_namespace": "repo",
        "logical_source_id": name,
        "repository": "loteque/reasoning-distiller",
        "commit": "a" * 40,
        "path": f"agents/{name}/DIRECTIVE.md",
        "raw_sha256": "sha256:" + digit * 64,
    }


def package_binding(name="package-control", digit="5"):
    return {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "package_control",
        "logical_namespace": "package",
        "logical_source_id": name,
        "project_id": "project",
        "package_contract": "package/1",
        "immutable_package_snapshot_id": "pkg-snapshot-1",
        "artifact_locator": f"package/{name}.json",
        "raw_sha256": "sha256:" + digit * 64,
    }


def operational_binding(name="validation", digit="e"):
    return {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "operational_evidence",
        "logical_namespace": "ops",
        "logical_source_id": name,
        "artifact_contract": "validation/1",
        "immutable_snapshot_id": "validation-snapshot-1",
        "raw_sha256": "sha256:" + digit * 64,
        "validation_status": "accepted_validation_result",
        "validation_result": {
            "contract": "validation-result/1",
            "immutable_snapshot_id": "result-snapshot-1",
            "raw_sha256": "sha256:" + "f" * 64,
        },
    }


def canonical_binding(snapshot="snapshot-1", relationship=None):
    binding = {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "canonical_state",
        "logical_namespace": "canonical",
        "logical_source_id": "state",
        "project_id": "project",
        "backend_type": "filesystem",
        "backend_contract": "backend/1",
        "backend_config_identity": "config-1",
        "immutable_snapshot_id": snapshot,
        "pems_semantic": "pems/2",
        "serializer": "jcs/1",
        "pems_sha256": "sha256:" + ("b" if snapshot == "snapshot-1" else "c") * 64,
        "standing_evidence": [
            {
                "contract": "standing/1",
                "immutable_snapshot_id": "standing-1",
                "raw_sha256": "sha256:" + "d" * 64,
            }
        ],
    }
    if relationship is not None:
        binding["repository_relationship"] = {
            "repository": "loteque/reasoning-distiller",
            "commit": relationship,
        }
    return binding


def snapshot_ref(binding):
    if binding["source_class"] == "repository_control":
        keys = (
            "source_class", "logical_namespace", "logical_source_id",
            "repository", "commit", "path", "raw_sha256",
        )
    elif binding["source_class"] == "package_control":
        keys = (
            "source_class", "logical_namespace", "logical_source_id", "project_id",
            "package_contract", "immutable_package_snapshot_id", "artifact_locator",
            "raw_sha256",
        )
    elif binding["source_class"] == "canonical_state":
        keys = (
            "source_class", "logical_namespace", "logical_source_id", "project_id",
            "backend_type", "backend_contract", "backend_config_identity",
            "immutable_snapshot_id", "pems_semantic", "serializer", "pems_sha256",
            "standing_evidence", "cove",
        )
    elif binding["source_class"] == "operational_evidence":
        keys = (
            "source_class", "logical_namespace", "logical_source_id",
            "artifact_contract", "immutable_snapshot_id", "raw_sha256",
            "validation_status", "validation_result",
        )
    else:
        raise AssertionError
    return {key: deepcopy(binding[key]) for key in keys if key in binding}


def control_item(binding):
    return {
        "source_ref": snapshot_ref(binding),
        "payload": {
            "encoding": "base64",
            "data": "e30=",
            "raw_sha256": binding["raw_sha256"],
        },
    }


def knowledge_item(binding):
    return {
        "canonical_snapshot_ref": snapshot_ref(binding),
        "semantic": "pems/2",
        "serializer": "jcs/1",
        "pems": {"semantic": "pems/2", "records": [], "relations": []},
    }


def operational_item(binding):
    return {
        "source_ref": snapshot_ref(binding),
        "validation_status": binding["validation_status"],
        "validation_result": deepcopy(binding["validation_result"]),
        "payload": {
            "encoding": "base64",
            "data": "e30=",
            "raw_sha256": binding["raw_sha256"],
        },
    }


def frame(index, plane, item_index, item):
    raw = bridge._jcs(deepcopy(item))
    return {
        "frame_index": index,
        "kind": "plane_item",
        "plane": plane,
        "item_index": item_index,
        "encoding": "base64",
        "raw_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "data": base64.b64encode(raw).decode("ascii"),
    }


def make_pack(bindings, control=(), knowledge=(), operational=(), pack_id=PACK_ID_A):
    return {
        "contract": "reasoning-distiller-context-pack/2",
        "source_registry": [deepcopy(binding) for binding in bindings],
        "control_plane": {"items": [deepcopy(x) for x in control]},
        "knowledge_plane": {"items": [deepcopy(x) for x in knowledge]},
        "operational_evidence_plane": {"items": [deepcopy(x) for x in operational]},
        "identity": {"pack_identity_sha256": pack_id},
    }


def make_activation(pack, activation_id=ACT_ID_A):
    metadata = deepcopy(pack)
    for key in ("control_plane", "knowledge_plane", "operational_evidence_plane"):
        metadata.pop(key)
    metadata_raw = bridge._jcs(metadata)
    frames = [
        {
            "frame_index": 0,
            "kind": "metadata",
            "encoding": "base64",
            "raw_sha256": "sha256:" + hashlib.sha256(metadata_raw).hexdigest(),
            "data": base64.b64encode(metadata_raw).decode("ascii"),
        }
    ]
    n = 1
    for plane, key in (
        ("control", "control_plane"),
        ("knowledge", "knowledge_plane"),
        ("operational_evidence", "operational_evidence_plane"),
    ):
        for i, item in enumerate(pack[key]["items"]):
            frames.append(frame(n, plane, i, item))
            n += 1
    return {
        "contract": "reasoning-distiller-context-rendered-activation/2",
        "pack": {
            "contract": "reasoning-distiller-context-pack/2",
            "pack_identity_sha256": pack["identity"]["pack_identity_sha256"],
        },
        "frames": frames,
        "identity": {"activation_identity_sha256": activation_id},
    }


def test_g3_is_bound_to_exact_governance_and_g2_base():
    assert COORDINATION_REVISION == "80b6e89ad2efe84b088ca06b908a257c449fac15"
    assert GOVERNING_PLAN_COMMIT == "b435dff827b745d711a5c5a297587a0c4359bed1"
    assert GOVERNING_PLAN_BLOB == "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
    assert G2_CANDIDATE == "95eac1148744d90b9074cbdfce82edfe4751f87a"


def test_source_id_matches_g1_frozen_example():
    binding = {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "repository_control",
        "logical_namespace": "repo",
        "logical_source_id": "engineer-directive",
        "repository": "loteque/reasoning-distiller",
        "commit": "a" * 40,
        "path": "agents/engineer/DIRECTIVE.md",
        "raw_sha256": "sha256:" + "4" * 64,
    }
    assert bridge.derive_context_source_id(binding) == (
        "src:ctx:1c4234268966ab53aa12b1d0da51af7646b20ed33a09d99045d5dd05d09555f5"
    )


def test_registry_has_complete_stable_records_and_exact_occurrences():
    rb = repo_binding()
    cb = canonical_binding()
    pack = make_pack([rb, cb], control=[control_item(rb)], knowledge=[knowledge_item(cb)])
    result = bridge.derive_provenance_registry(pack, make_activation(pack))
    assert result.ok, result.failure
    registry = result.registry
    assert registry["pack_identity_sha256"] == PACK_ID_A
    assert registry["rendered_activation_identity_sha256"] == ACT_ID_A
    assert len(registry["sources"]) == 2
    by_class = {record["source_class"]: record for record in registry["sources"]}
    assert by_class["repository_control"]["payload_sha256"] == rb["raw_sha256"]
    assert by_class["canonical_state"]["payload_sha256"] == cb["pems_sha256"]
    assert by_class["repository_control"]["binding"] == rb
    assert by_class["canonical_state"]["binding"] == cb
    assert registry["occurrences"] == [
        {
            "pack_identity_sha256": PACK_ID_A,
            "frame_index": 1,
            "plane": "control",
            "item_index": 0,
            "source_id": by_class["repository_control"]["source_id"],
        },
        {
            "pack_identity_sha256": PACK_ID_A,
            "frame_index": 2,
            "plane": "knowledge",
            "item_index": 0,
            "source_id": by_class["canonical_state"]["source_id"],
        },
    ]
    expected_identity = "sha256:" + hashlib.sha256(
        bridge._REGISTRY_DOMAIN + bridge._jcs({
            k: v for k, v in registry.items() if k != "identity"
        })
    ).hexdigest()
    assert registry["identity"]["registry_sha256"] == expected_identity
    assert result.raw_sha256 == "sha256:" + hashlib.sha256(result.serialized_registry).hexdigest()


def test_all_four_source_classes_produce_complete_stable_records():
    repo = repo_binding("repo", "4")
    package = package_binding("pkg", "5")
    canonical = canonical_binding()
    operational = operational_binding()
    pack = make_pack(
        [repo, package, canonical, operational],
        control=[control_item(repo), control_item(package)],
        knowledge=[knowledge_item(canonical)],
        operational=[operational_item(operational)],
    )
    result = bridge.derive_provenance_registry(pack, make_activation(pack))
    assert result.ok, result.failure
    records = {record["source_class"]: record for record in result.registry["sources"]}
    assert set(records) == {
        "repository_control",
        "package_control",
        "canonical_state",
        "operational_evidence",
    }
    assert records["repository_control"]["payload_sha256"] == repo["raw_sha256"]
    assert records["package_control"]["payload_sha256"] == package["raw_sha256"]
    assert records["canonical_state"]["payload_sha256"] == canonical["pems_sha256"]
    assert records["operational_evidence"]["payload_sha256"] == operational["raw_sha256"]
    assert len(result.registry["occurrences"]) == 4


def test_model_visible_payload_digest_must_match_resolved_binding():
    binding = repo_binding("payload-drift", "4")
    item = control_item(binding)
    item["payload"]["raw_sha256"] = "sha256:" + "9" * 64
    pack = make_pack([binding], control=[item])
    result = bridge.derive_provenance_registry(pack, make_activation(pack))
    assert not result.ok
    assert result.failure["code"] == bridge.PROVENANCE_BRIDGE_INVALID
    assert "payload digest" in result.failure["diagnostics"][0]


def test_metadata_frame_must_bind_exact_pack_metadata():
    binding = repo_binding("metadata-drift", "4")
    pack = make_pack([binding], control=[control_item(binding)])
    activation = make_activation(pack)
    activation["frames"][0]["data"] = "e30="
    activation["frames"][0]["raw_sha256"] = "sha256:" + hashlib.sha256(b"{}").hexdigest()
    result = bridge.derive_provenance_registry(pack, activation)
    assert not result.ok
    assert result.failure["code"] == bridge.PROVENANCE_BRIDGE_INVALID


def test_same_binding_is_stable_across_pack_local_positions():
    shared = repo_binding("shared", "4")
    other = repo_binding("other", "5")

    pack_a = make_pack(
        [shared, other],
        control=[control_item(shared), control_item(other)],
        pack_id=PACK_ID_A,
    )
    pack_b = make_pack(
        [other, shared],
        control=[control_item(other), control_item(shared)],
        pack_id=PACK_ID_B,
    )
    result_a = bridge.derive_provenance_registry(pack_a, make_activation(pack_a, ACT_ID_A))
    result_b = bridge.derive_provenance_registry(pack_b, make_activation(pack_b, ACT_ID_B))
    assert result_a.ok and result_b.ok
    source_id = bridge.derive_context_source_id(shared)
    record_a = next(x for x in result_a.registry["sources"] if x["source_id"] == source_id)
    record_b = next(x for x in result_b.registry["sources"] if x["source_id"] == source_id)
    assert record_a == record_b
    occurrence_a = next(x for x in result_a.registry["occurrences"] if x["source_id"] == source_id)
    occurrence_b = next(x for x in result_b.registry["occurrences"] if x["source_id"] == source_id)
    assert occurrence_a["item_index"] == 0
    assert occurrence_b["item_index"] == 1
    assert occurrence_a["pack_identity_sha256"] != occurrence_b["pack_identity_sha256"]


def test_different_immutable_snapshots_get_different_source_ids():
    assert bridge.derive_context_source_id(canonical_binding("snapshot-1")) != bridge.derive_context_source_id(
        canonical_binding("snapshot-2")
    )


def test_unresolved_frame_source_fails_closed():
    registered = repo_binding("registered", "4")
    missing = repo_binding("missing", "5")
    pack = make_pack([registered], control=[control_item(missing)])
    result = bridge.derive_provenance_registry(pack, make_activation(pack))
    assert not result.ok
    assert result.failure["code"] == bridge.PROVENANCE_BRIDGE_INVALID


def test_ambiguous_frame_source_fails_closed():
    a = canonical_binding(relationship="a" * 40)
    b = canonical_binding(relationship="b" * 40)
    pack = make_pack([a, b], knowledge=[knowledge_item(a)])
    result = bridge.derive_provenance_registry(pack, make_activation(pack))
    assert not result.ok
    assert result.failure["code"] == bridge.PROVENANCE_BRIDGE_INVALID
    assert "ambiguous" in result.failure["diagnostics"][0]


def test_conflicting_stable_records_under_one_source_id_fail_closed(monkeypatch):
    a = repo_binding("a", "4")
    b = repo_binding("b", "5")
    pack = make_pack([a, b], control=[control_item(a), control_item(b)])
    monkeypatch.setattr(bridge, "_binding_digest", lambda _raw: "f" * 64)
    result = bridge.derive_provenance_registry(pack, make_activation(pack))
    assert not result.ok
    assert result.failure["code"] == bridge.PROVENANCE_SOURCE_COLLISION


def test_missing_or_reordered_plane_frame_fails_closed():
    a = repo_binding("a", "4")
    b = repo_binding("b", "5")
    pack = make_pack([a, b], control=[control_item(a), control_item(b)])
    activation = make_activation(pack)
    activation["frames"][1], activation["frames"][2] = activation["frames"][2], activation["frames"][1]
    result = bridge.derive_provenance_registry(pack, activation)
    assert not result.ok
    assert result.failure["code"] == bridge.PROVENANCE_BRIDGE_INVALID


@pytest.mark.skipif(sys.platform != "linux", reason="P6 immutable persistence requires Linux openat2")
def test_registry_persistence_is_immutable(tmp_path):
    binding = repo_binding("persisted", "4")
    pack = make_pack([binding], control=[control_item(binding)])
    result = bridge.derive_provenance_registry(pack, make_activation(pack))
    assert result.ok
    output = tmp_path / "derived"
    output.mkdir()

    first = bridge.persist_provenance_registry(
        result.serialized_registry,
        output_root=output,
        relative_path="registry.json",
        prohibited_roots=[],
    )
    second = bridge.persist_provenance_registry(
        result.serialized_registry,
        output_root=output,
        relative_path="registry.json",
        prohibited_roots=[],
    )
    assert first.status == "PERSISTED"
    assert second.status == "NO_CHANGE"

    (output / "registry.json").write_bytes(b"conflict")
    with pytest.raises(ImmutableOutputCollisionError):
        bridge.persist_provenance_registry(
            result.serialized_registry,
            output_root=output,
            relative_path="registry.json",
            prohibited_roots=[],
        )


@pytest.mark.skipif(sys.platform != "linux", reason="P6 immutable persistence requires Linux openat2")
def test_persistence_rejects_registry_identity_tampering(tmp_path):
    binding = repo_binding("tamper", "4")
    pack = make_pack([binding], control=[control_item(binding)])
    result = bridge.derive_provenance_registry(pack, make_activation(pack))
    assert result.ok
    tampered = bytearray(result.serialized_registry)
    marker = b'"registry_sha256":"sha256:'
    start = tampered.index(marker) + len(marker)
    tampered[start] = ord("0") if tampered[start] != ord("0") else ord("1")
    output = tmp_path / "derived"
    output.mkdir()
    with pytest.raises(ValueError, match="identity mismatch"):
        bridge.persist_provenance_registry(
            bytes(tampered),
            output_root=output,
            relative_path="registry.json",
            prohibited_roots=[],
        )
    assert not (output / "registry.json").exists()
