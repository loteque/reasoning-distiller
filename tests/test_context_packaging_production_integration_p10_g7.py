from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import context_packaging.prepare_integration as prepare


ROOT = Path(__file__).resolve().parents[1]
G6_CANDIDATE = "ed04d9f711d2c5298b3b86ca5bf5ea6937d4082a"
G6_ENGINEER_EVIDENCE = "60c609a44ea74869aea81bcd9cbe280ac7126abb"
G6_EVIDENCE_RUN = "32908277963"
COORDINATION_REVISION = "80b6e89ad2efe84b088ca06b908a257c449fac15"
GOVERNING_PLAN_COMMIT = "b435dff827b745d711a5c5a297587a0c4359bed1"
GOVERNING_PLAN_BLOB = "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
HISTORICAL_VERSION = "0.5.3"
HISTORICAL_COMMIT = "1d781baf8be8f21d25eb85ddc340f1d2bc93922b"
HISTORICAL_MANIFEST_ASSET_SHA256 = "5c9448c6e6acc6f3925aae173870f4d6e8a237035c0e870637ef8d7499765044"
HISTORICAL_ARCHIVE_SHA256 = "5d1751f1910e13ba5b3e9787a6188a1b995e0ac5b88bbec9c2ac935e9d33ef67"
CURRENT_TEST_VERSION = "0.6.0"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = _load_module("p10_g7_package_builder", ROOT / "packaging/build_release_package.py")
installer = _load_module("p10_g7_installer", ROOT / "packaging/rd_install.py")
G4 = _load_module(
    "p10_g4_helpers_for_g7",
    ROOT / "tests/test_context_packaging_production_integration_p10_g4.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exact_runtime() -> bool:
    return (
        sys.implementation.name == "cpython"
        and sys.version_info[:3] == (3, 12, 0)
        and sys.implementation.cache_tag == "cpython-312"
    )


def _candidate_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    sha = completed.stdout.strip()
    assert len(sha) == 40 and all(ch in "0123456789abcdef" for ch in sha)
    return sha


def _historical_release_assets() -> tuple[Path, Path, dict]:
    manifest_text = os.environ.get("P10_G7_V053_MANIFEST")
    archive_text = os.environ.get("P10_G7_V053_ARCHIVE")
    if not manifest_text or not archive_text:
        pytest.skip("G7 true-downgrade evidence requires pinned v0.5.3 release assets")
    manifest_path = Path(manifest_text).resolve()
    archive_path = Path(archive_text).resolve()
    assert manifest_path.is_file()
    assert archive_path.is_file()
    assert _sha256(manifest_path) == HISTORICAL_MANIFEST_ASSET_SHA256
    assert _sha256(archive_path) == HISTORICAL_ARCHIVE_SHA256
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["contract"] == "reasoning-distiller-install-package/1"
    assert manifest["version"] == HISTORICAL_VERSION
    assert manifest["source_commit"] == HISTORICAL_COMMIT
    assert manifest["transport_sha256"] == HISTORICAL_ARCHIVE_SHA256
    assert manifest["managed_roots"] == [
        "admission",
        "agents",
        "backends",
        "protocols",
        "runtime",
        "schemas",
        "validators",
    ]
    return manifest_path, archive_path, manifest


def _build_and_install_current(tmp_path: Path) -> tuple[Path, Path, dict, dict]:
    candidate_sha = _candidate_sha()
    release = builder.build(
        CURRENT_TEST_VERSION,
        candidate_sha,
        tmp_path / "current-release",
        root=ROOT,
    )
    current_manifest = json.loads(Path(release["manifest"]).read_text(encoding="utf-8"))
    assert current_manifest["source_commit"] == candidate_sha
    assert current_manifest["managed_roots"] == [
        "admission",
        "agents",
        "backends",
        "context_packaging",
        "protocols",
        "runtime",
        "schemas",
        "validators",
    ]
    project = tmp_path / "project"
    project.mkdir()
    result = installer.install(
        release["archive"],
        release["manifest"],
        release["transport_sha256"],
        project,
    )
    assert result["status"] == "PASS"
    assert result["version"] == CURRENT_TEST_VERSION
    return project, project / ".reasoning-distiller", release, current_manifest


def _legacy_request(project: Path, name: str) -> Path:
    evidence = project / f"{name}-evidence.txt"
    evidence.write_text("P10 G7 legacy contract remains operable.\n", encoding="utf-8")
    digest = "sha256:" + hashlib.sha256(evidence.read_bytes()).hexdigest()
    output = project / f"{name}-out"
    output.mkdir()
    request = {
        "contract": "reasoning-distiller-invocation/1",
        "invocation_id": f"p10-g7-{name}",
        "created_at": "2026-08-25T17:00:00-07:00",
        "project_root": ".",
        "evidence": [
            {
                "source_id": "src:g7:legacy",
                "type": "repository_file",
                "locator": evidence.name,
                "digest": digest,
            }
        ],
        "source_registry": [
            {
                "source_id": "src:g7:legacy",
                "type": "repository_file",
                "locator": evidence.name,
                "digest": digest,
            }
        ],
        "source_context": {"summary": "P10 G7 legacy compatibility", "refs": ["P10-G7"]},
        "output": {
            "raw_candidate_path": f"{output.name}/raw.json",
            "submission_path": f"{output.name}/submission.json",
        },
    }
    request_path = project / f"{name}-request.json"
    request_path.write_text(json.dumps(request, sort_keys=True), encoding="utf-8")
    return request_path


def _run_runtime(runtime: Path, args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(runtime), *args],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _manifest_inventory(manifest: dict) -> dict[str, dict]:
    return {item["path"]: item for item in manifest["files"]}


def _actual_managed_paths(installed_root: Path, managed_roots: list[str]) -> set[str]:
    actual: set[str] = set()
    for root in managed_roots:
        base = installed_root / root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_dir() and not path.is_symlink():
                continue
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            actual.add(path.relative_to(installed_root).as_posix())
    return actual


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G7 supported runtime is exact CPython 3.12.0/cpython-312",
)
def test_p10_g7_explicit_v2_selection_preserves_v1_and_contract_rollback(tmp_path):
    project, installed_root, _, _ = _build_and_install_current(tmp_path)
    runtime = installed_root / "runtime/rd_distill.py"
    installed_manifest = installed_root / ".installation/MANIFEST.json"
    manifest_before = installed_manifest.read_bytes()
    runtime_before = _sha256(runtime)

    legacy_request = _legacy_request(project, "legacy-current")
    before_bundle = project / "legacy-before-bundle.json"
    before = _run_runtime(
        runtime,
        ["prepare", "--request", str(legacy_request), "--bundle-out", str(before_bundle)],
        cwd=project,
    )
    assert before.returncode == 0, before.stderr.decode()
    legacy_before = json.loads(before_bundle.read_text(encoding="utf-8"))
    assert legacy_before["contract"] == "reasoning-distiller-activation-bundle/1"

    _, _, v2_request_path = G4._request_for(project)
    v2 = _run_runtime(
        runtime,
        ["prepare", "--request", str(v2_request_path)],
        cwd=tmp_path,
    )
    assert v2.returncode == 0, v2.stderr.decode()
    v2_bundle = json.loads(v2.stdout)
    assert v2_bundle["contract"] == "reasoning-distiller-activation-bundle/2"

    after_bundle = project / "legacy-after-bundle.json"
    after = _run_runtime(
        runtime,
        ["prepare", "--request", str(legacy_request), "--bundle-out", str(after_bundle)],
        cwd=project,
    )
    assert after.returncode == 0, after.stderr.decode()
    assert after_bundle.read_bytes() == before_bundle.read_bytes()
    assert installed_manifest.read_bytes() == manifest_before
    assert _sha256(runtime) == runtime_before


