# P9R3 Renderer Execution-Binding Implementation

Status: **P9R3 EXECUTION-BINDING IMPLEMENTED; P9R4 NOT STARTED**

Repository: `loteque/reasoning-distiller`

Remediation branch: `implement/context-packaging-p9-remediation`

Exact P9R2 parent: `ebb436a14dee2a67d778e3252892f7be5cd0e2ca`

Coordination revision verified for this work: `80b6e89ad2efe84b088ca06b908a257c449fac15`

Governing plan: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd` / blob `8474d2da42f863f0a190fd80292085176d3f97f0`

Governing P9 renderer-identity amendment: `373667be85521e6f0f83bf19fed3378357e51118` / blob `90142ffe6b6652faceb3e8347f33fa71c8dc3ed9`

Frozen P9R1 execution-identity protocol parent: `fa91287d0e69d5161c9d8b1acc5da02cc10f6c31`

Disposition basis: `P9_RENDERER_IDENTITY_STAGE3_RECONCILED_ACCEPTED_WITH_GATES`

## Gate purpose

This commit implements P9R3 only. It extends the exact P9R2 closed execution bundle with the frozen P9R1 descriptor, execution-binding derivation, and comparison behavior. It adds the honestly versioned `/2` render/decode path while preserving the historical `/1` callable path and protocol/schema bytes. It does not begin P9R4 adversarial/full-regression execution or any later P9/P10/reconciliation/admission/production work.

## P9R3 execution binding

The implementation adds the frozen roots:

```text
member:render
member:decode
member:resolve_bundle
member:describe_bundle
member:derive_execution_binding
member:compare_execution_binding
```

For the `/2` path each call:

1. resolves one fresh immutable tuple bundle;
2. validates the exact runtime ABI against CPython `3.12.0` / `cpython-312`;
3. constructs `reasoning-distiller-python-closed-bundle-descriptor/1` from only captured bundle/runtime state;
4. derives `reasoning-distiller-renderer-execution-binding/1` using the frozen domain and JCS descriptor bytes;
5. compares the complete expected `/2` profile binding before successful render/decode behavior;
6. executes through only references captured in that same bundle; and
7. records the same independently derived actual binding in the `/2` activation.

There is no binding cache.

Historical public `/1` rendering/decoding remains available through the pre-existing entrypoints. P9R3 adds explicit `/2` entrypoints so a `/1` profile is never silently reinterpreted as execution-bound `/2` proof.

## Closed descriptor implementation

The bundle descriptor implements the P9R1 frozen representation for:

- repository Python functions and their normalized code/default/keyword-default/closure/dependency descriptors;
- repository types plus separately registered behavior methods and class constants;
- immutable behavior constants;
- the actually captured subset of the frozen runtime primitive allowlist;
- normalized instructions and exception-table control flow;
- normalized immutable persistent values; and
- exact runtime ABI identity.

Bootstrap global dependencies are frozen as an immutable same-bundle declaration. Descriptor construction validates executable global names against that declaration and resolves each declared target through the already captured bundle rather than reading live module-global target objects after resolution.

This preserves the P9R2 same-bundle boundary during measurement as well as execution.

## `copy.deepcopy` primitive closure

The frozen P9R1 primitive allowlist includes `primitive:copy.deepcopy`, but the exact CPython 3.12.0 callable has the historical mutable default `_nil=[]`. That value is not representable by the frozen P9R1 persistent-value grammar and therefore cannot be admitted into the closed descriptor merely because the primitive is allowlisted.

P9R3 does not broaden or rewrite the frozen primitive contract. The renderer's JSON-value copying use is instead performed by registered same-bundle `member:jcs_clone`, implemented as strict-JSON decode of the renderer's captured JCS bytes. Consequently `copy.deepcopy` is not an actually captured execution dependency and does not enter the descriptor.

## Failure behavior

P9R3 preserves the frozen failure split:

- false/stale complete binding: `TOOLCHAIN_IDENTITY_MISMATCH`;
- CPython micro/cache-tag mismatch: `TOOLCHAIN_IDENTITY_MISMATCH`;
- substituted captured runtime primitive identity/reference kind: `TOOLCHAIN_IDENTITY_MISMATCH`;
- unsupported interpreter family: `UNSUPPORTED_RENDERER`;
- unsupported bundle/dependency/persistent-value shape: `UNSUPPORTED_RENDERER`;
- activation byte overflow: unchanged `RENDER_LIMIT_EXCEEDED` semantics.

A `/1` profile presented to the explicit `/2` path fails as `UNSUPPORTED_RENDERER` and is not upgraded or translated.

## Local P9R3 implementation harness

The implementation harness was run under CPython `3.13.5` and is structural only. The combined P9R2/P9R3 local harness reported:

```text
12 passed
```

The checks cover:

- P9R2 historical `/1` bundle behavior after the P9R3 extension;
- sorted/duplicate-free explicit member and primitive registries;
- all six frozen P9R1 roots;
- no primitive allowlist broadening and no captured `copy.deepcopy` dependency;
- deterministic normalized descriptor/binding construction under an explicitly synthetic exact-runtime tuple;
- `/1` rejection on the `/2` path;
- runtime micro and interpreter-family fail-closed behavior;
- truthful structural `/2` round-trip and derived-binding activation emission;
- false binding rejection;
- same-resolved-bundle stability after module-global substitutions;
- runtime primitive substitution failure; and
- fresh-resolution binding re-derivation with no stale cache.

A separate mechanical descriptor-shape harness also traversed the generated descriptor recursively against the frozen P9R1 field/value constraints and passed.

The synthetic runtime tuple used by structural tests is deliberately test-only. It does not convert the CPython 3.13.5 host into CPython 3.12.0 and is not execution evidence for the frozen runtime ABI.

## Evidence boundary

Exact CPython `3.12.0` / `cpython-312` candidate-bound execution evidence is **NOT_ESTABLISHED** by this gate. The available host is CPython `3.13.5`; the live implementation correctly fails exact `/2` derivation on that host with `TOOLCHAIN_IDENTITY_MISMATCH` unless a test explicitly substitutes the runtime tuple for structural harness purposes.

P9R4 full adversarial/regression execution and P9R5 candidate-bound evidence remain separate later gates. This commit must not be described as completing either gate.

## Explicit stop boundary

P9R3 is complete only when this implementation, its P9R3-local regression test, and the stage-aware P9R2 regression adjustment are committed together directly over exact P9R2 head `ebb436a14dee2a67d778e3252892f7be5cd0e2ca` and the resulting durable commit is observed.

After that observation, stop. Do not begin P9R4, P9R5, P9R6 independent review, P9R7 Steward reconciliation, P10, production integration, admission, canonical mutation, authority mutation, or activation mutation in this bounded work unit.
