# P9 Renderer Execution-Identity Amendment - Stage 1 RPG Engineer Proposal

Status: **Proposed**
Method: `proposal-review-synthesis/1`
Repository: `loteque/reasoning-distiller`
Coordination control ref: `main`
Coordination revision inspected and re-resolved before this Stage 1 write: `80b6e89ad2efe84b088ca06b908a257c449fac15`
Stage: **Stage 1 independent proposal**
Proposal-author scope: **Reasoning Graph Protocol Engineer**

Authority posture: this artifact is a technical proposal only. The Engineer directive authorizes protocol design and candidate/proposal production but does not confer Project Steward authority, canonical semantic identity, admission authority, or RIL authority. No separate Steward or RIL activation is claimed by this Stage 1 artifact. This proposal does not authorize P9 implementation, P9 reconciliation, P10, admission, canonical mutation, authority mutation, or activation mutation.

## 1. Problem and decision requested

Exact P9 candidate `e961eb83d2c5dd1719b986c89a8915c102e395c3` implements a deterministic renderer whose structural framing, purity boundary, bounds handling, and pack round trip passed its declared candidate-bound and fresh independent tests. Independent review `ff482ffcac5b58133ee3a480bab4164ee599732f` nevertheless found a P9-blocking replay-identity defect: `P9_RENDERER_COMPONENT_IDENTITY_UNBOUND`.

The frozen P9 profile currently contains a caller-supplied `renderer_component` with `contract`, `immutable_identity`, and `raw_sha256`. The renderer validates the syntax and internal consistency of those supplied values but does not establish that they identify the behavior-bearing renderer implementation that is actually executing. A stale profile can therefore continue to declare the old renderer identity after the executing renderer behavior has changed.

The implementation cannot close that gap by copying the P7 source-file strategy. P9 explicitly requires rendering and decoding to perform no filesystem or repository lookup, and the renderer must not become dependent on mutable installation or repository state.

The decision requested is:

> Define the narrowest governed P9 identity amendment that makes the renderer identity recorded in the renderer profile and rendered activation verifiably correspond to the renderer behavior actually executing, fails closed when a previously recorded identity is reused with changed behavior, preserves the pure pack-plus-profile rendering boundary, and leaves every existing plane, framing, bounds, authority, and P10 boundary unchanged.

This proposal does **not** assume in advance that the answer must be a source-file digest, a package content identity, or a particular runtime mechanism.

## 2. Bound evidence and semantic basis

| Evidence | Immutable identity | Relevance |
|---|---|---|
| Governing implementation plan | commit `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`, blob `8474d2da42f863f0a190fd80292085176d3f97f0` | Requires renderer purity, deterministic replay identity, visible behavior/toolchain changes, structural plane preservation, separate bounds, and no P10 authorization |
| Closed P8 base | `05d9d7b0141cd7fa5e66dd72533b57e046001247` | Closed semantic base immediately beneath P9 |
| P9 candidate | `e961eb83d2c5dd1719b986c89a8915c102e395c3` | Exact blocked P9 deterministic-renderer candidate |
| P9 renderer implementation | blob `7d28edfa63302475343b2e8b10ef0309089429ff` | Current repository-owned behavior-bearing renderer artifact |
| Frozen renderer contract | blob `c8f18df390f92bfd25d6ac01c5932aeaf3ac396c` | `reasoning-distiller-context-renderer/1`; requires pure rendering and claims exact renderer implementation binding |
| Frozen renderer-profile schema | blob `768bcae7051e2805594df6d45402d331dc43bda4` | `/1` profile shape accepts caller-supplied Git-blob identity plus raw SHA-256 |
| Frozen rendered-activation schema | blob `f52c6007be3e7aa84c7e65f5e0708641e6920367` | `/1` activation repeats the same renderer-component identity shape |
| Frozen failure schema | blob `10195c52df81156a954eb9b5acee5a4f1b26f576` | Already provides `TOOLCHAIN_IDENTITY_MISMATCH` and `UNSUPPORTED_RENDERER` without requiring a new failure family |
| P9 independent review | `ff482ffcac5b58133ee3a480bab4164ee599732f` | Establishes blocker `P9_RENDERER_COMPONENT_IDENTITY_UNBOUND` and required stale-identity regression |
| P7 comparative remediation | `d4557ef183731304401444f42cf62819cae567af` | Demonstrates fail-closed behavior identity through exact source-byte verification, but uses filesystem access that P9 forbids and is therefore non-transferable as P9 architecture |
| Current package-build config | main blob `64fc29060c23d43d63aa7a43bff28184ef9878d9` | Existing release packages have a normative `content_identity`, but `context_packaging` is not a managed release root at the coordination revision |
| Current release-package builder | main blob `05546c4351c9cbf0a7c84321e6dde02fe746adfc` | Shows package content identity is computed over a closed file manifest, useful as an alternative model but not currently an execution proof for P9 renderer code |

