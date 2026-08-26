# P10-G8 Candidate-Bound Engineer Evidence

Disposition: **P10_G8_FULL_REGRESSION_ENGINEER_EXECUTION_PASS**

## Scope and boundary

This Engineer-produced record establishes P10-G8 candidate-bound full-regression evidence only. It does not perform P10-G9 independent implementation review, Steward reconciliation, admission, activation, canonical mutation, RIL activation, authority mutation, or any G9+ work.

## Governing anchors

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision re-resolved immediately before this evidence write: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing P10 Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1` / blob `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- Receiving role/scope: implementation Engineer, P10-G8 only
- Closed G7 semantic candidate: `ec410a501e7db051f59eb2fb373c30da150bd81a`
- G7 Engineer evidence: `14230043fdea5fbd7e4eeca9592dea8f2a19e764`
- G7 successful candidate-bound run: `32914349031`
- G7 evidence-record rerun: `32914528151`
- G7 evidence PR: `#88`
- G7 disposition: `P10_G7_MIGRATION_ROLLBACK_COMPATIBILITY_ENGINEER_EXECUTION_PASS`

Immediately before this write, `main` still resolved to the coordination revision above and `impl/p10-g7-migration-rollback-20260825` still resolved exactly to the G7 semantic candidate above. The G8 evidence transport therefore did not broaden or move the semantic candidate.

## Immutable G8 candidate/package/runtime tuple

- Semantic candidate: `ec410a501e7db051f59eb2fb373c30da150bd81a`
- Candidate tree: `bb68cef577ef9b89c347f658fcb89e995e7c2a8e`
- Evidence package version: `0.0.0-p10-g8`
  - This is an evidence-only package identifier for this G8 run. It is not a release-version or publication claim.
- Package content identity: `sha256:7e2513792ec22d24c88d1aea0f02e9150f9822693b63fc222c8b9124c0f50932`
- Package transport SHA-256: `4b435f795ff6c09798990c907fb87a69646195f46c4bae6afce7bfc3b145426f`
- Package manifest SHA-256: `d2ca39b49772b27e8b085204ce462899c4f875edceb2d8c1a21d4284c4a346ef`
- Package inventory: 97 files
- Managed roots: `admission`, `agents`, `backends`, `context_packaging`, `protocols`, `runtime`, `schemas`, `validators`
- Runtime: CPython `3.12.0`, cache tag `cpython-312`
- Runtime executable SHA-256: `dff2212b560fa5591efed5375998288dd1238dbc5da44618dbc1d3777e08ffe8`
- Runner: Linux X64, GitHub `ubuntu-24.04`, image version `20260823.283.1`
- Exact package rehydration verification: PASS for all 97 packaged files

The workflow built one deterministic package from the exact semantic candidate, recorded its package identities, removed the behavior-bearing managed roots from the checked-out tree, rehydrated those roots from that exact archive, and verified the SHA-256 of every one of the 97 packaged files against the manifest before running the regression gates. The semantic Git HEAD remained the exact candidate throughout.

## Exact execution provenance

- Evidence branch: `evidence/p10-g8-ec410a50-engineer-20260825`
- Evidence workflow transport commit executed: `86f3ddf5f3f22d7a9affe54ea69b5919625e8582`
- Evidence PR: `#89`
- Workflow run: `32915555803`
- Workflow attempt: `1`
- Job: `98018416862`
- Evidence artifact: `p10-g8-ec410a50-evidence`, artifact ID `9588046889`
- Artifact ZIP SHA-256: `33fffbaed2090e07c3283b3dcb97c22c273c861dd8a5a42a1145bc92d4818855`

The accepted run completed successfully and the final enforcement step emitted `P10_G8_FULL_REGRESSION_ENGINEER_EXECUTION_PASS`.

## Accepted G8 results

1. Complete supported-runtime P10 G0-G7 suite: PASS
   - Exact files: `tests/test_context_packaging_production_integration_p10_g0.py` through `tests/test_context_packaging_production_integration_p10_g7.py`.
   - Result: 53 passed, 1 skipped.
   - The skipped case is G7's unsupported-runtime pressure test, intentionally inapplicable on the one required supported-runtime tuple CPython 3.12.0 / `cpython-312`; G8 did not introduce a second runtime tuple.

2. Fixed production invocation `/1` regression: PASS
   - `tests/test_production_invocation.py`
   - Result: 12 passed.

3. Unaffected P0-P9 context-packaging regression sweep: PASS
   - Result: 214 passed, 2 predecessor assertions deselected by the established unaffected-regression selector, 162 subtests passed.
   - The inventory covered the P0-P9 context-packaging tests present on the exact candidate while excluding the P10 gate files themselves.

4. Canonical package and installer regressions: PASS
   - `tests/test_package_builder.py`
   - `tests/test_install_package_contract.py`
   - `tests/test_installer_p3.py`
   - `tests/test_installer_p4.py`
   - Result: 36 passed, 11 subtests passed.

5. Inherited PS-19 classifier mismatch baseline: reproduced unchanged
   - The separately executed predecessor assertion reproduced the existing `PS-19` mismatch: actual `PLANE_CLASSIFICATION_CONFLICT` versus expected `UNKNOWN_SEMANTICS_FIELD`.
   - The workflow required this exact historical mismatch signature and treated successful reproduction as baseline evidence, not as a new G8 regression.

## G8 conclusion

For the exact immutable semantic candidate/package/runtime tuple recorded above, the complete P10 supported-runtime suite, fixed production `/1`, unaffected P0-P9 context-packaging regressions, and package/installer seams all pass. The known inherited PS-19 mismatch is separately reproduced unchanged.

Engineer disposition: **P10_G8_FULL_REGRESSION_ENGINEER_EXECUTION_PASS**.

## Authority boundary

This record establishes only P10-G8 Engineer execution evidence. P10-G9 independent implementation review is **NOT_ESTABLISHED**. Steward reconciliation is **NOT_ESTABLISHED**. No admission, activation, canonical mutation, RIL activation, authority mutation, release publication, or G9+ work is performed or authorized by this record.
