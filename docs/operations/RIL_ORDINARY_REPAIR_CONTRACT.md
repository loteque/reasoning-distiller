# RIL Ordinary Repair Contract

Status: **Normative v1 primitive contract**

Implements architecture gate **R10** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contract:

- `reasoning-distiller-ordinary-repair-result/1`

## Purpose

Provide an explicit, deterministic recovery primitive for **derived projections only**.

Ordinary repair exists for the case where authoritative append-only history is valid but a current projection is missing, malformed, stale, or otherwise inconsistent with replay.

```text
append-only history
      ↓ validate + replay
  history valid?
   ├─ no  → STOP / exceptional recovery required
   └─ yes → derive exact current state
                ↓
        replace/recreate projection
```

Ordinary repair grants no authority and performs no semantic state transition.

## Authoritative boundary

Append-only mutation events are authoritative. Current projections are derived.

Ordinary repair MUST NOT:

- create, edit, delete, reorder, rename, or truncate mutation events;
- create a mutation event representing repair;
- modify proposal, approval, submission, activation, reconciliation, admission, PEMS, or COVE artifacts;
- infer a replacement state when replay fails;
- conceal invalid authoritative history.

If event replay is invalid, ordinary repair MUST return `FAIL/EXCEPTIONAL_RECOVERY_REQUIRED` and perform no mutation.

## Supported v1 domains

R10 repairs the derived projections for:

- `operator_registry`;
- `role_registry`;
- `steward_authorization`.

Each domain uses its already-defined initial state and storage paths.

## Repair semantics

For a selected domain:

1. Replay authoritative history from the domain's normative initial state.
2. If replay fails, return `FAIL/EXCEPTIONAL_RECOVERY_REQUIRED`.
3. Derive canonical projection bytes from the replayed state.
4. If the projection is already an exact canonical match, return `PASS/NO_CHANGE`.
5. If the projection is missing, create it atomically and return `PASS/REBUILT`.
6. If the projection is a normal file but differs, replace it atomically and return `PASS/REPAIRED`.
7. If the projection path is a symlink, directory, or other unsafe path conflict, return `FAIL/PROJECTION_PATH_CONFLICT` without mutation.

A malformed or non-canonical **regular projection file** is derived-state corruption and may be replaced after authoritative replay succeeds.

## Whole-project repair

`repair_all(project_root)` evaluates supported domains in deterministic order:

```text
operator_registry
role_registry
steward_authorization
```

All authoritative histories MUST validate before any projection is changed. This preflight rule prevents partial repair when another supported domain already requires exceptional recovery.

After successful preflight, each domain projection is independently rebuilt/repaired/no-op'd from replay.

## Result envelope

Domain repair returns:

```json
{
  "contract": "reasoning-distiller-ordinary-repair-result/1",
  "status": "PASS|FAIL",
  "outcome": "NO_CHANGE|REBUILT|REPAIRED|EXCEPTIONAL_RECOVERY_REQUIRED|PROJECTION_PATH_CONFLICT",
  "domain": "operator_registry|role_registry|steward_authorization"
}
```

Whole-project repair returns the same contract with `domain: "all"` and a deterministic `repairs` map when successful.

## No approval ceremony

Ordinary repair does not alter authoritative semantic state. It deterministically re-materializes derived state from already-authorized history, so R10 does not require a new proposal/approval/event transaction.

Exceptional recovery is a separate gate and ceremony.

## Conformance gate

R10 PASS requires tests proving:

1. valid history + missing projection → exact deterministic rebuild;
2. valid history + stale projection → exact deterministic repair;
3. valid history + malformed regular projection → repair;
4. already-valid projection → idempotent `NO_CHANGE`;
5. invalid event history → `EXCEPTIONAL_RECOVERY_REQUIRED` and no projection mutation;
6. unsafe projection path → fail closed;
7. event bytes are identical before and after every ordinary repair;
8. whole-project repair preflights every supported history before mutating any projection;
9. repaired projections subsequently classify as valid;
10. no new authority, semantic mutation event, PEMS, or COVE state is created.
