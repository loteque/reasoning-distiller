# RIL Operator Management and Root Transfer Contract

Status: **Normative R5 primitive contract**

Contracts/building blocks:

- `reasoning-distiller-operator-registry/1`
- common `reasoning-distiller-proposal/1`
- common `reasoning-distiller-approval/1`
- common `reasoning-distiller-mutation-event/1`
- common `reasoning-distiller-operation-result/1`

Governing design: `docs/design/RD_INIT_DESIGN_CONTRACT.md` and `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

## Purpose

R5 adds deterministic administration of delegated human operators and a separate protected-root transfer ceremony.

It does not grant Steward reconciliation/admission authority and does not create canonical project knowledge.

## Authority model

Ordinary operator administration requires an **active** operator holding:

```text
rd:operator_management
```

The protected root may use that capability like any other manager, but ordinary mutations MUST NOT disable, demote, remove, or otherwise mutate the protected root.

Root transfer is a distinct ceremony. It requires explicit approval by the currently protected root and cannot be performed by delegated `rd:operator_management` authority alone.

## Operator entry

A non-root operator entry has the form:

```json
{
  "status": "active",
  "protected_root": false,
  "capabilities": ["rd:role_registry"]
}
```

Capabilities are unique and sorted canonically.

Reasoning Distiller capability names are fixed to the accepted `rd:*` vocabulary. R5 recognizes:

```text
rd:operator_management
rd:role_registry
rd:steward_authorization
```

Project-defined administrative capabilities MUST use `project:<name>`. A `project:*` capability never satisfies an `rd:*` capability check.

Unknown `rd:*` capability names fail closed.

## Ordinary operations

R5 supports:

```text
ADD_OPERATOR
UPDATE_CAPABILITIES
DISABLE_OPERATOR
REENABLE_OPERATOR
```

All use the accepted common transaction sequence:

```text
plan → exact proposal digest → explicit human approval → apply
     → append-only event → deterministic operator projection
```

### ADD_OPERATOR

Preconditions:

- target `operator_id` is a valid, non-root project-local operator identity;
- target does not already exist;
- capabilities are valid under the namespace rules.

The created operator is active and not protected root.

### UPDATE_CAPABILITIES

Preconditions:

- target exists;
- target is not the protected root;
- replacement capability set is valid.

This is full replacement, not an implicit merge.

### DISABLE_OPERATOR

Preconditions:

- target exists;
- target is not the protected root.

Disabling preserves identity and history. It grants no fallback or authority transfer.

### REENABLE_OPERATOR

Preconditions:

- target exists;
- target is not the protected root.

The existing capability set is retained.

## Human approval

An ordinary-management proposal is approved by an operator identity using explicit human confirmation:

```text
ADMINISTER_OPERATORS
```

Apply MUST verify against authoritative current state that the approver:

- exists;
- is active;
- holds `rd:operator_management`.

Approval remains exact-proposal-bound and follows common consumed-approval retry semantics.

## Root transfer ceremony

Root transfer is intentionally not an ordinary operator mutation.

Operation:

```text
TRANSFER_ROOT
```

A root-transfer proposal identifies:

```text
from_operator_id
→ to_operator_id
```

Preconditions at plan/apply time:

- `from_operator_id` is the current protected root;
- target operator already exists;
- target operator is active;
- target already holds every core Reasoning Distiller administrative capability;
- target is not already root.

Required core capabilities:

```text
rd:operator_management
rd:role_registry
rd:steward_authorization
```

Root transfer does **not** silently add missing capabilities. Capability delegation must be completed and approved before the ceremony.

The approval artifact MUST be issued by the current root with explicit human confirmation:

```text
TRANSFER_ROOT_OPERATOR
```

Successful transfer atomically:

1. changes `root_operator_id` to the target;
2. sets the old root `protected_root` to `false`;
3. sets the target `protected_root` to `true`;
4. preserves both operators' capability sets and active statuses;
5. appends one immutable operator-registry mutation event.

The old root remains an ordinary active operator unless changed later through an independently approved ordinary mutation.

No ordinary operation may create a second protected root.

## Retry and fail-closed behavior

The common consumed-approval rules apply:

```text
same approval + resulting state still current
  → PASS / NO_CHANGE

same approval + state changed later
  → FAIL / APPROVAL_ALREADY_CONSUMED

changed proposal
  → FAIL / APPROVAL_MISMATCH
```

Expected failures include:

```text
OPERATOR_NOT_FOUND
OPERATOR_ALREADY_EXISTS
ROOT_PROTECTED
APPROVER_NOT_AUTHORIZED
INVALID_CAPABILITY
TARGET_INACTIVE
TARGET_MISSING_CORE_CAPABILITIES
ROOT_TRANSFER_SOURCE_MISMATCH
PROJECTION_CONFLICT
STALE_BASIS
```

Conflicting projections and invalid authoritative event history remain fail-closed under the common substrate.

## Non-authority invariants

R5 MUST NOT:

- create or mutate the role registry;
- grant Steward reconciliation authority;
- grant admission authority;
- create activation evidence;
- reconcile a Distiller submission;
- mutate PEMS/COVE/canonical state;
- rewrite historical operator events.

## R5 conformance gate

PASS requires tests proving at least:

1. authorized manager can add a delegated operator;
2. unauthorized/inactive approver is rejected;
3. project capabilities do not satisfy `rd:operator_management`;
4. capabilities can be replaced only through approved mutation;
5. delegated operators can be disabled and reenabled;
6. ordinary mutations cannot change the protected root;
7. root transfer requires current-root approval;
8. root-transfer target must be active and hold all core capabilities;
9. successful root transfer leaves exactly one protected root;
10. old root remains an ordinary operator after transfer;
11. retry is idempotent while old approval cannot authorize a later transition;
12. no Steward/admission/canonical state is created.