The P9 review establishes no defect in plane classification, framing, deterministic escaping/decoding, limit behavior, or the no-discovery/no-side-effect path. This amendment should therefore change only the identity model required to prove which renderer behavior executed.

## 3. Required invariants

Any accepted amendment must preserve all of the following.

1. **Executing-behavior identity:** the renderer identity accepted from a profile must be independently derivable from, or cryptographically bound to, the renderer behavior that will actually execute.
2. **Stale-identity fail closed:** holding a previously accepted renderer identity constant while changing behavior-bearing renderer code must produce incompatibility or failure before a successful activation is returned.
3. **No caller self-attestation:** a syntactically valid identity value supplied only by the caller is not proof of the executing implementation.
4. **Renderer purity:** rendering remains a deterministic semantic transformation of the supplied canonical pack under the supplied renderer profile. Identity verification must not introduce source discovery, repository lookup, filesystem lookup, network access, model calls, semantic search, cache state, installation-state queries, or project-state mutation.
5. **No mutable-state dependence:** successful bytes and identity decisions cannot depend on mutable repository state, mutable install receipts, ambient process configuration, or caches.
6. **Same-object execution:** identity must cover the behavior object graph actually used for rendering/decoding. Verification of one object followed by execution through a replaceable different object is insufficient.
7. **Replay visibility:** a behavior-affecting implementation change must either change the bound renderer identity or fail under the old profile.
8. **Host/path independence:** checkout path, source filename, temporary directory, repository location, and filesystem enumeration cannot enter the renderer identity.
9. **Runtime honesty:** if the execution identity depends on a runtime ABI or interpreter semantics, that dependency must be explicit in the binding instead of silently treated as equivalent.
10. **Plane invariants unchanged:** control, knowledge, and operational-evidence classification and framing remain exactly structural and cannot be promoted by payload content.
11. **Bounds invariant unchanged:** `limits.max_activation_bytes` remains a post-identity serialized activation byte limit; overflow still fails with no truncation, ranking, summarization, omission, or partial activation.
12. **Pack semantics unchanged:** canonical pack contracts `/1` and `/2`, pack identity, source registry, provenance, and existing P0-P8 semantics are not revised by this amendment.
13. **Failure compatibility:** use an existing fail-closed failure family where sufficient; do not broaden the failure protocol merely to rename an identity mismatch.
14. **Version honesty:** the frozen `/1` renderer/profile/activation identity semantics must not be silently redefined under the same wire identities.
15. **No authority expansion:** renderer identity remains reproducibility evidence only. It grants no role authority, activation, canonical standing, reconciliation, admission, or trust promotion.
16. **No successor expansion:** P10 and production `rd-distill` integration remain outside this amendment.

## 4. Pressure cases

The amendment should be judged against at least these cases before implementation resumes.