@pytest.mark.skipif(
    _exact_runtime(),
    reason="unsupported-runtime pressure runs only outside exact CPython 3.12.0",
)
def test_p10_g7_v2_rejects_actual_unsupported_cpython_runtime():
    if not (
        sys.implementation.name == "cpython"
        and (
            (sys.version_info[:2] == (3, 12) and sys.version_info.micro != 0)
            or sys.version_info[:2] == (3, 13)
        )
    ):
        pytest.skip("G7 pressure case is CPython 3.12.1+ or 3.13.x")
    with pytest.raises(prepare.PrepareFailure) as caught:
        prepare._verify_runtime()
    assert caught.value.stage == "preflight"
    assert caught.value.reason_code == "RENDERER_RUNTIME_INCOMPATIBLE"
    assert caught.value.exit_code == prepare.EXIT_PREFLIGHT


@pytest.mark.skipif(
    not _exact_runtime(),
    reason="P10 G7 downgrade evidence is certified at CPython 3.12.0/cpython-312",
)
def test_p10_g7_true_v053_downgrade_restores_historical_manifest_and_bytes(tmp_path):
    historical_manifest_path, historical_archive, historical_manifest = _historical_release_assets()
    project, installed_root, _, current_manifest = _build_and_install_current(tmp_path)

    current_inventory = _manifest_inventory(current_manifest)
    historical_inventory = _manifest_inventory(historical_manifest)
    current_only = set(current_inventory) - set(historical_inventory)
    changed_shared = {
        path
        for path in set(current_inventory) & set(historical_inventory)
        if current_inventory[path]["sha256"] != historical_inventory[path]["sha256"]
    }
    assert current_only
    assert changed_shared
    assert any(path.startswith("context_packaging/") for path in current_only)
    assert "runtime/rd_distill.py" in changed_shared

    blocked = installer.plan_installation_transition(
        historical_manifest_path,
        project,
        allow_downgrade=False,
    )
    assert blocked["status"] == "PASS"
    assert blocked["outcome"] == "DOWNGRADE_REQUIRES_AUTHORIZATION"
    assert blocked["previous_version"] == CURRENT_TEST_VERSION

    downgrade = installer.install(
        historical_archive,
        historical_manifest_path,
        HISTORICAL_ARCHIVE_SHA256,
        project,
        allow_downgrade=True,
    )
    assert downgrade["status"] == "PASS"
    assert downgrade["version"] == HISTORICAL_VERSION
    assert downgrade["previous_version"] == CURRENT_TEST_VERSION

    stored_manifest_path = installed_root / ".installation/MANIFEST.json"
    stored_manifest = json.loads(stored_manifest_path.read_text(encoding="utf-8"))
    assert stored_manifest == historical_manifest
    installation = json.loads(
        (installed_root / ".installation/INSTALLATION.json").read_text(encoding="utf-8")
    )
    assert installation["version"] == HISTORICAL_VERSION
    assert installation["source_commit"] == HISTORICAL_COMMIT

    actual_paths = _actual_managed_paths(installed_root, historical_manifest["managed_roots"])
    assert actual_paths == set(historical_inventory)
    assert current_only.isdisjoint(actual_paths)
    assert not (installed_root / "context_packaging").exists()
    assert not (project / ".rd-install-transaction.json").exists()
    assert not (project / ".rd-install-backup").exists()

    for path, item in historical_inventory.items():
        restored = installed_root / path
        assert restored.is_file() and not restored.is_symlink()
        assert _sha256(restored) == item["sha256"]
    for path in changed_shared:
        assert _sha256(installed_root / path) == historical_inventory[path]["sha256"]
        assert historical_inventory[path]["sha256"] != current_inventory[path]["sha256"]

    historical_runtime = installed_root / "runtime/rd_distill.py"
    legacy_request = _legacy_request(project, "legacy-downgraded")
    legacy_bundle = project / "legacy-downgraded-bundle.json"
    legacy = _run_runtime(
        historical_runtime,
        ["prepare", "--request", str(legacy_request), "--bundle-out", str(legacy_bundle)],
        cwd=project,
    )
    assert legacy.returncode == 0, legacy.stderr.decode()
    assert json.loads(legacy_bundle.read_text(encoding="utf-8"))["contract"] == "reasoning-distiller-activation-bundle/1"

    v2_shape = json.loads(legacy_request.read_text(encoding="utf-8"))
    v2_shape["contract"] = "reasoning-distiller-invocation/2"
    v2_request = project / "historical-v2-request.json"
    v2_request.write_text(json.dumps(v2_shape, sort_keys=True), encoding="utf-8")
    rejected = _run_runtime(
        historical_runtime,
        ["prepare", "--request", str(v2_request), "--bundle-out", str(project / "should-not-exist.json")],
        cwd=project,
    )
    assert rejected.returncode == 2
    rejection = json.loads(rejected.stdout)
    assert rejection["contract"] == "reasoning-distiller-invocation-result/1"
    assert rejection["status"] == "FAIL"
    assert rejection["stage"] == "preflight"
    assert rejection["reason_code"] == "UNSUPPORTED_CONTRACT"
    assert not (project / "should-not-exist.json").exists()


def test_p10_g7_is_bound_to_exact_g6_and_does_not_create_rollback_api():
    assert G6_CANDIDATE == "ed04d9f711d2c5298b3b86ca5bf5ea6937d4082a"
    assert G6_ENGINEER_EVIDENCE == "60c609a44ea74869aea81bcd9cbe280ac7126abb"
    assert G6_EVIDENCE_RUN == "32908277963"
    assert COORDINATION_REVISION == "80b6e89ad2efe84b088ca06b908a257c449fac15"
    assert GOVERNING_PLAN_COMMIT == "b435dff827b745d711a5c5a297587a0c4359bed1"
    assert GOVERNING_PLAN_BLOB == "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
    assert HISTORICAL_COMMIT == "1d781baf8be8f21d25eb85ddc340f1d2bc93922b"
    assert not hasattr(prepare, "rollback")
    assert not hasattr(prepare, "downgrade")
    assert not hasattr(installer, "rollback")
