# RIL Activation Evidence Contract

Status: **Normative v1 primitive contract**

Implements architecture gate **R8** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contract:

- `reasoning-distiller-role-activation/1`

## Purpose

Prove that a specific runtime invocation is explicitly acting as a durable registered role before a Steward-authority operation is permitted.

Activation is distinct from registration and authorization:

```text
registered role
    +
authorized for requested scope
    +
accepted activation evidence for current invocation
    =
runtime role activation accepted
```

This primitive is read-only. It grants no authority, changes no role registration, changes no Steward authorization, and performs no reconciliation or admission.

## V1 activation artifact

V1 accepts one evidence method: `explicit_declaration`.

```json
{
  "contract": "reasoning-distiller-role-activation/1",
  "role_id": "steward:default",
  "method": "explicit_declaration",
  "context": {
    "invocation_id": "run-123",
    "source": "agent-session"
  }
}
```

Required fields are exact. `invocation_id` and `source` MUST be non-empty strings.

The artifact is canonicalized and digested using the R1 canonical JSON/digest rules.

`explicit_declaration` is an intentionally weak but explicit v1 evidence method. Future policy may add stronger typed methods such as platform attestations or signatures without changing durable role or authorization identity semantics.

## Validation

For requested authority scope `semantic_reconciliation` or `admission`, validation MUST prove all of the following:

1. the activation artifact conforms exactly to this contract;
2. the evidence method is accepted by the current package policy;
3. the role exists in the current role registry;
4. the role is currently `available`;
5. the requested scope is currently assigned;
6. the assigned role for that scope exactly equals `activation.role_id`;
7. role-registry and Steward-authorization projections do not conflict with authoritative replay.

Authorization alone is insufficient. A role-name match alone is insufficient. Activation evidence for one role cannot activate another role.

## Result semantics

Validation uses the common operation-result envelope.

Successful validation returns:

- `PASS/ACTIVATION_ACCEPTED`;
- requested `scope`;
- accepted `role_id`;
- canonical `activation_digest`;
- `invocation_id`.

Expected fail-closed outcomes include:

- `INVALID_ACTIVATION_EVIDENCE`;
- `UNSUPPORTED_ACTIVATION_METHOD`;
- `UNKNOWN_SCOPE`;
- `ROLE_NOT_FOUND`;
- `ROLE_UNAVAILABLE`;
- `SCOPE_UNASSIGNED`;
- `ROLE_NOT_AUTHORIZED_FOR_SCOPE`;
- role/authorization projection or history conflicts surfaced from lower primitives.

## Storage and mutation

This primitive MUST NOT persist activation evidence or mutate project state. The caller may retain the supplied artifact as invocation provenance. Any later domain primitive that relies on activation MUST receive or bind to the exact activation artifact/digest it validated.

## Conformance gate

R8 PASS requires tests proving:

1. valid explicit declaration for the currently authorized available role passes;
2. malformed evidence fails;
3. unknown evidence method fails;
4. unassigned scope fails;
5. activation role differing from authorized role fails;
6. unavailable authorized role fails rather than falling back;
7. reconciliation and admission scopes remain independent;
8. validation is deterministic and mutation-free;
9. conflicting role or authorization projection fails closed;
10. activation does not create or change authority.
