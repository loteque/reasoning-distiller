# R18 — Operation Delegability Classification

Status: **Draft normative design contract — designer recommendation complete; awaiting acceptance**

Contract: `reasoning-distiller-operation-delegability/1`

Depends on: accepted R1–R17, including `reasoning-distiller-authority-grant/1`.

Implementation status: **not authorized by this draft.**

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

- `DELEGABLE` — an operation contract may publish deterministic grant-matching semantics and permit grant-derived approval.
- `NON_DELEGABLE` — grant-derived approval is forbidden; the operation retains direct/protected human ceremony.
- `NOT_APPLICABLE` — the operation is not proposal-approval-gated and therefore does not consume authority-grant approval authority.
- `DEFERRED` — no safe complete v1 grant-matching vocabulary is accepted yet; operation remains non-delegable until separately amended.

Absent an explicit accepted `DELEGABLE` declaration, fail closed as non-delegable.

## Classification principles

The designer review applies these rules:

1. Authority grants may automate ordinary bounded mutation; they must not automate creation or expansion of the authority system that governs grants themselves.
2. Operations that create, transfer, restore, or expand core RIL administrative authority are non-delegable by default.
3. Operations that only reduce existing ordinary administrative authority may be delegable when exact targets/effects are mechanically bounded.
4. Semantic Steward authorization remains distinct from workflow/approval delegation and is non-delegable in v1.
5. Protected-root establishment/transfer and exceptional recovery remain explicit human ceremonies.
6. Deterministic reconstruction of derived state is not an authority decision and does not use grants.
7. Role-registry mutation remains delegable because project role registration itself grants no Steward/reconciliation/admission authority and consumer roles cannot claim `rd:*` capabilities.
8. Every delegable operation must publish a complete authority-relevant target/effect schema; unknown effects fail closed.
9. Materiality, D3, workflow scope, apply-time validation, and all R17 exclusions remain mandatory for every grant-derived approval.

## Existing-operation matrix

| Domain / operation | Classification | Recommendation |
|---|---|---|
| `role_registry` ordinary ADD/UPDATE/DISABLE/REENABLE | **DELEGABLE** | Preserve accepted `role-registry.change`; exact role IDs and mutation classes are scope-matchable and role registration alone creates no core RIL authority. |
| `operator_registry` `ADD_OPERATOR` | **NON_DELEGABLE** | Creates a new durable human administrative identity and may establish future authority-bearing capability holders. |
| `operator_registry` `UPDATE_CAPABILITIES` | **DEFERRED** | Could safely automate authority-reducing subsets, but replacement semantics can also expand core authority. Requires a future monotonic-authority predicate before opt-in. |
| `operator_registry` `DISABLE_OPERATOR` | **DELEGABLE** | Reduces/removes actionability of one exact non-root operator without creating or expanding authority. |
| `operator_registry` `REENABLE_OPERATOR` | **NON_DELEGABLE** | Restores the operator's existing administrative capabilities and therefore restores authority/actionability. |
| `operator_registry` `INITIALIZE_ROOT` | **NON_DELEGABLE** | Establishes the protected root and fixed core capabilities; explicit human ceremony is foundational. |
| `operator_registry` `TRANSFER_ROOT` | **NON_DELEGABLE** | Protected-root authority transfer remains a stronger direct-root ceremony. |
| `steward_authorization` `AUTHORIZE` | **NON_DELEGABLE** | Creates semantic reconciliation/admission authority assignment. |
| `steward_authorization` `REASSIGN` | **NON_DELEGABLE** | Transfers semantic Steward authority between roles. |
| `steward_authorization` `REVOKE` | **NON_DELEGABLE** | Although authority-reducing, semantic Steward governance is kept entirely outside grant-derived approval in v1 for conceptual simplicity and audit clarity. |
| ordinary repair of derived projections | **NOT_APPLICABLE** | Already deterministic and approval-free; valid authoritative history determines the exact result. |
| exceptional recovery | **NON_DELEGABLE** | Explicit protected-root human recovery ceremony over damaged authoritative history. |
| authority-grant creation / expansion | **NON_DELEGABLE** | R17 non-subdelegation floor. |
| authority-grant revocation by grantor/root | **NOT_APPLICABLE to delegated approval** | Direct revocation is a safety/control operation; a grant cannot authorize its own or another grant's lifecycle authority. |
| workflow creation with authenticated bounded intent | **NON_DELEGABLE** | Establishes durable human intent and, for auto-advance, prospective automation consent. |
| workflow revision / scope expansion | **NON_DELEGABLE** | Creates materially new bounded intent; R17 already forbids delegation. |
| workflow cancellation | **DEFERRED** | Cancellation does not expand work but may destroy remaining intent. Keep direct requester/root control until workflow-control delegation is separately designed. |
| workflow materiality acknowledgement | **NON_DELEGABLE** | Exists specifically to restore informed human intent after material information surfaced. |
| reconciliation invocation | **NOT_APPLICABLE** | Authority comes from valid Steward authorization + activation, not proposal-specific operator approval. |
| admission invocation | **NOT_APPLICABLE** | Authority comes from valid admission Steward authorization + activation, not proposal-specific operator approval. |
| storage/Canon verification | **NOT_APPLICABLE** | Read-only verification, not proposal-governed mutation. |

