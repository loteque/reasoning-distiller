# P7 Independent Review: Reproducibility

Disposition: **P7_INDEPENDENT_REVIEW_CHANGES_REQUIRED**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision independently resolved before review: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Coordination revision re-resolved immediately before disposition: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Closed P6 semantic base: `091e9ac97f0a068045acbcc57e90a934d24f9f7a`
- Exact P7 candidate: `0fb11fe7fb18d615549dc8ce8b86044e95e4bc1a`
- P7 Engineer evidence: `3784fd921e36ff89bb68b313acd7117bb0ef4bea`
- Candidate-bound workflow run: `32768500929`
- Active role: fresh independent Reasoning Graph Protocol Engineer, P7 review only.

The current Engineer directive, Project chat-transition amendment, and proposal-review method were read from the exact live coordination revision. This review establishes no Steward authority, reconciliation, admission, canonical standing, authorization, activation, P8+, or other successor scope.

## Independent reconstruction of the P7 gate

The governing plan defines P7 as the reproducibility gate. It perturbs locale, ordering, filesystem enumeration, path separators, Unicode environment, temporary paths, and toolchain identities. Contracted equivalent inputs must remain byte-identical, while incompatible toolchain changes must fail visibly.

R7 is an accepted reproducibility blocker. Replay identity must bind the schema, semantic validator, closure descriptor, COVE adapter when used, serializer contract, builder contract, and renderer contract when used, either directly by immutable artifact identity or through a normative package content identity that contractually fixes all relevant behavior artifacts. Section 6.4 further requires immutable behavior identity for the pack-builder contract/implementation.

## Candidate and bound-evidence inspection

Across the closed P6 base to the exact P7 candidate, the semantic diff is limited to:

- `.gitattributes`; and
- `tests/test_context_packaging_reproducibility_p7.py`.

The P5 builder and P6 persistence-adapter runtime blobs are preserved. The P7 suite covers host locale/timezone/temp-path variation, path separators, Unicode environment, mapping and sequence order, filesystem enumeration order, direct toolchain-component identity perturbation, and cross-host exact-byte equality.

The Engineer evidence workflow checks out the exact candidate on Linux and Windows, verifies the exact P6 merge base and bounded diff, verifies the preserved runtime blobs, checks byte-transport attributes for selected identity-bearing artifacts, runs the exact P7 pytest and unittest gates, runs unaffected P0-P6 regressions, and compares canonical pack bytes across native `/` and `\\` hosts.

The supplied run completed successfully. Its original cross-host comparison reported:

- `P7_CROSS_HOST_BYTE_IDENTITY_PASS`
- serialized pack SHA-256: `sha256:18342ab665edc1010fa8bc608cb4df3d66049eda2882b1a061dc3a7b739bf041`
- pack identity SHA-256: `sha256:a235dc025b30c2eaa7c416af300e9f2ae72778bb2bc60a4aec91efb2e03ff3ff`

## Fresh independent execution

This review did not rely only on the Engineer disposition. I triggered a fresh rerun of the candidate-bound workflow and inspected the resulting jobs.

Fresh rerun observations for run `32768500929`, attempt 2:

- Linux P7 job: `97592790730` — PASS
- Windows P7 job: `97592792642` — PASS
- P0-P6 regression job: `97592791832` — PASS
- cross-host comparison job: `97592857516` — PASS
- exact Linux P7 pytest gate: `4 passed, 2 subtests passed`
- exact Linux P7 unittest gate: `4/4 PASS`
- fresh cross-host marker: `P7_CROSS_HOST_BYTE_IDENTITY_PASS`
- serialized pack SHA-256 remained `sha256:18342ab665edc1010fa8bc608cb4df3d66049eda2882b1a061dc3a7b739bf041`
- pack identity SHA-256 remained `sha256:a235dc025b30c2eaa7c416af300e9f2ae72778bb2bc60a4aec91efb2e03ff3ff`

The fresh execution confirms the implemented P7 suite is stable and candidate-bound. It does not cure the independently identified coverage/identity defect below.

