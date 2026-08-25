# P9 Renderer Execution-Identity Amendment - Stage 3 Steward Final Plan

Status: **P9 RENDERER IDENTITY AMENDMENT APPROVED WITH REQUIRED GATES; P9 REMAINS OPEN**
Method: `proposal-review-synthesis/1`
Repository: `loteque/reasoning-distiller`
Coordination control ref: `main`
Coordination revision resolved before reconciliation and re-resolved immediately before this write: `80b6e89ad2efe84b088ca06b908a257c449fac15`
Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
Exact blocked P9 candidate: `e961eb83d2c5dd1719b986c89a8915c102e395c3`
Blocking P9 independent review: `ff482ffcac5b58133ee3a480bab4164ee599732f`
Stage 1 proposal commit: `1cbbb61925c95219b8050c33efd1bf7b68a5fed4`
Stage 1 proposal blob: `a16edba937d8d30dd62dfe1082d0124673eb23e4`
Stage 2 review/synthesis commit: `930020caaceab1a37fd55053fc12cbd06cec7491`
Stage 2 review/synthesis blob: `43e04193045ce2c81e03832580bfef3ac94b6a1a`
Stage 2 disposition: `P9_RENDERER_IDENTITY_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`
Stage: **Stage 3 Project Engineering Steward reconciliation**
Final disposition: **`P9_RENDERER_IDENTITY_STAGE3_RECONCILED_ACCEPTED_WITH_GATES`**

## Authority and activation record

Operational role for this Stage 3 reconciliation: `steward:default`.

Requested authority scope: `semantic_reconciliation`.

At exact coordination revision `80b6e89ad2efe84b088ca06b908a257c449fac15`, project-owned Steward authorization assigns `semantic_reconciliation` to `steward:default`. The package-provided default Steward is the available default role under the live RIL role contract.

This Stage 3 invocation uses the accepted v1 `explicit_declaration` activation method with:

```text
invocation_id: chat-20260824T2141-0700-p9-stage3
source: chatgpt-project
activation_digest: sha256:71ffde2e06c0a037944d26f8bc588a949260a3f4d4151d3e80072794f2730c25
validation: PASS/ACTIVATION_ACCEPTED
scope: semantic_reconciliation
role_id: steward:default
```

This activation is read-only invocation evidence. It creates no role registration, Steward authorization, admission, canonical mutation, authority mutation, or activation-state mutation.

This document is the Stage 3 artifact required by `docs/governance/PROPOSAL_REVIEW_METHOD.md`. It is a proposal-review reconciliation and amended implementation plan. It is not an R12 candidate-bound reconciliation disposition under `docs/operations/RIL_RECONCILIATION_CONTRACT.md`, and it does not close the exact blocked P9 candidate.

## 1. Decision

Adopt the Stage 1 renderer execution-identity direction **with all Stage 2 R1-R7 revisions incorporated as mandatory requirements**.

The approved narrow P9 remediation is an honestly versioned `/2` renderer identity family whose renderer implementation identity is established by a frozen runtime-derived execution binding over a mechanically closed renderer execution bundle. The expected binding is supplied by the `/2` profile, but successful rendering or decoding independently derives the actual binding from the exact bundle resolved for that call, compares exact canonical binding values before success, executes through that same bundle, and records the derived binding in the `/2` activation.

This approval is intentionally bounded. The runtime-derived mechanism proves stale or mismatched renderer behavior only under the accepted non-hostile execution-runtime threat model defined below. It is not external attestation and does not prove integrity against a hostile interpreter or arbitrary hostile same-process mutation.

P9 remains open. Exact candidate `e961eb83d2c5dd1719b986c89a8915c102e395c3` remains blocked by `P9_RENDERER_COMPONENT_IDENTITY_UNBOUND`. No P9 implementation has been performed by this Stage 3 reconciliation, and no P10, production integration, admission, canonical mutation, authority mutation, or activation mutation is authorized by the existence of this document.

## 2. Input recommendations and Steward disposition

