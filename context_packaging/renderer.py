from __future__ import annotations
from base64 import b64decode as _b64decode_primitive, b64encode as _b64encode_primitive
from collections.abc import Mapping
from copy import deepcopy as _deepcopy_primitive
from hashlib import sha256 as _sha256_primitive
from io import BytesIO as _BytesIO_primitive
from json import loads as _json_loads_primitive
from math import isfinite as _isfinite_primitive
from typing import Any
RENDERER_CONTRACT = 'reasoning-distiller-context-renderer/1'
RENDERER_PROFILE_CONTRACT = 'reasoning-distiller-context-renderer-profile/1'
RENDERED_ACTIVATION_CONTRACT = 'reasoning-distiller-context-rendered-activation/1'
FRAMING_CONTRACT = 'reasoning-distiller-context-renderer-framing/1'
FAILURE_CONTRACT = 'reasoning-distiller-context-pack-failure/1'
PACK_CONTRACTS = ('reasoning-distiller-context-pack/1', 'reasoning-distiller-context-pack/2')
PLANE_ORDER = ('control', 'knowledge', 'operational_evidence')
_PLANE_KEYS = ('control_plane', 'knowledge_plane', 'operational_evidence_plane')
_PROFILE_KEYS = frozenset({'contract', 'profile_id', 'profile_version', 'supported_pack_contracts', 'pack_profile', 'renderer_component', 'framing', 'limits'})
_PACK_KEYS = frozenset({'contract', 'profile', 'request', 'source_registry', 'control_plane', 'knowledge_plane', 'operational_evidence_plane', 'inclusion_ledger', 'toolchain', 'identity', 'eligibility'})
_PACK_REQUIRED_KEYS = frozenset({'contract', 'profile', 'request', 'source_registry', 'control_plane', 'knowledge_plane', 'operational_evidence_plane', 'inclusion_ledger', 'toolchain', 'identity'})
_DIGEST_MAGIC = b'reasoning-distiller-context-renderer-digest/1\x00'
_MEMBER_REGISTRY = (('member:component', 15), ('member:constant:decode_result_slots', 84), ('member:constant:digest_magic', 39), ('member:constant:failure_contract', 32), ('member:constant:framing_contract', 31), ('member:constant:pack_contracts', 33), ('member:constant:pack_keys', 37), ('member:constant:pack_required_keys', 38), ('member:constant:plane_keys', 35), ('member:constant:plane_order', 34), ('member:constant:profile_keys', 36), ('member:constant:render_result_slots', 83), ('member:constant:rendered_activation_contract', 30), ('member:constant:renderer_contract', 28), ('member:constant:renderer_profile_contract', 29), ('member:decode', 73), ('member:decode_execute', 2), ('member:decode_frames', 9), ('member:decode_result_failure_get', 81), ('member:decode_result_init', 71), ('member:decode_result_ok_get', 82), ('member:decode_result_pack_get', 80), ('member:domain', 23), ('member:failure', 24), ('member:frame', 7), ('member:frame_raw', 10), ('member:frames', 6), ('member:get', 69), ('member:header', 8), ('member:jcs', 19), ('member:jcs_bootstrap', 74), ('member:jcs_float', 18), ('member:jcs_string', 17), ('member:need', 21), ('member:norm', 20), ('member:pack', 5), ('member:pack_summary', 11), ('member:plane_key', 12), ('member:profile', 4), ('member:profile_id', 13), ('member:registry', 0), ('member:render', 72), ('member:render_execute', 1), ('member:render_result_activation_get', 75), ('member:render_result_failure_get', 78), ('member:render_result_init', 70), ('member:render_result_ok_get', 79), ('member:render_result_serialized_activation_get', 76), ('member:render_result_serialized_activation_sha256_get', 77), ('member:request_id', 14), ('member:resolve_bundle', 3), ('member:sha', 22), ('member:strict_json', 16), ('member:type:RenderedActivationDecodeResult', 26), ('member:type:RenderedActivationResult', 25), ('member:type:_RF', 27))

