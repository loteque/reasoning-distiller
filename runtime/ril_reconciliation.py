#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from ril_activation import validate_activation
from ril_mutation import ContractError, canonical_json_bytes, digest, load_json

ASSESSMENT_CONTRACT = "reasoning-distiller-reconciliation-assessment/1"
DISPOSITION_CONTRACT = "reasoning-distiller-reconciliation-disposition/1"
RESULT_CONTRACT = "reasoning-distiller-reconciliation-result/1"
SCOPE = "semantic_reconciliation"

_ALLOWED = {
    "COMPATIBLE": {"RECOMMEND", "DEFER"},
    "INCOMPATIBLE": {"DO_NOT_RECOMMEND"},
    "REVISION_REQUIRED": {"DEFER"},
}


def _result(status: str, outcome: str, detail: str | None = None, **extra: Any) -> dict[str, Any]:
    value: dict[str, Any] = {"contract": RESULT_CONTRACT, "status": status, "outcome": outcome}
    if detail:
        value["detail"] = detail
    value.update(extra)
    return value


def validate_assessment(value: Any) -> dict[str, Any]:
    required = {"contract", "semantic_status", "admission_recommendation", "rationale"}
    if not isinstance(value, dict) or set(value) != required:
        raise ContractError("INVALID_RECONCILIATION_ASSESSMENT", "assessment fields do not match contract")
    if value["contract"] != ASSESSMENT_CONTRACT:
        raise ContractError("INVALID_RECONCILIATION_ASSESSMENT", "unsupported assessment contract")
    status = value["semantic_status"]
    recommendation = value["admission_recommendation"]
    rationale = value["rationale"]
    if status not in _ALLOWED:
        raise ContractError("INVALID_SEMANTIC_STATUS", str(status))
    if recommendation not in _ALLOWED[status]:
        raise ContractError("INVALID_ADMISSION_RECOMMENDATION", f"{status}/{recommendation}")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ContractError("RATIONALE_REQUIRED", "rationale must be a non-empty string")
    normalized = {
        "contract": ASSESSMENT_CONTRACT,
        "semantic_status": status,
        "admission_recommendation": recommendation,
        "rationale": rationale.strip(),
    }
    canonical_json_bytes(normalized)
    return normalized


def _candidate(project_root: Path, candidate_path: Path) -> tuple[dict[str, Any], str, str]:
    root = project_root.resolve()
    submissions = (root / "project-knowledge" / "submissions").resolve(strict=False)
    path = candidate_path if candidate_path.is_absolute() else root / candidate_path
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ContractError("CANDIDATE_NOT_FOUND", str(candidate_path)) from exc
    try:
        resolved.relative_to(submissions)
    except ValueError as exc:
        raise ContractError("CANDIDATE_PATH_OUTSIDE_SUBMISSIONS", str(candidate_path)) from exc
    if resolved.is_symlink() or not resolved.is_file():
        raise ContractError("INVALID_CANDIDATE_PATH", str(candidate_path))
    candidate = load_json(resolved)
    rel = resolved.relative_to(root).as_posix()
    return candidate, digest(candidate), rel


def _persist_immutable(path: Path, artifact: dict[str, Any], conflict_code: str) -> str:
    data = canonical_json_bytes(artifact)
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise ContractError(conflict_code, str(path))
        if path.read_bytes() != data:
            raise ContractError(conflict_code, str(path))
        return "NO_CHANGE"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise ContractError(conflict_code, str(path.parent))
    try:
        with open(path, "xb") as handle:
            handle.write(data)
            handle.flush()
    except FileExistsError:
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ContractError(conflict_code, str(path))
        return "NO_CHANGE"
    return "CREATED"


def reconcile_candidate(
    project_root: Path,
    candidate_path: Path,
    activation: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    try:
        candidate, candidate_digest, candidate_rel = _candidate(project_root, candidate_path)
        normalized_assessment = validate_assessment(assessment)

        activation_result = validate_activation(project_root, SCOPE, activation)
        if activation_result.get("status") != "PASS":
            return _result(
                "FAIL",
                activation_result.get("outcome", "ACTIVATION_REJECTED"),
                activation_result.get("detail"),
            )

        activation_digest = digest(activation)
        role_id = activation_result["role_id"]
        invocation_id = activation_result["invocation_id"]
        disposition = {
            "contract": DISPOSITION_CONTRACT,
            "candidate_digest": candidate_digest,
            "candidate_path": candidate_rel,
            "role_id": role_id,
            "invocation_id": invocation_id,
            "activation_digest": activation_digest,
            "assessment": normalized_assessment,
        }
        canonical_json_bytes(disposition)

        base = project_root / "project-knowledge" / "reconciliation"
        activation_path = base / "activation-evidence" / f"{activation_digest.split(':', 1)[1]}.json"
        disposition_path = base / "dispositions" / f"{candidate_digest.split(':', 1)[1]}.json"

        if disposition_path.exists():
            if disposition_path.is_symlink() or not disposition_path.is_file():
                raise ContractError("DISPOSITION_CONFLICT", str(disposition_path))
            existing = disposition_path.read_bytes()
            expected = canonical_json_bytes(disposition)
            if existing != expected:
                raise ContractError("DISPOSITION_CONFLICT", "candidate already has a different reconciliation disposition")
            _persist_immutable(activation_path, activation, "ACTIVATION_EVIDENCE_CONFLICT")
            return _result(
                "PASS",
                "NO_CHANGE",
                candidate_digest=candidate_digest,
                disposition_digest=digest(disposition),
                disposition_path=disposition_path.relative_to(project_root).as_posix(),
            )

        _persist_immutable(activation_path, activation, "ACTIVATION_EVIDENCE_CONFLICT")
        _persist_immutable(disposition_path, disposition, "DISPOSITION_CONFLICT")
        return _result(
            "PASS",
            "RECONCILED",
            candidate_digest=candidate_digest,
            disposition_digest=digest(disposition),
            disposition_path=disposition_path.relative_to(project_root).as_posix(),
            semantic_status=normalized_assessment["semantic_status"],
            admission_recommendation=normalized_assessment["admission_recommendation"],
        )
    except ContractError as exc:
        return _result("FAIL", exc.code, exc.detail)


if __name__ == "__main__":
    import json
    print(json.dumps(_result("FAIL", "LIBRARY_PRIMITIVE", "R12 is exposed as deterministic functions; public ril UX is not implemented yet"), sort_keys=True, separators=(",", ":")))
