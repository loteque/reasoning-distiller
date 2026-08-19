# RIL Architecture Synthesis

Status: **Implementation blueprint — primitive-first**

Governing contract: [`docs/design/RD_INIT_DESIGN_CONTRACT.md`](./RD_INIT_DESIGN_CONTRACT.md) (`reasoning-distiller-ril-design/1`)

Designer directive: [`agents/designer/DIRECTIVE.md`](../../agents/designer/DIRECTIVE.md)

Public command identity: `ril`.

## 1. Purpose

This document synthesizes the accepted RIL design decisions into an implementation-ready primitive architecture and dependency order.

It does **not** authorize upper-layer `ril` CLI or human-to-agent UX implementation. Those layers remain blocked until every primitive they depend on has a normative contract, implementation, coverage, and passing conformance gate.

Core rule:

> **Primitives first; UX later.**

## 2. System boundaries

```text
                         Reasoning Distiller package
┌─────────────────────────────────────────────────────────────────┐
│ normative RGP / PEMS / COVE contracts                          │
│ generic validators                                             │
│ generic role definitions                                       │
│ deterministic runtime primitives                               │
│                                                               │
│                    no project authority                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │ installed package
                               ▼
                         consuming project
┌─────────────────────────────────────────────────────────────────┐
│ project evidence                                               │
│ project role registry                                          │
│ project operator registry                                      │
│ approval artifacts                                             │
│ append-only administrative / authority events                  │
│ deterministic current projections                              │
│ Steward reconciliation dispositions                            │
│ admitted PEMS/COVE state                                       │
└─────────────────────────────────────────────────────────────────┘
```

Authority remains separated:

```text
Distiller              → candidate production only
Human operators        → project administrative approval only
Authorized Steward     → semantic reconciliation and/or admission
RIL orchestrator       → inspection + composition only
```

Consumer-side Architect or RGP Engineer protocol-governance capability is forbidden. RGP/PEMS/COVE evolution occurs upstream only.

## 3. Architectural layers

```text
Layer 5  UX adapters
         ├─ Unix-like `ril ...`
         └─ Human ↔ Agent interaction
                     ▲
Layer 4  Lifecycle orchestrator / state classifier
                     ▲
Layer 3  Domain primitives
         ├─ operators
         ├─ roles
         ├─ Steward authorization
         ├─ activation
         ├─ evidence / invocation
         ├─ reconciliation
         ├─ admission
         └─ repair / recovery
                     ▲
Layer 2  Common mutation substrate
         proposal → approval → apply → event → projection
                     ▲
Layer 1  Existing package/runtime substrate
         install → bootstrap → validators → rd-distill
```

Layer 2 is the first new implementation slice because Layers 3 and 4 depend on it.

## 4. Common mutation substrate

Three project-owned systems initially share one transactional architecture:

- operator registry;
- role registry;
- Steward authorization.

### 4.1 Transaction model

```text
current authoritative history + requested change
                    │
                    ▼
               PLAN primitive
                    │
                    ▼
          canonical proposal artifact
                    │
               SHA-256 digest
                    │
                    ▼
             HUMAN REVIEW
                    │
                    ▼
          approval artifact bound
          to exact proposal digest
                    │
                    ▼
               APPLY primitive
        ┌───────────┼─────────────┐
        │ validate  │ validate    │ validate
        │ proposal  │ approval    │ current state
        └───────────┼─────────────┘
                    ▼
          append immutable event
                    │
                    ▼
       rebuild deterministic projection
```

### 4.2 Source-of-truth rule

```text
append-only event history = authoritative
current projection         = derived
proposal                   = intent
approval artifact          = human authorization evidence
```

A projection creates no authority independently of the authoritative history.

### 4.3 Required common contracts

The first design/implementation slice MUST define these versioned contracts:

| Contract | Purpose |
|---|---|
| `reasoning-distiller-proposal/1` | canonical exact mutation proposal |
| `reasoning-distiller-approval/1` | human approval bound to proposal digest |
| `reasoning-distiller-mutation-event/1` | immutable successful state-transition event |
| `reasoning-distiller-projection-status/1` | projection/replay consistency result |
| `reasoning-distiller-operation-result/1` | common machine-readable PASS/FAIL/NO_CHANGE result envelope |

Domain-specific proposal/event payloads remain typed; the common envelope does not erase operator/role/authority semantics.

