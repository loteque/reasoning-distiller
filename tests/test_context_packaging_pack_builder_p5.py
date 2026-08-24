import copy
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from context_packaging import ContextPackBuildResult, ProjectedKnowledge, ProjectionCause, ResolvedSource, build_context_pack
from context_packaging.pack_builder import PACK_BUILDER_CONTRACT
ROOT = Path(__file__).resolve().parents[1]

def _sha(raw: bytes) -> str:
    return 'sha256:' + hashlib.sha256(raw).hexdigest()

def _git_blob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\x00' + raw).hexdigest()

def _ref(binding):
    source_class = binding['source_class']
    keys = {'repository_control': ('source_class', 'logical_namespace', 'logical_source_id', 'repository', 'commit', 'path', 'raw_sha256'), 'canonical_state': ('source_class', 'logical_namespace', 'logical_source_id', 'project_id', 'backend_type', 'backend_contract', 'backend_config_identity', 'immutable_snapshot_id', 'pems_semantic', 'serializer', 'pems_sha256', 'standing_evidence', 'cove'), 'operational_evidence': ('source_class', 'logical_namespace', 'logical_source_id', 'artifact_contract', 'immutable_snapshot_id', 'raw_sha256', 'validation_status', 'validation_result')}[source_class]
    return {key: copy.deepcopy(binding[key]) for key in keys if key in binding}

def _artifact_component(role, contract, rel):
    raw = (ROOT / rel).read_bytes()
    return {'role': role, 'contract': contract, 'immutable_identity': 'git-blob:' + _git_blob(raw), 'raw_sha256': _sha(raw)}

