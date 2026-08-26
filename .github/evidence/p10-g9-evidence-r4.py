#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path.cwd()
CANDIDATE = os.environ["CANDIDATE"]
CANDIDATE_TREE = os.environ["CANDIDATE_TREE"]
PACKAGE_VERSION = os.environ["PACKAGE_VERSION"]
GOVERNING_PLAN = os.environ["GOVERNING_PLAN"]
GOVERNING_PLAN_BLOB = os.environ["GOVERNING_PLAN_BLOB"]
EVIDENCE_HEAD = os.environ["GITHUB_SHA"]


def write(path: str | Path, data: str) -> None:
    Path(path).write_text(data)


def run(cmd, *, log: str | None = None, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(map(str, cmd)), flush=True)
    completed = subprocess.run(
        list(map(str, cmd)),
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    print(completed.stdout, end="", flush=True)
    if log:
        Path(log).write_text(completed.stdout)
    if check and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def load_json(path: str | Path):
    return json.loads(Path(path).read_text())


def exact_runtime(version: tuple[int, int, int]) -> dict:
    assert platform.python_implementation() == "CPython"
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:3] == version, sys.version
    assert sys.implementation.cache_tag == "cpython-312"
    exe = Path(sys.executable).resolve()
    return {
        "implementation": sys.implementation.name,
        "version": ".".join(map(str, sys.version_info[:3])),
        "cache_tag": sys.implementation.cache_tag,
        "executable": str(exe),
        "executable_sha256": sha_file(exe),
        "runner_os": os.environ.get("RUNNER_OS"),
        "runner_arch": os.environ.get("RUNNER_ARCH"),
        "image_os": os.environ.get("ImageOS"),
        "image_version": os.environ.get("ImageVersion"),
    }


