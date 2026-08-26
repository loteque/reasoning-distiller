"""P4 deterministic COVE/1 adapter for context-packaging PEMS/2.

This adapter exposes only the frozen ``cove/1 | pems/2 | jcs/1`` tuple.  It
reuses the exact package-owned COVE structural encoder/decoder from the frozen
P1 evidence artifact and uses the package's already-frozen jcs/1 serializer.
It performs no projection, pack construction, persistence, rendering,
admission, reconciliation, authorization, activation, or canonical mutation.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from .pems_projection import _jcs, _strict_json

ROOT = Path(__file__).resolve().parents[1]
FROZEN_COVE_SOURCE = ROOT / "admission/apply_admission_transaction.py"
FROZEN_COVE_SOURCE_GIT_BLOB = "0f0117a7770f1928e41bd76082d9a572102e823a"
COVE_SEMANTIC = "cove/1"
PEMS_SEMANTIC = "pems/2"
SERIALIZER = "jcs/1"
_REQUIRED_MEMBERS = frozenset({"c", "p", "s", "d", "h", "x"})
_FROZEN_MODULE: ModuleType | None = None


class CoveAdapterError(ValueError):
    """The value cannot be represented by the frozen P4 COVE adapter."""


@dataclass(frozen=True)
class CoveSemanticTuple:
    cove: str
    pems: str
    serializer: str


SUPPORTED_TUPLES = (CoveSemanticTuple(COVE_SEMANTIC, PEMS_SEMANTIC, SERIALIZER),)


def encode_cove_pems(document: Mapping[str, Any]) -> bytes:
    """Encode one PEMS/2 object as canonical COVE/1 jcs/1 bytes.

    Success includes an exact structural decode check and a second encoding
    check.  The input object is never normalized or rewritten by this adapter.
    """
    if not isinstance(document, dict) or document.get("semantic") != PEMS_SEMANTIC:
        raise CoveAdapterError("P4 COVE adapter requires a PEMS/2 object")
    frozen = _frozen_cove_module()
    original = deepcopy(document)
    try:
        envelope = frozen.encode_cove(original)
        _validate_envelope(envelope)
        decoded = _decode_envelope(envelope, frozen)
        if decoded != document:
            raise CoveAdapterError("COVE decode does not exactly reproduce PEMS")
        first = _jcs(envelope)
        repeated = frozen.encode_cove(deepcopy(decoded))
        _validate_envelope(repeated)
        if _decode_envelope(repeated, frozen) != decoded:
            raise CoveAdapterError("repeated COVE decode does not exactly reproduce PEMS")
        if _jcs(repeated) != first:
            raise CoveAdapterError("repeated COVE encoding is not byte-identical")
        return first
    except CoveAdapterError:
        raise
    except (IndexError, KeyError, TypeError, UnicodeError, ValueError) as exc:
        raise CoveAdapterError("COVE encoding failed") from exc


def decode_cove_pems(raw: bytes) -> Mapping[str, Any]:
    """Decode canonical bytes for the one supported COVE/PEMS/JCS tuple.

    Alternate tuple spellings, non-canonical bytes, and structurally different
    encodings of the same PEMS object fail closed.  Successful decode is checked
    by exact deterministic re-encoding.
    """
    if not isinstance(raw, bytes):
        raise CoveAdapterError("COVE input must be bytes")
    frozen = _frozen_cove_module()
    try:
        envelope = _strict_json(raw)
        _validate_envelope(envelope)
        decoded = _decode_envelope(envelope, frozen)
        if not isinstance(decoded, dict) or decoded.get("semantic") != PEMS_SEMANTIC:
            raise CoveAdapterError("COVE payload is not a PEMS/2 object")
        repeated = frozen.encode_cove(deepcopy(decoded))
        _validate_envelope(repeated)
        if repeated != envelope:
            raise CoveAdapterError("COVE structure is not the deterministic package encoding")
        canonical = _jcs(repeated)
        if canonical != raw:
            raise CoveAdapterError("COVE bytes are not canonical jcs/1")
        if _decode_envelope(repeated, frozen) != decoded:
            raise CoveAdapterError("COVE repeated round trip changed PEMS semantics")
        return decoded
    except CoveAdapterError:
        raise
    except (IndexError, KeyError, TypeError, UnicodeError, ValueError) as exc:
        raise CoveAdapterError("COVE decoding failed") from exc


def _validate_envelope(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != _REQUIRED_MEMBERS:
        raise CoveAdapterError("COVE envelope shape is unsupported")
    actual = CoveSemanticTuple(value.get("c"), value.get("p"), value.get("s"))
    if actual not in SUPPORTED_TUPLES:
        raise CoveAdapterError("unsupported COVE semantic tuple")
    dictionary, shapes = value.get("d"), value.get("h")
    if not isinstance(dictionary, list) or any(not isinstance(item, str) for item in dictionary):
        raise CoveAdapterError("COVE dictionary is invalid")
    if not isinstance(shapes, list) or any(
        not isinstance(shape, list) or any(not isinstance(index, int) or isinstance(index, bool) for index in shape)
        for shape in shapes
    ):
        raise CoveAdapterError("COVE shapes are invalid")


def _decode_envelope(value: Mapping[str, Any], frozen: ModuleType) -> Mapping[str, Any]:
    decoded = frozen._decode(value["x"], value["d"], value["h"])
    if not isinstance(decoded, dict):
        raise CoveAdapterError("COVE payload did not decode to an object")
    return decoded


def _frozen_cove_module() -> ModuleType:
    global _FROZEN_MODULE
    if _FROZEN_MODULE is not None:
        return _FROZEN_MODULE
    raw = FROZEN_COVE_SOURCE.read_bytes()
    if _git_blob_sha(raw) != FROZEN_COVE_SOURCE_GIT_BLOB:
        raise CoveAdapterError("frozen package-owned COVE source identity mismatch")
    spec = importlib.util.spec_from_file_location("context_packaging_p4_frozen_cove", FROZEN_COVE_SOURCE)
    if spec is None or spec.loader is None:
        raise CoveAdapterError("frozen package-owned COVE source is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if (
        getattr(module, "COVE", None) != COVE_SEMANTIC
        or getattr(module, "PROFILE", None) != PEMS_SEMANTIC
        or getattr(module, "SERIALIZER", None) != SERIALIZER
        or not callable(getattr(module, "encode_cove", None))
        or not callable(getattr(module, "_decode", None))
    ):
        raise CoveAdapterError("frozen package-owned COVE behavior does not match P4 tuple")
    _FROZEN_MODULE = module
    return module


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