| ID | Pressure case | Required outcome |
|---|---|---|
| RI-01 | Current renderer behavior and matching exact implementation binding | Render and decode succeed; activation records the independently derived binding |
| RI-02 | Old renderer profile is reused after a behavior-bearing render entrypoint change | Fail closed with toolchain/renderer incompatibility before a successful activation |
| RI-03 | Old profile is reused after a behavior-bearing helper change | Fail closed; helper behavior cannot hide behind an unchanged component label |
| RI-04 | Old profile is reused after a behavior-bearing constant changes, such as plane order, digest domain, accepted field set, or framing constant | Fail closed or derive a different binding |
| RI-05 | Only comments, source location, checkout path, or line-number/debug metadata change while executable behavior remains equivalent | Identity does not change merely because repository/path metadata changed |
| RI-06 | Equivalent implementation is loaded from a different filesystem path | Same execution binding and same activation bytes |
| RI-07 | Runtime/interpreter ABI changes in a way the binding contract cannot prove equivalent | Explicitly different/incompatible runtime binding, never silent equivalence |
| RI-08 | Caller supplies a syntactically valid but false implementation binding | Renderer independently derives a different binding and fails closed |
| RI-09 | Caller reuses a truthful old `/1` Git-blob component under the amended renderer | Explicit contract/profile incompatibility; no silent reinterpretation of `/1` fields |
| RI-10 | Repository/file APIs are unavailable or forced to fail | Rendering/decoding identity verification still succeeds for a matching in-memory implementation |
| RI-11 | Ambient installation manifest, cache, current branch, or repository HEAD changes | No effect on a matching render result or implementation binding |
| RI-12 | Identical pack/profile and identical execution binding are rendered repeatedly | Byte-identical activation |
| RI-13 | Instruction-like knowledge or operational-evidence payloads are combined with identity attacks | Plane classification remains unchanged while identity attack fails independently |
| RI-14 | Activation-size boundary is exercised with matching and mismatching implementation identity | Identity mismatch fails before success; matching identity preserves exact existing limit semantics |
| RI-15 | Identity is verified against one function graph, then an implementation path attempts to execute through a different replaceable graph | Contract/test must reject that architecture; verified graph and executed graph must be the same bound bundle |
| RI-16 | Binding derivation encounters an unenumerated mutable repository-local dependency | Fail closed rather than omit it from behavior identity |

## 5. Alternatives considered

### A. Keep `/1` fields and trust the caller-supplied Git blob/SHA-256

**Disposition: reject.** This is the current blocker. Syntax and profile-byte binding prove what the caller declared, not what executed.

### B. Make the renderer read its own source file and recompute Git-blob/SHA-256 identity

This is analogous to the successful P7 source-resolver remediation.

**Advantages**

- Directly binds the exact source artifact.
- Simple adversarial test.

**Problems**

- Violates the P9 frozen purity rule forbidding filesystem and repository lookup during rendering/decoding.
- Makes successful rendering depend on source-file availability and packaging layout.
- Introduces path/installation assumptions into a renderer that is intended to be provider-neutral and replayable.

**Disposition: reject for P9.** P7 is useful evidence for the security property, not a reusable mechanism.

### C. Embed the expected source digest as a literal constant in the renderer

**Advantages**

- No filesystem lookup.
- Very small code change.

**Problems**

- Does not close the stale-identity attack. Behavior can change while the literal identity remains unchanged.
- A build-time convention that developers "must update the constant" is process discipline, not an independently established execution binding.

**Disposition: reject.**

### D. Use the existing Reasoning Distiller release-package `content_identity`

The repository already has a deterministic package manifest/content identity model.

**Advantages**

- Content identity can cryptographically bind a closed set of package files.
- It is a good model for a future immutable execution package.

**Problems in the current P9 basis**

- At live coordination revision `80b6e89...`, `packaging/package-build.json` does not manage `context_packaging`, so the current package identity does not bind `context_packaging/renderer.py`.
- Even if the file were added to a package manifest, merely recording the package identity in the renderer profile would not prove that the currently executing Python objects were loaded from that exact immutable package.
- Consulting an installed manifest or scanning installed files at render time would reintroduce mutable-state/filesystem dependence.
- Expanding the release/install execution architecture is materially broader than the narrow P9 blocker.

