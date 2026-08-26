# Project Chat-Transition Amendment

Status: **Normative v3 amendment**

Amends:

- `reasoning-distiller-project-integration/1`

Contract:

- `reasoning-distiller-project-chat-transition/3`

Supersedes:

- `reasoning-distiller-project-chat-transition/2`.

## Purpose

Add an explicit proactive chat-transition responsibility to interactive Project-hosted role work without changing repository role authority, RIL activation, production Distiller evidence, or canonical project-knowledge semantics.

The governing rules are:

> **When the current role reaches a meaningful chat boundary, tell the user before silently continuing across it.**
>
> **Within the current bounded work unit, emit required bounded handoffs proactively. When that work unit reaches its defined completion condition, emit terminal status or handoff and stop before beginning another work unit.**
>
> **Resolve interactive coordination controls from the live coordination control ref independently of immutable semantic candidates or task branches.**

The reminder and stop behavior exists to preserve semantic role separation, useful context isolation, and explicit scope boundaries. It is coordination behavior only.

## Interactive coordination control plane

Interactive coordination policy and semantic implementation evidence are distinct revision domains.

Unless a task-specific governing repository contract explicitly designates another coordination control ref, the coordination control ref is the repository's live `main` branch.

Before consequential interactive repository work, and again at each new role activation or bounded-work-unit activation, the active role MUST:

1. resolve the exact current coordination control ref and record it as `coordination_revision`;
2. read its current role directive and this amendment from that exact coordination revision;
3. resolve semantic candidates, evidence refs, implementation branches, review inputs, and reconciliation inputs independently; and
4. preserve both identities when the coordination revision differs from the semantic or candidate revision.

A role MUST NOT use a candidate, evidence, or work-branch copy of a role directive or this amendment as the interactive coordination control merely because that ref is the semantic basis of the task.

A later coordination revision may govern how an interactive role coordinates work around an older immutable candidate without modifying that candidate. Coordination policy does not become candidate evidence merely because it governs the surrounding workflow.

If the coordination control ref cannot be resolved, or the task requires a different control ref but that ref cannot be established from governing evidence, the coordination revision is unknown and consequential continuation MUST stop or narrow rather than silently falling back to a candidate/work ref.

This separation MUST NOT:

- mutate immutable candidate bytes;
- rewrite or broaden a fixed production evidence set;
- change semantic identity or canonical standing;
- manufacture role authority, authorization, or accepted activation evidence; or
- cause a candidate to be treated as if it were rebased onto the coordination revision.

## Bounded work unit

A **bounded work unit** is the currently selected unit of consequential work whose completion is meaningful under the governing workflow or explicit task scope. Its label is not semantically significant.

Examples include, when actually selected by the governing workflow or task:

- an implementation phase such as `P3`;
- a proposal or review stage such as `Stage 2`;
- an experimental gate such as `Gate 0`;
- one GitHub issue;
- one experiment;
- one proposal;
- one reconciliation;
- one admission operation;
- one migration step;
- one explicitly scoped implementation or review task.

A bounded work unit may contain multiple role-bounded activations, independent reviews, remediation cycles, evidence-producing operations, or reconciliations. Those internal boundaries do not by themselves create a new work unit.

Resolve the current bounded work unit from the strongest applicable evidence, in this order:

1. a task-specific governing repository contract, accepted plan, or other authoritative workflow artifact that explicitly selects the current unit;
2. an explicit user-selected scope, constrained by any narrower governing repository boundary;
3. a durable bounded handoff or exact next-action artifact that explicitly identifies the current unit;
4. when only one consequential action is selected and no larger unit is established, that action itself.

Do not infer a broader work unit from naming conventions, adjacent phases, repository layout, remembered plans, prior chats, or the mere existence of an apparent successor step.

If the current work-unit boundary cannot be established with sufficient confidence for consequential continuation, keep the boundary unknown and stop or narrow the operation rather than inventing scope.

## Internal activation and terminal boundary

An **internal activation** is a role-, evidence-, review-, remediation-, or execution-bounded operation performed as part of the current bounded work unit.

A **terminal boundary** is reached when the current bounded work unit satisfies its governing completion condition, or when a governing contract requires the unit to terminate or block.

A role MUST distinguish an internal activation boundary from a terminal work-unit boundary.

Crossing an internal activation boundary may require a bounded handoff and fresh or isolated context, but it does not authorize beginning work outside the current bounded work unit.

When the terminal boundary is reached, the active interactive role MUST:

1. state the work unit's terminal status;
2. provide a compact terminal bounded handoff or completion record when useful for future continuation;
3. identify any unresolved blocker or required future receiving role when applicable;
4. stop before beginning a sibling, successor, next phase, next gate, next issue, or other work unit.

The assistant MUST NOT require the user to separately request each bounded handoff inside an established work unit. Meaningful internal boundaries proactively trigger the handoff behavior defined by this amendment.

A successor work unit may begin only after it is explicitly selected by a new user request or by a governing instruction that itself authorizes and selects that successor scope. Completion of the current work unit alone never selects the next one.

## Chat-boundary conditions

A role SHOULD identify a chat boundary when one or more of the following materially applies:

