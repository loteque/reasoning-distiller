from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRANCH_BASE = "bc670a602806870ede81eb41ef23f09fe42f772c"
COORDINATION_REVISION = "80b6e89ad2efe84b088ca06b908a257c449fac15"
SEMANTIC_BASE = "cc14721725949a560b52f0a5d80808e95c2d6ad0"
GOVERNING_PLAN_COMMIT = "b435dff827b745d711a5c5a297587a0c4359bed1"
GOVERNING_PLAN_BLOB = "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
G0_CANDIDATE = "2b5c81a5b7b92c810be84f87f42524842ec308a7"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = _load_module("p10_g2_package_builder", ROOT / "packaging/build_release_package.py")
installer = _load_module("p10_g2_installer", ROOT / "packaging/rd_install.py")


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_source(root: Path, config: dict, marker: str) -> None:
    (root / "packaging").mkdir(parents=True)
    (root / "packaging/package-build.json").write_text(
        json.dumps(config, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for managed_root in config["managed_roots"]:
        directory = root / managed_root
        directory.mkdir(parents=True)
        (directory / "a.txt").write_text(
            f"{marker}:{managed_root}\n",
            encoding="utf-8",
        )


def test_p10_g2_is_bound_to_governing_inputs_and_package_scope_only() -> None:
    assert COORDINATION_REVISION == "80b6e89ad2efe84b088ca06b908a257c449fac15"
    assert SEMANTIC_BASE == "cc14721725949a560b52f0a5d80808e95c2d6ad0"
    assert GOVERNING_PLAN_COMMIT == "b435dff827b745d711a5c5a297587a0c4359bed1"
    assert GOVERNING_PLAN_BLOB == "eae54b9e2c0618faec61acf2f9e4acd942ec063d"
    assert G0_CANDIDATE == "2b5c81a5b7b92c810be84f87f42524842ec308a7"
    assert BRANCH_BASE == "bc670a602806870ede81eb41ef23f09fe42f772c"

    config = builder.load_config()
    assert config["managed_roots"] == sorted(config["managed_roots"])
    assert "context_packaging" in config["managed_roots"]
    assert "context_packaging" not in config["excluded_top_level"]
    assert {"docs", "evaluation", "project-knowledge", "tests"}.isdisjoint(
        config["managed_roots"]
    )


def test_p10_g2_manifest_closes_over_current_p9_p10_surface() -> None:
    with tempfile.TemporaryDirectory() as td:
        result = builder.build("0.0.0-p10-g2", "1" * 40, Path(td))
        manifest = _json(result["manifest"])
        paths = {item["path"] for item in manifest["files"]}

    current_context_files = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "context_packaging").rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }
    assert current_context_files
    assert current_context_files <= paths

    required = {
        "agents/distiller/DIRECTIVE.md",
        "context_packaging/renderer.py",
        "protocols/rgp/context-renderer-v2.json",
        "protocols/rgp/python-closed-bundle-v1.json",
        "protocols/rgp/renderer-execution-binding-v1.json",
        "protocols/rgp/production-integration-v2.json",
        "runtime/rd_distill.py",
        "runtime/rd_distill_core.py",
        "schemas/activation-bundle-v2.schema.json",
        "schemas/context-provenance-registry.schema.json",
        "schemas/context-rendered-activation-v2.schema.json",
        "schemas/context-renderer-profile-v2.schema.json",
        "schemas/invocation-request-v2.schema.json",
        "schemas/invocation-result-v2.schema.json",
        "schemas/model-transport.schema.json",
        "schemas/prepared-invocation.schema.json",
        "schemas/python-closed-bundle-descriptor.schema.json",
        "schemas/renderer-execution-binding.schema.json",
        "validators/rgp_validator.py",
    }
    assert required <= paths
    assert not any(
        path.startswith(("docs/", "evaluation/", "project-knowledge/", "tests/"))
        for path in paths
    )


def test_p10_g2_package_identity_binds_exact_p9_runtime_contract() -> None:
    binding = _json(ROOT / "protocols/rgp/renderer-execution-binding-v1.json")
    bundle = _json(ROOT / "protocols/rgp/python-closed-bundle-v1.json")
    expected = {
        "implementation": "cpython",
        "major": 3,
        "minor": 12,
        "micro": 0,
        "cache_tag": "cpython-312",
    }
    assert binding["contract"] == "reasoning-distiller-renderer-execution-binding/1"
    assert binding["scheme"] == "python-closed-bundle/1"
    assert binding["runtime_abi"] == expected
    assert bundle["scheme"] == "python-closed-bundle/1"
    assert bundle["runtime_abi"] == expected

    config = builder.load_config()
    assert "protocols" in config["managed_roots"]
    assert "context_packaging" in config["managed_roots"]
    renderer = (ROOT / "context_packaging/renderer.py").read_text(encoding="utf-8")
    assert "_EXPECTED_RUNTIME_ABI = ('cpython', 3, 12, 0, 'cpython-312')" in renderer


def test_p10_g2_context_packaging_change_changes_package_identity() -> None:
    config = builder.load_config()
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        source = base / "source"
        _write_source(source, config, "before")
        first = builder.build("9.0.0", "2" * 40, base / "one", root=source)
        (source / "context_packaging/a.txt").write_text(
            "after:context_packaging\n",
            encoding="utf-8",
        )
        second = builder.build("9.0.0", "2" * 40, base / "two", root=source)

        assert first["content_identity"] != second["content_identity"]
        assert first["transport_sha256"] != second["transport_sha256"]


def test_p10_g2_install_is_source_independent_and_explicit_downgrade_cleans_new_root() -> None:
    current_config = builder.load_config()
    old_config = copy.deepcopy(current_config)
    old_config["managed_roots"] = [
        root for root in old_config["managed_roots"] if root != "context_packaging"
    ]
    assert old_config["managed_roots"] == sorted(old_config["managed_roots"])

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        current_source = base / "current-source"
        old_source = base / "old-source"
        target = base / "project"
        target.mkdir()

        _write_source(current_source, current_config, "current")
        current = builder.build(
            "9.0.0",
            "3" * 40,
            base / "current-release",
            root=current_source,
        )
        shutil.rmtree(current_source)

        installed = installer.install(
            current["archive"],
            current["manifest"],
            current["transport_sha256"],
            target,
        )
        assert installed["status"] == "PASS"
        managed = target / ".reasoning-distiller"
        assert (managed / "context_packaging/a.txt").is_file()

        _write_source(old_source, old_config, "old")
        old = builder.build(
            "8.0.0",
            "4" * 40,
            base / "old-release",
            root=old_source,
        )
        shutil.rmtree(old_source)

        downgraded = installer.install(
            old["archive"],
            old["manifest"],
            old["transport_sha256"],
            target,
            allow_downgrade=True,
        )
        assert downgraded["status"] == "PASS"
        assert not (managed / "context_packaging").exists()
        assert _json(managed / ".installation/MANIFEST.json") == _json(old["manifest"])
