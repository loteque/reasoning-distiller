# P4 Independent Engineer Review — `c5e265aa2c572b6156c987bfa75e3740c097f2ec`

## Review identity

- Repository: `loteque/reasoning-distiller`
- Review scope: independent P4 COVE adapter review only
- Live-main contract basis re-resolved immediately before review evidence write: `7d3127e157f8df2d5e871a30c08e3190848b17e0`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Closed P3 semantic base: `197956138e6181ed9f9aae1d6a40b9f5084695a8`
- P3 Steward reconciliation evidence: `653d9aff48641e59e5e0b60eed41aa2caa0bb375` / `P3_STEWARD_RECONCILIATION_ACCEPTED`
- Exact P4 candidate: `c5e265aa2c572b6156c987bfa75e3740c097f2ec`
- Candidate parent: `197956138e6181ed9f9aae1d6a40b9f5084695a8`
- Candidate tree: `d1d56a4fec46b63b84634f9736d5032325eee018`
- Candidate-bound workflow run: `32670251997`
- Candidate-bound workflow job: `97269899394`
- Candidate-bound artifact: `9501166842`
- Candidate-bound artifact digest: `sha256:172c85605f4a473519ac2d644c4ec9b36119d16bba45e6aacbc9e6156dcc797f`
- Review date: 2026-08-23

This artifact records an independent Reasoning Graph Protocol Engineer review disposition. It does not establish Steward authority or activation, Steward reconciliation, admission, merge, canonical standing, production authorization, P4 closure, or authorization to begin P5.

## Governing evidence inspected

The review was reconstructed from live repository and immutable GitHub evidence rather than prior chat conclusions, including:

- `agents/engineer/DIRECTIVE.md@7d3127e157f8df2d5e871a30c08e3190848b17e0`;
- `docs/governance/PROPOSAL_REVIEW_METHOD.md@7d3127e157f8df2d5e871a30c08e3190848b17e0`;
- `docs/operations/PROJECT_CHAT_TRANSITION_AMENDMENT.md@7d3127e157f8df2d5e871a30c08e3190848b17e0`;
- `docs/proposals/context-packaging/FINAL_PLAN.md@0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`;
- P3 Steward reconciliation evidence `653d9aff48641e59e5e0b60eed41aa2caa0bb375`;
- `schemas/context-pack.schema.json@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `docs/design/CONTEXT_PACKAGING_BYTES_DIGESTS_TOOLCHAIN_CONTRACT.md@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `tests/fixtures/context-packaging-protocol-schema-p1b.json@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `tests/fixtures/context-packaging-bytes-digests-toolchain-p1c.json@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `tests/support/context_packaging_p1c_reference.py@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `admission/apply_admission_transaction.py@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `context_packaging/pems_projection.py@197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- `context_packaging/cove_adapter.py@c5e265aa2c572b6156c987bfa75e3740c097f2ec`;
- `context_packaging/__init__.py@c5e265aa2c572b6156c987bfa75e3740c097f2ec`;
- `docs/design/CONTEXT_PACKAGING_COVE_ADAPTER_P4.md@c5e265aa2c572b6156c987bfa75e3740c097f2ec`;
- `tests/test_context_packaging_cove_adapter_p4.py@c5e265aa2c572b6156c987bfa75e3740c097f2ec`;
- candidate-bound workflow definition `.github/workflows/p4-context-packaging-candidate-evidence.yml@997079ef4f882ac505442d8c00a0443b0f82935d`;
- candidate-bound workflow run `32670251997`, job `97269899394`, artifact `9501166842`.

The current live `main` matches the supplied review basis and does not alter the immutable candidate or governing P4 gate.

## P4 scope reconstructed

The governing P4 gate is limited to a package-owned COVE adapter. The plan requires the implementation to reuse or extract existing package-owned COVE primitives behind the frozen adapter boundary, without duplicating or reinterpreting COVE semantics. The public tuple is `cove/1 | pems/2 | jcs/1`. P4 exits only when exact PEMS round-trip and repeated-byte determinism pass for every supported tuple.

The frozen P1 boundary is composite:

1. P1b closes the public `cove_payload` shape to `cove/1`, `pems/2`, and `jcs/1` and reserves the `cove_adapter` toolchain role.
2. P1c requires exact immutable behavior identity and raw digest for a COVE adapter whenever COVE participates in a pack, and requires behavior/toolchain drift to be visible.
3. P4 owns the concrete encode/decode implementation and round-trip validation rather than P1c redefining COVE behavior.

P4 does not own P5 pack construction, persistence, rendering, production integration, canonical mutation, reconciliation, admission, role mutation, authorization mutation, or activation creation.

## Candidate analysis

The exact candidate conforms to that boundary:

1. `SUPPORTED_TUPLES` contains exactly one tuple: `cove/1 | pems/2 | jcs/1`.
2. The adapter reuses the package-owned COVE structural encoder and decoder from `admission/apply_admission_transaction.py` rather than cloning their COVE algorithm. The reused source is pinned to Git blob `0f0117a7770f1928e41bd76082d9a572102e823a`, and loading fails closed when the on-disk artifact does not match that immutable identity.
3. The reused encoder itself deterministically derives a sorted string dictionary, sorted shape set, and structural `x` representation. P4 does not call the admission transaction, normalize PEMS, apply an admission plan, or mutate canonical state.
4. P4 deliberately does not adopt the admission helper's local sorted-JSON helper as `jcs/1`. It serializes through the exact P3 JCS implementation inherited from the closed P3 base. That implementation was previously parity-checked against the frozen P1c JCS behavior during P3 evidence.
5. `encode_cove_pems` deep-copies its input, requires PEMS/2, invokes the frozen structural encoder, decodes the result, and requires exact equality with the original PEMS object before success.
6. Encoding is repeated from the decoded object and must reproduce byte-identical canonical JCS output. This makes repeated-byte determinism an enforced success condition rather than only a test expectation.
7. `decode_cove_pems` accepts bytes only, parses strict JSON with duplicate-member rejection, requires the exact closed envelope member set and supported semantic tuple, structurally decodes it, and then re-encodes it with the frozen encoder.
8. A decoded envelope succeeds only when the re-encoded structure equals the supplied structure and the canonical JCS bytes equal the exact input bytes. Alternate tuple values, extra members, unused dictionary additions, whitespace/noncanonical encodings, and structurally different representations fail closed.
9. The adapter performs no PEMS semantic rewrite. PEMS validity remains the upstream P3 responsibility; P4 is a structural lossless adapter over the exact PEMS value it receives.
10. The candidate changes only the adapter, its package export surface, its P4 implementation note, and its P4 tests. No P5 builder, persistence, renderer, production, admission, reconciliation, or authority implementation is introduced.

No P4-local semantic contradiction, lossy transformation, input mutation, hidden normalization, tuple ambiguity, deterministic-order dependency, malleability acceptance, or authority-boundary violation was identified.

## Candidate-bound execution evidence

Workflow run `32670251997`, job `97269899394` was inspected directly. The workflow checked out detached candidate `c5e265aa2c572b6156c987bfa75e3740c097f2ec` rather than the evidence branch, and mechanically verified:

- exact candidate HEAD;
- exact P3 parent `197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- P4 adapter blob `3a85c5cf3a705e93bb53adbda4ebdaa67d8f07e9`;
- P4 test blob `35c784b78468eba6ac8286c8f6ece8e8746ac2d2`;
- frozen package-owned COVE source blob `0f0117a7770f1928e41bd76082d9a572102e823a`.

