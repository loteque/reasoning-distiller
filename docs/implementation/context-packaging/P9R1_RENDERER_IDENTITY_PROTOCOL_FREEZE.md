# P9R1 Renderer Identity Protocol Freeze

Status: **P9R1 IDENTITY PROTOCOL FROZEN; RENDERER BEHAVIOR UNCHANGED**

Repository: `loteque/reasoning-distiller`

Remediation branch: `implement/context-packaging-p9-remediation`

Blocked P9 semantic base: `e961eb83d2c5dd1719b986c89a8915c102e395c3`

P9R0 pressure-freeze parent: `637da425560f1ab287eacfe90f1e9c167b607a18`

Coordination revision re-resolved immediately before this write: `80b6e89ad2efe84b088ca06b908a257c449fac15`

Governing plan: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd` / blob `8474d2da42f863f0a190fd80292085176d3f97f0`

Governing P9 renderer-identity amendment: `373667be85521e6f0f83bf19fed3378357e51118` / blob `90142ffe6b6652faceb3e8347f33fa71c8dc3ed9`

Disposition: `P9_RENDERER_IDENTITY_STAGE3_RECONCILED_ACCEPTED_WITH_GATES`

## Gate purpose

This commit freezes P9R1 only. It defines the execution-binding protocol later P9R2/P9R3 implementation must satisfy. It does not refactor or modify `context_packaging/renderer.py`. P9R0 RI-01 through RI-24 remain mandatory.

## Frozen contract family

The side-by-side family is:

```text
reasoning-distiller-context-renderer/2
reasoning-distiller-context-renderer-profile/2
reasoning-distiller-context-rendered-activation/2
reasoning-distiller-renderer-execution-binding/1
reasoning-distiller-python-closed-bundle/1
reasoning-distiller-python-closed-bundle-descriptor/1
```

Historical `/1` renderer/profile/activation, framing `/1`, failure `/1`, context-pack `/1` and `/2`, and `jcs/1` remain unchanged. `/2` profiles and activations use `renderer_execution_binding`; the historical caller-declared `/1` `renderer_component` is not reused as proof.

## Exact runtime ABI

`python-closed-bundle/1` initially supports exactly:

```json
{"implementation":"cpython","major":3,"minor":12,"micro":0,"cache_tag":"cpython-312"}
```

There is no patch-floating `3.12` equivalence. Later candidate-bound evidence must request and assert this exact tuple. Prior P9 evidence used patch-floating `3.12` and does not establish `/2` runtime evidence.

## Binding digest and comparison

The binding is SHA-256 over:

```text
ASCII("reasoning-distiller-renderer-execution-binding/1")
NUL
ASCII("python-closed-bundle/1")
NUL
JCS(reasoning-distiller-python-closed-bundle-descriptor/1)
```

The profile supplies the expected complete binding. Each render/decode call independently derives the actual binding from the one captured closed bundle and exact runtime ABI. Exact canonical equality is required before success. The activation records that independently derived actual binding, never an unchecked profile copy.

## Mechanically closed bundle

Frozen roots:

```text
member:render
member:decode
member:resolve_bundle
member:describe_bundle
member:derive_execution_binding
member:compare_execution_binding
```

Every repository-owned behavior-bearing callable and constant used by those roots must be explicitly registered. Every executable global reference must resolve to another registered member, an allowlisted runtime primitive, or frozen non-behavioral module metadata (`__name__`, `__package__`, `__loader__`, `__spec__`). Unregistered repository behavior, mutable repository-local module dependencies, dynamic import/helper discovery, eval/exec, and mutable list/dict/set defaults or persistent closure cells fail closed.

The member registry, resolver, descriptor builder, binding derivation, and binding comparison are themselves behavior-bearing members of the same bundle. Introspection checks closure; it does not grant an open-ended dependency set.

## Normalized callable descriptor

Descriptor construction uses CPython 3.12.0 `dis.get_instructions(code, show_caches=False, adaptive=False)` and `dis.Bytecode(code).exception_entries`.

It binds code name/qualname, calling convention, `co_nlocals`, `co_stacksize`, execution flags, local/global/free/cell names, normalized instructions, and normalized exception control flow. Instruction table indexes and source/debug byte offsets are not identity fields.

Operand normalization is frozen as follows:

- `dis.hasconst`: recursively normalized semantic constant, never the `co_consts` index;
- `dis.hasname`: semantic name plus exact-ABI `argrepr` only for name-op semantic modifiers;
- `dis.haslocal` / `dis.hasfree`: semantic names, never table indexes;
- comparisons: semantic comparison value;
- jumps: normalized target instruction ordinal;
- other argument-bearing opcodes: semantic integer oparg under the exact ABI;
- argument-free opcodes: JSON null.

Nested executable code constants recurse through the same descriptor. Only constants actually referenced by executable instructions, defaults, closures, or registered immutable members are included. This makes unreferenced docstring changes non-semantic while preserving behavior-bearing constants.

Excluded debug/location material includes `co_filename`, `co_firstlineno`, `co_linetable`, instruction position/source-line records, checkout/source path, repository identity, comments, and unreferenced docstrings. Raw `marshal`, raw `repr`, pickle, or other opaque code-object serialization is forbidden.

## Normalized persistent data

Representable behavior data is closed to `None`, booleans, canonical decimal integers, finite float64 by exact IEEE-754 bits, exact strings, exact bytes by padded RFC 4648 Base64, tuples, frozensets sorted by normalized JCS bytes, and nested code descriptors. Unsupported or mutable persistent values fail closed. Ephemeral local mutable objects created during a call are execution state, not persistent bundle dependencies, provided their constructors and operations remain inside the frozen code/runtime boundary.

## Runtime primitive boundary

The exact primitive allowlist is frozen in `protocols/rgp/python-closed-bundle-v1.json`. Repository code may not silently grow it. Python-defined standard-library primitives carry a normalized callable descriptor for the captured reference while their standard-library internals are accepted under the exact runtime ABI. Built-in callables/types are fixed by module/qualname/reference kind under that ABI. A substituted primitive must change the binding or fail resolution.

Runtime ABI information is obtained only from `sys.implementation.name`, `sys.version_info.major/minor/micro`, and `sys.implementation.cache_tag` under the accepted non-hostile runtime trust boundary.

## Same-bundle execution

Each future `/2` call must capture one bundle and all member/primitive references once, validate closure/runtime ABI on that instance, derive and compare the binding from that same instance, then execute only through those captured references. After resolution there is no module-global behavior lookup. The same derived binding is emitted in the activation. No binding cache is permitted.

## Failure and migration

Binding/runtime mismatch uses existing `TOOLCHAIN_IDENTITY_MISMATCH`. Unsupported `/2` profile, bundle, dependency, or interpreter shapes use `UNSUPPORTED_RENDERER`. Activation-size overflow remains `RENDER_LIMIT_EXCEEDED` with existing post-identity serialized-byte semantics.

A `/1` profile is not valid `/2` input. No historical Git blob or raw SHA-256 renderer component value can be copied or converted into `/2` execution proof. Migration requires resolving a real supported closed bundle and deriving a new execution binding. Pack semantics remain unchanged.

## Threat and discovery boundary

Successful binding validation uses no filesystem/source path, Git/repository state, installation manifest, current branch, network, model/search, cache, or mutable project state. This is deterministic execution binding under a non-hostile exact CPython runtime, not external attestation. Hostile interpreter or arbitrary hostile same-process guarantees require the separately governed immutable package/execution-boundary contingency.

## Historical `/1` byte freeze

P9R1 mechanically preserves:

```text
context_packaging/renderer.py                           7d28edfa63302475343b2e8b10ef0309089429ff
protocols/rgp/context-renderer-v1.json                 c8f18df390f92bfd25d6ac01c5932aeaf3ac396c
schemas/context-renderer-profile.schema.json           768bcae7051e2805594df6d45402d331dc43bda4
schemas/context-rendered-activation.schema.json        f52c6007be3e7aa84c7e65f5e0708641e6920367
```

The P9R1 mechanical test recomputes these Git-blob identities and also checks P9R0 remains RI-01 through RI-24.

## Exit and stop boundary

P9R1 is frozen when these protocol/schema artifacts, exact-byte attributes, note, and mechanical test are committed together over P9R0 with `context_packaging/renderer.py` unchanged.

The next gate is P9R2 Closed-bundle refactor. P9R2 is behavior-changing implementation and is not performed here. P9R3 binding implementation, P9R4 execution, candidate-bound evidence, independent review, Steward reconciliation, P10, production integration, admission, canonical mutation, authority mutation, and activation mutation remain outside this commit.
