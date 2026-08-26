"""P3 exact PEMS/2 projection for deterministic context packaging.

Consumes explicit P1 request/profile semantics plus P2 ``ResolvedSource`` values,
applies the frozen package-owned P1d closure rules, validates source and projected
PEMS/2, and enforces P3 projection limits. It performs no source discovery,
COVE encoding, pack building/persistence, rendering, canonical mutation,
admission, reconciliation, authorization, or activation.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib, heapq, importlib.util, json, math
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, ValidationError
from .source_resolver import ResolvedSource, _snapshot_key

FAILURE = "reasoning-distiller-context-pack-failure/1"
DESCRIPTOR = "reasoning-distiller-pems2-closure-descriptor/1"
ROOT = Path(__file__).resolve().parents[1]
DESC_PATH = ROOT / "protocols/rgp/pems2-context-closure-v1.json"
SCHEMA_PATH = ROOT / "backends/pems-cove/pems-v2.schema.json"
VALIDATOR_PATH = ROOT / "backends/pems-cove/validate_pems2_contract.py"
MISSING = object()
RANK = {"record": 0, "relation": 1}


@dataclass(frozen=True)
class ProjectionCause:
    namespace: str
    semantic_id: str
    kind: str
    cause_id: str


@dataclass(frozen=True)
class ProjectedKnowledge:
    canonical_snapshot_ref: Mapping[str, Any]
    pems: Mapping[str, Any]
    causes: tuple[ProjectionCause, ...]


@dataclass(frozen=True)
class PemsProjectionResult:
    items: tuple[ProjectedKnowledge, ...] = ()
    failure: Mapping[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.failure is None


def project_pems(request, profile, resolved_sources) -> PemsProjectionResult:
    """Return exact closed PEMS projections or one frozen fail-closed result.

    Explicit selectors and descriptor root rules have depth zero; each closure
    edge adds one. Record/relation/byte limits are cumulative across snapshots.
    ``max_depth`` is per snapshot. Required closure is never truncated.
    """
    failure = _preflight(request, profile, resolved_sources)
    if failure:
        return PemsProjectionResult(failure=failure)
    try:
        desc, schema_v, semantic_v = _toolchain(profile["knowledge"]["closure_descriptor"])
    except Exception:
        return PemsProjectionResult(failure=_fail(
            "TOOLCHAIN_IDENTITY_MISMATCH", "toolchain",
            diag="bound PEMS projection toolchain identity mismatch"))

    limits = profile["limits"]["projection"]
    selectors = set(profile["knowledge"]["selector_kinds"])
    sources = [s for s in resolved_sources if s.binding.get("source_class") == "canonical_state"]
    items, totals = [], {"max_records": 0, "max_relations": 0, "max_bytes": 0}

    for selection in request["knowledge_selection"]["snapshots"]:
        records, relations = selection["record_ids"], selection["relation_ids"]
        if records and "record_id" not in selectors:
            return PemsProjectionResult(failure=_fail("INVALID_REQUEST", "request", diag="record_id selector disabled"))
        if relations and "relation_id" not in selectors:
            return PemsProjectionResult(failure=_fail("INVALID_REQUEST", "request", diag="relation_id selector disabled"))
        if not records and not relations and profile["knowledge"]["empty_result"] == "reject":
            return PemsProjectionResult(failure=_fail("EMPTY_RESULT_DISALLOWED", "projection"))

        source = _find_source(selection["canonical_snapshot_ref"], sources)
        if source is None:
            return PemsProjectionResult(failure=_fail(
                "INVALID_REQUEST", "projection", diag="selected canonical snapshot absent from P2 result"))
        source_ref = _source_ref(source.binding)
        try:
            doc = _strict_json(source.content)
        except Exception:
            return PemsProjectionResult(failure=_fail(
                "PEMS_SCHEMA_INVALID", "projection", source_ref, "canonical PEMS is not strict UTF-8 JSON"))
        code = _validation_code(doc, schema_v, semantic_v)
        if code:
            return PemsProjectionResult(failure=_fail(code, "projection", source_ref, "canonical PEMS validation failed"))

        result = _close(doc, records, relations, desc, limits, source_ref)
        if isinstance(result, dict) and result.get("contract") == FAILURE:
            return PemsProjectionResult(failure=result)
        projection, causes = result
        code = _validation_code(projection, schema_v, semantic_v)
        if code:
            return PemsProjectionResult(failure=_fail(code, "projection", source_ref, "selected PEMS validation failed"))
        try:
            size = len(_jcs(projection))
        except ValueError:
            return PemsProjectionResult(failure=_fail(
                "PEMS_SCHEMA_INVALID", "projection", source_ref, "selected PEMS is not jcs/1 representable"))

        totals["max_records"] += len(projection["records"])
        totals["max_relations"] += len(projection["relations"])
        totals["max_bytes"] += size
        for metric, actual in totals.items():
            if actual > limits[metric]:
                return PemsProjectionResult(failure=_limit(metric, actual, limits[metric], source_ref))
        items.append(ProjectedKnowledge(deepcopy(selection["canonical_snapshot_ref"]), projection, causes))
    return PemsProjectionResult(items=tuple(items))


def _close(doc, seed_records, seed_relations, desc, limits, source_ref):
    records, relations = doc["records"], doc["relations"]
    index = {
        "record": {x["id"]: x for x in records},
        "relation": {x["id"]: x for x in relations},
    }
    selected, depth, causes, queue = set(), {}, {}, []

    def add(ns, sid, d, kind, cid):
        if sid not in index[ns]:
            return _fail("SELECTED_SEMANTIC_ID_MISSING", "projection", source_ref, f"missing {ns} id: {sid}")
        key = (ns, sid)
        causes.setdefault(key, set()).add((kind, cid))
        if key in selected:
            return None
        if d > limits["max_depth"]:
            return _limit("max_depth", d, limits["max_depth"], source_ref)
        selected.add(key); depth[key] = d
        heapq.heappush(queue, (d, RANK[ns], sid, ns))
        nr = sum(ns0 == "record" for ns0, _ in selected)
        nl = len(selected) - nr
        if nr > limits["max_records"]:
            return _limit("max_records", nr, limits["max_records"], source_ref)
        if nl > limits["max_relations"]:
            return _limit("max_relations", nl, limits["max_relations"], source_ref)
        return None

    for sid in sorted(seed_records):
        f = add("record", sid, 0, "request_selector", _cid("request_selector", "record", sid))
        if f: return f
    for sid in sorted(seed_relations):
        f = add("relation", sid, 0, "request_selector", _cid("request_selector", "relation", sid))
        if f: return f

    for rule in sorted((r for r in desc["reference_rules"] if r["scope"] == "root"), key=lambda r: r["rule_id"]):
        value = _path(doc, rule["path"])
        for sid in _refs(rule, value):
            if rule["rule"] != "include_transitively":
                return _fail("UNDEFINED_CLOSURE_RULE", "projection", source_ref, f"invalid root closure rule: {rule['rule_id']}")
            f = add(rule["target_namespace"], sid, 0, "pems_closure",
                    _cid("pems_closure", rule["rule_id"], "root", rule["target_namespace"], sid))
            if f: return f

    while queue:
        d, _rank, sid, ns = heapq.heappop(queue)
        if depth.get((ns, sid)) != d: continue
        item = index[ns][sid]
        rules = [r for r in desc["reference_rules"] if r["scope"] == ns and
                 ("record_kinds" not in r or item.get("kind") in r["record_kinds"])]
        for rule in sorted(rules, key=lambda r: r["rule_id"]):
            refs = _refs(rule, _path(item, rule["path"]))
            if not refs: continue
            if rule["rule"] == "preserve_external_reference": continue
            if rule["rule"] == "reject":
                return _fail(rule.get("failure_code", "UNDEFINED_CLOSURE_RULE"), "projection", source_ref,
                             f"undefined closure rule: {rule['rule_id']} on {ns}:{sid}")
            if rule["rule"] != "include_transitively":
                return _fail("UNDEFINED_CLOSURE_RULE", "projection", source_ref, "unsupported closure rule outcome")
            for target in sorted(refs):
                f = add(rule["target_namespace"], target, d + 1, "pems_closure",
                        _cid("pems_closure", rule["rule_id"], ns, sid, rule["target_namespace"], target))
                if f: return f

        if ns == "record":
            for rule in sorted(desc.get("structural_rules", []), key=lambda r: r["rule_id"]):
                trig = rule["trigger"]
                if item.get("kind") != trig.get("record_kind") or _path(item, trig["path"]) != trig.get("equals"):
                    continue
                match = rule["relation_match"]
                found = [r for r in relations if r.get("kind") == match.get("kind") and r.get("from") == sid]
                for rel in sorted(found, key=lambda r: r["id"]):
                    f = add("relation", rel["id"], d + 1, "pems_closure",
                            _cid("pems_closure", rule["rule_id"], "record", sid, "relation", rel["id"]))
                    if f: return f

    projection = {
        "semantic": doc["semantic"], "project_id": doc["project_id"],
        "records": [deepcopy(x) for x in records if ("record", x["id"]) in selected],
        "relations": [deepcopy(x) for x in relations if ("relation", x["id"]) in selected],
    }
    out = []
    for ns, sid in sorted(selected, key=lambda x: (RANK[x[0]], x[1])):
        for kind, cid in sorted(causes[(ns, sid)]):
            out.append(ProjectionCause(ns, sid, kind, cid))
    return projection, tuple(out)


def _preflight(request, profile, sources):
    if not isinstance(profile, Mapping): return _fail("INVALID_PROFILE", "profile")
    try:
        k, l = profile["knowledge"], profile["limits"]["projection"]
        if profile["contract"] != "reasoning-distiller-context-profile/1" or k["required"] is not True:
            return _fail("INVALID_PROFILE", "profile")
        if k["empty_result"] not in {"allow", "reject"} or k["snapshot_multiplicity"] not in {"single", "explicit_request"}:
            return _fail("INVALID_PROFILE", "profile")
        if not isinstance(k["selector_kinds"], list) or not k["selector_kinds"] or len(k["selector_kinds"]) != len(set(k["selector_kinds"])):
            return _fail("INVALID_PROFILE", "profile")
        if not set(k["selector_kinds"]) <= {"record_id", "relation_id"} or not isinstance(k["closure_descriptor"], Mapping):
            return _fail("INVALID_PROFILE", "profile")
        if any(not isinstance(l[m], int) or isinstance(l[m], bool) or l[m] < 1 for m in ("max_records", "max_relations", "max_depth", "max_bytes")):
            return _fail("INVALID_PROFILE", "profile")
    except (KeyError, TypeError): return _fail("INVALID_PROFILE", "profile")

    if not isinstance(request, Mapping): return _fail("INVALID_REQUEST", "request")
    try:
        selections = request["knowledge_selection"]["snapshots"]
        if request["contract"] != "reasoning-distiller-context-pack-request/1" or not isinstance(selections, list) or not selections:
            return _fail("INVALID_REQUEST", "request")
        if k["snapshot_multiplicity"] == "single" and len(selections) != 1: return _fail("INVALID_REQUEST", "request")
        for s in selections:
            if not isinstance(s["canonical_snapshot_ref"], Mapping): return _fail("INVALID_REQUEST", "request")
            for field in ("record_ids", "relation_ids"):
                values = s[field]
                if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values) or len(values) != len(set(values)):
                    return _fail("INVALID_REQUEST", "request")
    except (KeyError, TypeError): return _fail("INVALID_REQUEST", "request")
    if not all(isinstance(s, ResolvedSource) for s in sources):
        return _fail("INVALID_REQUEST", "request", diag="P3 requires P2 ResolvedSource inputs")
    return None


def _toolchain(profile_desc):
    dr, sr, vr = DESC_PATH.read_bytes(), SCHEMA_PATH.read_bytes(), VALIDATOR_PATH.read_bytes()
    desc = _strict_json(dr)
    if desc.get("contract") != DESCRIPTOR or desc.get("semantic") != "pems/2": raise ValueError
    if profile_desc.get("contract") != DESCRIPTOR or profile_desc.get("semantic") != "pems/2": raise ValueError
    if _norm(profile_desc.get("raw_sha256")) != _sha(dr): raise ValueError
    if profile_desc.get("immutable_snapshot_id") != "git-blob:" + _blob(dr): raise ValueError
    basis = desc["pems_basis"]
    if basis["schema_path"] != "backends/pems-cove/pems-v2.schema.json" or basis["schema_git_blob_sha1"] != _blob(sr): raise ValueError
    if basis["validator_path"] != "backends/pems-cove/validate_pems2_contract.py" or basis["validator_git_blob_sha1"] != _blob(vr): raise ValueError
    schema = _strict_json(sr); Draft202012Validator.check_schema(schema); sv = Draft202012Validator(schema)
    spec = importlib.util.spec_from_file_location("context_packaging_p3_bound_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None: raise ValueError
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if not callable(getattr(module, "validate_candidate_document", None)): raise ValueError
    return desc, sv, module


def _validation_code(doc, schema_v, semantic_v):
    try: schema_v.validate(doc)
    except ValidationError: return "PEMS_SCHEMA_INVALID"
    try: semantic_v.validate_candidate_document(doc, schema_v)
    except (AssertionError, ValidationError, KeyError, TypeError, ValueError): return "PEMS_SEMANTIC_INVALID"
    return None


def _find_source(ref, sources):
    try: key = _snapshot_key(ref)
    except (KeyError, TypeError): return None
    found = [s for s in sources if _safe_key(s.binding) == key]
    return found[0] if len(found) == 1 else None


def _safe_key(value):
    try: return _snapshot_key(value)
    except (KeyError, TypeError): return None


def _source_ref(binding):
    return {k: binding.get(k) for k in ("source_class", "logical_namespace", "logical_source_id")}


def _path(value, path):
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value: return MISSING
        value = value[part]
    return value


def _refs(rule, value):
    if value is MISSING or value is None: return []
    if rule["value_shape"] == "array": return [x for x in value if isinstance(x, str) and x] if isinstance(value, list) else []
    if rule["value_shape"] == "scalar": return [value] if isinstance(value, str) and value else []
    return []


def _cid(*parts):
    return "p3:" + json.dumps([str(x) for x in parts], ensure_ascii=False, separators=(",", ":"))


def _fail(code, stage, source_ref=None, diag=None):
    out = {"contract": FAILURE, "code": code, "stage": stage}
    if source_ref is not None: out["source_ref"] = deepcopy(source_ref)
    if diag: out["diagnostics"] = [diag]
    return out


def _limit(metric, actual, maximum, source_ref):
    return _fail("CLOSURE_LIMIT_EXCEEDED", "projection", source_ref,
                 f"projection.{metric}: actual={actual} limit={maximum}")


def _strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out: raise ValueError("duplicate JSON member")
            out[key] = value
        return out
    def bad(value): raise ValueError(value)
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad)


def _sha(data): return "sha256:" + hashlib.sha256(data).hexdigest()
def _blob(data): return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
def _norm(value):
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71: raise ValueError
    body = value[7:]
    if any(c not in "0123456789abcdefABCDEF" for c in body): raise ValueError
    return "sha256:" + body.lower()


# Exact P1c reference behavior needed only to measure the P3 ``max_bytes`` bound.
def _jcs_string(value):
    out = bytearray(b'"'); escapes = {8:b"\\b",9:b"\\t",10:b"\\n",12:b"\\f",13:b"\\r",34:b'\\"',92:b"\\\\"}
    try: value.encode("utf-8")
    except UnicodeEncodeError as e: raise ValueError from e
    for ch in value:
        cp = ord(ch)
        out.extend(escapes[cp] if cp in escapes else (f"\\u{cp:04x}".encode() if cp <= 31 else ch.encode("utf-8")))
    return bytes(out + b'"')


def _jcs_float(value):
    if not math.isfinite(value): raise ValueError
    if value == 0: return b"0"
    if value < 0: return b"-" + _jcs_float(-value)
    text = str(value); exp = 0; exp_text = ""
    if "e" in text:
        mantissa, raw = text.split("e", 1); exp = int(raw); exp_text = ("e+" if exp >= 0 else "e-") + str(abs(exp))
    else: mantissa = text
    if "." in mantissa: first, last = mantissa.split(".", 1); dot = "."
    else: first, last, dot = mantissa, "", ""
    if last == "0": last, dot = "", ""
    if 0 < exp < 21:
        first += last; last = dot = exp_text = ""; missing = exp - len(first)
        while missing >= 0: first += "0"; missing -= 1
    elif -7 < exp < 0:
        last = first + last; first, dot, exp_text, missing = "0", ".", "", exp
        while missing < -1: last = "0" + last; missing += 1
    return f"{first}{dot}{last}{exp_text}".encode()


def _jcs(value):
    sink = BytesIO()
    def emit(obj):
        if obj is None: sink.write(b"null")
        elif obj is True: sink.write(b"true")
        elif obj is False: sink.write(b"false")
        elif isinstance(obj, str): sink.write(_jcs_string(obj))
        elif isinstance(obj, int):
            if not -(2**53-1) <= obj <= 2**53-1: raise ValueError
            sink.write(str(obj).encode())
        elif isinstance(obj, float): sink.write(_jcs_float(obj))
        elif isinstance(obj, list):
            sink.write(b"[")
            for i, item in enumerate(obj):
                if i: sink.write(b",")
                emit(item)
            sink.write(b"]")
        elif isinstance(obj, dict):
            if any(not isinstance(k, str) for k in obj): raise ValueError
            try: items = sorted(obj.items(), key=lambda x: x[0].encode("utf-16be"))
            except UnicodeEncodeError as e: raise ValueError from e
            sink.write(b"{")
            for i, (key, item) in enumerate(items):
                if i: sink.write(b",")
                sink.write(_jcs_string(key)); sink.write(b":"); emit(item)
            sink.write(b"}")
        else: raise ValueError
    emit(value); return sink.getvalue()
