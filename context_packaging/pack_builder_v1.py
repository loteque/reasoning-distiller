"""P5 pure deterministic context-pack builder.

Consumes only exact P1 protocol values plus P2/P3/P4 outputs.  The builder
constructs canonical separated planes, a source registry, selection provenance,
toolchain identity, non-circular digests, canonical bytes, and an out-of-band
build receipt.  It performs no persistence, rendering, source discovery,
admission, reconciliation, authorization, activation, or canonical mutation.
"""
from __future__ import annotations
import base64
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from typing import Any, Mapping, Sequence
from .cove_adapter import CoveAdapterError, encode_cove_pems
from .pems_projection import ProjectedKnowledge, _jcs, _strict_json
from .source_resolver import ResolvedSource, _snapshot_key
PACK_CONTRACT = 'reasoning-distiller-context-pack/1'
PACK_BUILDER_CONTRACT = 'reasoning-distiller-context-pack-builder/1'
RECEIPT_CONTRACT = 'reasoning-distiller-context-pack-receipt/1'
FAILURE_CONTRACT = 'reasoning-distiller-context-pack-failure/1'
DIGEST_MAGIC = b'reasoning-distiller-context-digest/1\x00'
_SOURCE_CLASS_RANK = {'repository_control': 0, 'package_control': 1, 'canonical_state': 2, 'operational_evidence': 3}
_PLANE_RANK = {'control': 0, 'knowledge': 1, 'operational_evidence': 2}
_CAUSE_RANK = {'profile_slot': 0, 'request_selector': 1, 'pems_closure': 2}
_TOOLCHAIN_RANK = {'pems_schema': 0, 'pems_validator': 1, 'closure_descriptor': 2, 'cove_adapter': 3, 'jcs_serializer': 4, 'pack_builder': 5}
_CONTROL_CLASSES = {'repository_control', 'package_control'}

