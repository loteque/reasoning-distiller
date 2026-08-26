# Context Packaging `/2` R4 PEMS Schema Resource

Status: **Normative implementation prerequisite for the reconciled `/2` packaging amendment**

Governing reconciliation:

- Stage 3 commit: `0b9853ffaccff73817f553001d3368a4384478d8`
- Stage 3 blob: `8f3b6ac5caf1a864088ba1e018bf2b39aeadf219`
- governing plan: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd` / `8474d2da42f863f0a190fd80292085176d3f97f0`

This artifact establishes the R4 prerequisite only. It does not change PEMS semantics, edit the inherited `/1` schemas, remediate P5, begin P6, mutate canonical state, perform admission, or establish any role authority.

## 1. Immutable package-owned resource identity

The `/2` schema family binds PEMS/2 through this retrieval/resource identity:

```text
urn:reasoning-distiller:schema-resource:pems-v2:git-blob:cd7683d704e8aef2842a0c1b25b453fb1dbc8030
```

That identity denotes exactly the package-owned repository artifact:

```text
repository = loteque/reasoning-distiller
path       = backends/pems-cove/pems-v2.schema.json
git_blob   = cd7683d704e8aef2842a0c1b25b453fb1dbc8030
raw_sha256 = sha256:b08e592ab7c10092ff381fe8057cac63ccb7aaa077b52532f5ee609c6fd279c3
semantic   = pems/2
```

The machine-readable registry is `schemas/resources/context-packaging-v2-resource-registry.json`.

## 2. Resolution rule

A `/2` validator MUST resolve the immutable resource identity by registering the exact bytes of the pinned Git blob above under that identity before validating the `/2` schema closure. Network retrieval is not part of this resolution rule.

The PEMS schema's historical embedded `$id` is observed metadata on the pinned bytes. It is not the `/2` retrieval identity and MUST NOT be used by `/2` as evidence of immutability. The resource contains only local-fragment `$ref` values, so registering the exact pinned bytes under the immutable alias preserves the existing PEMS validation semantics without introducing a remote dependency.

A resolver MUST fail closed if the repository path does not have the exact pinned Git blob identity or raw SHA-256. It MUST NOT fall back to `main`, another branch, an unpinned URL, or a different local file.

## 3. Immutability and versioning

The source Git blob is already content-addressed and immutable. The alias embeds that exact blob identity. A future PEMS schema byte change therefore requires a distinct resource identity and a separately reviewed packaging-schema basis. Rebinding this alias to different bytes is non-conforming.

No accepted `/1` artifact is changed or reclassified by this rule. In particular, the inherited `/1` mutable-`main` PEMS reference remains a separately classified historical red rather than being silently repaired under `/1`.

## 4. R4 disposition

`R4_IMMUTABLE_PEMS_RESOURCE_ESTABLISHED`

The prerequisite is satisfied for subsequent `/2` schema-family freeze only if conformance mechanically verifies the resource registry against the exact blob and SHA-256 above and demonstrates that `/2` schema validation resolves PEMS through the immutable alias without network retrieval.