**Disposition: reject as the immediate P9 mechanism.** A future verified immutable execution-package boundary could become a valid binding scheme if it can prove loaded execution bytes without render-time discovery.

### E. Define renderer identity only by normative algorithm contract plus output digest

**Advantages**

- Runtime-agnostic.
- No implementation introspection.

**Problems**

- A changed implementation may diverge on inputs not exercised by the current replay while retaining the same declared algorithm label.
- Output identity detects divergence after a particular render but does not establish which implementation behavior produced it.
- It weakens the governing R7 requirement that behavior/toolchain identity be visible.

**Disposition: reject as insufficient for the current replay-identity requirement.**

### F. Runtime-derived execution fingerprint over a closed renderer implementation bundle

The renderer derives a deterministic implementation binding from the in-memory code/data graph that it will actually execute. The profile must carry that exact derived binding. The activation records the derived binding, not an unchecked caller copy.

**Advantages**

- Changed behavior-bearing code or constants change the derived identity.
- Stale profiles fail without reading source files or repository state.
- The binding can exclude path/debug metadata and therefore remain location-independent.
- Runtime ABI dependence can be made explicit rather than hidden.
- The mechanism stays local to P9 and does not require a new installer/package architecture.

**Costs and risks**

- Requires a frozen, deterministic definition of the behavior graph and normalized code/data representation.
- Python runtime semantics must be handled explicitly; raw `marshal` or source-location-dependent code-object serialization is not sufficient.
- The implementation must avoid a verify-one-object/execute-another TOCTOU design.
- The self-measurement helper is itself trusted code. As with existing toolchain checks, this protects against stale/mismatched implementation under the accepted runtime, not an arbitrarily malicious runtime that rewrites its own verifier.

**Disposition: recommended.**

## 6. Proposed amended identity architecture

### 6.1 Version the amended family honestly

Do not edit the frozen `/1` wire meanings in place.

Introduce side-by-side amended identities, with final filenames subject to Stage 2/3 review:

```text
reasoning-distiller-context-renderer/2
reasoning-distiller-context-renderer-profile/2
reasoning-distiller-context-rendered-activation/2
```

The following semantics remain unchanged and can retain their existing contracts:

```text
reasoning-distiller-context-renderer-framing/1
reasoning-distiller-context-pack-failure/1
reasoning-distiller-context-pack/1
reasoning-distiller-context-pack/2
jcs/1
```

`/1` renderer/profile/activation artifacts remain immutable historical candidate evidence. A remediated P9 candidate must not accept `/1` renderer identity as if it carried the new execution-binding guarantee.

### 6.2 Replace self-declared source identity with an execution binding

The `/2` profile and activation should represent the renderer component conceptually as:

```json
{
  "role": "renderer",
  "contract": "reasoning-distiller-context-renderer/2",
  "implementation_binding": {
    "contract": "reasoning-distiller-renderer-execution-binding/1",
    "scheme": "python-code-graph/1",
    "runtime_abi": "<deterministic supported-runtime identifier>",
    "identity_sha256": "sha256:<64 lowercase hex>"
  }
}
```

The names above are proposal names, not pre-authorized frozen bytes. The semantic requirements are normative for this proposal:

1. `identity_sha256` is derived by the executing renderer from the exact bound behavior graph.
2. The renderer independently derives the binding before successful render/decode and requires exact equality with the profile binding.
3. The activation emits the independently derived binding.
4. A changed behavior graph under an old profile fails closed, preferably using existing `TOOLCHAIN_IDENTITY_MISMATCH` at the existing failure contract rather than creating a new failure family.
5. A profile cannot establish implementation identity by supplying the binding alone.

### 6.3 Define a closed implementation bundle

The renderer implementation should be refactored so the behavior used by render and decode is a closed bundle rather than an open set of replaceable module globals.

