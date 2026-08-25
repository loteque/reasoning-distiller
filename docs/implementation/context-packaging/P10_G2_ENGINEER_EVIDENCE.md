# P10-G2 Engineer execution evidence

Disposition: **P10_G2_INSTALLED_PACKAGE_ENGINEER_EXECUTION_PASS**

Repository: `loteque/reasoning-distiller`

Coordination control: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`

Governing P10 plan: `b435dff827b745d711a5c5a297587a0c4359bed1` / blob `eae54b9e2c0618faec61acf2f9e4acd942ec063d`

Semantic base: `cc14721725949a560b52f0a5d80808e95c2d6ad0`

Closed G0 candidate: `2b5c81a5b7b92c810be84f87f42524842ec308a7`

G1 base: `bc670a602806870ede81eb41ef23f09fe42f772c`

Exact P10-G2 semantic candidate: `95eac1148744d90b9074cbdfce82edfe4751f87a`

Semantic branch: `impl/p10-g2-installed-package-closure-20260825`

Evidence branch: `evidence/p10-g2-95eac114-engineer-20260825`

Evidence PR: `#81`

Accepted candidate-bound workflow run: `32894426018`

Accepted evidence-workflow commit: `dda22552717f0463a1af5896c7ec96fa9d3c7ea2`

## Exact accepted execution surface

The accepted run checked out the exact semantic candidate `95eac1148744d90b9074cbdfce82edfe4751f87a` for every evidence job. The workflow branch itself was not treated as the semantic candidate.

The accepted G2 execution platform is the repository's canonical deterministic-installer platform: GitHub `ubuntu-latest`, with exact P9 runtime identity:

```text
implementation: cpython
version: 3.12.0
cache tag: cpython-312
binding scheme: python-closed-bundle/1
```

This does not establish Windows installer compatibility. The existing `reasoning-distiller-install-package/1` manifest carries POSIX-style `0644`/`0755` file modes, the canonical P3 installer verifies those modes, and the repository's package-installer workflow runs that contract on Ubuntu. P10-G2 does not broaden the installer platform contract.

## Accepted run results

Workflow run `32894426018` completed with overall `success`.

All three candidate-bound jobs completed successfully:

1. `g2-package-closure` PASS
   - exact semantic candidate verified;
   - direct G1 base verified;
   - G2 delta verified to the three intended semantic files;
   - exact CPython 3.12.0 / `cpython-312` verified;
   - `tests/test_context_packaging_production_integration_p10_g2.py` PASS.

2. `g2-package-regressions` PASS
   - `tests/test_package_builder.py`;
   - `tests/test_install_package_contract.py`;
   - `tests/test_installer_p3.py`;
   - `tests/test_installer_p4.py`.

3. `g2-predecessor-regressions` PASS
   - P10-G0 pressure freeze;
   - P10-G1 protocol/handoff freeze;
   - P9 renderer identity/closed-bundle/execution-binding/rendering regressions;
   - RI-15 remediation regression;
   - fixed production `/1` invocation regressions.

## G2 obligations established

For this exact candidate and accepted platform/runtime tuple, the evidence establishes:

- `context_packaging` is part of the deterministic release managed roots;
- current P9 renderer/runtime contracts and P10-G1 protocol/schema resources are present in package closure;
- changing packaged `context_packaging` content changes package content identity;
- installation proceeds from package/archive artifacts after the synthetic source tree is removed;
- an explicit downgrade to an older manifest removes the newer `context_packaging` managed root rather than leaving behavior-affecting orphan files;
- canonical package/installer behavior remains green;
- selected P9, G0, G1, and fixed `/1` production behavior remains green.

## Windows pressure observation

Earlier exploratory evidence deliberately ran the G2 suite on Windows. The exact diagnostic recorded a failure at `packaging/rd_install.py` staged-tree mode validation because Windows reported a mode different from the manifest's POSIX `0644` value (`installed file mode mismatch: admission/a.txt`).

That observation is retained on evidence PR `#81`. It is **not** classified as a G2 semantic blocker because the live package/installer contract and its canonical CI do not establish Windows as a supported acceptance platform, and P10-G2 does not authorize changing those existing installer semantics or broadening their platform contract.

No Windows PASS is claimed.

## Boundary

This evidence establishes only the P10-G2 installed-package closure prerequisite. It is not P10-G8 full candidate/package/runtime evidence, independent implementation review, Steward reconciliation, admission, canonical mutation, or authority/activation mutation.

No P10-G3 or later runtime implementation is included in semantic candidate `95eac1148744d90b9074cbdfce82edfe4751f87a`.
