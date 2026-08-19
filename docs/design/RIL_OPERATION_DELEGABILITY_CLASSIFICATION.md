# R18 — Operation Delegability Classification

Status: **Normative design contract — accepted and integrated**

Contract: `reasoning-distiller-operation-delegability/1`

Depends on: accepted R1–R17, including `reasoning-distiller-authority-grant/1`.

Implementation status: **not authorized by acceptance alone; implementation/conformance must satisfy the gates below.**

## Purpose

R18 classifies existing RIL operations by whether prospective authority carried by `authority-grant:<id>` may satisfy proposal-specific approval requirements.

R18 does not create new authority. It determines where the already-accepted R17 authority-grant mechanism may be used and where direct/protected human ceremony remains mandatory.

## Classification vocabulary

Each operation is classified as one of:

```text
DELEGABLE
NON_DELEGABLE
NOT_APPLICABLE
DEFERRED
```

- `DELEGABLE` — an operation contract publishes deterministic grant-matching semantics and permits grant-derived approval.
- `NON_DELEGABLE` — grant-derived approval is forbidden; the operation retains direct/protected human ceremony.
- `NOT_APPLICABLE` — the operation is not proposal-approval-gated and therefore does not consume authority-grant approval authority.
- `DEFERRED` — no safe complete v1 grant-matching vocabulary is accepted yet; operation remains non-delegable until separately amended.

Absent an explicit accepted `DELEGABLE` declaration, fail closed as non-delegable.

## Classification principles

1. Authority grants may automate ordinary bounded mutation; they must not automate creation or expansion of the authority system that governs grants themselves.
2. Operations that create, transfer, restore, or expand core RIL administrative authority are non-delegable by default.
3. Operations that only reduce existing ordinary administrative authority may be delegable when exact targets/effects are mechanically bounded.
4. Semantic Steward authorization remains distinct from workflow/approval delegation and is non-delegable in v1.
5. Protected-root establishment/transfer and exceptional recovery remain explicit human ceremonies.
6. Deterministic reconstruction of derived state is not an authority decision and does not use grants.
7. Role-registry mutation remains delegable because project role registration itself grants no Steward/reconciliation/admission authority and consumer roles cannot claim `rd:*` capabilities.
8. Every delegable operation must publish a complete authority-relevant target/effect schema; unknown effects fail closed.
9. Materiality, D3, workflow scope, apply-time validation, and all R17 exclusions remain mandatory for every grant-derived approval.

## Accepted existing-operation matrix

| Domain / operation | Classification | Normative result |
|---|---|---|
| `role_registry` ordinary ADD/UPDATE/DISABLE/REENABLE | **DELEGABLE** | Preserve accepted `role-registry.change`; exact role IDs and mutation classes are scope-matchable and role registration alone creates no core RIL authority. |
| `operator_registry` `ADD_OPERATOR` | **NON_DELEGABLE** | Creates a new durable human administrative identity and potential future authority holder. |
| `operator_registry` `UPDATE_CAPABILITIES` | **DEFERRED** | Full replacement can reduce and expand authority. No grant use until an accepted authority-non-increasing predicate exists. |
| `operator_registry` `DISABLE_OPERATOR` | **DELEGABLE** | Exact non-root operator disable may use grant-derived approval. |
| `operator_registry` `REENABLE_OPERATOR` | **NON_DELEGABLE** | Restores administrative actionability. |
| `operator_registry` `INITIALIZE_ROOT` | **NON_DELEGABLE** | Foundational protected-root ceremony. |
| `operator_registry` `TRANSFER_ROOT` | **NON_DELEGABLE** | Protected-root transfer remains a stronger direct-root ceremony. |
| `steward_authorization` `AUTHORIZE` | **NON_DELEGABLE** | Creates semantic reconciliation/admission authority assignment. |
| `steward_authorization` `REASSIGN` | **NON_DELEGABLE** | Transfers semantic Steward authority. |
| `steward_authorization` `REVOKE` | **NON_DELEGABLE** | Steward governance remains entirely direct-human in v1 for audit clarity. |
| ordinary repair of derived projections | **NOT_APPLICABLE** | Deterministic and approval-free. |
| exceptional recovery | **NON_DELEGABLE** | Explicit protected-root recovery ceremony over damaged authoritative history. |
| authority-grant creation / expansion | **NON_DELEGABLE** | R17 non-subdelegation floor. |
| authority-grant revocation by grantor/root | **NOT_APPLICABLE** | Direct safety/control operation; grants cannot authorize grant lifecycle authority. |
| workflow creation with authenticated bounded intent | **NON_DELEGABLE** | Establishes durable human intent and prospective automation consent. |
| workflow revision / scope expansion | **NON_DELEGABLE** | Creates materially new bounded intent. |
| workflow cancellation | **DEFERRED** | May destroy remaining intent; workflow-control delegation is not accepted yet. |
| workflow materiality acknowledgement | **NON_DELEGABLE** | Exists specifically to restore informed human intent. |
| reconciliation invocation | **NOT_APPLICABLE** | Authority is Steward authorization + activation, not proposal approval. |
| admission invocation | **NOT_APPLICABLE** | Authority is admission Steward authorization + activation. |
| storage/Canon verification | **NOT_APPLICABLE** | Read-only verification. |

## Operator-disable grant schema

R18 accepts the second grant-delegable operation class:

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