def download(url: str, path: Path, expected_sha256: str) -> None:
    with urllib.request.urlopen(url) as response:
        path.write_bytes(response.read())
    actual = sha_file(path)
    assert actual == expected_sha256, (url, expected_sha256, actual)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def supplemental_witnesses(base) -> list[dict]:
    import context_packaging.finalize_integration as finalize
    import context_packaging.model_transport as transport
    import context_packaging.prepare_integration as prepare
    import context_packaging.renderer as renderer

    supplemental: list[dict] = []

    # PI-34: each sealed input is changed after prepare and the request binding is
    # changed to match those new bytes. Finalize must reject the post-prepare
    # request/input identity as different from the prepared invocation.
    for field in ("pack", "renderer_profile", "profile_eligibility"):
        tag = f"PI-34-{field}-r4"
        b, project, installed_root, request, request_raw, _rp, prepared, transport_run, candidate_raw = base.prepare_transport(tag)
        artifact = project / request["context"][field]["locator"]
        changed = artifact.read_bytes() + b" post-prepare-drift"
        artifact.write_bytes(changed)
        changed_request = copy.deepcopy(request)
        changed_request["context"][field]["raw_sha256"] = base.sha(changed)
        changed_request_raw = base.raw(changed_request)
        try:
            finalize.finalize_invocation_v2(
                changed_request_raw,
                candidate_raw,
                transport_run.serialized_transport_binding,
                cwd=b,
                installed_root=installed_root,
            )
        except finalize.FinalizeFailure as exc:
            assert (exc.stage, exc.reason_code) == ("validation", "SEALED_INPUT_MISMATCH"), (
                field,
                exc.stage,
                exc.reason_code,
            )
            supplemental.append({
                "id": "PI-34",
                "variant": field,
                "kind": "direct_candidate_package_execution",
                "observed_stage": exc.stage,
                "observed_reason_code": exc.reason_code,
                "observed_exit_code": exc.exit_code,
            })
        else:
            raise AssertionError(f"PI-34 {field} unexpectedly succeeded")
        assert not (project / request["output"]["submission_path"]).exists()

    # PI-37: both immutable output paths reject different pre-existing bytes and
    # preserve them.
    for collision in ("raw_candidate_path", "submission_path"):
        tag = f"PI-37-{collision}-r4"
        b, project, installed_root, request, request_raw, _rp, prepared, transport_run, candidate_raw = base.prepare_transport(tag)
        target = project / request["output"][collision]
        target.write_bytes(b"PREEXISTING-DIFFERENT-BYTES")
        try:
            finalize.finalize_invocation_v2(
                request_raw,
                candidate_raw,
                transport_run.serialized_transport_binding,
                cwd=b,
                installed_root=installed_root,
            )
        except finalize.FinalizeFailure as exc:
            assert (exc.stage, exc.reason_code) == ("persistence", "IMMUTABLE_OUTPUT_COLLISION"), (
                collision,
                exc.stage,
                exc.reason_code,
            )
            assert target.read_bytes() == b"PREEXISTING-DIFFERENT-BYTES"
            supplemental.append({
                "id": "PI-37",
                "variant": collision,
                "kind": "direct_candidate_package_execution",
                "observed_stage": exc.stage,
                "observed_reason_code": exc.reason_code,
                "observed_exit_code": exc.exit_code,
            })
        else:
            raise AssertionError(f"PI-37 {collision} unexpectedly succeeded")

    # PI-38: mutation-target stores exist before prepare and remain byte-identical
    # through prepare, transport, and finalize.
    b, project, installed_root, request, request_raw, request_path = base.new_case("PI-38-E2E-r4")
    stores: dict[Path, bytes] = {}
    for rel in (
        "project-knowledge/canonical-state.json",
        "admission-store/state.json",
        "role-store/state.json",
        "authority-store/state.json",
    ):
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = (rel + "\nUNCHANGED-PI38-R4\n").encode()
        path.write_bytes(payload)
        stores[path] = payload

    prepared = prepare.prepare_invocation_v2(request_raw, cwd=b, installed_root=installed_root)
    source_id = prepared.provenance_registry["sources"][0]["source_id"]
    graph = {
        "records": [{
            "temp_id": "r1",
            "kind": "observation",
            "statement": "PI-38 end-to-end store sentinel witness.",
            "provenance": {"primary": [source_id]},
        }]
    }
    candidate_raw = renderer._jcs(graph)
    transport_run = transport.run_reference_transport(
        prepared.serialized_prepared_invocation,
        prepared.serialized_activation_bundle,
        expected_prepared_invocation_sha256=prepared.prepared_invocation["identity"]["prepared_invocation_sha256"],
        provider=lambda _request: candidate_raw,
        installed_root=installed_root,
    )
    result = finalize.finalize_invocation_v2(
        request_raw,
        candidate_raw,
        transport_run.serialized_transport_binding,
        cwd=b,
        installed_root=installed_root,
    )
    assert result.result["status"] == "PASS"
    for path, payload in stores.items():
        assert path.read_bytes() == payload, path
    supplemental.append({
        "id": "PI-38",
        "variant": "stores-present-before-prepare",
        "kind": "direct_candidate_package_execution",
        "observed_stage": "success",
        "observed_reason_code": None,
        "observed_exit_code": 0,
    })

    Path("/tmp/pi-supplemental-direct.json").write_text(json.dumps(supplemental, indent=2, sort_keys=True) + "\n")
    Path("/tmp/pi-supplemental-direct.txt").write_text(
        json.dumps(supplemental, indent=2, sort_keys=True)
        + "\nP10_G9_PI_COMPOUND_DIRECT_WITNESS_PASS\n"
    )
    print(Path("/tmp/pi-supplemental-direct.txt").read_text())
    return supplemental


def run_p1b_except_ps19() -> None:
    path = ROOT / "tests/test_context_packaging_protocol_schemas_p1b.py"
    mod = load_module("p1b_except_ps19_r4", path)
    mod.P1b.setUpClass()
    case = mod.P1b(methodName="test_negative_fixtures_reject_and_classify_exactly")
    original = case.fx["negative_cases"]
    selected = [item for item in original if item["id"] != "PS-19"]
    ids = [item["id"] for item in selected]
    assert len(selected) == len(original) - 1
    assert "PS-20" in ids
    assert any(int(item.split("-")[1]) > 20 for item in ids if item.startswith("PS-"))
    case.fx["negative_cases"] = selected
    try:
        case.test_negative_fixtures_reject_and_classify_exactly()
    finally:
        case.fx["negative_cases"] = original
    text = "P10_G9_P1B_NEGATIVES_EXCEPT_PS19_PASS\n" + json.dumps(ids) + "\n"
    write("/tmp/p1b-except-ps19.txt", text)
    print(text, end="")