1. the next consequential work belongs to another role;
2. a proposal or review workflow is moving to a stage that requires semantic independence;
3. an independent review should not inherit conclusions or assumptions from the current conversation;
4. accumulated conversation context would materially bias a fresh activation;
5. the active role has completed the artifact, decision, candidate, reconciliation, or other result that the next role must receive;
6. the work is changing from analysis or review into a separately bounded implementation or governed operation;
7. another repository contract requires a distinct activation or evidence boundary.

A new chat SHOULD NOT be recommended merely because the conversation is long or because a minor subtask changed. Ordinary continuation inside the same role, scope, authority posture, evidence boundary, and bounded work unit should remain in the current chat.

## Required reminder behavior

When a meaningful chat boundary is reached inside the current bounded work unit, the active interactive role SHOULD:

1. explicitly state that a chat boundary has been reached;
2. identify why continuing in the same chat would weaken role separation, independence, or evidence boundaries;
3. identify the current bounded work unit and whether the boundary is internal or terminal;
4. identify the exact `coordination_revision` governing the interactive role;
5. identify the semantic/candidate/evidence revision separately when distinct;
6. recommend the appropriate next role;
7. recommend a fresh chat or, when stronger independence is required, an isolated Project workspace/context;
8. provide a compact bounded handoff suitable for starting that activation.

A reminder SHOULD occur at the transition point, not repeatedly throughout ordinary same-role work.

## Bounded handoff

The handoff SHOULD include, when applicable:

- repository;
- exact `coordination_revision` and coordination control ref;
- semantic, candidate, evidence, implementation, or reconciliation revision when distinct;
- current bounded work unit;
- whether the handoff is internal or terminal;
- exact problem and constraints;
- current role and completed scope;
- completed artifact, result, candidate, disposition, or decision input;
- governing contracts and evidence the receiving role requires;
- authority evidence when the receiving operation depends on it;
- unresolved uncertainties and disagreements;
- receiving role and requested scope;
- exact next action the receiving activation should perform;
- for a terminal handoff, the condition establishing completion or block and an explicit stop before any successor unit.

The handoff is coordination metadata. It does not create project authority, canonical knowledge, accepted RIL activation evidence, or authorization for a successor work unit.

## Role-directive integration

Interactive Project hosting of repository roles MUST preserve the role-specific directives.

The current role directives define their local reminder behavior:

- `agents/architect/DIRECTIVE.md`;
- `agents/engineer/DIRECTIVE.md`;
- `agents/steward/DIRECTIVE.md`;
- `agents/distiller/DIRECTIVE.md`.

Those directives operate under this amendment's coordination-revision, bounded-work-unit continuation, and terminal-stop rules when used interactively in a Project workspace.

A role transition must not silently broaden the outgoing or incoming role's authority or the selected work-unit scope.

## Distiller production exception

The production Distiller boundary remains controlled by `docs/operations/PRODUCTION_INVOCATION_CONTRACT.md`.

Chat-transition reminders, coordination-revision selection, and bounded-work-unit coordination MUST NOT:

- enter the fixed production evidence set merely because they exist in Project context;
- be inserted into the prepared production activation bundle unless independently authorized as explicit evidence by the governing process;
- appear inside raw Distiller candidate bytes;
- appear inside the Distiller structured output contract;
- cause the model-side production activation to search for or infer additional project context;
- broaden or sequence production work beyond the explicit invocation contract.

For production `rd-distill`, any chat-transition reminder, coordination-revision selection, or work-unit stop/continuation decision belongs to the surrounding interactive coordination layer before or after the model activation.

## Relationship to role activation

A chat-transition reminder, coordination revision, bounded work-unit label, chat title, handoff, fresh chat, isolated Project, or role label is not proof of registered role identity, role authorization, or accepted RIL activation.

Where governed role authority is required, the applicable repository role, authorization, and activation contracts remain controlling.

A bounded work unit limits coordination scope; it does not grant authority to perform every operation that could occur inside that scope.

## Conformance

A Project-hosted workflow conforms to this amendment when:

1. interactive coordination controls are resolved from the exact live coordination control ref independently of semantic/candidate refs;
2. candidate/work-branch copies of role directives are not silently substituted for the live coordination controls;
3. the current bounded work unit is established from explicit governing or task evidence rather than naming inference;
4. meaningful cross-role, review, remediation, evidence, execution, or independence boundaries inside that unit cause proactive user-facing bounded handoffs;
5. the user does not need to separately request each required internal handoff;
6. same-role ordinary continuation does not produce noisy or unnecessary chat-change prompts;
7. each consequential handoff identifies the coordination revision, distinct semantic/candidate revision when applicable, current work unit, boundary type, next role/context, and exact next action when applicable;
8. internal handoffs do not silently expand the selected work-unit scope;
9. terminal completion or block produces a terminal status or handoff and a stop before any successor work unit begins;
10. completion of one work unit is not treated as selection or authorization of the next;
11. reminders, coordination refs, and work-unit labels do not manufacture authority or activation evidence;
12. independent review receives stronger context isolation when required;
13. production Distiller candidate bytes and structured output remain free of chat-navigation prose;
14. production Distiller evidence remains fixed by its governing invocation contract.