class RenderedActivationResult:
    __slots__ = ('_activation', '_serialized_activation', '_serialized_activation_sha256', '_failure')

    def __init__(self, activation=None, serialized_activation=None, serialized_activation_sha256=None, failure=None):
        self._activation = activation
        self._serialized_activation = serialized_activation
        self._serialized_activation_sha256 = serialized_activation_sha256
        self._failure = failure

    @property
    def activation(self):
        return self._activation

    @property
    def serialized_activation(self):
        return self._serialized_activation

    @property
    def serialized_activation_sha256(self):
        return self._serialized_activation_sha256

    @property
    def failure(self):
        return self._failure

    @property
    def ok(self) -> bool:
        return self._failure is None

class RenderedActivationDecodeResult:
    __slots__ = ('_pack', '_failure')

    def __init__(self, pack=None, failure=None):
        self._pack = pack
        self._failure = failure

    @property
    def pack(self):
        return self._pack

    @property
    def failure(self):
        return self._failure

    @property
    def ok(self) -> bool:
        return self._failure is None

class _RF(ValueError):
    pass

def _get_bound(bundle: tuple[Any, ...], index: int) -> Any:
    return bundle[index]

def render_context_pack(pack: Mapping[str, Any], profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationResult:
    bundle = _resolve_bundle()
    return bundle[1](bundle, pack, profile_raw, profile)

def decode_rendered_activation(raw: bytes, profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationDecodeResult:
    bundle = _resolve_bundle()
    return bundle[2](bundle, raw, profile_raw, profile)

def _resolve_bundle() -> tuple[Any, ...]:
    return (_MEMBER_REGISTRY, _render_bound, _decode_bound, _resolve_bundle, _profile_bound, _pack_bound, _frames_bound, _frame_bound, _header_bound, _decode_frames_bound, _frame_raw_bound, _pack_summary_bound, _plane_key_bound, _profile_id_bound, _request_id_bound, _component_bound, _strict_json_bound, _jcs_string_bound, _jcs_float_bound, _jcs_bound, _norm_bound, _need_bound, _sha_bound, _domain_bound, _failure_bound, RenderedActivationResult, RenderedActivationDecodeResult, _RF, RENDERER_CONTRACT, RENDERER_PROFILE_CONTRACT, RENDERED_ACTIVATION_CONTRACT, FRAMING_CONTRACT, FAILURE_CONTRACT, PACK_CONTRACTS, PLANE_ORDER, _PLANE_KEYS, _PROFILE_KEYS, _PACK_KEYS, _PACK_REQUIRED_KEYS, _DIGEST_MAGIC, Mapping, Exception, KeyError, TypeError, UnicodeError, ValueError, bool, bytearray, bytes, dict, float, int, list, set, str, all, any, enumerate, isinstance, len, ord, sorted, _b64decode_primitive, _b64encode_primitive, _deepcopy_primitive, _sha256_primitive, _BytesIO_primitive, _json_loads_primitive, _isfinite_primitive, _get_bound, RenderedActivationResult.__init__, RenderedActivationDecodeResult.__init__, render_context_pack, decode_rendered_activation, _jcs, RenderedActivationResult.activation.fget, RenderedActivationResult.serialized_activation.fget, RenderedActivationResult.serialized_activation_sha256.fget, RenderedActivationResult.failure.fget, RenderedActivationResult.ok.fget, RenderedActivationDecodeResult.pack.fget, RenderedActivationDecodeResult.failure.fget, RenderedActivationDecodeResult.ok.fget, RenderedActivationResult.__slots__, RenderedActivationDecodeResult.__slots__)

def _render_bound(b: tuple[Any, ...], pack: Mapping[str, Any], profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationResult:
    try:
        p = b[4](b, profile_raw, profile)
        pack_raw = b[5](b, pack, p)
        out: dict[str, Any] = {'contract': b[30], 'renderer_profile': {'profile_id': p['profile_id'], 'profile_version': p['profile_version'], 'raw_sha256': b[22](b, profile_raw)}, 'renderer_component': b[15](b, p['renderer_component']), 'pack': b[11](b, pack, pack_raw), 'framing': b[64](b[49](p['framing'])), 'frames': b[6](b, pack)}
        out['identity'] = {'activation_identity_sha256': b[23](b, 'activation_identity', b[19](b, out))}
        raw = b[19](b, out)
        limit = p['limits']['max_activation_bytes']
        if b[59](raw) > limit:
            raise b[27]('RENDER_LIMIT_EXCEEDED', f'rendering.max_activation_bytes exceeded: actual={b[59](raw)} limit={limit}')
        return b[25](out, raw, b[22](b, raw))
    except b[27] as exc:
        return b[25](failure=b[24](b, exc.args[0], exc.args[1]))
    except (b[42], b[43], b[45], b[44]) as exc:
        return b[25](failure=b[24](b, 'UNSUPPORTED_RENDERER', f'invalid renderer input: {exc.__class__.__name__}'))

def _decode_bound(b: tuple[Any, ...], raw: bytes, profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationDecodeResult:
    try:
        p = b[4](b, profile_raw, profile)
        b[21](b, b[58](raw, b[48]), 'rendered activation must be bytes')
        try:
            activation = b[16](b, raw)
        except b[41] as exc:
            raise b[27]('UNSUPPORTED_RENDERER', 'rendered activation is not strict UTF-8 JSON') from exc
        b[21](b, b[58](activation, b[49]) and b[19](b, activation) == raw, 'rendered activation is not canonical JCS bytes')
        b[8](b, activation, profile_raw, p)
        pack = b[9](b, activation['frames'])
        pack_raw = b[5](b, pack, p)
        b[21](b, activation['pack'] == b[11](b, pack, pack_raw), 'rendered pack summary does not bind decoded pack')
        limit = p['limits']['max_activation_bytes']
        if b[59](raw) > limit:
            raise b[27]('RENDER_LIMIT_EXCEEDED', f'rendering.max_activation_bytes exceeded: actual={b[59](raw)} limit={limit}')
        return b[26](pack)
    except b[27] as exc:
        return b[26](failure=b[24](b, exc.args[0], exc.args[1]))
    except (b[42], b[43], b[45], b[44]) as exc:
        return b[26](failure=b[24](b, 'UNSUPPORTED_RENDERER', f'invalid rendered activation: {exc.__class__.__name__}'))

def _profile_bound(b: tuple[Any, ...], raw: bytes, value: Mapping[str, Any]) -> dict[str, Any]:
    b[21](b, b[58](raw, b[48]) and b[58](value, b[40]), 'renderer profile must be mapping plus exact raw bytes')
    try:
        parsed = b[16](b, raw)
    except b[41] as exc:
        raise b[27]('UNSUPPORTED_RENDERER', 'renderer profile raw bytes must be strict UTF-8 JSON') from exc
    b[21](b, parsed == b[49](value), 'renderer profile raw bytes do not bind profile object')
    b[21](b, b[53](value) == b[36] and value.get('contract') == b[29], 'unsupported renderer profile contract or fields')
    b[21](b, b[55]((b[58](value.get(k), b[54]) and value[k] for k in ('profile_id', 'profile_version'))), 'renderer profile identity is invalid')
    supported = value.get('supported_pack_contracts')
    b[21](b, b[58](supported, b[52]) and supported and (b[59](supported) == b[59](b[53](supported))) and b[55]((x in b[33] for x in supported)), 'supported pack contracts are invalid')
    b[21](b, supported == [x for x in b[33] if x in supported], 'supported pack contracts are not canonical order')
    b[13](b, value.get('pack_profile'))
    c = b[15](b, value.get('renderer_component'))
    b[21](b, c['role'] == 'renderer' and c['contract'] == b[28], 'renderer component does not bind renderer/1')
    f = value.get('framing')
    b[21](b, b[58](f, b[40]) and b[53](f) == {'contract', 'serializer', 'text_encoding', 'item_encoding', 'plane_order'}, 'renderer framing is invalid')
    b[21](b, f.get('contract') == b[31] and f.get('serializer') == 'jcs/1' and (f.get('text_encoding') == 'utf-8') and (f.get('item_encoding') == 'base64') and (f.get('plane_order') == b[52](b[34])), 'unsupported renderer framing')
    limits = value.get('limits')
    maximum = limits.get('max_activation_bytes') if b[58](limits, b[40]) else None
    b[21](b, b[58](limits, b[40]) and b[53](limits) == {'max_activation_bytes'} and b[58](maximum, b[51]) and (not b[58](maximum, b[46])) and (maximum > 0), 'renderer limit is invalid')
    return b[64](b[49](value))

def _pack_bound(b: tuple[Any, ...], value: Mapping[str, Any], profile: Mapping[str, Any]) -> bytes:
    b[21](b, b[58](value, b[40]), 'pack must be a mapping')
    keys = b[53](value)
    b[21](b, not keys - b[37] and b[38].issubset(keys), 'pack fields are not supported')
    b[21](b, value.get('contract') in b[33] and value['contract'] in profile['supported_pack_contracts'], 'pack contract is not supported')
    b[21](b, b[13](b, value.get('profile')) == b[13](b, profile.get('pack_profile')), 'renderer profile does not bind pack profile')
    b[14](b, value.get('request'))
    identity = value.get('identity')
    b[21](b, b[58](identity, b[40]) and 'pack_identity_sha256' in identity, 'pack identity is missing')
    b[20](b, identity['pack_identity_sha256'])
    for plane in b[34]:
        box = value.get(b[12](b, plane))
        b[21](b, b[58](box, b[40]) and b[53](box) == {'items'} and b[58](box['items'], b[52]), f'{plane} plane is invalid')
    tool = value.get('toolchain')
    comps = tool.get('components') if b[58](tool, b[40]) else None
    b[21](b, b[58](tool, b[40]) and b[53](tool) == {'components'} and b[58](comps, b[52]), 'pack toolchain is invalid')
    jcs = [c for c in comps if b[58](c, b[40]) and c.get('role') == 'jcs_serializer']
    b[21](b, b[59](jcs) == 1 and jcs[0].get('contract') == 'jcs/1', 'pack does not bind exactly one jcs/1 serializer')
    try:
        return b[19](b, b[64](b[49](value)))
    except b[41] as exc:
        raise b[27]('UNSUPPORTED_RENDERER', 'pack is not canonical-JCS representable') from exc

def _frames_bound(b: tuple[Any, ...], pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    meta = b[64](b[49](pack))
    for key in b[35]:
        meta.pop(key)
    out = [b[7](b, 0, 'metadata', meta)]
    n = 1
    for plane in b[34]:
        for i, item in b[57](pack[b[12](b, plane)]['items']):
            out.append(b[7](b, n, 'plane_item', item, plane, i))
            n += 1
    return out

def _frame_bound(b: tuple[Any, ...], n: int, kind: str, payload: Any, plane: str | None=None, item: int | None=None) -> dict[str, Any]:
    raw = b[19](b, b[64](payload))
    out = {'frame_index': n, 'kind': kind, 'encoding': 'base64', 'raw_sha256': b[22](b, raw), 'data': b[63](raw).decode('ascii')}
    if plane is not None:
        out['plane'] = plane
    if item is not None:
        out['item_index'] = item
    return out

def _header_bound(b: tuple[Any, ...], a: Mapping[str, Any], profile_raw: bytes, p: Mapping[str, Any]) -> None:
    b[21](b, b[53](a) == {'contract', 'renderer_profile', 'renderer_component', 'pack', 'framing', 'frames', 'identity'} and a.get('contract') == b[30], 'rendered activation header is invalid')
    b[21](b, a.get('renderer_profile') == {'profile_id': p['profile_id'], 'profile_version': p['profile_version'], 'raw_sha256': b[22](b, profile_raw)}, 'renderer profile identity mismatch')
    b[21](b, a.get('renderer_component') == b[15](b, p['renderer_component']), 'renderer component identity mismatch')
    b[21](b, a.get('framing') == b[49](p['framing']) and b[58](a.get('frames'), b[52]) and b[58](a.get('pack'), b[40]), 'rendered activation framing is invalid')
    ident = a.get('identity')
    b[21](b, b[58](ident, b[40]) and b[53](ident) == {'activation_identity_sha256'}, 'activation identity is invalid')
    pre = b[64](b[49](a))
    pre.pop('identity')
    b[21](b, b[20](b, ident['activation_identity_sha256']) == b[23](b, 'activation_identity', b[19](b, pre)), 'activation identity mismatch')

def _decode_frames_bound(b: tuple[Any, ...], frames: list[Any]) -> dict[str, Any]:
    b[21](b, b[46](frames), 'metadata frame is missing')
    decoded = []
    for n, f in b[57](frames):
        b[21](b, b[58](f, b[40]) and f.get('frame_index') == n, 'rendered frame order is invalid')
        raw = b[10](b, f)
        try:
            payload = b[16](b, raw)
        except b[41] as exc:
            raise b[27]('UNSUPPORTED_RENDERER', 'frame payload is not strict JSON') from exc
        b[21](b, b[19](b, payload) == raw, 'frame payload is not canonical JCS')
        decoded.append((f, payload))
    first, meta = decoded[0]
    b[21](b, first.get('kind') == 'metadata' and b[53](first) == {'frame_index', 'kind', 'encoding', 'raw_sha256', 'data'} and b[58](meta, b[49]) and (not b[56]((k in meta for k in b[35]))), 'metadata frame is invalid')
    pack = b[64](meta)
    for plane in b[34]:
        pack[b[12](b, plane)] = {'items': []}
    rank = 0
    next_item = {p: 0 for p in b[34]}
    fields = {'frame_index', 'kind', 'plane', 'item_index', 'encoding', 'raw_sha256', 'data'}
    for f, payload in decoded[1:]:
        b[21](b, b[53](f) == fields and f.get('kind') == 'plane_item' and (f.get('plane') in b[34]), 'plane frame is invalid')
        plane = f['plane']
        r = b[34].index(plane)
        b[21](b, r >= rank and f.get('item_index') == next_item[plane], 'rendered plane/item order is invalid')
        rank = r
        next_item[plane] += 1
        pack[b[12](b, plane)]['items'].append(payload)
    return pack

def _frame_raw_bound(b: tuple[Any, ...], f: Mapping[str, Any]) -> bytes:
    b[21](b, f.get('encoding') == 'base64' and b[58](f.get('data'), b[54]), 'unsupported frame encoding')
    try:
        raw = b[62](f['data'].encode('ascii'), validate=True)
    except b[41] as exc:
        raise b[27]('UNSUPPORTED_RENDERER', 'invalid frame base64') from exc
    b[21](b, b[20](b, f.get('raw_sha256')) == b[22](b, raw), 'frame digest mismatch')
    return raw

def _pack_summary_bound(b: tuple[Any, ...], pack: Mapping[str, Any], raw: bytes) -> dict[str, Any]:
    return {'contract': pack['contract'], 'profile': b[13](b, pack['profile']), 'request': b[14](b, pack['request']), 'pack_identity_sha256': b[20](b, pack['identity']['pack_identity_sha256']), 'serialized_pack_sha256': b[22](b, raw)}

def _plane_key_bound(b: tuple[Any, ...], plane: str) -> str:
    return b[35][b[34].index(plane)]

def _profile_id_bound(b: tuple[Any, ...], v: Any) -> dict[str, str]:
    b[21](b, b[58](v, b[40]) and b[53](v) == {'profile_id', 'profile_version', 'raw_sha256'} and b[58](v.get('profile_id'), b[54]) and b[46](v['profile_id']) and b[58](v.get('profile_version'), b[54]) and b[46](v['profile_version']), 'profile identity is invalid')
    return {'profile_id': v['profile_id'], 'profile_version': v['profile_version'], 'raw_sha256': b[20](b, v['raw_sha256'])}

def _request_id_bound(b: tuple[Any, ...], v: Any) -> dict[str, str]:
    b[21](b, b[58](v, b[40]) and b[53](v) == {'request_id', 'raw_sha256'} and b[58](v.get('request_id'), b[54]) and b[46](v['request_id']), 'request identity is invalid')
    return {'request_id': v['request_id'], 'raw_sha256': b[20](b, v['raw_sha256'])}

def _component_bound(b: tuple[Any, ...], v: Any) -> dict[str, str]:
    keys = {'role', 'contract', 'immutable_identity', 'raw_sha256'}
    b[21](b, b[58](v, b[40]) and b[53](v) == keys and b[55]((b[58](v.get(k), b[54]) and v[k] for k in ('role', 'contract', 'immutable_identity'))), 'renderer component is invalid')
    imm = v['immutable_identity']
    b[21](b, imm.startswith('git-blob:') and b[59](imm) == 49 and b[55]((c in '0123456789abcdef' for c in imm[9:])), 'renderer component immutable identity is invalid')
    return {'role': v['role'], 'contract': v['contract'], 'immutable_identity': imm, 'raw_sha256': b[20](b, v['raw_sha256'])}

def _strict_json_bound(b: tuple[Any, ...], raw: bytes) -> Any:
    value_error = b[45]

    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise value_error('duplicate JSON member')
            out[key] = value
        return out

    def bad(value):
        raise value_error(value)
    return b[67](raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=bad)

def _jcs_string_bound(b: tuple[Any, ...], value: str) -> bytes:
    out = b[47](b'"')
    escapes = {8: b'\\b', 9: b'\\t', 10: b'\\n', 12: b'\\f', 13: b'\\r', 34: b'\\"', 92: b'\\\\'}
    try:
        value.encode('utf-8')
    except b[44] as exc:
        raise b[45] from exc
    for ch in value:
        cp = b[60](ch)
        out.extend(escapes[cp] if cp in escapes else f'\\u{cp:04x}'.encode() if cp <= 31 else ch.encode('utf-8'))
    return b[48](out + b'"')

def _jcs_float_bound(b: tuple[Any, ...], value: float) -> bytes:
    if not b[68](value):
        raise b[45]
    if value == 0:
        return b'0'
    if value < 0:
        return b'-' + b[18](b, -value)
    text = b[54](value)
    exp = 0
    exp_text = ''
    if 'e' in text:
        mantissa, raw = text.split('e', 1)
        exp = b[51](raw)
        exp_text = ('e+' if exp >= 0 else 'e-') + b[54](-exp if exp < 0 else exp)
    else:
        mantissa = text
    if '.' in mantissa:
        first, last = mantissa.split('.', 1)
        dot = '.'
    else:
        first, last, dot = (mantissa, '', '')
    if last == '0':
        last, dot = ('', '')
    if 0 < exp < 21:
        first += last
        last = dot = exp_text = ''
        missing = exp - b[59](first)
        while missing >= 0:
            first += '0'
            missing -= 1
    elif -7 < exp < 0:
        last = first + last
        first, dot, exp_text, missing = ('0', '.', '', exp)
        while missing < -1:
            last = '0' + last
            missing += 1
    return f'{first}{dot}{last}{exp_text}'.encode()

def _jcs_bound(b: tuple[Any, ...], value: Any) -> bytes:
    sink = b[66]()

    def emit(obj):
        if obj is None:
            sink.write(b'null')
        elif obj is True:
            sink.write(b'true')
        elif obj is False:
            sink.write(b'false')
        elif b[58](obj, b[54]):
            sink.write(b[17](b, obj))
        elif b[58](obj, b[51]):
            if not -(2 ** 53 - 1) <= obj <= 2 ** 53 - 1:
                raise b[45]
            sink.write(b[54](obj).encode())
        elif b[58](obj, b[50]):
            sink.write(b[18](b, obj))
        elif b[58](obj, b[52]):
            sink.write(b'[')
            for i, item in b[57](obj):
                if i:
                    sink.write(b',')
                emit(item)
            sink.write(b']')
        elif b[58](obj, b[49]):
            if b[56]((not b[58](key, b[54]) for key in obj)):
                raise b[45]
            try:
                items = b[61](obj.items(), key=lambda item: item[0].encode('utf-16be'))
            except b[44] as exc:
                raise b[45] from exc
            sink.write(b'{')
            for i, (key, item) in b[57](items):
                if i:
                    sink.write(b',')
                sink.write(b[17](b, key))
                sink.write(b':')
                emit(item)
            sink.write(b'}')
        else:
            raise b[45]
    emit(value)
    return sink.getvalue()

def _jcs(value: Any) -> bytes:
    bundle = _resolve_bundle()
    return bundle[19](bundle, value)

def _norm_bound(b: tuple[Any, ...], v: Any) -> str:
    b[21](b, b[58](v, b[54]) and b[59](v) == 71 and v.startswith('sha256:') and b[55]((c in '0123456789abcdefABCDEF' for c in v[7:])), 'invalid sha256 identity')
    return 'sha256:' + v[7:].lower()

def _need_bound(b: tuple[Any, ...], ok: bool, message: str) -> None:
    if not ok:
        raise b[27]('UNSUPPORTED_RENDERER', message)

def _sha_bound(b: tuple[Any, ...], raw: bytes) -> str:
    return 'sha256:' + b[65](raw).hexdigest()

def _domain_bound(b: tuple[Any, ...], domain: str, raw: bytes) -> str:
    return b[22](b, b[39] + domain.encode('ascii') + b'\x00' + raw)

def _failure_bound(b: tuple[Any, ...], code: str, diagnostic: str) -> dict[str, Any]:
    return {'contract': b[32], 'code': code, 'stage': 'rendering', 'diagnostics': [diagnostic]}
