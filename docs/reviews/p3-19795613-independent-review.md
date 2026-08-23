# P3 Independent Engineer Review — `197956138e6181ed9f9aae1d6a40b9f5084695a8`

## Review identity

- Repository: `loteque/reasoning-distiller`
- Review scope: independent P3 Projection review only
- Live-main contract basis re-resolved immediately before review evidence write: `7d3127e157f8df2d5e871a30c08e3190848b17e0`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Closed P2 semantic base: `f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`
- P2 independent review evidence: `200fc6fe8f3095583ac9d2269644c2227319d065` / `P2_INDEPENDENT_REVIEW_PASS`
- P2 Steward reconciliation evidence: `4b66998b53cc5d41955508ed7eefa52d2c73658f` / `P2_STEWARD_RECONCILIATION_ACCEPTED`
- Exact P3 candidate: `197956138e6181ed9f9aae1d6a40b9f5084695a8`
- Candidate parent: `f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`
- Candidate tree: `d6ce3f7e47618f5c663d6350394f9cc024fe9ff3`
- Candidate-bound workflow run: `32665380603`
- Candidate-bound workflow job: `97257846456`
- Candidate-bound artifact: `9499865055`
- Review date: 2026-08-23

This artifact records an independent Reasoning Graph Protocol Engineer review disposition. It does not establish Steward authority or activation, Steward reconciliation, admission, merge, canonical standing, production authorization, or P4 completion.

## Governing evidence inspected

The review was reconstructed from live repository and immutable GitHub evidence rather than prior chat conclusions, including:

- `agents/engineer/DIRECTIVE.md@7d3127e157f8df2d5e871a30c08e3190848b17e0`;
- `docs/governance/PROPOSAL_REVIEW_METHOD.md@7d3127e157f8df2d5e871a30c08e3190848b17e0`;
- `docs/proposals/context-packaging/FINAL_PLAN.md@0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`;
- P2 independent review evidence `200fc6fe8f3095583ac9d2269644c2227319d065`;
- P2 Steward reconciliation evidence `4b66998b53cc5d41955508ed7eefa52d2c73658f`;
- `docs/design/CONTEXT_PACKAGING_SOURCE_IDENTITY_CONTRACT.md@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `docs/design/CONTEXT_PACKAGING_BYTES_DIGESTS_TOOLCHAIN_CONTRACT.md@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `docs/design/CONTEXT_PACKAGING_PEMS_CLOSURE_CONTRACT.md@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `docs/design/CONTEXT_PACKAGING_SOURCE_RESOLUTION_P2.md@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `protocols/rgp/pems2-context-closure-v1.json@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `backends/pems-cove/pems-v2.schema.json@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `backends/pems-cove/validate_pems2_contract.py@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `context_packaging/source_resolver.py@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `context_packaging/pems_projection.py@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `tests/test_context_packaging_pems_projection_p3.py@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- candidate-bound workflow run `32665380603`, job `97257846456`.

The current `main` revision is newer than the implementation's earlier `58b99891e116b5a06dd603810c2b98ea83e328c3` coordination basis. The intervening live-main changes inspected for this review concern platform/chat naming and do not alter the immutable P3 candidate, PEMS closure semantics, PEMS schema/validator, or governing context-packaging plan. Contract interpretation for this review is nevertheless bound to the current live revision above.

## P3 scope reconstructed

The governing P3 gate is limited to exact PEMS selection, semantic closure, and package-owned validation. Its acceptance boundary requires the selected projection to remain valid PEMS/2, preserve the selected semantics and provenance, and produce reproducible closure causes.

P3 is downstream of the frozen P1 profile/request/closure contracts and the closed P2 read-only resolver. It does not own COVE encoding, complete pack construction, persistence, rendering, production `rd-distill` integration, canonical mutation, reconciliation, admission, authorization, or activation.

## Candidate analysis

The exact candidate implements that boundary without broadening it:

