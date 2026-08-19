# R16B-D1 — Durable Workflow Primitive and Artifact Design Contract

Status: **Normative dependency design contract — accepted; integration resolved**

Contract: `reasoning-distiller-workflow-design/1`

Depends on: accepted R1–R15 primitive/orchestration contracts, accepted amended R16A `reasoning-distiller-ril-cli-design/1`, and draft R16B `reasoning-distiller-ril-human-agent-design/1`.

Implementation status: **not authorized by this document alone.**

## Purpose

This contract resolves R16B dependency D1 by defining the durable workflow primitive/artifact model used to preserve bounded human intent across sessions, interruptions, agents, and execution attempts.

A workflow records authenticated bounded intent and progression. It grants no operator authority, Steward authority, approval, activation, semantic authority, admission authority, or resource lock.

## Core model

A workflow consists of an immutable content-addressed workflow definition, an immutable append-only workflow-event history, separately maintained history and normative heads, and deterministic projection of lifecycle/current condition.

`workflow:<id>` always identifies exactly one immutable bounded intent. Its identity never advances with workflow history.

## Workflow definition and authenticated creation

The immutable definition contains normative bounded intent plus an advisory initial execution plan. The plan never expands intent and may become stale/recomputed without changing authorized bounded intent.

The normative creation payload includes every field affecting workflow semantics, including subject/scope, permitted/conditional operations, terminal conditions, execution mode, continuation policy, materiality-acknowledgement policy, and relationship fields such as `supersedes:` or `resumes:` where applicable.

Workflow creation is an authenticated operator act, not proposal → approval → apply. Any enabled operator may create a workflow representing that operator's bounded intent; creation itself cannot authorize execution of named operations.

Authentication MUST bind the operator to the exact canonical creation payload. Identity uses a two-stage digest: hash the canonical payload; authenticate that digest; hash payload plus authentication binding as `workflow:<id>`. Thus workflow identity commits to both exact bounded intent and the authenticated act establishing it.

## Continuation and materiality policies

Continuation policy SHALL support at least `requester-only`, `any-enabled-operator`, and explicit operator set. Default is requester-only. Protected root may request continuation of any OPEN workflow. Continuation permission grants no downstream authority.

Materiality acknowledgement is a distinct policy, default requester-only. Protected root may acknowledge any `MATERIALITY_PAUSE`. Acknowledgement restores sufficiently informed intent only within immutable scope and cannot revise intent, expand scope, or override missing/failed authority or validation.

## Execution mode

The definition specifies `operator-driven` or `auto-advance`; default is operator-driven. Operator-driven requires a permitted continuation request before consequential advancement. Auto-advance creates durable eligibility for autonomous continuation whenever the next in-scope operation becomes valid, but prescribes no daemon/scheduler architecture and grants no authority.

Every underlying operation independently validates its normal requirements. Materiality pause suspends auto-advance; valid acknowledgement restores eligibility under unchanged scope.

## Lifecycle, condition, and completion

Normative lifecycle is `OPEN`, `COMPLETED`, `CANCELLED`, or `SUPERSEDED`; terminal states are irreversible. OPEN condition MAY include `READY`, `AWAITING_APPROVAL`, `AWAITING_ACTIVATION`, `AWAITING_EVIDENCE`, `UNRESOLVED`, `BLOCKED`, `MATERIALITY_PAUSE`, and `EXECUTION_FAILED`.

Conditions are derived from immutable intent, authoritative workflow history, and current authoritative RIL state/evidence. Ordinary condition changes do not themselves create events.

Completion is semantically proved by the workflow primitive from bounded intent, authoritative state, and bound normative results. Once proved, `core/completed` seals the terminal result. Completion cannot be declared by an adapter/operator.

## Cancellation, revision, and retry

Requester may cancel their own OPEN workflow; protected root may cancel any OPEN workflow. Cancellation terminates outstanding intent without deleting history or reversing completed operations and is durably attributable to the authenticated cancelling operator. Fresh intent after cancellation creates a new workflow using `resumes:` where applicable.

Material revision creates a new immutable successor and atomically appends `core/superseded` to the predecessor. Either both successor creation and predecessor supersession become authoritative or neither does. `supersedes:` means revised intent; `resumes:` means fresh intent after cancellation. Relationships inherit no approval, activation, authority, or stale execution state.

Execution failure is an OPEN condition, not terminal. Retry of materially unchanged in-scope intent remains covered only while scope, semantics, authoritative state, and independent authority/evidence remain valid and no unacknowledged materiality condition exists. Intent persistence does not imply evidence persistence.

## Materiality pause and underlying operation binding

The agent/orchestrator must pause before the next consequential operation when newly discovered information would reasonably be expected to affect the human's original decision. A normative materiality-pause fact is recorded and condition becomes `MATERIALITY_PAUSE`.

