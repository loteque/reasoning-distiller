# RIL Operator Management and Root Transfer Contract

Status: **Normative R5 primitive contract — amended for accepted R18 delegability classification**

Contracts/building blocks:

- `reasoning-distiller-operator-registry/1`
- common `reasoning-distiller-proposal/1`
- common `reasoning-distiller-approval/1` / `reasoning-distiller-approval/2`
- common `reasoning-distiller-mutation-event/1`
- common `reasoning-distiller-operation-result/1`
- accepted `reasoning-distiller-authority-grant/1`
- accepted `reasoning-distiller-operation-delegability/1`

Governing design: `docs/design/RD_INIT_DESIGN_CONTRACT.md`, `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`, `docs/design/RIL_AUTHORITY_GRANT_DESIGN_CONTRACT.md`, and `docs/design/RIL_OPERATION_DELEGABILITY_CLASSIFICATION.md`.

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

R18 permits prospective `authority-grant:<id>` authority only for the exact delegable subset explicitly published below. Delegability never changes the capability required of the grantor when the grant is created and never permits an agent/runtime to become the authority holder.

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

All semantic mutations use the accepted common transaction sequence:

```text
plan → exact proposal digest → accepted approval authority basis → apply
     → append-only event → deterministic operator projection
```

Direct human approval remains available for all ordinary operations. Grant-derived approval is accepted only for operation classes explicitly marked `delegable: true` below.

### ADD_OPERATOR

Preconditions:

- target `operator_id` is a valid, non-root project-local operator identity;
- target does not already exist;
- capabilities are valid under the namespace rules.

The created operator is active and not protected root.

R18 classification:

```text
operation: ADD_OPERATOR
delegable: false
```

Creating a new durable administrative identity is non-delegable.

### UPDATE_CAPABILITIES

Preconditions:

- target exists;
- target is not the protected root;
- replacement capability set is valid.

This is full replacement, not an implicit merge.

R18 classification:

```text
operation: UPDATE_CAPABILITIES
delegability: DEFERRED
```

Until a separately accepted deterministic authority-non-increasing predicate exists, every `UPDATE_CAPABILITIES` proposal remains outside authority grants.

### DISABLE_OPERATOR

Preconditions:

- target exists;
- target is not the protected root.

Disabling preserves identity and history. It grants no fallback or authority transfer.

R18 publishes this exact grant-matching schema:

```text
operation_class: operator-registry.disable
delegable: true

authority_relevant_targets:
  - operator_id

selectors:
  operator_id: exact | one-of

constraints:
  operation: eq(DISABLE_OPERATOR)
```

Grant matching MUST independently prove from authoritative current operator-registry state that every selected target is not the protected root. Exact/finite target selection is required; wildcard, prefix, fuzzy, inferred, or natural-language operator targeting is not normative grant scope.

A grant-derived approval remains bound to the exact immutable proposal and still requires all accepted R17 checks, including workflow containment, D3 applicability revalidation, materiality clearance, grant lifecycle/limit validation, atomic approval issuance, and independent apply-time validation.

### REENABLE_OPERATOR

Preconditions:

- target exists;
- target is not the protected root.

The existing capability set is retained.

R18 classification:

```text
operation: REENABLE_OPERATOR
delegable: false
```

Re-enabling restores administrative actionability and is non-delegable in v1.

## Approval

An ordinary-management proposal may be approved through either accepted approval authority basis where the exact operation permits it:

```text
direct-operator
```

or, only for `operator-registry.disable`:

```text
authority-grant
```

For direct operator approval, the approving operator MUST, against authoritative current state:

- exist;
- be active;
- hold `rd:operator_management`;
- provide the required exact proposal-bound authentication/confirmation evidence.

For grant-derived `DISABLE_OPERATOR` approval, the grant creation ceremony MUST already have established authenticated prospective authority from an operator who satisfied the applicable `rd:operator_management` authority requirement, and the common grant validator MUST return `WITHIN_GRANT` for the exact proposal.

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

`TRANSFER_ROOT` is explicitly non-delegable under R18. An `authority-grant:<id>` MUST NOT satisfy this ceremony.

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
OUTSIDE_GRANT
NON_DELEGABLE
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
- rewrite historical operator events;
- allow authority grants to establish, restore, transfer, or expand protected/core operator authority beyond the explicitly accepted delegable subset.

## R5 / R18 conformance gate

PASS requires tests proving at least:

1. authorized manager can add a delegated operator through direct approval;
2. unauthorized/inactive approver is rejected;
3. project capabilities do not satisfy `rd:operator_management`;
4. capabilities can be replaced only through directly approved mutation while R18 deferral remains in force;
5. delegated operators can be disabled and reenabled through their permitted authority paths;
6. ordinary mutations cannot change the protected root;
7. root transfer requires current-root direct approval;
8. root-transfer target must be active and hold all core capabilities;
9. successful root transfer leaves exactly one protected root;
10. old root remains an ordinary operator after transfer;
11. retry is idempotent while old approval cannot authorize a later transition;
12. no Steward/admission/canonical state is created;
13. a valid workflow-bound grant can authorize an exact non-root `DISABLE_OPERATOR` proposal when all R17 checks pass;
14. an operator-disable grant cannot target the protected root, even if the grant payload names that operator;
15. exact and finite `one-of` operator target selectors are enforced and out-of-scope targets return `OUTSIDE_GRANT`;
16. grants cannot authorize `ADD_OPERATOR`;
17. grants cannot authorize `REENABLE_OPERATOR`;
18. grants cannot authorize `TRANSFER_ROOT`;
19. grants cannot authorize `UPDATE_CAPABILITIES` while the operation remains `DEFERRED`;
20. grant-derived operator disable preserves exact proposal binding, D3 revalidation, materiality, grant-consumption accounting, and apply-time validation.

## R18 integration status

R18-I1 and the operator-management portion of R18-I3 are integrated by this amendment.
