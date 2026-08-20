#!/usr/bin/env python3
"""Provider-neutral Reasoning Distiller invocation and ingestion adapter.

`ingest` turns human evidence selection into a deterministic
reasoning-distiller-invocation/1 request plus activation bundle. `prepare`
validates an existing request and emits its bundle. A model runner preserves
the model's raw candidate bytes and passes them to `finalize`, which validates
and immutably submits the candidate.

No command in this module performs model execution, admission, canonical
mutation, or source-repository fallback.
"""
from __future__ import annotations

import argparse
import base64
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

INVOCATION_CONTRACT = "reasoning-distiller-invocation/1"
RESULT_CONTRACT = "reasoning-distiller-invocation-result/1"
ACTIVATION_CONTRACT = "reasoning-distiller-activation-bundle/1"
INGEST_RESULT_CONTRACT = "reasoning-distiller-ingest-result/1"
PROJECT_CONTRACT = "reasoning-distiller-project/1"
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
PROJECT_CONFIG_PATH = Path("project-knowledge/project.json")
RESERVED_EVIDENCE_ROOTS = frozenset({".git", ".reasoning-distiller", "project-knowledge"})
INVOCATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class InvocationFailure(Exception):
    def __init__(
        self,
        stage: str,
        reason_code: str,
        detail: str,
        exit_code: int,
        *,
        raw_candidate_path: str | None = None,
    ):
        super().__init__(detail)
        self.stage = stage
        self.reason_code = reason_code
        self.detail = detail
        self.exit_code = exit_code
        self.raw_candidate_path = raw_candidate_path


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(
    stage: str,
    reason: str,
    detail: str,
    exit_code: int,
    *,
    raw_candidate_path: str | None = None,
) -> InvocationFailure:
    return InvocationFailure(
        stage,
        reason,
        detail,
        exit_code,
        raw_candidate_path=raw_candidate_path,
    )


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


def ingest_fail(reason_code: str, detail: str) -> dict[str, Any]:
    return {
        "contract": INGEST_RESULT_CONTRACT,
        "status": "FAIL",
        "reason_code": reason_code,
        "detail": detail,
    }


def emit_json(value: dict[str, Any], stream: TextIO = sys.stdout) -> None:
    print(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        file=stream,
    )


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_rel_path(value: Any, field: str) -> str:
    if not _nonempty(value):
        raise fail(
            "preflight",
            "INVALID_REQUEST",
            f"{field} must be a non-empty relative path",
            EXIT_PREFLIGHT,
        )
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise fail(
            "preflight",
            "UNSAFE_PATH",
            f"{field} must stay within the project workspace",
            EXIT_PREFLIGHT,
        )
    return value


def _validate_source(source: Any, field: str) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise fail(
            "preflight",
            "INVALID_REQUEST",
            f"{field} must be an object",
            EXIT_PREFLIGHT,
        )
    allowed = {"source_id", "type", "locator", "digest"}
    unknown = set(source) - allowed
    if unknown:
        raise fail(
            "preflight",
            "INVALID_REQUEST",
            f"{field} has unknown fields: {sorted(unknown)}",
            EXIT_PREFLIGHT,
        )
    for key in ("source_id", "type", "locator"):
        if key not in source or not _nonempty(source[key]):
            raise fail(
                "preflight",
                "INVALID_REQUEST",
                f"{field}.{key} is required",
                EXIT_PREFLIGHT,
            )
    _validate_rel_path(source["locator"], f"{field}.locator")
    digest = source.get("digest")
    if digest is not None:
        if (
            not isinstance(digest, str)
            or not digest.startswith("sha256:")
            or len(digest) != 71
        ):
            raise fail(
                "preflight",
                "INVALID_REQUEST",
                f"{field}.digest must be sha256:<64 lowercase hex>",
                EXIT_PREFLIGHT,
            )
        hexdigest = digest[7:]
        if any(ch not in "0123456789abcdef" for ch in hexdigest):
            raise fail(
                "preflight",
                "INVALID_REQUEST",
                f"{field}.digest must be sha256:<64 lowercase hex>",
                EXIT_PREFLIGHT,
            )
    return source


