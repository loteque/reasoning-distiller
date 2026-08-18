# P4 — Journaled Installer Recovery

Status: **Implemented**

P4 hardens `packaging/rd_install.py` against process interruption during activation or restoration.

## Recovery artifacts

The installer may create two temporary project-root artifacts:

```text
.rd-install-transaction.json
.rd-install-backup/
```

They are installer-owned recovery state, not project knowledge and not part of the installed framework tree.

The journal contract is `reasoning-distiller-install-transaction/1`.

## State model

```text
PREPARED
  -> BACKUP_PENDING
  -> ACTIVATE_PENDING
  -> VALIDATE_PENDING
  -> COMMITTED

Any non-COMMITTED interrupted state
  -> RESTORE_PENDING
  -> previous verified install or empty state
```

`COMMITTED` means the incoming local tree has already passed installed-tree validation. If interruption occurs after that durable state, recovery finalizes the new installation rather than rolling it back.

All earlier states recover to the exact previous verified installation. If there was no previous install, they recover to an empty managed root.

## Mandatory behavior

Before reading or applying a new package, every install invocation runs recovery.

Recovery fails closed when:

- a backup exists without a journal;
- the journal contract, fields, root, or state are invalid;
- a previous installation is expected but cannot be recovered and verified;
- a `COMMITTED` journal does not match the live incoming content identity.

No new install proceeds until recovery reaches a clean state.

## Idempotency

Restoration is idempotent across interruption. If the backup has already been renamed back to the managed root but the process stopped before journal removal, a later recovery verifies the restored manifest content identity and finalizes cleanup.

## CLI

Recovery can be requested explicitly:

```bash
python packaging/rd_install.py --recover-only --target /workspace/project
```

Normal installation performs the same recovery automatically before package validation.

## P4 pressure cases

The P4 suite covers:

- interruption after prior installation has moved to backup;
- interruption after incoming activation;
- interruption during a first install with no prior state;
- interruption after durable `COMMITTED` state;
- interruption after restore rename but before journal cleanup;
- orphan backup rejection;
- malformed journal rejection;
- preservation of project-owned files throughout recovery.

P4 does not alter RGP, reconciliation authority, project canonical state, or package semantics.
