# Deterministic Context Packaging `/2` Bytes, Digests, and Toolchain Contract

Status: **Normative successor P1c freeze for the reconciled `/2` packaging amendment**

Contract:

- `reasoning-distiller-context-pack-bytes-digests-toolchain/2`

Governing evidence:

- governing plan: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd` / `8474d2da42f863f0a190fd80292085176d3f97f0`
- Stage 3 reconciliation: `0b9853ffaccff73817f553001d3368a4384478d8` / `8f3b6ac5caf1a864088ba1e018bf2b39aeadf219`
- predecessor P1c contract blob: `97cd7bce6be427e8ae0703d3c0a086abf7ad7a67`
- accepted P1c remediation basis: `ec5fe4c6c7e8678c3ead0ac629d97d04022b914c`

This successor contract inherits the predecessor P1c byte representation, RFC 8785 `jcs/1` behavior, domain-separated SHA-256 framing, canonical array ordering rules, lowercase canonical SHA-256 emission, non-circular pack identity construction, exact raw-profile/request document binding, and P1a standing-evidence normalization except where this contract explicitly changes the bound schema family and pack-builder behavior identity.

It does not claim that the current P5 `context_packaging/pack_builder.py` implements `/2`; that implementation remains a later bounded P5 remediation after independent review and closure of this amendment basis.

## 1. Exact `/2` schema basis

The `/2` family is bound to these exact schema blobs:

| Schema | Git blob |
|---|---|
| `schemas/context-profile-v2.schema.json` | `58794d4dc5251be4444b84b56f474ff5544e6e10` |
| `schemas/context-pack-request-v2.schema.json` | `372c8f65cee97999db626632944c6d57a42738b7` |
| `schemas/context-pack-v2.schema.json` | `810c921c086f11b2e35f7d21c9d9f5251405898b` |
| `schemas/context-pack-result-v2.schema.json` | `8759a26030fe37fb07852f969f296b5265a18995` |

The unchanged shared `/1` schemas remain bound to their accepted blobs:

| Shared schema | Git blob |
|---|---|
| `schemas/context-pack-failure.schema.json` | `10195c52df81156a954eb9b5acee5a4f1b26f576` |
| `schemas/context-pack-receipt.schema.json` | `b8ef42aec266acd87c5a0b45740e7122c30114e5` |
| `schemas/context-profile-eligibility.schema.json` | `ad8ba5839136fe7e1080d1d7e26ca351202864dc` |
| `schemas/context-source-binding.schema.json` | `e5d5bc005f7a3dcd4f2f788dd08d49f3b57d4a1e` |

The predecessor `/1` profile/request/pack/result schema blobs remain immutable historical artifacts and are not part of the `/2` schema basis.

## 2. Immutable PEMS resource basis

The `/2` pack schema binds:

```text
urn:reasoning-distiller:schema-resource:pems-v2:git-blob:cd7683d704e8aef2842a0c1b25b453fb1dbc8030
```

The package-owned resource registry is blob `3afb30b240d0d26d4deb21938e379a2a570b26ab` at `schemas/resources/context-packaging-v2-resource-registry.json`. Resolution registers the exact PEMS schema blob `cd7683d704e8aef2842a0c1b25b453fb1dbc8030`, raw SHA-256 `sha256:b08e592ab7c10092ff381fe8057cac63ccb7aaa077b52532f5ee609c6fd279c3`, under that immutable alias without network retrieval.

The historical PEMS `$id` containing `/blob/main/` is not the `/2` resource identity.

## 3. `/2` builder behavior identity

The behavior contract is:

```text
reasoning-distiller-context-pack-builder/2
```

and is frozen by:

```text
docs/design/CONTEXT_PACKAGING_V2_BUILDER_BEHAVIOR_CONTRACT.md
git-blob:f037625990497bd4eb491238367516a4c61b4e0c
raw-sha256:sha256:b99020add18a9ab64cb0e42c3450a02807cb5b080127fe0f9a49eac4588fc7ed
```

A later conforming implementation must bind its own exact implementation artifact identity in the toolchain record while implementing this behavior contract. This amendment freezes behavior; it does not falsely identify the current P5 implementation as conforming `/2` code.

## 4. Knowledge provenance and ordering

Canonical `/2` semantic-item subjects use `pems_ref {namespace,id}` plus exact `source_ref`. The lossless grouping identity is:

```text
(JCS(canonical_snapshot_ref), namespace, id)
```

The existing inclusion-ledger array order remains:

```text
(plane_rank, JCS(subject))
```

The existing cause rank/order and already frozen duplicate semantics remain unchanged. `pems_ref` participates through ordinary JCS of the subject. There is no namespace-specific sort rank and no tagged-string codec.

## 5. Digest framing and domains

The predecessor P1c digest framing contract remains exactly:

```text
UTF8("reasoning-distiller-context-digest/1") ||
0x00 || U16BE(len(ASCII(domain))) || ASCII(domain) ||
U64BE(len(body)) || body
```

with SHA-256 and lowercase hexadecimal output. The frozen domains remain unchanged:

```text
context-profile
context-pack-request
canonical-state-binding
selected-pems-projection
cove-payload-set
context-pack-manifest
context-pack-payload-set
context-pack-identity
```

No new digest domain is introduced for `pems_ref`.

## 6. Identity-preimage `/1` reuse rule

`reasoning-distiller-context-pack-identity-preimage/1` is version-neutral across `/1` and `/2` only while all five properties remain identical:

1. member set;
2. meaning of every member;
3. canonical serialization/framing of the preimage;
4. hash algorithm and framing rule;
5. domain semantics of the resulting pack identity.

The `/2` profile, request, manifest, payload and toolchain values enter through the existing component digest members. Therefore `/2` pack identity changes naturally without renaming this inner preimage contract. Any future change to one of the five properties requires an independently versioned preimage contract before use.

## 7. Receipt `/1` sharing

`reasoning-distiller-context-pack-receipt/1` remains a version-neutral opaque digest receipt. It binds request ID, pack identity, serialized-pack digest and optional artifact location without interpreting pack fields.

Receipt `/1` alone MUST NOT be used to infer whether the referenced pack is `/1` or `/2`. Operations requiring version dispatch must possess and inspect the referenced pack contract under its governing protocol. This clause introduces no P6 lookup or persistence semantics.

## 8. Digest stability and churn

For exact equivalent immutable source bindings and selected PEMS/COVE payloads:

- raw source byte digests remain stable when source bytes are unchanged;
- canonical-state-binding digest remains stable when its exact binding preimage is unchanged;
- selected PEMS digest remains stable when its exact selected-Pems preimage is unchanged;
- COVE payload-set and payload-set digests remain stable when their exact preimages are unchanged;
- profile digest changes when the versioned profile canonical value changes;
- request digest changes when the versioned request canonical value changes;
- manifest digest changes where versioned manifest inputs change;
- pack identity changes through changed component digests under the shared identity-preimage rule;
- serialized-pack digest changes because canonical `/2` wire bytes differ.

No digest is assumed stable or changed solely from its name; exact preimage equality controls.

## 9. Deterministic conformance vector

The `/2` conformance fixture freezes a same-string record/relation collision and intentionally supplies its inclusion ledger and toolchain components in non-canonical order. Conformance must reproduce the fixture's exact canonical ledger order, component digests, pack identity and serialized-pack digest using the inherited P1c reference algorithms.

This vector is protocol conformance machinery only. It is not evidence that P5 has been remediated or that production integration exists.

## 10. Scope boundary

This successor basis does not change P1d/P3 semantics, accepted `/1` bytes, the current P5 candidate, P6 persistence, rendering, production invocation, admission, canonical state, authority, or activation. Independent review of this exact amendment implementation is required before any fresh P5 remediation begins.
