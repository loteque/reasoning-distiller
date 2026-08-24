import copy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from context_packaging import (
    ContextPackBuildResult,
    PACK_BUILDER_CONTRACT_V1,
    PACK_BUILDER_CONTRACT_V2,
    PACK_CONTRACT_V1,
    PACK_CONTRACT_V2,
    ProjectedKnowledge,
    ProjectionCause,
    ResolvedSource,
    build_context_pack,
)

ROOT = Path(__file__).resolve().parents[1]
PEMS_RESOURCE_ID = (
    "urn:reasoning-distiller:schema-resource:pems-v2:"
    "git-blob:cd7683d704e8aef2842a0c1b25b453fb1dbc8030"
)


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _git_blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
    ).hexdigest()


def _ref(binding):
    source_class = binding["source_class"]
    keys = {
        "repository_control": (
            "source_class", "logical_namespace", "logical_source_id",
            "repository", "commit", "path", "raw_sha256",
        ),
        "canonical_state": (
            "source_class", "logical_namespace", "logical_source_id",
            "project_id", "backend_type", "backend_contract",
            "backend_config_identity", "immutable_snapshot_id",
            "pems_semantic", "serializer", "pems_sha256",
            "standing_evidence", "cove",
        ),
        "operational_evidence": (
            "source_class", "logical_namespace", "logical_source_id",
            "artifact_contract", "immutable_snapshot_id", "raw_sha256",
            "validation_status", "validation_result",
        ),
    }[source_class]
    return {key: copy.deepcopy(binding[key]) for key in keys if key in binding}


def _artifact_component(role, contract, rel):
    raw = (ROOT / rel).read_bytes()
    return {
        "role": role,
        "contract": contract,
        "immutable_identity": "git-blob:" + _git_blob(raw),
        "raw_sha256": _sha(raw),
    }


