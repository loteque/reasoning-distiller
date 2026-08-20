#!/usr/bin/env python3
"""Reasoning Distiller invocation adapter with explicit ingestion source typing.

The proven v0.4.1 adapter is preserved byte-for-byte in ``rd_distill_core.py``.
This compatibility entrypoint adds an explicit ``governed_artifact`` evidence
selection path without inferring authority from filenames, paths, or prose.
"""
from __future__ import annotations

import importlib.util as _importlib_util
import sys as _sys
from pathlib import Path as _Path
from typing import Any as _Any, TextIO as _TextIO

_CORE_PATH = _Path(__file__).resolve().with_name("rd_distill_core.py")
_spec = _importlib_util.spec_from_file_location("rd_distill_core", _CORE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load Reasoning Distiller core: {_CORE_PATH}")
_core = _importlib_util.module_from_spec(_spec)
_sys.modules.setdefault("rd_distill_core", _core)
_spec.loader.exec_module(_core)

# Preserve the existing import surface, including helpers used by project tests.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals().setdefault(_name, getattr(_core, _name))

INGEST_SOURCE_TYPES = frozenset({"repository_file", "governed_artifact"})


def expand_typed_evidence_specs(
    project_root: _Path,
    specs: list[str],
    governed_specs: list[str],
) -> tuple[list[str], dict[str, str]]:
    """Expand evidence selections and bind each locator to one explicit type."""
    if not specs and not governed_specs:
        raise _core.fail(
            "preflight",
            "EVIDENCE_REQUIRED",
            "at least one evidence or governed-evidence selection is required",
            _core.EXIT_PREFLIGHT,
        )

    repository_locators = (
        _core.expand_evidence_specs(project_root, specs) if specs else []
    )
    governed_locators = (
        _core.expand_evidence_specs(project_root, governed_specs)
        if governed_specs
        else []
    )
    overlap = sorted(set(repository_locators) & set(governed_locators))
    if overlap:
        raise _core.fail(
            "preflight",
            "EVIDENCE_SOURCE_TYPE_CONFLICT",
            f"evidence selected with multiple source types: {overlap}",
            _core.EXIT_PREFLIGHT,
        )

    source_types = {
        locator: "repository_file" for locator in repository_locators
    }
    source_types.update(
        {locator: "governed_artifact" for locator in governed_locators}
    )
    return sorted(source_types), source_types


def build_typed_sources(
    project_root: _Path,
    locators: list[str],
    source_types: dict[str, str],
) -> list[dict[str, _Any]]:
    """Create deterministic source records without deriving type from names."""
    sources: list[dict[str, _Any]] = []
    seen_ids: set[str] = set()
    for locator in sorted(locators):
        path = _core.resolve_within(project_root, locator, "evidence")
        if path.is_symlink() or not path.is_file():
            raise _core.fail(
                "preflight",
                "EVIDENCE_UNRESOLVED",
                f"evidence is not a regular file: {locator}",
                _core.EXIT_PREFLIGHT,
            )

        source_type = source_types.get(locator, "repository_file")
        if source_type not in INGEST_SOURCE_TYPES:
            raise _core.fail(
                "preflight",
                "EVIDENCE_SOURCE_TYPE_INVALID",
                f"unsupported ingestion source type for {locator}: {source_type}",
                _core.EXIT_PREFLIGHT,
            )

        # Source-id spelling is deterministic bookkeeping only. Authority comes
        # from source_registry.type, never from this prefix.
        prefix = "file" if source_type == "repository_file" else "governed"
        source_id = (
            f"src:{prefix}:"
            + _core.sha256_bytes(locator.encode("utf-8"))[:24]
        )
        if source_id in seen_ids:
            raise _core.fail(
                "preflight",
                "SOURCE_ID_COLLISION",
                f"deterministic source id collision for {locator}",
                _core.EXIT_PREFLIGHT,
            )
        seen_ids.add(source_id)
        sources.append(
            {
                "source_id": source_id,
                "type": source_type,
                "locator": locator,
                "digest": "sha256:" + _core.sha256_bytes(path.read_bytes()),
            }
        )
    return sources


def create_ingestion_artifacts(
    *,
    project_root: _Path,
    project_config: dict[str, _Any],
    invocation_id: str,
    created_at: str,
    specs: list[str],
    context: str | None,
    refs: list[str],
    write: bool = True,
    governed_specs: list[str] | None = None,
) -> dict[str, _Any]:
    """Create request/bundle artifacts with optional explicit governed inputs."""
    locators, source_types = expand_typed_evidence_specs(
        project_root,
        specs,
        list(governed_specs or []),
    )
    sources = build_typed_sources(project_root, locators, source_types)
    request = _core.build_ingestion_request(
        invocation_id=invocation_id,
        created_at=created_at,
        sources=sources,
        project_config=project_config,
        context=context,
        refs=refs,
    )
    _, evidence = _core.preflight(request, cwd=project_root)
    bundle = _core.make_activation_bundle(request, evidence)

    request_bytes = _core.canonical_json_bytes(request) + b"\n"
    bundle_bytes = _core.canonical_json_bytes(bundle) + b"\n"
    request_path, bundle_path = _core._artifact_paths(
        project_root,
        project_config,
        invocation_id,
    )
    _core._preflight_artifact_write(request_path, request_bytes)
    _core._preflight_artifact_write(bundle_path, bundle_bytes)

    if write:
        _core.immutable_write(request_path, request_bytes, same_bytes_ok=True)
        _core.immutable_write(bundle_path, bundle_bytes, same_bytes_ok=True)

    return {
        "request": request,
        "bundle": bundle,
        "request_path": request_path,
        "bundle_path": bundle_path,
        "locators": locators,
    }


def collect_typed_interactive_inputs(
    *,
    input_fn=input,
    output: _TextIO = _sys.stderr,
) -> tuple[list[str], list[str], str, str, str | None, list[str]]:
    """Interactive evidence collection with explicit source type selection."""
    print("Reasoning Distiller ingestion", file=output)
    print("", file=output)
    specs: list[str] = []
    governed_specs: list[str] = []
    while True:
        print("Evidence source:", file=output)
        print("  [1] Add file", file=output)
        print("  [2] Add directory", file=output)
        print("  [3] Add glob", file=output)
        print("  [4] Done", file=output)
        choice = input_fn("> ").strip()
        if choice in {"1", "2", "3"}:
            label = {"1": "File", "2": "Directory", "3": "Glob"}[choice]
            value = _core._prompt(label, input_fn=input_fn)
            if not value:
                continue
            while True:
                source_type = _core._prompt(
                    "Source type",
                    default="repository_file",
                    input_fn=input_fn,
                )
                if source_type in INGEST_SOURCE_TYPES:
                    break
                print(
                    "Source type must be repository_file or governed_artifact.",
                    file=output,
                )
            target = governed_specs if source_type == "governed_artifact" else specs
            target.append(value)
        elif choice == "4":
            if specs or governed_specs:
                break
            print("Add at least one evidence source.", file=output)
        else:
            print("Choose 1, 2, 3, or 4.", file=output)

    invocation_id = _core._prompt(
        "Invocation ID",
        default=_core._default_invocation_id(),
        input_fn=input_fn,
    )
    created_at = _core._prompt(
        "Created at",
        default=_core._default_created_at(),
        input_fn=input_fn,
    )
    context_value = _core._prompt("Context summary", input_fn=input_fn)
    refs_value = _core._prompt(
        "Context refs (comma-separated, optional)",
        input_fn=input_fn,
    )
    refs = [item.strip() for item in refs_value.split(",") if item.strip()]
    return (
        specs,
        governed_specs,
        invocation_id,
        created_at,
        context_value or None,
        refs,
    )


def print_typed_ingestion_preview(
    *,
    locators: list[str],
    sources: list[dict[str, _Any]],
    invocation_id: str,
    request_path: _Path,
    bundle_path: _Path,
    output: _TextIO = _sys.stderr,
) -> None:
    by_locator = {source["locator"]: source for source in sources}
    print("", file=output)
    print(f"Invocation: {invocation_id}", file=output)
    print(f"Evidence files: {len(locators)}", file=output)
    for locator in locators:
        source = by_locator[locator]
        print(
            f"  [{source['type']}] {locator}  {source['digest']}",
            file=output,
        )
    print(f"Request: {request_path}", file=output)
    print(f"Bundle:  {bundle_path}", file=output)
    print("Model execution: not requested", file=output)
    print("Admission: not requested", file=output)


def ingest_command(args) -> int:
    try:
        project_root = _core._resolve_project_root(args.project_root)
        project_config = _core.load_project_config(project_root)

        if args.evidence or args.governed_evidence:
            specs = list(args.evidence or [])
            governed_specs = list(args.governed_evidence or [])
            if not args.invocation_id:
                raise _core.fail(
                    "preflight",
                    "INVOCATION_ID_REQUIRED",
                    (
                        "--invocation-id is required when --evidence or "
                        "--governed-evidence is supplied non-interactively"
                    ),
                    _core.EXIT_PREFLIGHT,
                )
            invocation_id = args.invocation_id
            created_at = args.created_at or _core._default_created_at()
            context = args.context
            refs = list(args.ref or [])
            interactive = False
        else:
            if not _sys.stdin.isatty():
                raise _core.fail(
                    "preflight",
                    "INTERACTIVE_INPUT_UNAVAILABLE",
                    (
                        "no --evidence or --governed-evidence arguments were "
                        "supplied and stdin is not interactive"
                    ),
                    _core.EXIT_PREFLIGHT,
                )
            (
                specs,
                governed_specs,
                default_id,
                default_created,
                default_context,
                default_refs,
            ) = collect_typed_interactive_inputs()
            invocation_id = args.invocation_id or default_id
            created_at = args.created_at or default_created
            context = args.context if args.context is not None else default_context
            refs = list(args.ref) if args.ref else default_refs
            interactive = True

        locators, source_types = expand_typed_evidence_specs(
            project_root,
            specs,
            governed_specs,
        )
        sources = build_typed_sources(project_root, locators, source_types)
        request_path, bundle_path = _core._artifact_paths(
            project_root,
            project_config,
            _core.validate_invocation_id(invocation_id),
        )
        print_typed_ingestion_preview(
            locators=locators,
            sources=sources,
            invocation_id=invocation_id,
            request_path=request_path,
            bundle_path=bundle_path,
        )

        if interactive and not args.yes and not args.dry_run:
            answer = input("Create activation bundle? [Y/n]: ").strip().lower()
            if answer not in {"", "y", "yes"}:
                _core.emit_json(
                    {
                        "contract": _core.INGEST_RESULT_CONTRACT,
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
            governed_specs=governed_specs,
            context=context,
            refs=refs,
            write=not args.dry_run,
        )
        request = artifacts["request"]
        result = {
            "contract": _core.INGEST_RESULT_CONTRACT,
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
        _core.emit_json(result)
        return 0
    except _core.InvocationFailure as exc:
        _core.emit_json(_core.ingest_fail(exc.reason_code, exc.detail))
        return exc.exit_code
    except Exception as exc:
        _core.emit_json(
            _core.ingest_fail("UNEXPECTED_INTERNAL_FAILURE", str(exc))
        )
        return _core.EXIT_INTERNAL


def build_parser():
    parser = _core.build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, _core.argparse._SubParsersAction)
    )
    ingest = subparsers.choices["ingest"]
    ingest.add_argument(
        "--governed-evidence",
        action="append",
        help=(
            "evidence file, directory, or glob explicitly typed as a "
            "governed_artifact; repeat for multiple selections"
        ),
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(_core.INVOCATION_CONTRACT)
        return 0
    if args.command == "ingest":
        return ingest_command(args)
    if args.command == "prepare":
        return _core.prepare_command(args)
    if args.command == "finalize":
        return _core.finalize_command(args)
    parser.error("ingest, prepare, or finalize is required")
    return _core.EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
