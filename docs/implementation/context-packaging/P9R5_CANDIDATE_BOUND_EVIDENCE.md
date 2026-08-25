# P9R5 Candidate-Bound Provenance Reconstruction

## Scope and authority boundary

This Engineer-produced artifact binds immutable provenance and already-observed execution evidence for P9R5 for exact candidate `872ae5f0dfa0a123fe060a5ea17aa85c2de13097`.

This is a static candidate-bound evidence record only. It does not perform P9R6 independent review, Project Steward reconciliation, admission, RIL activation, canonical mutation, authority mutation, or any P10 work. Accepted RIL activation is `NOT_ESTABLISHED` by this artifact.

No candidate byte is modified by this evidence record. The evidence branch is a direct child of the immutable candidate and adds this record only.

## Governing anchors

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision observed immediately before evidence-branch creation: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing implementation plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing implementation plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Governing P9 renderer-identity amendment commit: `373667be85521e6f0f83bf19fed3378357e51118`
- Governing P9 renderer-identity amendment blob: `90142ffe6b6652faceb3e8347f33fa71c8dc3ed9`
- Governing P9 amendment disposition: `P9_RENDERER_IDENTITY_STAGE3_RECONCILED_ACCEPTED_WITH_GATES`

## Exact candidate identity

- Candidate commit: `872ae5f0dfa0a123fe060a5ea17aa85c2de13097`
- Direct parent: `c21535e0d2820b0a1ba1866da60059a450470658`
- Candidate tree: `258b04273404e492dd659fd6733a2b3f2c273b73`
- Renderer: `context_packaging/renderer.py`
- Renderer blob: `cfe478acb3b722ddcd336ea7bdc6a002b56bd787`
- RI-15 remediation regression: `tests/test_context_packaging_renderer_ri15_remediation.py`
- RI-15 remediation regression blob: `cb74f4bf2e44a20cd86092e94226d5991698aa99`

The observed candidate delta from parent `c21535e0d2820b0a1ba1866da60059a450470658` consists of exactly those two files.

## Freeze-before-behavior history

The exact ancestry observed for the P9 stages is:

1. P9R0 pressure freeze: `637da425560f1ab287eacfe90f1e9c167b607a18`
2. P9R1 protocol/schema freeze: `fa91287d0e69d5161c9d8b1acc5da02cc10f6c31`
3. P9R2 closed-bundle behavior: `ebb436a14dee2a67d778e3252892f7be5cd0e2ca`
4. P9R3/P9R4 failed behavior-bearing base: `c21535e0d2820b0a1ba1866da60059a450470658`
5. RI-15 remediation candidate: `872ae5f0dfa0a123fe060a5ea17aa85c2de13097`

This ordered history is the candidate-bound provenance needed to establish that the P9R0 and P9R1 freezes precede P9R2/P9R3 behavior implementation. It is evidence for reconstruction, not an independent-review disposition.

The candidate contains the following implementation-stage records:

| Stage record | Blob |
| --- | --- |
| `docs/implementation/context-packaging/P9R0_RENDERER_IDENTITY_PRESSURE_FREEZE.md` | `f16fbba14e32df57489258dbdfde2f38bdc4e591` |
| `docs/implementation/context-packaging/P9R1_RENDERER_IDENTITY_PROTOCOL_FREEZE.md` | `9be80861d4b22dab1a7221c3c951c71da232fc65` |
| `docs/implementation/context-packaging/P9R2_CLOSED_BUNDLE_REFACTOR.md` | `8cc05b104a1b4db388141e99cb37e68179ae5c6d` |
| `docs/implementation/context-packaging/P9R3_RENDERER_EXECUTION_BINDING.md` | `f2898704ac3fc601574fde5f67f1d6ecba84d1bf` |

## Frozen protocol artifacts

All paths and blob identities below are bound to candidate `872ae5f0dfa0a123fe060a5ea17aa85c2de13097`.

| Protocol artifact | Blob |
| --- | --- |
| `protocols/rgp/context-renderer-v2.json` | `2ebdcdea8d44881cc7cafd72c60885fb8b72df7d` |
| `protocols/rgp/python-closed-bundle-v1.json` | `894320add6f895068819712515f111d699020aa3` |
| `protocols/rgp/renderer-execution-binding-v1.json` | `dd9c92901776233890027923961fcdaa31840afb` |

## Frozen schema artifacts

