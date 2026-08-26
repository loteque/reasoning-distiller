"""P1c deterministic context-pack reference helpers.

This module is test-only conformance machinery for the P1c bytes/digests/toolchain
gate. It intentionally does not resolve sources, implement PEMS closure, decide
profile eligibility, persist packs, render activations, or mutate governed state.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
from io import BytesIO
from typing import Any

MAGIC = b"reasoning-distiller-context-digest/1\x00"
SOURCE_CLASS_RANK = {
    "repository_control": 0,
    "package_control": 1,
    "canonical_state": 2,
    "operational_evidence": 3,
}
PLANE_RANK = {"control": 0, "knowledge": 1, "operational_evidence": 2}
CAUSE_RANK = {"profile_slot": 0, "request_selector": 1, "pems_closure": 2}
TOOLCHAIN_RANK = {
    "pems_schema": 0,
    "pems_validator": 1,
    "closure_descriptor": 2,
    "cove_adapter": 3,
    "jcs_serializer": 4,
    "pack_builder": 5,
}

class JCSError(ValueError):
    pass

def _jcs_string(value: str) -> bytes:
    out = bytearray(b'"')
    escapes = {
        0x08: b"\\b",
        0x09: b"\\t",
        0x0A: b"\\n",
        0x0C: b"\\f",
        0x0D: b"\\r",
        0x22: b'\\"',
        0x5C: b"\\\\",
    }
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise JCSError("JCS strings must contain valid Unicode scalar values") from exc
    for ch in value:
        cp = ord(ch)
        if cp in escapes:
            out.extend(escapes[cp])
        elif cp <= 0x1F:
            out.extend(f"\\u{cp:04x}".encode("ascii"))
        else:
            out.extend(ch.encode("utf-8"))
    out.extend(b'"')
    return bytes(out)

def _jcs_float(value: float) -> bytes:
    if not math.isfinite(value):
        raise JCSError("NaN and Infinity are not permitted by JCS")
    if value == 0:
        return b"0"
    if value < 0:
        return b"-" + _jcs_float(-value)

    # CPython's float conversion supplies the shortest round-trippable decimal.
    # The normalization below applies ECMAScript/JCS fixed-vs-exponent thresholds.
    text = str(value)
    exp_text = ""
    exp_value = 0
    if "e" in text:
        mantissa, raw_exp = text.split("e", 1)
        exp_value = int(raw_exp)
        exp_text = ("e+" if exp_value >= 0 else "e-") + str(abs(exp_value))
    else:
        mantissa = text

    if "." in mantissa:
        first, last = mantissa.split(".", 1)
        dot = "."
    else:
        first, last, dot = mantissa, "", ""

    if last == "0":
        last = ""
        dot = ""

    if 0 < exp_value < 21:
        first = first + last
        last = ""
        dot = ""
        exp_text = ""
        missing = exp_value - len(first)
        while missing >= 0:
            first += "0"
            missing -= 1
    elif -7 < exp_value < 0:
        last = first + last
        first = "0"
        dot = "."
        exp_text = ""
        missing = exp_value
        while missing < -1:
            last = "0" + last
            missing += 1

    return f"{first}{dot}{last}{exp_text}".encode("ascii")

def jcs_bytes(value: Any) -> bytes:
    sink = BytesIO()

    def emit(obj: Any) -> None:
        if obj is None:
            sink.write(b"null")
        elif obj is True:
            sink.write(b"true")
        elif obj is False:
            sink.write(b"false")
        elif isinstance(obj, str):
            sink.write(_jcs_string(obj))
        elif isinstance(obj, int):
            if obj < -(2**53 - 1) or obj > 2**53 - 1:
                raise JCSError("integer outside interoperable I-JSON safe range")
            sink.write(str(obj).encode("ascii"))
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
            if any(not isinstance(k, str) for k in obj):
                raise JCSError("JCS object keys must be strings")
            try:
                items = sorted(obj.items(), key=lambda kv: kv[0].encode("utf-16be"))
            except UnicodeEncodeError as exc:
                raise JCSError("JCS object keys must contain valid Unicode scalar values") from exc
            sink.write(b"{")
            for i, (key, item) in enumerate(items):
                if i:
                    sink.write(b",")
                sink.write(_jcs_string(key))
                sink.write(b":")
                emit(item)
            sink.write(b"}")
        else:
            raise JCSError(f"unsupported JCS type: {type(obj)!r}")

    emit(value)
    return sink.getvalue()

def strict_json_object(raw: bytes) -> Any:
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"duplicate JSON member: {key}")
            result[key] = value
        return result

    def bad_constant(value):
        raise ValueError(f"non-finite JSON number: {value}")

    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=pairs,
        parse_constant=bad_constant,
    )

def raw_sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()

def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")

def b64decode(text: str) -> bytes:
    if not isinstance(text, str) or any(ord(c) > 127 for c in text):
        raise ValueError("base64 must be ASCII")
    try:
        raw = base64.b64decode(text, validate=True)
    except Exception as exc:
        raise ValueError("invalid base64") from exc
    if b64encode(raw) != text:
        raise ValueError("non-canonical base64")
    return raw

def digest_preimage(domain: str, body: bytes) -> bytes:
    encoded = domain.encode("ascii")
    if len(encoded) > 0xFFFF:
        raise ValueError("domain too long")
    return MAGIC + len(encoded).to_bytes(2, "big") + encoded + len(body).to_bytes(8, "big") + body

def domain_sha256(domain: str, value: Any) -> str:
    body = value if isinstance(value, bytes) else jcs_bytes(value)
    return raw_sha256(digest_preimage(domain, body))

def normalize_sha256(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError("invalid sha256 identity")
    digest = value[7:]
    if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
        raise ValueError("invalid sha256 identity")
    return "sha256:" + digest.lower()

def canonical_binding(binding: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(binding)
    if "standing_evidence" in out:
        normalized = []
        for evidence in out["standing_evidence"]:
            evidence = copy.deepcopy(evidence)
            evidence["raw_sha256"] = normalize_sha256(evidence["raw_sha256"])
            normalized.append(evidence)
        unique = {jcs_bytes(e): e for e in normalized}
        out["standing_evidence"] = [unique[key] for key in sorted(unique)]
    return out

def canonical_snapshot_ref(binding: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "source_class", "logical_namespace", "logical_source_id", "project_id",
        "backend_type", "backend_contract", "backend_config_identity",
        "immutable_snapshot_id", "pems_semantic", "serializer", "pems_sha256",
        "standing_evidence", "cove",
    )
    return canonical_binding({k: binding[k] for k in keys if k in binding})

def canonicalize_pack(pack: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(pack)
    for binding in out["source_registry"]:
        if binding.get("source_class") == "canonical_state":
            binding.update(canonical_binding(binding))
    out["source_registry"].sort(
        key=lambda b: (SOURCE_CLASS_RANK[b["source_class"]], jcs_bytes(b))
    )
    out["control_plane"]["items"].sort(key=lambda x: jcs_bytes(x["source_ref"]))
    for item in out["knowledge_plane"]["items"]:
        item["canonical_snapshot_ref"] = canonical_binding(item["canonical_snapshot_ref"])
    out["knowledge_plane"]["items"].sort(
        key=lambda x: jcs_bytes(x["canonical_snapshot_ref"])
    )
    out["operational_evidence_plane"]["items"].sort(
        key=lambda x: jcs_bytes(x["source_ref"])
    )
    for entry in out["inclusion_ledger"]:
        if entry["plane"] == "knowledge" and "source_ref" in entry["subject"]:
            entry["subject"]["source_ref"] = canonical_binding(entry["subject"]["source_ref"])
        entry["causes"].sort(
            key=lambda c: (CAUSE_RANK[c["kind"]], c["cause_id"].encode("utf-8"))
        )
    out["inclusion_ledger"].sort(
        key=lambda e: (PLANE_RANK[e["plane"]], jcs_bytes(e["subject"]))
    )
    out["toolchain"]["components"].sort(
        key=lambda c: (TOOLCHAIN_RANK[c["role"]], jcs_bytes(c))
    )
    return out

def canonical_binding_digests(pack: dict[str, Any]) -> list[str]:
    by_ref = {}
    for binding in pack["source_registry"]:
        if binding["source_class"] == "canonical_state":
            by_ref[jcs_bytes(canonical_snapshot_ref(binding))] = domain_sha256(
                "canonical-state-binding", canonical_binding(binding)
            )
    result = []
    for item in pack["knowledge_plane"]["items"]:
        key = jcs_bytes(canonical_binding(item["canonical_snapshot_ref"]))
        if key not in by_ref:
            raise ValueError("knowledge item has no exact canonical binding")
        result.append(by_ref[key])
    return result

def selected_pems_view(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract": "reasoning-distiller-selected-pems-projection/1",
        "items": [
            {
                "canonical_snapshot_ref": x["canonical_snapshot_ref"],
                "semantic": x["semantic"],
                "serializer": x["serializer"],
                "pems": x["pems"],
            }
            for x in pack["knowledge_plane"]["items"]
        ],
    }

def cove_view(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract": "reasoning-distiller-cove-payload-set/1",
        "items": [
            {
                "canonical_snapshot_ref": x["canonical_snapshot_ref"],
                "cove_payload": x["cove_payload"],
            }
            for x in pack["knowledge_plane"]["items"]
            if "cove_payload" in x
        ],
    }

def manifest_view(pack: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(pack)
    out.pop("identity", None)
    for item in out["control_plane"]["items"]:
        item["payload"].pop("data", None)
    for item in out["knowledge_plane"]["items"]:
        item.pop("pems", None)
        if "cove_payload" in item:
            item["cove_payload"].pop("data", None)
    for item in out["operational_evidence_plane"]["items"]:
        item["payload"].pop("data", None)
    return out

def payload_view(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract": "reasoning-distiller-context-pack-payload-set/1",
        "control": [
            {"source_ref": x["source_ref"], "payload": x["payload"]}
            for x in pack["control_plane"]["items"]
        ],
        "knowledge": [
            {
                "canonical_snapshot_ref": x["canonical_snapshot_ref"],
                "pems": x["pems"],
                **(
                    {"cove_payload": x["cove_payload"]}
                    if "cove_payload" in x
                    else {}
                ),
            }
            for x in pack["knowledge_plane"]["items"]
        ],
        "operational_evidence": [
            {"source_ref": x["source_ref"], "payload": x["payload"]}
            for x in pack["operational_evidence_plane"]["items"]
        ],
    }

def bind_json_document(raw: bytes, validated_object: dict[str, Any], kind: str) -> str:
    parsed = strict_json_object(raw)
    if parsed != validated_object:
        raise ValueError(f"{kind} raw bytes do not parse to the validated P1b object")
    return raw_sha256(raw)

def build_identity(
    profile_raw: bytes,
    profile: dict[str, Any],
    request_raw: bytes,
    request: dict[str, Any],
    pack: dict[str, Any],
):
    profile_raw_sha = bind_json_document(profile_raw, profile, "profile")
    request_raw_sha = bind_json_document(request_raw, request, "request")
    if normalize_sha256(request["profile"]["raw_sha256"]) != profile_raw_sha:
        raise ValueError("request profile raw_sha256 does not bind the exact profile bytes")
    if normalize_sha256(pack["profile"]["raw_sha256"]) != profile_raw_sha:
        raise ValueError("pack profile raw_sha256 does not bind the exact profile bytes")
    if normalize_sha256(pack["request"]["raw_sha256"]) != request_raw_sha:
        raise ValueError("pack request raw_sha256 does not bind the exact request bytes")

    pack = canonicalize_pack(pack)
    ident = {
        "profile_sha256": domain_sha256("context-profile", profile),
        "request_sha256": domain_sha256("context-pack-request", request),
        "canonical_state_binding_sha256s": canonical_binding_digests(pack),
        "selected_pems_sha256": domain_sha256(
            "selected-pems-projection", selected_pems_view(pack)
        ),
    }
    cove = cove_view(pack)
    if cove["items"]:
        ident["cove_payload_sha256"] = domain_sha256("cove-payload-set", cove)
    ident["manifest_sha256"] = domain_sha256(
        "context-pack-manifest", manifest_view(pack)
    )
    ident["payload_set_sha256"] = domain_sha256(
        "context-pack-payload-set", payload_view(pack)
    )
    preimage = {
        "contract": "reasoning-distiller-context-pack-identity-preimage/1",
        **ident,
    }
    ident["pack_identity_sha256"] = domain_sha256("context-pack-identity", preimage)
    return pack, ident

def validate_toolchain(profile: dict[str, Any], pack: dict[str, Any]) -> bool:
    components = pack["toolchain"]["components"]
    roles = [c["role"] for c in components]
    if len(roles) != len(set(roles)):
        return False
    required = {
        "pems_schema",
        "pems_validator",
        "closure_descriptor",
        "jcs_serializer",
        "pack_builder",
    }
    if any("cove_payload" in x for x in pack["knowledge_plane"]["items"]):
        required.add("cove_adapter")
    if set(roles) != required:
        return False
    by_role = {c["role"]: c for c in components}
    closure = profile["knowledge"]["closure_descriptor"]
    actual = by_role["closure_descriptor"]
    return (
        actual["contract"] == closure["contract"]
        and actual["immutable_identity"] == closure["immutable_snapshot_id"]
        and actual["raw_sha256"] == closure["raw_sha256"]
        and by_role["jcs_serializer"]["contract"] == "jcs/1"
    )
