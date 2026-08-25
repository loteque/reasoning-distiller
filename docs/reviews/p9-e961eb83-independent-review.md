# P9 Independent Review: Deterministic Renderer

Disposition: **P9_INDEPENDENT_REVIEW_CHANGES_REQUIRED**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision independently resolved before review: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Coordination revision re-resolved immediately before disposition/write: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Closed P8 base: `05d9d7b0141cd7fa5e66dd72533b57e046001247`
- Exact P9 candidate: `e961eb83d2c5dd1719b986c89a8915c102e395c3`
- Exact candidate parent: `05d9d7b0141cd7fa5e66dd72533b57e046001247`
- Exact candidate tree: `7af9655fc59e67b7659b1c0479314ed8d402d38b`
- Candidate branch re-resolved before disposition: `implement/context-packaging-p9@e961eb83d2c5dd1719b986c89a8915c102e395c3`
- Renderer blob: `7d28edfa63302475343b2e8b10ef0309089429ff`
- Renderer contract blob: `c8f18df390f92bfd25d6ac01c5932aeaf3ac396c`
- Renderer-profile schema blob: `768bcae7051e2805594df6d45402d331dc43bda4`
- Rendered-activation schema blob: `f52c6007be3e7aa84c7e65f5e0708641e6920367`
- P9 test blob: `335c139a6e6ddf08434fdc16e7a6e249ef093bdf`
- Engineer evidence commit: `17546bbc2e7fefd2245cc8aeed512e69b3aac9aa`
- Engineer evidence workflow run: `32805121766`
- Engineer evidence original attempt: `1`, PASS
- Engineer evidence original artifact: `9547867811`
- Fresh independent rerun: run `32805121766`, attempt `2`, PASS
- Fresh rerun artifact: `9548431522`
- Active role: fresh independent Reasoning Graph Protocol Engineer, P9 review only.

The current Engineer directive, Project chat-transition amendment, and proposal-review method were read from the exact live coordination revision. This review establishes no Steward authority, reconciliation, admission, canonical standing, authorization, activation, P10, canonical mutation, authority mutation, or other successor scope.

## Independent reconstruction of the P9 gate

The governing plan makes P9 the deterministic-renderer gate. The renderer must be a pure function of the supplied canonical pack and renderer profile; preserve control, knowledge, and operational-evidence planes structurally through framing and decoding; discover nothing; use deterministic byte representation; fail rather than truncate, rank, summarize, or silently omit content; and make renderer behavior identity visible in replay identity.

The governing reproducibility requirement remains applicable when rendering is performed: replay identity must bind the renderer contract/implementation by immutable artifact identity or a normative package content identity that fixes the relevant behavior bytes. P9 therefore cannot treat a caller-declared renderer digest as proof that the executing implementation has those bytes.

The frozen P9 renderer contract repeats this requirement. It says the renderer profile binds the exact renderer implementation as a toolchain component with contract, immutable identity, and raw SHA-256, and that the exact renderer blob contains the repository-owned parsing and serialization behavior used by P9.

## Candidate inspection

Candidate `e961eb83d2c5dd1719b986c89a8915c102e395c3` is one commit above closed P8 base `05d9d7b0141cd7fa5e66dd72533b57e046001247` and has tree `7af9655fc59e67b7659b1c0479314ed8d402d38b`.

The candidate delta is limited to:

- `.gitattributes`
- `context_packaging/__init__.py`
- `context_packaging/renderer.py`
- `protocols/rgp/context-renderer-v1.json`
- `schemas/context-rendered-activation.schema.json`
- `schemas/context-renderer-profile.schema.json`
- `tests/test_context_packaging_deterministic_renderer_p9.py`

The new renderer keeps repository-owned strict-JSON and JCS behavior local to `renderer.py`, so mutable project helper implementations are not consulted by rendering/decoding. The exact renderer blob is therefore the behavior-bearing repository artifact for the P9 rendering implementation.

## Structural-plane and renderer behavior inspection

No blocking defect was identified in the inspected structural framing itself.