## Operator-disable grant schema

R18 recommends the first additional delegable operation class:

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

Grant matching MUST additionally prove from authoritative current state that the target is not the protected root. A grant cannot convert a protected-root target into an ordinary target.

No wildcard/prefix/fuzzy operator selection is normative v1 grant scope.

## Deferred operator capability updates

`UPDATE_CAPABILITIES` is deliberately not blanket-delegable because its full-replacement semantics can both reduce and expand authority.

A future amendment MAY make a strictly authority-non-increasing subset delegable if a deterministic predicate is accepted, conceptually:

```text
new_rd_capabilities ⊆ current_rd_capabilities
```

and if project-defined capabilities are independently classified for authority significance. Until then, all `UPDATE_CAPABILITIES` proposals remain outside grants.

This avoids an apparent "remove one capability" grant accidentally authorizing a replacement set that adds a different capability.

## Steward authorization policy

R18 keeps the entire `steward_authorization` domain non-delegable in v1, including revocation.

Designer rationale: the domain determines who may exercise semantic reconciliation/admission authority. Keeping assignment and revocation under one direct-human governance rule is easier to audit and prevents grants from becoming an indirect mechanism for shaping semantic authority topology.

This can be revisited later if operational experience demonstrates a strong need for emergency automated revocation.

## Role registry policy

The existing R17 delegability amendment remains valid:

```text
operation_class: role-registry.change
delegable: true
```

Grant matching must cover every affected role ID and every mutation class, and proposal role definitions remain subject to the role-registry prohibition on consumer `rd:*` capabilities and protocol-governance roles.

A grant never turns role registration into Steward authorization.

## Non-proposal operations

R18 explicitly distinguishes automation from delegation.

An operation such as ordinary repair, reconciliation, admission, or verification may run automatically when its own accepted prerequisites/authority are satisfied even though it does not use `authority-grant` at all.

Therefore `NOT_APPLICABLE` does not mean "requires a human". It means R17 proposal-derived approval authority is not the governing mechanism.

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

## Integration amendments required if accepted

- **R18-I1 — operator management:** split/publish stable operation-class metadata so `operator-registry.disable` is `delegable: true`; keep ADD/REENABLE/TRANSFER non-delegable and UPDATE_CAPABILITIES deferred.
- **R18-I2 — R17 registry:** record `operator-registry.disable` as the second accepted delegable operation class and preserve unamended-default non-delegability.
- **R18-I3 — conformance:** add tests proving grants cannot target protected root, cannot authorize ADD/REENABLE/TRANSFER/UPDATE_CAPABILITIES, and exact/finite operator-target scope is enforced.

No R16A topology change is required because authority-grant evaluation is already generic and operator management commands already exist.

## Reconciliation

Designer reconciliation against accepted R1–R17: **SEMANTIC PASS.**

The classification does not weaken protected-root ceremony, Steward authorization/activation separation, role-registry restrictions, exceptional recovery, D3, materiality, workflow scope, or apply-time validation.

The key conservative choice is that authority-creating/restoring operations remain human-bound while deterministic ordinary role mutation and exact authority-reducing operator disable may use prospective bounded grants.

## Acceptance gate

R18 is **DESIGNER-COMPLETE / AWAITING ACCEPTANCE**.

Acceptance authorizes the three integration amendments above, not implementation by itself.