| Schema artifact | Blob |
| --- | --- |
| `schemas/context-renderer-profile-v2.schema.json` | `9ef040712c14851075e56803ae8e2adf57c31cd4` |
| `schemas/context-rendered-activation-v2.schema.json` | `449c88c71accb0c87d338566b745e5581b464e61` |
| `schemas/renderer-execution-binding.schema.json` | `97c4eac2a9a640eac3e15cb91902b8c5945114c0` |
| `schemas/python-closed-bundle-descriptor.schema.json` | `cf5f550da2d7ce69339b12ae689c20f87554e39e` |

## Candidate-local gate artifacts

| Candidate-local test | Blob |
| --- | --- |
| `tests/test_context_packaging_renderer_identity_pressure_freeze_p9r0.py` | `a89e9fc15216e1b70c80c40b37febbdd2e352cd5` |
| `tests/test_context_packaging_renderer_identity_protocol_freeze_p9r1.py` | `83a593ee44b3e421dce4d5853d1d1e8271e53285` |
| `tests/test_context_packaging_renderer_closed_bundle_p9r2.py` | `c6676797d85951b4b0407c23840ed74d42911d39` |
| `tests/test_context_packaging_renderer_execution_binding_p9r3.py` | `c88ab7d901e8520711c11f5a77c3464c673b4e12` |
| `tests/test_context_packaging_renderer_ri15_remediation.py` | `cb74f4bf2e44a20cd86092e94226d5991698aa99` |
| `tests/test_context_packaging_deterministic_renderer_p9.py` | `335c139a6e6ddf08434fdc16e7a6e249ef093bdf` |

## External execution-harness provenance

The exact runtime execution used a separate transport commit. These transport artifacts are evidence inputs and are not members of the immutable candidate tree.

- Transport commit: `3a7f79ddedbb57aa4860107e39afa6dd7f599637`
- Transport tree: `315ad0bd1464c444e54b2522e8716158c81a4b83`
- Workflow: `.github/workflows/p9-ri15-remediation-builder.yml`
- Workflow blob: `0a695b8ebd1e530b682c68ece3d96f37474347e6`
- External RI harness: `tests/test_context_packaging_renderer_p9r4_external_execution.py`
- External RI harness blob: `5a723affb78fe3b58e4ca936d7becdaa480772b2`
- Corrected-cases harness: `tests/test_context_packaging_renderer_p9r4_corrected_cases.py`
- Corrected-cases harness blob: `c8f35e3dd6377635d4366054b643af50408ba667`

The candidate-local gate artifacts above remain identified by candidate-tree blobs. The workflow and external RI harness remain identified by transport-commit blobs. This record does not collapse those provenance domains.

## Exact runtime execution binding

- GitHub Actions run: `32842231262`
- Job: `97784064477`
- Runtime: CPython `3.12.0`
- Implementation: `cpython`
- `version_info`: `(3, 12, 0)`
- Cache tag: `cpython-312`
- Candidate-local frozen gate result observed in the job: 26 passed
- RI-01 through RI-24: `24/24 PASS`
- External RI main harness: 22 passed, with RI-02 and RI-17 exercised by the corrected-cases harness
- Corrected-cases harness: 2 passed
- Original deterministic P9 pytest gate: 22 passed
- Original deterministic P9 unittest gate: 11 tests, OK
- Unaffected P0-P8 regression gate: 165 passed, 2 deselected, 162 subtests passed
- Enforced execution disposition: `P9_RI15_REMEDIATION_EXECUTION_PASS`

### Separately classified inherited red

The execution also reproduced the inherited PS-19 classifier mismatch separately from P9:

- Test: `tests/test_context_packaging_protocol_schemas_p1b.py::P1b::test_negative_fixtures_reject_and_classify_exactly`
- Actual classification: `PLANE_CLASSIFICATION_CONFLICT`
- Expected classification: `UNKNOWN_SEMANTICS_FIELD`
- Evidence classification token: `P1B_PS19_CLASSIFIER_MISMATCH_REPRODUCED`

This inherited red is recorded separately and is not reclassified as a P9 failure or success by this artifact.

## Boundary and exact next action

This artifact issues no P9R6 independent-review disposition and makes no claim that independent review has passed. It performs no Project Steward reconciliation, admission, role activation, canonical mutation, authority mutation, or P10 work. Accepted RIL activation remains `NOT_ESTABLISHED`.

The next consequential action belongs to a fresh independent Reasoning Graph Protocol Engineer activation. That reviewer must independently re-resolve the live governing contracts, reconstruct all P9 gates from the exact candidate and bound evidence, inspect the immutable history and execution provenance, and issue only the P9R6 independent-review disposition. Steward reconciliation and later stages remain outside that review scope.
