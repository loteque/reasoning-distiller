"""P9 pure deterministic renderer for canonical context packs.

Only the supplied pack and exact renderer profile are consumed. Plane identity is
structural, payloads are opaque framed JCS bytes, and bounds fail closed without
truncation, ranking, summarization, discovery, persistence, or state mutation.

The JCS/strict-JSON behavior used by the renderer is intentionally local to this
module so the exact renderer blob binds every repository-owned behavior-bearing
serialization dependency used by P9.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import math
from typing import Any, Mapping

RENDERER_CONTRACT = "reasoning-distiller-context-renderer/1"
RENDERER_PROFILE_CONTRACT = "reasoning-distiller-context-renderer-profile/1"
RENDERED_ACTIVATION_CONTRACT = "reasoning-distiller-context-rendered-activation/1"
FRAMING_CONTRACT = "reasoning-distiller-context-renderer-framing/1"
FAILURE_CONTRACT = "reasoning-distiller-context-pack-failure/1"
PACK_CONTRACTS = ("reasoning-distiller-context-pack/1", "reasoning-distiller-context-pack/2")
PLANE_ORDER = ("control", "knowledge", "operational_evidence")
_PLANE_KEYS = {"control": "control_plane", "knowledge": "knowledge_plane", "operational_evidence": "operational_evidence_plane"}
_PROFILE_KEYS = {"contract", "profile_id", "profile_version", "supported_pack_contracts", "pack_profile", "renderer_component", "framing", "limits"}
_PACK_KEYS = {"contract", "profile", "request", "source_registry", "control_plane", "knowledge_plane", "operational_evidence_plane", "inclusion_ledger", "toolchain", "identity", "eligibility"}
_DIGEST_MAGIC = b"reasoning-distiller-context-renderer-digest/1\x00"


@dataclass(frozen=True)
class RenderedActivationResult:
    activation: Mapping[str, Any] | None = None
    serialized_activation: bytes | None = None
    serialized_activation_sha256: str | None = None
    failure: Mapping[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.failure is None


@dataclass(frozen=True)
class RenderedActivationDecodeResult:
    pack: Mapping[str, Any] | None = None
    failure: Mapping[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.failure is None


class _RF(ValueError):
    def __init__(self, code: str, diagnostic: str):
        super().__init__(diagnostic)
        self.code, self.diagnostic = code, diagnostic


def render_context_pack(pack: Mapping[str, Any], profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationResult:
    """Render one canonical pack to provider-neutral activation bytes."""
    try:
        p = _profile(profile_raw, profile)
        pack_raw = _pack(pack, p)
        out: dict[str, Any] = {
            "contract": RENDERED_ACTIVATION_CONTRACT,
            "renderer_profile": {"profile_id": p["profile_id"], "profile_version": p["profile_version"], "raw_sha256": _sha(profile_raw)},
            "renderer_component": _component(p["renderer_component"]),
            "pack": _pack_summary(pack, pack_raw),
            "framing": deepcopy(dict(p["framing"])),
            "frames": _frames(pack),
        }
        out["identity"] = {"activation_identity_sha256": _domain("activation_identity", _jcs(out))}
        raw = _jcs(out)
        limit = p["limits"]["max_activation_bytes"]
        if len(raw) > limit:
            raise _RF("RENDER_LIMIT_EXCEEDED", f"rendering.max_activation_bytes exceeded: actual={len(raw)} limit={limit}")
        return RenderedActivationResult(out, raw, _sha(raw))
    except _RF as exc:
        return RenderedActivationResult(failure=_failure(exc.code, exc.diagnostic))
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        return RenderedActivationResult(failure=_failure("UNSUPPORTED_RENDERER", f"invalid renderer input: {type(exc).__name__}"))


def decode_rendered_activation(raw: bytes, profile_raw: bytes, profile: Mapping[str, Any]) -> RenderedActivationDecodeResult:
    """Verify and decode activation bytes to the exact framed canonical pack."""
    try:
        p = _profile(profile_raw, profile)
        _need(isinstance(raw, bytes), "rendered activation must be bytes")
        try:
            activation = _strict_json(raw)
        except Exception as exc:
            raise _RF("UNSUPPORTED_RENDERER", "rendered activation is not strict UTF-8 JSON") from exc
        _need(isinstance(activation, dict) and _jcs(activation) == raw, "rendered activation is not canonical JCS bytes")
        _header(activation, profile_raw, p)
        pack = _decode_frames(activation["frames"])
        pack_raw = _pack(pack, p)
        _need(activation["pack"] == _pack_summary(pack, pack_raw), "rendered pack summary does not bind decoded pack")
        limit = p["limits"]["max_activation_bytes"]
        if len(raw) > limit:
            raise _RF("RENDER_LIMIT_EXCEEDED", f"rendering.max_activation_bytes exceeded: actual={len(raw)} limit={limit}")
        return RenderedActivationDecodeResult(pack)
    except _RF as exc:
        return RenderedActivationDecodeResult(failure=_failure(exc.code, exc.diagnostic))
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        return RenderedActivationDecodeResult(failure=_failure("UNSUPPORTED_RENDERER", f"invalid rendered activation: {type(exc).__name__}"))


def _profile(raw: bytes, value: Mapping[str, Any]) -> dict[str, Any]:
    _need(isinstance(raw, bytes) and isinstance(value, Mapping), "renderer profile must be mapping plus exact raw bytes")
    try:
        parsed = _strict_json(raw)
    except Exception as exc:
        raise _RF("UNSUPPORTED_RENDERER", "renderer profile raw bytes must be strict UTF-8 JSON") from exc
    _need(parsed == dict(value), "renderer profile raw bytes do not bind profile object")
    _need(set(value) == _PROFILE_KEYS and value.get("contract") == RENDERER_PROFILE_CONTRACT, "unsupported renderer profile contract or fields")
    _need(all(isinstance(value.get(k), str) and value[k] for k in ("profile_id", "profile_version")), "renderer profile identity is invalid")
    supported = value.get("supported_pack_contracts")
    _need(isinstance(supported, list) and supported and len(supported) == len(set(supported)) and all(x in PACK_CONTRACTS for x in supported), "supported pack contracts are invalid")
    _need(supported == [x for x in PACK_CONTRACTS if x in supported], "supported pack contracts are not canonical order")
    _profile_id(value.get("pack_profile")); c = _component(value.get("renderer_component"))
    _need(c["role"] == "renderer" and c["contract"] == RENDERER_CONTRACT, "renderer component does not bind renderer/1")
    f = value.get("framing")
    _need(isinstance(f, Mapping) and set(f) == {"contract", "serializer", "text_encoding", "item_encoding", "plane_order"}, "renderer framing is invalid")
    _need(f.get("contract") == FRAMING_CONTRACT and f.get("serializer") == "jcs/1" and f.get("text_encoding") == "utf-8" and f.get("item_encoding") == "base64" and f.get("plane_order") == list(PLANE_ORDER), "unsupported renderer framing")
    limits = value.get("limits"); maximum = limits.get("max_activation_bytes") if isinstance(limits, Mapping) else None
    _need(isinstance(limits, Mapping) and set(limits) == {"max_activation_bytes"} and isinstance(maximum, int) and not isinstance(maximum, bool) and maximum > 0, "renderer limit is invalid")
    return deepcopy(dict(value))


def _pack(value: Mapping[str, Any], profile: Mapping[str, Any]) -> bytes:
    _need(isinstance(value, Mapping), "pack must be a mapping")
    keys = set(value); required = _PACK_KEYS - {"eligibility"}
    _need(not (keys - _PACK_KEYS) and required.issubset(keys), "pack fields are not supported")
    _need(value.get("contract") in PACK_CONTRACTS and value["contract"] in profile["supported_pack_contracts"], "pack contract is not supported")
    _need(_profile_id(value.get("profile")) == _profile_id(profile.get("pack_profile")), "renderer profile does not bind pack profile")
    _request_id(value.get("request"))
    identity = value.get("identity"); _need(isinstance(identity, Mapping) and "pack_identity_sha256" in identity, "pack identity is missing"); _norm(identity["pack_identity_sha256"])
    for plane in PLANE_ORDER:
        box = value.get(_PLANE_KEYS[plane]); _need(isinstance(box, Mapping) and set(box) == {"items"} and isinstance(box["items"], list), f"{plane} plane is invalid")
    tool = value.get("toolchain"); comps = tool.get("components") if isinstance(tool, Mapping) else None
    _need(isinstance(tool, Mapping) and set(tool) == {"components"} and isinstance(comps, list), "pack toolchain is invalid")
    jcs = [c for c in comps if isinstance(c, Mapping) and c.get("role") == "jcs_serializer"]
    _need(len(jcs) == 1 and jcs[0].get("contract") == "jcs/1", "pack does not bind exactly one jcs/1 serializer")
    try:
        return _jcs(deepcopy(dict(value)))
    except Exception as exc:
        raise _RF("UNSUPPORTED_RENDERER", "pack is not canonical-JCS representable") from exc


def _frames(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    meta = deepcopy(dict(pack))
    for key in _PLANE_KEYS.values(): meta.pop(key)
    out = [_frame(0, "metadata", meta)]
    n = 1
    for plane in PLANE_ORDER:
        for i, item in enumerate(pack[_PLANE_KEYS[plane]]["items"]):
            out.append(_frame(n, "plane_item", item, plane, i)); n += 1
    return out


def _frame(n: int, kind: str, payload: Any, plane: str | None = None, item: int | None = None) -> dict[str, Any]:
    raw = _jcs(deepcopy(payload))
    out = {"frame_index": n, "kind": kind, "encoding": "base64", "raw_sha256": _sha(raw), "data": base64.b64encode(raw).decode("ascii")}
    if plane is not None: out["plane"] = plane
    if item is not None: out["item_index"] = item
    return out


def _header(a: Mapping[str, Any], profile_raw: bytes, p: Mapping[str, Any]) -> None:
    _need(set(a) == {"contract", "renderer_profile", "renderer_component", "pack", "framing", "frames", "identity"} and a.get("contract") == RENDERED_ACTIVATION_CONTRACT, "rendered activation header is invalid")
    _need(a.get("renderer_profile") == {"profile_id": p["profile_id"], "profile_version": p["profile_version"], "raw_sha256": _sha(profile_raw)}, "renderer profile identity mismatch")
    _need(a.get("renderer_component") == _component(p["renderer_component"]), "renderer component identity mismatch")
    _need(a.get("framing") == dict(p["framing"]) and isinstance(a.get("frames"), list) and isinstance(a.get("pack"), Mapping), "rendered activation framing is invalid")
    ident = a.get("identity"); _need(isinstance(ident, Mapping) and set(ident) == {"activation_identity_sha256"}, "activation identity is invalid")
    pre = deepcopy(dict(a)); pre.pop("identity")
    _need(_norm(ident["activation_identity_sha256"]) == _domain("activation_identity", _jcs(pre)), "activation identity mismatch")


def _decode_frames(frames: list[Any]) -> dict[str, Any]:
    _need(bool(frames), "metadata frame is missing"); decoded = []
    for n, f in enumerate(frames):
        _need(isinstance(f, Mapping) and f.get("frame_index") == n, "rendered frame order is invalid")
        raw = _frame_raw(f)
        try: payload = _strict_json(raw)
        except Exception as exc: raise _RF("UNSUPPORTED_RENDERER", "frame payload is not strict JSON") from exc
        _need(_jcs(payload) == raw, "frame payload is not canonical JCS"); decoded.append((f, payload))
    first, meta = decoded[0]
    _need(first.get("kind") == "metadata" and set(first) == {"frame_index", "kind", "encoding", "raw_sha256", "data"} and isinstance(meta, dict) and not any(k in meta for k in _PLANE_KEYS.values()), "metadata frame is invalid")
    pack = deepcopy(meta)
    for plane in PLANE_ORDER: pack[_PLANE_KEYS[plane]] = {"items": []}
    rank = 0; next_item = {p: 0 for p in PLANE_ORDER}
    fields = {"frame_index", "kind", "plane", "item_index", "encoding", "raw_sha256", "data"}
    for f, payload in decoded[1:]:
        _need(set(f) == fields and f.get("kind") == "plane_item" and f.get("plane") in PLANE_ORDER, "plane frame is invalid")
        plane = f["plane"]; r = PLANE_ORDER.index(plane)
        _need(r >= rank and f.get("item_index") == next_item[plane], "rendered plane/item order is invalid")
        rank = r; next_item[plane] += 1; pack[_PLANE_KEYS[plane]]["items"].append(payload)
    return pack


def _frame_raw(f: Mapping[str, Any]) -> bytes:
    _need(f.get("encoding") == "base64" and isinstance(f.get("data"), str), "unsupported frame encoding")
    try: raw = base64.b64decode(f["data"].encode("ascii"), validate=True)
    except Exception as exc: raise _RF("UNSUPPORTED_RENDERER", "invalid frame base64") from exc
    _need(_norm(f.get("raw_sha256")) == _sha(raw), "frame digest mismatch"); return raw


def _pack_summary(pack: Mapping[str, Any], raw: bytes) -> dict[str, Any]:
    return {"contract": pack["contract"], "profile": _profile_id(pack["profile"]), "request": _request_id(pack["request"]), "pack_identity_sha256": _norm(pack["identity"]["pack_identity_sha256"]), "serialized_pack_sha256": _sha(raw)}


def _profile_id(v: Any) -> dict[str, str]:
    _need(isinstance(v, Mapping) and set(v) == {"profile_id", "profile_version", "raw_sha256"} and isinstance(v.get("profile_id"), str) and bool(v["profile_id"]) and isinstance(v.get("profile_version"), str) and bool(v["profile_version"]), "profile identity is invalid")
    return {"profile_id": v["profile_id"], "profile_version": v["profile_version"], "raw_sha256": _norm(v["raw_sha256"])}


def _request_id(v: Any) -> dict[str, str]:
    _need(isinstance(v, Mapping) and set(v) == {"request_id", "raw_sha256"} and isinstance(v.get("request_id"), str) and bool(v["request_id"]), "request identity is invalid")
    return {"request_id": v["request_id"], "raw_sha256": _norm(v["raw_sha256"])}


def _component(v: Any) -> dict[str, str]:
    keys = {"role", "contract", "immutable_identity", "raw_sha256"}; _need(isinstance(v, Mapping) and set(v) == keys and all(isinstance(v.get(k), str) and v[k] for k in ("role", "contract", "immutable_identity")), "renderer component is invalid")
    imm = v["immutable_identity"]; _need(imm.startswith("git-blob:") and len(imm) == 49 and all(c in "0123456789abcdef" for c in imm[9:]), "renderer component immutable identity is invalid")
    return {"role": v["role"], "contract": v["contract"], "immutable_identity": imm, "raw_sha256": _norm(v["raw_sha256"])}


def _strict_json(raw: bytes) -> Any:
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate JSON member")
            out[key] = value
        return out

    def bad(value):
        raise ValueError(value)

    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad)


def _jcs_string(value: str) -> bytes:
    out = bytearray(b'"')
    escapes = {8: b"\\b", 9: b"\\t", 10: b"\\n", 12: b"\\f", 13: b"\\r", 34: b'\\"', 92: b"\\\\"}
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError from exc
    for ch in value:
        cp = ord(ch)
        out.extend(escapes[cp] if cp in escapes else (f"\\u{cp:04x}".encode() if cp <= 31 else ch.encode("utf-8")))
    return bytes(out + b'"')


def _jcs_float(value: float) -> bytes:
    if not math.isfinite(value):
        raise ValueError
    if value == 0:
        return b"0"
    if value < 0:
        return b"-" + _jcs_float(-value)
    text = str(value); exp = 0; exp_text = ""
    if "e" in text:
        mantissa, raw = text.split("e", 1); exp = int(raw); exp_text = ("e+" if exp >= 0 else "e-") + str(abs(exp))
    else:
        mantissa = text
    if "." in mantissa:
        first, last = mantissa.split(".", 1); dot = "."
    else:
        first, last, dot = mantissa, "", ""
    if last == "0":
        last, dot = "", ""
    if 0 < exp < 21:
        first += last; last = dot = exp_text = ""; missing = exp - len(first)
        while missing >= 0:
            first += "0"; missing -= 1
    elif -7 < exp < 0:
        last = first + last; first, dot, exp_text, missing = "0", ".", "", exp
        while missing < -1:
            last = "0" + last; missing += 1
    return f"{first}{dot}{last}{exp_text}".encode()


def _jcs(value: Any) -> bytes:
    sink = BytesIO()

    def emit(obj):
        if obj is None:
            sink.write(b"null")
        elif obj is True:
            sink.write(b"true")
        elif obj is False:
            sink.write(b"false")
        elif isinstance(obj, str):
            sink.write(_jcs_string(obj))
        elif isinstance(obj, int):
            if not -(2**53 - 1) <= obj <= 2**53 - 1:
                raise ValueError
            sink.write(str(obj).encode())
        elif isinstance(obj, float):
            sink.write(_jcs_float(obj))
        elif isinstance(obj, list):
            sink.write(b"[")
            for i, item in enumerate(obj):
                if i:
                    sink.write(b",")
                emit(item)
            sink.write(b"]")
        elif isinstance(obj, dict):
            if any(not isinstance(key, str) for key in obj):
                raise ValueError
            try:
                items = sorted(obj.items(), key=lambda item: item[0].encode("utf-16be"))
            except UnicodeEncodeError as exc:
                raise ValueError from exc
            sink.write(b"{")
            for i, (key, item) in enumerate(items):
                if i:
                    sink.write(b",")
                sink.write(_jcs_string(key)); sink.write(b":"); emit(item)
            sink.write(b"}")
        else:
            raise ValueError

    emit(value)
    return sink.getvalue()


def _norm(v: Any) -> str:
    _need(isinstance(v, str) and len(v) == 71 and v.startswith("sha256:") and all(c in "0123456789abcdefABCDEF" for c in v[7:]), "invalid sha256 identity")
    return "sha256:" + v[7:].lower()


def _need(ok: bool, message: str) -> None:
    if not ok: raise _RF("UNSUPPORTED_RENDERER", message)


def _sha(raw: bytes) -> str: return "sha256:" + hashlib.sha256(raw).hexdigest()
def _domain(domain: str, raw: bytes) -> str: return _sha(_DIGEST_MAGIC + domain.encode("ascii") + b"\x00" + raw)
def _failure(code: str, diagnostic: str) -> dict[str, Any]: return {"contract": FAILURE_CONTRACT, "code": code, "stage": "rendering", "diagnostics": [diagnostic]}