1. `project_pems` consumes explicit P1 request/profile values and P2 `ResolvedSource` values; it performs no source discovery or mutable rebinding.
2. The profile-bound closure descriptor is checked against the exact descriptor bytes and Git blob identity. The descriptor in turn binds the exact package-owned PEMS schema and semantic validator blobs.
3. Canonical PEMS bytes are parsed as strict UTF-8 JSON and the complete source document is schema- and semantic-validated before projection.
4. Explicit record and relation selectors are applied exactly. Missing selected IDs fail closed rather than being ignored.
5. Frozen P1d root, reference, external-reference, reject, and structural closure rules are applied deterministically. Undefined/rejected closure behavior fails closed.
6. Closure traversal terminates on the structured `(namespace, semantic_id)` identity and remains cycle-safe. Deterministic cause IDs are collected for explicit selectors and closure additions.
7. Selected records and relations are copied without semantic rewriting, inference, summarization, or provenance alteration. Source record/relation presentation order is preserved for the selected subset.
8. The completed projection is independently revalidated against the exact package-owned PEMS schema and semantic validator.
9. Projection record, relation, depth, and JCS-byte limits fail closed. Required closure is never truncated to fit a bound.
10. The implementation exposes no P4 COVE, P5 pack-build, persistence, renderer, canonical mutation, reconciliation/admission, or authority surface.

No P3-local semantic contradiction, deterministic-order dependency, silent repair, hidden relevance judgment, or authority-boundary violation was identified.

## Candidate-bound execution evidence

Workflow run `32665380603`, job `97257846456` was inspected as candidate-bound execution evidence. It checked out detached candidate `197956138e6181ed9f9aae1d6a40b9f5084695a8`, verified its P2 parent and the behavior-defining P3 support blobs, recorded **JCS parity PASS**, and completed **57/57 PASS**. Artifact `9499865055` was produced; the workflow log recorded artifact ZIP SHA-256 `e3787f14b283a13fbacd3e1534f7e7e167bb77254b26b22756064728bb0dd688`.

This execution evidence supports but does not substitute for the independent semantic review. The reviewer does not claim a separate local test execution.

## Findings

### Blocking findings

**None identified in the exact P3 candidate.**

### Required P3 amendments

**None.**

### Boundary observations

P3 relies on the contracted upstream boundaries rather than redundantly reimplementing them. In particular, `ResolvedSource` is a P2 result type whose resolver has already verified source identity and exact bytes, and P3 performs focused P3 preflight rather than replaying the complete P1b request/profile schema suite. This is acceptable stage composition for the reviewed gate. Later integration must preserve those upstream validation/resolution boundaries rather than constructing unverified values and treating their Python type or shape as proof.

The candidate includes a P1c-equivalent JCS implementation only for deterministic `max_bytes` measurement and its bound workflow records parity against the frozen P1c behavior. Later refactoring may reduce implementation duplication only if it preserves the frozen behavior and receives the evidence required for the gate in which that refactoring occurs.

## External red-check observations

Two externally reported red-check observations were assessed independently against the immutable repository state. Neither is evidence of a P3-local regression.

### 1. Inherited P1b PS-19 / schema-harness observation

The exact inherited P1b fixture defines PS-19 as an unknown `instruction_priority` member under `pack.control_plane.items[0]` with expected classification `UNKNOWN_SEMANTICS_FIELD`. The inherited P1b test classifier, however, broadly classifies mutations under `pack/control_plane/items` as `PLANE_CLASSIFICATION_CONFLICT`. That fixture/classifier mismatch is present unchanged in the P3 candidate's inherited P1b files; P3 changes none of those files.

A related external observation concerned offline/runtime resolution of the P1b context-pack schema's PEMS `$ref`. Direct inspection confirms that the intended P1b schema test constructs an explicit local registry containing the PEMS schema. This independent P3 review did not reproduce or adjudicate the broader external runtime-suite failure, and it does not declare that repository-wide concern fixed.

Disposition for this review: inherited P1b test/harness debt, outside the P3 semantic candidate. It should be reconciled separately without silently changing the frozen P1b contract, but it is not a P3 blocker.

### 2. Inherited Extraction Parity Distiller-directive observation

The externally reported Extraction Parity mismatch concerns the frozen blob identity of `agents/distiller/DIRECTIVE.md`. Direct inspection shows that the exact blob at the closed P2 parent is already `81291456b127015b813af4eda4046397b4815037`. The P3 candidate does not modify that directive.

Disposition for this review: inherited extraction/parity state, not introduced by P3. This review does not declare the external parity baseline repaired or admitted; that remains with the applicable extraction/parity workflow owner.

These external reds therefore remain visible repository-wide follow-up concerns. Passing P3 does not erase or reinterpret them.

## Disposition

**`P3_INDEPENDENT_REVIEW_PASS`**

Candidate `197956138e6181ed9f9aae1d6a40b9f5084695a8` conforms to the reconstructed P3 gate under governing plan `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd` within the independent-review scope. No P3-local blocking finding remains.

The candidate is eligible for a separately governed Project Steward reconciliation step. This disposition is not Steward reconciliation, admission, merge, canonical standing, authorization, activation, or approval to begin P4.