The bundle must include every repository-owned behavior-bearing element used by successful rendering/decoding, including at least:

- render and decode entry behavior;
- strict JSON parsing behavior owned by the renderer;
- JCS serialization behavior owned by the renderer;
- frame construction and frame decoding behavior;
- profile/component validation behavior;
- pack validation/summary behavior;
- digest-domain behavior;
- Base64 handling configuration used by the renderer;
- plane ordering and plane-key constants;
- accepted contract/field sets;
- limit enforcement behavior;
- activation identity behavior.

The implementation may use standardized runtime primitives such as SHA-256, UTF-8, RFC 4648 Base64, and the selected Python runtime's JSON/byte operations only if their dependency identity is covered by the frozen execution-binding contract and runtime ABI rule.

Repository-local mutable helper modules must not be consulted by the bound renderer behavior.

### 6.4 Freeze a normalized execution descriptor

`python-code-graph/1` should define a deterministic descriptor for the closed implementation bundle and hash canonical JCS bytes of that descriptor.

The descriptor should include behavior-affecting information and exclude ambient/debug-only information.

At minimum Stage 2 should require the frozen definition to address:

- stable ordered member names;
- callable code bytes or an equivalently deterministic executable representation;
- nested code objects;
- argument/closure structure needed to distinguish executable semantics;
- immutable defaults and closure data that affect behavior;
- explicit semantic constants used by the bundle;
- the selected runtime ABI identifier;
- standardized primitive dependencies used by the bundle;
- rejection of unsupported mutable repository-local dependencies.

It must exclude at least:

- absolute or relative source filename;
- checkout/repository path;
- first source line number;
- line tables/debug location metadata;
- comments/docstrings unless they are intentionally executable data;
- filesystem timestamps or permissions;
- repository branch/HEAD identity.

A raw `marshal.dumps(code)` is not automatically acceptable because it may encode source-location or runtime-version details that have not been reviewed as semantic identity.

### 6.5 Bind and execute the same graph

A successful call must not perform this unsafe sequence:

```text
fingerprint object graph A
then execute mutable/global object graph B
```

Instead, rendering/decoding must:

1. resolve the closed implementation bundle used for this call;
2. derive its exact execution binding;
3. compare that binding with the exact supplied profile binding;
4. execute through that same bundle;
5. emit that same derived binding in the activation.

The implementation must not cache a binding in a way that lets later behavior mutation execute under a stale cached value. If a cache is used only as a pure optimization, equivalence under mutation pressure must be proven; the simpler default is deterministic derivation from the bound bundle for each call or from an immutable bundle whose identity cannot diverge from the executed references.

### 6.6 Keep artifact provenance separate from execution proof

A Git blob, source SHA-256, source commit, or release-package content identity may still be useful provenance outside the renderer execution binding. It must not be represented as if it proves the executing behavior unless a separate verified execution environment contract actually establishes that relation.

For P9 `/2`, the normative replay identity is the execution binding. Stage 2 may recommend an additional non-authoritative artifact provenance record, but it must not be required for successful pure rendering unless it can be validated without violating the P9 boundary.

## 7. Amendment to the governing R7/P9 interpretation

The governing plan currently allows behavior identity through an immutable artifact digest or a normative package content identity that fixes the relevant behavior bytes. That wording is too narrow for a pure renderer that cannot read its source/package at invocation.

This proposal recommends that Stage 3 amend the renderer-specific interpretation of R7 to permit:

> **a frozen execution-binding contract whose identity is independently derived from the exact behavior graph executed by the renderer and whose collision-resistant digest changes when behavior-bearing code/data or required runtime semantics change.**

This is not permission for arbitrary self-declared version strings. The binding must be independently derived and pressure-tested against stale implementation identity.

For components where immutable artifact/package verification is available without violating their contract, artifact/package identity remains valid. This amendment need not weaken P7 or other existing toolchain checks.

## 8. Dependency and ownership boundaries

