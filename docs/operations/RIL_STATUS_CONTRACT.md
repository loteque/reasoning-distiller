# RIL Composite Lifecycle Status Contract

Status: **Normative v1 primitive contract**

Implements architecture gate **R9** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contract: `reasoning-distiller-status/1`

## Purpose

Provide a deterministic, read-only classification of observable Reasoning Distiller project state.

Status is a projection over lower-level state. It is **not** authoritative state, grants no authority, performs no repair, and MUST NOT mutate the project.

## Result

A successful classification has this shape:

```json
{
  "contract": "reasoning-distiller-status/1",
  "status": "PASS",
  "dimensions": {},
  "blocker": null,
  "next_action": "...",
  "lifecycle": "..."
}
```

`blocker`, when present, is:

```json
{
  "precedence": 1,
  "code": "...",
  "dimension": "..."
}
```

The classifier MUST report all dimensions it can establish independently even when one dimension blocks forward progress.

## Dimensions

R9 classifies:

| Dimension | States |
|---|---|
| installation | `MISSING`, `VALID`, `INCOMPATIBLE` |
| project_bootstrap | `MISSING`, `VALID`, `CONFLICT` |
| operator | `MISSING`, `VALID`, `CONFLICT` |
| role_registry | `VALID`, `REBUILDABLE`, `CONFLICT` |
| reconciliation_authority | `UNASSIGNED`, `AVAILABLE`, `TARGET_UNAVAILABLE`, `CONFLICT` |
| admission_authority | `UNASSIGNED`, `AVAILABLE`, `TARGET_UNAVAILABLE`, `CONFLICT` |
| projection_health | `VALID`, `REBUILDABLE`, `CONFLICT` |
| history_health | `VALID`, `INVALID` |
| evidence | `NONE`, `AVAILABLE` |
| candidate | `NONE`, `PENDING` |
| reconciliation | `NOT_REQUIRED`, `REQUIRED`, `BLOCKED` |
| admission | `NOT_READY`, `BLOCKED` |

R9 intentionally does not claim `SELECTED`, `VALID_SUBMISSION`, `DISPOSITION_READY`, `READY`, or `ADMITTED`; those stronger states depend on later R12-R14 primitives.

## Installation and bootstrap

Installation is `VALID` only when `.reasoning-distiller` exists as a normal directory. A symlink or non-directory at that path is `INCOMPATIBLE`.

Project bootstrap is `VALID` only when:

- `project-knowledge` is a normal directory;
- `project-knowledge/project.json` is a normal file;
- its canonical bytes exactly match the v1 project bootstrap contract.

Missing required bootstrap state is `MISSING`; conflicting state is `CONFLICT`.

## Authoritative histories and projections

Operator, role, and Steward-authorization histories are validated by the R1-R8 replay/projection primitives.

Rules:

- invalid authoritative event history => `history_health=INVALID`;
- present projection differing from valid replay => `projection_health=CONFLICT`;
- missing projection with valid replay => `projection_health=REBUILDABLE`;
- otherwise => `projection_health=VALID`.

R9 MUST NOT invoke rebuild functions. A `REBUILDABLE` observation remains read-only.

## Authority availability

For each Steward scope independently:

- no assignment => `UNASSIGNED`;
- assigned role exists and is `available` => `AVAILABLE`;
- assigned role is missing or disabled => `TARGET_UNAVAILABLE`;
- role/authorization history or projection conflict => `CONFLICT`.

Status does not infer activation evidence. An available authorization means only that durable authorization currently points to an available role.

## Evidence and candidate observations

R9 may observe only filesystem presence:

- any normal file under `project-knowledge/evidence` => `evidence=AVAILABLE`, otherwise `NONE`;
- any normal file under `project-knowledge/submissions` => `candidate=PENDING`, otherwise `NONE`.

This does not validate semantic content.

## Blocker precedence

The first blocker MUST follow this order:

1. installation or project incompatibility/conflict;
2. invalid authoritative history;
3. conflicting derived projection;
4. missing initial operator when an authority-sensitive next transition exists;
5. missing or unavailable required reconciliation authority;
6. activation evidence required for a later authority-bearing operation;
7. missing explicit evidence/candidate input;
8. no blocker; normal next transition.

`REBUILDABLE` is not corruption. It may become the next action (`REBUILD_PROJECTIONS`) but MUST NOT be repaired by status.

## Simplified lifecycle

R9 may emit only lifecycle states justified by implemented primitives and filesystem observations:

```text
UNINSTALLED
INSTALLED
INITIALIZED
EVIDENCE_READY
CANDIDATE_READY
RECONCILIATION_REQUIRED
```

Later gates may extend this enum without changing R9's read-only invariants.

## Next action

Stable R9 next-action values:

```text
INSTALL
BOOTSTRAP_PROJECT
REPAIR_HISTORY
REPAIR_PROJECTION
ESTABLISH_INITIAL_OPERATOR
AUTHORIZE_RECONCILIATION_STEWARD
RESTORE_RECONCILIATION_ROLE
ADD_EVIDENCE
RUN_DISTILLER
PROVIDE_ACTIVATION_EVIDENCE
RECONCILE
READY
```

`READY` means no currently implemented R9 prerequisite is missing; it does not imply admission has occurred.

## Read-only invariant

A status call MUST NOT create, remove, rewrite, rebuild, authorize, activate, reconcile, or admit anything. Directory entries and file bytes before and after classification MUST be identical.

## Conformance gate

R9 PASS requires tests proving:

1. empty target reports `UNINSTALLED`/`INSTALL`;
2. installed but unbootstrapped reports `INSTALLED`/`BOOTSTRAP_PROJECT`;
3. valid bootstrap with no operator reports the first-use operator requirement before authority-sensitive progress;
4. invalid authoritative history outranks projection and authority blockers;
5. projection conflict outranks missing authority;
6. missing projection is `REBUILDABLE` and is not rebuilt;
7. reconciliation/admission authorization scopes are classified independently;
8. disabled authorization target is `TARGET_UNAVAILABLE` with no fallback;
9. evidence and candidate observations never claim semantic validity;
10. status performs zero filesystem mutation.
