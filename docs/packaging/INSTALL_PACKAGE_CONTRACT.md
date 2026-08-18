# Reasoning Distiller Install Package Contract

Status: **Normative P1 contract**
Contract: `reasoning-distiller-install-package/1`
Governing plan: `docs/proposals/install-package/FINAL_PLAN.md`

## Boundary

A release package contains only generic Reasoning Distiller framework material. It is retrieved read-only by an agent already authorized in a consuming project and installed into a project-local managed root.

The installer and installed runtime require no network access and no working reference to the source repository.

Default managed root:

```text
.reasoning-distiller/
```

Project knowledge, project integration wrappers, role activation, authority, canonical state, policy, evidence, and adapters are outside the managed root.

## Artifacts

V1 release transport consists of:

```text
reasoning-distiller-<version>.tar.gz
reasoning-distiller-<version>.manifest.json
reasoning-distiller-<version>.sha256
```

The archive format is transport. Package semantic identity is the manifest content identity.

## Three identities

| Identity | Definition |
|---|---|
| release version | human release selector |
| content identity | SHA-256 of the canonical manifest identity payload defined below |
| transport digest | SHA-256 of exact downloaded archive bytes |

A release version must not identify more than one content identity.

## Manifest

The manifest conforms to `schemas/install-package-manifest.schema.json`.

Each file entry contains:

- `path`: POSIX-style path relative to the managed root;
- `mode`: `0644` or `0755` in V1;
- `sha256`: SHA-256 of exact file bytes.

Paths are normalized before acceptance and must be unique. Absolute paths, empty components, `.`/`..` components, backslashes, NUL, and case-fold collisions are invalid. Symlinks are not package file entries in V1.

`managed_roots` identifies top-level subtrees the package owns. Every file must fall under one declared managed root, except the reserved framework metadata files `VERSION`, `.installation/MANIFEST.json`, and `.installation/INSTALLATION.json` as applicable. V1 manifests describe release payload files; generated installation metadata is not included in the release file list.

## Canonical content identity

Algorithm: `rd-manifest-c14n/1`.

Construct this identity payload from the validated manifest:

```json
{
  "contract": "reasoning-distiller-install-package/1",
  "version": "<release version>",
  "source_commit": "<40 lowercase hex>",
  "compatibility": {},
  "managed_roots": [],
  "files": []
}
```

Rules:

1. `managed_roots` is sorted lexicographically by UTF-8 path string.
2. `files` is sorted lexicographically by `path`.
3. Each file object contains exactly `path`, `mode`, and `sha256`.
4. `compatibility` uses only strings, arrays of strings, and objects; object keys are sorted recursively by JSON serialization.
5. Serialize with UTF-8 JSON using sorted object keys, separators `,` and `:`, `ensure_ascii=false`, and no trailing newline.
6. Compute SHA-256 of those exact bytes and encode as lowercase hex.
7. The manifest field `content_identity` must equal `sha256:<hex>`.

`transport_sha256` is not part of the identity payload because compressed transport bytes may differ without changing installed content. It is verified separately.

## Compatibility

V1 manifest compatibility contains explicit contract selectors:

```json
{
  "project_knowledge_package": ["project-knowledge-package/1"],
  "rgp": ["rgp/1"],
  "backends": {
    "pems-cove": ["pems/2", "cove/1"]
  }
}
```

Additional backend keys may be added without granting authority or selecting a backend for a project. Compatibility declares what the package can work with; project configuration selects what is active.

## Installed metadata

After a successful install, the managed tree contains:

```text
.reasoning-distiller/.installation/MANIFEST.json
.reasoning-distiller/.installation/INSTALLATION.json
```

`MANIFEST.json` is the exact verified release manifest.

`INSTALLATION.json` conforms to `schemas/installation-record.schema.json` and records the installation event, including release version, content identity, transport digest, source commit, target managed root, and contract versions. Source repository/locator fields are optional provenance and update-discovery metadata only.

## Managed-tree rule

The installer may create, replace, or remove only files proven package-managed by the new or previous verified manifest plus `.installation/` transaction metadata defined by the installer contract.

It may read project-owned configuration for compatibility validation. It may not alter project knowledge, canonical state, authority, role activation, policy, or integration wrappers.

## Runtime isolation

Installed runtime must fail locally when required installed content is absent. It must never fall back to:

- a source-repository checkout;
- a remote import;
- a remote schema fetch;
- a symlink outside the managed root;
- a generic-repository path resolver.

Repository URLs and source locators are allowed only in metadata, documentation, and explicit update-discovery operations.

## P1 validation requirements

A conforming P1 implementation must prove:

- manifest and installation examples pass their schemas;
- invalid paths/modes/digests fail;
- duplicate and case-fold-colliding paths fail;
- files outside declared managed roots fail;
- content identity is independent of file declaration order and managed-root order;
- changing path, mode, digest, version, source commit, compatibility, or managed roots changes content identity;
- changing transport digest alone does not change content identity;
- same release version with a different content identity is treated as an identity collision by later release/install gates.

P1 defines contracts only. It does not authorize RGP semantic changes, project canonical migration, or project Steward authority changes.