def _fixture(
    *,
    family=2,
    cove=False,
    accepted_operational=False,
    semantic_item=False,
    collision=False,
):
    pems = {
        "semantic": "pems/2",
        "project_id": "project",
        "records": [],
        "relations": [],
    }
    causes = ()
    record_ids = []
    relation_ids = []

    if semantic_item or collision:
        pems["records"] = [{
            "id": "shared" if collision else "record:one",
            "kind": "proposition",
            "lifecycle": "current",
            "data": {
                "statement": "keep provenance explicit",
                "proposition_kind": "observation",
                "epistemic_role": "asserted",
            },
        }]
        record_id = pems["records"][0]["id"]
        record_ids = [record_id]
        causes = (
            ProjectionCause(
                namespace="record",
                semantic_id=record_id,
                kind="request_selector",
                cause_id=f'root:["record","{record_id}"]',
            ),
            ProjectionCause(
                namespace="record",
                semantic_id=record_id,
                kind="pems_closure",
                cause_id=f'closure:["record","{record_id}"]',
            ),
        )

    if collision:
        pems["relations"] = [{
            "id": "shared",
            "kind": "references",
            "from": "shared",
            "to": "shared",
            "lifecycle": "current",
            "data": {},
        }]
        relation_ids = ["shared"]
        causes = causes + (
            ProjectionCause(
                namespace="relation",
                semantic_id="shared",
                kind="request_selector",
                cause_id='root:["relation","shared"]',
            ),
        )

    pems_raw = json.dumps(
        pems, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    control_raw = b"control-line\r\n"
    operational_raw = b"\x00evidence\xff"

    closure_path = ROOT / "protocols/rgp/pems2-context-closure-v1.json"
    closure_raw = closure_path.read_bytes()
    closure = json.loads(closure_raw.decode("utf-8"))
    closure_identity = "git-blob:" + _git_blob(closure_raw)

    if family == 2:
        profile_contract = "reasoning-distiller-context-profile/2"
        request_contract = "reasoning-distiller-context-pack-request/2"
        result_contract = "reasoning-distiller-context-pack-result/2"
        pack_contract = PACK_CONTRACT_V2
        builder_contract = PACK_BUILDER_CONTRACT_V2
    else:
        profile_contract = "reasoning-distiller-context-profile/1"
        request_contract = "reasoning-distiller-context-pack-request/1"
        result_contract = "reasoning-distiller-context-pack-result/1"
        pack_contract = PACK_CONTRACT_V1
        builder_contract = PACK_BUILDER_CONTRACT_V1

    profile = {
        "contract": profile_contract,
        "profile_id": f"p5-test-v{family}",
        "profile_version": str(family),
        "contracts": {
            "request": request_contract,
            "pack": pack_contract,
            "result": result_contract,
            "failure": "reasoning-distiller-context-pack-failure/1",
            "source_binding": "reasoning-distiller-context-source-binding/1",
            "eligibility": "reasoning-distiller-context-profile-eligibility/1",
            "receipt": "reasoning-distiller-context-pack-receipt/1",
        },
        "source_requirements": {
            "control_slots": [{
                "slot_id": "repo-control",
                "source_classes": ["repository_control"],
                "cardinality": "one_or_more",
            }],
            "operational_evidence_slots": [{
                "slot_id": "evidence",
                "cardinality": "zero_or_more",
                "accepted_statuses": [
                    "carried_unvalidated",
                    "accepted_validation_result",
                ],
            }],
            "consistency_rules": [],
        },
        "knowledge": {
            "required": True,
            "canonical_slot_id": "canonical",
            "selector_kinds": ["record_id", "relation_id"],
            "empty_result": "allow",
            "snapshot_multiplicity": "single",
            "closure_descriptor": {
                "contract": closure["contract"],
                "semantic": "pems/2",
                "immutable_snapshot_id": closure_identity,
                "raw_sha256": _sha(closure_raw),
            },
        },
        "limits": {
            "source_resolution": {
                "max_bindings": 8,
                "max_single_source_bytes": 100000,
                "max_total_source_bytes": 200000,
            },
            "projection": {
                "max_records": 100,
                "max_relations": 100,
                "max_depth": 20,
                "max_bytes": 100000,
            },
            "canonical_pack": {
                "max_control_items": 8,
                "max_operational_evidence_items": 8,
                "max_bytes": 200000,
            },
            "rendering": {"max_activation_bytes": 200000},
        },
        "output": {
            "serializer": "jcs/1",
            "knowledge_encoding": "cove/1" if cove else "pems/2",
        },
    }
    profile_raw = json.dumps(
        profile, ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8")

    repo = {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "repository_control",
        "logical_namespace": "repo",
        "logical_source_id": "engineer-directive",
        "repository": "loteque/reasoning-distiller",
        "commit": "a" * 40,
        "path": "agents/engineer/DIRECTIVE.md",
        "raw_sha256": _sha(control_raw),
    }
    canonical = {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "canonical_state",
        "logical_namespace": "canonical",
        "logical_source_id": "project-memory",
        "project_id": "project",
        "backend_type": "test",
        "backend_contract": "test-backend/1",
        "backend_config_identity": "test-config:1",
        "immutable_snapshot_id": "canonical:snapshot:1",
        "pems_semantic": "pems/2",
        "serializer": "jcs/1",
        "pems_sha256": _sha(pems_raw),
        "standing_evidence": [
            {
                "contract": "standing/1",
                "immutable_snapshot_id": "standing:1",
                "raw_sha256": "sha256:" + "B" * 64,
            },
            {
                "contract": "standing/1",
                "immutable_snapshot_id": "standing:1",
                "raw_sha256": "sha256:" + "b" * 64,
            },
        ],
    }
    operational = {
        "contract": "reasoning-distiller-context-source-binding/1",
        "source_class": "operational_evidence",
        "logical_namespace": "run",
        "logical_source_id": "evidence",
        "artifact_contract": "run-evidence/1",
        "immutable_snapshot_id": "run:1",
        "raw_sha256": _sha(operational_raw),
        "validation_status": (
            "accepted_validation_result"
            if accepted_operational
            else "carried_unvalidated"
        ),
    }
    if accepted_operational:
        operational["validation_result"] = {
            "contract": "validator-result/1",
            "validator_contract": "validator/1",
            "immutable_snapshot_id": "validation:1",
            "raw_sha256": "sha256:" + "C" * 64,
        }

    request = {
        "contract": request_contract,
        "request_id": f"request:p5:v{family}",
        "profile": {
            "profile_id": profile["profile_id"],
            "profile_version": profile["profile_version"],
            "raw_sha256": _sha(profile_raw),
        },
        "source_bindings": [repo, canonical, operational],
        "slot_bindings": [
            {
                "slot_id": "repo-control",
                "plane": "control",
                "source_ref": _ref(repo),
            },
            {
                "slot_id": "evidence",
                "plane": "operational_evidence",
                "source_ref": _ref(operational),
            },
        ],
        "multiple_snapshot_sources": [],
        "accepted_canonical_standing": [],
        "knowledge_selection": {
            "snapshots": [{
                "canonical_snapshot_ref": _ref(canonical),
                "record_ids": record_ids,
                "relation_ids": relation_ids,
            }]
        },
        "consistency_requirements": [],
        "output": {
            "pack_contract": pack_contract,
            "serializer": "jcs/1",
            "knowledge_encoding": "cove/1" if cove else "pems/2",
        },
    }
    request_raw = json.dumps(
        request, ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8")

    sources = [
        ResolvedSource(repo, control_raw),
        ResolvedSource(canonical, pems_raw),
        ResolvedSource(operational, operational_raw),
    ]
    projected = [
        ProjectedKnowledge(
            canonical_snapshot_ref=_ref(canonical),
            pems=pems,
            causes=causes,
        )
    ]
    components = [
        _artifact_component(
            "pems_schema",
            "pems/2",
            "backends/pems-cove/pems-v2.schema.json",
        ),
        _artifact_component(
            "pems_validator",
            "reasoning-distiller-pems-v2-validator/1",
            "backends/pems-cove/validate_pems2_contract.py",
        ),
        {
            "role": "closure_descriptor",
            "contract": closure["contract"],
            "immutable_identity": closure_identity,
            "raw_sha256": _sha(closure_raw),
        },
        _artifact_component(
            "jcs_serializer",
            "jcs/1",
            "context_packaging/pems_projection.py",
        ),
        _artifact_component(
            "pack_builder",
            builder_contract,
            "context_packaging/pack_builder.py",
        ),
    ]
    if cove:
        components.append(
            _artifact_component(
                "cove_adapter",
                "cove/1|pems/2|jcs/1",
                "context_packaging/cove_adapter.py",
            )
        )

    return {
        "profile": profile,
        "profile_raw": profile_raw,
        "request": request,
        "request_raw": request_raw,
        "sources": sources,
        "projected": projected,
        "components": components,
        "control_raw": control_raw,
        "operational_raw": operational_raw,
    }


def _build(fx):
    return build_context_pack(
        fx["profile_raw"],
        fx["profile"],
        fx["request_raw"],
        fx["request"],
        fx["sources"],
        fx["projected"],
        fx["components"],
    )


def _upper_sha(value):
    return "sha256:" + value[7:].upper()


def test_v2_build_is_byte_identical_and_pure_over_reordered_runtime_inputs():
    fx = _fixture(semantic_item=True)
    before = copy.deepcopy(
        (fx["profile"], fx["request"], fx["sources"], fx["projected"], fx["components"])
    )
    first = _build(fx)
    assert isinstance(first, ContextPackBuildResult)
    assert first.ok
    assert first.pack["contract"] == PACK_CONTRACT_V2
    assert first.receipt["operation"] == "build"
    assert first.receipt["result"] == "built"

    fx["sources"] = list(reversed(fx["sources"]))
    fx["components"] = list(reversed(fx["components"]))
    second = _build(fx)
    assert second.ok
    assert second.serialized_pack == first.serialized_pack
    assert second.receipt == first.receipt
    assert before[0] == fx["profile"]
    assert before[1] == fx["request"]


def test_v2_same_string_record_relation_ids_emit_distinct_pems_refs():
    result = _build(_fixture(collision=True))
    assert result.ok, result.failure
    knowledge = [
        entry for entry in result.pack["inclusion_ledger"]
        if entry["plane"] == "knowledge" and "pems_ref" in entry["subject"]
    ]
    assert {tuple(sorted(entry["subject"]["pems_ref"].items())) for entry in knowledge} == {
        (("id", "shared"), ("namespace", "record")),
        (("id", "shared"), ("namespace", "relation")),
    }
    assert all("semantic_id" not in entry["subject"] for entry in knowledge)


def test_v2_preserves_all_causes_for_one_namespaced_subject():
    result = _build(_fixture(semantic_item=True))
    assert result.ok
    entry = next(
        item for item in result.pack["inclusion_ledger"]
        if item["subject"].get("pems_ref") == {
            "namespace": "record",
            "id": "record:one",
        }
    )
    assert entry["causes"] == [
        {
            "kind": "request_selector",
            "cause_id": 'root:["record","record:one"]',
        },
        {
            "kind": "pems_closure",
            "cause_id": 'closure:["record","record:one"]',
        },
    ]


def test_v2_source_digest_case_is_identity_equivalent_and_emits_lowercase():
    baseline = _build(_fixture(semantic_item=True))
    assert baseline.ok

    fx = _fixture(semantic_item=True)
    canonical = copy.deepcopy(fx["sources"][1].binding)
    canonical["pems_sha256"] = _upper_sha(canonical["pems_sha256"])
    canonical["standing_evidence"][0]["raw_sha256"] = _upper_sha(
        canonical["standing_evidence"][0]["raw_sha256"]
    )
    fx["sources"][1] = ResolvedSource(canonical, fx["sources"][1].content)

    projected = fx["projected"][0]
    projected_ref = copy.deepcopy(projected.canonical_snapshot_ref)
    projected_ref["pems_sha256"] = _upper_sha(projected_ref["pems_sha256"])
    fx["projected"] = [
        ProjectedKnowledge(
            canonical_snapshot_ref=projected_ref,
            pems=projected.pems,
            causes=projected.causes,
        )
    ]
    result = _build(fx)
    assert result.ok, result.failure
    assert result.serialized_pack == baseline.serialized_pack

    packed_binding = next(
        item for item in result.pack["source_registry"]
        if item["source_class"] == "canonical_state"
    )
    packed_ref = result.pack["knowledge_plane"]["items"][0]["canonical_snapshot_ref"]
    assert packed_binding["pems_sha256"] == packed_binding["pems_sha256"].lower()
    assert packed_ref["pems_sha256"] == packed_ref["pems_sha256"].lower()
    assert packed_binding["standing_evidence"][0]["raw_sha256"].endswith("b" * 64)


def test_v2_toolchain_digest_case_is_identity_equivalent_and_emits_lowercase():
    baseline = _build(_fixture(semantic_item=True))
    assert baseline.ok

    fx = _fixture(semantic_item=True)
    validator = next(
        item for item in fx["components"] if item["role"] == "pems_validator"
    )
    validator["raw_sha256"] = _upper_sha(validator["raw_sha256"])
    result = _build(fx)
    assert result.ok, result.failure
    assert result.serialized_pack == baseline.serialized_pack
    packed = next(
        item for item in result.pack["toolchain"]["components"]
        if item["role"] == "pems_validator"
    )
    assert packed["raw_sha256"] == packed["raw_sha256"].lower()


def test_v2_operational_validation_result_digest_is_lowercase_without_authority_promotion():
    result = _build(_fixture(accepted_operational=True))
    assert result.ok
    item = result.pack["operational_evidence_plane"]["items"][0]
    assert item["validation_status"] == "accepted_validation_result"
    assert item["validation_result"]["raw_sha256"] == "sha256:" + "c" * 64
    serialized = result.serialized_pack.decode("utf-8")
    assert '"trusted"' not in serialized
    assert '"authorized"' not in serialized
    assert '"activated"' not in serialized


def test_v2_exact_source_bytes_are_base64_preserved_and_receipt_is_out_of_band():
    fx = _fixture()
    result = _build(fx)
    assert result.ok
    control = result.pack["control_plane"]["items"][0]["payload"]
    operational = result.pack["operational_evidence_plane"]["items"][0]["payload"]
    assert control["data"] == "Y29udHJvbC1saW5lDQo="
    assert control["raw_sha256"] == _sha(fx["control_raw"])
    assert operational["data"] == "AGV2aWRlbmNl/w=="
    assert operational["raw_sha256"] == _sha(fx["operational_raw"])
    assert "receipt" not in result.pack
    assert result.receipt["serialized_pack_sha256"] == _sha(result.serialized_pack)


def test_v2_cross_family_profile_request_combination_fails_closed():
    fx = _fixture()
    fx["request"]["contract"] = "reasoning-distiller-context-pack-request/1"
    fx["request_raw"] = json.dumps(
        fx["request"], ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8")
    result = _build(fx)
    assert not result.ok
    assert result.failure["code"] == "INVALID_REQUEST"


def test_v1_legacy_family_remains_v1_and_is_not_auto_upgraded():
    result = _build(_fixture(family=1, semantic_item=True))
    assert result.ok, result.failure
    assert result.pack["contract"] == PACK_CONTRACT_V1
    semantic = next(
        entry for entry in result.pack["inclusion_ledger"]
        if entry["plane"] == "knowledge" and "semantic_id" in entry["subject"]
    )
    assert semantic["subject"]["semantic_id"] == "record:one"
    assert "pems_ref" not in semantic["subject"]


def test_v1_collision_remains_unrepresentable_instead_of_guessing_namespace():
    result = _build(_fixture(family=1, collision=True))
    assert not result.ok
    assert result.failure["code"] == "PEMS_SEMANTIC_INVALID"
    assert result.failure["stage"] == "projection"


def test_v2_cove_output_uses_p4_adapter_and_requires_cove_toolchain_identity():
    fx = _fixture(cove=True, semantic_item=True)
    result = _build(fx)
    assert result.ok, result.failure
    item = result.pack["knowledge_plane"]["items"][0]
    assert item["cove_payload"]["cove_semantic"] == "cove/1"
    assert item["cove_payload"]["pems_semantic"] == "pems/2"
    assert "cove_payload_sha256" in result.pack["identity"]

    fx["components"] = [
        component for component in fx["components"]
        if component["role"] != "cove_adapter"
    ]
    failure = _build(fx)
    assert not failure.ok
    assert failure.failure["code"] == "TOOLCHAIN_IDENTITY_MISMATCH"


def test_v2_requires_closed_amendment_pems_resource_bytes():
    fx = _fixture()
    schema = next(item for item in fx["components"] if item["role"] == "pems_schema")
    schema["immutable_identity"] = "git-blob:" + "0" * 40
    result = _build(fx)
    assert not result.ok
    assert result.failure["code"] == "TOOLCHAIN_IDENTITY_MISMATCH"


def test_v2_toolchain_change_changes_manifest_and_pack_identity():
    fx = _fixture()
    first = _build(fx)
    assert first.ok
    mutated = copy.deepcopy(fx)
    for component in mutated["components"]:
        if component["role"] == "pems_validator":
            component["immutable_identity"] = "git-blob:" + "0" * 40
            component["raw_sha256"] = "sha256:" + "0" * 64
    second = _build(mutated)
    assert second.ok
    assert (
        first.pack["identity"]["payload_set_sha256"]
        == second.pack["identity"]["payload_set_sha256"]
    )
    assert (
        first.pack["identity"]["manifest_sha256"]
        != second.pack["identity"]["manifest_sha256"]
    )
    assert (
        first.pack["identity"]["pack_identity_sha256"]
        != second.pack["identity"]["pack_identity_sha256"]
    )


def test_v2_raw_profile_or_request_mismatch_fails_before_pack_identity():
    fx = _fixture()
    fx["profile_raw"] = fx["profile_raw"].replace(b'"p5-test-v2"', b'"p5-else-v2"', 1)
    profile_failure = _build(fx)
    assert not profile_failure.ok
    assert profile_failure.failure["code"] == "INVALID_PROFILE"

    fx = _fixture()
    fx["request_raw"] = fx["request_raw"].replace(
        b'"request:p5:v2"', b'"request:else:v2"', 1
    )
    request_failure = _build(fx)
    assert not request_failure.ok
    assert request_failure.failure["code"] == "INVALID_REQUEST"


def test_v2_pack_byte_limit_rejects_instead_of_truncating():
    fx = _fixture()
    fx["profile"]["limits"]["canonical_pack"]["max_bytes"] = 100
    fx["profile_raw"] = json.dumps(
        fx["profile"], ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8")
    fx["request"]["profile"]["raw_sha256"] = _sha(fx["profile_raw"])
    fx["request_raw"] = json.dumps(
        fx["request"], ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8")
    result = _build(fx)
    assert not result.ok
    assert result.failure["code"] == "PACK_LIMIT_EXCEEDED"
    assert result.pack is None
    assert result.serialized_pack is None


def test_v2_context_pack_schema_accepts_p5_output_and_pems_ref_collision():
    result = _build(_fixture(collision=True))
    assert result.ok, result.failure
    pack_schema = json.loads(
        (ROOT / "schemas/context-pack-v2.schema.json").read_text(encoding="utf-8")
    )
    source_schema = json.loads(
        (ROOT / "schemas/context-source-binding.schema.json").read_text(
            encoding="utf-8"
        )
    )
    pems_schema = json.loads(
        (ROOT / "backends/pems-cove/pems-v2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    registry = Registry().with_resources([
        (source_schema["$id"], Resource.from_contents(source_schema)),
        (PEMS_RESOURCE_ID, Resource.from_contents(pems_schema)),
    ])
    errors = list(
        Draft202012Validator(pack_schema, registry=registry).iter_errors(result.pack)
    )
    assert not errors, [error.message for error in errors]


def test_builder_sources_contain_no_persistence_or_filesystem_write_api():
    for rel in (
        "context_packaging/pack_builder.py",
        "context_packaging/pack_builder_v1.py",
    ):
        source = (ROOT / rel).read_text(encoding="utf-8")
        forbidden = (
            ".write_text(",
            ".write_bytes(",
            "open(",
            "os.replace(",
            "os.rename(",
            "shutil.",
            "subprocess.",
        )
        for token in forbidden:
            assert token not in source