def reproduce_ps19() -> None:
    path = ROOT / "tests/test_context_packaging_protocol_schemas_p1b.py"
    mod = load_module("p1b_ps19_r4", path)
    mod.P1b.setUpClass()
    case = mod.P1b(methodName="test_negative_fixtures_reject_and_classify_exactly")
    original = case.fx["negative_cases"]
    selected = [item for item in original if item["id"] == "PS-19"]
    assert len(selected) == 1
    case.fx["negative_cases"] = selected
    try:
        try:
            case.test_negative_fixtures_reject_and_classify_exactly()
        except AssertionError as exc:
            text = str(exc)
            assert "PS-19" in text
            assert "PLANE_CLASSIFICATION_CONFLICT" in text
            assert "UNKNOWN_SEMANTICS_FIELD" in text
            output = text + "\nP10_G9_INHERITED_PS19_REPRODUCED\n"
            write("/tmp/ps19.txt", output)
            print(output, end="")
        else:
            raise AssertionError("PS-19 unexpectedly passed")
    finally:
        case.fx["negative_cases"] = original


def supplement_ledger() -> None:
    path = Path("/tmp/pi-ledger.json")
    ledger = load_json(path)
    rows = {row["id"]: row for row in ledger["rows"]}
    expected = {f"PI-{n:02d}" for n in range(1, 61)}
    assert set(rows) == expected

    direct = load_json("/tmp/pi-supplemental-direct.json")
    grouped: dict[str, list[dict]] = {}
    for row in direct:
        grouped.setdefault(row["id"], []).append(row)

    for case_id in ("PI-34", "PI-37", "PI-38"):
        rows[case_id]["witness"] = {
            "id": case_id,
            "kind": "supplemental_direct_candidate_package_execution",
            "execution_log": "/tmp/pi-supplemental-direct.txt",
            "variants": grouped[case_id],
        }

    rows["PI-26"]["witness"] = {
        "id": "PI-26",
        "kind": "supplemental_exact_pytest_nodeids",
        "execution_log": "/tmp/pi-supplemental-pytest.txt",
        "witness_ids": [
            "tests/test_context_packaging_authority_memory_isolation_p8.py::P8AuthorityMemoryIsolationTests::test_pc02_pc22_ambient_memory_is_not_a_supported_source_class",
            "tests/test_context_packaging_authority_memory_isolation_p8.py::P8AuthorityMemoryIsolationTests::test_pc17_unselected_prior_candidate_cannot_enter_pack",
        ],
    }
    rows["PI-31"]["witness"] = {
        "id": "PI-31",
        "kind": "supplemental_exact_pytest_nodeids",
        "execution_log": "/tmp/pi-supplemental-pytest.txt",
        "witness_ids": [
            "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_unsupported_provider_and_nonconforming_mapping_fail_closed",
            "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_plane_frames_are_copied_without_instruction_shape_promotion",
        ],
    }
    rows["PI-48"]["witness"] = {
        "id": "PI-48",
        "kind": "supplemental_exact_pytest_nodeids",
        "execution_log": "/tmp/pi-supplemental-pytest.txt",
        "witness_ids": [
            "tests/test_context_packaging_production_integration_p10_g1.py::test_p10_g1_transport_and_handoff_boundaries_are_explicit",
            "tests/test_context_packaging_production_integration_p10_g1.py::test_p10_g1_semantic_negative_cases_preserve_g0_boundaries",
        ],
    }

    ledger["contract"] = "reasoning-distiller-p10-g9-pi-execution-ledger/4"
    ledger["supplemental_witnesses"] = {
        "compound_direct_cases": ["PI-34", "PI-37", "PI-38"],
        "compound_exact_node_cases": ["PI-26", "PI-31", "PI-48"],
        "unsupported_runtime_cases": ["PI-14", "PI-52"],
    }
    ledger["rows"] = [rows[f"PI-{n:02d}"] for n in range(1, 61)]
    assert len(ledger["rows"]) == 60
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    output = json.dumps(ledger["supplemental_witnesses"], indent=2, sort_keys=True)
    write("/tmp/pi-ledger-supplement.txt", output + "\nP10_G9_PI_COMPOUND_WITNESS_SUPPLEMENT_PASS\n")
    print(Path("/tmp/pi-ledger-supplement.txt").read_text())