def validate_request(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise fail(
            "preflight",
            "INVALID_REQUEST",
            "request must be an object",
            EXIT_PREFLIGHT,
        )
    required = {
        "contract",
        "invocation_id",
        "created_at",
        "project_root",
        "evidence",
        "source_registry",
        "output",
    }
    allowed = required | {"source_context"}
    missing = required - set(document)
    unknown = set(document) - allowed
    if missing or unknown:
        raise fail(
            "preflight",
            "INVALID_REQUEST",
            f"request fields missing={sorted(missing)} unknown={sorted(unknown)}",
            EXIT_PREFLIGHT,
        )
    if document["contract"] != INVOCATION_CONTRACT:
        raise fail(
            "preflight",
            "UNSUPPORTED_CONTRACT",
            f"expected {INVOCATION_CONTRACT}",
            EXIT_PREFLIGHT,
        )
    if not _nonempty(document["invocation_id"]) or not _nonempty(document["created_at"]):
        raise fail(
            "preflight",
            "INVALID_REQUEST",
            "invocation_id and created_at must be non-empty strings",
            EXIT_PREFLIGHT,
        )
    _validate_rel_path(document["project_root"], "project_root")

    for name in ("evidence", "source_registry"):
        value = document[name]
        if not isinstance(value, list) or not value:
            raise fail(
                "preflight",
                "INVALID_REQUEST",
                f"{name} must be a non-empty array",
                EXIT_PREFLIGHT,
            )
        for index, source in enumerate(value):
            _validate_source(source, f"{name}[{index}]")

    registry: dict[str, dict[str, Any]] = {}
    for source in document["source_registry"]:
        source_id = source["source_id"]
        if source_id in registry:
            raise fail(
                "preflight",
                "DUPLICATE_SOURCE_ID",
                f"duplicate source registry id: {source_id}",
                EXIT_PREFLIGHT,
            )
        registry[source_id] = source

    evidence_ids: set[str] = set()
    for source in document["evidence"]:
        source_id = source["source_id"]
        if source_id in evidence_ids:
            raise fail(
                "preflight",
                "DUPLICATE_EVIDENCE",
                f"duplicate evidence source id: {source_id}",
                EXIT_PREFLIGHT,
            )
        evidence_ids.add(source_id)
        registered = registry.get(source_id)
        if registered is None:
            raise fail(
                "preflight",
                "UNRESOLVED_SOURCE",
                f"evidence source not present in source_registry: {source_id}",
                EXIT_PREFLIGHT,
            )
        for key in ("type", "locator"):
            if registered[key] != source[key]:
                raise fail(
                    "preflight",
                    "SOURCE_REGISTRY_MISMATCH",
                    f"source registry mismatch for {source_id}: {key}",
                    EXIT_PREFLIGHT,
                )
        if (
            source.get("digest")
            and registered.get("digest")
            and source["digest"] != registered["digest"]
        ):
            raise fail(
                "preflight",
                "SOURCE_REGISTRY_MISMATCH",
                f"source registry mismatch for {source_id}: digest",
                EXIT_PREFLIGHT,
            )

    output = document["output"]
    if not isinstance(output, dict) or set(output) != {
        "raw_candidate_path",
        "submission_path",
    }:
        raise fail(
            "preflight",
            "INVALID_REQUEST",
            "output requires exactly raw_candidate_path and submission_path",
            EXIT_PREFLIGHT,
        )
    raw_path = _validate_rel_path(
        output["raw_candidate_path"],
        "output.raw_candidate_path",
    )
    submission_path = _validate_rel_path(
        output["submission_path"],
        "output.submission_path",
    )
    if raw_path == submission_path:
        raise fail(
            "preflight",
            "OUTPUT_PATH_COLLISION",
            "raw candidate and submission paths must differ",
            EXIT_PREFLIGHT,
        )

    context = document.get("source_context")
    if context is not None:
        if not isinstance(context, dict) or set(context) - {"summary", "refs"}:
            raise fail(
                "preflight",
                "INVALID_REQUEST",
                "source_context has invalid shape",
                EXIT_PREFLIGHT,
            )
        if "summary" in context and not isinstance(context["summary"], str):
            raise fail(
                "preflight",
                "INVALID_REQUEST",
                "source_context.summary must be a string",
                EXIT_PREFLIGHT,
            )
        if "refs" in context:
            refs = context["refs"]
            if (
                not isinstance(refs, list)
                or any(not _nonempty(item) for item in refs)
                or len(refs) != len(set(refs))
            ):
                raise fail(
                    "preflight",
                    "INVALID_REQUEST",
                    "source_context.refs must contain unique non-empty strings",
                    EXIT_PREFLIGHT,
                )
    return document


def load_request(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise fail(
            "preflight",
            "REQUEST_READ_FAILED",
            str(exc),
            EXIT_PREFLIGHT,
        ) from exc
    return validate_request(document)


def resolve_within(root: Path, relative: str, field: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise fail(
            "preflight",
            "PATH_ESCAPE",
            f"{field} escapes project root",
            EXIT_PREFLIGHT,
        ) from exc
    return candidate


def project_root_for(request: dict[str, Any], cwd: Path | None = None) -> Path:
    base = (cwd or Path.cwd()).resolve()
    root = resolve_within(base, request["project_root"], "project_root")
    if not root.is_dir():
        raise fail(
            "preflight",
            "PROJECT_ROOT_MISSING",
            f"project root is not a directory: {root}",
            EXIT_PREFLIGHT,
        )
    return root


def ensure_framework() -> None:
    if not DIRECTIVE_PATH.is_file() or not RGP_VALIDATOR_PATH.is_file():
        raise fail(
            "preflight",
            "FRAMEWORK_INCOMPLETE",
            "local Distiller directive or RGP validator is missing",
            EXIT_PREFLIGHT,
        )


def read_evidence(
    request: dict[str, Any],
    project_root: Path,
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for source in request["evidence"]:
        path = resolve_within(
            project_root,
            source["locator"],
            f"evidence:{source['source_id']}",
        )
        if path.is_symlink() or not path.is_file():
            raise fail(
                "preflight",
                "EVIDENCE_UNRESOLVED",
                f"evidence is not a regular file: {source['source_id']}",
                EXIT_PREFLIGHT,
            )
        data = path.read_bytes()
        actual = "sha256:" + sha256_bytes(data)
        if source.get("digest") and source["digest"] != actual:
            raise fail(
                "preflight",
                "EVIDENCE_DIGEST_MISMATCH",
                f"digest mismatch for {source['source_id']}",
                EXIT_PREFLIGHT,
            )
        try:
            content = data.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = base64.b64encode(data).decode("ascii")
            encoding = "base64"
        resolved.append(
            {
                "source_id": source["source_id"],
                "type": source["type"],
                "locator": source["locator"],
                "sha256": actual,
                "encoding": encoding,
                "content": content,
            }
        )
    return resolved


def preflight(
    request: dict[str, Any],
    cwd: Path | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    ensure_framework()
    project_root = project_root_for(request, cwd)
    evidence = read_evidence(request, project_root)
    for name, rel in request["output"].items():
        resolve_within(project_root, rel, f"output.{name}")
    return project_root, evidence


def make_activation_bundle(
    request: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
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
        "instruction": (
            "Return only the raw rgp/1 candidate graph JSON required by the "
            "installed Distiller directive. Use only the supplied evidence and "
            "source registry."
        ),
        "evidence": evidence,
        "source_registry": request["source_registry"],
        "source_context": request.get("source_context", {}),
    }


def _load_rgp_validator():
    spec = importlib.util.spec_from_file_location(
        "rd_rgp_validator",
        RGP_VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise fail(
            "validation",
            "VALIDATOR_LOAD_FAILED",
            "cannot load local RGP validator",
            EXIT_VALIDATION,
        )
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
        raise fail(
            "validation",
            "RGP_VALIDATION_FAILED",
            "; ".join(errors),
            EXIT_VALIDATION,
            raw_candidate_path=request["output"]["raw_candidate_path"],
        )
    registry_ids = {
        entry["source_id"] for entry in request["source_registry"]
    }
    unknown = sorted(referenced_provenance(graph) - registry_ids)
    if unknown:
        raise fail(
            "validation",
            "UNRESOLVED_PROVENANCE",
            (
                "candidate references source ids absent from source_registry: "
                f"{unknown}"
            ),
            EXIT_VALIDATION,
            raw_candidate_path=request["output"]["raw_candidate_path"],
        )


def immutable_write(path: Path, data: bytes, *, same_bytes_ok: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise fail(
                "persistence",
                "PERSISTENCE_READ_FAILED",
                f"cannot inspect existing output {path}: {exc}",
                EXIT_PERSISTENCE,
            ) from exc
        if same_bytes_ok and existing == data:
            return
        raise fail(
            "persistence",
            "IMMUTABLE_OUTPUT_COLLISION",
            f"refusing to overwrite existing output: {path}",
            EXIT_PERSISTENCE,
        )
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


def make_submission(
    request: dict[str, Any],
    graph: dict[str, Any],
) -> dict[str, Any]:
    submission = {
        "submission_id": submission_id_for(request["invocation_id"], graph),
        "producer": {
            "role": "reasoning-distiller",
            "instance": request["invocation_id"],
        },
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


def finalize(
    request: dict[str, Any],
    raw_bytes: bytes,
    cwd: Path | None = None,
) -> dict[str, Any]:
    project_root, _ = preflight(request, cwd)
    raw_rel = request["output"]["raw_candidate_path"]
    submission_rel = request["output"]["submission_path"]
    raw_path = resolve_within(
        project_root,
        raw_rel,
        "output.raw_candidate_path",
    )
    submission_path = resolve_within(
        project_root,
        submission_rel,
        "output.submission_path",
    )

    try:
        immutable_write(raw_path, raw_bytes, same_bytes_ok=True)
    except InvocationFailure as exc:
        exc.raw_candidate_path = (
            raw_rel
            if raw_path.exists() and raw_path.read_bytes() == raw_bytes
            else None
        )
        raise

    try:
        graph = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise fail(
            "parse",
            "RAW_CANDIDATE_PARSE_FAILED",
            str(exc),
            EXIT_PARSE,
            raw_candidate_path=raw_rel,
        ) from exc
    validate_candidate(graph, request)
    submission = make_submission(request, graph)
    submission_bytes = canonical_json_bytes(submission) + b"\n"
    try:
        immutable_write(
            submission_path,
            submission_bytes,
            same_bytes_ok=True,
        )
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


# ---------------------------------------------------------------------------
# Ingestion wizard
# ---------------------------------------------------------------------------

def _resolve_project_root(raw: str) -> Path:
    try:
        root = Path(raw).expanduser().resolve(strict=True)
    except OSError as exc:
        raise fail(
            "preflight",
            "PROJECT_ROOT_MISSING",
            str(exc),
            EXIT_PREFLIGHT,
        ) from exc
    if not root.is_dir():
        raise fail(
            "preflight",
            "PROJECT_ROOT_MISSING",
            f"project root is not a directory: {root}",
            EXIT_PREFLIGHT,
        )
    return root


def load_project_config(project_root: Path) -> dict[str, Any]:
    path = resolve_within(
        project_root,
        PROJECT_CONFIG_PATH.as_posix(),
        "project_config",
    )
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise fail(
            "preflight",
            "PROJECT_NOT_BOOTSTRAPPED",
            (
                f"{PROJECT_CONFIG_PATH.as_posix()} is missing; run "
                ".reasoning-distiller/runtime/rd_bootstrap.py first"
            ),
            EXIT_PREFLIGHT,
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise fail(
            "preflight",
            "PROJECT_CONFIG_INVALID",
            str(exc),
            EXIT_PREFLIGHT,
        ) from exc

    if not isinstance(document, dict) or document.get("contract") != PROJECT_CONTRACT:
        raise fail(
            "preflight",
            "PROJECT_CONFIG_INVALID",
            f"expected {PROJECT_CONTRACT}",
            EXIT_PREFLIGHT,
        )
    paths = document.get("paths")
    required = {"evidence", "invocations", "submissions"}
    if not isinstance(paths, dict) or set(paths) != required:
        raise fail(
            "preflight",
            "PROJECT_CONFIG_INVALID",
            f"paths must contain exactly {sorted(required)}",
            EXIT_PREFLIGHT,
        )
    for name in sorted(required):
        rel = _validate_rel_path(paths[name], f"project.paths.{name}")
        resolve_within(project_root, rel, f"project.paths.{name}")
    return document


def validate_invocation_id(value: str) -> str:
    if not INVOCATION_ID_RE.fullmatch(value):
        raise fail(
            "preflight",
            "INVALID_INVOCATION_ID",
            (
                "invocation id must start with an alphanumeric character and "
                "contain only A-Z, a-z, 0-9, '.', '_' or '-' (max 128 chars)"
            ),
            EXIT_PREFLIGHT,
        )
    return value


def _is_reserved_evidence(rel: str) -> bool:
    parts = Path(rel).parts
    return bool(parts and parts[0] in RESERVED_EVIDENCE_ROOTS)


def _safe_evidence_file(project_root: Path, path: Path) -> str | None:
    try:
        relative = path.relative_to(project_root)
    except ValueError as exc:
        raise fail(
            "preflight",
            "EVIDENCE_PATH_ESCAPE",
            f"evidence path escapes project root: {path}",
            EXIT_PREFLIGHT,
        ) from exc

    rel = relative.as_posix()
    if _is_reserved_evidence(rel):
        return None
    if path.is_symlink():
        raise fail(
            "preflight",
            "EVIDENCE_SYMLINK",
            f"symlink evidence is not allowed: {rel}",
            EXIT_PREFLIGHT,
        )
    resolved = path.resolve()
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError as exc:
        raise fail(
            "preflight",
            "EVIDENCE_PATH_ESCAPE",
            f"evidence path escapes project root: {rel}",
            EXIT_PREFLIGHT,
        ) from exc
    if not path.is_file():
        return None
    return rel


def expand_evidence_specs(
    project_root: Path,
    specs: list[str],
) -> list[str]:
    if not specs:
        raise fail(
            "preflight",
            "EVIDENCE_REQUIRED",
            "at least one evidence file, directory, or glob is required",
            EXIT_PREFLIGHT,
        )

    locators: set[str] = set()
    for raw in specs:
        if not _nonempty(raw):
            raise fail(
                "preflight",
                "EVIDENCE_SPEC_INVALID",
                "evidence specs must be non-empty",
                EXIT_PREFLIGHT,
            )
        spec_path = Path(raw)
        if spec_path.is_absolute() or ".." in spec_path.parts:
            raise fail(
                "preflight",
                "EVIDENCE_SPEC_UNSAFE",
                f"evidence spec must stay within project root: {raw}",
                EXIT_PREFLIGHT,
            )

        matches: list[Path]
        if glob.has_magic(raw):
            absolute_pattern = str(project_root / raw)
            matches = [
                Path(item)
                for item in glob.glob(
                    absolute_pattern,
                    recursive=True,
                    include_hidden=True,
                )
            ]
        else:
            target = project_root / raw
            if target.is_symlink():
                raise fail(
                    "preflight",
                    "EVIDENCE_SYMLINK",
                    f"symlink evidence is not allowed: {raw}",
                    EXIT_PREFLIGHT,
                )
            if target.is_dir():
                matches = list(target.rglob("*"))
            elif target.exists():
                matches = [target]
            else:
                matches = []

        if not matches:
            raise fail(
                "preflight",
                "EVIDENCE_SPEC_EMPTY",
                f"evidence spec matched nothing: {raw}",
                EXIT_PREFLIGHT,
            )

        accepted_before = len(locators)
        for match in matches:
            locator = _safe_evidence_file(project_root, match)
            if locator is not None:
                locators.add(locator)

        if len(locators) == accepted_before:
            raise fail(
                "preflight",
                "EVIDENCE_SPEC_EXCLUDED",
                (
                    f"evidence spec produced no admissible files: {raw}; "
                    "reserved roots are .git/, .reasoning-distiller/, and "
                    "project-knowledge/"
                ),
                EXIT_PREFLIGHT,
            )

    if not locators:
        raise fail(
            "preflight",
            "EVIDENCE_REQUIRED",
            "no admissible evidence files remain after exclusions",
            EXIT_PREFLIGHT,
        )
    return sorted(locators)


def build_sources(
    project_root: Path,
    locators: list[str],
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for locator in sorted(locators):
        path = resolve_within(project_root, locator, "evidence")
        if path.is_symlink() or not path.is_file():
            raise fail(
                "preflight",
                "EVIDENCE_UNRESOLVED",
                f"evidence is not a regular file: {locator}",
                EXIT_PREFLIGHT,
            )
        source_id = "src:file:" + sha256_bytes(locator.encode("utf-8"))[:24]
        if source_id in seen_ids:
            raise fail(
                "preflight",
                "SOURCE_ID_COLLISION",
                f"deterministic source id collision for {locator}",
                EXIT_PREFLIGHT,
            )
        seen_ids.add(source_id)
        sources.append(
            {
                "source_id": source_id,
                "type": "repository_file",
                "locator": locator,
                "digest": "sha256:" + sha256_bytes(path.read_bytes()),
            }
        )
    return sources


def build_ingestion_request(
    *,
    invocation_id: str,
    created_at: str,
    sources: list[dict[str, Any]],
    project_config: dict[str, Any],
    context: str | None,
    refs: list[str],
) -> dict[str, Any]:
    validate_invocation_id(invocation_id)
    if not _nonempty(created_at):
        raise fail(
            "preflight",
            "CREATED_AT_REQUIRED",
            "created-at must be a non-empty string",
            EXIT_PREFLIGHT,
        )
    if len(refs) != len(set(refs)) or any(not _nonempty(item) for item in refs):
        raise fail(
            "preflight",
            "INVALID_CONTEXT_REFS",
            "context refs must be unique non-empty strings",
            EXIT_PREFLIGHT,
        )

    paths = project_config["paths"]
    invocations_dir = paths["invocations"].rstrip("/")
    submissions_dir = paths["submissions"].rstrip("/")
    request: dict[str, Any] = {
        "contract": INVOCATION_CONTRACT,
        "invocation_id": invocation_id,
        "created_at": created_at,
        "project_root": ".",
        "evidence": sources,
        "source_registry": [dict(source) for source in sources],
        "output": {
            "raw_candidate_path": (
                f"{invocations_dir}/{invocation_id}.raw.json"
            ),
            "submission_path": (
                f"{submissions_dir}/{invocation_id}.json"
            ),
        },
    }
    source_context: dict[str, Any] = {}
    if context is not None:
        source_context["summary"] = context
    if refs:
        source_context["refs"] = refs
    if source_context:
        request["source_context"] = source_context
    return validate_request(request)


def _artifact_paths(
    project_root: Path,
    project_config: dict[str, Any],
    invocation_id: str,
) -> tuple[Path, Path]:
    invocations_dir = project_config["paths"]["invocations"].rstrip("/")
    request_path = resolve_within(
        project_root,
        f"{invocations_dir}/{invocation_id}.request.json",
        "request_output",
    )
    bundle_path = resolve_within(
        project_root,
        f"{invocations_dir}/{invocation_id}.bundle.json",
        "bundle_output",
    )
    return request_path, bundle_path


def _preflight_artifact_write(path: Path, data: bytes) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise fail(
                "persistence",
                "INGESTION_OUTPUT_COLLISION",
                f"output exists but is not a normal file: {path}",
                EXIT_PERSISTENCE,
            )
        if path.read_bytes() != data:
            raise fail(
                "persistence",
                "INGESTION_OUTPUT_COLLISION",
                f"refusing to overwrite different ingestion artifact: {path}",
                EXIT_PERSISTENCE,
            )


def create_ingestion_artifacts(
    *,
    project_root: Path,
    project_config: dict[str, Any],
    invocation_id: str,
    created_at: str,
    specs: list[str],
    context: str | None,
    refs: list[str],
    write: bool = True,
) -> dict[str, Any]:
    locators = expand_evidence_specs(project_root, specs)
    sources = build_sources(project_root, locators)
    request = build_ingestion_request(
        invocation_id=invocation_id,
        created_at=created_at,
        sources=sources,
        project_config=project_config,
        context=context,
        refs=refs,
    )
    _, evidence = preflight(request, cwd=project_root)
    bundle = make_activation_bundle(request, evidence)

    request_bytes = canonical_json_bytes(request) + b"\n"
    bundle_bytes = canonical_json_bytes(bundle) + b"\n"
    request_path, bundle_path = _artifact_paths(
        project_root,
        project_config,
        invocation_id,
    )

    _preflight_artifact_write(request_path, request_bytes)
    _preflight_artifact_write(bundle_path, bundle_bytes)

    if write:
        immutable_write(request_path, request_bytes, same_bytes_ok=True)
        immutable_write(bundle_path, bundle_bytes, same_bytes_ok=True)

    return {
        "request": request,
        "bundle": bundle,
        "request_path": request_path,
        "bundle_path": bundle_path,
        "locators": locators,
    }


def _default_invocation_id() -> str:
    return datetime.now().astimezone().strftime("distill-%Y%m%d-%H%M%S")


def _default_created_at() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _prompt(
    label: str,
    *,
    default: str | None = None,
    input_fn=input,
) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input_fn(f"{label}{suffix}: ").strip()
    return value if value else (default or "")


def collect_interactive_inputs(
    *,
    input_fn=input,
    output: TextIO = sys.stderr,
) -> tuple[list[str], str, str, str | None, list[str]]:
    print("Reasoning Distiller ingestion", file=output)
    print("", file=output)
    specs: list[str] = []
    while True:
        print("Evidence source:", file=output)
        print("  [1] Add file", file=output)
        print("  [2] Add directory", file=output)
        print("  [3] Add glob", file=output)
        print("  [4] Done", file=output)
        choice = input_fn("> ").strip()
        if choice in {"1", "2", "3"}:
            label = {"1": "File", "2": "Directory", "3": "Glob"}[choice]
            value = _prompt(label, input_fn=input_fn)
            if value:
                specs.append(value)
        elif choice == "4":
            if specs:
                break
            print("Add at least one evidence source.", file=output)
        else:
            print("Choose 1, 2, 3, or 4.", file=output)

    invocation_id = _prompt(
        "Invocation ID",
        default=_default_invocation_id(),
        input_fn=input_fn,
    )
    created_at = _prompt(
        "Created at",
        default=_default_created_at(),
        input_fn=input_fn,
    )
    context_value = _prompt("Context summary", input_fn=input_fn)
    refs_value = _prompt(
        "Context refs (comma-separated, optional)",
        input_fn=input_fn,
    )
    refs = [item.strip() for item in refs_value.split(",") if item.strip()]
    return specs, invocation_id, created_at, context_value or None, refs


def print_ingestion_preview(
    *,
    locators: list[str],
    sources: list[dict[str, Any]],
    invocation_id: str,
    request_path: Path,
    bundle_path: Path,
    output: TextIO = sys.stderr,
) -> None:
    by_locator = {source["locator"]: source for source in sources}
    print("", file=output)
    print(f"Invocation: {invocation_id}", file=output)
    print(f"Evidence files: {len(locators)}", file=output)
    for locator in locators:
        digest = by_locator[locator]["digest"]
        print(f"  {locator}  {digest}", file=output)
    print(f"Request: {request_path}", file=output)
    print(f"Bundle:  {bundle_path}", file=output)
    print("Model execution: not requested", file=output)
    print("Admission: not requested", file=output)


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
        invocation_id = (
            request.get("invocation_id", "unknown")
            if isinstance(request, dict)
            else "unknown"
        )
        emit_json(result_fail(invocation_id, exc))
        return exc.exit_code
    except Exception as exc:
        failure = fail(
            "internal",
            "UNEXPECTED_INTERNAL_FAILURE",
            str(exc),
            EXIT_INTERNAL,
        )
        invocation_id = (
            request.get("invocation_id", "unknown")
            if isinstance(request, dict)
            else "unknown"
        )
        emit_json(result_fail(invocation_id, failure))
        return EXIT_INTERNAL


def finalize_command(args: argparse.Namespace) -> int:
    request: dict[str, Any] | None = None
    try:
        request = load_request(args.request)
        try:
            raw = args.raw_candidate.read_bytes()
        except OSError as exc:
            raise fail(
                "activation",
                "RAW_CANDIDATE_UNAVAILABLE",
                str(exc),
                EXIT_ACTIVATION,
            ) from exc
        result = finalize(request, raw)
        emit_json(result)
        return 0
    except InvocationFailure as exc:
        invocation_id = (
            request.get("invocation_id", "unknown")
            if isinstance(request, dict)
            else "unknown"
        )
        emit_json(result_fail(invocation_id, exc))
        return exc.exit_code
    except Exception as exc:
        failure = fail(
            "internal",
            "UNEXPECTED_INTERNAL_FAILURE",
            str(exc),
            EXIT_INTERNAL,
        )
        invocation_id = (
            request.get("invocation_id", "unknown")
            if isinstance(request, dict)
            else "unknown"
        )
        emit_json(result_fail(invocation_id, failure))
        return EXIT_INTERNAL


def ingest_command(args: argparse.Namespace) -> int:
    try:
        project_root = _resolve_project_root(args.project_root)
        project_config = load_project_config(project_root)

        if args.evidence:
            specs = list(args.evidence)
            if not args.invocation_id:
                raise fail(
                    "preflight",
                    "INVOCATION_ID_REQUIRED",
                    (
                        "--invocation-id is required when --evidence is supplied "
                        "non-interactively"
                    ),
                    EXIT_PREFLIGHT,
                )
            invocation_id = args.invocation_id
            created_at = args.created_at or _default_created_at()
            context = args.context
            refs = list(args.ref or [])
            interactive = False
        else:
            if not sys.stdin.isatty():
                raise fail(
                    "preflight",
                    "INTERACTIVE_INPUT_UNAVAILABLE",
                    (
                        "no --evidence arguments were supplied and stdin is not "
                        "interactive"
                    ),
                    EXIT_PREFLIGHT,
                )
            specs, default_id, default_created, default_context, default_refs = (
                collect_interactive_inputs()
            )
            invocation_id = args.invocation_id or default_id
            created_at = args.created_at or default_created
            context = args.context if args.context is not None else default_context
            refs = list(args.ref) if args.ref else default_refs
            interactive = True

        locators = expand_evidence_specs(project_root, specs)
        sources = build_sources(project_root, locators)
        request_path, bundle_path = _artifact_paths(
            project_root,
            project_config,
            validate_invocation_id(invocation_id),
        )
        print_ingestion_preview(
            locators=locators,
            sources=sources,
            invocation_id=invocation_id,
            request_path=request_path,
            bundle_path=bundle_path,
        )

        if interactive and not args.yes and not args.dry_run:
            answer = input("Create activation bundle? [Y/n]: ").strip().lower()
            if answer not in {"", "y", "yes"}:
                emit_json(
                    {
                        "contract": INGEST_RESULT_CONTRACT,
                        "status": "CANCELLED",
                        "invocation_id": invocation_id,
                    }
                )
                return 0

        artifacts = create_ingestion_artifacts(
            project_root=project_root,
            project_config=project_config,
            invocation_id=invocation_id,
            created_at=created_at,
            specs=specs,
            context=context,
            refs=refs,
            write=not args.dry_run,
        )
        request = artifacts["request"]
        result = {
            "contract": INGEST_RESULT_CONTRACT,
            "status": "PASS",
            "outcome": "PREVIEW" if args.dry_run else "CREATED",
            "invocation_id": invocation_id,
            "evidence_count": len(artifacts["locators"]),
            "request_path": artifacts["request_path"].relative_to(
                project_root
            ).as_posix(),
            "bundle_path": artifacts["bundle_path"].relative_to(
                project_root
            ).as_posix(),
            "raw_candidate_path": request["output"]["raw_candidate_path"],
            "submission_path": request["output"]["submission_path"],
            "next_action": "submit activation bundle to a model runner",
        }
        emit_json(result)
        return 0
    except InvocationFailure as exc:
        emit_json(ingest_fail(exc.reason_code, exc.detail))
        return exc.exit_code
    except Exception as exc:
        emit_json(ingest_fail("UNEXPECTED_INTERNAL_FAILURE", str(exc)))
        return EXIT_INTERNAL


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rd-distill",
        description=(
            "Provider-neutral ingestion, activation, and candidate submission "
            "adapter for reasoning-distiller-invocation/1"
        ),
    )
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="command")

    ingest = sub.add_parser(
        "ingest",
        help=(
            "select evidence and build an invocation request plus activation bundle"
        ),
    )
    ingest.add_argument(
        "--project-root",
        default=".",
        help="initialized project repository root (default: current directory)",
    )
    ingest.add_argument(
        "--evidence",
        action="append",
        help=(
            "evidence file, directory, or glob relative to project root; repeat "
            "for multiple selections"
        ),
    )
    ingest.add_argument("--invocation-id")
    ingest.add_argument("--created-at")
    ingest.add_argument("--context")
    ingest.add_argument(
        "--ref",
        action="append",
        help="source-context reference; repeat for multiple refs",
    )
    ingest.add_argument(
        "--dry-run",
        action="store_true",
        help="preview and validate without writing request or bundle",
    )
    ingest.add_argument(
        "--yes",
        action="store_true",
        help="skip final confirmation in interactive mode",
    )

    prepare = sub.add_parser(
        "prepare",
        help="validate fixed inputs and emit the model activation bundle",
    )
    prepare.add_argument("--request", type=Path, required=True)
    prepare.add_argument("--bundle-out", type=Path)

    finalize_parser = sub.add_parser(
        "finalize",
        help="preserve, validate, and immutably submit raw model output",
    )
    finalize_parser.add_argument("--request", type=Path, required=True)
    finalize_parser.add_argument("--raw-candidate", type=Path, required=True)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(INVOCATION_CONTRACT)
        return 0
    if args.command == "ingest":
        return ingest_command(args)
    if args.command == "prepare":
        return prepare_command(args)
    if args.command == "finalize":
        return finalize_command(args)
    parser.error("ingest, prepare, or finalize is required")
    return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