### 4.4 Approval retry semantics

An approval authorizes one transition, not repeated authority.

```text
same approval + resulting state still current
  → PASS / NO_CHANGE

same approval + state changed after original transition
  → FAIL / APPROVAL_ALREADY_CONSUMED

proposal digest differs
  → FAIL / APPROVAL_MISMATCH
```

Original proposal, approval, and mutation event remain durable.

## 5. Operator architecture

### 5.1 Identity

A human operator has a project-local durable identity, e.g.:

```text
operator:owner
operator:alice
```

Authentication evidence is a separate extensible concern. Operator identity remains stable as authentication mechanisms evolve.

### 5.2 Initial operator

Bootstrap creates no human authority.

First authority-sensitive operation with no operator registry produces:

```text
BLOCKED / INITIAL_OPERATOR_REQUIRED
```

A dedicated initial-operator ceremony establishes the protected root operator.

Initial core capabilities:

```text
rd:operator_management
rd:role_registry
rd:steward_authorization
```

Project-defined capabilities MUST use a separate namespace such as `project:*` and cannot satisfy `rd:*` checks.

### 5.3 Operator events

Ordinary operator administration uses the common mutation substrate.

Required operations:

```text
ADD_OPERATOR
UPDATE_CAPABILITIES
DISABLE_OPERATOR
REENABLE_OPERATOR
```

The protected root cannot be removed or demoted through ordinary operator mutation. Root transfer is a separate ceremony.

## 6. Role-registry architecture

### 6.1 Identity model

Registry entries are durable **role definitions**, not role instances.

Role IDs are project-global. Submission origin is provenance.

### 6.2 Package role

The package supplies:

```text
steward:default
```

It is always available in a valid installation, immutable to consumer registry operations, excluded from snapshot-disable semantics, and never authorized automatically.

### 6.3 Operating-entity submissions

Submissions are either:

```text
incremental
snapshot(scope=...)
```

Diff classification:

```text
unknown role     → ADD
identical role   → NO_CHANGE
changed role     → UPDATE
absent in scoped snapshot → DISABLE
```

All mutating outcomes are proposals requiring appropriate human approval.

Package-provided roles are excluded from consumer disable proposals.

### 6.4 Role lifecycle

Required operations:

```text
ADD
UPDATE
DISABLE
REENABLE
```

Ordinary destructive deletion is not part of v1.

Disabling an authorized role does not transfer authority; affected scopes become blocked.

## 7. Steward authorization architecture

Steward authority is assigned independently per scope:

```text
semantic_reconciliation → zero or one role_id
admission               → zero or one role_id
```

Required operations:

```text
AUTHORIZE(scope, role_id)
REASSIGN(scope, role_id)
REVOKE(scope)
```

Preconditions include:

- target role exists;
- target role is currently available;
- approving operator possesses `rd:steward_authorization`;
- exact proposal has a valid approval artifact;
- projection matches authoritative history.

There is no fallback when authorization is missing or its target becomes unavailable.

## 8. Runtime role activation

Authorization and activation are independent checks.

```text
registered role
    ↓
authorized for scope
    ↓
current invocation supplies activation evidence
    ↓
activation validator accepts evidence
    ↓
operation allowed
```

The v1 activation contract SHOULD support an explicit declaration method while reserving typed authentication/attestation evidence for future policy strengthening.

An invocation cannot gain authority solely because its role name matches an authorized role.

## 9. Reconciliation and admission boundary

These remain separate domain primitives.

```text
immutable Distiller submission
        ↓
authorized + activated reconciliation Steward
        ↓
semantic reconciliation
        ↓
immutable reconciliation disposition
        ↓
STOP unless admission separately requested
        ↓
authorized + activated admission Steward
        ↓
admission primitive
        ↓
PEMS/COVE canonical storage
```

Reconciliation may determine semantic compatibility and produce an admission recommendation/disposition, but it does not itself mutate PEMS/COVE unless the separate admission primitive is invoked with valid admission authority.

The exact reconciliation transformation and admission contracts remain the next domain-design work after the administrative substrate is proven.

## 10. Projection, repair, and recovery

### 10.1 Projection policy

```text
missing projection
  → replay valid history
  → rebuild automatically

matching projection
  → proceed

conflicting projection
  → FAIL CLOSED
  → ordinary repair required
```