@dataclass(frozen=True)
class ContextPackBuildResult:
    pack: Mapping[str, Any] | None = None
    serialized_pack: bytes | None = None
    receipt: Mapping[str, Any] | None = None
    failure: Mapping[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.failure is None

class _BuildFailure(ValueError):

    def __init__(self, code: str, diagnostic: str, source_ref: Mapping[str, Any] | None=None, stage: str='pack'):
        super().__init__(diagnostic)
        self.code = code
        self.diagnostic = diagnostic
        self.source_ref = deepcopy(source_ref) if source_ref is not None else None
        self.stage = stage

def build_context_pack(profile_raw: bytes, profile: Mapping[str, Any], request_raw: bytes, request: Mapping[str, Any], resolved_sources: Sequence[ResolvedSource], projected_knowledge: Sequence[ProjectedKnowledge], toolchain_components: Sequence[Mapping[str, Any]]) -> ContextPackBuildResult:
    """Build one canonical pack without persistence or mutable-state access."""
    try:
        _preflight(profile_raw, profile, request_raw, request)
        source_index = _index_resolved_sources(resolved_sources)
        control_items, control_ledger, control_bindings = _build_control_plane(request, source_index)
        operational_items, operational_ledger, operational_bindings = _build_operational_plane(request, source_index)
        knowledge_items, knowledge_ledger, knowledge_bindings = _build_knowledge_plane(profile, request, source_index, projected_knowledge)
        _enforce_plane_separation(control_items, knowledge_items, operational_items)
        limits = profile['limits']['canonical_pack']
        if len(control_items) > limits['max_control_items']:
            raise _BuildFailure('PACK_LIMIT_EXCEEDED', 'canonical_pack.max_control_items exceeded')
        if len(operational_items) > limits['max_operational_evidence_items']:
            raise _BuildFailure('PACK_LIMIT_EXCEEDED', 'canonical_pack.max_operational_evidence_items exceeded')
        source_registry = _canonical_source_registry([*control_bindings, *knowledge_bindings, *operational_bindings])
        inclusion_ledger = [*control_ledger, *knowledge_ledger, *operational_ledger]
        components = _validate_and_canonicalize_toolchain(profile, knowledge_items, toolchain_components)
        profile_raw_sha = _raw_sha256(profile_raw)
        request_raw_sha = _raw_sha256(request_raw)
        pack: dict[str, Any] = {'contract': PACK_CONTRACT, 'profile': {'profile_id': profile['profile_id'], 'profile_version': profile['profile_version'], 'raw_sha256': profile_raw_sha}, 'request': {'request_id': request['request_id'], 'raw_sha256': request_raw_sha}, 'source_registry': source_registry, 'control_plane': {'items': control_items}, 'knowledge_plane': {'items': knowledge_items}, 'operational_evidence_plane': {'items': operational_items}, 'inclusion_ledger': inclusion_ledger, 'toolchain': {'components': components}}
        eligibility = _pack_eligibility(request)
        if eligibility is not None:
            pack['eligibility'] = eligibility
        pack = _canonicalize_pack(pack)
        identity = _build_identity(profile, request, pack)
        pack['identity'] = identity
        serialized = _jcs(pack)
        if len(serialized) > limits['max_bytes']:
            raise _BuildFailure('PACK_LIMIT_EXCEEDED', f"canonical_pack.max_bytes exceeded: actual={len(serialized)} limit={limits['max_bytes']}")
        replay = _canonicalize_pack(pack)
        replay['identity'] = _build_identity(profile, request, replay)
        replay_bytes = _jcs(replay)
        if replay_bytes != serialized:
            raise _BuildFailure('NONDETERMINISTIC_OUTPUT', 'canonical pack serialization was not a deterministic fixed point')
        receipt = {'contract': RECEIPT_CONTRACT, 'request_id': request['request_id'], 'operation': 'build', 'result': 'built', 'pack_identity_sha256': identity['pack_identity_sha256'], 'serialized_pack_sha256': _raw_sha256(serialized)}
        return ContextPackBuildResult(pack=pack, serialized_pack=serialized, receipt=receipt)
    except _BuildFailure as exc:
        return ContextPackBuildResult(failure=_failure(exc.code, exc.stage, exc.diagnostic, exc.source_ref))
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        return ContextPackBuildResult(failure=_failure('INVALID_REQUEST', 'pack', f'invalid P5 build input: {type(exc).__name__}'))

def _preflight(profile_raw, profile, request_raw, request) -> None:
    if not isinstance(profile_raw, bytes) or not isinstance(request_raw, bytes):
        raise _BuildFailure('INVALID_REQUEST', 'profile/request raw inputs must be bytes')
    if not isinstance(profile, Mapping) or not isinstance(request, Mapping):
        raise _BuildFailure('INVALID_REQUEST', 'profile/request must be mappings')
    try:
        parsed_profile = _strict_json(profile_raw)
        parsed_request = _strict_json(request_raw)
    except Exception as exc:
        raise _BuildFailure('INVALID_REQUEST', 'profile/request raw bytes must be strict UTF-8 JSON') from exc
    if parsed_profile != dict(profile):
        raise _BuildFailure('INVALID_PROFILE', 'profile raw bytes do not bind profile object')
    if parsed_request != dict(request):
        raise _BuildFailure('INVALID_REQUEST', 'request raw bytes do not bind request object')
    if profile.get('contract') != 'reasoning-distiller-context-profile/1':
        raise _BuildFailure('INVALID_PROFILE', 'unsupported profile contract')
    if request.get('contract') != 'reasoning-distiller-context-pack-request/1':
        raise _BuildFailure('INVALID_REQUEST', 'unsupported request contract')
    if profile.get('contracts', {}).get('pack') != PACK_CONTRACT:
        raise _BuildFailure('UNSUPPORTED_PROFILE', 'profile does not bind context-pack/1')
    if request.get('output', {}).get('pack_contract') != PACK_CONTRACT:
        raise _BuildFailure('INVALID_REQUEST', 'request does not bind context-pack/1')
    profile_raw_sha = _raw_sha256(profile_raw)
    requested_profile = request.get('profile')
    if not isinstance(requested_profile, Mapping):
        raise _BuildFailure('INVALID_REQUEST', 'request profile identity missing')
    if requested_profile.get('profile_id') != profile.get('profile_id') or requested_profile.get('profile_version') != profile.get('profile_version') or _normalize_sha256(requested_profile.get('raw_sha256')) != profile_raw_sha:
        raise _BuildFailure('INVALID_REQUEST', 'request profile identity mismatch')
    p_out = profile.get('output')
    r_out = request.get('output')
    if not isinstance(p_out, Mapping) or not isinstance(r_out, Mapping):
        raise _BuildFailure('INVALID_REQUEST', 'output contract missing')
    if p_out.get('serializer') != 'jcs/1' or r_out.get('serializer') != 'jcs/1' or p_out.get('knowledge_encoding') != r_out.get('knowledge_encoding') or (p_out.get('knowledge_encoding') not in {'pems/2', 'cove/1'}):
        raise _BuildFailure('UNSUPPORTED_ENCODING_TUPLE', 'profile/request output tuple mismatch', stage='encoding')
    eligibility = request.get('eligibility')
    if eligibility is not None:
        if not isinstance(eligibility, Mapping):
            raise _BuildFailure('PROFILE_INELIGIBLE', 'eligibility binding is invalid', stage='eligibility')
        if eligibility.get('decision') != 'eligible':
            raise _BuildFailure('PROFILE_INELIGIBLE', 'profile eligibility is not eligible', stage='eligibility')
        bound_profile = eligibility.get('profile')
        if not isinstance(bound_profile, Mapping) or (bound_profile.get('profile_id') != requested_profile.get('profile_id') or bound_profile.get('profile_version') != requested_profile.get('profile_version') or _normalize_sha256(bound_profile.get('raw_sha256')) != profile_raw_sha):
            raise _BuildFailure('PROFILE_INELIGIBLE', 'eligibility binding does not identify the exact profile', stage='eligibility')

def _index_resolved_sources(resolved_sources):
    index: dict[tuple[Any, ...], ResolvedSource] = {}
    for source in resolved_sources:
        if not hasattr(source, 'binding') or not hasattr(source, 'content'):
            raise _BuildFailure('SOURCE_IDENTITY_INVALID', 'invalid resolved source')
        if not isinstance(source.binding, Mapping) or not isinstance(source.content, bytes):
            raise _BuildFailure('SOURCE_IDENTITY_INVALID', 'invalid resolved source')
        try:
            key = _snapshot_key(source.binding)
        except Exception as exc:
            raise _BuildFailure('SOURCE_IDENTITY_INVALID', 'resolved source identity is invalid') from exc
        existing = index.get(key)
        if existing is not None:
            if dict(existing.binding) != dict(source.binding) or existing.content != source.content:
                raise _BuildFailure('LOGICAL_SOURCE_CONFLICT', 'multiple non-equivalent resolved sources share one snapshot identity', _snapshot_ref(source.binding))
            continue
        _verify_resolved_digest(source)
        index[key] = source
    return index

def _verify_resolved_digest(source) -> None:
    binding = source.binding
    source_class = binding.get('source_class')
    field = 'pems_sha256' if source_class == 'canonical_state' else 'raw_sha256'
    expected = _normalize_sha256(binding.get(field))
    actual = _raw_sha256(source.content)
    if expected != actual:
        raise _BuildFailure('SOURCE_DIGEST_MISMATCH', f'{field} does not match exact resolved bytes', _snapshot_ref(binding))

def _find_resolved(ref, source_index):
    try:
        source = source_index.get(_snapshot_key(ref))
    except Exception as exc:
        raise _BuildFailure('SOURCE_IDENTITY_INVALID', 'invalid snapshot reference', ref) from exc
    if source is None:
        raise _BuildFailure('IMMUTABLE_SNAPSHOT_UNAVAILABLE', 'P5 input does not contain the referenced P2 source', ref)
    return source

def _build_control_plane(request, source_index):
    items: dict[bytes, dict[str, Any]] = {}
    causes: dict[bytes, list[dict[str, str]]] = {}
    bindings: list[Mapping[str, Any]] = []
    for slot in request.get('slot_bindings', []):
        if slot.get('plane') != 'control':
            continue
        ref = _normalize_snapshot_ref(slot['source_ref'])
        source = _find_resolved(ref, source_index)
        if source.binding.get('source_class') not in _CONTROL_CLASSES:
            raise _BuildFailure('PLANE_CLASSIFICATION_CONFLICT', 'non-control source classified into control plane', ref)
        key = _jcs(ref)
        item = {'source_ref': ref, 'payload': {'encoding': 'base64', 'data': _b64(source.content), 'raw_sha256': _raw_sha256(source.content)}}
        if key in items and items[key] != item:
            raise _BuildFailure('PLANE_CLASSIFICATION_CONFLICT', 'control source reference resolved to non-identical payloads', ref)
        if key not in items:
            items[key] = item
            bindings.append(_canonical_binding(source.binding))
        causes.setdefault(key, []).append({'kind': 'profile_slot', 'cause_id': str(slot['slot_id'])})
    plane_items = list(items.values())
    ledger = [{'plane': 'control', 'subject': {'source_ref': deepcopy(items[key]['source_ref'])}, 'causes': deepcopy(causes[key])} for key in items]
    return (plane_items, ledger, bindings)

def _build_operational_plane(request, source_index):
    items: dict[bytes, dict[str, Any]] = {}
    causes: dict[bytes, list[dict[str, str]]] = {}
    bindings: list[Mapping[str, Any]] = []
    for slot in request.get('slot_bindings', []):
        if slot.get('plane') != 'operational_evidence':
            continue
        ref = _normalize_snapshot_ref(slot['source_ref'])
        source = _find_resolved(ref, source_index)
        if source.binding.get('source_class') != 'operational_evidence':
            raise _BuildFailure('PLANE_CLASSIFICATION_CONFLICT', 'non-operational source classified into operational-evidence plane', ref)
        binding = _canonical_binding(source.binding)
        status = binding.get('validation_status')
        item = {'source_ref': ref, 'validation_status': status, 'payload': {'encoding': 'base64', 'data': _b64(source.content), 'raw_sha256': _raw_sha256(source.content)}}
        if status == 'accepted_validation_result':
            if 'validation_result' not in binding:
                raise _BuildFailure('OPERATIONAL_EVIDENCE_IDENTITY_INVALID', 'accepted validation status lacks validation result identity', ref)
            item['validation_result'] = deepcopy(binding['validation_result'])
        elif 'validation_result' in binding:
            raise _BuildFailure('OPERATIONAL_EVIDENCE_IDENTITY_INVALID', 'validation result identity is invalid for carried status', ref)
        key = _jcs(ref)
        if key in items and items[key] != item:
            raise _BuildFailure('PLANE_CLASSIFICATION_CONFLICT', 'operational source reference resolved to non-identical payloads', ref)
        if key not in items:
            items[key] = item
            bindings.append(binding)
        causes.setdefault(key, []).append({'kind': 'profile_slot', 'cause_id': str(slot['slot_id'])})
    plane_items = list(items.values())
    ledger = [{'plane': 'operational_evidence', 'subject': {'source_ref': deepcopy(items[key]['source_ref'])}, 'causes': deepcopy(causes[key])} for key in items]
    return (plane_items, ledger, bindings)

def _build_knowledge_plane(profile, request, source_index, projected_knowledge):
    selections = request.get('knowledge_selection', {}).get('snapshots', [])
    selection_refs = {_jcs(_normalize_snapshot_ref(item['canonical_snapshot_ref'])): item for item in selections}
    seen: set[bytes] = set()
    items: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    bindings: list[Mapping[str, Any]] = []
    encoding = request['output']['knowledge_encoding']
    for projected in projected_knowledge:
        if not hasattr(projected, 'canonical_snapshot_ref') or not hasattr(projected, 'pems'):
            raise _BuildFailure('PEMS_SEMANTIC_INVALID', 'invalid P3 projection input', stage='projection')
        ref = _normalize_snapshot_ref(projected.canonical_snapshot_ref)
        key = _jcs(ref)
        if key not in selection_refs or key in seen:
            raise _BuildFailure('INVALID_REQUEST', 'P3 projection does not correspond one-to-one with requested snapshot selection', ref)
        seen.add(key)
        source = _find_resolved(ref, source_index)
        if source.binding.get('source_class') != 'canonical_state':
            raise _BuildFailure('PLANE_CLASSIFICATION_CONFLICT', 'non-canonical source classified into knowledge plane', ref)
        binding = _canonical_binding(source.binding)
        pems = deepcopy(projected.pems)
        if not isinstance(pems, Mapping) or pems.get('semantic') != 'pems/2':
            raise _BuildFailure('PEMS_SEMANTIC_INVALID', 'P3 projection is not PEMS/2', ref, 'projection')
        item: dict[str, Any] = {'canonical_snapshot_ref': ref, 'semantic': 'pems/2', 'serializer': 'jcs/1', 'pems': pems}
        if encoding == 'cove/1':
            try:
                raw_cove = encode_cove_pems(pems)
            except CoveAdapterError as exc:
                raise _BuildFailure('COVE_ROUNDTRIP_MISMATCH', 'P4 COVE adapter rejected selected PEMS projection', ref, 'encoding') from exc
            item['cove_payload'] = {'cove_semantic': 'cove/1', 'pems_semantic': 'pems/2', 'serializer': 'jcs/1', 'encoding': 'base64', 'data': _b64(raw_cove), 'raw_sha256': _raw_sha256(raw_cove)}
        items.append(item)
        bindings.append(binding)
        ledger.append({'plane': 'knowledge', 'subject': {'source_ref': deepcopy(ref)}, 'causes': [{'kind': 'request_selector', 'cause_id': str(ref['immutable_snapshot_id'])}]})
        semantic_ids = {'record': {str(record.get('id')) for record in pems.get('records', []) if isinstance(record, Mapping) and record.get('id') is not None}, 'relation': {str(relation.get('id')) for relation in pems.get('relations', []) if isinstance(relation, Mapping) and relation.get('id') is not None}}
        if semantic_ids['record'] & semantic_ids['relation']:
            raise _BuildFailure('PEMS_SEMANTIC_INVALID', 'selection provenance cannot identify colliding record/relation ids', ref, 'projection')
        covered: set[tuple[str, str]] = set()
        by_semantic: dict[str, list[dict[str, str]]] = {}
        for cause in getattr(projected, 'causes', ()):
            namespace = str(cause.namespace)
            semantic_id = str(cause.semantic_id)
            kind = str(cause.kind)
            if namespace not in semantic_ids or semantic_id not in semantic_ids[namespace]:
                raise _BuildFailure('PEMS_SEMANTIC_INVALID', 'P3 provenance names a semantic item absent from the projection', ref, 'projection')
            if kind not in {'request_selector', 'pems_closure'}:
                raise _BuildFailure('UNKNOWN_SEMANTICS_FIELD', 'unsupported P3 selection-provenance cause kind', ref, 'projection')
            covered.add((namespace, semantic_id))
            by_semantic.setdefault(semantic_id, []).append({'kind': kind, 'cause_id': str(cause.cause_id)})
        expected = {(namespace, semantic_id) for namespace, values in semantic_ids.items() for semantic_id in values}
        if covered != expected:
            raise _BuildFailure('PEMS_SEMANTIC_INVALID', 'P3 projection lacks deterministic provenance for one or more semantic items', ref, 'projection')
        for semantic_id, semantic_causes in by_semantic.items():
            ledger.append({'plane': 'knowledge', 'subject': {'source_ref': deepcopy(ref), 'semantic_id': semantic_id}, 'causes': semantic_causes})
    if seen != set(selection_refs):
        raise _BuildFailure('INVALID_REQUEST', 'not every requested canonical snapshot has one P3 projection')
    return (items, ledger, bindings)

def _enforce_plane_separation(control, knowledge, operational) -> None:
    seen: dict[tuple[str, str], str] = {}
    groups = (('control', (item['source_ref'] for item in control)), ('knowledge', (item['canonical_snapshot_ref'] for item in knowledge)), ('operational_evidence', (item['source_ref'] for item in operational)))
    for plane, refs in groups:
        for ref in refs:
            logical = (str(ref['logical_namespace']), str(ref['logical_source_id']))
            previous = seen.get(logical)
            if previous is not None and previous != plane:
                raise _BuildFailure('PLANE_CLASSIFICATION_CONFLICT', f'logical source is classified into both {previous} and {plane}', ref)
            seen[logical] = plane

def _canonical_source_registry(bindings):
    unique: dict[bytes, dict[str, Any]] = {}
    for binding in bindings:
        canonical = _canonical_binding(binding)
        key = _jcs(canonical)
        unique[key] = canonical
    return sorted(unique.values(), key=lambda b: (_SOURCE_CLASS_RANK[b['source_class']], _jcs(b)))

def _validate_and_canonicalize_toolchain(profile, knowledge_items, components):
    normalized = [deepcopy(dict(c)) for c in components]
    roles = [component.get('role') for component in normalized]
    if len(roles) != len(set(roles)):
        raise _BuildFailure('TOOLCHAIN_IDENTITY_MISMATCH', 'duplicate toolchain role', stage='toolchain')
    required = {'pems_schema', 'pems_validator', 'closure_descriptor', 'jcs_serializer', 'pack_builder'}
    if any(('cove_payload' in item for item in knowledge_items)):
        required.add('cove_adapter')
    if set(roles) != required:
        raise _BuildFailure('TOOLCHAIN_IDENTITY_MISMATCH', 'toolchain roles do not exactly match behavior used by this build', stage='toolchain')
    for component in normalized:
        if component.get('role') not in _TOOLCHAIN_RANK:
            raise _BuildFailure('TOOLCHAIN_IDENTITY_MISMATCH', 'unknown toolchain role', stage='toolchain')
        if not all((isinstance(component.get(field), str) and component.get(field) for field in ('contract', 'immutable_identity', 'raw_sha256'))):
            raise _BuildFailure('TOOLCHAIN_IDENTITY_MISMATCH', 'incomplete toolchain component', stage='toolchain')
        _normalize_sha256(component['raw_sha256'])
    by_role = {component['role']: component for component in normalized}
    closure = profile['knowledge']['closure_descriptor']
    actual = by_role['closure_descriptor']
    if actual['contract'] != closure['contract'] or actual['immutable_identity'] != closure['immutable_snapshot_id'] or actual['raw_sha256'] != closure['raw_sha256'] or (by_role['jcs_serializer']['contract'] != 'jcs/1') or (by_role['pack_builder']['contract'] != PACK_BUILDER_CONTRACT):
        raise _BuildFailure('TOOLCHAIN_IDENTITY_MISMATCH', 'toolchain does not match profile closure/JCS identity', stage='toolchain')
    return sorted(normalized, key=lambda c: (_TOOLCHAIN_RANK[c['role']], _jcs(c)))

def _pack_eligibility(request):
    value = request.get('eligibility')
    if value is None:
        return None
    consumer = value['consumer']
    evidence = value['policy_evidence']
    return {'consumer_contract': consumer['consumer_contract'], 'consumer_id': consumer['consumer_id'], 'policy_evidence_snapshot_id': evidence['immutable_snapshot_id'], 'decision': value['decision']}

def _canonicalize_pack(pack):
    out = deepcopy(pack)
    out['source_registry'] = _canonical_source_registry(out['source_registry'])
    out['control_plane']['items'].sort(key=lambda x: _jcs(x['source_ref']))
    out['knowledge_plane']['items'].sort(key=lambda x: _jcs(x['canonical_snapshot_ref']))
    out['operational_evidence_plane']['items'].sort(key=lambda x: _jcs(x['source_ref']))
    for entry in out['inclusion_ledger']:
        entry['subject']['source_ref'] = _normalize_snapshot_ref(entry['subject']['source_ref'])
        entry['causes'].sort(key=lambda c: (_CAUSE_RANK[c['kind']], c['cause_id'].encode('utf-8')))
    out['inclusion_ledger'].sort(key=lambda e: (_PLANE_RANK[e['plane']], _jcs(e['subject'])))
    out['toolchain']['components'].sort(key=lambda c: (_TOOLCHAIN_RANK[c['role']], _jcs(c)))
    return out

def _build_identity(profile, request, pack):
    identity: dict[str, Any] = {'profile_sha256': _domain_sha256('context-profile', profile), 'request_sha256': _domain_sha256('context-pack-request', request), 'canonical_state_binding_sha256s': _canonical_binding_digests(pack), 'selected_pems_sha256': _domain_sha256('selected-pems-projection', _selected_pems_view(pack))}
    cove = _cove_view(pack)
    if cove['items']:
        identity['cove_payload_sha256'] = _domain_sha256('cove-payload-set', cove)
    identity['manifest_sha256'] = _domain_sha256('context-pack-manifest', _manifest_view(pack))
    identity['payload_set_sha256'] = _domain_sha256('context-pack-payload-set', _payload_view(pack))
    preimage = {'contract': 'reasoning-distiller-context-pack-identity-preimage/1', **identity}
    identity['pack_identity_sha256'] = _domain_sha256('context-pack-identity', preimage)
    return identity

def _canonical_binding_digests(pack):
    by_ref: dict[bytes, str] = {}
    for binding in pack['source_registry']:
        if binding['source_class'] != 'canonical_state':
            continue
        ref = _snapshot_ref(binding)
        by_ref[_jcs(ref)] = _domain_sha256('canonical-state-binding', _canonical_binding(binding))
    result = []
    for item in pack['knowledge_plane']['items']:
        key = _jcs(_normalize_snapshot_ref(item['canonical_snapshot_ref']))
        if key not in by_ref:
            raise _BuildFailure('CANONICAL_BINDING_UNPROVEN', 'knowledge item has no exact canonical-state binding', item['canonical_snapshot_ref'])
        result.append(by_ref[key])
    return result

def _selected_pems_view(pack):
    return {'contract': 'reasoning-distiller-selected-pems-projection/1', 'items': [{'canonical_snapshot_ref': item['canonical_snapshot_ref'], 'semantic': item['semantic'], 'serializer': item['serializer'], 'pems': item['pems']} for item in pack['knowledge_plane']['items']]}

def _cove_view(pack):
    return {'contract': 'reasoning-distiller-cove-payload-set/1', 'items': [{'canonical_snapshot_ref': item['canonical_snapshot_ref'], 'cove_payload': item['cove_payload']} for item in pack['knowledge_plane']['items'] if 'cove_payload' in item]}

def _manifest_view(pack):
    out = deepcopy(pack)
    out.pop('identity', None)
    for item in out['control_plane']['items']:
        item['payload'].pop('data', None)
    for item in out['knowledge_plane']['items']:
        item.pop('pems', None)
        if 'cove_payload' in item:
            item['cove_payload'].pop('data', None)
    for item in out['operational_evidence_plane']['items']:
        item['payload'].pop('data', None)
    return out

def _payload_view(pack):
    return {'contract': 'reasoning-distiller-context-pack-payload-set/1', 'control': [{'source_ref': item['source_ref'], 'payload': item['payload']} for item in pack['control_plane']['items']], 'knowledge': [{'canonical_snapshot_ref': item['canonical_snapshot_ref'], 'pems': item['pems'], **({'cove_payload': item['cove_payload']} if 'cove_payload' in item else {})} for item in pack['knowledge_plane']['items']], 'operational_evidence': [{'source_ref': item['source_ref'], 'payload': item['payload']} for item in pack['operational_evidence_plane']['items']]}

def _canonical_binding(binding):
    out = deepcopy(dict(binding))
    if out.get('source_class') == 'canonical_state':
        evidence = out.get('standing_evidence')
        if not isinstance(evidence, list) or not evidence:
            raise _BuildFailure('CANONICAL_BINDING_UNPROVEN', 'canonical-state standing evidence is missing', _snapshot_ref(out))
        out['standing_evidence'] = _canonical_standing_evidence(evidence)
    return out

def _normalize_snapshot_ref(ref):
    out = deepcopy(dict(ref))
    if out.get('source_class') == 'canonical_state' and 'standing_evidence' in out:
        out['standing_evidence'] = _canonical_standing_evidence(out['standing_evidence'])
    return out

def _canonical_standing_evidence(evidence):
    unique = {}
    for item in evidence:
        normalized = deepcopy(dict(item))
        normalized['raw_sha256'] = _normalize_sha256(normalized['raw_sha256'])
        unique[_jcs(normalized)] = normalized
    return [unique[key] for key in sorted(unique)]

def _snapshot_ref(binding):
    source_class = binding.get('source_class')
    keys = {'repository_control': ('source_class', 'logical_namespace', 'logical_source_id', 'repository', 'commit', 'path', 'raw_sha256'), 'package_control': ('source_class', 'logical_namespace', 'logical_source_id', 'project_id', 'package_contract', 'immutable_package_snapshot_id', 'artifact_locator', 'raw_sha256'), 'canonical_state': ('source_class', 'logical_namespace', 'logical_source_id', 'project_id', 'backend_type', 'backend_contract', 'backend_config_identity', 'immutable_snapshot_id', 'pems_semantic', 'serializer', 'pems_sha256', 'standing_evidence', 'cove'), 'operational_evidence': ('source_class', 'logical_namespace', 'logical_source_id', 'artifact_contract', 'immutable_snapshot_id', 'raw_sha256', 'validation_status', 'validation_result')}.get(source_class)
    if keys is None:
        raise _BuildFailure('UNSUPPORTED_SOURCE_CLASS', 'unsupported source class')
    return _normalize_snapshot_ref({key: binding[key] for key in keys if key in binding})

def _normalize_sha256(value):
    if not isinstance(value, str) or not value.startswith('sha256:'):
        raise ValueError('invalid sha256 identity')
    digest = value[7:]
    if len(digest) != 64 or any((ch not in '0123456789abcdefABCDEF' for ch in digest)):
        raise ValueError('invalid sha256 identity')
    return 'sha256:' + digest.lower()

def _raw_sha256(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()

def _domain_sha256(domain, value):
    body = value if isinstance(value, bytes) else _jcs(value)
    encoded = domain.encode('ascii')
    if len(encoded) > 65535:
        raise ValueError('digest domain too long')
    preimage = DIGEST_MAGIC + len(encoded).to_bytes(2, 'big') + encoded + len(body).to_bytes(8, 'big') + body
    return _raw_sha256(preimage)

def _b64(data):
    return base64.b64encode(data).decode('ascii')

def _failure(code, stage, diagnostic, source_ref=None):
    out: dict[str, Any] = {'contract': FAILURE_CONTRACT, 'code': code, 'stage': stage, 'diagnostics': [diagnostic]}
    if source_ref is not None:
        out['source_ref'] = {key: deepcopy(source_ref[key]) for key in ('source_class', 'logical_namespace', 'logical_source_id') if key in source_ref}
    return out