- Plane classification is taken from the canonical pack containers and emitted as explicit frame metadata in fixed order: `control`, `knowledge`, `operational_evidence`.
- Frame payloads are canonical JCS bytes encoded with standard Base64 and bound by SHA-256.
- Decoding verifies canonical activation bytes, activation identity, profile/component fields, frame order, Base64, frame digests, canonical frame payloads, and the reconstructed canonical-pack byte digest before returning the reconstructed pack.
- Instruction-like knowledge bytes remain inside a structurally knowledge-classified frame and are not parsed by the renderer as control, role, authority, activation, or trust semantics.
- Identical text in control and knowledge remains in separate frames rather than being deduplicated by content.
- The activation-byte limit is checked after the activation identity is attached; overflow returns `RENDER_LIMIT_EXCEEDED` without a partial activation.
- Rendering and decoding use only supplied values plus standard-library computation. No repository discovery, filesystem lookup, network call, model call, semantic search, ranking, summarization, persistence, cache mutation, canonical mutation, reconciliation, admission, authorization, or activation path was identified.

The decoder does not independently rederive the P5 semantic `pack_identity_sha256`, but it does reconstruct the full pack bytes, recompute the canonical serialized-pack SHA-256, and require the activation pack summary to match that reconstruction. Given P9's input contract is a canonical pack, I do not classify that distinction as a separate P9 blocker.

## Pressure-case inspection

The frozen pressure fixture binds the relevant P9 cases:

- PC-33: instruction-like admitted knowledge must remain knowledge and cannot promote itself into control/instruction semantics.
- PC-44: a renderer activation-byte overflow must fail with `RENDER_LIMIT_EXCEEDED`, never summarize/rank/omit.
- PC-45: equal text under distinct control/knowledge identities must remain distinct structurally.
- PC-46: equivalent contracted inputs/behavior identity must remain byte-identical despite host representation/order differences.

The P9 suite executes concrete semantic attacks for PC-33, PC-44, and PC-45. It also executes insertion-order perturbation and exact-byte round-trip determinism for the new renderer. The pressure-case membership test itself only verifies the PC-46 fixture entry rather than running a separate renderer-specific cross-host matrix. Source inspection shows the renderer does not consult locale, path separators, temporary paths, filesystem enumeration, or host-local source discovery, and its object ordering is explicit. I record the narrower PC-46 test shape as a review note, not the blocking finding below.

## Candidate-bound Engineer evidence inspected

The Engineer evidence commit `17546bbc2e7fefd2245cc8aeed512e69b3aac9aa` is directly above exact P9 candidate `e961eb83d2c5dd1719b986c89a8915c102e395c3` and adds the P9 evidence workflow.

The workflow explicitly checks out the exact P9 candidate, verifies its exact P8 parent and bounded candidate delta, verifies the exact renderer/contract/schema/test blobs, compiles the renderer and test module, runs the exact P9 pytest and unittest gates, runs unaffected P0-P8 context-packaging regressions, reproduces the inherited P1b PS-19 classifier mismatch separately, and uploads identity/test evidence.

Original run `32805121766`, attempt 1, completed successfully. Original artifact `9547867811` records the exact candidate, parent, tree, renderer blob, contract/schema/test blobs, and inherited dependency blobs.

## Fresh independent execution

This review independently re-ran the already-inspected candidate-bound P9 workflow. GitHub recorded the fresh execution as run `32805121766`, attempt `2`, and it completed successfully.

Observed attempt-2 evidence:

- exact candidate/parent/tree/blob verification: PASS
- exact P9 pytest gate: **22 passed**
- exact P9 unittest gate: **11 tests, all PASS**
- unaffected P0-P8 context-packaging regressions: **165 passed, 2 deselected, 162 subtests passed**
- inherited P1b PS-19 classifier mismatch: reproduced separately as expected
- attempt-2 artifact: `9548431522`

The fresh green execution confirms that the declared P9 suite is stable and candidate-bound. It does not cure the independent identity defect below.

## Blocking finding

### `P9_RENDERER_COMPONENT_IDENTITY_UNBOUND`

**Severity: blocking for P9 deterministic rendering/replay identity.**