### 10.2 Ordinary repair

Ordinary repair may:

- validate authoritative event history;
- regenerate derived projections.

It may not alter authoritative history.

### 10.3 Exceptional recovery

If authoritative history itself is invalid:

```text
preserve damaged history
       ↓
collect recovery evidence
       ↓
protected root human approval
       ↓
append RECOVERY event
       ↓
continue authoritative replay from recovery point
```

Delegated operator authority is insufficient.

## 11. Lifecycle/state model

RIL status is a **classification over observable state**, not a source of state.

The system has orthogonal dimensions; a single linear enum is insufficient for internal correctness. The status primitive SHOULD calculate a composite state and may expose a simplified next-action summary.

### 11.1 Dimensions

| Dimension | Representative states |
|---|---|
| installation | `MISSING`, `VALID`, `INCOMPATIBLE` |
| project bootstrap | `MISSING`, `VALID`, `CONFLICT` |
| operator | `MISSING`, `VALID`, `CONFLICT` |
| role registry | `VALID`, `CONFLICT` |
| reconciliation authority | `UNASSIGNED`, `AVAILABLE`, `TARGET_UNAVAILABLE`, `CONFLICT` |
| admission authority | `UNASSIGNED`, `AVAILABLE`, `TARGET_UNAVAILABLE`, `CONFLICT` |
| evidence | `NONE`, `AVAILABLE`, `SELECTED` |
| candidate | `NONE`, `PENDING`, `VALID_SUBMISSION` |
| reconciliation | `NOT_REQUIRED`, `REQUIRED`, `DISPOSITION_READY`, `BLOCKED` |
| admission | `NOT_READY`, `READY`, `ADMITTED`, `BLOCKED` |
| projection health | `VALID`, `REBUILDABLE`, `CONFLICT` |
| history health | `VALID`, `INVALID` |

### 11.2 Global blocking precedence

Status classification MUST surface the highest-precedence blocker before suggesting a transition:

```text
1. installation/project incompatibility
2. invalid authoritative history
3. conflicting derived projection
4. missing initial operator for authority-sensitive action
5. missing/unavailable required authority
6. missing activation evidence
7. missing explicit evidence/candidate input
8. normal next lifecycle transition
```

### 11.3 Simplified lifecycle projection

For human UX, the orchestrator may project the composite state into a simplified progression:

```text
UNINSTALLED
→ INSTALLED
→ INITIALIZED
→ EVIDENCE_READY
→ CANDIDATE_READY
→ RECONCILIATION_REQUIRED
→ RECONCILED
→ ADMISSION_READY
→ ADMITTED / READY
```

The simplified lifecycle MUST never hide a blocking orthogonal state.

## 12. Primitive dependency graph

```text
existing install/bootstrap
        │
        ├─────────────── status inspection foundation
        │
        ▼
common canonicalization + digest
        │
        ▼
proposal primitive
        │
        ▼
approval artifact primitive
        │
        ▼
event append + replay + projection
        │
        ├──────────────┬─────────────────┐
        ▼              ▼                 ▼
operator registry   role registry   projection repair
        │              │
        ▼              ▼
initial operator    role submission
        │              │
        ├──────┬───────┘
        ▼      ▼
operator mgmt  Steward authorization
                    │
                    ▼
             activation validation
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
reconciliation primitive   admission primitive
        │                       │
        └───────────┬───────────┘
                    ▼
            storage verification
                    │
                    ▼
          lifecycle orchestrator
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       `ril` CLI         Human ↔ Agent UX
```

Exceptional recovery depends on operator/root identity, approval evidence, and event replay, but remains outside ordinary mutation flows.

## 13. Implementation sequence

The implementation should proceed in gates, not by command surface.