```text
canonical context pack
        +
exact renderer profile /2
        |
        v
closed renderer implementation bundle
        |
        +--> derive execution binding from same bundle
        |        |
        |        +--> compare to profile implementation_binding
        |        `--> mismatch => fail closed
        |
        v
existing structural render/decode semantics
        |
        +--> unchanged planes
        +--> unchanged framing
        +--> unchanged activation byte bound
        `--> activation records derived execution binding
```

Forbidden dependencies remain:

```text
renderer -X-> repository/file discovery
renderer -X-> current branch/HEAD
renderer -X-> install receipt or mutable package state
renderer -X-> network/model/search
renderer -X-> authority/activation/admission/reconciliation
renderer -X-> plane promotion
renderer -X-> truncation/ranking/summarization
P9       -X-> P10 production integration
```

## 9. Compatibility and migration

1. Existing immutable P9 candidate `e961eb83...` and its `/1` contract/schema blobs remain historical evidence and are not rewritten.
2. `/1` renderer profiles do not gain `/2` execution-binding semantics retroactively.
3. A remediated P9 implementation may explicitly reject `/1` profiles as unsupported for the accepted P9 gate.
4. No migration should transform a `/1` profile's caller-declared Git blob/SHA into a `/2` execution binding without deriving the new binding from an actual supported renderer implementation.
5. Pack contracts `/1` and `/2` remain supported according to the renderer profile as before; this amendment does not revise pack semantics.
6. Activation `/2` identity changes are expected because the renderer component representation is part of activation identity.
7. Current production `rd-distill` behavior remains untouched.

## 10. Implementation sequence and gates

Implementation is **not authorized by this Stage 1 artifact**. If Stage 3 later accepts the design, the ordered implementation should be:

1. **Freeze identity pressure cases.** Materialize RI-01 through at least RI-16, especially stale entrypoint/helper/constant identity, path independence, no filesystem access, runtime ABI mismatch, and same-bundle execution.
2. **Freeze execution-binding contract.** Define exact canonical descriptor, digest domain, runtime ABI identity, supported primitive dependencies, and mutable-dependency rejection rules.
3. **Freeze side-by-side `/2` renderer/profile/activation contracts.** Keep `/1` bytes unchanged.
4. **Refactor to a closed behavior bundle.** Preserve existing P9 structural behavior without semantic expansion.
5. **Implement independent binding derivation and comparison.** Use the existing fail-closed failure family where possible.
6. **Emit derived binding.** The activation must record the binding derived from the executed bundle, not an unchecked profile copy.
7. **Run all original P9 invariants.** PC-33, PC-44, PC-45, PC-46 intent, exact pack round trip, deterministic bytes, bounds, and no-discovery/purity remain green.
8. **Run unaffected P0-P8 regressions.** Preserve inherited red classifications separately exactly as the current evidence workflow does.
9. **Produce candidate-bound immutable evidence.** Bind the exact amended protocol/schema/renderer/test blobs and the exact candidate parent/tree.
10. **Fresh independent P9 review.** P9 remains open until independent evidence verifies the identity amendment and all existing P9 semantics.
11. **Steward P9 reconciliation only after independent PASS.** No P10 begins merely because P9 later closes.

## 11. Risks and unresolved questions for Stage 2

### 11.1 Exact normalized code representation

The largest technical risk is accidentally freezing path/debug noise or omitting behavior-affecting state. Stage 2 must challenge the exact descriptor. The final contract should prefer a small explicit normalized representation over a broad opaque serialization whose semantic fields are poorly understood.

### 11.2 Runtime ABI granularity

The proposal requires runtime semantics to be explicit but does not predetermine whether the stable identifier should bind implementation family, major/minor version, cache tag, or another reviewed ABI identity. Too coarse can hide behavior changes; too fine can create unnecessary identity churn. Stage 2 should pressure both failure and portability.

### 11.3 Standard-library primitive boundary

The renderer already depends on standardized runtime primitives. Stage 2 should decide which dependencies are adequately fixed by the runtime ABI plus protocol semantics and which, if any, must be represented separately in the execution descriptor.