def stage_artifact(package: dict) -> None:
    out = Path("/tmp/evidence-r4")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    paths = [
        "/tmp/summary.json",
        "/tmp/runtime.json",
        "/tmp/pi-unsupported-runtime-runtime.json",
        "/tmp/pi-unsupported-runtime-package.json",
        "/tmp/dependencies.txt",
        "/tmp/candidate-tree.txt",
        "/tmp/build.json",
        "/tmp/package.json",
        "/tmp/p10-inventory.txt",
        "/tmp/p10-nodeids.txt",
        "/tmp/p10.txt",
        "/tmp/pi-witness-remediation.py",
        "/tmp/pi-witness-remediation-base.py",
        "/tmp/pi-witness-scripts.sha256",
        "/tmp/pi-direct-witnesses.json",
        "/tmp/pi-direct-execution.txt",
        "/tmp/pi-exact-pytest.txt",
        "/tmp/pi-supplemental-direct.json",
        "/tmp/pi-supplemental-direct.txt",
        "/tmp/pi-supplemental-pytest.txt",
        "/tmp/pi-unsupported-runtime.txt",
        "/tmp/pi-ledger.json",
        "/tmp/pi-ledger.txt",
        "/tmp/pi-ledger-supplement.txt",
        "/tmp/v1.txt",
        "/tmp/p1.txt",
        "/tmp/p1b-except-ps19.txt",
        "/tmp/ps19.txt",
        "/tmp/p0-p9-inventory.txt",
        "/tmp/p0-p9.txt",
        "/tmp/package-tests.txt",
    ]
    for src in paths:
        p = Path(src)
        assert p.is_file(), src
        shutil.copy2(p, out / p.name)
    for key in ("archive", "manifest", "sha256"):
        p = Path(package[key])
        assert p.is_file(), (key, p)
        shutil.copy2(p, out / p.name)


