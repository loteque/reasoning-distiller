#!/usr/bin/env python3
"""Reference adapter for reasoning-distiller-invocation/1.

The adapter is provider-neutral. `prepare` validates fixed local inputs and emits the
exact activation bundle for a model runner. The runner preserves the model's raw
candidate bytes and passes them to `finalize`, which validates and immutably submits
the candidate. No source-repository fallback or canonical mutation is performed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

INVOCATION_CONTRACT = "reasoning-distiller-invocation/1"
RESULT_CONTRACT = "reasoning-distiller-invocation-result/1"
ACTIVATION_CONTRACT = "reasoning-distiller-activation-bundle/1"
RGP_VERSION = "rgp/1"

EXIT_INTERNAL = 1
EXIT_PREFLIGHT = 2
EXIT_ACTIVATION = 3
EXIT_PARSE = 4
EXIT_VALIDATION = 5
EXIT_PERSISTENCE = 6

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]
DIRECTIVE_PATH = FRAMEWORK_ROOT / "agents" / "distiller" / "DIRECTIVE.md"
RGP_VALIDATOR_PATH = FRAMEWORK_ROOT / "validators" / "rgp_validator.py"


class InvocationFailure(Exception):
    def __init__(self, stage: str, reason_code: str, detail: str, exit_code: int, *, raw_candidate_path: str | None = None):
        super().__init__(detail)
        self.stage = stage
        self.reason_code = reason_code
        self.detail = detail
        self.exit_code = exit_code
        self.raw_candidate_path = raw_candidate_path


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(stage: str, reason: str, detail: str, exit_code: int, *, raw_candidate_path: str | None = None) -> InvocationFailure:
    return InvocationFailure(stage, reason, detail, exit_code, raw_candidate_path=raw_candidate_path)


def result_fail(invocation_id: str, failure: InvocationFailure) -> dict[str, Any]:
    result: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "invocation_id": invocation_id,
        "status": "FAIL",
        "stage": failure.stage,
        "reason_code": failure.reason_code,
        "detail": failure.detail,
    }
    if failure.raw_candidate_path is not None:
        result["raw_candidate_path"] = failure.raw_candidate_path
    return result


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_rel_path(value: Any, field: str) -> str:
    if not _nonempty(value):
        raise fail("preflight", "INVALID_REQUEST", f"{field} must be a non-empty relative path", EXIT_PREFLIGHT)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise fail("preflight", "UNSAFE_PATH", f"{field} must stay within the project workspace", EXIT_PREFLIGHT)
    return value


def _validate_source(source: Any, field: str) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise fail("preflight", "INVALID_REQUEST", f"{field} must be an object", EXIT_PREFLIGHT)
    allowed = {"source_id", "type", "locator", "digest"}
    unknown = set(source) - allowed
    if unknown:
        raise fail("preflight", "INVALID_REQUEST", f"{field} has unknown fields: {sorted(unknown)}", EXIT_PREFLIGHT)
    for key in ("source_id", "type", "locator"):
        if key not in source or not _nonempty(source[key]):
            raise fail("preflight", "INVALID_REQUEST", f"{field}.{key} is required", EXIT_PREFLIGHT)
    _validate_rel_path(source["locator"], f"{field}.locator")
    digest = source.get("digest")
    if digest is not None:
        if not isinstance(digest, str) or not digest.startswith("sha256:") or len(digest) != 71:
            raise fail("preflight", "INVALID_REQUEST", f"{field}.digest must be sha256:<64 lowercase hex>", EXIT_PREFLIGHT)
        hexdigest = digest[7:]
        if any(ch not in "0123456789abcdef" for ch in hexdigest):
            raise fail("preflight", "INVALID_REQUEST", f"{field}.digest must be sha256:<64 lowercase hex>", EXIT_PREFLIGHT)
    return source


def validate_request(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise fail("preflight", "INVALID_REQUEST", "request must be an object", EXIT_PREFLIGHT)
    required = {"contract", "invocation_id", "created_at", "project_root", "evidence", "source_registry", "output"}
    allowed = required | {"source_context"}
    missing = required - set(document)
    unknown = set(document) - allowed
    if missing or unknown:
        raise fail("preflight", "INVALID_REQUEST", f"request fields missing={sorted(missing)} unknown={sorted(unknown)}", EXIT_PREFLIGHT)
    if document["contract"] != INVOCATION_CONTRACT:
        raise fail("preflight", "UNSUPPORTED_CONTRACT", f"expected {INVOCATION_CONTRACT}", EXIT_PREFLIGHT)
    if not _nonempty(document["invocation_id"]) or not _nonempty(document["created_at"]):
        raise fail("preflight", "INVALID_REQUEST", "invocation_id and created_at must be non-empty strings", EXIT_PREFLIGHT)
    _validate_rel_path(document["project_root"], "project_root")

    for name in ("evidence", "source_registry"):
        value = document[name]
        if not isinstance(value, list) or not value:
            raise fail("preflight", "INVALID_REQUEST", f"{name} must be a non-empty array", EXIT_PREFLIGHT)
        for index, source in enumerate(value):
            _validate_source(source, f"{name}[{index}]")

    registry: dict[str, dict[str, Any]] = {}
    for source in document["source_registry"]:
        source_id = source["source_id"]
        if source_id in registry:
            raise fail("preflight", "DUPLICATE_SOURCE_ID", f"duplicate source registry id: {source_id}", EXIT_PREFLIGHT)
        registry[source_id] = source
    evidence_ids: set[str] = set()
    for source in document["evidence"]:
        source_id = source["source_id"]
        if source_id in evidence_ids:
            raise fail("preflight", "DUPLICATE_EVIDENCE", f"duplicate evidence source id: {source_id}", EXIT_PREFLIGHT)
        evidence_ids.add(source_id)
        registered = registry.get(source_id)
        if registered is None:
            raise fail("preflight", "UNRESOLVED_SOURCE", f"evidence source not present in source_registry: {source_id}", EXIT_PREFLIGHT)
        for key in ("type", "locator"):
            if registered[key] != source[key]:
                raise fail("preflight", "SOURCE_REGISTRY_MISMATCH", f"source registry mismatch for {source_id}: {key}", EXIT_PREFLIGHT)
        if source.get("digest") and registered.get("digest") and source["digest"] != registered["digest"]:
            raise fail("preflight", "SOURCE_REGISTRY_MISMATCH", f"source registry mismatch for {source_id}: digest", EXIT_PREFLIGHT)

    output = document["output"]
    if not isinstance(output, dict) or set(output) != {"raw_candidate_path", "submission_path"}:
        raise fail("preflight", "INVALID_REQUEST", "output requires exactly raw_candidate_path and submission_path", EXIT_PREFLIGHT)
    raw_path = _validate_rel_path(output["raw_candidate_path"], "output.raw_candidate_path")
    submission_path = _validate_rel_path(output["submission_path"], "output.submission_path")
    if raw_path == submission_path:
        raise fail("preflight", "OUTPUT_PATH_COLLISION", "raw candidate and submission paths must differ", EXIT_PREFLIGHT)

    context = document.get("source_context")
    if context is not None:
        if not isinstance(context, dict) or set(context) - {"summary", "refs"}:
            raise fail("preflight", "INVALID_REQUEST", "source_context has invalid shape", EXIT_PREFLIGHT)
        if "summary" in context and not isinstance(context["summary"], str):
            raise fail("preflight", "INVALID_REQUEST", "source_context.summary must be a string", EXIT_PREFLIGHT)
        if "refs" in context:
            refs = context["refs"]
            if not isinstance(refs, list) or any(not _nonempty(item) for item in refs) or len(refs) != len(set(refs)):
                raise fail("preflight", "INVALID_REQUEST", "source_context.refs must contain unique non-empty strings", EXIT_PREFLIGHT)
    return document


def load_request(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise fail("preflight", "REQUEST_READ_FAILED", str(exc), EXIT_PREFLIGHT) from exc
    return validate_request(document)


def resolve_within(root: Path, relative: str, field: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise fail("preflight", "PATH_ESCAPE", f"{field} escapes project root", EXIT_PREFLIGHT) from exc
    return candidate


def project_root_for(request: dict[str, Any], cwd: Path | None = None) -> Path:
    base = (cwd or Path.cwd()).resolve()
    root = resolve_within(base, request["project_root"], "project_root")
    if not root.is_dir():
        raise fail("preflight", "PROJECT_ROOT_MISSING", f"project root is not a directory: {root}", EXIT_PREFLIGHT)
    return root


def ensure_framework() -> None:
    if not DIRECTIVE_PATH.is_file() or not RGP_VALIDATOR_PATH.is_file():
        raise fail("preflight", "FRAMEWORK_INCOMPLETE", "local Distiller directive or RGP validator is missing", EXIT_PREFLIGHT)


def read_evidence(request: dict[str, Any], project_root: Path) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for source in request["evidence"]:
        path = resolve_within(project_root, source["locator"], f"evidence:{source['source_id']}")
        if path.is_symlink() or not path.is_file():
            raise fail("preflight", "EVIDENCE_UNRESOLVED", f"evidence is not a regular file: {source['source_id']}", EXIT_PREFLIGHT)
        data = path.read_bytes()
        actual = "sha256:" + sha256_bytes(data)
        if source.get("digest") and source["digest"] != actual:
            raise fail("preflight", "EVIDENCE_DIGEST_MISMATCH", f"digest mismatch for {source['source_id']}", EXIT_PREFLIGHT)
        try:
            content = data.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = base64.b64encode(data).decode("ascii")
            encoding = "base64"
        resolved.append({
            "source_id": source["source_id"],
            "type": source["type"],
            "locator": source["locator"],
            "sha256": actual,
            "encoding": encoding,
            "content": content,
        })
    return resolved


def preflight(request: dict[str, Any], cwd: Path | None = None) -> tuple[Path, list[dict[str, Any]]]:
    ensure_framework()
    project_root = project_root_for(request, cwd)
    evidence = read_evidence(request, project_root)
    for name, rel in request["output"].items():
        resolve_within(project_root, rel, f"output.{name}")
    return project_root, evidence


def make_activation_bundle(request: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    directive = DIRECTIVE_PATH.read_bytes()
    return {
        "contract": ACTIVATION_CONTRACT,
        "invocation_id": request["invocation_id"],
        "directive": {
            "path": ".reasoning-distiller/agents/distiller/DIRECTIVE.md",
            "sha256": "sha256:" + sha256_bytes(directive),
            "encoding": "utf-8",
            "content": directive.decode("utf-8"),
        },
        "instruction": "Return only the raw rgp/1 candidate graph JSON required by the installed Distiller directive. Use only the supplied evidence and source registry.",
        "evidence": evidence,
        "source_registry": request["source_registry"],
        "source_context": request.get("source_context", {}),
    }


def _load_rgp_validator():
    spec = importlib.util.spec_from_file_location("rd_rgp_validator", RGP_VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise fail("validation", "VALIDATOR_LOAD_FAILED", "cannot load local RGP validator", EXIT_VALIDATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def referenced_provenance(graph: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for record in graph.get("records", []):
        if not isinstance(record, dict):
            continue
        provenance = record.get("provenance")
        if isinstance(provenance, dict):
            for values in provenance.values():
                if isinstance(values, list):
                    refs.update(item for item in values if isinstance(item, str))
    for relation in graph.get("relations", []) or []:
        if not isinstance(relation, dict):
            continue
        provenance = relation.get("provenance")
        if isinstance(provenance, dict):
            for values in provenance.values():
                if isinstance(values, list):
                    refs.update(item for item in values if isinstance(item, str))
    return refs


def validate_candidate(graph: Any, request: dict[str, Any]) -> None:
    validator = _load_rgp_validator()
    errors = validator.validate(graph)
    if errors:
        raise fail("validation", "RGP_VALIDATION_FAILED", "; ".join(errors), EXIT_VALIDATION,
                   raw_candidate_path=request["output"]["raw_candidate_path"])
    registry_ids = {entry["source_id"] for entry in request["source_registry"]}
    unknown = sorted(referenced_provenance(graph) - registry_ids)
    if unknown:
        raise fail("validation", "UNRESOLVED_PROVENANCE", f"candidate references source ids absent from source_registry: {unknown}", EXIT_VALIDATION,
                   raw_candidate_path=request["output"]["raw_candidate_path"])


def immutable_write(path: Path, data: bytes, *, same_bytes_ok: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise fail("persistence", "PERSISTENCE_READ_FAILED", f"cannot inspect existing output {path}: {exc}", EXIT_PERSISTENCE) from exc
        if same_bytes_ok and existing == data:
            return
        raise fail("persistence", "IMMUTABLE_OUTPUT_COLLISION", f"refusing to overwrite existing output: {path}", EXIT_PERSISTENCE)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def submission_id_for(invocation_id: str, graph: dict[str, Any]) -> str:
    seed = invocation_id.encode("utf-8") + b"\0" + canonical_json_bytes(graph)
    return "RGP-" + sha256_bytes(seed)[:32].upper()


def make_submission(request: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    submission = {
        "submission_id": submission_id_for(request["invocation_id"], graph),
        "producer": {"role": "reasoning-distiller", "instance": request["invocation_id"]},
        "created_at": request["created_at"],
        "rgp_version": RGP_VERSION,
        "status": "candidate",
        "candidate_graph": graph,
        "validation": {
            "status": "passed",
            "validator": "rgp-validator/1",
            "validated_at": request["created_at"],
        },
    }
    if "source_context" in request:
        submission["source_context"] = request["source_context"]
    return submission


def finalize(request: dict[str, Any], raw_bytes: bytes, cwd: Path | None = None) -> dict[str, Any]:
    project_root, _ = preflight(request, cwd)
    raw_rel = request["output"]["raw_candidate_path"]
    submission_rel = request["output"]["submission_path"]
    raw_path = resolve_within(project_root, raw_rel, "output.raw_candidate_path")
    submission_path = resolve_within(project_root, submission_rel, "output.submission_path")

    try:
        immutable_write(raw_path, raw_bytes, same_bytes_ok=True)
    except InvocationFailure as exc:
        exc.raw_candidate_path = raw_rel if raw_path.exists() and raw_path.read_bytes() == raw_bytes else None
        raise

    try:
        graph = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise fail("parse", "RAW_CANDIDATE_PARSE_FAILED", str(exc), EXIT_PARSE, raw_candidate_path=raw_rel) from exc
    validate_candidate(graph, request)
    submission = make_submission(request, graph)
    submission_bytes = canonical_json_bytes(submission) + b"\n"
    try:
        immutable_write(submission_path, submission_bytes, same_bytes_ok=True)
    except InvocationFailure as exc:
        exc.raw_candidate_path = raw_rel
        raise
    return {
        "contract": RESULT_CONTRACT,
        "invocation_id": request["invocation_id"],
        "status": "PASS",
        "submission_id": submission["submission_id"],
        "raw_candidate_path": raw_rel,
        "submission_path": submission_rel,
    }


def prepare_command(args: argparse.Namespace) -> int:
    request: dict[str, Any] | None = None
    try:
        request = load_request(args.request)
        _, evidence = preflight(request)
        bundle = make_activation_bundle(request, evidence)
        payload = canonical_json_bytes(bundle) + b"\n"
        if args.bundle_out:
            args.bundle_out.parent.mkdir(parents=True, exist_ok=True)
            args.bundle_out.write_bytes(payload)
        else:
            sys.stdout.buffer.write(payload)
        return 0
    except InvocationFailure as exc:
        invocation_id = request.get("invocation_id", "unknown") if isinstance(request, dict) else "unknown"
        print(json.dumps(result_fail(invocation_id, exc), sort_keys=True))
        return exc.exit_code
    except Exception as exc:
        failure = fail("internal", "UNEXPECTED_INTERNAL_FAILURE", str(exc), EXIT_INTERNAL)
        invocation_id = request.get("invocation_id", "unknown") if isinstance(request, dict) else "unknown"
        print(json.dumps(result_fail(invocation_id, failure), sort_keys=True))
        return EXIT_INTERNAL


def finalize_command(args: argparse.Namespace) -> int:
    request: dict[str, Any] | None = None
    try:
        request = load_request(args.request)
        try:
            raw = args.raw_candidate.read_bytes()
        except OSError as exc:
            raise fail("activation", "RAW_CANDIDATE_UNAVAILABLE", str(exc), EXIT_ACTIVATION) from exc
        result = finalize(request, raw)
        print(json.dumps(result, sort_keys=True))
        return 0
    except InvocationFailure as exc:
        invocation_id = request.get("invocation_id", "unknown") if isinstance(request, dict) else "unknown"
        print(json.dumps(result_fail(invocation_id, exc), sort_keys=True))
        return exc.exit_code
    except Exception as exc:
        failure = fail("internal", "UNEXPECTED_INTERNAL_FAILURE", str(exc), EXIT_INTERNAL)
        invocation_id = request.get("invocation_id", "unknown") if isinstance(request, dict) else "unknown"
        print(json.dumps(result_fail(invocation_id, failure), sort_keys=True))
        return EXIT_INTERNAL


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rd-distill", description="Reference adapter for reasoning-distiller-invocation/1")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="command")
    prepare = sub.add_parser("prepare", help="validate fixed inputs and emit the model activation bundle")
    prepare.add_argument("--request", type=Path, required=True)
    prepare.add_argument("--bundle-out", type=Path)
    finalize_parser = sub.add_parser("finalize", help="preserve, validate, and immutably submit raw model output")
    finalize_parser.add_argument("--request", type=Path, required=True)
    finalize_parser.add_argument("--raw-candidate", type=Path, required=True)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(INVOCATION_CONTRACT)
        return 0
    if args.command == "prepare":
        return prepare_command(args)
    if args.command == "finalize":
        return finalize_command(args)
    parser.error("prepare or finalize is required")
    return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
