# Context Packaging `/2` Builder Behavior Contract

Status: **Normative behavior freeze for the reconciled `/2` protocol amendment**

Contract:

- `reasoning-distiller-context-pack-builder/2`

Governing reconciliation:

- Stage 3 commit: `0b9853ffaccff73817f553001d3368a4384478d8`
- Stage 3 blob: `8f3b6ac5caf1a864088ba1e018bf2b39aeadf219`
- `/2` schema candidate basis: `fd76635490fb26e4c67b80c98b4e2b1b7bd44b0a`

This contract freezes behavior for a later conforming `/2` builder. It does not claim that `context_packaging/pack_builder.py` implements `/2`, does not remediate P5, and does not authorize P6, admission, canonical mutation, rendering, or production integration.

## 1. Contract dispatch

A conforming `/2` builder accepts only:

- `reasoning-distiller-context-profile/2`;
- `reasoning-distiller-context-pack-request/2`;
- requested output `reasoning-distiller-context-pack/2`.

It emits only `reasoning-distiller-context-pack/2` and success results under `reasoning-distiller-context-pack-result/2`.

Any `/1`/`/2` cross-family combination fails closed as a contract mismatch. No byte auto-upgrade or validation under the wrong family is permitted.

## 2. Knowledge provenance identity

For canonical `/2` knowledge provenance, a PEMS semantic item is identified by:

```text
(JCS(canonical_snapshot_ref), namespace, id)
```

where `namespace` is exactly `record` or `relation` and `id` is the exact opaque PEMS identifier.

The emitted subject is:

```json
{
  "source_ref": {"...": "exact canonical snapshot reference"},
  "pems_ref": {
    "namespace": "record",
    "id": "exact PEMS id"
  }
}
```

A snapshot-level subject remains the closed shape containing only `source_ref`.

`semantic_id` is never emitted in a canonical `/2` knowledge subject. Namespace information is never encoded into `id` or `cause_id`.

## 3. Coverage and causes

The expected semantic-item subject set is the union of exact record and relation identities in the selected P3 projection. A record and relation with the same string ID are different subjects.

Every selected semantic item must have exact outer-ledger coverage under the existing governed cause rules. Distinct deterministic causes are preserved. Cause ordering and any exact-duplicate coalescing continue to follow the already frozen P1c/P3 rules; this contract introduces no new cause vocabulary or deduplication semantics.

## 4. Canonical ordering

Builder-owned array ordering remains the P1c ordering. Inclusion-ledger entries sort by:

```text
(plane_rank, JCS(subject))
```

Because `pems_ref` is structurally inside the subject, record/relation namespace and opaque ID enter the existing JCS ordering directly. No namespace-specific sort rank or delimiter codec is introduced.

Equivalent host iteration orders must produce byte-identical canonical `/2` output.

## 5. PEMS schema resource

PEMS validation for `/2` binds the immutable resource:

```text
urn:reasoning-distiller:schema-resource:pems-v2:git-blob:cd7683d704e8aef2842a0c1b25b453fb1dbc8030
```

under `docs/design/CONTEXT_PACKAGING_V2_R4_RESOURCE.md` and `schemas/resources/context-packaging-v2-resource-registry.json`.

A conforming implementation fails closed rather than falling back to the historical mutable `main` URI.

## 6. Eligibility

A `/2` profile is a distinct exact profile artifact. Where eligibility is required, eligibility evidence must name that exact `/2` `(profile_id, profile_version, raw_sha256)` identity. Eligibility of a predecessor `/1` profile is not inherited or inferred.

## 7. No canonical migration

There is no canonical public `/1` to `/2` adapter in this contract. Existing `/1` packs remain `/1`. Canonical `/2` packs are rebuilt from exact governed `/2` inputs and P3 projection evidence. A legacy scalar `semantic_id` is never guessed into a namespace.

## 8. Scope boundary

This behavior contract is a protocol prerequisite for a later fresh P5 remediation activation. It does not modify the current P5 candidate, the P1d/P3 semantic contracts, accepted `/1` schema bytes, persistence, admission, or canonical state.
