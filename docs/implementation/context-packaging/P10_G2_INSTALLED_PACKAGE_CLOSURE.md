# P10-G2 Installed-package closure

Status: **IMPLEMENTATION CANDIDATE**

Repository: `loteque/reasoning-distiller`

Coordination basis: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`

Semantic base: `cc14721725949a560b52f0a5d80808e95c2d6ad0`

Governing P10 plan: `b435dff827b745d711a5c5a297587a0c4359bed1` / blob `eae54b9e2c0618faec61acf2f9e4acd942ec063d`

Closed P10-G0 candidate: `2b5c81a5b7b92c810be84f87f42524842ec308a7`

P10-G1 protocol/handoff candidate and direct G2 base: `bc670a602806870ede81eb41ef23f09fe42f772c`

Gate: **P10-G2 only**.

## Closure decision

`context_packaging` is added to `reasoning-distiller-package-build/1.managed_roots`.

The existing package builder recursively includes every regular non-generated file under every managed root, and the existing package `content_identity` commits to the sorted managed-root set plus every packaged file path, mode, and SHA-256 digest. Therefore the installed package identity now binds the exact repository-owned P9 renderer and all behavior-bearing helpers under `context_packaging`, rather than requiring a generic source-repository checkout.

The existing managed roots already bind:

- `agents`, including the installed Distiller directive;
- `protocols`, including the P9 execution-binding/closed-bundle contracts and the P10-G1 protocol freeze;
- `runtime`, including the existing `/1` production runtime surface and the location in which later governed P10 runtime work can be added;
- `schemas`, including the P9 and P10-G1 schemas;
- `validators`, including the installed RGP validator.

Adding `context_packaging` closes the missing package topology identified by P10 Stage 3 R6. Later G3-G6 behavior placed within already managed roots is therefore package-bound automatically; G2 does not implement that later behavior early.

## Runtime ABI boundary

Initial `/2` compatibility remains exactly the accepted P9 execution tuple:

```text
implementation: cpython
version: 3.12.0
cache tag: cpython-312
binding scheme: python-closed-bundle/1
```

The exact tuple is already frozen in `protocols/rgp/renderer-execution-binding-v1.json`, `protocols/rgp/python-closed-bundle-v1.json`, and the accepted `context_packaging/renderer.py` implementation. All of those bytes are now within managed package roots and therefore participate in release `content_identity`.

G2 does not broaden this ABI and does not claim nearby Python versions equivalent.

## Source-repository isolation and downgrade

The G2 regression gate proves package/install closure without original source-tree availability after package construction. The installer consumes the deterministic archive plus manifest and installs the packaged `context_packaging` root from those artifacts.

The existing installer already replaces the complete `.reasoning-distiller` managed tree transactionally. An explicit downgrade to an older manifest that does not contain `context_packaging` therefore removes the newer root instead of leaving behavior-affecting orphan files. The G2 regression gate exercises this path with `allow_downgrade=True` and verifies the installed manifest is exactly the older manifest.

No new cleanup algorithm is introduced.

## Release version

No production release number is selected here. Stage 3 reserves release-version choice to release governance. G2 proves package closure and content-identity behavior using test-only version strings.

## Scope exclusions

This candidate does **not** implement or claim completion of:

- P10-G3 provenance bridge logic or registry persistence;
- P10-G4 `/2` prepare integration;
- P10-G5 provider transport execution or a reference runner;
- P10-G6 `/2` finalize integration;
- P10-G7 migration/rollback behavior beyond exercising existing explicit package downgrade cleanup;
- P10-G8 complete candidate/package/runtime-bound evidence;
- P10-G9 independent implementation review;
- P10-G10 Steward reconciliation;
- admission, canonical mutation, role/authority mutation, or activation mutation.

A successful G2 test run establishes the package/install prerequisite only. It does not establish a successful production `/2` invocation, which cannot be claimed before the later governed implementation gates exist.
