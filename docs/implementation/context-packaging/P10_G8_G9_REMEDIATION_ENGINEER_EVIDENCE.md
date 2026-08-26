# P10 G8/G9 Remediation Engineer Evidence

## Scope

Implementation-Engineer evidence only for the remediation returned by P10-G9 independent review. This record does not issue a G9 review disposition and does not begin G10 or later governed work.

## Governing anchors

- Repository: `loteque/reasoning-distiller`
- Coordination: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`
- P10 Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`
- Plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- Rejected G9 candidate: `ec410a501e7db051f59eb2fb373c30da150bd81a`
- Rejected tree: `bb68cef577ef9b89c347f658fcb89e995e7c2a8e`
- Prior G8 evidence: `03639168533dd0ceef8dde7e9e08e3cf8ee4d232`
- Prior G8 runs: `32915555803`, `32915721707`
- Prior evidence PR: `#89`
- Review result: `P10_G9_INDEPENDENT_REVIEW_CHANGES_REQUIRED`

## Remediations

### PI-09 consumer binding

`/2` prepare now requires the eligibility consumer to equal both frozen production values:

- `consumer_contract = reasoning-distiller-invocation/2`
- `consumer_id = rd-distill`

A new adversarial regression keeps the pack summary and eligibility artifact mutually consistent while independently substituting a wrong consumer contract and a wrong consumer id. Both cases must fail preflight with `PROFILE_ELIGIBILITY_MISMATCH`, exit code `2`, before prepared or provenance output is created.

The G4 positive fixture was corrected to use the frozen `/2` consumer contract.

### G8 predecessor-negative coverage

The corrected G8 harness no longer lets inherited PS-19 terminate evidence for later negative fixtures. It runs the original P1b negative-case test with every negative fixture except PS-19 and requires that set to pass, including PS-20 and later PS cases. It then runs PS-19 alone and requires reproduction of the inherited `PLANE_CLASSIFICATION_CONFLICT` versus `UNKNOWN_SEMANTICS_FIELD` mismatch.

PS-19 remains predecessor baseline behavior and is not changed by this remediation.

## Immutable semantic candidate

- Candidate: `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`
- Tree: `81178c5efdc8f1419a068c61a92c0571b28f69fc`
- Semantic branch: `impl/p10-g9-remediation-20260825`

Relative to rejected candidate `ec410a501e7db051f59eb2fb373c30da150bd81a`, the clean candidate changes exactly:

- `context_packaging/prepare_integration.py`
- `tests/test_context_packaging_production_integration_p10_g4.py`
- `tests/test_context_packaging_production_integration_p10_g9_remediation.py`

Temporary patch-transport helpers are absent from the frozen candidate tree.

## Corrected G8 evidence tuple

Evidence PR: `#90`

Successful run:

- Run: `32923357528`
- Job: `98041197660`
- Evidence workflow head: `86a327a7a4584051719525a7d82b381bef7755a7`
- Artifact id: `9590605177`
- Artifact: `p10-g8-ae5d5c21-evidence`
- Artifact digest: `sha256:6fcb6a56cd53ce60d801e519dd52a630d68ea94af9bbc859ba2fce252108b974`

Candidate binding:

- Commit: `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`
- Tree: `81178c5efdc8f1419a068c61a92c0571b28f69fc`

Package binding:

- Version: `0.0.0-p10-g8-r2`
- Content identity: `sha256:fad84921ef302bbca28d48d7427677010526213f69d913cf743dd334193dac96`
- Transport SHA-256: `c7338985caf1a8147c7dd5457b3570e5f9cf6314087c7ac2468915a7d821902e`
- Manifest SHA-256: `cb83fadacf32e106800901e266d18b91c908d5feaf515e49c3a02a4d0204d4b7`
- Managed file count: `97`

Runtime binding:

- Implementation: `cpython`
- Version: `3.12.0`
- Cache tag: `cpython-312`
- Runner: `Linux X64`
- Image: `ubuntu24`, `20260816.277.1`
- Executable SHA-256: `dff2212b560fa5591efed5375998288dd1238dbc5da44618dbc1d3777e08ffe8`

## Observed result

Run `32923357528` completed successfully. The job metadata records success for exact candidate/runtime binding, deterministic package build and managed-root rehydration, historical v0.5.3 G7 assets, complete P10, fixed production `/1`, unaffected P0-P9, all P1b negatives except PS-19, isolated PS-19 reproduction, package/installer regressions, artifact upload, and the final corrected full-G8 enforcement step.

The evidence bundle records status `0` for:

- `p10_complete`
- `production_v1`
- `p0_p9`
- `p1b_negatives_except_ps19`
- `ps19_inherited_baseline`
- `package_installer`

Engineer execution result: `P10_G8_FULL_REGRESSION_ENGINEER_EXECUTION_PASS`.

`P10_INDEPENDENT_REVIEW_PASS` is not established by this Engineer evidence.

## Next boundary

The next consequential action belongs to a fresh independent P10-G9 implementation reviewer. The reviewer must independently re-resolve live coordination and governing contracts, bind this immutable semantic candidate and candidate/package/runtime evidence, challenge both remediated findings and the complete G9 gate, and issue only a P10-G9 independent-review disposition.

The evidence branch is transport and evidence only; it is not the semantic candidate.
