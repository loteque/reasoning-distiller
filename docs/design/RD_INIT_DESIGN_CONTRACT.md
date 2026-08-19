# rd_init Design Contract

Status: **Normative design-phase contract**

Contract: `reasoning-distiller-rd-init-design/1`

## Purpose

This contract governs the design phase for `rd_init`, the future orchestration interface for Reasoning Distiller project setup and lifecycle coordination.

It defines fixed invariants, open design questions, required design outputs, and acceptance gates. It deliberately does **not** settle every implementation detail in advance.

The design phase must resolve open questions before implementation authority is granted.

## Core principle

> **Primitives first; UX later.**

`rd_init` is an orchestration state machine over stable, deterministic primitives. It is not where primitive semantics, authority, protocol rules, or project truth are defined.

Every state-changing capability used by `rd_init` must first exist as an independently specified, tested, and passing primitive.

## Target UX adapters

The primitive substrate must support two future UX workflows without changing semantics:

```text
                    deterministic primitives
                             │
              ┌──────────────┴──────────────┐
              │                             │
        Unix-like CLI                 Human ↔ Agent
        noninteractive +              guided interaction
        composable commands           over same contracts
```

No semantic operation may exist only as conversational behavior or only as a TTY interaction.

## Fixed invariants

The design phase MUST preserve the following invariants unless explicitly superseded by an upstream governance decision outside this design phase.

### Authority

1. `rd_init` has no semantic-reconciliation authority.
2. `rd_init` has no admission authority.
3. The Distiller has candidate-production authority only; it does not reconcile or admit.
4. Steward authority is project-owned and must be explicitly granted by an authorized human/operator action.
5. Role registration does not grant authority.
6. Role authorization does not prove that a current invocation is acting as that role.
7. Authorization must be revocable and reassignable without rewriting history.

### Protocol ownership

1. RGP, PEMS, and COVE are normative package-owned contracts.
2. Consuming projects may not fork, mutate, replace, supersede, or reinterpret normative RGP/PEMS/COVE contracts, schemas, or generic validators.
3. Consumer-side Architect or RGP Engineer capabilities that govern those normative contracts are forbidden.
4. Projects may implement policies, adapters, and protocol layers **above** RGP/PEMS/COVE only when they conform to the accepted package contracts.
5. Protocol evolution occurs upstream in the generic Reasoning Distiller repository through explicit review/versioning/release.

### Distribution and locality

1. Installed projects operate from `.reasoning-distiller/` and project-owned state.
2. Runtime operation must not depend on a live checkout of the generic repository.
3. Version/update pathways may reference the generic repository or accepted release metadata, but ordinary project execution must remain local except for explicit model/provider transport.

### State and evidence

1. Project evidence is explicit; orchestration must not silently broaden a Distiller evidence set.
2. Operational provenance is not canonical project knowledge.
3. PEMS/COVE admission must remain distinct from candidate production and reconciliation.
4. Unknown or conflicting state fails closed rather than being silently repaired.

## Primitive dependency rule

`rd_init` may orchestrate only primitives whose contracts and conformance gates are accepted.

Expected primitive families include, but are not limited to:

```text
installation
project bootstrap
role registry
Steward authorization
status/state inspection
evidence preparation/validation
invocation preparation
rd-distill
Steward reconciliation
admission handoff/admission
PEMS/COVE storage verification
```

A missing primitive is a design/implementation gap. It must not be hidden inside `rd_init` as ad hoc logic.

## Role-registry direction

The project role registry is project-owned state.

The initial design direction is:

- one package-provided default Steward role is available in the project registry;
- an operating entity may submit active chat/project roles for addition to the registry;
- submitted roles carry no authority merely by being registered;
- a deterministic role-registry primitive manages available role identities;
- ordinary role removal should preserve audit history, favoring disable/reenable over destructive deletion;
- disabling the currently authorized Steward must not silently transfer authority.

The design phase must specify exact contracts, identities, conflict rules, and lifecycle semantics before implementation.

## Steward-authorization direction

Steward authorization must be modeled separately from role registration.

The system must support, at minimum:

```text
AUTHORIZE(role_id, scopes)
REASSIGN(role_id, scopes)
REVOKE
```

`semantic_reconciliation` and `admission` are distinct scopes and must not be conflated by default.

The user/operator must be able to reject authorization entirely, leaving the project with no currently authorized Steward.

Authorization history should be durable and auditable; current authorization may be a deterministic projection of append-only authorization events.

