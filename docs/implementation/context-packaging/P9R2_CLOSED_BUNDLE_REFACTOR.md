# P9R2 Closed-Bundle Refactor

Status: **P9R2 CLOSED-BUNDLE REFACTOR IMPLEMENTED; P9R3 NOT STARTED**

Repository: `loteque/reasoning-distiller`

Remediation branch: `implement/context-packaging-p9-remediation`

Exact P9R1 parent: `fa91287d0e69d5161c9d8b1acc5da02cc10f6c31`

Coordination revision verified for this work: `80b6e89ad2efe84b088ca06b908a257c449fac15`

Governing plan: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd` / blob `8474d2da42f863f0a190fd80292085176d3f97f0`

Governing P9 renderer-identity amendment: `373667be85521e6f0f83bf19fed3378357e51118` / blob `90142ffe6b6652faceb3e8347f33fa71c8dc3ed9`

Disposition: `P9_RENDERER_IDENTITY_STAGE3_RECONCILED_ACCEPTED_WITH_GATES`

## Gate purpose

This commit performs P9R2 only. It refactors the existing historical `/1` renderer implementation so every public render/decode call first resolves one fresh explicit execution bundle, then executes the existing renderer behavior only through references captured in that bundle. It does not derive, compare, accept, or emit the P9R1 execution binding, and it does not activate the `/2` wire family.

## Closed-bundle structure

`context_packaging/renderer.py` now resolves a fresh immutable tuple bundle on every render/decode call. There is no bundle cache.

The bundle captures, in a fixed mechanically named layout:

- every repository-owned callable used by the render/decode behavior graph;
- the result and internal failure types used by that graph plus their constructors;
- every behavior-bearing renderer constant used by the graph;
- every runtime primitive used by the graph from the frozen P9R1 primitive boundary; and
- the bundle accessor itself.

After resolution, the public entrypoints invoke the captured render/decode references by tuple position. Each repository-owned bound member obtains the captured bundle accessor by tuple position and resolves subsequent dependencies only from that already captured bundle. Registered execution members recursively contain no module-global load/store/delete instructions. Registered functions have no persistent closure cells and no mutable list/dict/set defaults.

Mutable repository behavior constants from the historical implementation were structurally frozen for the bundle: plane keys are tuples, and profile/pack field sets are frozensets. Ephemeral local lists/dicts/sets created during a call remain execution state, consistent with `python-closed-bundle/1`.

The bundle carrier is a built-in immutable tuple rather than a repository-owned mutable container or generated dataclass. This avoids introducing carrier behavior or persistent generated closure state into the future descriptor trust surface.

## Existing renderer semantics preserved

The historical public contracts remain active for this gate:

```text
reasoning-distiller-context-renderer/1
reasoning-distiller-context-renderer-profile/1
reasoning-distiller-context-rendered-activation/1
```

P9R2 does not reinterpret `/1` `renderer_component` as execution proof. Existing plane ordering, framing, strict JSON/JCS behavior, pack round-trip, activation-byte limit, purity, no-discovery behavior, and renderer failure codes/stage remain unchanged.

The historical P9R1 pre-refactor renderer blob remains durable evidence in the immutable P9R1 record:

```text
context_packaging/renderer.py  7d28edfa63302475343b2e8b10ef0309089429ff
P9R1 implementation note       b8962e5395c66e1e12d3629088bd60e4d0c9fd10
```

The P9R2 renderer blob produced by this refactor is:

```text
context_packaging/renderer.py  9da60cae90743568ff5ebb46675d9c59a5dd5efc
raw SHA-256                     0fff19853be3646fd7b865c96bc01fd2defe20450a73f2c00061dc82d4ebae17
```

The P9R1 mechanical test is made stage-aware: it now pins the unchanged P9R1 implementation-note blob and verifies that note records the exact historical renderer blob, while continuing to pin the unchanged historical `/1` protocol/schema blobs. It no longer incorrectly requires the live P9R2 renderer file to equal the P9R1 renderer blob.

## P9R2 regression coverage

`tests/test_context_packaging_renderer_closed_bundle_p9r2.py` adds checks that:

1. each bundle resolution returns a fresh immutable tuple with a sorted duplicate-free member registry;
2. registered post-resolution execution members have no module-global lookup, persistent closure, or mutable default dependency;
3. an already resolved bundle remains behaviorally stable after RI-18-style substitution of module-global helpers, runtime primitive aliases, result/failure type globals, and behavior constants;
4. each public render/decode call resolves exactly one fresh bundle and round-trips a representative valid pack; and
5. the historical `/1` wire family remains active while descriptor/binding functions are absent, explicitly stopping before P9R3.

Local implementation-harness verification before the repository write:

```text
pytest -q tests/test_context_packaging_renderer_closed_bundle_p9r2.py
5 passed
python -m py_compile renderer + P9R1/P9R2 tests
PASS
```

That harness ran under CPython `3.13.5`. It is structural/P9R2 implementation verification only. It is **not** candidate-bound evidence for the frozen `CPython 3.12.0 / cpython-312` execution-binding ABI and does not claim P9R3 or later gate evidence.

## Explicit stop boundary

P9R3 is not implemented here. There is no bundle descriptor construction, execution-binding derivation, binding comparison, `/2` profile acceptance, `/2` activation emission, runtime-ABI enforcement, binding cache, production integration, admission, canonical mutation, authority mutation, activation mutation, independent review, or Steward reconciliation in this gate.

The next consequential work, if selected after this P9R2 candidate is durably observed, is a separately bounded P9R3 implementation activation.
