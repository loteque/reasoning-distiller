# R17 — Bounded Authority Grant Design Contract

Status: **Normative design contract — accepted; integration amendments pending**

Contract: `reasoning-distiller-authority-grant/1`

Depends on: accepted R1–R16B, including accepted durable workflow, provenance, and pre-approval proposal-revalidation contracts.

Implementation status: **not authorized by acceptance alone; implementation requires the integration amendments recorded below.**

## Purpose

This contract defines prospective, bounded human authority for autonomous RIL execution through immutable `authority-grant:<id>` artifacts.

The design goal is to reduce repeated proposal-specific human interruptions without granting agents independent authority or weakening materiality, protected-operation, or apply-time validation boundaries.

## Core invariant

The grant carries authority; the agent does not.

An exact proposal may receive grant-derived approval only when deterministic validation proves that the complete proposal falls within an active grant and every independent validity/materiality requirement is satisfied.

## Accepted design decisions

1. **Typed identity:** use `authority-grant:<id>`.
2. **Creation authority:** grant creation is an authenticated human operator act, not agent authority.
3. **Creation payload:** authentication binds the exact canonical grant definition.
4. **Creation ceremony:** exact payload preview plus explicit prospective-delegation confirmation is required.
5. **Initial scope:** grants are workflow-bound in v1 and MUST reference exactly one immutable `workflow:<id>`.
6. **Workflow compatibility:** grant scope MUST be a subset of the workflow's immutable bounded intent; the grant cannot expand workflow intent.
7. **Operation scope:** grant definitions use explicit allowlisted operation classes plus deterministic target/constraint predicates.
8. **No open-ended language:** free-form prose cannot itself define normative grant scope.
9. **Whole-proposal containment:** grant use requires proof that the entire exact proposal is within scope; partial containment fails.
10. **Deterministic validator:** scope matching is performed by a common RIL primitive, not agent judgment.
11. **Delegation model:** grants do not delegate authority to an agent identity; any conforming orchestrator may present an exact proposal for deterministic grant evaluation.
12. **No subdelegation:** an authority grant cannot create, expand, or delegate another authority grant.
13. **Non-delegable floor:** protected-root transfer, protected-root establishment/authority-policy changes, exceptional recovery authority, authority-grant creation/expansion, workflow scope revision, and other contract-designated protected operations remain non-delegable.
14. **Steward separation:** grants do not create or replace Steward authorization or activation.
15. **Materiality supremacy:** a materiality pause blocks grant-derived approval until valid acknowledgement; a grant cannot waive informed-intent preservation.
16. **D3 ordering:** every grant-derived approval uses immediately-before D3 proposal applicability revalidation.
17. **Apply validation:** apply-time primitive validation remains independently mandatory.
18. **Approval artifact:** successful grant consumption creates an ordinary exact `approval:<id>` whose authority basis identifies the `authority-grant:<id>` rather than fresh proposal-specific human assent.
19. **Exact proposal binding:** grant-derived approval binds exactly one immutable proposal.
20. **Atomic issuance:** grant-scope validation, grant availability/limit validation, grant consumption accounting, and approval creation are atomic with respect to grant normative state.
21. **Consumption point:** finite grant limits are consumed when grant-derived approval is issued, not when apply later succeeds.
22. **Retry semantics:** reuse of the same valid approval for a permitted retry does not consume a second grant unit; apply-time semantics remain authoritative.
23. **Lifecycle:** grant state is ACTIVE until REVOKED, EXHAUSTED, or the bound workflow becomes terminal; terminal ineligibility is irreversible for that grant identity.
24. **Revocation:** the grantor may revoke their grant directly; protected root may revoke any active grant. Revocation never reverses already completed operations.
25. **No normative wall-clock expiry in v1:** time expiry is not required until RIL has an accepted trusted-time authority model; deterministic count/state/workflow constraints are preferred.
26. **Immutable definition:** material scope changes require a new grant; existing grants are never edited in place.
27. **Grant history:** mutable lifecycle/consumption state is recorded through an append-only `authority-grant-event:<id>` normative event chain with an authoritative normative head.
28. **Concurrency:** grant-derived approval and revocation use exact expected normative-head/state bindings; stale races fail rather than auto-rebase.
29. **Inspection:** grants and grant events are canonical typed references inspectable through resource-specific and generic R16A-style inspection; deeper inspection exposes workflow binding, scope, consumption, approvals, and events.
30. **Peer-adapter parity:** CLI, Human↔Agent, and automation adapters use the same grant primitives; no grant semantic exists only conversationally.