def _fixture(*, cove=False, accepted_operational=False, semantic_item=False):
    pems = {'semantic': 'pems/2', 'project_id': 'project', 'records': [], 'relations': []}
    causes = ()
    if semantic_item:
        pems['records'] = [{'id': 'record:one', 'kind': 'requirement', 'lifecycle': 'current', 'data': {'text': 'keep provenance explicit'}}]
        causes = (ProjectionCause(namespace='record', semantic_id='record:one', kind='request_selector', cause_id='p3:["request_selector","record","record:one"]'), ProjectionCause(namespace='record', semantic_id='record:one', kind='pems_closure', cause_id='p3:["pems_closure","rule","record","record:one"]'))
    pems_raw = json.dumps(pems, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    control_raw = b'control-line\r\n'
    operational_raw = b'\x00evidence\xff'
    closure_path = ROOT / 'protocols/rgp/pems2-context-closure-v1.json'
    closure_raw = closure_path.read_bytes()
    closure = json.loads(closure_raw.decode('utf-8'))
    closure_identity = 'git-blob:' + _git_blob(closure_raw)
    profile = {'contract': 'reasoning-distiller-context-profile/1', 'profile_id': 'p5-test', 'profile_version': '1', 'contracts': {'request': 'reasoning-distiller-context-pack-request/1', 'pack': 'reasoning-distiller-context-pack/1', 'result': 'reasoning-distiller-context-pack-result/1', 'failure': 'reasoning-distiller-context-pack-failure/1', 'source_binding': 'reasoning-distiller-context-source-binding/1', 'eligibility': 'reasoning-distiller-context-profile-eligibility/1', 'receipt': 'reasoning-distiller-context-pack-receipt/1'}, 'source_requirements': {'control_slots': [{'slot_id': 'repo-control', 'source_classes': ['repository_control'], 'cardinality': 'one_or_more'}], 'operational_evidence_slots': [{'slot_id': 'evidence', 'cardinality': 'zero_or_more', 'accepted_statuses': ['carried_unvalidated', 'accepted_validation_result']}], 'consistency_rules': []}, 'knowledge': {'required': True, 'canonical_slot_id': 'canonical', 'selector_kinds': ['record_id', 'relation_id'], 'empty_result': 'allow', 'snapshot_multiplicity': 'single', 'closure_descriptor': {'contract': closure['contract'], 'semantic': 'pems/2', 'immutable_snapshot_id': closure_identity, 'raw_sha256': _sha(closure_raw)}}, 'limits': {'source_resolution': {'max_bindings': 8, 'max_single_source_bytes': 100000, 'max_total_source_bytes': 200000}, 'projection': {'max_records': 100, 'max_relations': 100, 'max_depth': 20, 'max_bytes': 100000}, 'canonical_pack': {'max_control_items': 8, 'max_operational_evidence_items': 8, 'max_bytes': 200000}, 'rendering': {'max_activation_bytes': 200000}}, 'output': {'serializer': 'jcs/1', 'knowledge_encoding': 'cove/1' if cove else 'pems/2'}}
    profile_raw = json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8')
    repo = {'contract': 'reasoning-distiller-context-source-binding/1', 'source_class': 'repository_control', 'logical_namespace': 'repo', 'logical_source_id': 'engineer-directive', 'repository': 'loteque/reasoning-distiller', 'commit': 'a' * 40, 'path': 'agents/engineer/DIRECTIVE.md', 'raw_sha256': _sha(control_raw)}
    canonical = {'contract': 'reasoning-distiller-context-source-binding/1', 'source_class': 'canonical_state', 'logical_namespace': 'canonical', 'logical_source_id': 'project-memory', 'project_id': 'project', 'backend_type': 'test', 'backend_contract': 'test-backend/1', 'backend_config_identity': 'test-config:1', 'immutable_snapshot_id': 'canonical:snapshot:1', 'pems_semantic': 'pems/2', 'serializer': 'jcs/1', 'pems_sha256': _sha(pems_raw), 'standing_evidence': [{'contract': 'standing/1', 'immutable_snapshot_id': 'standing:1', 'raw_sha256': 'sha256:' + 'B' * 64}, {'contract': 'standing/1', 'immutable_snapshot_id': 'standing:1', 'raw_sha256': 'sha256:' + 'b' * 64}]}
    operational = {'contract': 'reasoning-distiller-context-source-binding/1', 'source_class': 'operational_evidence', 'logical_namespace': 'run', 'logical_source_id': 'evidence', 'artifact_contract': 'run-evidence/1', 'immutable_snapshot_id': 'run:1', 'raw_sha256': _sha(operational_raw), 'validation_status': 'accepted_validation_result' if accepted_operational else 'carried_unvalidated'}
    if accepted_operational:
        operational['validation_result'] = {'contract': 'validator-result/1', 'validator_contract': 'validator/1', 'immutable_snapshot_id': 'validation:1', 'raw_sha256': 'sha256:' + 'c' * 64}
    request = {'contract': 'reasoning-distiller-context-pack-request/1', 'request_id': 'request:p5', 'profile': {'profile_id': profile['profile_id'], 'profile_version': profile['profile_version'], 'raw_sha256': _sha(profile_raw)}, 'source_bindings': [repo, canonical, operational], 'slot_bindings': [{'slot_id': 'repo-control', 'plane': 'control', 'source_ref': _ref(repo)}, {'slot_id': 'evidence', 'plane': 'operational_evidence', 'source_ref': _ref(operational)}], 'multiple_snapshot_sources': [], 'accepted_canonical_standing': [], 'knowledge_selection': {'snapshots': [{'canonical_snapshot_ref': _ref(canonical), 'record_ids': ['record:one'] if semantic_item else [], 'relation_ids': []}]}, 'consistency_requirements': [], 'output': {'pack_contract': 'reasoning-distiller-context-pack/1', 'serializer': 'jcs/1', 'knowledge_encoding': 'cove/1' if cove else 'pems/2'}}
    request_raw = json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8')
    sources = [ResolvedSource(repo, control_raw), ResolvedSource(canonical, pems_raw), ResolvedSource(operational, operational_raw)]
    projected = [ProjectedKnowledge(canonical_snapshot_ref=_ref(canonical), pems=pems, causes=causes)]
    components = [_artifact_component('pems_schema', 'pems/2', 'backends/pems-cove/pems-v2.schema.json'), _artifact_component('pems_validator', 'reasoning-distiller-pems-v2-validator/1', 'backends/pems-cove/validate_pems2_contract.py'), {'role': 'closure_descriptor', 'contract': closure['contract'], 'immutable_identity': closure_identity, 'raw_sha256': _sha(closure_raw)}, _artifact_component('jcs_serializer', 'jcs/1', 'context_packaging/pems_projection.py'), _artifact_component('pack_builder', PACK_BUILDER_CONTRACT, 'context_packaging/pack_builder.py')]
    if cove:
        components.append(_artifact_component('cove_adapter', 'cove/1|pems/2|jcs/1', 'context_packaging/cove_adapter.py'))
    return {'profile': profile, 'profile_raw': profile_raw, 'request': request, 'request_raw': request_raw, 'sources': sources, 'projected': projected, 'components': components, 'control_raw': control_raw, 'operational_raw': operational_raw}

def _build(fx):
    return build_context_pack(fx['profile_raw'], fx['profile'], fx['request_raw'], fx['request'], fx['sources'], fx['projected'], fx['components'])

def test_p5_build_is_byte_identical_and_pure_over_reordered_runtime_inputs():
    fx = _fixture()
    before = copy.deepcopy((fx['profile'], fx['request'], fx['sources'], fx['projected'], fx['components']))
    first = _build(fx)
    assert isinstance(first, ContextPackBuildResult)
    assert first.ok
    assert first.serialized_pack
    assert first.receipt['operation'] == 'build'
    assert first.receipt['result'] == 'built'
    fx['sources'] = list(reversed(fx['sources']))
    fx['components'] = list(reversed(fx['components']))
    second = _build(fx)
    assert second.ok
    assert second.serialized_pack == first.serialized_pack
    assert second.receipt == first.receipt
    assert before[0] == fx['profile']
    assert before[1] == fx['request']

def test_exact_source_bytes_are_base64_preserved_and_receipt_is_out_of_band():
    fx = _fixture()
    result = _build(fx)
    assert result.ok
    control = result.pack['control_plane']['items'][0]['payload']
    operational = result.pack['operational_evidence_plane']['items'][0]['payload']
    assert control['data'] == 'Y29udHJvbC1saW5lDQo='
    assert control['raw_sha256'] == _sha(fx['control_raw'])
    assert operational['data'] == 'AGV2aWRlbmNl/w=='
    assert operational['raw_sha256'] == _sha(fx['operational_raw'])
    assert b'\r\n' not in result.serialized_pack
    assert 'receipt' not in result.pack
    assert result.receipt['serialized_pack_sha256'] == _sha(result.serialized_pack)

def test_source_registry_is_canonical_and_standing_evidence_is_set_normalized():
    result = _build(_fixture())
    assert result.ok
    classes = [item['source_class'] for item in result.pack['source_registry']]
    assert classes == ['repository_control', 'canonical_state', 'operational_evidence']
    canonical = next((item for item in result.pack['source_registry'] if item['source_class'] == 'canonical_state'))
    assert canonical['standing_evidence'] == [{'contract': 'standing/1', 'immutable_snapshot_id': 'standing:1', 'raw_sha256': 'sha256:' + 'b' * 64}]

def test_slot_duplicates_coalesce_payload_and_preserve_all_causes():
    fx = _fixture()
    duplicate = copy.deepcopy(fx['request']['slot_bindings'][0])
    duplicate['slot_id'] = 'repo-control-alias'
    fx['request']['slot_bindings'].append(duplicate)
    fx['request_raw'] = json.dumps(fx['request'], ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8')
    result = _build(fx)
    assert result.ok
    assert len(result.pack['control_plane']['items']) == 1
    entry = next((x for x in result.pack['inclusion_ledger'] if x['plane'] == 'control'))
    assert entry['causes'] == [{'kind': 'profile_slot', 'cause_id': 'repo-control'}, {'kind': 'profile_slot', 'cause_id': 'repo-control-alias'}]

def test_knowledge_ledger_has_snapshot_and_semantic_causes():
    fx = _fixture(semantic_item=True)
    result = _build(fx)
    assert result.ok
    knowledge = [entry for entry in result.pack['inclusion_ledger'] if entry['plane'] == 'knowledge']
    assert len(knowledge) == 2
    root = next((entry for entry in knowledge if 'semantic_id' not in entry['subject']))
    semantic = next((entry for entry in knowledge if 'semantic_id' in entry['subject']))
    assert root['causes'] == [{'kind': 'request_selector', 'cause_id': 'canonical:snapshot:1'}]
    assert semantic['subject']['semantic_id'] == 'record:one'
    assert semantic['causes'] == [{'kind': 'request_selector', 'cause_id': 'p3:["request_selector","record","record:one"]'}, {'kind': 'pems_closure', 'cause_id': 'p3:["pems_closure","rule","record","record:one"]'}]

def test_missing_semantic_provenance_fails_closed():
    fx = _fixture(semantic_item=True)
    fx['projected'] = [ProjectedKnowledge(canonical_snapshot_ref=fx['projected'][0].canonical_snapshot_ref, pems=fx['projected'][0].pems, causes=())]
    result = _build(fx)
    assert not result.ok
    assert result.failure['code'] == 'PEMS_SEMANTIC_INVALID'
    assert result.failure['stage'] == 'projection'

def test_plane_classification_conflict_fails_closed():
    fx = _fixture()
    repo = fx['request']['source_bindings'][0]
    operational = fx['request']['source_bindings'][2]
    operational['logical_namespace'] = repo['logical_namespace']
    operational['logical_source_id'] = repo['logical_source_id']
    fx['sources'][2] = ResolvedSource(operational, fx['operational_raw'])
    fx['request']['slot_bindings'][1]['source_ref'] = _ref(operational)
    fx['request_raw'] = json.dumps(fx['request'], ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8')
    result = _build(fx)
    assert not result.ok
    assert result.failure['code'] == 'PLANE_CLASSIFICATION_CONFLICT'

def test_operational_validation_status_is_carried_without_authority_promotion():
    result = _build(_fixture(accepted_operational=True))
    assert result.ok
    item = result.pack['operational_evidence_plane']['items'][0]
    assert item['validation_status'] == 'accepted_validation_result'
    assert item['validation_result']['validator_contract'] == 'validator/1'
    serialized = result.serialized_pack.decode('utf-8')
    assert '"trusted"' not in serialized
    assert '"authorized"' not in serialized
    assert '"activated"' not in serialized

def test_cove_output_uses_p4_adapter_and_requires_cove_toolchain_identity():
    fx = _fixture(cove=True)
    result = _build(fx)
    assert result.ok
    item = result.pack['knowledge_plane']['items'][0]
    assert item['cove_payload']['cove_semantic'] == 'cove/1'
    assert item['cove_payload']['pems_semantic'] == 'pems/2'
    assert 'cove_payload_sha256' in result.pack['identity']
    fx['components'] = [component for component in fx['components'] if component['role'] != 'cove_adapter']
    failure = _build(fx)
    assert not failure.ok
    assert failure.failure['code'] == 'TOOLCHAIN_IDENTITY_MISMATCH'

def test_toolchain_change_changes_manifest_and_pack_identity():
    fx = _fixture()
    first = _build(fx)
    assert first.ok
    mutated = copy.deepcopy(fx)
    for component in mutated['components']:
        if component['role'] == 'pems_validator':
            component['immutable_identity'] = 'git-blob:' + '0' * 40
            component['raw_sha256'] = 'sha256:' + '0' * 64
    second = _build(mutated)
    assert second.ok
    assert first.pack['identity']['payload_set_sha256'] == second.pack['identity']['payload_set_sha256']
    assert first.pack['identity']['manifest_sha256'] != second.pack['identity']['manifest_sha256']
    assert first.pack['identity']['pack_identity_sha256'] != second.pack['identity']['pack_identity_sha256']

def test_raw_profile_or_request_mismatch_fails_before_pack_identity():
    fx = _fixture()
    fx['profile_raw'] = fx['profile_raw'].replace(b'"p5-test"', b'"p5-else"', 1)
    profile_failure = _build(fx)
    assert not profile_failure.ok
    assert profile_failure.failure['code'] == 'INVALID_PROFILE'
    fx = _fixture()
    fx['request_raw'] = fx['request_raw'].replace(b'"request:p5"', b'"request:else"', 1)
    request_failure = _build(fx)
    assert not request_failure.ok
    assert request_failure.failure['code'] == 'INVALID_REQUEST'

def test_pack_byte_limit_rejects_instead_of_truncating():
    fx = _fixture()
    fx['profile']['limits']['canonical_pack']['max_bytes'] = 100
    fx['profile_raw'] = json.dumps(fx['profile'], ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8')
    fx['request']['profile']['raw_sha256'] = _sha(fx['profile_raw'])
    fx['request_raw'] = json.dumps(fx['request'], ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8')
    result = _build(fx)
    assert not result.ok
    assert result.failure['code'] == 'PACK_LIMIT_EXCEEDED'
    assert result.pack is None
    assert result.serialized_pack is None

def test_p1b_context_pack_schema_accepts_p5_output():
    fx = _fixture()
    result = _build(fx)
    assert result.ok
    pack_schema = json.loads((ROOT / 'schemas/context-pack.schema.json').read_text(encoding='utf-8'))
    source_schema = json.loads((ROOT / 'schemas/context-source-binding.schema.json').read_text(encoding='utf-8'))
    pems_schema = json.loads((ROOT / 'backends/pems-cove/pems-v2.schema.json').read_text(encoding='utf-8'))
    registry = Registry().with_resources([(source_schema['$id'], Resource.from_contents(source_schema)), (pems_schema['$id'], Resource.from_contents(pems_schema))])
    errors = list(Draft202012Validator(pack_schema, registry=registry).iter_errors(result.pack))
    assert not errors, [error.message for error in errors]

def test_builder_source_contains_no_persistence_or_filesystem_write_api():
    source = (ROOT / 'context_packaging/pack_builder.py').read_text(encoding='utf-8')
    forbidden = ('.write_text(', '.write_bytes(', 'open(', 'os.replace(', 'os.rename(', 'shutil.', 'subprocess.')
    for token in forbidden:
        assert token not in source
