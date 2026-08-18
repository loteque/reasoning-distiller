# P7 — Deterministic Consumer Update Proof

Status: **PASS**

P7 proved an in-place local update of the voxel-engine consumer from Reasoning Distiller `0.1.0` to `0.1.1` using the same deterministic installer and a read-only retrieved package.

## Identities

| Field | 0.1.0 | 0.1.1 |
|---|---|---|
| content identity | `sha256:ee0df2a91316ed0fa803d690b3e1b5bf6e07a320319255458e68ed1fb02b2dad` | `sha256:a487149caaaf41af70fdf2af6e52b7955a6c3fe14046321649357d21ba7241b4` |
| source commit | `8d81967b3f93e825172d961267818238fffc7d38` | `1da88edc000bbd6db78affe8e604ca499f516d55` |
| transport SHA-256 | `773ab0c9a5946f69ec568aabd9a255569f9511227142baadde077f826aa6cd8a` | `773ab0c9a5946f69ec568aabd9a255569f9511227142baadde077f826aa6cd8a` |

The transport bytes remained identical because the managed payload bytes did not change; version and source identity are carried in the manifest/installation metadata and therefore changed canonical content identity without fabricating a runtime code change.

## Proof

- update workflow run: `32107802754` — PASS
- consumer update commit: `a05a4f717c99792f8785076b727b7dabaa0aa923`
- update commit changed only `.reasoning-distiller/.installation/INSTALLATION.json` and `.reasoning-distiller/.installation/MANIFEST.json`
- project integration binding was then updated explicitly, separately from installation mechanics
- final consumer integration run: `32108062550` — PASS
- final local framework audit run: `32108062478` — PASS
- canonical PEMS/COVE bytes were not changed by the package update
- authority, rules, roles, and policy were not changed by the package update
- runtime remains local-only and network-blocked validation passes
- remote repository references are permitted only in the explicit update pathway and provenance metadata

The proof also exposed a stale project integration binding after installation. This was corrected as project-owned integration metadata, not by giving the installer authority to mutate project knowledge.

## Exit criterion

P7 is complete. A second immutable package was retrieved read-only, installed over an existing managed tree, produced an auditable local diff, preserved project semantic authority/canonical state, and passed final local runtime/audit validation.

Next gate: **P8 — accepted immutable release baseline and install/update instructions.**
