from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

import context_packaging.prepare_integration as prepare


ROOT = Path(__file__).resolve().parents[1]
REJECTED_G9_CANDIDATE = "ec410a501e7db051f59eb2fb373c30da150bd81a"
GOVERNING_PLAN_COMMIT = "b435dff827b745d711a5c5a297587a0c4359bed1"
GOVERNING_PLAN_BLOB = "eae54b9e2c0618faec61acf2f9e4acd942ec063d"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


G4 = _load_module(
    "p10_g4_helpers_for_g9_remediation",
    ROOT / "tests/test_context_packaging_production_integration_p10_g4.py",
)


def _raw(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _exact_runtime() -> bool:
    return (
        sys.implementation.name == "cpython"
        and sys.version_info[:3] == (3, 12, 0)
        and sys.implementation.cache_tag == "cpython-312"
    )


def test_pi09_frozen_production_consumer_constants_are_exact() -> None:
    assert prepare.PRODUCTION_CONSUMER_CONTRACT == "reasoning-distiller-invocation/2"
    assert prepare.PRODUCTION_CONSUMER_ID == "rd-distill"


@pytest.mark.skipif(not _exact_runtime(), reason="P10 G9 remediation exact runtime is CPython 3.12.0/cpython-312")
@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [
        ("consumer_contract", "reasoning-distiller-invocation/99"),
        ("consumer_id", "not-rd-distill"),
    ],
)
def test_pi09_mutually_consistent_wrong_consumer_fails_preflight(tmp_path, field, wrong_value):
    project, installed_root = G4._install_candidate(tmp_path)
    request, _, _ = G4._request_for(project)

    pack_path = project / "artifacts/pack.json"
    eligibility_path = project / "artifacts/eligibility.json"
    pack = json.loads(pack_path.read_bytes())
    eligibility = json.loads(eligibility_path.read_bytes())

    assert pack["eligibility"]["consumer_contract"] == "reasoning-distiller-invocation/2"
    assert pack["eligibility"]["consumer_id"] == "rd-distill"
    assert eligibility["consumer"]["consumer_contract"] == "reasoning-distiller-invocation/2"
    assert eligibility["consumer"]["consumer_id"] == "rd-distill"

    pack["eligibility"][field] = wrong_value
    eligibility["consumer"][field] = wrong_value
    pack_raw = _raw(pack)
    eligibility_raw = _raw(eligibility)
    pack_path.write_bytes(pack_raw)
    eligibility_path.write_bytes(eligibility_raw)

    mutated = copy.deepcopy(request)
    mutated["context"]["pack"]["raw_sha256"] = _sha(pack_raw)
    mutated["context"]["profile_eligibility"]["raw_sha256"] = _sha(eligibility_raw)

    with pytest.raises(prepare.PrepareFailure) as exc_info:
        prepare.prepare_invocation_v2(_raw(mutated), cwd=tmp_path, installed_root=installed_root)

    failure = exc_info.value
    assert failure.stage == "preflight"
    assert failure.exit_code == prepare.EXIT_PREFLIGHT == 2
    assert failure.reason_code == "PROFILE_ELIGIBILITY_MISMATCH"
    assert not (project / "out/prepared.json").exists()
    assert not (project / "out/registry.json").exists()
