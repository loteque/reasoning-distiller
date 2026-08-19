# R16B-D1 — Durable Workflow Primitive and Artifact Design Contract

Status: **Normative dependency design contract — accepted design; integration amendment required**

Contract: `reasoning-distiller-workflow-design/1`

Depends on: accepted R1–R15 primitive/orchestration contracts, accepted R16A `reasoning-distiller-ril-cli-design/1`, and draft R16B `reasoning-distiller-ril-human-agent-design/1`.

Implementation status: **not authorized by this document alone.**

## Purpose

This contract resolves R16B dependency D1 by defining the durable workflow primitive/artifact model used to preserve bounded human intent across sessions, interruptions, agents, and execution attempts.

A workflow records authenticated bounded intent and progression. It grants no operator authority, Steward authority, approval, activation, semantic authority, admission authority, or resource lock.

## Core model

A workflow consists of:

1. an immutable content-addressed workflow definition;
2. an immutable append-only workflow-event history;
3. a separately maintained authoritative event-chain head;
4. a deterministic projection of workflow lifecycle and current condition.

```text
workflow:<id>             immutable authenticated intent
     │
     └── authoritative head
              ↓
      workflow-event:<id>
              ↓
      workflow-event:<id>
              ↓
      workflow-event:<id>
              │
              ↓
      deterministic projection
```

`workflow:<id>` always identifies exactly one immutable bounded intent. Its identity never advances with workflow history.

## Workflow definition

The immutable workflow definition contains both:

- **normative bounded intent**, which constrains what may be attempted; and
- an **advisory initial execution plan**, which describes the initial expected path.

The plan never expands intent. It may become stale or be recomputed without changing the authorized bounded intent.

The normative creation payload includes every field that affects workflow semantics, including at least:

- subject/scope;
- permitted operations and conditional operations;
- terminal conditions;
- execution mode;
- continuation policy;
- materiality-acknowledgement policy;
- relationship fields such as `supersedes:` or `resumes:` where applicable.

## Authenticated creation

Workflow creation is an authenticated operator act, not a proposal → approval → apply mutation.

Any enabled operator may create a workflow representing that operator's bounded intent. Creation itself cannot authorize execution of any operation named by the workflow.

Authentication MUST bind the operator to the exact canonical creation payload.

A two-stage digest construction avoids circular identity:

```text
creation_payload
      ↓ hash
payload_digest
      ↓ authenticated binding by operator
workflow artifact = creation_payload + authentication binding
      ↓ hash
workflow:<id>
```

`workflow:<id>` therefore identifies both the exact bounded intent and the authenticated act that established it. Identical bounded intent established independently by different operators produces distinct workflow artifacts.

## Continuation policy

The immutable workflow definition specifies who may request continuation.

Supported policy forms SHALL include at least:

```text
requester-only
any-enabled-operator
explicit operator set
```

The default is `requester-only`.

The protected root operator may request continuation of any OPEN workflow regardless of ordinary continuation policy.

Continuation permission grants no downstream authority. It is permission to request the next in-scope step only.

## Materiality acknowledgement policy

Materiality acknowledgement is distinct from continuation permission.

The immutable workflow definition specifies which operators may acknowledge a materiality pause. The default is requester-only.

The protected root operator may acknowledge any `MATERIALITY_PAUSE`.

Acknowledgement restores sufficiently informed intent only within the existing immutable workflow scope. It cannot revise intent, expand scope, or override missing/failed normative authority or validation.

## Execution mode

The immutable workflow definition specifies one of:

```text
operator-driven
auto-advance
```

Default: `operator-driven`.

`operator-driven` requires a permitted continuation request before the next consequential advancement.

`auto-advance` creates durable eligibility for autonomous continuation whenever the next in-scope operation becomes valid. It does not require or prescribe a daemon, polling service, scheduler, monitoring latency, or deployment architecture.

Auto-advance creates no authority. Every underlying operation independently validates its normal requirements.

A materiality pause suspends auto-advance. After valid acknowledgement, the existing auto-advance mode resumes if scope remains unchanged.

## Workflow lifecycle and condition

Lifecycle and current condition are separate dimensions.

Normative lifecycle:

```text
OPEN
COMPLETED
CANCELLED
SUPERSEDED
```

All terminal lifecycle states are irreversible.

```text
OPEN ──→ COMPLETED
  ├────→ CANCELLED
  └────→ SUPERSEDED
```