## Grant definition

Conceptually:

```text
authority-grant:<id>
  grantor: operator:alice
  workflow: workflow:<id>
  scope:
    operations: [<operation-class-id>]
    targets: [<target-selector>]
    constraints: [<constraint>]
  limits:
    approvals: <optional finite count>
  exclusions:
    <contract-defined non-delegable classes>
  authentication:
    binds: hash(canonical grant payload)
```

The grant identity commits to both the exact scope and authenticated human act establishing that prospective authority.

## Structured scope vocabulary

R17 v1 defines a deliberately small common scope language. Individual operation contracts publish the exact operation classes, target fields, and constraint keys they support. Unsupported vocabulary fails closed.

### Operation classes

Every proposal type eligible for delegated approval SHALL expose one stable canonical `operation_class` identifier. The identifier is contract-defined and version-stable within the applicable protocol version.

A grant contains an explicit allowlist:

```text
scope:
  operations:
    - <operation-class-id>
```

Wildcards, prefix matching, free-form categories, and agent-inferred equivalence are not normative v1 scope semantics.

An operation class marked `delegable: false` by its defining primitive can never be authorized by a grant even if named in the grant payload.

### Target selectors

Target selectors are conjunctions over exact proposal fields whose semantics are published by the proposal's operation contract. V1 selectors MAY use only:

```text
exact     # field equals one canonical value/reference
one-of    # field equals one member of a finite canonical set
within    # field's canonical typed target is contained by a contract-defined parent target
```

`within` is valid only where the relevant target hierarchy is itself deterministic and contract-defined. No filesystem glob, regex, fuzzy matching, natural-language matching, or inferred project relationship is normative scope syntax unless a future accepted contract explicitly adds it.

Examples:

```text
targets:
  - field: candidate
    match: exact
    value: candidate:abc

  - field: resource
    match: one-of
    values: [resource:a, resource:b]
```

If a proposal exposes multiple authority-relevant targets, every such target must be covered by the grant. Unmentioned authority-relevant target dimensions fail closed rather than inheriting permission.

### Constraints

Constraints are typed predicates over canonical proposal fields. V1 common predicate forms are:

```text
eq
one-of
max-count
subset-of
```

Each operation contract declares which proposal fields accept which predicates and how canonical comparison is performed. A constraint key or predicate not explicitly published for that operation class is unsupported and therefore outside grant scope.

Constraints only narrow authority. They cannot transform a proposal, select a different target, or create a default value missing from the proposal.

### Containment algorithm

For an exact proposal P and grant G, the common validator succeeds only when all of the following are true:

1. G is ACTIVE and bound to the currently applicable workflow;
2. P belongs to an operation class explicitly allowed by G;
3. that operation class is contract-delegable;
4. every authority-relevant proposal target is covered by G's target selectors;
5. every applicable grant constraint evaluates true against P;
6. no proposal field introduces an authority-relevant effect not represented by the operation contract's published grant-matching schema;
7. the complete proposal lies within the bound workflow's immutable intent;
8. no contract-defined exclusion/non-delegable rule applies.

If any fact is unknown, unsupported, ambiguous, or partially covered, the result is `OUTSIDE_GRANT` and ordinary proposal-specific approval remains required.

The validator MUST NOT mutate or normalize a proposal into compliance.

## Workflow-bound authority

V1 grants are valid only in the context of one immutable workflow.

The grant validator MUST prove:

```text
grant scope ⊆ workflow bounded intent
```

and, for every proposed use:

```text
proposal ⊆ grant scope ⊆ workflow bounded intent
```

A workflow revision creates a new workflow identity; an existing grant bound to the predecessor does not migrate automatically.

When the bound workflow becomes COMPLETED, CANCELLED, or SUPERSEDED, the grant becomes permanently ineligible for new approval issuance.

## Grant-derived approval

The authority chain is:

```text
authenticated human act
        ↓
authority-grant:<id>
        ↓
exact proposal:<id>
        ↓
D3 applicability validation
        ↓
grant scope/limit validation
        ↓
materiality / workflow-boundary validation
        ↓
atomic grant consumption + approval creation
        ↓
approval:<id>
  proposal: proposal:<id>
  authority_basis: authority-grant:<id>
        ↓
independent apply-time validation
```

An agent/runtime is never the authority basis merely because it requested evaluation.

## Approval authority-basis extension

R17 extends the common approval model so an exact approval records one accepted authority basis.

At minimum the approval contract SHALL distinguish:

```text
authority_basis:
  kind: direct-operator
  authentication: <exact authenticated assent evidence>
```

or:

```text
authority_basis:
  kind: authority-grant
  grant: authority-grant:<id>
  grant_event: authority-grant-event:<approval-issued-event-id>
```

Both forms still bind the approval to exactly one immutable proposal.

The `authority-grant` form does not claim that a human reviewed the exact proposal at issuance time. It means a prior authenticated human act prospectively authorized that proposal class/target/effect and deterministic RIL validation proved exact containment at issuance time.

Consumers MUST NOT collapse the distinction between direct proposal-specific assent and grant-derived authority in audit or presentation.

## Grant event history

Grant definitions are immutable. Normative evolving state is represented by a linear append-only event chain:

```text
authority-grant-event:<id>
```

Core event classes SHALL include at least:

```text
core/approval-issued
core/revoked
core/exhausted
```

`core/approval-issued` binds the exact proposal, resulting approval, and prior expected grant normative head. `core/revoked` records authenticated revocation. `core/exhausted` may be deterministically sealed when finite capacity is consumed.

The grant primitive owns normative event creation and head advancement.

## Lifecycle and eligibility

Projected grant state includes:

```text
ACTIVE
REVOKED
EXHAUSTED
WORKFLOW_TERMINAL
```

Only ACTIVE grants may issue new grant-derived approvals.

Workflow-terminal ineligibility may be derived from the authoritative bound workflow rather than duplicated as a grant event; once the bound workflow is terminal, grant eligibility cannot return.

## Scope validation result

The common grant validator returns one of:

```text
WITHIN_GRANT
OUTSIDE_GRANT
GRANT_INACTIVE
GRANT_EXHAUSTED
WORKFLOW_MISMATCH
NON_DELEGABLE
INVALID
```

Only `WITHIN_GRANT` permits grant-derived approval issuance to proceed to the remaining mandatory checks.

These classifications are deterministic protocol state, not shell exit-code taxonomy.

## Non-delegable authority

At minimum, v1 SHALL classify the following as non-delegable through `authority-grant`:

- creation, expansion, or transfer of authority grants;
- protected-root establishment or transfer;
- changes to protected authority/governance policy;
- exceptional recovery requiring protected ceremony;
- workflow revision/scope expansion;
- any operation explicitly marked non-delegable by its normative primitive contract.

Revocation is not delegated authority expansion and remains directly available to the grantor and protected root.

## Materiality

A technically in-scope proposal MUST NOT receive grant-derived approval while the workflow is in `MATERIALITY_PAUSE` or when the accepted materiality mechanism determines that newly surfaced information requires human acknowledgement.

This preserves the distinction between prior authority and current informed intent.

## Interaction with D3

D3 remains mandatory. A grant does not freeze proposal applicability.

A proposal must be `APPLICABLE` immediately before grant-derived approval issuance. `STALE`, `BLOCKED`, or `INVALID` prevents issuance.

D3 and grant validation answer different questions:

```text
D3: Is this exact proposal still applicable?
Grant: Is this exact proposal prospectively authorized?
Materiality: Does informed human intent still hold?
Apply: Is this exact mutation valid now?
```

## Revocation and races

Revocation and grant-derived approval issuance race against exact grant normative state.

If revocation wins, later issuance fails. If a valid approval issuance wins first, later revocation prevents future issuance but does not erase the already-issued approval or reverse completed effects. Any separate approval invalidation semantics remain governed by the approval contract.

The adapter MUST report the actual race outcome rather than pretending revocation rewrote history.

## CLI integration contract

R16A SHALL gain the first-class resource family:

```text
ril authority-grant
ril authority-grant list
ril authority-grant show <authority-grant> [--depth=<supported-depth>]
ril authority-grant create [<file|->] [--auth <file|->]
ril authority-grant revoke <authority-grant> [--auth <file|->]
```

Bare `ril authority-grant` is a read-only dashboard showing active grants, bound workflows, remaining finite capacity where applicable, and current actionability.

There is no `update`; scope changes create a new immutable grant.

Creation accepts one canonical structured grant-definition format via file, stdin, or guided interactive construction. Interactive construction is not a second scope language. Before creation, RIL displays the exact canonical grant definition, authenticates the grantor's assent to that definition, and separately makes prospective delegated approval consequences conspicuous.

Requester revocation uses ordinary explicit confirmation. Protected-root revocation of another operator's grant uses the stronger exact-reference override ceremony. Revocation is exact-state and does not silently retry over intervening grant consumption.

Grant events are inspectable through generic typed-reference inspection and may also be surfaced by depth-expanded grant inspection.

## Human↔Agent integration contract

R16B auto-advance orchestration SHALL evaluate applicable active authority grants before returning `AWAITING_APPROVAL` for an ordinary delegable proposal.

For each candidate grant, the adapter/orchestrator uses the common deterministic grant validator. If exactly one applicable authority path is established, it may issue grant-derived approval and continue without fresh proposal-specific human assent.

If no grant covers the proposal, normal proposal-specific approval is required. If multiple grants could cover the proposal, the deterministic orchestration layer MAY choose among them only when the choice cannot alter authority scope, consumption semantics, or audit meaning; otherwise it MUST surface the ambiguity rather than allowing the agent to choose authority strategically.

Grant use never bypasses D3, materiality, Steward activation, workflow scope, apply-time validation, or non-delegable-operation rules.

Control-return output MUST distinguish direct human approval from grant-derived approval and identify the consumed `authority-grant:<id>` where material.

## Automation consequence

With a valid auto-advance workflow and active authority grant, ordinary proposal-governed mutations need not interrupt the human merely to obtain proposal-specific assent.

Human interruption remains required when:

1. material information requires acknowledgement;
2. desired action exceeds immutable workflow/grant scope;
3. a non-delegable protected operation is reached;
4. machine-state blockers cannot be resolved without crossing one of those human boundaries.

This reduces ordinary approval from a fundamental human boundary to a deterministic scope check.

## Reconciliation findings

The focused acceptance review resolved both previously open design questions:

1. **Approval authority basis:** accepted as the explicit `direct-operator` versus `authority-grant` union defined above. Grant-derived approval remains an exact ordinary approval artifact and does not grant agents authority.
2. **Structured scope vocabulary:** accepted as a fail-closed operation-class + target-selector + typed-constraint language whose concrete fields/predicates are published by each delegable operation contract.

Reconciliation against accepted R1–R16B: **SEMANTIC PASS; CROSS-CONTRACT INTEGRATION AMENDMENTS REQUIRED.**

No contradiction was found with exact proposal identity, D3 pre-approval revalidation, proposal/approval/apply separation, apply-time validation, workflow immutable intent, materiality, Steward activation, protected-root ceremony, provenance non-authority, or Canon boundaries.

Required integration amendments are:

- **R17-I1 — approval primitive/artifact:** incorporate the accepted `authority_basis` union and atomic grant-derived issuance path.
- **R17-I2 — operation contracts:** every operation intended to be grant-delegable publishes `operation_class`, `delegable`, authority-relevant target fields, and supported scope predicates; unamended operations remain non-delegable by default.
- **R17-I3 — R16A:** incorporate the `ril authority-grant` peer-adapter family and grant inspection/reference semantics.
- **R17-I4 — R16B:** incorporate grant evaluation into bounded auto-advance before ordinary `AWAITING_APPROVAL`, while retaining all existing interruption and validation boundaries.

These are integration work, not unresolved R17 design questions.

## Acceptance status

R17 is **ACCEPTED / INTEGRATION-PENDING R17-I1..I4**.

Implementation SHALL NOT treat authority grants as available until the required approval, operation-contract, CLI, and Human↔Agent integration amendments are accepted and reconciled.
