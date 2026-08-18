# P3 Deterministic Installer

Status: **Implemented**
Entrypoint: `packaging/rd_install.py`
Contract: `reasoning-distiller-installer/1`

## Purpose

`rd_install.py` is the canonical local installer executed by an already-authorized runner. The runner retrieves the release package, manifest, and expected transport digest. The installer performs no network I/O and has no source-repository fallback.

For the same package bytes, manifest, explicit arguments, and target pre-state, the installer produces the same managed framework tree or the same fail-closed result. `installed_at` defaults to the fixed value `1970-01-01T00:00:00Z`; a runner may explicitly supply event metadata without changing package content identity.

## P3 transaction

```text
verify local artifacts
  -> verify manifest/content identity
  -> verify archive/member bytes and modes
  -> read project compatibility (optional, read-only)
  -> verify previous installation manifest
  -> detect managed-file drift
  -> apply explicit downgrade policy
  -> stage complete new tree
  -> validate staged tree
  -> move previous tree to backup
  -> activate staged tree
  -> validate live tree
  -> remove backup
```

If live-tree validation fails during the P3 transaction, the previous managed tree is restored. Crash-journal recovery for interruption between filesystem operations is intentionally the P4 gate.

## Ownership boundary

The installer may create, replace, or remove only the selected managed root (default `.reasoning-distiller/`) plus temporary sibling staging/backup paths required for the transaction. Project knowledge is read-only and is never migrated by installation.

Unknown pre-existing managed trees fail closed. Existing installations must contain a valid `.installation/MANIFEST.json`; every previously managed file is checked for content and mode drift before an update.

Files added under previously managed roots are drift and block update. Files elsewhere in the project are untouched.

## Compatibility

When `--project-package` is supplied, the installer checks:

- Project Knowledge Package contract is supported by the release manifest;
- project `framework.compatible_contracts` includes both `reasoning-distiller-install-package/1` and `reasoning-distiller-installer/1`;
- selected canonical backend type is listed by release compatibility when one is declared.

Backend-specific version/config validation remains the responsibility of backend/project validators and later consumer integration gates.

## Downgrades

Numeric dotted version downgrades are rejected by default. `--allow-downgrade` is an explicit runner decision and permits the downgrade after all normal integrity, compatibility, and drift checks pass.

A repeated release version is accepted only when its content identity is unchanged.

## Example

```bash
python packaging/rd_install.py \
  --package /tmp/reasoning-distiller-0.3.0.tar.gz \
  --manifest /tmp/reasoning-distiller-0.3.0.manifest.json \
  --transport-sha256 <64-lowercase-hex> \
  --target /workspace/project \
  --project-package /workspace/project/project-knowledge/package.json
```

Optional provenance/update fields (`--source-repository`, `--source-locator`, `--update-locator`) are installation metadata only and are not runtime dependencies.

## P3 acceptance proof

The P3 suite proves:

- clean install;
- deterministic installed payload and default metadata;
- update preserving project-owned files;
- explicit downgrade policy;
- content and unexpected-file drift rejection;
- bad transport rejection before live-tree change;
- project compatibility rejection before activation;
- unknown local managed-root rejection;
- post-activation validation rollback to the prior verified installation.

P4 is the next gate and adds journaled crash/interruption recovery.