No transition returns a terminal workflow to OPEN.

Current condition is derived while OPEN and MAY include at least:

```text
READY
AWAITING_APPROVAL
AWAITING_ACTIVATION
AWAITING_EVIDENCE
UNRESOLVED
BLOCKED
MATERIALITY_PAUSE
EXECUTION_FAILED
```

Conditions are derived from immutable intent, authoritative workflow history, and current authoritative RIL state/evidence. Ordinary condition changes do not themselves create workflow events.

## Completion

Completion is determined by the workflow primitive from immutable bounded intent, authoritative state, and bound normative operation results.

Completion means that one of the workflow's defined successful terminal outcomes has been reached. It does not require every operation in the advisory initial plan to execute.

Conditional branches may therefore complete naturally, e.g. a workflow whose intent is `reconcile and admit if accepted` may complete after a valid rejection disposition because conditional admission is no longer applicable.

Once the primitive proves completion, it appends `core/completed`. Completion cannot be declared by an adapter or operator.

`core/completed` seals the terminal result irreversibly.

## Cancellation

Ordinary cancellation belongs to the workflow's requesting operator.

The protected root operator may cancel any OPEN workflow directly.

Cancellation:

- terminates outstanding workflow intent;
- does not delete the workflow or history;
- does not reverse completed normative operations;
- is durably attributable to the authenticated cancelling operator;
- grants no authority over operations named by the workflow.

Cancellation is terminal. A cancelled workflow cannot be reopened.

Fresh intent to pursue substantially the same objective creates a new workflow using a `resumes:` relationship.

## Revision and supersession

Material revision of bounded intent creates a new immutable successor workflow.

One workflow identity always means one immutable bounded intent.

Revision is an atomic cross-workflow primitive transition:

```text
workflow:old
   ↓
core/superseded
  successor: workflow:new

workflow:new
  supersedes: workflow:old
```

Either the successor creation and predecessor terminal supersession both become authoritative, or neither does.

There is no valid intermediate state in which both predecessor and successor are OPEN due solely to partially persisted revision.

`supersedes:` means revised intent. `resumes:` means fresh intent to pursue substantially the same objective after cancellation. A later related workflow may use a non-authoritative relationship such as `follows:` where useful.

No relationship inherits approval, activation, authority, or stale execution state.

## Execution failure and retry

Execution failure is a condition, not a terminal lifecycle state:

```text
lifecycle: OPEN
condition: EXECUTION_FAILED
```

A failed attempt is durably recorded when persistence is materially useful.

Retrying the same materially unchanged in-scope objective remains covered by the durable workflow intent when:

- the operation remains within immutable intent;
- material semantics have not changed;
- authoritative state remains compatible;
- applicable authority/evidence independently validates;
- no materiality condition requiring acknowledgement exists.

Retry preserves intent, not authority evidence. Approval, activation, authentication, or other evidence is reusable only if its own normative contract says it remains valid.

A materially different recovery path is not a retry; the workflow becomes blocked pending revision or cancellation.

## Materiality pause

The agent/orchestrator must pause before the next consequential operation when newly discovered information would reasonably be expected to affect the human's original decision.

The workflow records a normative materiality-pause fact and projects:

```text
lifecycle: OPEN
condition: MATERIALITY_PAUSE
```

A valid acknowledgement may restore progression within unchanged scope. If the desired operation changes, a successor workflow is required. If the operation becomes normatively invalid, acknowledgement cannot override the failure.

## Underlying operation binding

Operations performed as part of a workflow carry explicit workflow context at invocation time.

Workflow context grants no authority. It establishes why the independently authorized operation is being performed and which bounded intent it is intended to advance.

Successful operation progression is recorded by binding the exact normative result artifact into workflow history, e.g.:

```text
workflow-event:<id>
  workflow: workflow:<id>
  operation: reconciliation
  result: disposition:<id>
```

The workflow primitive validates that the referenced result:

- exists and is valid;
- concerns the workflow subject;
- satisfies an in-scope operation/branch of immutable intent.

Workflow events bind existing normative evidence together; they do not duplicate or reinterpret it.

Operations performed without workflow context cannot be retroactively adopted into a workflow as though they were performed under that bounded intent.

## Event writer boundary

Only the deterministic workflow primitive may append normative workflow events.

