# P5 Independent Review: Pure Pack Build

Disposition: **P5_INDEPENDENT_REVIEW_CHANGES_REQUIRED**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision inspected and re-resolved before review evidence writes: `40241e24ecca2dacf0848ee28cf1ddc1410d15f1`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- P5 semantic candidate: `a8a0592a69b325d411b36bbc97deadee796c3fd7`
- Direct P4 parent: `c5e265aa2c572b6156c987bfa75e3740c097f2ec`
- Candidate implementation branch re-resolved during review: `implement/context-packaging-p5` was identical to the candidate.
- Active review role: independent Reasoning Graph Protocol Engineer, P5 review/evidence only.

This review does not establish or begin P6 persistence, Steward reconciliation, admission, authority, authorization, registration, or activation.

## Candidate-bound execution evidence

Evidence workflow branch: `evidence/context-packaging-p5-a8a0592a-independent-20260823`

Latest evidence workflow definition commit: `d92385b501a1af72604d00e8138d550dd2e6fd26`

Candidate-bound Actions evidence:

- workflow run: `32679550957`
- job: `97293691062`
- artifact: `9503712839`
- artifact digest: `sha256:91dffd9be3e74524ae4a80b995fa0ea2ea930fd3e60456e460665dce2a686b64`

The workflow checked out the semantic candidate itself in detached-HEAD state and verified:

- candidate: `a8a0592a69b325d411b36bbc97deadee796c3fd7`
- parent: `c5e265aa2c572b6156c987bfa75e3740c097f2ec`
- `context_packaging/pack_builder.py` blob: `b0e806e966598e6d819b6d52c643efa23cdb6ef9`
- `tests/test_context_packaging_pack_builder_p5.py` blob: `66f8e4f227a1e0bf64ce3b6722ee90cdf7a04493`
- `context_packaging/__init__.py` blob: `d758a0ba698add4e0ac79574b150e0f8d8b19084`
- P5 design-note blob: `e186060e4e8477adddc0f1164dbe4f4a66cb98b5`

Execution results:

- exact P5 suite: **16 passed**
- unaffected context-packaging regressions from the retained P0 pressure baseline plus P1a/P1c/P1d/P1e/P2/P3/P4: **98 passed, 146 subtests passed**

The known P1b negative-fixture file was intentionally excluded from the unaffected green regression set and executed separately as an inherited red.

## Inherited reds preserved separately

These reproduced on the exact candidate and are not used as P5-local blocking findings:

1. P1b PS-19 classifier mismatch: `1 failed, 4 passed`; expected `UNKNOWN_SEMANTICS_FIELD`, observed `PLANE_CLASSIFICATION_CONFLICT`.
2. Runtime-isolation/schema issue: `tests/test_runtime_isolation_p5.py` reproduced one failure because `schemas/context-pack.schema.json` contains the forbidden runtime repository reference at `$.$defs.knowledgeItem.properties.pems.$ref`.
3. Extraction-parity Distiller-directive issue: `agents/distiller/DIRECTIVE.md` expected blob `d578841d64da93f0883686eda80f00fde53d5f66` but candidate contains `81291456b127015b813af4eda4046397b4815037`; the other copied-artifact integrity entries passed.

All three inherited-red commands returned nonzero status and were captured separately in artifact `9503712839`.

## P5-local blocking findings

### 1. New canonical pack output preserves noncanonical uppercase SHA-256 spelling

The normative P1c bytes/digests/toolchain contract distinguishes permissive P1b input compatibility from canonical builder output: P1b schemas may accept uppercase hexadecimal, but a builder emitting a new canonical P1c pack MUST emit lowercase hexadecimal for SHA-256 fields. The frozen rule explicitly covers raw source/content digests, canonical `pems_sha256`, COVE payload raw digests, toolchain component raw digests, and receipt byte digests.

Candidate `a8a0592a...` validates SHA-256 spellings for several caller-supplied identities but does not canonicalize them when copying them into the new pack. Its direct P5 tests intentionally assert that an uppercase canonical `pems_sha256` and an uppercase toolchain `raw_sha256` remain uppercase in emitted pack data.

An independent candidate-bound pressure probe reproduced both behaviors:

- uppercase `source_registry[*].pems_sha256` was emitted unchanged;
- uppercase `toolchain.components[*].raw_sha256` was emitted unchanged.

This means hexadecimal presentation alone can alter canonical serialized pack bytes and identities even where earlier source-identity comparison semantics treat the digest spellings as equivalent. That conflicts with the frozen P1c canonical-output rule.

Required before P5 acceptance: canonicalize every SHA-256 spelling that P5 owns in newly emitted pack structure to the frozen lowercase representation while leaving the underlying source bytes untouched, and replace the two contradictory P5 expectations with case-normalization/equivalence pressure cases.

### 2. P5 rejects a P1d/P3-valid `(namespace, id)` collision because the outer ledger loses namespace

P1d explicitly freezes PEMS visited identity as `(namespace, id)`, with `record.id` and `relation.id` declaring distinct namespaces. P3 preserves those namespaces in `ProjectionCause` and successfully projects a valid document where a record and a relation share the same string ID.

P5 instead builds the outer knowledge ledger around the P1b `semantic_id` field alone. It detects a record/relation string-ID collision and returns `PEMS_SEMANTIC_INVALID` with diagnostic `selection provenance cannot identify colliding record/relation ids` before emitting the ledger.

An independent candidate-bound pressure probe established both halves on the exact candidate:

- P3 accepted and projected a document containing the same string ID in the record and relation namespaces, with distinct namespaced causes;
- P5 rejected that P3 result as `PEMS_SEMANTIC_INVALID`.

The projected PEMS is not semantically invalid under the frozen P1d/P3 boundary. The representational problem is that the frozen outer ledger subject does not carry the PEMS namespace needed to preserve the already-frozen identity model.

Required before P5 acceptance: resolve the protocol representation mismatch through the appropriate governed contract change so P5 can preserve deterministic selection provenance for both namespaces without silently redefining valid PEMS as invalid. This review does not authorize changing the frozen P1b schema or any earlier accepted contract; it only records that the current P5 candidate cannot satisfy the P5 provenance exit criterion for the full P1d/P3-valid input domain.

## Disposition

`P5_INDEPENDENT_REVIEW_CHANGES_REQUIRED`

The green exact suite and unaffected regressions are valid execution evidence but do not override the two P5-local semantic blockers above. The three inherited reds remain separate and do not contribute to this disposition.

P5 is not closed by this review. No P6 persistence, Steward reconciliation, admission, authority, authorization, registration, or activation work begins from this review.