## rd_init orchestration boundary

`rd_init` may:

- inspect local project/install state;
- classify lifecycle state;
- identify the next required primitive;
- present available safe actions;
- invoke bounded primitives after required inputs/authorizations are satisfied;
- surface machine-readable status and diagnostics;
- coordinate the Unix-like CLI and human-to-agent UX adapters over the same primitive contracts.

`rd_init` must not:

- absorb primitive semantics into orchestration code;
- grant or infer project authority;
- mutate normative protocols;
- invent evidence or project facts;
- silently choose a Steward;
- silently admit candidate knowledge;
- treat structural validity as semantic acceptance;
- hide undefined states behind UX defaults.

## Candidate lifecycle model

The design phase should evaluate and refine a lifecycle similar to:

```text
UNINSTALLED
  ↓
INSTALLED
  ↓
INITIALIZED
  ↓
EVIDENCE_READY
  ↓
CANDIDATE_READY
  ↓
RECONCILIATION_REQUIRED
  ↓
RECONCILED
  ↓
ADMISSION_READY
  ↓
ADMITTED
  ↓
READY
```

Blocked, conflicted, unavailable-authority, incompatible-version, and recovery states must also be designed explicitly.

The lifecycle model is not accepted merely because it appears here; it is an open design subject constrained by the fixed invariants.

## Open design questions

The Reasoning Distiller Designer must resolve at least the following before implementation of upper-layer orchestration:

1. Exact lifecycle/state-machine states, transitions, blocked states, and recovery semantics.
2. Exact scope of safe automatic actions versus actions requiring explicit operator confirmation.
3. Role-registry contract, stable identity scheme, submission format, append/update/disable/reenable semantics, and conflict handling.
4. Default Steward registry-entry semantics and how package upgrades affect it.
5. Steward authorization event contract, current-state projection, reassign/revoke behavior, and unavailable-target handling.
6. Invocation authentication/identity check proving that an acting role corresponds to an authorized registry target.
7. Whether reconciliation and admission authorities may be held by different registered roles and how handoff works when they are split.
8. Steward reconciliation primitive inputs, outputs, allowed semantic transformations, conflict behavior, and durable disposition format.
9. Admission primitive/handoff contract and the exact distinction between `RECONCILED`, `ADMISSION_READY`, and `ADMITTED`.
10. Evidence-readiness semantics: what may be discovered, enumerated, validated, or selected automatically without broadening the evidence boundary.
11. Machine-readable status/result contracts suitable for both Unix pipelines and human-to-agent mediation.
12. Recovery and migration behavior when installed package versions, project contracts, registry state, or authorization projections differ.
13. Extension-policy boundary for project-defined layers above RGP/PEMS/COVE and how conformance is asserted.
14. Which current generic agent roles should ship in consuming packages versus remain upstream-only governance roles.
15. Exact CLI command topology and agent-mediated interaction semantics, after primitives are complete.

The Designer may add additional questions when they are required to close an implementation ambiguity.

## Required design outputs

The design phase must produce implementation-ready artifacts covering:

- lifecycle/state-machine specification;
- primitive inventory and dependency graph;
- role-registry contract;
- Steward authorization contract;
- reconciliation contract;
- admission boundary contract;
- state/status inspection contract;
- error/conflict/recovery taxonomy;
- protocol-extension/conformance policy;
- compatibility/versioning rules;
- security/authority invariants;
- conformance-test plan for each primitive;
- Unix-like CLI composition design;
- human-to-agent composition design.

Diagrams and tables should be used where they materially reduce ambiguity.

## Design acceptance gates

A design decision becomes implementation authority only when:

1. it is consistent with all fixed invariants;
2. inputs, outputs, ownership, and failure semantics are explicit;
3. authority boundaries are explicit;
4. deterministic primitive behavior is specified where applicable;
5. both future UX adapters can consume the primitive without changing its semantics;
6. required conformance tests can be stated before implementation;
7. unresolved alternatives that affect correctness are either decided or explicitly deferred behind a non-blocking boundary;
8. the resulting design is recorded as durable project evidence.

Upper-layer `rd_init` UX implementation must not begin while required primitives remain undefined or unproven.

## Relationship to the Designer directive

`agents/designer/DIRECTIVE.md` defines the behavior of a Reasoning Distiller Designer operating under this contract.

The Designer designs and proposes. It does not grant project authority, admit knowledge, or treat proposed protocol changes as accepted normative contracts.