The exact P4 gate completed **7/7 PASS**. The unaffected earlier context-packaging regressions completed **91 PASS + 146 subtests PASS**. The inherited P1b suite was then executed separately and reproduced exactly one known PS-19 classification-harness failure, with the remaining four P1b tests passing. The workflow itself concluded success because that inherited red was asserted rather than hidden.

Artifact `9501166842` was produced with digest `sha256:172c85605f4a473519ac2d644c4ec9b36119d16bba45e6aacbc9e6156dcc797f`.

This execution evidence supports but does not substitute for the independent semantic review. The reviewer does not claim a separate local test execution.

## Findings

### Blocking findings

**None identified in the exact P4 candidate.**

### Required P4 amendments

**None.**

### Boundary observations

#### Exact COVE provenance

The P1 artifacts freeze the public tuple and the mechanism requiring an immutable behavior-binding `cove_adapter` toolchain component; they do not, in the inspected P1 fixture, separately enumerate `admission/apply_admission_transaction.py` as a P1 sample toolchain component because that sample carries no COVE payload. P4 therefore supplies the concrete immutable behavior binding by pinning the exact existing package-owned COVE source blob.

This satisfies the reviewed P4 boundary, but later reconciliation should preserve the distinction: P1 froze the adapter contract/toolchain-binding rules; the exact reused implementation blob is concretely bound by the P4 candidate. No claim is made here that a standalone P1 `COVE_ADAPTER_CONTRACT.md` artifact exists.

#### Reuse coupling

Loading the exact COVE primitives from the admission transaction module creates conservative implementation coupling to a larger artifact. The governing plan explicitly permits reuse or extraction, so this is not a P4 blocker. The whole-source blob check also fails visibly if any part of that artifact drifts before load, even when unrelated to COVE.

A future extraction into a narrower package-owned COVE module would change behavior/toolchain identity and must not be treated as a transparent refactor without the evidence required by the gate in which that change occurs.

#### One-process cache behavior

The adapter caches the verified frozen module after first successful load. This does not defeat the reviewed immutable-candidate P4 round-trip gate, but P7 reproducibility/toolchain-perturbation work should exercise changed behavior identities and process/replay boundaries rather than assuming a hot in-process file mutation is equivalent to an immutable replay.

## External red-check observation

The inherited P1b PS-19 classification-harness mismatch is directly reproduced by the candidate-bound workflow and is unchanged by P4. It is outside the P4 semantic candidate and is neither fixed nor erased by this disposition.

No broader repository-wide red observation is declared fixed, admitted, or irrelevant by this review merely because the P4 gate passes.

## Independent disposition

**`P4_INDEPENDENT_REVIEW_PASS`**

Rationale: the exact immutable candidate reuses rather than redefines package-owned COVE structure, binds the reused behavior immutably, enforces exact PEMS structural round-trip, enforces byte-identical repeated canonical encoding, rejects unsupported/malleable/noncanonical inputs, and remains contained to the P4 adapter boundary. Candidate-bound execution independently confirms the required gate and unaffected regressions, while preserving the known inherited PS-19 red separately.

This disposition is an independent Engineer recommendation only. It does not close P4, establish Steward authority or activation, perform Steward reconciliation, admit or merge the candidate, grant canonical standing or production authorization, or select P5.

## Exact next action

A fresh **Project Steward** activation may independently establish whatever Steward authority and accepted activation the live contracts require for `semantic_reconciliation`, then reconcile exact P4 candidate `c5e265aa2c572b6156c987bfa75e3740c097f2ec` against this independent review and the candidate-bound execution evidence.

Do not begin P5 during that reconciliation. A chat handoff, role label, or this review disposition does not itself establish Steward authority or accepted activation evidence.