CLI, Human ↔ Agent, and future automation adapters request workflow transitions. They do not directly manufacture authoritative workflow history.

Events may preserve requester, agent, underlying-operation, and other provenance without making those actors authoritative writers.

## Event identity

A `workflow-event:<id>` commits to the complete normative workflow-history fact, including as applicable:

- workflow identity;
- event type;
- predecessor/history binding;
- normative result references;
- semantic transition payload;
- authenticated operator act required for the transition.

Optional agent/runtime diagnostics are non-normative provenance and need not affect event identity.

## Linear authoritative history

Each workflow uses one linear domain-local hash chain.

Every append names the expected current head. Concurrent append attempts against the same predecessor cannot both become authoritative.

```text
append B expecting A → accepted
append C expecting A → STALE_WORKFLOW_HEAD
```

The losing request may re-read workflow state and retry only if its requested transition remains valid.

This ordering is local to one workflow and does not introduce a global cross-domain project chronology.

## Authoritative head

`workflow:<id>` identifies immutable intent. A separately maintained authoritative head identifies the current end of its event chain.

The workflow primitive owns atomic head advancement and validates the expected predecessor.

The head is an append/concurrency boundary, not a replacement workflow identity.

## Core and extension event vocabulary

Workflow history uses a closed normative core plus extensible informational events.

Core state-affecting events SHALL include at least:

```text
core/operation-result-bound
core/attempt-failed
core/materiality-paused
core/materiality-acknowledged
core/cancelled
core/superseded
core/completed
```

Only contract-defined core events may affect workflow semantics, lifecycle, intent, authority, deterministic progression, or normative condition projection.

Namespaced extension events MAY preserve diagnostics and observations, but are informational only. Unknown informational extension events may be preserved/ignored safely and cannot extend workflow semantics.

## Workflow conflicts

Workflow artifacts are not locks or reservations.

RIL SHOULD detect known overlap/conflict between OPEN workflows proactively, but authoritative project state remains decisive.

Before every consequential operation the workflow path revalidates authoritative state. If another workflow or operation has made the intended transition stale or materially changed its meaning, the affected workflow remains OPEN and projects a blocking condition rather than silently adapting intent.

## Root override boundaries

Protected root may:

- continue any OPEN workflow;
- cancel any OPEN workflow;
- acknowledge any MATERIALITY_PAUSE.

These overrides affect workflow-control permissions only.

Root override MUST NOT:

- expand immutable intent;
- revise a workflow in place;
- satisfy proposal approval automatically;
- manufacture Steward authorization or activation;
- override normative operation failure;
- reverse completed operations.

## Non-authority invariant

A workflow or workflow event can record intent, context, progression, result bindings, cancellation, acknowledgement, blocking, and completion.

Neither can grant or substitute for:

- administrative proposal approval;
- protected-root ceremonies other than the workflow-control overrides explicitly defined here;
- Steward authorization;
- Steward activation;
- reconciliation judgment;
- admission authority;
- protocol mutation authority.

## Reconciliation findings

This D1 design was reconciled against accepted R1–R15, accepted R16A, and draft R16B.

Result: **SEMANTIC PASS; ONE CROSS-ADAPTER INTEGRATION AMENDMENT REQUIRED.**

No conflict was found with the authority model, proposal/approval/apply separation, activation model, reconciliation/admission separation, Canon boundary, repair/recovery model, or R16B interaction rules.

### Integration finding I1 — R16A workflow surface

The base RIL orchestrator contract requires that no semantic operation exist only as conversational behavior or only as TTY interaction. D1 introduces durable workflow creation, inspection, continuation, cancellation, revision/supersession, and materiality acknowledgement as accepted primitive-level operations.

Accepted R16A does not currently expose a workflow resource or commands for these operations.

Therefore D1 cannot be considered fully integrated until R16A is amended with an explicit workflow CLI surface, or an equally explicit accepted cross-adapter mechanism is defined that satisfies the no-conversation-only-semantics invariant.

The exact R16A workflow command topology is intentionally not invented by this contract and requires a focused CLI amendment decision.

## D1 resolution status

The durable workflow primitive/artifact design itself is complete and accepted by this dependency contract.

R16B dependency D1 is **DESIGN-RESOLVED / INTEGRATION-PENDING I1**.

After I1 is resolved and R16A reconciliation passes, D1 may be marked fully resolved in R16B.