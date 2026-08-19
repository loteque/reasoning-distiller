# RIL Operator Registry Contract

Status: **Normative R4 primitive contract**

Contracts:

- `reasoning-distiller-operator-registry/1`
- `reasoning-distiller-initial-operator-request/1`
- `reasoning-distiller-initial-operator-result/1`

Depends on `docs/operations/RIL_COMMON_MUTATION_CONTRACT.md`.

## Purpose

R4 establishes project-local human operator identity and the protected root operator without granting Steward reconciliation or admission authority.

Installation and project bootstrap create no operator authority. The first authority-sensitive operation against a project with no operator registry must stop with `INITIAL_OPERATOR_REQUIRED` until the initial-operator ceremony succeeds.

## Project-owned paths

```text
project-knowledge/operators/
├── proposals/
├── approvals/
├── events/
└── current.json
```

`events/` is authoritative. `current.json` is a deterministic projection.

## Operator registry state

The v1 projection is canonical JSON:

```json
{
  "contract": "reasoning-distiller-operator-registry/1",
  "root_operator_id": "operator:owner",
  "operators": {
    "operator:owner": {
      "status": "active",
      "protected_root": true,
      "capabilities": [
        "rd:operator_management",
        "rd:role_registry",
        "rd:steward_authorization"
      ]
    }
  }
}
```

Core capabilities are package-defined and fixed for the initial root:

- `rd:operator_management`
- `rd:role_registry`
- `rd:steward_authorization`

Creating the initial operator does not grant semantic reconciliation or admission authority.

## Initial-operator ceremony

The ceremony has three deterministic stages:

```text
PLAN
  → exact proposal, no mutation

HUMAN APPROVAL
  → approval artifact bound to exact proposal digest

APPLY
  → validate empty operator history + exact approval
  → append INITIALIZE_ROOT event
  → write current projection
```

The initial operator being established is the human identity referenced by the approval artifact. In v1 the ceremony requires `authentication.method = human_confirmation` and `authentication.confirmation = ESTABLISH_ROOT_OPERATOR`. Stronger authentication evidence can be added later without changing operator identity semantics.

## PLAN

Input:

- project root;
- `operator_id` in the `operator:` namespace.

The planned transition is exactly:

```text
INITIALIZE_ROOT(operator_id)
```

with the complete fixed core capability set and `protected_root=true`.

PLAN must not create operator directories, proposals, approvals, events, or projections.

## APPLY preconditions

APPLY must fail closed unless all are true:

1. operator event history is empty;
2. no valid operator root already exists;
3. proposal domain is `operator_registry`;
4. proposal operation is `INITIALIZE_ROOT`;
5. proposal basis is the empty operator state;
6. target ID uses `operator:` namespace;
7. target receives exactly the fixed core capability set;
8. approval is bound to the exact proposal;
9. approval `operator_id` equals the root operator being established;
10. approval authentication records the required explicit human confirmation.

## Retry semantics

The same proposal + approval may be retried after successful application only as an idempotent `NO_CHANGE` when the resulting root state is still current.

A second distinct initial-root proposal after initialization fails with `ROOT_ALREADY_ESTABLISHED`.

The initial-operator ceremony never replaces the root. Root transfer belongs to R5.

## Projection behavior

Missing projection with valid history is rebuildable.

Conflicting projection fails closed.

Invalid event history fails closed.

## Required results

Expected outcomes include:

```text
PASS / PLANNED
PASS / APPLIED
PASS / NO_CHANGE
FAIL / INITIAL_OPERATOR_REQUIRED
FAIL / INVALID_INITIAL_OPERATOR
FAIL / HUMAN_CONFIRMATION_REQUIRED
FAIL / ROOT_ALREADY_ESTABLISHED
FAIL / APPROVAL_MISMATCH
FAIL / PROJECTION_CONFLICT
```

## Security and authority invariants

- Operator registration is administrative identity, not Steward authority.
- No agent may self-create root authority merely by claiming to be human.
- The primitive validates the explicit human-confirmation evidence required by v1; stronger authentication policy is intentionally deferred.
- Ordinary mutation cannot replace or remove the protected root.
- No consumer operation may reinterpret the fixed `rd:*` capability meanings.

## R4 conformance gate

R4 passes only if tests prove:

1. empty project reports initial operator required;
2. PLAN is mutation-free;
3. root proposal is deterministic;
4. wrong/missing human confirmation is rejected;
5. approval for another proposal is rejected;
6. APPLY creates exactly one protected root with exactly the fixed capabilities;
7. successful retry is `NO_CHANGE`;
8. a different second-root attempt is rejected;
9. missing projection rebuilds from history;
10. conflicting projection fails closed;
11. no Steward reconciliation/admission state is created.
