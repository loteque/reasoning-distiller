from __future__ import annotations
from base64 import b64decode as _b64decode_primitive, b64encode as _b64encode_primitive
from collections.abc import Mapping
from hashlib import sha256 as _sha256_primitive
from io import BytesIO as _BytesIO_primitive
from json import loads as _json_loads_primitive
from math import isfinite as _isfinite_primitive
from dis import Bytecode as _Bytecode_primitive, get_instructions as _get_instructions_primitive, hasconst as _dis_hasconst_source, hasname as _dis_hasname_source, haslocal as _dis_haslocal_source, hasfree as _dis_hasfree_source, hasjrel as _dis_hasjrel_source, hasjabs as _dis_hasjabs_source
from struct import pack as _struct_pack_primitive
from types import CodeType as _CodeType_primitive, FunctionType as _FunctionType_primitive
import sys as _sys_runtime
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
RENDERER_CONTRACT_V2 = 'reasoning-distiller-context-renderer/2'
RENDERER_PROFILE_CONTRACT_V2 = 'reasoning-distiller-context-renderer-profile/2'
RENDERED_ACTIVATION_CONTRACT_V2 = 'reasoning-distiller-context-rendered-activation/2'
EXECUTION_BINDING_CONTRACT = 'reasoning-distiller-renderer-execution-binding/1'
BUNDLE_SCHEME = 'python-closed-bundle/1'
DESCRIPTOR_CONTRACT = 'reasoning-distiller-python-closed-bundle-descriptor/1'
_PROFILE_V2_KEYS = frozenset({'contract', 'profile_id', 'profile_version', 'supported_pack_contracts', 'pack_profile', 'renderer_execution_binding', 'framing', 'limits'})
_EXPECTED_RUNTIME_ABI = ('cpython', 3, 12, 0, 'cpython-312')
_RUNTIME_ABI_CAPTURE = (_sys_runtime.implementation.name, _sys_runtime.version_info.major, _sys_runtime.version_info.minor, _sys_runtime.version_info.micro, _sys_runtime.implementation.cache_tag)
_DIS_HASCONST = tuple(_dis_hasconst_source)
_DIS_HASNAME = tuple(_dis_hasname_source)
_DIS_HASLOCAL = tuple(_dis_haslocal_source)
_DIS_HASFREE = tuple(_dis_hasfree_source)
_DIS_HASJREL = tuple(_dis_hasjrel_source)
_DIS_HASJABS = tuple(_dis_hasjabs_source)
_BINDING_DOMAIN = b'reasoning-distiller-renderer-execution-binding/1\x00python-closed-bundle/1\x00'
_PRIMITIVE_REGISTRY = (('primitive:base64.b64decode', 62, 'cpython-3.12.0:base64.b64decode', 'exact_abi_python_callable', 'base64', 'b64decode', 'base64', 'b64decode'), ('primitive:base64.b64encode', 63, 'cpython-3.12.0:base64.b64encode', 'exact_abi_python_callable', 'base64', 'b64encode', 'base64', 'b64encode'), ('primitive:builtins.Exception', 41, 'cpython-3.12.0:builtins.Exception', 'exact_abi_type', 'builtins', 'Exception', 'builtins', 'Exception'), ('primitive:builtins.KeyError', 42, 'cpython-3.12.0:builtins.KeyError', 'exact_abi_type', 'builtins', 'KeyError', 'builtins', 'KeyError'), ('primitive:builtins.TypeError', 43, 'cpython-3.12.0:builtins.TypeError', 'exact_abi_type', 'builtins', 'TypeError', 'builtins', 'TypeError'), ('primitive:builtins.UnicodeError', 44, 'cpython-3.12.0:builtins.UnicodeError', 'exact_abi_type', 'builtins', 'UnicodeError', 'builtins', 'UnicodeError'), ('primitive:builtins.ValueError', 45, 'cpython-3.12.0:builtins.ValueError', 'exact_abi_type', 'builtins', 'ValueError', 'builtins', 'ValueError'), ('primitive:builtins.all', 55, 'cpython-3.12.0:builtins.all', 'exact_abi_builtin', 'builtins', 'all', 'builtins', 'all'), ('primitive:builtins.any', 56, 'cpython-3.12.0:builtins.any', 'exact_abi_builtin', 'builtins', 'any', 'builtins', 'any'), ('primitive:builtins.bool', 46, 'cpython-3.12.0:builtins.bool', 'exact_abi_type', 'builtins', 'bool', 'builtins', 'bool'), ('primitive:builtins.bytearray', 47, 'cpython-3.12.0:builtins.bytearray', 'exact_abi_type', 'builtins', 'bytearray', 'builtins', 'bytearray'), ('primitive:builtins.bytes', 48, 'cpython-3.12.0:builtins.bytes', 'exact_abi_type', 'builtins', 'bytes', 'builtins', 'bytes'), ('primitive:builtins.dict', 49, 'cpython-3.12.0:builtins.dict', 'exact_abi_type', 'builtins', 'dict', 'builtins', 'dict'), ('primitive:builtins.enumerate', 57, 'cpython-3.12.0:builtins.enumerate', 'exact_abi_type', 'builtins', 'enumerate', 'builtins', 'enumerate'), ('primitive:builtins.float', 50, 'cpython-3.12.0:builtins.float', 'exact_abi_type', 'builtins', 'float', 'builtins', 'float'), ('primitive:builtins.int', 51, 'cpython-3.12.0:builtins.int', 'exact_abi_type', 'builtins', 'int', 'builtins', 'int'), ('primitive:builtins.isinstance', 58, 'cpython-3.12.0:builtins.isinstance', 'exact_abi_builtin', 'builtins', 'isinstance', 'builtins', 'isinstance'), ('primitive:builtins.len', 59, 'cpython-3.12.0:builtins.len', 'exact_abi_builtin', 'builtins', 'len', 'builtins', 'len'), ('primitive:builtins.list', 52, 'cpython-3.12.0:builtins.list', 'exact_abi_type', 'builtins', 'list', 'builtins', 'list'), ('primitive:builtins.ord', 60, 'cpython-3.12.0:builtins.ord', 'exact_abi_builtin', 'builtins', 'ord', 'builtins', 'ord'), ('primitive:builtins.set', 53, 'cpython-3.12.0:builtins.set', 'exact_abi_type', 'builtins', 'set', 'builtins', 'set'), ('primitive:builtins.sorted', 61, 'cpython-3.12.0:builtins.sorted', 'exact_abi_builtin', 'builtins', 'sorted', 'builtins', 'sorted'), ('primitive:builtins.str', 54, 'cpython-3.12.0:builtins.str', 'exact_abi_type', 'builtins', 'str', 'builtins', 'str'), ('primitive:collections.abc.Mapping', 40, 'cpython-3.12.0:collections.abc.Mapping', 'exact_abi_type', 'collections.abc', 'Mapping', 'collections.abc', 'Mapping'), ('primitive:dis.Bytecode', 123, 'cpython-3.12.0:dis.Bytecode', 'exact_abi_type', 'dis', 'Bytecode', 'dis', 'Bytecode'), ('primitive:dis.get_instructions', 124, 'cpython-3.12.0:dis.get_instructions', 'exact_abi_python_callable', 'dis', 'get_instructions', 'dis', 'get_instructions'), ('primitive:hashlib.sha256', 65, 'cpython-3.12.0:hashlib.sha256', 'exact_abi_builtin', 'hashlib', 'sha256', '_hashlib', 'openssl_sha256'), ('primitive:io.BytesIO', 66, 'cpython-3.12.0:io.BytesIO', 'exact_abi_type', 'io', 'BytesIO', '_io', 'BytesIO'), ('primitive:json.loads', 67, 'cpython-3.12.0:json.loads', 'exact_abi_python_callable', 'json', 'loads', 'json', 'loads'), ('primitive:math.isfinite', 68, 'cpython-3.12.0:math.isfinite', 'exact_abi_builtin', 'math', 'isfinite', 'math', 'isfinite'), ('primitive:struct.pack', 125, 'cpython-3.12.0:struct.pack', 'exact_abi_builtin', 'struct', 'pack', '_struct', 'pack'), ('primitive:types.CodeType', 126, 'cpython-3.12.0:types.CodeType', 'exact_abi_type', 'types', 'CodeType', 'builtins', 'code'), ('primitive:types.FunctionType', 127, 'cpython-3.12.0:types.FunctionType', 'exact_abi_type', 'types', 'FunctionType', 'builtins', 'function'))
_TYPE_LAYOUT = (('member:type:RenderedActivationDecodeResult', 'context_packaging.renderer', 'RenderedActivationDecodeResult', (), (('__init__', 'member:decode_result_init', 'function'), ('pack', 'member:decode_result_pack_get', 'property'), ('failure', 'member:decode_result_failure_get', 'property'), ('ok', 'member:decode_result_ok_get', 'property')), (('__slots__', 'member:constant:decode_result_slots'),)), ('member:type:RenderedActivationResult', 'context_packaging.renderer', 'RenderedActivationResult', (), (('__init__', 'member:render_result_init', 'function'), ('activation', 'member:render_result_activation_get', 'property'), ('serialized_activation', 'member:render_result_serialized_activation_get', 'property'), ('serialized_activation_sha256', 'member:render_result_serialized_activation_sha256_get', 'property'), ('failure', 'member:render_result_failure_get', 'property'), ('ok', 'member:render_result_ok_get', 'property')), (('__slots__', 'member:constant:render_result_slots'),)), ('member:type:_RF', 'context_packaging.renderer', '_RF', ('primitive:builtins.ValueError',), (), ()))
_BOOTSTRAP_DEPENDENCIES = (('member:compare_execution_binding', (('_resolve_bundle', 'member:resolve_bundle'),)), ('member:decode', (('_resolve_bundle', 'member:resolve_bundle'),)), ('member:decode_v1', (('_resolve_bundle', 'member:resolve_bundle'),)), ('member:derive_execution_binding', (('_resolve_bundle', 'member:resolve_bundle'),)), ('member:describe_bundle', (('_resolve_bundle', 'member:resolve_bundle'),)), ('member:jcs_bootstrap', (('_resolve_bundle', 'member:resolve_bundle'),)), ('member:render', (('_resolve_bundle', 'member:resolve_bundle'),)), ('member:render_v1', (('_resolve_bundle', 'member:resolve_bundle'),)), ('member:resolve_bundle', (('BUNDLE_SCHEME', 'member:constant:bundle_scheme'), ('DESCRIPTOR_CONTRACT', 'member:constant:descriptor_contract'), ('EXECUTION_BINDING_CONTRACT', 'member:constant:execution_binding_contract'), ('Exception', 'primitive:builtins.Exception'), ('FAILURE_CONTRACT', 'member:constant:failure_contract'), ('FRAMING_CONTRACT', 'member:constant:framing_contract'), ('KeyError', 'primitive:builtins.KeyError'), ('Mapping', 'primitive:collections.abc.Mapping'), ('PACK_CONTRACTS', 'member:constant:pack_contracts'), ('PLANE_ORDER', 'member:constant:plane_order'), ('RENDERED_ACTIVATION_CONTRACT', 'member:constant:rendered_activation_contract'), ('RENDERED_ACTIVATION_CONTRACT_V2', 'member:constant:rendered_activation_contract_v2'), ('RENDERER_CONTRACT', 'member:constant:renderer_contract'), ('RENDERER_CONTRACT_V2', 'member:constant:renderer_contract_v2'), ('RENDERER_PROFILE_CONTRACT', 'member:constant:renderer_profile_contract'), ('RENDERER_PROFILE_CONTRACT_V2', 'member:constant:renderer_profile_contract_v2'), ('RenderedActivationDecodeResult', 'member:type:RenderedActivationDecodeResult'), ('RenderedActivationResult', 'member:type:RenderedActivationResult'), ('TypeError', 'primitive:builtins.TypeError'), ('UnicodeError', 'primitive:builtins.UnicodeError'), ('ValueError', 'primitive:builtins.ValueError'), ('_BINDING_DOMAIN', 'member:constant:binding_domain'), ('_BOOTSTRAP_DEPENDENCIES', 'member:constant:bootstrap_dependencies'), ('_Bytecode_primitive', 'primitive:dis.Bytecode'), ('_BytesIO_primitive', 'primitive:io.BytesIO'), ('_CodeType_primitive', 'primitive:types.CodeType'), ('_DIGEST_MAGIC', 'member:constant:digest_magic'), ('_DIS_HASCONST', 'member:constant:dis_hasconst'), ('_DIS_HASFREE', 'member:constant:dis_hasfree'), ('_DIS_HASJABS', 'member:constant:dis_hasjabs'), ('_DIS_HASJREL', 'member:constant:dis_hasjrel'), ('_DIS_HASLOCAL', 'member:constant:dis_haslocal'), ('_DIS_HASNAME', 'member:constant:dis_hasname'), ('_EXPECTED_RUNTIME_ABI', 'member:constant:expected_runtime_abi'), ('_FunctionType_primitive', 'primitive:types.FunctionType'), ('_MEMBER_REGISTRY', 'member:registry'), ('_PACK_KEYS', 'member:constant:pack_keys'), ('_PACK_REQUIRED_KEYS', 'member:constant:pack_required_keys'), ('_PLANE_KEYS', 'member:constant:plane_keys'), ('_PRIMITIVE_REGISTRY', 'member:constant:primitive_registry'), ('_PROFILE_KEYS', 'member:constant:profile_keys'), ('_PROFILE_V2_KEYS', 'member:constant:profile_v2_keys'), ('_RF', 'member:type:_RF'), ('_RUNTIME_ABI_CAPTURE', 'member:constant:runtime_abi_capture'), ('_TYPE_LAYOUT', 'member:constant:type_layout'), ('_b64decode_primitive', 'primitive:base64.b64decode'), ('_b64encode_primitive', 'primitive:base64.b64encode'), ('_binding_shape_bound', 'member:binding_shape'), ('_callable_parts_bound', 'member:callable_parts'), ('_code_descriptor_bound', 'member:code_descriptor'), ('_compare_execution_binding_bound', 'member:compare_execution_binding_execute'), ('_component_bound', 'member:component'), ('_decode_bound', 'member:decode_execute'), ('_decode_frames_bound', 'member:decode_frames'), ('_decode_v2_bound', 'member:decode_v2_execute'), ('_derive_execution_binding_bound', 'member:derive_execution_binding_execute'), ('_describe_bundle_bound', 'member:describe_bundle_execute'), ('_descriptor_members_bound', 'member:descriptor_members'), ('_domain_bound', 'member:domain'), ('_failure_bound', 'member:failure'), ('_frame_bound', 'member:frame'), ('_frame_raw_bound', 'member:frame_raw'), ('_frames_bound', 'member:frames'), ('_function_descriptor_bound', 'member:function_descriptor'), ('_get_bound', 'member:get'), ('_get_instructions_primitive', 'primitive:dis.get_instructions'), ('_global_dependencies_bound', 'member:global_dependencies'), ('_header_bound', 'member:header'), ('_header_v2_bound', 'member:header_v2'), ('_isfinite_primitive', 'primitive:math.isfinite'), ('_jcs', 'member:jcs_bootstrap'), ('_jcs_bound', 'member:jcs'), ('_jcs_clone_bound', 'member:jcs_clone'), ('_jcs_float_bound', 'member:jcs_float'), ('_jcs_string_bound', 'member:jcs_string'), ('_json_loads_primitive', 'primitive:json.loads'), ('_lookup_target_bound', 'member:lookup_target'), ('_member_id_for_object_bound', 'member:member_id_for_object'), ('_need_bound', 'member:need'), ('_norm_bound', 'member:norm'), ('_normalize_value_bound', 'member:normalize_value'), ('_offset_ordinal_bound', 'member:offset_ordinal'), ('_pack_bound', 'member:pack'), ('_pack_summary_bound', 'member:pack_summary'), ('_plane_key_bound', 'member:plane_key'), ('_primitive_descriptor_bound', 'member:primitive_descriptor'), ('_profile_bound', 'member:profile'), ('_profile_id_bound', 'member:profile_id'), ('_profile_v2_bound', 'member:profile_v2'), ('_render_bound', 'member:render_execute'), ('_render_v2_bound', 'member:render_v2_execute'), ('_request_id_bound', 'member:request_id'), ('_resolve_bundle', 'member:resolve_bundle'), ('_runtime_abi_bound', 'member:runtime_abi'), ('_sha256_primitive', 'primitive:hashlib.sha256'), ('_sha_bound', 'member:sha'), ('_strict_json_bound', 'member:strict_json'), ('_struct_pack_primitive', 'primitive:struct.pack'), ('_type_descriptor_bound', 'member:type_descriptor'), ('all', 'primitive:builtins.all'), ('any', 'primitive:builtins.any'), ('bool', 'primitive:builtins.bool'), ('bytearray', 'primitive:builtins.bytearray'), ('bytes', 'primitive:builtins.bytes'), ('compare_execution_binding', 'member:compare_execution_binding'), ('decode_rendered_activation', 'member:decode_v1'), ('decode_rendered_activation_v2', 'member:decode'), ('derive_execution_binding', 'member:derive_execution_binding'), ('describe_bundle', 'member:describe_bundle'), ('dict', 'primitive:builtins.dict'), ('enumerate', 'primitive:builtins.enumerate'), ('float', 'primitive:builtins.float'), ('int', 'primitive:builtins.int'), ('isinstance', 'primitive:builtins.isinstance'), ('len', 'primitive:builtins.len'), ('list', 'primitive:builtins.list'), ('ord', 'primitive:builtins.ord'), ('render_context_pack', 'member:render_v1'), ('render_context_pack_v2', 'member:render'), ('set', 'primitive:builtins.set'), ('sorted', 'primitive:builtins.sorted'), ('str', 'primitive:builtins.str'))))
_MEMBER_REGISTRY = (('member:binding_shape', 119), ('member:callable_parts', 112), ('member:code_descriptor', 111), ('member:compare_execution_binding', 132), ('member:compare_execution_binding_execute', 109), ('member:component', 15), ('member:constant:binding_domain', 101), ('member:constant:bootstrap_dependencies', 133), ('member:constant:bundle_scheme', 89), ('member:constant:decode_result_slots', 84), ('member:constant:descriptor_contract', 90), ('member:constant:digest_magic', 39), ('member:constant:dis_hasconst', 95), ('member:constant:dis_hasfree', 98), ('member:constant:dis_hasjabs', 100), ('member:constant:dis_hasjrel', 99), ('member:constant:dis_haslocal', 97), ('member:constant:dis_hasname', 96), ('member:constant:execution_binding_contract', 88), ('member:constant:expected_runtime_abi', 92), ('member:constant:failure_contract', 32), ('member:constant:framing_contract', 31), ('member:constant:pack_contracts', 33), ('member:constant:pack_keys', 37), ('member:constant:pack_required_keys', 38), ('member:constant:plane_keys', 35), ('member:constant:plane_order', 34), ('member:constant:primitive_registry', 94), ('member:constant:profile_keys', 36), ('member:constant:profile_v2_keys', 91), ('member:constant:render_result_slots', 83), ('member:constant:rendered_activation_contract', 30), ('member:constant:rendered_activation_contract_v2', 87), ('member:constant:renderer_contract', 28), ('member:constant:renderer_contract_v2', 85), ('member:constant:renderer_profile_contract', 29), ('member:constant:renderer_profile_contract_v2', 86), ('member:constant:runtime_abi_capture', 93), ('member:constant:type_layout', 102), ('member:decode', 129), ('member:decode_execute', 2), ('member:decode_frames', 9), ('member:decode_result_failure_get', 81), ('member:decode_result_init', 71), ('member:decode_result_ok_get', 82), ('member:decode_result_pack_get', 80), ('member:decode_v1', 73), ('member:decode_v2_execute', 104), ('member:derive_execution_binding', 131), ('member:derive_execution_binding_execute', 108), ('member:describe_bundle', 130), ('member:describe_bundle_execute', 107), ('member:descriptor_members', 116), ('member:domain', 23), ('member:failure', 24), ('member:frame', 7), ('member:frame_raw', 10), ('member:frames', 6), ('member:function_descriptor', 113), ('member:get', 69), ('member:global_dependencies', 117), ('member:header', 8), ('member:header_v2', 106), ('member:jcs', 19), ('member:jcs_bootstrap', 74), ('member:jcs_clone', 64), ('member:jcs_float', 18), ('member:jcs_string', 17), ('member:lookup_target', 121), ('member:member_id_for_object', 122), ('member:need', 21), ('member:norm', 20), ('member:normalize_value', 110), ('member:offset_ordinal', 118), ('member:pack', 5), ('member:pack_summary', 11), ('member:plane_key', 12), ('member:primitive_descriptor', 115), ('member:profile', 4), ('member:profile_id', 13), ('member:profile_v2', 105), ('member:registry', 0), ('member:render', 128), ('member:render_execute', 1), ('member:render_result_activation_get', 75), ('member:render_result_failure_get', 78), ('member:render_result_init', 70), ('member:render_result_ok_get', 79), ('member:render_result_serialized_activation_get', 76), ('member:render_result_serialized_activation_sha256_get', 77), ('member:render_v1', 72), ('member:render_v2_execute', 103), ('member:request_id', 14), ('member:resolve_bundle', 3), ('member:runtime_abi', 120), ('member:sha', 22), ('member:strict_json', 16), ('member:type:RenderedActivationDecodeResult', 26), ('member:type:RenderedActivationResult', 25), ('member:type:_RF', 27), ('member:type_descriptor', 114))
del _sys_runtime, _dis_hasconst_source, _dis_hasname_source, _dis_haslocal_source, _dis_hasfree_source, _dis_hasjrel_source, _dis_hasjabs_source

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


