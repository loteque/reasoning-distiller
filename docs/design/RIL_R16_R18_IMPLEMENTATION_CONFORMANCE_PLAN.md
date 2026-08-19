# R16–R18 — Implementation and Conformance Gate Plan

Status: **Non-authoritative implementation plan — design-complete; implementation authorization required**

Depends on: accepted R1–R18, including R16A CLI, R16B Human↔Agent interaction, D1 durable workflows, D2 provenance, D3 proposal revalidation, R17 authority grants, and R18 operation delegability classification.

## Purpose

This plan defines the implementation/conformance sequence for the accepted R16–R18 design without granting implementation authority by itself.

The objective is to implement the new orchestration and adapter surfaces in dependency order while continuously proving that no implementation shortcut weakens exact proposal binding, human intent, protected authority, Steward activation, materiality, or apply-time validation.

## Gate sequence

### G1 — Shared artifact and validation substrate

Implement and test the accepted shared structures before adapter behavior:

1. `reasoning-distiller-approval/2` authority-basis union;
2. D3 proposal-applicability validator;
3. `provenance:<id>` artifact creation/validation/indexing by subject;
4. typed-reference dispatch required by generic `ril show`;
5. common operation delegation metadata registry with fail-closed default.

PASS requires deterministic canonical identities, exact proposal binding, compatibility with existing direct approvals, and proof that provenance has no authority effect.

### G2 — Durable workflow primitive

Implement D1 workflow definitions, append-only workflow events, dual heads, lifecycle/condition projection, exact-state concurrency, cancellation, revision/supersession, materiality acknowledgement, retry, and continuation eligibility.

PASS requires at minimum:

- immutable authenticated workflow scope;
- `history_head` and `normative_head` semantics;
- informational events cannot alter normative concurrency;
- terminal states are irreversible;
- revision is atomic and never silently rebases intent;
- acknowledgement binds to the exact materiality pause;
- workflow permission never substitutes for approval, activation, or other downstream authority.

### G3 — Authority-grant primitive

Implement R17 grant definition validation, lifecycle/event history, scope matching, grant consumption, revocation, exhaustion, expected-head concurrency, and atomic grant-derived approval issuance.

Initial accepted delegable registry:

```text
role-registry.change
operator-registry.disable
```

PASS requires fail-closed treatment of every other operation class, immutable grant definitions, no subdelegation, exact workflow binding, deterministic scope containment, and proof that revocation cannot rewrite previously issued approval evidence.

### G4 — R18 operation-specific integration

Integrate grant matching into delegable operation contracts only.

For `role-registry.change`, preserve the accepted role target/mutation schema and consumer `rd:*` prohibitions.

For `operator-registry.disable`, enforce:

```text
operation_class: operator-registry.disable
delegable: true
selector: operator_id = exact | one-of
constraint: operation == DISABLE_OPERATOR
```

and independently prove the target is not protected root from authoritative state.

PASS requires negative tests proving grants cannot authorize:

```text
INITIALIZE_ROOT
ADD_OPERATOR
UPDATE_CAPABILITIES
REENABLE_OPERATOR
TRANSFER_ROOT
steward-authorization changes
exceptional recovery
authority-grant creation/expansion
workflow revision/materiality acknowledgement
```

### G5 — Shared orchestration

Implement the adapter-neutral orchestration path used by CLI, Human↔Agent, and automation adapters.

For an exact proposal within a durable auto-advance workflow, the orchestration order is:

```text
proposal
  ↓
D3 applicability
  ↓
operation delegability
  ↓
applicable grant discovery
  ↓
grant containment/lifecycle/limit validation
  ↓
materiality/workflow-boundary validation
  ↓
atomic grant-derived approval issuance OR AWAITING_APPROVAL
  ↓
apply-time validation
  ↓
apply
  ↓
workflow result binding / continuation
```

No adapter may reorder these checks in a way that changes authority meaning.

Multiple applicable grants must obey R17 ambiguity rules; agent/runtime convenience is not a valid tie-break.

### G6 — R16A CLI adapter

Implement the accepted command topology and presentation semantics, including:

- project discovery and global options;
- generic `ril show <typed-reference>`;
- inspection `--depth=0|1|2` semantics;
- human/JSON/quiet presentation invariants;
- workflow resource family;
- authority-grant resource family;
- D3-aware `ril approve`;
- grant-aware workflow continuation;
- canonical typed-reference output rules;
- aggregate history behavior.

PASS requires command-to-primitive mapping tests proving the CLI introduces no semantic operation or authority unavailable through shared orchestration.

### G7 — R16B Human↔Agent adapter

Implement peer-adapter behavior over the same orchestration boundary.

PASS requires tests proving:

- conversational affirmations are context-bound;
- broad requests cannot become open-ended delegation;
- proposal presentation exposes exact immutable references;
- direct approval invokes D3 immediately before approval creation;
- grant-derived approval occurs without fresh assent only when R17/R18 prove coverage;
- materiality pauses interrupt auto-advance;
- protected ceremonies remain explicit;
- control return never implies an operation completed when it merely proposed, approved, attempted, or blocked;
- cross-session continuation reconstructs authority from durable artifacts rather than chat history.

### G8 — Cross-adapter parity

For every semantic action exposed by more than one adapter, construct conformance fixtures proving equivalent normative artifacts/results from equivalent authoritative inputs.

At minimum cover:

```text
proposal inspection
approval creation
workflow creation/continuation/cancellation/revision/acknowledgement
authority-grant creation/revocation/consumption
role-registry grant-derived mutation
operator-disable grant-derived mutation
D3 stale/block outcomes
materiality pause behavior
```

Presentation may differ; normative meaning may not.

### G9 — Automation-boundary adversarial suite

Create explicit negative tests for the three remaining human automation boundaries:

1. **Materiality** — an in-scope grant cannot bypass a valid materiality pause.
2. **Scope/authority expansion** — an agent cannot broaden workflow or grant scope, infer wildcard authority, or convert unsupported operations into delegable ones.
3. **Non-delegable protected authority** — root/governance/recovery/Steward and other designated ceremonies cannot be satisfied by grants or conversational convenience.

Also test machine-state boundaries including stale state, grant exhaustion/revocation, missing activation, unresolved evidence, workflow concurrency races, and grant-selection ambiguity.

### G10 — End-to-end autonomous workflow proof

Run at least one full fixture in which a human prospectively creates:

```text
workflow:<id> + authority-grant:<id>
```

and the system autonomously performs a multi-stage bounded sequence containing both accepted delegable mutation classes plus non-proposal automatic operations, with no human interruption until completion.

Run paired fixtures proving interruption occurs exactly when materiality, scope expansion, or protected authority is introduced.

PASS demonstrates the practical R18 automation ceiling rather than only isolated primitive correctness.

## Implementation ordering rule

No adapter implementation should precede the shared primitive/orchestration behavior it depends on. CLI or conversational code MUST NOT temporarily encode authority semantics that are later intended to move into shared primitives.

The preferred dependency order is therefore:

```text
G1 → G2 → G3 → G4 → G5 → G6/G7 → G8 → G9 → G10
```

G6 and G7 may proceed in parallel only after G5 is stable enough to serve as their common semantic boundary.

## Compatibility rule

Existing R1–R15 direct-approval behavior must remain valid while approval/2 and grant-derived authority are introduced. Migration must not reinterpret historical `reasoning-distiller-approval/1` artifacts as grant-derived or weaken their existing verification semantics.

## Stop conditions

Implementation must stop for design review if any gate discovers that accepted behavior requires:

- agent/runtime judgment to determine authority scope;
- mutation of immutable workflow/grant intent;
- a hidden new authority source;
- weakening protected-root or exceptional-recovery ceremony;
- collapsing Steward authorization and activation;
- bypassing D3 or apply-time validation;
- treating provenance as authority;
- inventing trusted wall-clock semantics;
- changing Canon outside accepted admission/storage contracts.

## Completion condition

R16–R18 implementation is conformant only when G1–G10 all pass and the produced evidence demonstrates that ordinary grant-covered automation proceeds without redundant human approval while the three accepted human boundaries remain impossible to bypass.

## Current gate

Design integration through R18 is complete. The next actionable gate is **G1 — Shared artifact and validation substrate**.

Starting G1 is implementation work and therefore requires explicit implementation authorization beyond acceptance of this planning document.