Grant matching MUST additionally prove from authoritative current state that every selected target is not the protected root. A grant cannot convert a protected-root target into an ordinary target.

No wildcard, prefix, fuzzy, inferred, or natural-language operator selection is normative v1 grant scope.

The authoritative operator-management contract publishes the same metadata and owns operation-specific enforcement.

## Deferred operator capability updates

`UPDATE_CAPABILITIES` is deliberately not blanket-delegable because its full-replacement semantics can both reduce and expand authority.

A future amendment MAY make a strictly authority-non-increasing subset delegable if a deterministic predicate is accepted, conceptually:

```text
new_rd_capabilities ⊆ current_rd_capabilities
```

and if project-defined capabilities are independently classified for authority significance. Until then, all `UPDATE_CAPABILITIES` proposals remain outside grants.

## Steward authorization policy

The entire `steward_authorization` domain remains non-delegable in v1, including revocation.

The domain determines who may exercise semantic reconciliation/admission authority. Keeping assignment and revocation under one direct-human governance rule preserves audit clarity and prevents grants from becoming an indirect mechanism for shaping semantic authority topology.

## Role registry policy

The existing R17 delegability amendment remains valid:

```text
operation_class: role-registry.change
delegable: true
```

Grant matching must cover every affected role ID and every mutation class, and proposal role definitions remain subject to the role-registry prohibition on consumer `rd:*` capabilities and protocol-governance roles.

A grant never turns role registration into Steward authorization.

## R17 delegable-operation registry extension

R18 normatively extends the accepted R17 delegable-operation registry. The accepted v1 registry is now:

```text
role-registry.change
operator-registry.disable
```

This section is the accepted R18-I2 amendment to `reasoning-distiller-authority-grant/1`. R17's default remains fail-closed: operations not explicitly present through an accepted operation contract/amendment are non-delegable.

No R17 authority semantics are otherwise changed.

## Non-proposal operations

R18 distinguishes automation from delegation.

An operation such as ordinary repair, reconciliation, admission, or verification may run automatically when its own accepted prerequisites/authority are satisfied even though it does not use `authority-grant` at all.

`NOT_APPLICABLE` therefore does not mean "requires a human". It means R17 proposal-derived approval authority is not the governing mechanism.

## Practical automation ceiling after R18

Under this classification, an auto-advance workflow can autonomously:

- inspect, diagnose, verify, and prepare proposals;
- perform ordinary deterministic repair;
- execute reconciliation/admission when independently valid Steward activation exists;
- consume grants for accepted role-registry changes;
- consume grants for exact ordinary non-root operator disable operations;
- continue through ordinary machine-resolvable boundaries.

It still returns to a human for:

- new or restored administrative identity/authority;
- Steward authority topology changes;
- protected-root establishment/transfer;
- exceptional recovery;
- workflow creation/revision/materiality acknowledgement;
- operations outside accepted grant scope;
- materiality or other preserved R16/R17 human boundaries.

## Conformance requirements

R18 conformance SHALL prove at minimum:

1. `operator-registry.disable` is recognized as delegable only through its published exact schema;
2. a valid workflow-bound grant can authorize exact non-root `DISABLE_OPERATOR` proposals;
3. a grant can never disable the protected root;
4. exact and finite `one-of` target selectors are enforced;
5. target mismatch fails `OUTSIDE_GRANT` rather than broadening scope;
6. grants cannot authorize `ADD_OPERATOR`;
7. grants cannot authorize `REENABLE_OPERATOR`;
8. grants cannot authorize `TRANSFER_ROOT` or `INITIALIZE_ROOT`;
9. grants cannot authorize `UPDATE_CAPABILITIES` while classification is `DEFERRED`;
10. Steward authorization changes remain non-delegable;
11. exceptional recovery remains non-delegable;
12. authority-grant creation/expansion remains non-delegable;
13. workflow revision/materiality acknowledgement remain non-delegable;
14. grant-derived operator disable still enforces D3, workflow containment, materiality, grant state/limits, exact approval binding, atomic consumption, and apply-time validation;
15. unclassified/unamended operation classes fail closed as non-delegable.

The amended operator-management contract incorporates these operation-specific conformance obligations.

## Reconciliation

Final reconciliation against accepted R1–R17 and the amended R5 operator-management contract: **PASS.**

The classification does not weaken protected-root ceremony, Steward authorization/activation separation, role-registry restrictions, exceptional recovery, D3, materiality, workflow scope, or apply-time validation.

The key conservative boundary remains: authority-creating/restoring operations are human-bound while deterministic ordinary role mutation and exact authority-reducing non-root operator disable may use prospective bounded grants.

## Integration resolution

- **R18-I1 — operator management:** **RESOLVED** by the R5 amendment publishing `operator-registry.disable` as delegable and explicit non/deferred metadata for sibling operations.
- **R18-I2 — R17 registry:** **RESOLVED** by this accepted normative registry extension adding `operator-registry.disable` alongside `role-registry.change`.
- **R18-I3 — conformance:** **RESOLVED at contract level** by the explicit conformance requirements here and in amended R5. Executable tests remain implementation/conformance work.

## Acceptance status

R18 is **ACCEPTED AND INTEGRATED**.

Implementation SHALL preserve the accepted classification and must not infer delegation for any operation not explicitly accepted as `DELEGABLE`.
