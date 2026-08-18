# P2 Deterministic Package Builder

Status: **Normative P2 implementation contract**
Builder contract: `reasoning-distiller-package-build/1`
Package contract: `reasoning-distiller-install-package/1`

## Purpose

`packaging/build_release_package.py` builds the immutable Reasoning Distiller install package from an exact source commit identity and an explicit allowlist.

The builder does not infer a branch head, choose a release version, publish artifacts, install into a consumer project, or include repository contents outside the allowlist.

## Inputs

```text
--version <release-version>
--source-commit <40-lowercase-hex>
--output-dir <local-directory>
```

The source commit is supplied by the runner and becomes part of canonical package content identity. The builder reads package policy from `packaging/package-build.json`.

## Allowlist boundary

V1 managed roots are:

```text
admission/
agents/
backends/
protocols/
schemas/
validators/
```

The builder traverses only these roots. Project knowledge, evaluation/reference corpus, tests, repository workflows, proposal/extraction history, and project integration material are not package inputs.

Symlinks and unsupported filesystem nodes inside a managed root fail closed.

## Determinism

For identical source bytes, build configuration, version, and source-commit inputs, two clean builds must produce:

- the same sorted file list and per-file digests;
- the same canonical `content_identity`;
- the same normalized tar members and metadata;
- the same `.tar.gz` bytes and transport SHA-256;
- the same manifest bytes;
- the same `.sha256` bytes.

Archive normalization uses sorted paths, fixed uid/gid `0`, empty owner/group names, mtime `0`, deterministic file modes from build policy, and gzip mtime `0`.

The package contract only requires canonical content identity to be stable; P2 deliberately proves the stronger property of byte-identical V1 transport output.

## Outputs

```text
reasoning-distiller-<version>.tar.gz
reasoning-distiller-<version>.manifest.json
reasoning-distiller-<version>.sha256
```

The manifest is validated against the P1 schema and semantic validator before outputs are accepted. The archive is re-opened and checked against the manifest before it is written.

## Authority boundary

The builder packages generic framework bytes only. It does not grant project role authority, select project policy, alter canonical project knowledge, perform semantic reconciliation, or write a consumer repository.

## P2 gate

P2 passes only when CI proves:

1. two clean builds from the same inputs are byte-identical;
2. package content is confined to the explicit allowlist;
3. project-owned/reference material cannot enter the payload by repository location alone;
4. unsafe symlinks fail closed;
5. changing packaged bytes changes package identities;
6. the generated manifest/archive validate under P1;
7. the existing extraction-parity suite remains green.
