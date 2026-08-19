# RIL Steward Authorization Contract

Status: **Normative v1 primitive contract**

Implements architecture gate **R7** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contract: `reasoning-distiller-steward-authorization-state/1`

## Purpose

Provide deterministic project-owned assignment of Steward authority to registered durable role definitions.

RIL facilitates the authorization transaction but **does not possess, infer, or create Steward authority on its own**. Authority exists only after an authorized human operator approves and applies an exact proposal.

## Authority scopes

R7 defines exactly two independent scopes:

```text
semantic_reconciliation
admission
```

For each scope, the authoritative state contains either one registered `role_id` or `null`.

```json
{
  "contract": "reasoning-distiller-steward-authorization-state/1",
  "assignments": {
    "admission": null,
    "semantic_reconciliation": "steward:default"
  }
}
```

The scopes are independent. Mutation of one scope MUST NOT change the other.

## Operations

R7 supports:

```text
AUTHORIZE(scope, role_id)
REASSIGN(scope, role_id)
REVOKE(scope)
```

Semantics:

- `AUTHORIZE` requires the scope to be unassigned.
- `REASSIGN` requires the scope to be assigned and the new target to differ from the current target.
- `REVOKE` requires the scope to be assigned and produces `null`.
- no operation performs implicit fallback or cross-scope mutation.

## Target requirements

For `AUTHORIZE` and `REASSIGN`, the target role MUST:

1. exist in the project role registry;
2. be currently `available`;
3. be identified by its durable project-global `role_id`.

`steward:default` is valid because it is the protected package-provided always-available Steward role.

Registration alone grants no authority. A role may be registered and available while holding no Steward scope.

If a role holding a scope later becomes unavailable, R7 does not silently revoke or transfer that scope. The assignment remains historically intact and higher-level status/operation checks MUST treat the scope as blocked until explicit human action resolves it.

## Human approval

Every mutation uses the common R1-R3 transaction substrate:

```text
current authorization history + requested scope transition
        ↓
proposal
        ↓ exact digest
human operator approval
        ↓
approval artifact
        ↓
apply
        ↓
append-only event
        ↓
current projection
```

The approving operator MUST:

- exist in the operator registry;
- be active;
- hold `rd:steward_authorization`;
- provide explicit `STEWARD_AUTHORIZATION_CHANGE` human-confirmation evidence bound to the exact proposal.

The operator is authorizing a role. The operator does not thereby become a Steward.

## Storage

Project-owned R7 state is stored under:

```text
project-knowledge/steward-authorization/
  events/
  current.json
  proposals/
  approvals/
```

Events are authoritative. `current.json` is a deterministic projection and may be rebuilt when missing. A conflicting projection fails closed.

Proposal and approval artifacts are durable evidence and MUST NOT be deleted after successful application.

## Fail-closed conditions

At minimum, mutation fails without changing authorization state when:

- scope is unknown;
- operation does not match current assignment state;
- target role does not exist;
- target role is disabled/unavailable;
- proposal basis is stale;
- approval is bound to another proposal;
- approving operator lacks `rd:steward_authorization`;
- operator, role, or authorization projection conflicts with authoritative history.

## Explicit non-authority

This primitive MUST NOT:

- perform semantic reconciliation;
- perform admission;
- activate a role for an invocation;
- create or mutate PEMS/COVE canonical knowledge;
- register roles;
- silently choose `steward:default` or any other role;
- infer authorization from a role name, active chat role, or package installation.

## Conformance gate

R7 PASS requires tests proving:

1. both scopes begin unassigned;
2. `AUTHORIZE` assigns exactly one available registered role to exactly one scope;
3. `semantic_reconciliation` and `admission` remain independent;
4. `REASSIGN` replaces only the selected scope;
5. `REVOKE` produces an explicitly unassigned scope;
6. the protected default Steward can be selected but is never selected automatically;
7. unknown or unavailable role targets are rejected;
8. an inactive/unauthorized operator cannot approve a transition;
9. exact proposal/approval binding and idempotent retry semantics are preserved;
10. projection conflict fails closed and missing projection is rebuildable;
11. durable proposal/approval/event evidence is retained;
12. no reconciliation, admission, PEMS, COVE, or canonical project state is created by R7.
