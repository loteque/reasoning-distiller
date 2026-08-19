# R17 — Bounded Authority Grant Design Contract

Status: **Draft normative design contract — designer recommendation complete; awaiting acceptance**

Contract: `reasoning-distiller-authority-grant/1`

Depends on: accepted R1–R16B, including accepted durable workflow, provenance, and pre-approval proposal-revalidation contracts.

Implementation status: **not authorized by this draft.**

## Purpose

This contract defines prospective, bounded human authority for autonomous RIL execution through immutable `authority-grant:<id>` artifacts.

The design goal is to reduce repeated proposal-specific human interruptions without granting agents independent authority or weakening materiality, protected-operation, or apply-time validation boundaries.

## Core invariant

The grant carries authority; the agent does not.

An exact proposal may receive grant-derived approval only when deterministic validation proves that the complete proposal falls within an active grant and every independent validity/materiality requirement is satisfied.

## Designer survey decisions

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
    operations: [<allowlisted operation classes>]
    targets: <deterministic constraints>
    constraints: <deterministic bounded predicates>
  limits:
    approvals: <optional finite count>
  exclusions:
    <contract-defined non-delegable classes>
  authentication:
    binds: hash(canonical grant payload)
```

The grant identity commits to both the exact scope and authenticated human act establishing that prospective authority.

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

## Scope language

Grant scope MUST use deterministic structured fields defined by accepted operation contracts. It MUST NOT rely on an agent deciding whether a proposal is "close enough" to natural-language intent.

The validator is fail-closed:

- unknown operation class → outside grant;
- unknown target semantics → outside grant;
- unsupported constraint → outside grant;
- partially covered proposal → outside grant;
- ambiguous scope → outside grant.

The correct outcome is then ordinary `APPROVAL_REQUIRED`, not guessed delegation.

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

## CLI integration recommendation

A first-class resource is recommended:

```text
ril authority-grant
ril authority-grant list
ril authority-grant show <authority-grant> [--depth=<supported-depth>]
ril authority-grant create [<file|->] [--auth <file|->]
ril authority-grant revoke <authority-grant> [--auth <file|->]
```

Bare `ril authority-grant` is a read-only dashboard showing active grants, bound workflows, remaining finite capacity where applicable, and current actionability.

There is no `update`; scope changes create a new immutable grant.

Grant events are inspectable through generic typed-reference inspection and may also be surfaced by depth-expanded grant inspection.

## Automation consequence

With a valid auto-advance workflow and active authority grant, ordinary proposal-governed mutations need not interrupt the human merely to obtain proposal-specific assent.

Human interruption remains required when:

1. material information requires acknowledgement;
2. desired action exceeds immutable workflow/grant scope;
3. a non-delegable protected operation is reached;
4. machine-state blockers cannot be resolved without crossing one of those human boundaries.

This reduces ordinary approval from a fundamental human boundary to a deterministic scope check.

## Reconciliation findings

Designer reconciliation against accepted R1–R16B finds the model **semantically compatible in principle** with the existing authority architecture, provided approval semantics are amended to recognize `authority-grant:<id>` as an alternate human-derived authority basis for an exact approval artifact.

The primary integration changes required before acceptance are:

- extend the approval artifact/primitive contract with `authority_basis: authority-grant:<id>` and deterministic grant-derived issuance;
- add shared authority-grant primitive/artifact/event semantics;
- add peer-adapter surfaces, including the recommended R16A CLI family;
- update R16B auto-advance semantics to consume valid grants without fresh proposal-specific assent while retaining D3/materiality/apply checks;
- define the exact structured operation/target constraint vocabulary accepted by grant scope matching.

No recommendation permits agents to become independent authority holders.

## Acceptance gate

This R17 draft is **designer-complete but not yet accepted**. Acceptance should follow focused review of the integration changes above, especially the structured scope vocabulary and the extension of approval authority basis.