Operations performed as part of a workflow carry explicit workflow context. Context grants no authority; it records why the independently authorized operation is being performed and which bounded intent it advances. Successful progression binds exact normative result artifacts into workflow history after validation of existence, subject, and in-scope applicability.

Operations performed without workflow context cannot be retroactively adopted as though performed under that durable intent.

## Event writer, identity, and vocabulary

Only the deterministic workflow primitive may append normative workflow events. Adapters request transitions; they do not manufacture authoritative history.

A `workflow-event:<id>` commits to the complete normative workflow-history fact, including workflow identity, event type, predecessor/history binding, normative result references, semantic transition payload, and authenticated operator act where required. Optional runtime diagnostics are non-normative.

Core events SHALL include at least:

```text
core/operation-result-bound
core/attempt-failed
core/materiality-paused
core/materiality-acknowledged
core/cancelled
core/superseded
core/completed
```

Only contract-defined core events affect workflow semantics. Namespaced extension events may preserve diagnostics/observations but cannot affect lifecycle, intent, authority, deterministic progression, or normative condition projection.

## Linear history, dual heads, and concurrency

Each workflow has one linear domain-local event chain. Workflow identity remains immutable while head pointers identify accumulated history.

The model distinguishes:

```text
history_head    = most recently appended workflow event
normative_head  = most recent core event affecting workflow semantics
```

Informational extension events advance `history_head` but not `normative_head`. The primitive atomically serializes informational appends after the current physical history head without requiring informational writers to predict it.

Normative transitions bind the expected `normative_head` plus exact authoritative external state/artifacts material to that transition. The primitive then appends the core event after the current physical `history_head`. Intervening informational events therefore do not invalidate normative acts or gain accidental semantic concurrency effects.

Competing normative transitions against the same semantic predecessor cannot both become authoritative. A stale request must reread and reevaluate; it is not automatically rebased or retried where doing so would alter reviewed/authenticated intent.

This ordering is local to one workflow and introduces no global cross-domain chronology.

## Workflow conflicts

Workflows are not locks/reservations. RIL SHOULD detect known overlap/conflict between OPEN workflows proactively, but authoritative project state remains decisive. Before each consequential operation, authoritative state is revalidated. Stale/materially changed intent blocks rather than silently adapting.

## Root override boundaries

Protected root may continue any OPEN workflow, cancel any OPEN workflow, and acknowledge any `MATERIALITY_PAUSE`. These are workflow-control overrides only. Root cannot expand immutable intent, revise in place, synthesize proposal approval, manufacture Steward authorization/activation, override normative failure, or reverse completed operations.

## Non-authority invariant

Workflow artifacts/events may record intent, context, progression, result bindings, cancellation, acknowledgement, blocking, and completion. They cannot grant/substitute administrative approval, Steward authorization/activation, reconciliation judgment, admission authority, or protocol mutation authority.

## R16A CLI integration

The accepted amended R16A contract exposes all D1 primitive-level workflow operations through the first-class `ril workflow` family:

```text
ril workflow
ril workflow list [--all]
ril workflow show <workflow> [--depth=0|1|2]
ril workflow create [<file|->] [--auth <file|->]
ril workflow continue <workflow>
ril workflow cancel <workflow> [--auth <file|->]
ril workflow revise <workflow> [<file|->] [--auth <file|->]
ril workflow acknowledge <workflow> <workflow-event> [--auth <file|->]
```

The CLI amendment preserves D1 semantics: canonical structured creation/revision input; exact payload authentication; additional prospective confirmation for auto-advance; continuation to the next meaningful boundary without manufacturing prerequisites; risk-sensitive cancellation; exact-state atomic revision; exact-pause acknowledgement; dual-head normative concurrency; and control-return output that distinguishes completed, stopped, and remaining action.

Workflow inspection uses standardized R16A depth semantics. Depth 0 presents the current authoritative view and normative head; depth 1 adds ordered event context and distinguishes normative/history heads; depth 2 expands referenced normative evidence. `workflow-event:<id>` is directly inspectable through generic typed-reference inspection.

## Reconciliation findings

This D1 design is reconciled against accepted R1–R15, amended accepted R16A, and draft R16B.

Result: **PASS.**

The previous integration finding I1 is **RESOLVED** by the accepted R16A workflow CLI amendment. No workflow semantic operation is conversation-only or TTY-only. No conflict was found with the authority model, proposal/approval/apply separation, activation model, reconciliation/admission separation, Canon boundary, repair/recovery model, or R16B interaction rules.

## D1 resolution status

The durable workflow primitive/artifact design is complete, accepted, and cross-adapter integrated.

R16B dependency D1 is **RESOLVED**.
