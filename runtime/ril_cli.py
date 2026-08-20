#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import ril_authority_grant as grants
import ril_mutation as mutation
import ril_shared_orchestration as shared
import ril_workflow as workflows

RESULT_CONTRACT = "reasoning-distiller-ril-cli-result/1"
DEPTHS = (0, 1, 2)


def discover_project(start: Path, explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    cur = start.resolve()
    for p in (cur, *cur.parents):
        if (p / ".reasoning-distiller").exists() or (p / "reasoning-distiller").exists():
            return p
    return cur


def _stores(root: Path) -> tuple[Path, Path]:
    base = root / ".reasoning-distiller"
    return base / "workflows", base / "grants"


def _json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _depth(value: str) -> int:
    try: n = int(value)
    except ValueError as exc: raise argparse.ArgumentTypeError("depth must be 0, 1, or 2") from exc
    if n not in DEPTHS: raise argparse.ArgumentTypeError("depth must be 0, 1, or 2")
    return n


def _result(status: str, outcome: str, **extra: Any) -> dict[str, Any]:
    r = {"contract": RESULT_CONTRACT, "status": status, "outcome": outcome}
    r.update(extra); return r


def _workflow_view(store: Path, ref: str, depth: int) -> dict[str, Any]:
    definition = workflows.load_workflow(store, ref)
    projection = workflows.project_workflow(store, ref)
    out = {"reference": ref, "requested_depth": depth, "maximum_supported_depth": 2,
           "definition": definition, "lifecycle": projection["lifecycle"], "condition": projection["condition"],
           "head": projection["normative_head"]}
    if depth >= 1:
        out.update({"history_head": projection["history_head"], "normative_head": projection["normative_head"],
                    "bound_results": projection["bound_results"], "materiality_pause": projection["materiality_pause"]})
    if depth >= 2:
        out["projection"] = projection
    return out


def _grant_view(store: Path, ref: str, depth: int) -> dict[str, Any]:
    definition = grants.load_grant(store, ref)
    projection = grants.project_grant(store, ref)
    out = {"reference": ref, "requested_depth": depth, "maximum_supported_depth": 2,
           "definition": definition, "lifecycle": projection["lifecycle"], "head": projection["normative_head"]}
    if depth >= 1:
        out["projection"] = projection
    if depth >= 2:
        root = store / "authority-grants" / ref.split(":", 1)[1]
        events = []
        event_dir = root / "events"
        if event_dir.exists():
            for p in sorted(event_dir.glob("*.json")):
                events.append(grants.load_json(p))
        out["events"] = events
    return out


def inspect_typed(root: Path, typed_ref: str, depth: int) -> dict[str, Any]:
    wf_store, grant_store = _stores(root)
    if typed_ref.startswith("workflow:"):
        return _workflow_view(wf_store, typed_ref, depth)
    if typed_ref.startswith("authority-grant:"):
        return _grant_view(grant_store, typed_ref, depth)
    raise ValueError("generic show requires a supported complete typed reference")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ril")
    p.add_argument("--project")
    mode = p.add_mutually_exclusive_group(); mode.add_argument("--human", action="store_true"); mode.add_argument("--json", action="store_true"); mode.add_argument("--quiet", action="store_true")
    sp = p.add_subparsers(dest="resource", required=True)
    show = sp.add_parser("show"); show.add_argument("reference"); show.add_argument("--depth", type=_depth, default=0)
    wf = sp.add_parser("workflow"); wsp = wf.add_subparsers(dest="verb", required=True)
    ws = wsp.add_parser("show"); ws.add_argument("workflow"); ws.add_argument("--depth", type=_depth, default=0)
    wc = wsp.add_parser("continue"); wc.add_argument("workflow"); wc.add_argument("proposal"); wc.add_argument("--grant", action="append", dest="grants")
    ag = sp.add_parser("authority-grant"); asp = ag.add_subparsers(dest="verb", required=True)
    ash = asp.add_parser("show"); ash.add_argument("grant"); ash.add_argument("--depth", type=_depth, default=0)
    ap = sp.add_parser("approve"); ap.add_argument("proposal"); ap.add_argument("--operator", required=True); ap.add_argument("--auth")
    return p


def execute(ns: argparse.Namespace, cwd: Path | None = None) -> dict[str, Any]:
    root = discover_project(cwd or Path.cwd(), ns.project)
    depth = getattr(ns, "depth", 0)
    if ns.quiet and depth != 0:
        return _result("FAIL", "QUIET_DEPTH_CONFLICT", project_root=str(root))
    try:
        if ns.resource == "show": value = inspect_typed(root, ns.reference, ns.depth)
        elif ns.resource == "workflow" and ns.verb == "show": value = _workflow_view(_stores(root)[0], ns.workflow, ns.depth)
        elif ns.resource == "authority-grant" and ns.verb == "show": value = _grant_view(_stores(root)[1], ns.grant, ns.depth)
        elif ns.resource == "workflow" and ns.verb == "continue":
            proposal = _json(ns.proposal)
            value = shared.advance_auto_proposal(root, _stores(root)[0], _stores(root)[1], ns.workflow, proposal, grant_refs=ns.grants)
        elif ns.resource == "approve":
            proposal = _json(ns.proposal)
            # Direct approval is deliberately D3-gated immediately before creation.
            # This generic adapter can prove current state only for proposal shapes supported by G5.
            descriptor = shared._descriptor(root, proposal)
            rv = mutation.revalidate_proposal(proposal, descriptor["current_state"])
            if rv["classification"] != "APPLICABLE":
                return _result("STOPPED", f"PROPOSAL_{rv['classification']}", project_root=str(root), revalidation=rv)
            auth = _json(ns.auth) if ns.auth else None
            value = mutation.make_approval(proposal, ns.operator, auth)
        else: return _result("FAIL", "UNIMPLEMENTED_CLI_ROUTE", project_root=str(root))
        return _result("PASS", "OK", project_root=str(root), value=value)
    except Exception as exc:
        return _result("FAIL", getattr(exc, "code", "CLI_ERROR"), project_root=str(root), detail=getattr(exc, "detail", str(exc)))


def render(result: dict[str, Any], ns: argparse.Namespace) -> str:
    if ns.quiet:
        value = result.get("value")
        if isinstance(value, dict):
            for key in ("reference", "workflow", "grant"):
                if isinstance(value.get(key), str): return value[key]
        if isinstance(value, str): return value
        return result.get("outcome", "")
    if ns.json: return json.dumps(result, sort_keys=True, separators=(",", ":"))
    return json.dumps(result, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    p = parser(); ns = p.parse_args(argv); result = execute(ns); print(render(result, ns))
    return 0 if result["status"] in {"PASS", "STOPPED"} else 1


if __name__ == "__main__": raise SystemExit(main())