## Blocking finding

### `P7_PACK_BUILDER_TRANSITIVE_IDENTITY_UNBOUND`

**Severity: blocking for P7 reproducibility.**

The `/2` pack builder's recorded `pack_builder` toolchain identity does not bind the complete implementation that actually determines pack behavior.

`context_packaging/pack_builder.py` imports `context_packaging/pack_builder_v1.py` as `_v1` and delegates behavior-bearing operations to it, including source indexing, control/operational-plane construction, canonical source registry handling, failure construction, pack identity construction, and JCS serialization helpers. In particular, finalization calls `_v1._build_identity(...)` and `_v1._jcs(...)`.

The P5/P7 toolchain fixture, however, constructs the `pack_builder` component from `context_packaging/pack_builder.py` alone. Its immutable identity and raw SHA-256 therefore do not change when `context_packaging/pack_builder_v1.py` changes. The v2 pack schema exposes a single `pack_builder` component role and the candidate establishes no normative package content identity that contractually binds `pack_builder.py`, `pack_builder_v1.py`, and all relevant builder behavior bytes as one implementation identity.

This creates an unrepresented behavior-change path: replay can present the same declared `pack_builder` identity while executing changed helper implementation bytes. Such a change cannot be classified as compatible or incompatible from the recorded replay identity because the changed behavior artifact is absent from that identity. Therefore P7 has not established the R7 requirement that replay identity bind the builder contract/implementation, nor the P7 requirement that incompatible toolchain changes fail visibly.

The candidate's `.gitattributes` byte-transport protections reinforce the gap: `context_packaging/pack_builder.py` is marked `-text`, but `context_packaging/pack_builder_v1.py` is not. This is not the primary defect by itself; it is evidence that the P7 transport proof does not treat the helper as an identity-bearing builder implementation artifact.

For comparison, the P4 COVE adapter explicitly pins its loaded package-owned encoder/decoder source with a frozen Git-blob identity and fails when those bytes do not match, so the same transitive-identity objection is not being generalized mechanically to every helper dependency.

## Required remediation evidence

A remediated P7 candidate must establish, without silently changing frozen protocol semantics, that the recorded `pack_builder` replay identity immutably binds every behavior-bearing builder artifact actually used by `/2`. An implementation may satisfy that requirement only through a mechanism permitted by the governing contracts, for example by:

1. making the recorded builder implementation identity transitively bind and verify the helper implementation bytes;
2. using a normative package content identity whose contract fixes all relevant builder behavior artifacts; or
3. eliminating the unbound runtime dependency so the recorded builder artifact fully contains the behavior it claims to identify.

If satisfying this requirement needs a change to a frozen schema or protocol basis, that is a governance boundary rather than permission for this independent review to amend it.

The remediated P7 gate must also include an adversarial regression that changes a behavior-bearing builder dependency while holding the previously recorded top-level builder identity constant, and must prove that the replay is rejected or otherwise made explicitly incompatible according to the governing contract. Any raw-byte artifact newly made identity-bearing must also be transported byte-exactly across the supported host checkouts.

## Independent review disposition

**P7_INDEPENDENT_REVIEW_CHANGES_REQUIRED**

Candidate `0fb11fe7fb18d615549dc8ce8b86044e95e4bc1a` passes its declared host/environment/order/toolchain perturbation suite and fresh rerun, but it does not prove complete pack-builder implementation identity. Because R7 is explicitly a reproducibility blocker, the missing transitive binding is P7-blocking rather than a deferrable improvement.

P7 is not independently accepted or closed by this review. P7 Steward reconciliation is not established. No P8+, admission, canonical mutation, authority mutation, activation, or other successor work begins from this review.

## Terminal boundary

The P7 independent-review work unit is complete. The next valid action, if selected, belongs to a fresh implementation Engineer activation scoped only to remediation of this P7 blocker against the exact reviewed candidate and evidence. If that Engineer concludes the frozen protocol/schema cannot express a compliant binding, the Engineer must stop at that governance boundary and hand off rather than silently amend earlier frozen semantics.
