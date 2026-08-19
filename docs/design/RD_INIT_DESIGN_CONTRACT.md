# RIL Orchestrator Design Contract

Status: **Normative design contract — guided requirements complete**

Contract: `reasoning-distiller-ril-design/1`

Public command: `ril`

## Supersession

This document supersedes the original `rd_init` Design Contract committed at [`cad8169ac545a339103b02815a6e359f47c41e3c`](https://github.com/loteque/reasoning-distiller/commit/cad8169ac545a339103b02815a6e359f47c41e3c).

The exact superseded document is preserved at the [raw committed artifact](https://raw.githubusercontent.com/loteque/reasoning-distiller/cad8169ac545a339103b02815a6e359f47c41e3c/docs/design/RD_INIT_DESIGN_CONTRACT.md).

The former `rd_init` name is superseded because lifecycle orchestration extends beyond initialization. The accepted public command is `ril`. `Reasoning Distiller` remains the product/protocol identity; `ril` is the command identity and is not assigned a separate acronym expansion. Package-distribution names MUST remain distinct from occupied `ril` package namespaces.

## Purpose

This contract governs design and implementation of the Reasoning Distiller lifecycle orchestrator and its deterministic primitive substrate.

The guided requirements pass is complete. The decisions below are normative constraints for architecture synthesis and primitive implementation. They do not authorize upper-layer UX implementation before its primitive gates pass.

## Core principle

> **Primitives first; UX later.**

The orchestrator is a state machine over stable deterministic primitives. It is not where primitive semantics, authority, protocol rules, or project truth are defined.

Primitive architecture and orchestration design may proceed together. Public UX implementation MUST NOT begin until every primitive on which that UX depends has a contract, implementation, coverage, and passing conformance gate.

## Target UX adapters

The same primitive semantics MUST support both future UX workflows:

```text
                    deterministic primitives
                             │
              ┌──────────────┴──────────────┐
              │                             │
        Unix-like CLI                 Human ↔ Agent
        ril ...                       guided interaction
        composable commands           over same contracts
```

No semantic operation may exist only as conversational behavior or only as a TTY interaction.

## Fixed invariants

### Authority

1. The orchestrator has no semantic-reconciliation authority.
2. The orchestrator has no admission authority.
3. The Distiller has candidate-production authority only; it does not reconcile or admit.
4. Steward authority is project-owned and originates from explicit human approval.
5. Agents may discover, propose, explain, validate, and execute approved decisions; agent action cannot substitute for human approval.
6. Role registration does not grant authority.
7. Role authorization does not prove that a current invocation is acting as that role.
8. Authorization is revocable and reassignable without rewriting history.
9. `semantic_reconciliation` and `admission` are independent authority scopes.
10. Each authority scope has exactly zero or one authorized role.
11. Reassignment of one authority scope does not implicitly modify another.
12. No unavailable authority target causes silent fallback or reassignment.

### Protocol ownership

1. RGP, PEMS, and COVE are normative package-owned contracts.
2. Consuming projects may not fork, mutate, replace, supersede, or reinterpret normative RGP/PEMS/COVE contracts, schemas, or generic validators.
3. Consumer-side Architect and RGP Engineer protocol-governance capabilities are forbidden, including equivalent capabilities under different names.
4. Projects may implement policies, adapters, and protocol layers above RGP/PEMS/COVE only when conformant with accepted package contracts.
5. Protocol evolution occurs upstream in the generic Reasoning Distiller repository through explicit review, versioning, validation, and release.

### Distribution and locality

1. Installed projects operate from `.reasoning-distiller/` and project-owned state.
2. Runtime operation must not depend on a live checkout of the generic repository.
3. Version/update pathways may reference the generic repository or accepted release metadata, but ordinary project execution remains local except for explicit model/provider transport.

### State and evidence

1. Project evidence is explicit; orchestration must not silently broaden a Distiller evidence set.
2. Operational provenance is not canonical project knowledge.
3. Candidate production, semantic reconciliation, and PEMS/COVE admission remain distinct operations.
4. Unknown or conflicting authority-sensitive state fails closed.
5. Authoritative append-only history is never silently rewritten.

## Accepted role-registry model

### Identity

A registry entry represents a **durable project role definition**, not an ephemeral chat, model run, agent invocation, or role instance.

Role IDs are project-global. Submission origin is provenance, not identity.

```text
role registry
  └── project-engineering-steward

runtime invocation
  └── activates/claims project-engineering-steward
```

### Role evolution

Operating entities may submit role definitions. Submissions are proposal inputs, not authority.

For a submitted role:

```text
unknown role    → ADD proposal
identical role  → NO_CHANGE
changed role    → UPDATE proposal → human approval required
```

A later submission cannot silently broaden or redefine an existing project-global role.

### Submission modes and snapshot scope

Submissions explicitly declare `incremental` or `snapshot` semantics.

```text
incremental
  present role → evaluate ADD / NO_CHANGE / UPDATE
  absent role  → untouched

snapshot
  present role → evaluate ADD / NO_CHANGE / UPDATE
  absent role within declared scope → DISABLE proposal
```

Every snapshot MUST declare the scope over which it claims completeness. Snapshot absence affects only that explicit scope.

Package-provided roles are excluded from consumer snapshot-disable semantics.

### Package-provided roles

The package provides one default Steward role.

The default Steward is:

- registered by the package;
- always available as an authorization target in a valid installation;
- immutable by consumer role-registry operations;
- not disableable by consumer snapshots or ordinary registry mutation;
- never authorized automatically.

Package-provided availability is distinct from project-owned authorization.

### Ordinary project-role lifecycle

Project role management MUST support at least:

```text
ADD
UPDATE_METADATA / UPDATE_DEFINITION as contractually permitted
DISABLE
REENABLE
```

Ordinary operation favors disable/reenable over destructive deletion so history remains auditable.

Disabling an authorized project role MUST NOT silently transfer its authority. The affected authority scope becomes blocked pending explicit human action.

## Steward authorization model

Authorization references registered durable role IDs.

Reconciliation and admission assignments are independent:

```text
semantic_reconciliation → zero or one role_id
admission               → zero or one role_id
```

The same role may hold both scopes, different roles may hold them, or either/both may be unassigned.

Required transitions include:

```text
AUTHORIZE(scope, role_id)
REASSIGN(scope, role_id)
REVOKE(scope)
```

There is no implicit fallback.

### Authorization persistence

Authorization uses append-only events plus a deterministic current-state projection.

```text
authorization events     ← authority source of truth
        ↓ replay
current projection       ← derived/disposable state
        ↓
runtime authority checks
```

A missing projection may be rebuilt automatically from valid authoritative history. A present projection that conflicts with replayed history blocks authority-sensitive operation and requires repair.

## Human operator model

### Stable identity

Human approvals reference a project-local stable operator identity such as `operator:owner`.

Operator identity is separate from authentication evidence:

```text
operator identity
      ↓
authentication evidence
      ↓
approval artifact
```

Authentication evidence is extensible. Initial policy may permit simpler evidence; future policy may require validated GitHub identity, cryptographic signatures, OS identity, enterprise IdP evidence, platform-specific human confirmation, or other accepted mechanisms without changing stable operator identity semantics.

### Initial operator

Installation and bootstrap create no operator authority.

The first authority-sensitive operation with no operator established MUST require an explicit **initial-operator setup ceremony**.

The initial operator is the protected root operator and begins with the complete Reasoning Distiller administrative capability set required for recovery and delegation.

### Multiple operators and capabilities

Multiple operators are supported with explicit administrative capabilities.

Reasoning Distiller owns a fixed core capability namespace, initially including at least:

```text
rd:operator_management
rd:role_registry
rd:steward_authorization
```

Projects may define namespaced extension capabilities such as `project:*`, but a project-defined capability can never satisfy, alias, override, or redefine a check requiring an `rd:*` capability.

Human administrative authority is distinct from Steward semantic authority.

### Root protection

Operators with `rd:operator_management` may manage delegated operators, but ordinary operator-management operations MUST NOT remove/demote the protected root in a way that destroys the project's recovery authority.

Changing the root requires a distinct explicit **root-transfer ceremony**.

## Proposal and human-approval transaction model

Role-registry mutations, operator-registry mutations, and Steward-authorization mutations use one common transactional architecture:

```text
proposal
   ↓ deterministic digest
human reviews exact proposal
   ↓
approval artifact
   ↓ exact digest binding
apply primitive
   ↓
append-only mutation event
   ↓
deterministic current projection
```

### Approval invariants

1. Approval MUST be bound to the exact proposed mutation by deterministic digest.
2. Approval of proposal X cannot authorize proposal Y.
3. The original approval artifact is preserved durably.
4. The immutable mutation event preserves or references the approval artifact/digest.
5. Approval artifacts are not reusable authority credentials.
6. Retry is idempotent:
   - same approval + resulting state still present → `NO_CHANGE` / success;
   - same approval + state subsequently changed → reject;
   - changed proposal → reject.
7. The applying primitive MUST validate the approving operator and required administrative capability.

Initial-operator setup, root transfer, and exceptional recovery are special ceremonies because they establish, transfer, or recover the root of trust.

## Runtime role activation

Authorization determines what a durable role may do. Activation evidence determines whether the current invocation may act as that role.

```text
durable role identity
       ↓
activation evidence
       ↓
current invocation
       ↓
authorization check
       ↓
operation permitted / denied
```

Activation evidence uses a structured extensible contract. An explicit declaration may be an initially accepted evidence method. Future policy may require stronger session, platform, signature, or identity evidence without changing role-registry or authorization semantics.

## Projection, repair, and recovery

### Projection behavior

```text
projection missing
    → deterministic rebuild from valid authoritative history allowed

projection consistent
    → proceed

projection conflicting
    → FAIL CLOSED
    → explicit repair required
```

### Ordinary repair

Ordinary repair validates authoritative event history and may rebuild derived projections only. It MUST NOT alter authoritative event history.

If event history is invalid, ordinary repair stops.

### Exceptional recovery

Historical corruption uses a separate evidence-backed recovery ceremony.

The ceremony MUST:

1. preserve damaged/original history untouched;
2. identify the damaged range/state;
3. collect durable recovery evidence;
4. require explicit protected-root-operator approval;
5. append a special recovery record establishing the authoritative continuation;
6. make replay semantics understand that recovery record rather than pretending corruption never occurred.

Delegated administrative authority alone is insufficient for exceptional recovery.

## Orchestrator boundary

The lifecycle orchestrator may:

- inspect local project/install state;
- classify lifecycle state;
- identify the next required primitive;
- present available safe actions;
- invoke bounded primitives after required inputs and approvals are satisfied;
- surface machine-readable status and diagnostics;
- compose the Unix-like CLI and human-to-agent adapters over identical primitive contracts.

The orchestrator MUST NOT:

- absorb primitive semantics into orchestration code;
- grant or infer project authority;
- mutate normative protocols;
- invent evidence or project facts;
- silently choose an authority holder;
- silently admit candidate knowledge;
- treat structural validity as semantic acceptance;
- hide undefined states behind UX defaults.

## Primitive dependency rule

The orchestrator may invoke only primitives whose contracts and conformance gates are accepted.

The synthesis phase MUST refine at least these primitive families:

```text
installation
project bootstrap
status/state inspection
operator identity + registry
initial-operator ceremony
operator mutation
root-transfer ceremony
approval artifact creation/validation
role registry + role submission
Steward authorization
activation evidence validation
evidence preparation/validation
invocation preparation
rd-distill
Steward reconciliation
admission handoff/admission
PEMS/COVE storage verification
projection rebuild/ordinary repair
exceptional recovery
```

A missing primitive is a design/implementation gap and MUST NOT be hidden as ad hoc orchestrator logic.

## Candidate lifecycle design subject

Architecture synthesis MUST refine the lifecycle/state machine. The earlier candidate remains useful as a starting point but is not accepted merely by inclusion here:

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

Blocked, missing-operator, unavailable-authority, conflicted, incompatible-version, corruption, repair, recovery, and migration states MUST be explicit where materially distinct.

## Public command identity

The accepted public command is:

```text
ril
```

Intended command-family ergonomics include forms such as:

```text
ril status
ril roles
ril operators
ril steward
ril evidence
ril distill
ril reconcile
ril admit
ril repair
```

These examples establish command identity and design direction, not yet final subcommand topology. Final CLI topology remains an architecture/UX composition output after primitive semantics are complete.

`ril` was selected after rejecting candidates with material executable/developer-tool collisions. `Reasoning Distiller` remains the product and protocol identity. `ril` MUST NOT be given an invented normative acronym expansion.

## Remaining architecture-synthesis questions

The guided requirements pass is complete. Architecture synthesis must now turn the decisions above into implementation-ready artifacts and may surface additional questions only when a correctness-relevant ambiguity genuinely remains.

At minimum synthesis must settle:

1. exact lifecycle states, transitions, blocked states, and recovery transitions;
2. exact schemas for operator, role, submission, proposal, approval, event, projection, activation, repair, and recovery artifacts;
3. primitive inputs, outputs, ownership, idempotence, failure semantics, and exit/result contracts;
4. reconciliation primitive semantics and durable disposition format;
5. admission primitive/handoff semantics and exact distinction among reconciled, admission-ready, and admitted state;
6. evidence-readiness discovery/selection boundaries;
7. compatibility and migration rules across accepted package versions;
8. project extension/conformance assertion mechanism above RGP/PEMS/COVE;
9. exact package role inventory versus upstream-only governance roles;
10. machine-readable status/result contracts usable unchanged by both UX adapters;
11. primitive conformance-test matrix and dependency ordering;
12. final Unix-like command topology and human-to-agent composition after primitive gates permit UX implementation.

## Required design outputs

Architecture synthesis MUST produce implementation-ready artifacts covering:

- lifecycle/state-machine specification;
- primitive inventory and dependency graph;
- common proposal/approval/event/projection transaction contract;
- operator identity and registry contract;
- initial-operator and root-transfer ceremony contracts;
- role-registry and role-submission contract;
- Steward authorization contract;
- activation-evidence contract;
- reconciliation contract;
- admission boundary contract;
- state/status inspection contract;
- repair and exceptional-recovery contracts;
- error/conflict/recovery taxonomy;
- protocol-extension/conformance policy;
- compatibility/versioning/migration rules;
- security/authority invariants;
- conformance-test plan for every primitive;
- Unix-like CLI composition design;
- human-to-agent composition design.

Diagrams and tables SHOULD be used where they materially reduce ambiguity.

## Design and implementation gates

A design decision becomes implementation authority only when:

1. it is consistent with all fixed invariants and accepted guided decisions;
2. inputs, outputs, ownership, and failure semantics are explicit;
3. authority boundaries are explicit;
4. deterministic primitive behavior is specified where applicable;
5. both future UX adapters can consume the primitive without changing semantics;
6. required conformance tests can be stated before implementation;
7. correctness-relevant alternatives are decided or explicitly deferred behind a non-blocking boundary;
8. the resulting design is recorded as durable project evidence.

The staged completion rule is normative:

```text
primitive contracts
       ↓
primitive architecture settled
       ↓
orchestration DESIGN allowed
       │
       ├──────────────┐
       ↓              ↓
primitive         state-machine /
implementation    composition design
       │              │
       ↓              │
tests + PASS           │
       └──────┬────────┘
              ↓
       public UX implementation
              ↓
       ril CLI + Human ↔ Agent
```

Public UX implementation MUST NOT begin until every primitive it depends upon is implemented, covered, and passing.

## Relationship to the Designer directive

`agents/designer/DIRECTIVE.md` defines the behavior of a Reasoning Distiller Designer operating under this contract.

The Designer designs and proposes. It does not grant project authority, admit knowledge, fork consumer RGP/PEMS/COVE contracts, or treat proposed protocol changes as accepted normative contracts.