| Input | Recommendation | Steward disposition |
|---|---|---|
| Stage 1 RPG Engineer proposal | Use an honestly versioned `/2` renderer/profile/activation family and runtime-derived identity over the same closed behavior bundle that performs render/decode; preserve renderer purity and all existing P9 structural semantics | **Accepted as architectural base, subject to Stage 2 revisions** |
| Stage 2 independent Engineer review/synthesis | `P9_RENDERER_IDENTITY_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`; retain the core direction but require R1-R7, a bounded threat model, mechanically closed bundle, frozen descriptor, conservative runtime ABI, structural same-bundle execution, explicit R7 amendment, `/1` rejection, and a conditional stronger execution-boundary fallback | **Accepted in full; all R1-R7 are mandatory** |
| Existing P9 candidate/review evidence | Structural renderer behavior is otherwise sound, but caller-declared renderer identity is not proven to identify executing behavior | **Blocker remains established until remediated exact candidate receives fresh independent PASS** |

No Stage 2 required amendment is rejected.

## 3. Explicit amendment to the governing R7 interpretation for P9

The governing plan currently requires replay identity to bind behavior-defining toolchain components directly by immutable artifact digest or through a qualifying package content identity that contractually fixes the relevant behavior bytes.

For **P9 renderer execution identity only**, this Stage 3 reconciliation accepts a third proof form:

> A frozen renderer execution-binding contract may establish P9 renderer replay identity when its collision-resistant identity is independently derived from the exact mechanically closed execution bundle used by the render/decode call, includes every behavior-bearing repository-owned code/data dependency plus required runtime semantics, is compared exactly against the profile before successful execution, and is emitted from that same derived binding in the activation.

This amendment has the following mandatory limits:

1. A caller-declared digest, Git blob, version string, package identity, or execution-binding value is never sufficient by declaration alone.
2. The execution-binding scheme must fail closed on unenumerated behavior-bearing dependencies, unsupported dependency shapes, runtime ABI mismatch, or any inability to establish the complete bound bundle.
3. The scheme must preserve the P9 no-discovery boundary. No source-file, repository, branch, package-installation, cache, network, or mutable project-state lookup may become part of successful render/decode identity verification.
4. The exact bundle measured for the call must be the bundle executed for the call under the accepted threat model.
5. A behavior-affecting change to a bound entrypoint, helper, constant, validation path, binding verifier, or required runtime semantics must change the required binding or cause fail-closed incompatibility under the old profile.
6. Artifact and package identities remain valid provenance and may remain valid execution proof forms only when a separately frozen mechanism establishes the relation between that immutable artifact/package and the exact behavior actually executed without violating P9 purity.
7. This renderer-specific amendment does not weaken P7 or silently generalize runtime self-measurement as a universal R7 proof form for other components.

The approved execution-binding contract name is:

```text
reasoning-distiller-renderer-execution-binding/1
```

The approved initial scheme name is:

```text
python-closed-bundle/1
```

Stage 1's proposed name `python-code-graph/1` is rejected because the normative object must be a mechanically closed execution bundle, not an open-ended reachability walk.

## 4. Accepted threat model

### 4.1 Threat model accepted for P9

The runtime-derived execution-binding mechanism is sufficient for the exact P9 blocker when all of the following are true:

- the interpreter/runtime used for the call is accepted by the frozen runtime-ABI contract and is not hostile or instrumented to falsify introspection;
- the renderer must detect stale or false profile bindings;
- repository-owned render/decode behavior, helpers, constants, verifier behavior, and dependency declarations may differ from the profile expectation and must be detected;
- runtime ABI changes not explicitly proven equivalent must be visible or rejected;
- dynamic or unenumerated repository-local behavior dependencies must fail closed;
- the process is not assumed to contain an adversary capable of arbitrarily rewriting both the verifier and the executing object graph during the same call.

Under this bounded model, the accepted runtime and process integrity for the duration of one call are part of the trust base.

### 4.2 Threats explicitly not proven by this mechanism

The runtime-derived scheme does **not** establish integrity against:

- a hostile or instrumented interpreter that can lie about code objects, runtime identity, or introspection results;
- arbitrary hostile same-process mutation that can rewrite the verifier and executing functions during a call;
- an attacker controlling both the binding derivation implementation and the runtime introspection surface;
- proof that the loaded objects came from a particular release package, unless a separate verified execution contract establishes that provenance-to-execution relation.

No document, field, test name, or future implementation may describe the accepted runtime-derived scheme as external attestation.

### 4.3 Mandatory escalation condition

If P9 is later required to defend against any excluded hostile-runtime or hostile-same-process threat above, or if implementation cannot mechanically close the execution bundle under the accepted model, the runtime-derived path is insufficient. P9 implementation must stop and a separate proposal/review/Steward-reconciliation cycle must define a verified immutable package/execution boundary before P9 can resume.

## 5. Stage 2 R1-R7 reconciliation

| Revision | Steward disposition | Normative resolution |
|---|---|---|
| **R1 Threat model** | **Accepted, governance freeze** | Use the bounded non-hostile-runtime model in Section 4. Runtime self-measurement is deterministic execution binding under an accepted runtime, not external attestation. Stronger hostile-runtime claims require the package/execution-boundary contingency. |
| **R2 Mechanically closed execution bundle** | **Accepted, protocol-freeze blocker** | `python-closed-bundle/1` must enumerate every repository-owned callable and behavior-bearing constant used by render/decode, enumerate the allowlisted runtime primitives, include binding derivation/comparison in the trust surface, and reject dynamic imports/discovery, mutable repository-local dependencies, unenumerated globals, unsupported dependency shapes, and mutable defaults/closure state unless deterministically bound and non-divergent. |
| **R3 Normalized callable/data descriptor** | **Accepted, protocol-freeze blocker** | Before renderer behavior implementation changes, freeze a versioned deterministic descriptor covering executable instruction representation, nested code, calling convention, execution-affecting flags, referenced globals/names, free/cell variables, defaults, behavior-bearing immutable closure data, behavior-bearing constants, control-flow/exception metadata where relevant, deterministic ordering, and a named digest domain. Filename, checkout path, first source line, line/debug tables, repository identity, and other debug-only location metadata are excluded. Docstrings or other constants may be excluded only by a frozen rule proving they cannot affect accepted renderer behavior. Raw `marshal`, raw `repr`, or broad opaque code-object serialization is not an approved descriptor. |
| **R4 Structural same-bundle execution** | **Accepted, implementation blocker** | Each call resolves one explicit bundle instance, derives the binding from it, compares the exact expected binding, executes only through references captured by that same bundle, and emits the same derived binding. After bundle resolution, module-global behavior lookup is forbidden except for explicitly allowlisted runtime primitives covered by the runtime contract. No stale binding cache is permitted in the initial implementation. |
| **R5 Conservative runtime ABI** | **Accepted, protocol-freeze blocker** | Initial support must be exact and fail closed. For CPython, the frozen ABI identity must include implementation name; major, minor, and micro version; implementation cache tag or an equivalent reviewed bytecode/runtime compatibility identifier; and execution-binding scheme version. If the descriptor depends on additional interpreter bytecode compatibility data, the freeze must include an equivalent exact identifier. Patch-floating `3.12` alone is insufficient. The selected CI/runtime must be pinned to an exact accepted tuple before candidate evidence is valid. |
| **R6 R7 governance amendment** | **Accepted, project-scoped amendment** | Section 3 is the governing P9-specific R7 amendment. An implementation Engineer may rely on this exact amendment but may not generalize it to other toolchain components or invent another proof form without new authority. |
| **R7 `/2` migration and `/1` rejection** | **Accepted, wire-contract blocker** | `/1` renderer/profile/activation bytes remain immutable historical evidence. The `/2` renderer must not accept a `/1` profile as execution-bound input. No migration may turn a `/1` caller-declared Git blob/SHA pair into `/2` execution proof without deriving a valid `/2` binding from a supported execution bundle. |

## 6. Wire versioning and contract decisions

