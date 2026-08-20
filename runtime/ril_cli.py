#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import ril_authority_grant as grants
import ril_mutation as mutation
import ril_orchestrator as legacy
import ril_shared_orchestration as shared
import ril_workflow as workflows

RESULT_CONTRACT = "reasoning-distiller-ril-cli-result/1"
DEPTHS = (0, 1, 2)


def discover_project(start: Path, explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    cur = start.resolve()
    for p in (cur, *cur.parents):
        if (p / ".reasoning-distiller").exists() or (p / "reasoning-distiller").exists() or (p / "project-knowledge").exists():
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
    try:
        n = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("depth must be 0, 1, or 2") from exc
    if n not in DEPTHS:
        raise argparse.ArgumentTypeError("depth must be 0, 1, or 2")
    return n


def _result(status: str, outcome: str, **extra: Any) -> dict[str, Any]:
    r = {"contract": RESULT_CONTRACT, "status": status, "outcome": outcome}
    r.update(extra)
    return r


def _workflow_view(store: Path, ref: str, depth: int) -> dict[str, Any]:
    definition = workflows.load_workflow(store, ref)
    projection = workflows.project_workflow(store, ref)
    out = {
        "reference": ref,
        "requested_depth": depth,
        "maximum_supported_depth": 2,
        "definition": definition,
        "lifecycle": projection["lifecycle"],
        "condition": projection["condition"],
        "head": projection["normative_head"],
    }
    if depth >= 1:
        out.update({
            "history_head": projection["history_head"],
            "normative_head": projection["normative_head"],
            "bound_results": projection["bound_results"],
            "materiality_pause": projection["materiality_pause"],
        })
    if depth >= 2:
        out["projection"] = projection
        out["events"] = workflows.read_events(store, ref)
    return out


def _grant_view(store: Path, ref: str, depth: int) -> dict[str, Any]:
    definition = grants.load_grant(store, ref)
    projection = grants.project_grant(store, ref)
    out = {
        "reference": ref,
        "requested_depth": depth,
        "maximum_supported_depth": 2,
        "definition": definition,
        "state": projection["state"],
        "head": projection["normative_head"],
    }
    if depth >= 1:
        out["projection"] = projection
    if depth >= 2:
        out["events"] = grants.read_events(store, ref)
    return out


def _event_view(store: Path, ref: str, kind: str, depth: int) -> dict[str, Any]:
    if depth > 1:
        raise ValueError(f"{kind} supports depth 0|1")
    parents: list[tuple[str, dict[str, Any]]] = []
    root_name = "workflows" if kind == "workflow-event" else "authority-grants"
    base = Path(store) / root_name
    if base.exists():
        for child in sorted(base.iterdir()):
            if not child.is_dir():
                continue
            parent_ref = ("workflow:" if kind == "workflow-event" else "authority-grant:") + child.name
            events = workflows.read_events(store, parent_ref) if kind == "workflow-event" else grants.read_events(store, parent_ref)
            for event in events:
                if event.get("reference") == ref:
                    parents.append((parent_ref, event))
    if len(parents) != 1:
        raise ValueError("typed event reference is missing or ambiguous")
    parent_ref, event = parents[0]
    out = {"reference": ref, "requested_depth": depth, "maximum_supported_depth": 1, "event": event}
    if depth >= 1:
        out["parent"] = _workflow_view(store, parent_ref, 0) if kind == "workflow-event" else _grant_view(store, parent_ref, 0)
    return out


def _content_addressed_view(root: Path, typed_ref: str, depth: int) -> dict[str, Any]:
    if depth != 0:
        raise ValueError("this artifact supports depth 0 only")
    kind, _, ident = typed_ref.partition(":")
    if not kind or not ident:
        raise ValueError("generic show requires a complete typed reference")
    hits: list[tuple[str, Any]] = []
    for base in (root / "project-knowledge", root / ".reasoning-distiller"):
        if not base.exists():
            continue
        for path in base.rglob("*.json"):
            if not path.is_file() or path.is_symlink():
                continue
            try:
                value = mutation.load_json(path)
                if mutation.digest(value).split(":", 1)[1] == ident:
                    hits.append((str(path.relative_to(root)), value))
            except Exception:
                continue
    if len(hits) != 1:
        raise ValueError("typed reference is missing or ambiguous")
    return {"reference": typed_ref, "requested_depth": 0, "maximum_supported_depth": 0, "path": hits[0][0], "artifact": hits[0][1]}


def inspect_typed(root: Path, typed_ref: str, depth: int) -> dict[str, Any]:
    wf_store, grant_store = _stores(root)
    if typed_ref.startswith("workflow:"):
        return _workflow_view(wf_store, typed_ref, depth)
    if typed_ref.startswith("workflow-event:"):
        return _event_view(wf_store, typed_ref, "workflow-event", depth)
    if typed_ref.startswith("authority-grant:"):
        return _grant_view(grant_store, typed_ref, depth)
    if typed_ref.startswith("authority-grant-event:"):
        return _event_view(grant_store, typed_ref, "authority-grant-event", depth)
    if ":" not in typed_ref:
        raise ValueError("generic show never infers type from a bare identifier")
    return _content_addressed_view(root, typed_ref, depth)


def _add_depth(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--depth", type=_depth, default=0)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ril")
    p.add_argument("--project")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--human", action="store_true")
    mode.add_argument("--json", action="store_true")
    mode.add_argument("--quiet", action="store_true")
    sp = p.add_subparsers(dest="resource", required=True)

    sp.add_parser("status")
    sp.add_parser("repair")
    canon = sp.add_parser("canon"); csp = canon.add_subparsers(dest="verb", required=True); csp.add_parser("verify")

    show = sp.add_parser("show"); show.add_argument("reference"); _add_depth(show)

    wf = sp.add_parser("workflow"); wsp = wf.add_subparsers(dest="verb", required=True)
    wsp.add_parser("list").add_argument("--all", action="store_true", dest="all_workflows")
    ws = wsp.add_parser("show"); ws.add_argument("workflow"); _add_depth(ws)
    wc = wsp.add_parser("continue"); wc.add_argument("workflow"); wc.add_argument("proposal"); wc.add_argument("--grant", action="append", dest="grants")
    wcreate = wsp.add_parser("create"); wcreate.add_argument("definition");
    wcancel = wsp.add_parser("cancel"); wcancel.add_argument("workflow"); wcancel.add_argument("--operator", required=True); wcancel.add_argument("--auth", required=True); wcancel.add_argument("--protected-root", action="store_true")
    wrev = wsp.add_parser("revise"); wrev.add_argument("workflow"); wrev.add_argument("definition"); wrev.add_argument("--expected-head")
    wack = wsp.add_parser("acknowledge"); wack.add_argument("workflow"); wack.add_argument("event"); wack.add_argument("--operator", required=True); wack.add_argument("--auth", required=True); wack.add_argument("--protected-root", action="store_true")

    ag = sp.add_parser("authority-grant"); asp = ag.add_subparsers(dest="verb", required=True)
    asp.add_parser("list")
    ash = asp.add_parser("show"); ash.add_argument("grant"); _add_depth(ash)
    agc = asp.add_parser("create"); agc.add_argument("definition"); agc.add_argument("--workflow-scope-confirmed", action="store_true")
    agr = asp.add_parser("revoke"); agr.add_argument("grant"); agr.add_argument("--operator", required=True); agr.add_argument("--auth", required=True); agr.add_argument("--protected-root", action="store_true"); agr.add_argument("--expected-head")

    ap = sp.add_parser("approve"); ap.add_argument("proposal"); ap.add_argument("--operator", required=True); ap.add_argument("--auth")

    op = sp.add_parser("operator"); osp = op.add_subparsers(dest="verb", required=True)
    for verb in ("add", "update", "disable", "enable"):
        q = osp.add_parser(verb); q.add_argument("operator"); q.add_argument("--capability", action="append", dest="capabilities")
    tr = osp.add_parser("transfer-root"); tr.add_argument("operator")

    role = sp.add_parser("role"); rsp = role.add_subparsers(dest="verb", required=True)
    rsub = rsp.add_parser("submission"); rssp = rsub.add_subparsers(dest="submission_verb", required=True)
    rcreate = rssp.add_parser("create"); rcreate.add_argument("submission"); rcreate.add_argument("--snapshot", action="store_true")

    steward = sp.add_parser("steward"); ssp = steward.add_subparsers(dest="verb", required=True)
    for verb in ("set-reconciliation", "set-admission"):
        q = ssp.add_parser(verb); q.add_argument("role")
    ssp.add_parser("clear-reconciliation"); ssp.add_parser("clear-admission")
    return p


def _legacy(root: Path, action: str, arguments: dict[str, Any]) -> Any:
    req = {"contract": legacy.REQUEST_CONTRACT, "action": action, "arguments": arguments}
    return legacy.orchestrate(root, req)


def _list_workflows(store: Path, include_all: bool) -> list[dict[str, Any]]:
    base = Path(store) / "workflows"
    if not base.exists():
        return []
    values = []
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        ref = "workflow:" + child.name
        view = _workflow_view(store, ref, 0)
        if include_all or view["lifecycle"] == "OPEN":
            values.append(view)
    return values


def _list_grants(store: Path) -> list[dict[str, Any]]:
    return [_grant_view(store, ref, 0) for ref in shared.list_grants(store)]


def execute(ns: argparse.Namespace, cwd: Path | None = None) -> dict[str, Any]:
    root = discover_project(cwd or Path.cwd(), ns.project)
    depth = getattr(ns, "depth", 0)
    if ns.quiet and depth != 0:
        return _result("FAIL", "QUIET_DEPTH_CONFLICT", project_root=str(root))
    wf_store, grant_store = _stores(root)
    try:
        if ns.resource == "status":
            value = _legacy(root, "STATUS", {})
        elif ns.resource == "repair":
            value = _legacy(root, "REPAIR_ALL", {})
        elif ns.resource == "canon" and ns.verb == "verify":
            value = _legacy(root, "VERIFY_STORAGE", {})
        elif ns.resource == "show":
            value = inspect_typed(root, ns.reference, ns.depth)
        elif ns.resource == "workflow" and ns.verb == "list":
            value = _list_workflows(wf_store, ns.all_workflows)
        elif ns.resource == "workflow" and ns.verb == "show":
            value = _workflow_view(wf_store, ns.workflow, ns.depth)
        elif ns.resource == "workflow" and ns.verb == "create":
            obj = _json(ns.definition); value = workflows.create_workflow(wf_store, obj)
        elif ns.resource == "workflow" and ns.verb == "continue":
            proposal = _json(ns.proposal)
            value = shared.advance_auto_proposal(root, wf_store, grant_store, ns.workflow, proposal, grant_refs=ns.grants)
        elif ns.resource == "workflow" and ns.verb == "cancel":
            value = workflows.cancel_workflow(wf_store, ns.workflow, ns.operator, _json(ns.auth), protected_root=ns.protected_root)
        elif ns.resource == "workflow" and ns.verb == "revise":
            value = workflows.revise_workflow(wf_store, ns.workflow, _json(ns.definition), expected_normative_head=ns.expected_head)
        elif ns.resource == "workflow" and ns.verb == "acknowledge":
            value = workflows.acknowledge_materiality(wf_store, ns.workflow, ns.event, ns.operator, _json(ns.auth), protected_root=ns.protected_root)
        elif ns.resource == "authority-grant" and ns.verb == "list":
            value = _list_grants(grant_store)
        elif ns.resource == "authority-grant" and ns.verb == "show":
            value = _grant_view(grant_store, ns.grant, ns.depth)
        elif ns.resource == "authority-grant" and ns.verb == "create":
            if not ns.workflow_scope_confirmed:
                return _result("FAIL", "GRANT_WORKFLOW_SCOPE_CONFIRMATION_REQUIRED", project_root=str(root))
            value = shared.g4.create_authorized_grant(root, grant_store, _json(ns.definition), workflow_contains_grant_scope=True)
        elif ns.resource == "authority-grant" and ns.verb == "revoke":
            value = grants.revoke_grant(grant_store, ns.grant, ns.operator, _json(ns.auth), protected_root=ns.protected_root, expected_normative_head=ns.expected_head)
        elif ns.resource == "approve":
            proposal = _json(ns.proposal)
            descriptor = shared._descriptor(root, proposal)
            rv = mutation.revalidate_proposal(proposal, descriptor["current_state"])
            if rv["classification"] != "APPLICABLE":
                return _result("STOPPED", f"PROPOSAL_{rv['classification']}", project_root=str(root), revalidation=rv)
            auth = _json(ns.auth) if ns.auth else None
            value = mutation.make_approval(proposal, ns.operator, auth)
        elif ns.resource == "operator":
            opmap = {"add": "ADD_OPERATOR", "update": "UPDATE_CAPABILITIES", "disable": "DISABLE_OPERATOR", "enable": "REENABLE_OPERATOR"}
            if ns.verb == "transfer-root":
                value = _legacy(root, "ROOT_TRANSFER_PLAN", {"to_operator_id": ns.operator})
            else:
                args = {"operation": opmap[ns.verb], "target_operator_id": ns.operator}
                if ns.verb in {"add", "update"}: args["capabilities"] = ns.capabilities or []
                value = _legacy(root, "OPERATOR_PLAN", args)
        elif ns.resource == "role" and ns.verb == "submission" and ns.submission_verb == "create":
            submission = _json(ns.submission)
            if ns.snapshot: submission["mode"] = "snapshot"
            value = _legacy(root, "ROLE_SUBMISSION_PLAN", {"submission": submission})
        elif ns.resource == "steward":
            mapping = {
                "set-reconciliation": ("SET", "semantic_reconciliation", ns.role),
                "clear-reconciliation": ("CLEAR", "semantic_reconciliation", None),
                "set-admission": ("SET", "admission", ns.role),
                "clear-admission": ("CLEAR", "admission", None),
            }
            operation, scope, role_id = mapping[ns.verb]
            args = {"operation": operation, "scope": scope}
            if role_id is not None: args["role_id"] = role_id
            value = _legacy(root, "STEWARD_AUTH_PLAN", args)
        else:
            return _result("FAIL", "UNIMPLEMENTED_CLI_ROUTE", project_root=str(root))
        return _result("PASS", "OK", project_root=str(root), value=value)
    except Exception as exc:
        return _result("FAIL", getattr(exc, "code", "CLI_ERROR"), project_root=str(root), detail=getattr(exc, "detail", str(exc)))


def render(result: dict[str, Any], ns: argparse.Namespace) -> str:
    if ns.quiet:
        value = result.get("value")
        if isinstance(value, dict):
            for key in ("reference", "workflow", "grant", "proposal_digest"):
                if isinstance(value.get(key), str):
                    return value[key]
        if isinstance(value, str):
            return value
        return result.get("outcome", "")
    if ns.json:
        return json.dumps(result, sort_keys=True, separators=(",", ":"))
    return json.dumps(result, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    p = parser(); ns = p.parse_args(argv); result = execute(ns); print(render(result, ns))
    return 0 if result["status"] in {"PASS", "STOPPED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
