#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

RESULT_CONTRACT = "reasoning-distiller-steward-setup-result/1"
AUTH_CONTRACT = "reasoning-distiller-steward-authorization/1"
PROJECT_CONTRACT = "reasoning-distiller-project/1"
CONFIRM = "AUTHORIZE_STEWARD"
ALLOWED_SCOPES = {"semantic_reconciliation", "admission"}
AUTH_REL = Path("project-knowledge/governance/steward-authorization.json")


def emit(value: dict) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def fail(code: str, detail: str) -> tuple[int, dict]:
    return 2, {"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": code, "detail": detail}


def target_root(raw: str) -> Path:
    target = Path(raw).expanduser().resolve(strict=True)
    if not target.is_dir():
        raise ValueError("target is not a directory")
    return target


def validate_preconditions(target: Path) -> tuple[int, dict] | None:
    install = target / ".reasoning-distiller"
    if not install.is_dir() or install.is_symlink():
        return fail("INSTALLATION_MISSING", ".reasoning-distiller installation is missing or invalid")
    project = target / "project-knowledge/project.json"
    if not project.is_file() or project.is_symlink():
        return fail("PROJECT_NOT_BOOTSTRAPPED", "project-knowledge/project.json is missing or invalid")
    try:
        data = json.loads(project.read_text(encoding="utf-8"))
    except Exception:
        return fail("PROJECT_NOT_BOOTSTRAPPED", "project-knowledge/project.json is not valid JSON")
    if data.get("contract") != PROJECT_CONTRACT:
        return fail("PROJECT_NOT_BOOTSTRAPPED", "project contract is not reasoning-distiller-project/1")
    return None


def proposed(holder: str, scopes: list[str]) -> tuple[int, dict] | dict:
    holder = holder.strip()
    if not holder:
        return fail("HOLDER_REQUIRED", "authority holder must be supplied explicitly")
    unique = sorted(set(scopes))
    if not unique:
        return fail("SCOPE_REQUIRED", "at least one authority scope must be supplied explicitly")
    unknown = [s for s in unique if s not in ALLOWED_SCOPES]
    if unknown:
        return fail("UNKNOWN_SCOPE", ",".join(unknown))
    return {
        "contract": AUTH_CONTRACT,
        "role": "steward",
        "authority_holder": holder,
        "scopes": unique,
    }


def preflight_path(target: Path) -> tuple[int, dict] | None:
    pk = target / "project-knowledge"
    gov = pk / "governance"
    auth = target / AUTH_REL
    if pk.is_symlink():
        return fail("PATH_CONFLICT", "project-knowledge must not be a symlink")
    if gov.exists() and (not gov.is_dir() or gov.is_symlink()):
        return fail("PATH_CONFLICT", "project-knowledge/governance is not a normal directory")
    if auth.exists() and (not auth.is_file() or auth.is_symlink()):
        return fail("PATH_CONFLICT", f"{AUTH_REL.as_posix()} is not a normal file")
    try:
        auth.parent.resolve(strict=False).relative_to(target)
    except ValueError:
        return fail("PATH_CONFLICT", "authorization path escapes target")
    return None


def run(mode: str, target: Path, holder: str, scopes: list[str], confirmation: str | None) -> tuple[int, dict]:
    problem = validate_preconditions(target)
    if problem:
        return problem
    problem = preflight_path(target)
    if problem:
        return problem
    auth = proposed(holder, scopes)
    if isinstance(auth, tuple):
        return auth

    if mode == "plan":
        return 0, {
            "contract": RESULT_CONTRACT,
            "status": "PASS",
            "outcome": "PLAN",
            "proposed_authorization": auth,
        }

    if confirmation != CONFIRM:
        return fail("CONFIRMATION_REQUIRED", f"apply requires --confirm {CONFIRM}")

    path = target / AUTH_REL
    expected = canonical(auth)
    if path.exists():
        if path.read_bytes() == expected:
            return 0, {
                "contract": RESULT_CONTRACT,
                "status": "PASS",
                "outcome": "ALREADY_AUTHORIZED",
                "authorization_path": AUTH_REL.as_posix(),
            }
        return fail("AUTHORIZATION_CONFLICT", f"{AUTH_REL.as_posix()} already contains a different authorization")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(expected)
    return 0, {
        "contract": RESULT_CONTRACT,
        "status": "PASS",
        "outcome": "CREATED",
        "authorization_path": AUTH_REL.as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or persist explicit project-owned Steward authorization")
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("plan", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--target", required=True)
        p.add_argument("--authority-holder", required=True)
        p.add_argument("--scope", action="append", default=[])
        if name == "apply":
            p.add_argument("--confirm")
    args = parser.parse_args()
    try:
        target = target_root(args.target)
        code, result = run(args.mode, target, args.authority_holder, args.scope, getattr(args, "confirm", None))
        emit(result)
        return code
    except (OSError, ValueError) as exc:
        code, result = fail("TARGET_INVALID", str(exc))
        emit(result)
        return code
    except Exception as exc:
        emit({"contract": RESULT_CONTRACT, "status": "FAIL", "reason_code": "INTERNAL_ERROR", "detail": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
