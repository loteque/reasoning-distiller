#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

import ril_activation_fast_path as activation_fast_path
import ril_admission as admission
import ril_authority_grant as grants
import ril_mutation as mutation
import ril_operator_management as operator_management
import ril_operators as operators
import ril_orchestrator as legacy
import ril_reconciliation as reconciliation
import ril_recovery as recovery
import ril_roles as roles
import ril_shared_orchestration as shared
import ril_steward_authorization as steward_authorization
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
            if not child.is_dir() or child.is_symlink():
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


def _json_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for base in (root / "project-knowledge", root / ".reasoning-distiller"):
        if not base.exists() or not base.is_dir() or base.is_symlink():
            continue
        for path in base.rglob("*.json"):
            if path.is_file() and not path.is_symlink():
                paths.append(path)
    return sorted(set(paths), key=lambda p: p.as_posix())


def _artifact_contracts(kind: str) -> set[str] | None:
    return {
        "proposal": {mutation.PROPOSAL_CONTRACT},
        "approval": {mutation.APPROVAL_CONTRACT, mutation.APPROVAL_V2_CONTRACT},
        "submission": {roles.SUBMISSION_CONTRACT},
        "disposition": {reconciliation.DISPOSITION_CONTRACT},
        "receipt": {admission.RECEIPT_CONTRACT},
    }.get(kind)


def _candidate_files(root: Path) -> list[Path]:
    base = root / "project-knowledge" / "submissions"
    if not base.exists() or not base.is_dir() or base.is_symlink():
        return []
    return sorted((p for p in base.rglob("*.json") if p.is_file() and not p.is_symlink()), key=lambda p: p.as_posix())


def _inventory(root: Path, kind: str) -> list[dict[str, Any]]:
    contracts = _artifact_contracts(kind)
    files = _candidate_files(root) if kind == "candidate" else _json_files(root)
    values: list[dict[str, Any]] = []
    for path in files:
        try:
            value = mutation.load_json(path)
        except Exception:
            continue
        if contracts is not None and (not isinstance(value, dict) or value.get("contract") not in contracts):
            continue
        ref = f"{kind}:" + mutation.digest(value).split(":", 1)[1]
        values.append({"reference": ref, "path": path.relative_to(root).as_posix(), "artifact": value})
    unique: dict[str, dict[str, Any]] = {}
    for item in values:
        unique.setdefault(item["reference"], item)
    return [unique[k] for k in sorted(unique)]


def _artifact_view(root: Path, typed_ref: str, depth: int) -> dict[str, Any]:
    if depth != 0:
        raise ValueError("this artifact supports depth 0 only")
    kind, sep, ident = typed_ref.partition(":")
    if not sep or not kind or not ident:
        raise ValueError("generic show requires a complete typed reference")
    supported = {"candidate", "proposal", "approval", "submission", "disposition", "receipt"}
    if kind not in supported:
        raise ValueError("unsupported typed reference")
    hits = [item for item in _inventory(root, kind) if item["reference"] == typed_ref]
    if len(hits) != 1:
        raise ValueError("typed reference is missing or ambiguous")
    return {"reference": typed_ref, "requested_depth": 0, "maximum_supported_depth": 0, "path": hits[0]["path"], "artifact": hits[0]["artifact"]}


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
    return _artifact_view(root, typed_ref, depth)