The following contract identities are approved for the amended P9 family:

```text
reasoning-distiller-context-renderer/2
reasoning-distiller-context-renderer-profile/2
reasoning-distiller-context-rendered-activation/2
reasoning-distiller-renderer-execution-binding/1
```

The initial execution-binding scheme is:

```text
python-closed-bundle/1
```

The following remain unchanged by this amendment:

```text
reasoning-distiller-context-renderer-framing/1
reasoning-distiller-context-pack-failure/1
reasoning-distiller-context-pack/1
reasoning-distiller-context-pack/2
jcs/1
```

Normative migration rules:

1. `/1` renderer/profile/activation artifacts remain unchanged and retain their historical semantics.
2. `/2` does not reinterpret `/1` component fields.
3. A `/2` profile carries an expected execution binding. The renderer independently derives the actual binding and compares exact canonical values.
4. A `/2` activation records the derived execution binding, never an unchecked copy of the profile field.
5. A `/1` profile is unsupported as a `/2` execution-bound profile.
6. Migration from `/1` to `/2` requires deriving a new binding from an actual supported execution bundle.
7. Existing pack `/1` and `/2` semantics are unchanged.
8. Activation identity changes caused by the new renderer-component representation are expected and correct.
9. Existing failure family `TOOLCHAIN_IDENTITY_MISMATCH` or the existing renderer-incompatibility path should be used for binding mismatch unless implementation demonstrates a real semantic gap requiring separate governance.

## 7. Approved execution architecture

```text
canonical context pack
        +
exact renderer profile /2
        |
        v
resolve one closed execution bundle
        |
        +--> validate supported dependency shapes
        +--> identify exact accepted runtime ABI
        +--> normalize exact bundle descriptor
        +--> derive execution binding
        |
        +--> exact binding mismatch => fail closed
        |
        v
execute render/decode through that same captured bundle
        |
        v
activation records the exact derived execution binding
```

The closed bundle must include the behavior necessary for:

- render entry behavior;
- decode entry behavior;
- renderer/profile/component validation;
- pack validation and pack-summary behavior;
- strict JSON behavior owned by the renderer;
- JCS behavior owned by the renderer;
- frame construction and decoding;
- Base64 configuration and use boundary;
- digest-domain behavior;
- plane ordering and all behavior-bearing constants;
- accepted contracts/field sets;
- limit enforcement;
- activation identity;
- execution-binding descriptor construction;
- execution-binding derivation and comparison.

A small frozen runtime-primitive allowlist may cover standardized primitives such as SHA-256 and RFC 4648 Base64. Broader helpers such as JSON parsing or float rendering must either be package-owned deterministic behavior or explicitly covered by the exact accepted runtime ABI and primitive boundary.

## 8. Approved invariants

The remediated P9 must preserve all previously approved P9 invariants and add the following identity invariants.

1. **Executing-behavior identity:** accepted renderer identity is independently derived from or cryptographically bound to the behavior actually executed.
2. **Stale-identity fail closed:** an old profile cannot successfully execute changed behavior under the old binding.
3. **No caller self-attestation:** profile syntax or exact profile bytes do not prove implementation identity.
4. **Closed-bundle completeness:** every repository-owned behavior-bearing dependency is explicitly represented or the bundle fails closed.
5. **Same-bundle execution:** the measured bundle is the executed bundle for the call under the accepted threat model.
6. **Verifier inclusion:** binding derivation/comparison behavior belongs to the reviewed trust surface and cannot hide behind an unchanged identity.
7. **Runtime honesty:** runtime equivalence that is not explicitly frozen is rejected rather than assumed.
8. **Path independence:** filename, checkout path, repository location, temporary paths, and debug line metadata do not enter the execution identity.
9. **No discovery:** renderer identity verification uses no filesystem, repository, installation-state, current-branch, network, model, search, cache, or mutable project-state discovery.
10. **No stale cache:** initial P9 binding derivation has no cache capable of diverging from executable references.
11. **Plane preservation:** control, knowledge, and operational-evidence classification/framing remain structural and unchanged.
12. **Bounds preservation:** `limits.max_activation_bytes` retains the existing post-identity serialized-activation semantics and fails without truncation, ranking, summarization, omission, or partial activation.
13. **Pack preservation:** context-pack `/1` and `/2`, source registry, provenance, and P0-P8 semantics are unchanged.
14. **Failure compatibility:** use existing mismatch/incompatibility semantics where sufficient.
15. **Version honesty:** frozen `/1` wire semantics are never silently redefined.
16. **Authority isolation:** execution identity grants no role authority, activation, canonical standing, reconciliation, admission, or trust promotion.
17. **Production isolation:** P10 and native production `rd-distill` integration remain outside this amendment.
18. **Stronger-threat fail boundary:** hostile-runtime or hostile-same-process integrity requirements trigger the separately governed immutable execution-boundary path rather than being implied by this scheme.