| Gate | Slice | Exit condition |
|---|---|---|
| **R1** | common canonical JSON/digest/result rules | deterministic identities proven |
| **R2** | proposal + approval artifact contracts/primitives | exact binding + mismatch tests pass |
| **R3** | append-only event + replay + projection substrate | replay/idempotence/corruption tests pass |
| **R4** | operator registry + initial-operator ceremony | protected root semantics pass |
| **R5** | operator management + root-transfer design/primitive | delegation + root invariants pass |
| **R6** | role registry + incremental/snapshot submissions | package-role protection + scoped diff pass |
| **R7** | Steward authorization | independent scopes/reassign/revoke pass |
| **R8** | activation evidence | authorized role + accepted activation required |
| **R9** | status/composite lifecycle classifier | blocker precedence + no hidden conflict pass |
| **R10** | ordinary repair + projection rebuild | history-preserving repair pass |
| **R11** | exceptional recovery | root-only evidence-backed continuation pass |
| **R12** | reconciliation contract + primitive | authority-bound semantic disposition pass |
| **R13** | admission contract + primitive | separate admission authority + canonical mutation pass |
| **R14** | PEMS/COVE storage verification | admitted-state integrity pass |
| **R15** | orchestrator composition | invokes proven primitives only |
| **R16** | UX adapters | `ril` CLI + Human↔Agent parity |

No later gate may absorb a missing earlier primitive.

## 14. Conformance matrix

| Primitive family | Must prove |
|---|---|
| canonicalization/digest | same semantic artifact → same bytes/digest under contract rules |
| proposal | exact current-state basis + requested transition; no mutation |
| approval | exact proposal binding; human operator identity; required capability policy |
| apply/event | preflight before mutation; append once; retry idempotence |
| projection | replay determinism; missing rebuild; conflict detection |
| initial operator | no preexisting authority; one protected root; idempotent retry |
| operator management | capability enforcement; root protection; append-only history |
| role registry | project-global identity; approval-gated update; scoped snapshot; package role immutable |
| Steward authorization | zero/one holder per scope; independent scopes; no fallback |
| activation | authorization alone insufficient; invalid/missing activation blocks |
| status | read-only; deterministic; blocker precedence; no authority mutation |
| ordinary repair | derived state only; event history untouched |
| exceptional recovery | damaged history preserved; root approval required; recovery continuation explicit |
| reconciliation | immutable candidate input; authorized+activated Steward; no admission mutation |
| admission | reconciled/admission-ready input; separately authorized+activated Steward; bounded canonical mutation |
| storage verification | admitted PEMS/COVE state conforms to package contracts |
| orchestrator | composition only; no hidden authority/protocol semantics |
| UX parity | CLI and agent flows produce equivalent primitive requests/results |

## 15. Immediate implementation target

The next implementation target is **R1–R3: the common mutation substrate**.

Before writing domain-specific operator/role/Steward behavior, define and implement:

```text
canonical artifact serialization
proposal envelope + digest
approval artifact + exact binding
mutation event envelope
append-only event store
replay engine
current projection writer/checker
common operation result envelope
```

The first conformance gate should prove:

1. plan performs no mutation;
2. proposal identity is deterministic;
3. approval for proposal X cannot apply to proposal Y;
4. successful apply appends exactly one event;
5. retry of the same consumed approval yields `NO_CHANGE` only while the resulting state remains current;
6. projections reproduce event replay exactly;
7. missing projections rebuild safely;
8. conflicting projections fail closed;
9. authoritative event bytes are never rewritten by ordinary operations.

## 16. Deferred upper-layer UX

No `ril` command implementation is authorized by this synthesis except as future composition design.

The eventual UX may resemble:

```text
ril status
ril operators ...
ril roles ...
ril steward ...
ril evidence ...
ril distill ...
ril reconcile ...
ril admit ...
ril repair ...
```

but command topology remains subordinate to primitive contracts.

The Human↔Agent workflow must generate the same primitive inputs and consume the same result contracts; conversational approval cannot replace the durable approval artifact.

## 17. Remaining design work

No further broad owner requirements are required to begin R1–R3.

Before each later gate, the Designer must produce the corresponding normative domain contract. Correctness-relevant questions discovered during those slices must be surfaced explicitly rather than invented by the implementation engineer.

The largest intentionally deferred domain designs are:

- exact operator/role artifact schemas beyond the common substrate;
- root-transfer ceremony details;
- activation evidence v1 methods;
- semantic reconciliation transformation/disposition rules;
- admission handoff and PEMS/COVE mutation rules;
- compatibility/migration between future accepted package versions;
- project-layer conformance assertion above RGP/PEMS/COVE.

These deferrals do not block R1–R3.

## 18. Designer disposition

**Architecture synthesis: APPROVE FOR PRIMITIVE IMPLEMENTATION R1–R3.**

Implementation authority is limited to the common deterministic mutation substrate described above. Upper-layer orchestration and UX remain blocked by the staged completion gates.