def _add_depth(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--depth", type=_depth, default=0)


def _add_list_show(parent: argparse.ArgumentParser, noun: str) -> None:
    sub = parent.add_subparsers(dest="verb", required=True)
    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument(noun)


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
    wcreate = wsp.add_parser("create"); wcreate.add_argument("definition")
    wcancel = wsp.add_parser("cancel"); wcancel.add_argument("workflow"); wcancel.add_argument("--operator", required=True); wcancel.add_argument("--auth", required=True); wcancel.add_argument("--protected-root", action="store_true")
    wrev = wsp.add_parser("revise"); wrev.add_argument("workflow"); wrev.add_argument("definition"); wrev.add_argument("--expected-head")
    wack = wsp.add_parser("acknowledge"); wack.add_argument("workflow"); wack.add_argument("event"); wack.add_argument("--operator", required=True); wack.add_argument("--auth", required=True); wack.add_argument("--protected-root", action="store_true")

    ag = sp.add_parser("authority-grant"); asp = ag.add_subparsers(dest="verb", required=True)
    asp.add_parser("list")
    ash = asp.add_parser("show"); ash.add_argument("grant"); _add_depth(ash)
    agc = asp.add_parser("create"); agc.add_argument("definition"); agc.add_argument("--workflow-scope-confirmed", action="store_true")
    agr = asp.add_parser("revoke"); agr.add_argument("grant"); agr.add_argument("--operator", required=True); agr.add_argument("--auth", required=True); agr.add_argument("--protected-root", action="store_true"); agr.add_argument("--expected-head")

    ap = sp.add_parser("approve"); ap.add_argument("proposal"); ap.add_argument("--operator", required=True); ap.add_argument("--auth")
    applyp = sp.add_parser("apply"); applyp.add_argument("proposal"); applyp.add_argument("--approval", required=True)

    proposal = sp.add_parser("proposal"); _add_list_show(proposal, "proposal")
    approval = sp.add_parser("approval"); _add_list_show(approval, "approval")
    candidate = sp.add_parser("candidate"); _add_list_show(candidate, "candidate")

    act = sp.add_parser("activation"); actsp = act.add_subparsers(dest="verb", required=True)
    actrun = actsp.add_parser("run"); actrun.add_argument("--role", required=True); actrun.add_argument("--scope", required=True); actrun.add_argument("--invocation-id", required=True); actrun.add_argument("--source", required=True)

    rec = sp.add_parser("reconciliation"); recsp = rec.add_subparsers(dest="verb", required=True)
    rr = recsp.add_parser("run"); rr.add_argument("candidate"); rr.add_argument("--activation", required=True); rr.add_argument("--assessment", required=True)
    rs = recsp.add_parser("show"); rs.add_argument("reference")

    adm = sp.add_parser("admission"); admsp = adm.add_subparsers(dest="verb", required=True)
    ar = admsp.add_parser("run"); ar.add_argument("candidate"); ar.add_argument("--activation", required=True); ar.add_argument("--plan", required=True)
    ash2 = admsp.add_parser("show"); ash2.add_argument("reference")

    history = sp.add_parser("history"); hsp = history.add_subparsers(dest="verb", required=False)
    hs = hsp.add_parser("show"); hs.add_argument("event")

    op = sp.add_parser("operator"); osp = op.add_subparsers(dest="verb", required=True)
    for verb in ("add", "update", "disable", "enable"):
        q = osp.add_parser(verb); q.add_argument("operator"); q.add_argument("--capability", action="append", dest="capabilities")
    tr = osp.add_parser("transfer-root"); tr.add_argument("operator")

    role = sp.add_parser("role"); rsp = role.add_subparsers(dest="verb", required=True)
    rsub = rsp.add_parser("submission"); rssp = rsub.add_subparsers(dest="submission_verb", required=True)
    rssp.add_parser("list")
    rshow = rssp.add_parser("show"); rshow.add_argument("submission")
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
        if not child.is_dir() or child.is_symlink():
            continue
        ref = "workflow:" + child.name
        view = _workflow_view(store, ref, 0)
        if include_all or view["lifecycle"] == "OPEN":
            values.append(view)
    return values


def _list_grants(store: Path) -> list[dict[str, Any]]:
    return [_grant_view(store, ref, 0) for ref in shared.list_grants(store)]


def _candidate_path(root: Path, value: str) -> Path:
    if value.startswith("candidate:"):
        hits = [x for x in _inventory(root, "candidate") if x["reference"] == value]
        if len(hits) != 1:
            raise ValueError("candidate reference is missing or ambiguous")
        return root / hits[0]["path"]
    return Path(value)


def _resolve_artifact_path(root: Path, value: str, kind: str) -> Path:
    if value.startswith(kind + ":"):
        hits = [x for x in _inventory(root, kind) if x["reference"] == value]
        if len(hits) != 1:
            raise ValueError(f"{kind} reference is missing or ambiguous")
        return root / hits[0]["path"]
    return Path(value)


def _universal_apply(root: Path, grant_store: Path, proposal: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    domain = proposal.get("domain")
    operation = proposal.get("operation")
    if domain == roles.DOMAIN and operation == roles.OPERATION:
        return shared.g4.apply_role_submission_with_authority(root, grant_store, proposal, approval)
    if domain == operators.DOMAIN:
        if operation == "INITIALIZE_ROOT":
            return operators.apply_initial_operator(root, proposal, approval)
        if operation == operator_management.ROOT_TRANSFER_OPERATION:
            return operator_management.apply_root_transfer(root, proposal, approval)
        if operation in operator_management.ORDINARY_OPERATIONS:
            return shared.g4.apply_operator_change_with_authority(root, grant_store, proposal, approval)
    if domain == steward_authorization.DOMAIN:
        return steward_authorization.apply_authorization_change(root, proposal, approval)
    if domain == recovery.DOMAIN and operation == recovery.OPERATION:
        return recovery.apply_recovery(root, proposal, approval)
    return mutation.operation_result("FAIL", "UNSUPPORTED_APPLY_OPERATION", f"{domain}/{operation}")


def _history(root: Path, wf_store: Path, grant_store: Path) -> dict[str, Any]:
    domains: list[dict[str, Any]] = []
    wf_base = wf_store / "workflows"
    if wf_base.exists():
        for child in sorted(wf_base.iterdir()):
            if child.is_dir() and not child.is_symlink():
                ref = "workflow:" + child.name
                events = workflows.read_events(wf_store, ref)
                if events:
                    domains.append({"history": ref, "ordering": "domain-local", "events": events})
    grant_base = grant_store / "authority-grants"
    if grant_base.exists():
        for child in sorted(grant_base.iterdir()):
            if child.is_dir() and not child.is_symlink():
                ref = "authority-grant:" + child.name
                events = grants.read_events(grant_store, ref)
                if events:
                    domains.append({"history": ref, "ordering": "domain-local", "events": events})
    for path in _json_files(root):
        if path.parent.name != "events":
            continue
        try:
            value = mutation.load_json(path)
        except Exception:
            continue
        if isinstance(value, dict) and value.get("contract") in {mutation.EVENT_CONTRACT, recovery.RECORD_CONTRACT}:
            key = path.parent.relative_to(root).as_posix()
            bucket = next((x for x in domains if x["history"] == key), None)
            if bucket is None:
                bucket = {"history": key, "ordering": "domain-local", "events": []}
                domains.append(bucket)
            bucket["events"].append(value)
    return {"ordering": "domain-local-only", "global_sequence": None, "histories": domains}


def execute(ns: argparse.Namespace, cwd: Path | None = None) -> dict[str, Any]:
    root = discover_project(cwd or Path.cwd(), ns.project)
    depth = getattr(ns, "depth", 0)
    if ns.quiet and depth != 0:
        return _result("FAIL", "QUIET_DEPTH_CONFLICT", project_root=str(root))
    wf_store, grant_store = _stores(root)
    try:
        if ns.resource == "status": value = _legacy(root, "STATUS", {})
        elif ns.resource == "repair": value = _legacy(root, "REPAIR_ALL", {})
        elif ns.resource == "canon" and ns.verb == "verify": value = _legacy(root, "VERIFY_STORAGE", {})
        elif ns.resource == "show": value = inspect_typed(root, ns.reference, ns.depth)
        elif ns.resource == "workflow" and ns.verb == "list": value = _list_workflows(wf_store, ns.all_workflows)
        elif ns.resource == "workflow" and ns.verb == "show": value = _workflow_view(wf_store, ns.workflow, ns.depth)
        elif ns.resource == "workflow" and ns.verb == "create": value = workflows.create_workflow(wf_store, _json(ns.definition))
        elif ns.resource == "workflow" and ns.verb == "continue": value = shared.advance_auto_proposal(root, wf_store, grant_store, ns.workflow, _json(ns.proposal), grant_refs=ns.grants)
        elif ns.resource == "workflow" and ns.verb == "cancel": value = workflows.cancel_workflow(wf_store, ns.workflow, ns.operator, _json(ns.auth), protected_root=ns.protected_root)
        elif ns.resource == "workflow" and ns.verb == "revise": value = workflows.revise_workflow(wf_store, ns.workflow, _json(ns.definition), expected_normative_head=ns.expected_head)
        elif ns.resource == "workflow" and ns.verb == "acknowledge": value = workflows.acknowledge_materiality(wf_store, ns.workflow, ns.event, ns.operator, _json(ns.auth), protected_root=ns.protected_root)
        elif ns.resource == "authority-grant" and ns.verb == "list": value = _list_grants(grant_store)
        elif ns.resource == "authority-grant" and ns.verb == "show": value = _grant_view(grant_store, ns.grant, ns.depth)
        elif ns.resource == "authority-grant" and ns.verb == "create":
            if not ns.workflow_scope_confirmed:
                return _result("FAIL", "GRANT_WORKFLOW_SCOPE_CONFIRMATION_REQUIRED", project_root=str(root))
            value = shared.g4.create_authorized_grant(root, grant_store, _json(ns.definition), workflow_contains_grant_scope=True)
        elif ns.resource == "authority-grant" and ns.verb == "revoke": value = grants.revoke_grant(grant_store, ns.grant, ns.operator, _json(ns.auth), protected_root=ns.protected_root, expected_normative_head=ns.expected_head)
        elif ns.resource == "approve":
            proposal = _json(ns.proposal); descriptor = shared._descriptor(root, proposal); rv = mutation.revalidate_proposal(proposal, descriptor["current_state"])
            if rv["classification"] != "APPLICABLE":
                return _result("STOPPED", f"PROPOSAL_{rv['classification']}", project_root=str(root), revalidation=rv)
            value = mutation.make_direct_approval_v2(proposal, ns.operator, _json(ns.auth) if ns.auth else None)
        elif ns.resource == "apply": value = _universal_apply(root, grant_store, _json(ns.proposal), _json(ns.approval))
        elif ns.resource in {"proposal", "approval", "candidate"}:
            kind = ns.resource
            value = _inventory(root, kind) if ns.verb == "list" else inspect_typed(root, getattr(ns, kind), 0)
        elif ns.resource == "activation" and ns.verb == "run":
            value = activation_fast_path.run_activation(root, ns.role, ns.scope, ns.invocation_id, ns.source)
            validation = value["validation"]
            return _result(validation["status"], validation["outcome"], project_root=str(root), value=value)
        elif ns.resource == "reconciliation" and ns.verb == "run": value = reconciliation.reconcile_candidate(root, _candidate_path(root, ns.candidate), _json(ns.activation), _json(ns.assessment))
        elif ns.resource == "reconciliation" and ns.verb == "show":
            ref = ns.reference
            if ref.startswith("candidate:"):
                cand = inspect_typed(root, ref, 0); digest_hex = ref.split(":", 1)[1]; path = root / "project-knowledge" / "reconciliation" / "dispositions" / f"{digest_hex}.json"
                value = mutation.load_json(path)
            else: value = inspect_typed(root, ref, 0)
        elif ns.resource == "admission" and ns.verb == "run":
            cand = _candidate_path(root, ns.candidate); candidate_obj = mutation.load_json(cand); candidate_hex = mutation.digest(candidate_obj).split(":", 1)[1]
            disposition_path = root / "project-knowledge" / "reconciliation" / "dispositions" / f"{candidate_hex}.json"
            value = admission.admit(root, disposition_path, _json(ns.activation), _json(ns.plan))
        elif ns.resource == "admission" and ns.verb == "show":
            ref = ns.reference
            if ref.startswith("candidate:"):
                digest_hex = ref.split(":", 1)[1]; value = mutation.load_json(root / "project-knowledge" / "admission" / "receipts" / f"{digest_hex}.json")
            else: value = inspect_typed(root, ref, 0)
        elif ns.resource == "history": value = inspect_typed(root, ns.event, 0) if ns.verb == "show" else _history(root, wf_store, grant_store)
        elif ns.resource == "operator":
            opmap = {"add": "ADD_OPERATOR", "update": "UPDATE_CAPABILITIES", "disable": "DISABLE_OPERATOR", "enable": "REENABLE_OPERATOR"}
            if ns.verb == "transfer-root": value = _legacy(root, "ROOT_TRANSFER_PLAN", {"to_operator_id": ns.operator})
            else:
                args = {"operation": opmap[ns.verb], "target_operator_id": ns.operator}
                if ns.verb in {"add", "update"}: args["capabilities"] = ns.capabilities or []
                value = _legacy(root, "OPERATOR_PLAN", args)
        elif ns.resource == "role" and ns.verb == "submission" and ns.submission_verb == "list": value = _inventory(root, "submission")
        elif ns.resource == "role" and ns.verb == "submission" and ns.submission_verb == "show": value = inspect_typed(root, ns.submission, 0)
        elif ns.resource == "role" and ns.verb == "submission" and ns.submission_verb == "create":
            submission = _json(ns.submission)
            if ns.snapshot: submission["mode"] = "snapshot"
            value = _legacy(root, "ROLE_SUBMISSION_PLAN", {"submission": submission})
        elif ns.resource == "steward":
            mapping = {"set-reconciliation": ("SET", "semantic_reconciliation", ns.role), "clear-reconciliation": ("CLEAR", "semantic_reconciliation", None), "set-admission": ("SET", "admission", ns.role), "clear-admission": ("CLEAR", "admission", None)}
            operation, scope, role_id = mapping[ns.verb]; args = {"operation": operation, "scope": scope}
            if role_id is not None: args["role_id"] = role_id
            value = _legacy(root, "STEWARD_AUTH_PLAN", args)
        else: return _result("FAIL", "UNIMPLEMENTED_CLI_ROUTE", project_root=str(root))
        return _result("PASS", "OK", project_root=str(root), value=value)
    except Exception as exc:
        return _result("FAIL", getattr(exc, "code", "CLI_ERROR"), project_root=str(root), detail=getattr(exc, "detail", str(exc)))


def render(result: dict[str, Any], ns: argparse.Namespace) -> str:
    if ns.quiet:
        value = result.get("value")
        if isinstance(value, dict):
            for key in ("reference", "workflow", "grant", "proposal_digest", "disposition_digest", "receipt_digest", "activation_digest"):
                if isinstance(value.get(key), str): return value[key]
        if isinstance(value, str): return value
        return result.get("outcome", "")
    if ns.json: return json.dumps(result, sort_keys=True, separators=(",", ":"))
    return json.dumps(result, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    p = parser(); ns = p.parse_args(argv); result = execute(ns); print(render(result, ns))
    return 0 if result["status"] in {"PASS", "STOPPED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())