## 9. Package/execution-boundary contingency

### 9.1 Current package mechanism is not accepted as the immediate P9 solution

At coordination revision `80b6e89ad2efe84b088ca06b908a257c449fac15`, the release package managed roots do not include `context_packaging`. Even if they did, the existing package `content_identity` establishes a deterministic package file set. It does not by itself prove that a specific render call executed objects loaded from those exact files.

Therefore the current package identity must not be copied into a renderer profile and described as an execution proof.

### 9.2 When the contingency becomes mandatory

A separately verified immutable package/execution boundary becomes mandatory if any of the following occurs:

- the project requires integrity against a runtime that can falsify introspection;
- the project requires integrity against arbitrary hostile same-process mutation during the call;
- package provenance itself must be the execution trust root;
- the closed-bundle contract cannot completely enumerate behavior-bearing dependencies;
- a stable normalized descriptor cannot be frozen without either omitting behavior or depending on forbidden mutable/discovery state;
- the implementation requires a binding cache or loader relation that cannot prove non-divergence from the executed references.

The required stronger architecture must establish a relation equivalent to:

```text
verified immutable package identity
            |
            v
verified loader / execution environment
            |
            v
exact loaded renderer behavior
            |
            v
render/decode call
```

Crossing into that architecture is a new governance boundary. It is not authorized as an implementation detail by this Stage 3 plan.

## 10. Pressure-case gate

Stage 1 RI-01 through RI-16 and Stage 2 RI-17 through RI-24 are all accepted as mandatory P9 remediation pressure cases.

The required set therefore includes:

- truthful current binding succeeds;
- stale entrypoint identity fails;
- stale helper identity fails;
- stale behavior-bearing constant identity fails;
- path/debug-only noise does not alter binding;
- equivalent different source path is stable;
- unproven runtime ABI equivalence fails;
- false caller binding fails;
- `/1` profile reuse is rejected;
- repository/file APIs can fail without affecting truthful `/2` rendering;
- ambient install/cache/HEAD changes have no effect;
- identical contracted inputs/binding remain byte-identical;
- plane attacks remain plane-isolated while identity attacks fail independently;
- byte-limit semantics remain unchanged;
- verify-one/execute-another architecture is rejected;
- unenumerated mutable repository-local dependencies fail closed;
- verifier behavior change invalidates old binding;
- post-resolution module-global substitution cannot silently change executed behavior under the old binding;
- mutable closure/default dependency shapes fail closed unless frozen and non-divergent;
- runtime micro-version mismatch fails without explicit equivalence;
- runtime primitive substitution is detected or represented by a changed binding;
- unsupported interpreter family fails closed;
- descriptor noise stability excludes path/line/debug-only changes;
- no discovery remains true during identity validation.

No pressure case may be weakened to accommodate an implementation shortcut.

## 11. Ordered implementation plan and gates

The exact P9 remediation bounded work unit is authorized only in the following order.