### 11.4 Self-measurement trust root

No in-process mechanism can defend against an arbitrarily malicious runtime that rewrites both the renderer and its own verifier. This proposal's threat model is the same class as existing toolchain-identity checks: detect stale/mismatched behavior under the accepted execution runtime and adversarial inputs, not prove code integrity against a hostile interpreter. Stage 2 should reject the proposal if the governing plan requires a stronger external attestation root than that.

### 11.5 Package-content identity as a later optimization

A future immutable, verified execution-package contract could provide a cleaner external root and avoid implementation introspection. Stage 2 should keep that avenue open, but it should not expand current P9 into release/installer redesign unless it concludes that a runtime-derived binding is insufficient.

## 12. Acceptance criteria

An accepted final amendment should make all of the following objectively testable.

- A truthful `/2` profile for the current renderer succeeds.
- The activation records the renderer binding independently derived from the implementation that executed.
- Reusing that profile after changing any behavior-bearing renderer entrypoint, helper, or relevant constant fails closed or yields a different required binding.
- A syntactically valid false binding cannot be accepted merely because profile raw bytes match the profile object.
- No render/decode path reads renderer source bytes, repository metadata, package installation state, current branch/HEAD, or any mutable project state.
- The same implementation loaded at a different path derives the same binding.
- Runtime semantics that cannot be proven equivalent are visible in the binding or rejected.
- The verified behavior bundle is the one actually executed.
- Existing P9 plane, framing, round-trip, trust-channel, byte-limit, no-truncation, and no-side-effect invariants remain unchanged.
- Existing pack `/1` and `/2` semantics remain unchanged.
- Frozen `/1` renderer/profile/activation bytes remain immutable historical evidence and are not silently reinterpreted.
- Candidate-bound and fresh independent evidence includes an adversarial stale-identity regression.
- P9 implementation does not resume until Stage 2 independent review/synthesis and Stage 3 Steward reconciliation approve an amended basis.
- P10, production integration, admission, canonical mutation, authority mutation, and activation mutation remain out of scope.

## 13. Stage 1 recommendation

**Recommend an honestly versioned `/2` P9 renderer identity family whose normative replay identity is a runtime-derived execution fingerprint over the same closed renderer implementation bundle that performs rendering and decoding.**

Do not use render-time filesystem/source hashing. Do not treat an embedded source digest, a caller-supplied Git blob, or the current release-package content identity as sufficient execution proof. Preserve package-content identity as a possible future binding scheme only if a separately governed immutable execution environment can prove that the loaded behavior corresponds to that package without reintroducing mutable/discovery dependencies.

The amendment should leave P9 rendering semantics untouched except for the implementation-identity proof and the resulting honest wire-version change.

## 14. Exact next action and terminal boundary

This Stage 1 proposal is complete when durably committed unchanged as the Stage 1 artifact.

The next consequential action belongs to a **separate fresh independent Engineer activation** under `docs/governance/PROPOSAL_REVIEW_METHOD.md`, receiving:

1. the original P9 blocker and constraints;
2. exact P9 candidate `e961eb83d2c5dd1719b986c89a8915c102e395c3`;
3. independent review `ff482ffcac5b58133ee3a480bab4164ee599732f`;
4. governing plan `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd` / blob `8474d2da42f863f0a190fd80292085176d3f97f0`;
5. this complete Stage 1 proposal artifact.

That Engineer must independently challenge and synthesize the architecture, especially the self-measurement trust root, normalized code graph, runtime ABI boundary, versioning, and whether a stronger immutable package/execution boundary is required. It must not merely endorse or rewrite this proposal.

After Stage 2, a separately authorized Project Engineering Steward must reconcile Stage 1 and Stage 2 before any P9 implementation resumes.

No P9 implementation, P10, admission, canonical mutation, authority mutation, activation mutation, or Steward reconciliation begins from this Stage 1 activation.