def render_context_pack_v2(pack: Mapping[str, Any], profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationResult:
    bundle = _resolve_bundle()
    return bundle[103](bundle, pack, profile_raw, profile)

def decode_rendered_activation_v2(raw: bytes, profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationDecodeResult:
    bundle = _resolve_bundle()
    return bundle[104](bundle, raw, profile_raw, profile)

def describe_bundle() -> dict[str, Any]:
    bundle = _resolve_bundle()
    return bundle[107](bundle)

def derive_execution_binding() -> dict[str, Any]:
    bundle = _resolve_bundle()
    return bundle[108](bundle)

def compare_execution_binding(expected: Mapping[str, Any], actual: Mapping[str, Any]) -> None:
    bundle = _resolve_bundle()
    bundle[109](bundle, expected, actual)

def _resolve_bundle() -> tuple[Any, ...]:
    return (_MEMBER_REGISTRY, _render_bound, _decode_bound, _resolve_bundle, _profile_bound, _pack_bound, _frames_bound, _frame_bound, _header_bound, _decode_frames_bound, _frame_raw_bound, _pack_summary_bound, _plane_key_bound, _profile_id_bound, _request_id_bound, _component_bound, _strict_json_bound, _jcs_string_bound, _jcs_float_bound, _jcs_bound, _norm_bound, _need_bound, _sha_bound, _domain_bound, _failure_bound, RenderedActivationResult, RenderedActivationDecodeResult, _RF, RENDERER_CONTRACT, RENDERER_PROFILE_CONTRACT, RENDERED_ACTIVATION_CONTRACT, FRAMING_CONTRACT, FAILURE_CONTRACT, PACK_CONTRACTS, PLANE_ORDER, _PLANE_KEYS, _PROFILE_KEYS, _PACK_KEYS, _PACK_REQUIRED_KEYS, _DIGEST_MAGIC, Mapping, Exception, KeyError, TypeError, UnicodeError, ValueError, bool, bytearray, bytes, dict, float, int, list, set, str, all, any, enumerate, isinstance, len, ord, sorted, _b64decode_primitive, _b64encode_primitive, _jcs_clone_bound, _sha256_primitive, _BytesIO_primitive, _json_loads_primitive, _isfinite_primitive, _get_bound, RenderedActivationResult.__init__, RenderedActivationDecodeResult.__init__, render_context_pack, decode_rendered_activation, _jcs, RenderedActivationResult.activation.fget, RenderedActivationResult.serialized_activation.fget, RenderedActivationResult.serialized_activation_sha256.fget, RenderedActivationResult.failure.fget, RenderedActivationResult.ok.fget, RenderedActivationDecodeResult.pack.fget, RenderedActivationDecodeResult.failure.fget, RenderedActivationDecodeResult.ok.fget, RenderedActivationResult.__slots__, RenderedActivationDecodeResult.__slots__, RENDERER_CONTRACT_V2, RENDERER_PROFILE_CONTRACT_V2, RENDERED_ACTIVATION_CONTRACT_V2, EXECUTION_BINDING_CONTRACT, BUNDLE_SCHEME, DESCRIPTOR_CONTRACT, _PROFILE_V2_KEYS, _EXPECTED_RUNTIME_ABI, _RUNTIME_ABI_CAPTURE, _PRIMITIVE_REGISTRY, _DIS_HASCONST, _DIS_HASNAME, _DIS_HASLOCAL, _DIS_HASFREE, _DIS_HASJREL, _DIS_HASJABS, _BINDING_DOMAIN, _TYPE_LAYOUT, _render_v2_bound, _decode_v2_bound, _profile_v2_bound, _header_v2_bound, _describe_bundle_bound, _derive_execution_binding_bound, _compare_execution_binding_bound, _normalize_value_bound, _code_descriptor_bound, _callable_parts_bound, _function_descriptor_bound, _type_descriptor_bound, _primitive_descriptor_bound, _descriptor_members_bound, _global_dependencies_bound, _offset_ordinal_bound, _binding_shape_bound, _runtime_abi_bound, _lookup_target_bound, _member_id_for_object_bound, _Bytecode_primitive, _get_instructions_primitive, _struct_pack_primitive, _CodeType_primitive, _FunctionType_primitive, render_context_pack_v2, decode_rendered_activation_v2, describe_bundle, derive_execution_binding, compare_execution_binding, _BOOTSTRAP_DEPENDENCIES)

def _render_bound(b: tuple[Any, ...], pack: Mapping[str, Any], profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationResult:
    try:
        p = b[4](b, profile_raw, profile)
        pack_raw = b[5](b, pack, p)
        out: dict[str, Any] = {'contract': b[30], 'renderer_profile': {'profile_id': p['profile_id'], 'profile_version': p['profile_version'], 'raw_sha256': b[22](b, profile_raw)}, 'renderer_component': b[15](b, p['renderer_component']), 'pack': b[11](b, pack, pack_raw), 'framing': b[64](b, b[49](p['framing'])), 'frames': b[6](b, pack)}
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
    return b[64](b, b[49](value))

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
        return b[19](b, b[64](b, b[49](value)))
    except b[41] as exc:
        raise b[27]('UNSUPPORTED_RENDERER', 'pack is not canonical-JCS representable') from exc

def _frames_bound(b: tuple[Any, ...], pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    meta = b[64](b, b[49](pack))
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
    raw = b[19](b, b[64](b, payload))
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
    pre = b[64](b, b[49](a))
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
    pack = b[64](b, meta)
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


def _jcs_clone_bound(b: tuple[Any, ...], value: Any) -> Any:
    return b[16](b, b[19](b, value))

def _render_v2_bound(b: tuple[Any, ...], pack: Mapping[str, Any], profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationResult:
    try:
        p = b[105](b, profile_raw, profile)
        actual = b[108](b)
        b[109](b, p['renderer_execution_binding'], actual)
        pack_raw = b[5](b, pack, p)
        out: dict[str, Any] = {
            'contract': b[87],
            'renderer_profile': {'profile_id': p['profile_id'], 'profile_version': p['profile_version'], 'raw_sha256': b[22](b, profile_raw)},
            'renderer_execution_binding': actual,
            'pack': b[11](b, pack, pack_raw),
            'framing': b[64](b, b[49](p['framing'])),
            'frames': b[6](b, pack),
        }
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

def _decode_v2_bound(b: tuple[Any, ...], raw: bytes, profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationDecodeResult:
    try:
        p = b[105](b, profile_raw, profile)
        actual = b[108](b)
        b[109](b, p['renderer_execution_binding'], actual)
        b[21](b, b[58](raw, b[48]), 'rendered activation must be bytes')
        try:
            activation = b[16](b, raw)
        except b[41] as exc:
            raise b[27]('UNSUPPORTED_RENDERER', 'rendered activation is not strict UTF-8 JSON') from exc
        b[21](b, b[58](activation, b[49]) and b[19](b, activation) == raw, 'rendered activation is not canonical JCS bytes')
        b[106](b, activation, profile_raw, p, actual)
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

def _profile_v2_bound(b: tuple[Any, ...], raw: bytes, value: Mapping[str, Any]) -> dict[str, Any]:
    b[21](b, b[58](raw, b[48]) and b[58](value, b[40]), 'renderer /2 profile must be mapping plus exact raw bytes')
    try:
        parsed = b[16](b, raw)
    except b[41] as exc:
        raise b[27]('UNSUPPORTED_RENDERER', 'renderer /2 profile raw bytes must be strict UTF-8 JSON') from exc
    b[21](b, parsed == b[49](value), 'renderer /2 profile raw bytes do not bind profile object')
    b[21](b, b[53](value) == b[91] and value.get('contract') == b[86], 'unsupported renderer /2 profile contract or fields')
    b[21](b, b[55]((b[58](value.get(k), b[54]) and value[k] for k in ('profile_id', 'profile_version'))), 'renderer /2 profile identity is invalid')
    supported = value.get('supported_pack_contracts')
    b[21](b, b[58](supported, b[52]) and supported and (b[59](supported) == b[59](b[53](supported))) and b[55]((x in b[33] for x in supported)), 'supported pack contracts are invalid')
    b[21](b, supported == [x for x in b[33] if x in supported], 'supported pack contracts are not canonical order')
    b[13](b, value.get('pack_profile'))
    b[119](b, value.get('renderer_execution_binding'))
    f = value.get('framing')
    b[21](b, b[58](f, b[40]) and b[53](f) == {'contract', 'serializer', 'text_encoding', 'item_encoding', 'plane_order'}, 'renderer framing is invalid')
    b[21](b, f.get('contract') == b[31] and f.get('serializer') == 'jcs/1' and (f.get('text_encoding') == 'utf-8') and (f.get('item_encoding') == 'base64') and (f.get('plane_order') == b[52](b[34])), 'unsupported renderer framing')
    limits = value.get('limits')
    maximum = limits.get('max_activation_bytes') if b[58](limits, b[40]) else None
    b[21](b, b[58](limits, b[40]) and b[53](limits) == {'max_activation_bytes'} and b[58](maximum, b[51]) and (not b[58](maximum, b[46])) and (maximum > 0), 'renderer limit is invalid')
    return b[64](b, b[49](value))

def _header_v2_bound(b: tuple[Any, ...], a: Mapping[str, Any], profile_raw: bytes, p: Mapping[str, Any], actual: Mapping[str, Any]) -> None:
    b[21](b, b[53](a) == {'contract', 'renderer_profile', 'renderer_execution_binding', 'pack', 'framing', 'frames', 'identity'} and a.get('contract') == b[87], 'rendered /2 activation header is invalid')
    b[21](b, a.get('renderer_profile') == {'profile_id': p['profile_id'], 'profile_version': p['profile_version'], 'raw_sha256': b[22](b, profile_raw)}, 'renderer profile identity mismatch')
    b[109](b, a.get('renderer_execution_binding'), actual)
    b[21](b, a.get('framing') == b[49](p['framing']) and b[58](a.get('frames'), b[52]) and b[58](a.get('pack'), b[40]), 'rendered activation framing is invalid')
    ident = a.get('identity')
    b[21](b, b[58](ident, b[40]) and b[53](ident) == {'activation_identity_sha256'}, 'activation identity is invalid')
    pre = b[64](b, b[49](a))
    pre.pop('identity')
    b[21](b, b[20](b, ident['activation_identity_sha256']) == b[23](b, 'activation_identity', b[19](b, pre)), 'activation identity mismatch')

def _runtime_abi_bound(b: tuple[Any, ...]) -> dict[str, Any]:
    actual = b[93]
    b[21](b, b[58](actual, b[34].__class__) and b[59](actual) == 5, 'runtime ABI capture shape is unsupported')
    b[21](b, b[58](actual[0], b[54]) and b[58](actual[1], b[51]) and b[58](actual[2], b[51]) and b[58](actual[3], b[51]) and b[58](actual[4], b[54]), 'runtime ABI capture values are unsupported')
    if actual[0] != 'cpython':
        raise b[27]('UNSUPPORTED_RENDERER', 'unsupported interpreter implementation')
    if actual != b[92]:
        raise b[27]('TOOLCHAIN_IDENTITY_MISMATCH', 'renderer runtime ABI does not match exact cpython-3.12.0/cpython-312 contract')
    return {'implementation': actual[0], 'major': actual[1], 'minor': actual[2], 'micro': actual[3], 'cache_tag': actual[4]}

def _offset_ordinal_bound(b: tuple[Any, ...], instructions: list[Any], offset: int, allow_end: bool) -> int:
    for i, ins in b[57](instructions):
        if ins.offset == offset:
            return i
        if allow_end and ins.offset > offset:
            return i
    if allow_end:
        return b[59](instructions)
    raise b[27]('UNSUPPORTED_RENDERER', 'bytecode target offset is not a normalized instruction boundary')

def _normalize_value_bound(b: tuple[Any, ...], value: Any) -> dict[str, Any]:
    cls = value.__class__ if value is not None else None
    if value is None:
        return {'type': 'none'}
    if cls is b[46]:
        return {'type': 'bool', 'value': value}
    if cls is b[51]:
        return {'type': 'int', 'value': b[54](value)}
    if cls is b[50]:
        if not b[68](value):
            raise b[27]('UNSUPPORTED_RENDERER', 'non-finite persistent float is unsupported')
        return {'type': 'float64', 'bits_be_hex': b[125]('>d', value).hex()}
    if cls is b[54]:
        try:
            value.encode('utf-8')
        except b[44] as exc:
            raise b[27]('UNSUPPORTED_RENDERER', 'surrogate-bearing persistent string is unsupported') from exc
        return {'type': 'str', 'value': value}
    if cls is b[48]:
        return {'type': 'bytes', 'base64': b[63](value).decode('ascii')}
    if cls is b[34].__class__:
        return {'type': 'tuple', 'items': [b[110](b, item) for item in value]}
    if cls is b[36].__class__:
        items = [b[110](b, item) for item in value]
        items = b[61](items, key=lambda item: b[19](b, item))
        return {'type': 'frozenset', 'items': items}
    if cls is b[126]:
        return {'type': 'code', 'code': b[111](b, value)}
    raise b[27]('UNSUPPORTED_RENDERER', 'persistent bundle value has unsupported or mutable shape')

def _code_descriptor_bound(b: tuple[Any, ...], code: Any) -> dict[str, Any]:
    b[21](b, code.__class__ is b[126], 'code descriptor input is not CodeType')
    instructions = b[52](b[124](code, show_caches=False, adaptive=False))
    out_ins = []
    for ins in instructions:
        opcode = ins.opcode
        if opcode in b[95]:
            kind, operand = 'const', b[110](b, ins.argval)
        elif opcode in b[96]:
            name = b[54](ins.argval)
            modifier = ins.argrepr if ins.argrepr != name else ''
            kind, operand = 'name', {'name': name, 'argrepr': modifier}
        elif opcode in b[97]:
            kind, operand = 'local', b[54](ins.argval)
        elif opcode in b[98]:
            kind, operand = 'free', b[54](ins.argval)
        elif ins.opname == 'COMPARE_OP':
            kind, operand = 'compare', b[54](ins.argval)
        elif opcode in b[99] or opcode in b[100]:
            kind, operand = 'jump', b[118](b, instructions, ins.argval, False)
        elif ins.arg is None:
            kind, operand = 'none', None
        else:
            kind, operand = 'integer', ins.arg
        out_ins.append({'opname': ins.opname, 'operand_kind': kind, 'operand': operand})
    exceptions = []
    for entry in b[123](code).exception_entries:
        exceptions.append({'start_ordinal': b[118](b, instructions, entry.start, False), 'end_ordinal': b[118](b, instructions, entry.end, True), 'target_ordinal': b[118](b, instructions, entry.target, False), 'depth': entry.depth, 'lasti': entry.lasti})
    parameter_count = code.co_argcount + code.co_kwonlyargcount
    if code.co_flags & 4:
        parameter_count += 1
    if code.co_flags & 8:
        parameter_count += 1
    return {
        'name': code.co_name,
        'qualname': code.co_qualname,
        'argcount': code.co_argcount,
        'posonlyargcount': code.co_posonlyargcount,
        'kwonlyargcount': code.co_kwonlyargcount,
        'nlocals': code.co_nlocals,
        'stacksize': code.co_stacksize,
        'flags': code.co_flags,
        'parameter_names': b[52](code.co_varnames[:parameter_count]),
        'local_names': b[52](code.co_varnames),
        'global_names': b[52](code.co_names),
        'freevars': b[52](code.co_freevars),
        'cellvars': b[52](code.co_cellvars),
        'instructions': out_ins,
        'exception_table': exceptions,
    }

def _callable_parts_bound(b: tuple[Any, ...], fn: Any) -> dict[str, Any]:
    b[21](b, fn.__class__ is b[127], 'callable descriptor requires exact Python function')
    defaults = fn.__defaults__ or ()
    kwdefaults = fn.__kwdefaults__ or {}
    closure = fn.__closure__ or ()
    b[21](b, b[59](closure) == b[59](fn.__code__.co_freevars), 'function closure does not match co_freevars')
    return {
        'code': b[111](b, fn.__code__),
        'defaults': [b[110](b, value) for value in defaults],
        'kwdefaults': [{'name': name, 'value': b[110](b, kwdefaults[name])} for name in b[61](kwdefaults, key=lambda item: item.encode('utf-8'))],
        'closure': [{'name': fn.__code__.co_freevars[i], 'value': b[110](b, cell.cell_contents)} for i, cell in b[57](closure)],
    }

def _lookup_target_bound(b: tuple[Any, ...], target_id: str) -> Any:
    for member_id, slot in b[0]:
        if member_id == target_id:
            return b[slot]
    for spec in b[94]:
        if spec[0] == target_id:
            return b[spec[1]]
    raise b[27]('UNSUPPORTED_RENDERER', 'declared bundle target is missing')

def _member_id_for_object_bound(b: tuple[Any, ...], target: Any) -> str:
    found = []
    for member_id, slot in b[0]:
        if b[slot] is target:
            found.append(member_id)
    for spec in b[94]:
        if b[spec[1]] is target:
            found.append(spec[0])
    b[21](b, b[59](found) == 1, 'global dependency is missing or ambiguously registered')
    return found[0]

def _global_dependencies_bound(b: tuple[Any, ...], member_id: str, fn: Any) -> list[dict[str, str]]:
    names = b[53]()
    pending = [fn.__code__]
    while pending:
        code = pending.pop()
        for ins in b[124](code, show_caches=False, adaptive=False):
            if ins.opname in ('LOAD_GLOBAL', 'STORE_GLOBAL', 'DELETE_GLOBAL'):
                if ins.argval not in ('__name__', '__package__', '__loader__', '__spec__'):
                    names.add(ins.argval)
        for constant in code.co_consts:
            if constant.__class__ is b[126]:
                pending.append(constant)
    declared = None
    for declared_member, deps in b[133]:
        if declared_member == member_id:
            declared = deps
            break
    if declared is None:
        b[21](b, not names, 'registered post-resolution member has undeclared module-global dependency')
        return []
    declared_names = b[53]((item[0] for item in declared))
    b[21](b, names == declared_names and b[59](declared_names) == b[59](declared), 'bootstrap global dependency declaration does not match executable globals')
    out = []
    previous = None
    for name, target_id in declared:
        key = (name.encode('utf-8'), target_id.encode('utf-8'))
        b[21](b, previous is None or previous < key, 'bootstrap dependency declaration is not canonical or contains duplicates')
        previous = key
        b[121](b, target_id)
        out.append({'name': name, 'target': target_id})
    return out

def _function_descriptor_bound(b: tuple[Any, ...], member_id: str, fn: Any) -> dict[str, Any]:
    parts = b[112](b, fn)
    return {'id': member_id, 'kind': 'python_function', 'module': fn.__module__, 'qualname': fn.__qualname__, 'code': parts['code'], 'defaults': parts['defaults'], 'kwdefaults': parts['kwdefaults'], 'closure': parts['closure'], 'global_dependencies': b[117](b, member_id, fn)}

def _type_descriptor_bound(b: tuple[Any, ...], member_id: str, cls: Any) -> dict[str, Any]:
    layout = None
    for item in b[102]:
        if item[0] == member_id:
            layout = item
            break
    b[21](b, layout is not None, 'registered Python type has no frozen type layout')
    _, module, qualname, bases, methods, constants = layout
    b[21](b, cls.__module__ == module and cls.__qualname__ == qualname, 'registered Python type identity mismatch')
    if bases:
        b[21](b, b[59](cls.__bases__) == b[59](bases), 'registered Python type bases mismatch')
        for i, target_id in b[57](bases):
            b[21](b, cls.__bases__[i] is b[121](b, target_id), 'registered Python type base target mismatch')
    else:
        b[21](b, b[59](cls.__bases__) == 1 and cls.__bases__[0].__module__ == 'builtins' and cls.__bases__[0].__qualname__ == 'object', 'registered Python type implicit object base mismatch')
    method_ids = []
    for attr, target_id, kind in methods:
        target = b[121](b, target_id)
        current = cls.__dict__[attr]
        if kind == 'property':
            b[21](b, current.fget is target, 'registered property target mismatch')
        else:
            b[21](b, current is target, 'registered method target mismatch')
        method_ids.append(target_id)
    constant_ids = []
    for attr, target_id in constants:
        b[21](b, cls.__dict__[attr] == b[121](b, target_id), 'registered type constant mismatch')
        constant_ids.append(target_id)
    return {'id': member_id, 'kind': 'python_type', 'module': module, 'qualname': qualname, 'bases': b[52](bases), 'methods': method_ids, 'class_constants': constant_ids}

def _primitive_descriptor_bound(b: tuple[Any, ...], spec: tuple[Any, ...]) -> dict[str, Any]:
    primitive_id, slot, runtime_id, mode, public_module, public_qualname, actual_module, actual_qualname = spec
    obj = b[slot]
    if obj.__module__ != actual_module or obj.__qualname__ != actual_qualname:
        raise b[27]('TOOLCHAIN_IDENTITY_MISMATCH', 'runtime primitive identity does not match frozen captured reference')
    if mode == 'exact_abi_python_callable':
        if obj.__class__ is not b[127]:
            raise b[27]('TOOLCHAIN_IDENTITY_MISMATCH', 'runtime primitive reference kind mismatch')
        parts = b[112](b, obj)
        callable_descriptor = {'code': parts['code'], 'defaults': parts['defaults'], 'kwdefaults': parts['kwdefaults'], 'closure': parts['closure']}
    elif mode == 'exact_abi_builtin':
        if obj.__class__ is not b[55].__class__:
            raise b[27]('TOOLCHAIN_IDENTITY_MISMATCH', 'runtime primitive reference kind mismatch')
        callable_descriptor = None
    elif mode == 'exact_abi_type':
        if b[46].__class__ not in obj.__class__.__mro__:
            raise b[27]('TOOLCHAIN_IDENTITY_MISMATCH', 'runtime primitive reference kind mismatch')
        callable_descriptor = None
    else:
        raise b[27]('UNSUPPORTED_RENDERER', 'runtime primitive identity mode is unsupported')
    return {'id': primitive_id, 'kind': 'runtime_primitive', 'runtime_id': runtime_id, 'identity_mode': mode, 'module': public_module, 'qualname': public_qualname, 'callable_descriptor': callable_descriptor}

def _descriptor_members_bound(b: tuple[Any, ...]) -> list[dict[str, Any]]:
    out = []
    for member_id, slot in b[0]:
        value = b[slot]
        if member_id == 'member:registry' or member_id.startswith('member:constant:'):
            out.append({'id': member_id, 'kind': 'immutable_constant', 'value': b[110](b, value)})
        elif member_id.startswith('member:type:'):
            out.append(b[114](b, member_id, value))
        else:
            out.append(b[113](b, member_id, value))
    for spec in b[94]:
        out.append(b[115](b, spec))
    ids = [item['id'] for item in out]
    b[21](b, b[59](ids) == b[59](b[53](ids)), 'bundle descriptor member ids are duplicated')
    return b[61](out, key=lambda item: item['id'].encode('utf-8'))

def _describe_bundle_bound(b: tuple[Any, ...]) -> dict[str, Any]:
    runtime = b[120](b)
    members = b[116](b)
    return {'contract': b[90], 'scheme': b[89], 'runtime_abi': runtime, 'members': members}

def _derive_execution_binding_bound(b: tuple[Any, ...]) -> dict[str, Any]:
    descriptor = b[107](b)
    identity = b[22](b, b[101] + b[19](b, descriptor))
    return {'contract': b[88], 'scheme': b[89], 'runtime_abi': descriptor['runtime_abi'], 'identity_sha256': identity}

def _binding_shape_bound(b: tuple[Any, ...], value: Any) -> dict[str, Any]:
    b[21](b, b[58](value, b[40]) and b[53](value) == {'contract', 'scheme', 'runtime_abi', 'identity_sha256'}, 'renderer execution binding shape is invalid')
    b[21](b, value.get('contract') == b[88] and value.get('scheme') == b[89], 'renderer execution binding contract or scheme is unsupported')
    runtime = value.get('runtime_abi')
    b[21](b, b[58](runtime, b[40]) and b[53](runtime) == {'implementation', 'major', 'minor', 'micro', 'cache_tag'}, 'renderer execution binding runtime ABI shape is invalid')
    expected_runtime = {'implementation': b[92][0], 'major': b[92][1], 'minor': b[92][2], 'micro': b[92][3], 'cache_tag': b[92][4]}
    b[21](b, b[49](runtime) == expected_runtime, 'renderer execution binding runtime ABI is unsupported')
    identity = b[20](b, value.get('identity_sha256'))
    return {'contract': b[88], 'scheme': b[89], 'runtime_abi': expected_runtime, 'identity_sha256': identity}

def _compare_execution_binding_bound(b: tuple[Any, ...], expected: Mapping[str, Any], actual: Mapping[str, Any]) -> None:
    left = b[119](b, expected)
    right = b[119](b, actual)
    if b[19](b, left) != b[19](b, right):
        raise b[27]('TOOLCHAIN_IDENTITY_MISMATCH', 'renderer execution binding does not match independently derived bundle identity')

def _failure_bound(b: tuple[Any, ...], code: str, diagnostic: str) -> dict[str, Any]:
    return {'contract': b[32], 'code': code, 'stage': 'rendering', 'diagnostics': [diagnostic]}