| Gate | Required work | Exit criterion |
|---|---|---|
| **P9R0 Pressure freeze** | Materialize RI-01 through RI-24 with stable expected PASS/FAIL outcomes and failure classes | All pressure cases exist before behavior implementation changes; stale identity, same-bundle, runtime ABI, verifier, dependency-closure, `/1` rejection, and no-discovery attacks are executable or mechanically checkable |
| **P9R1 Identity protocol freeze** | Freeze `reasoning-distiller-renderer-execution-binding/1`, `python-closed-bundle/1`, the closed-bundle member/dependency rules, normalized descriptor fields/exclusions/order/digest domain, exact runtime ABI identity, primitive allowlist, and side-by-side renderer/profile/activation `/2` schemas/contracts | No descriptor or dependency inclusion rule remains implicit; unsupported shapes fail closed; exact accepted runtime tuples are pinned; `/1` migration/rejection is normative |
| **P9R2 Closed-bundle refactor** | Refactor the existing renderer so render/decode behavior executes through one explicit resolved bundle and no unbound repository-local mutable behavior lookup remains | Existing structural behavior is unchanged; all behavior-bearing repository-owned dependencies are in the frozen bundle; no module-global behavior lookup remains after resolution except allowlisted runtime primitives |
| **P9R3 Binding implementation** | Derive the exact binding from the resolved bundle, compare profile expectation before success, execute through that bundle, and emit the same derived binding | False/stale bindings fail; activation records derived binding; no stale cache exists; runtime mismatch fails closed |
| **P9R4 Full adversarial and regression execution** | Run RI-01 through RI-24, original P9 structural/framing/round-trip/purity/bounds gates, PC-33/44/45/46 intent, and unaffected P0-P8 regressions | All new identity cases pass; original P9 semantics remain green; inherited unrelated reds are preserved and classified separately rather than hidden |
| **P9R5 Candidate-bound evidence** | Produce immutable evidence binding exact parent, candidate tree, renderer, `/2` contracts/schemas, binding contract/scheme artifacts, tests, runtime tuple, and execution results | Evidence is exact-candidate-bound, reproducible, and sufficient for an independent reviewer to reconstruct all P9 gates |
| **P9R6 Fresh independent P9 review** | A fresh independent Engineer activation challenges the exact remediated candidate and bound evidence | `P9_INDEPENDENT_REVIEW_PASS` or equivalent exact PASS is required; any blocker returns to implementation without Steward closure |
| **P9R7 P9 Steward reconciliation** | A fresh activated Steward reconciles only the exact remediated P9 candidate against its independent PASS evidence | P9 may be closed only here; this amendment Stage 3 artifact is not a substitute for candidate reconciliation |

Implementation must preserve commit/history evidence showing that P9R0 and P9R1 were frozen before renderer behavior implementation in P9R2/P9R3. If a required protocol fact discovered during implementation invalidates the frozen architecture rather than merely filling in an implementation detail, stop and return to governance rather than silently changing the Stage 3 basis.

## 12. Definition of done for the amended P9 remediation

A remediated P9 is not complete until durable evidence establishes all of the following:

- exact `/2` renderer/profile/activation contracts and `reasoning-distiller-renderer-execution-binding/1` are frozen;
- `python-closed-bundle/1` is mechanically closed and has no unenumerated behavior-bearing repository-local dependencies;
- the normalized descriptor has explicit inclusion/exclusion rules, deterministic ordering, named digest domain, and no path/debug identity noise;
- the exact supported runtime ABI tuple is pinned, including implementation, major/minor/micro, cache tag or reviewed equivalent, and scheme version;
- the selected primitive boundary is explicit and no hidden standard-library dependency escapes the ABI/primitive contract;
- the renderer resolves one bundle, derives its binding, compares it, executes through it, and emits the same binding;
- changed entrypoint, helper, behavior constant, verifier, runtime ABI, or represented primitive invalidates the old profile binding or fails closed;
- false caller bindings fail;
- `/1` profiles are not treated as `/2` proof and cannot be auto-upgraded;
- render/decode identity verification performs no source/repository/filesystem/install/network/model/search/cache/project-state discovery;
- path, checkout, line/debug metadata, and non-executable noise do not change the binding under the frozen descriptor rules;
- original plane, framing, pack round-trip, trust-channel, activation-byte-bound, no-truncation, and no-side-effect semantics remain unchanged;
- exact candidate-bound evidence passes RI-01 through RI-24 plus the original P9 and unaffected P0-P8 gates;
- fresh independent review passes the exact remediated candidate;
- a later fresh Steward performs candidate-bound P9 reconciliation;
- P10 remains unauthorized until P9 is actually closed and a separately selected P10 proposal/review/reconciliation workflow authorizes production integration.