The P9 renderer profile contains a `renderer_component` object with `contract`, `immutable_identity`, and `raw_sha256`, but the executing renderer never proves that those supplied identifiers describe the renderer implementation that is actually running.

`_profile(...)` verifies that the exact profile raw bytes parse to the supplied profile object, requires the expected profile fields, and passes `renderer_component` through `_component(...)`. `_component(...)` verifies field shape, string presence, Git-blob syntax, and SHA-256 syntax. `_profile(...)` additionally verifies only that the component role is `renderer` and contract is `reasoning-distiller-context-renderer/1`.

No renderer path derives the Git-blob identity or raw SHA-256 of the executing `renderer.py` implementation, compares the supplied component identity to a frozen implementation identity, or otherwise resolves an immutable package/content identity that contractually fixes the executing renderer bytes.

Consequently a caller can supply a profile whose renderer component contains any syntactically valid Git-blob identity and SHA-256, with matching exact profile raw bytes. The candidate will accept that profile and render an activation that records the caller-supplied component identity. The decoder will require consistency with that same supplied profile, but it still does not prove that the declared component is the code that executed.

This leaves a material replay-identity gap. If the renderer implementation changes while an old renderer profile is reused, the declared renderer component identity can remain unchanged even though the behavior-bearing implementation artifact has changed. The activation's profile SHA and activation SHA bind the supplied profile and output bytes, not the identity of the executing implementation. Therefore the recorded replay identity does not necessarily make a renderer implementation change visible.

This is the same class of identity defect that P7 treated as blocking for behavior-bearing builder dependencies: an identity field is insufficient when the runtime graph can execute behavior bytes not immutably fixed by that identity. P9 deliberately moved repository-owned JSON/JCS behavior into `renderer.py`; that successfully removes mutable repository-helper dependencies, but it makes the exact renderer blob itself the critical behavior artifact that must actually be bound.

The P9 tests construct the renderer profile by reading the current local `renderer.py` bytes and placing their Git-blob/SHA-256 identities into the profile, so the happy-path test fixture is truthful. The suite does not adversarially prove that a false/stale renderer-component identity is rejected, nor that changed renderer behavior cannot execute while the previously recorded component identity remains constant.

## Required remediation evidence

A remediated P9 candidate must establish, using a mechanism permitted by the frozen plan/contracts, that the declared renderer component identity immutably binds the exact behavior-bearing renderer implementation that executes rendering/decoding. The solution must preserve the P9 purity boundary rather than silently introducing forbidden discovery or mutable state.

The remediated gate must include an adversarial regression that holds the previously declared renderer component identity constant while changing the behavior-bearing renderer implementation or its effective implementation identity, and proves fail-closed/incompatibility rather than silently accepting the stale identity.

If the frozen renderer-profile/protocol basis cannot express such a binding without amendment, that is a governance boundary. An implementation Engineer must stop there and hand off rather than silently revising frozen semantics.

## Independent review disposition

**P9_INDEPENDENT_REVIEW_CHANGES_REQUIRED**

Candidate `e961eb83d2c5dd1719b986c89a8915c102e395c3` passes its declared P9 structural-plane, deterministic render/decode, PC-33/44/45, purity, byte-bound, schema, exact-pack round-trip, and regression suites, including a fresh independent rerun. However, it does not establish that the renderer component identity recorded in the renderer profile/activation is the identity of the renderer implementation that actually executed.

Because renderer implementation identity is explicitly part of the governing replay-identity requirement and the frozen P9 renderer contract claims an exact implementation binding, this defect is P9-blocking rather than a deferrable hardening item.

P9 is not independently accepted or closed by this review. P9 Steward reconciliation is not established. No P10, admission, canonical mutation, authority mutation, activation, or unrelated successor work begins from this review.

## Terminal boundary and bounded handoff

This P9 independent-review work unit is complete. The next valid consequential work, if selected, belongs in a fresh implementation Engineer activation scoped only to remediation of `P9_RENDERER_COMPONENT_IDENTITY_UNBOUND` against exact candidate `e961eb83d2c5dd1719b986c89a8915c102e395c3` and this review evidence. No P10 or Steward reconciliation should begin unless a remediated exact P9 candidate later receives independent PASS evidence.