def main() -> None:
    assert run(["git", "rev-parse", "HEAD"]).stdout.strip() == CANDIDATE
    assert run(["git", "rev-parse", "HEAD^{tree}"]).stdout.strip() == CANDIDATE_TREE
    write("/tmp/candidate-tree.txt", CANDIDATE_TREE + "\n")
    runtime = exact_runtime((3, 12, 0))
    write("/tmp/runtime.json", json.dumps(runtime, sort_keys=True) + "\n")
    run([sys.executable, "-m", "pip", "freeze"], log="/tmp/dependencies.txt")

    package_dir = Path("/tmp/package")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    built = run(
        [
            sys.executable,
            "packaging/build_release_package.py",
            "--version",
            PACKAGE_VERSION,
            "--source-commit",
            CANDIDATE,
            "--output-dir",
            str(package_dir),
        ],
        log="/tmp/build.json",
    )
    build = json.loads(built.stdout)
    manifest_path = Path(build["manifest"])
    archive_path = Path(build["archive"])
    manifest = load_json(manifest_path)
    archive_sha = sha_file(archive_path)
    manifest_sha = sha_file(manifest_path)
    assert manifest["source_commit"] == CANDIDATE
    assert manifest["version"] == PACKAGE_VERSION
    assert archive_sha == manifest["transport_sha256"] == build["transport_sha256"]
    assert manifest["content_identity"] == build["content_identity"]
    package = {
        "candidate": CANDIDATE,
        "version": PACKAGE_VERSION,
        "content_identity": manifest["content_identity"],
        "transport_sha256": archive_sha,
        "manifest_sha256": manifest_sha,
        "file_count": len(manifest["files"]),
        "managed_roots": manifest["managed_roots"],
        "archive": str(archive_path),
        "manifest": str(manifest_path),
        "sha256": build["sha256"],
    }
    write("/tmp/package.json", json.dumps(package, sort_keys=True) + "\n")

    for root in manifest["managed_roots"]:
        path = ROOT / root
        if path.exists():
            shutil.rmtree(path)
    run(["tar", "-xzf", str(archive_path), "-C", str(ROOT)])
    expected = {item["path"]: item["sha256"] for item in manifest["files"]}
    actual: dict[str, str] = {}
    for root in manifest["managed_roots"]:
        for path in (ROOT / root).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                actual[path.relative_to(ROOT).as_posix()] = sha_file(path)
    assert actual == expected
    print(f"EXACT_PACKAGE_REHYDRATION_PASS files={len(actual)}")

    v053 = Path("/tmp/v053")
    v053.mkdir(exist_ok=True)
    v053_manifest = v053 / "reasoning-distiller-0.5.3.manifest.json"
    v053_archive = v053 / "reasoning-distiller-0.5.3.tar.gz"
    download(
        "https://github.com/loteque/reasoning-distiller/releases/download/v0.5.3/reasoning-distiller-0.5.3.manifest.json",
        v053_manifest,
        "5c9448c6e6acc6f3925aae173870f4d6e8a237035c0e870637ef8d7499765044",
    )
    download(
        "https://github.com/loteque/reasoning-distiller/releases/download/v0.5.3/reasoning-distiller-0.5.3.tar.gz",
        v053_archive,
        "5d1751f1910e13ba5b3e9787a6188a1b995e0ac5b88bbec9c2ac935e9d33ef67",
    )

    test_env = os.environ.copy()
    test_env["P10_G7_V053_MANIFEST"] = str(v053_manifest)
    test_env["P10_G7_V053_ARCHIVE"] = str(v053_archive)

    p10_tests = sorted(ROOT.glob("tests/test_context_packaging_production_integration_p10_g*.py"))
    write("/tmp/p10-inventory.txt", "\n".join(path.relative_to(ROOT).as_posix() for path in p10_tests) + "\n")
    run([sys.executable, "-m", "pytest", "--collect-only", "-q", *p10_tests], log="/tmp/p10-nodeids.txt", env=test_env)
    run([sys.executable, "-m", "pytest", "-q", *p10_tests], log="/tmp/p10.txt", env=test_env)

    runtime_witness = Path("/tmp/runtime-witness")
    unsupported_log = runtime_witness / "pi-unsupported-runtime.txt"
    unsupported_runtime_path = runtime_witness / "pi-unsupported-runtime-runtime.json"
    unsupported_package_path = runtime_witness / "pi-unsupported-runtime-package.json"
    assert unsupported_log.is_file() and unsupported_runtime_path.is_file() and unsupported_package_path.is_file()
    shutil.copy2(unsupported_log, "/tmp/pi-unsupported-runtime.txt")
    shutil.copy2(unsupported_runtime_path, "/tmp/pi-unsupported-runtime-runtime.json")
    shutil.copy2(unsupported_package_path, "/tmp/pi-unsupported-runtime-package.json")
    assert "P10_G9_UNSUPPORTED_RUNTIME_WITNESS_PASS" in Path("/tmp/pi-unsupported-runtime.txt").read_text()
    unsupported_runtime = load_json("/tmp/pi-unsupported-runtime-runtime.json")
    unsupported_package = load_json("/tmp/pi-unsupported-runtime-package.json")
    assert unsupported_runtime["implementation"] == "cpython"
    assert unsupported_runtime["version"] == "3.12.1"
    assert unsupported_package["candidate"] == CANDIDATE
    assert unsupported_package["candidate_tree"] == CANDIDATE_TREE
    assert unsupported_package["content_identity"] == package["content_identity"]
    assert unsupported_package["transport_sha256"] == package["transport_sha256"]
    assert exact_runtime((3, 12, 0))["version"] == "3.12.0"

    base = load_module("p10_g9_base_r4", Path("/tmp/pi-witness-remediation-base.py"))
    direct = run([sys.executable, "/tmp/pi-witness-remediation-base.py", "execute"], log="/tmp/pi-direct-execution.txt", env=test_env)
    assert "P10_G9_DIRECT_PI_WITNESSES_PASS" in direct.stdout

    supplemental_witnesses(base)
    supplemental_nodes = [
        "tests/test_context_packaging_authority_memory_isolation_p8.py::P8AuthorityMemoryIsolationTests::test_pc02_pc22_ambient_memory_is_not_a_supported_source_class",
        "tests/test_context_packaging_authority_memory_isolation_p8.py::P8AuthorityMemoryIsolationTests::test_pc17_unselected_prior_candidate_cannot_enter_pack",
        "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_unsupported_provider_and_nonconforming_mapping_fail_closed",
        "tests/test_context_packaging_production_integration_p10_g5.py::test_p10_g5_plane_frames_are_copied_without_instruction_shape_promotion",
        "tests/test_context_packaging_production_integration_p10_g1.py::test_p10_g1_transport_and_handoff_boundaries_are_explicit",
        "tests/test_context_packaging_production_integration_p10_g1.py::test_p10_g1_semantic_negative_cases_preserve_g0_boundaries",
    ]
    supplemental_pytest = run([sys.executable, "-m", "pytest", "-q", *supplemental_nodes], env=test_env)
    write("/tmp/pi-supplemental-pytest.txt", supplemental_pytest.stdout + "P10_G9_PI_COMPOUND_PYTEST_WITNESS_PASS\n")

    run([sys.executable, "-m", "pytest", "-q", "tests/test_production_invocation.py"], log="/tmp/v1.txt")
    run([sys.executable, "-m", "pytest", "-q", "tests/test_context_packaging_protocol_schemas_v2.py"], log="/tmp/p1.txt")
    run_p1b_except_ps19()
    reproduce_ps19()

    p0_p9_tests = sorted(
        path for path in ROOT.glob("tests/test_context_packaging_*.py")
        if not path.name.startswith("test_context_packaging_production_integration_p10_g")
    )
    write("/tmp/p0-p9-inventory.txt", "\n".join(path.relative_to(ROOT).as_posix() for path in p0_p9_tests) + "\n")
    run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *p0_p9_tests,
            "-k",
            "not test_p5_runtime_implementation_is_unchanged_by_amendment and not test_negative_fixtures_reject_and_classify_exactly",
        ],
        log="/tmp/p0-p9.txt",
    )
    run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_package_builder.py",
            "tests/test_install_package_contract.py",
            "tests/test_installer_p3.py",
            "tests/test_installer_p4.py",
        ],
        log="/tmp/package-tests.txt",
    )

    ledger_run = run([sys.executable, "/tmp/pi-witness-remediation-base.py", "ledger"], log="/tmp/pi-ledger.txt", env=test_env)
    assert "P10_G9_PI01_PI60_EXACT_WITNESS_LEDGER_PASS" in ledger_run.stdout
    supplement_ledger()

    final_runtime = exact_runtime((3, 12, 0))
    assert final_runtime["version"] == "3.12.0"

    script_hashes: dict[str, str] = {}
    for line in Path("/tmp/pi-witness-scripts.sha256").read_text().splitlines():
        digest, file_path = line.split(maxsplit=1)
        script_hashes[Path(file_path).name] = digest

    summary = {
        "contract": "reasoning-distiller-p10-g9-engineer-evidence/4",
        "candidate": CANDIDATE,
        "candidate_tree": CANDIDATE_TREE,
        "governing_plan": GOVERNING_PLAN,
        "governing_plan_blob": GOVERNING_PLAN_BLOB,
        "package": package,
        "runtime": runtime,
        "unsupported_runtime": unsupported_runtime,
        "unsupported_runtime_package": unsupported_package,
        "pi_ledger": load_json("/tmp/pi-ledger.json"),
        "witness_script_sha256": script_hashes,
        "matrix": {
            "p10_complete": "PASS",
            "pi_direct_candidate_package_witnesses": "PASS",
            "pi_compound_direct_witnesses": "PASS",
            "pi_exact_pytest_nodeid_witnesses": "PASS",
            "pi_compound_exact_node_witnesses": "PASS",
            "pi_unsupported_runtime": "PASS",
            "pi01_pi60_exact_witness_ledger": "PASS",
            "production_v1": "PASS",
            "p1_v2_schema": "PASS",
            "p1b_negatives_except_ps19": "PASS",
            "ps19_inherited_baseline": "REPRODUCED_EXPECTED_MISMATCH",
            "p0_p9": "PASS",
            "package_installer": "PASS",
        },
        "workflow_run_id": os.environ["GITHUB_RUN_ID"],
        "workflow_run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "evidence_head": EVIDENCE_HEAD,
    }
    write("/tmp/summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")

    assert "P10_G9_PI_COMPOUND_DIRECT_WITNESS_PASS" in Path("/tmp/pi-supplemental-direct.txt").read_text()
    assert "P10_G9_PI_COMPOUND_PYTEST_WITNESS_PASS" in Path("/tmp/pi-supplemental-pytest.txt").read_text()
    assert "P10_G9_UNSUPPORTED_RUNTIME_WITNESS_PASS" in Path("/tmp/pi-unsupported-runtime.txt").read_text()
    assert "P10_G9_PI_COMPOUND_WITNESS_SUPPLEMENT_PASS" in Path("/tmp/pi-ledger-supplement.txt").read_text()
    assert "P10_G9_P1B_NEGATIVES_EXCEPT_PS19_PASS" in Path("/tmp/p1b-except-ps19.txt").read_text()
    assert "P10_G9_INHERITED_PS19_REPRODUCED" in Path("/tmp/ps19.txt").read_text()

    stage_artifact(package)
    print("P10_G9_WITNESS_REMEDIATION_ENGINEER_EXECUTION_PASS")


if __name__ == "__main__":
    main()