## 13. Remaining uncertainty and blocked decisions

The architecture and authority decisions are resolved by this Stage 3 plan. The following technical parameters remain intentionally gate-owned rather than silently invented here:

1. **Exact normalized descriptor byte/schema representation.** P9R1 must freeze it under the mandatory semantic inclusions/exclusions above. If no complete deterministic representation can be proven, implementation stops and the package/execution-boundary contingency is triggered.
2. **Exact initial CPython micro/cache-tag tuple.** Existing P9 evidence uses patch-floating Python `3.12`, which is insufficient for the new binding. P9R1 must select and pin the exact supported tuple actually used by the evidence workflow.
3. **Exact runtime primitive allowlist.** It must be minimized and frozen. Any primitive whose semantics are not adequately covered by the runtime ABI or a stable semantic contract must be package-owned or separately represented.
4. **Whether a future external immutable execution package is desirable.** It is not required for the currently accepted threat model and is not authorized by this plan. It becomes mandatory only under Section 9.2 conditions.

These are not permissions to improvise past a failed gate. Unknown or incomplete identity state fails closed.

## 14. Exact next authorized action

The next authorized action is:

> **Fresh Reasoning Graph Protocol / implementation Engineer: create a P9 remediation branch from exact blocked candidate `e961eb83d2c5dd1719b986c89a8915c102e395c3`, bind this Stage 3 final plan as the governing renderer-identity amendment, and begin P9R0 only by materializing RI-01 through RI-24 with stable expected outcomes. Then freeze P9R1 exactly as specified before modifying renderer behavior. Do not begin renderer refactoring or execution-binding implementation until P9R0 and P9R1 are complete. Remain inside the P9 remediation bounded work unit and do not begin P10, production integration, admission, canonical mutation, authority mutation, or activation mutation.**

The implementation branch should not use this proposal-history branch as the semantic code base merely because it contains the governance artifacts. The exact blocked P9 candidate remains the code base; this Stage 3 artifact is a separate governing input.

## 15. Final Steward disposition and terminal boundary

**`P9_RENDERER_IDENTITY_STAGE3_RECONCILED_ACCEPTED_WITH_GATES`**

The Stage 1 core direction is accepted. Stage 2's `P9_RENDERER_IDENTITY_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS` is reconciled by accepting every R1-R7 revision as mandatory.

The decisive Steward decisions are:

- accept the bounded non-hostile-runtime threat model for the exact P9 stale/mismatch blocker;
- accept a frozen runtime-derived execution binding as a renderer-specific R7 proof form;
- replace open-ended code-graph identity with mechanically closed `python-closed-bundle/1`;
- require normalized descriptor, exact runtime ABI, primitive boundary, and same-bundle execution to freeze before renderer behavior implementation;
- require honest side-by-side `/2` renderer/profile/activation contracts and normative `/1` rejection;
- reject the current package `content_identity` as a sufficient immediate execution proof;
- require a separately governed immutable package/execution boundary if stronger hostile-runtime guarantees are required or the closed-bundle scheme cannot satisfy its gates;
- preserve all existing P9 plane, framing, bounds, pack, authority, and production boundaries;
- require a new exact remediation candidate, fresh independent PASS, and later candidate-bound Steward reconciliation before P9 can close.

This Stage 3 proposal-review work unit is complete when this final plan is durably committed unchanged. The next consequential work belongs to the fresh implementation Engineer action in Section 14. No P9 implementation, P10, admission, canonical mutation, authority mutation, or activation mutation is performed by this Stage 3 reconciliation itself.
