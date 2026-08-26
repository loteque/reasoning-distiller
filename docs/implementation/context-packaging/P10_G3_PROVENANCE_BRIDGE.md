# P10-G3 Provenance Bridge implementation candidate

## Bound basis

- Repository: `loteque/reasoning-distiller`
- Coordination control: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`
- Governing plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- Closed G2 base: `95eac1148744d90b9074cbdfce82edfe4751f87a`
- Scope: P10-G3 Provenance Bridge only

This candidate does not implement G4 prepare integration, provider transport,
finalization, Steward reconciliation, admission, canonical mutation, or authority
mutation.

## Implemented bridge

`context_packaging/provenance_bridge.py` derives the frozen
`reasoning-distiller-context-provenance-registry/1` sidecar from one exact
`reasoning-distiller-context-pack/2` plus its exact
`reasoning-distiller-context-rendered-activation/2`.

Stable source identity follows the G1-frozen rule exactly:

```text
binding_bytes = JCS(full reasoning-distiller-context-source-binding/1 object)

binding_sha256 = sha256(
    "reasoning-distiller-context-provenance-binding/1\0"
    || binding_bytes
)

source_id = "src:ctx:" + lowercase_hex(binding_sha256)
```

Stable source records contain only source semantics that remain stable across
packs:

- `source_id`;
- `binding_sha256`;
- exact `source_class`;
- exact underlying `payload_sha256` represented by the binding;
- the complete canonical source binding.

For repository-control, package-control, and operational-evidence bindings,
`payload_sha256` is the binding's exact `raw_sha256`. For canonical-state
bindings it is the exact `pems_sha256`.

Pack-local occurrence records are separate and contain:

- exact pack identity;
- rendered `frame_index`;
- exact plane;
- exact `item_index`;
- stable `source_id`.

Pack identity, plane, item index, and frame index are never inputs to the stable
source ID.

## Closure and fail-closed behavior

Before a registry is returned, the bridge verifies that:

- every model-visible plane frame is present in exact renderer order;
- every frame's bytes exactly equal the JCS bytes of its sealed pack item;
- every plane-item source reference resolves to exactly one complete pack source
  binding;
- every pack source binding is represented by at least one model-visible frame;
- stable records are deterministic and source-ID keyed;
- a forced same-ID/different-record condition fails with
  `PROVENANCE_SOURCE_COLLISION`;
- unresolved, ambiguous, reordered, missing, or payload-divergent frame mappings
  fail with `PROVENANCE_BRIDGE_INVALID` at the activation boundary.

Registry identity follows the G1-frozen domain rule:

```text
registry_sha256 = sha256(
    "reasoning-distiller-context-provenance-registry/1\0"
    || JCS(registry_without_identity)
)
```

## Immutable persistence

`persist_provenance_registry(...)` validates exact canonical registry bytes and
registry identity, then delegates publication to the existing P6
`persist_immutable_artifact(...)` boundary. The G3 bridge therefore inherits the
existing secure beneath-root, immutable replay/collision behavior and does not
create a second filesystem publication mechanism.

The caller still supplies the output root, relative path, and complete
`prohibited_roots` lifecycle-boundary evidence. Persistence conveys no canonical
standing, admission, authorization, activation, or reconciliation semantics.

## Regression surface

`tests/test_context_packaging_production_integration_p10_g3.py` covers:

- the exact G1-frozen source-ID fixture;
- complete stable source records and pack-local occurrences;
- source-ID stability across different pack-local positions;
- distinct IDs for different immutable snapshots;
- unresolved and ambiguous frame/source references;
- forced source-ID collision with conflicting stable records;
- missing/reordered frame closure;
- immutable registry persist/replay/collision behavior;
- rejection of registry-identity tampering before persistence.

Candidate-bound execution evidence is established separately; this document does
not claim that evidence before it is observed.
