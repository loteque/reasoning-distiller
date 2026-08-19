# R16B — RIL Human ↔ Agent Interaction Design Contract

Status: **Normative design contract — accepted**

Contract: `reasoning-distiller-ril-human-agent-design/1`

Depends on: accepted R1–R15 primitive/orchestration contracts; amended R16A `reasoning-distiller-ril-cli-design/1`; accepted R16B-D1 `reasoning-distiller-workflow-design/1`; accepted R16B-D2 `reasoning-distiller-provenance/1`; accepted R16B-D3 `reasoning-distiller-proposal-revalidation/1`.

Implementation status: **not authorized by acceptance alone; implementation follows the R16 UX implementation/conformance gates.**

## Purpose

R16B defines Human ↔ Agent interaction over the same Reasoning Distiller orchestration and deterministic primitive semantics exposed by R16A.

The Human ↔ Agent adapter is a peer adapter to the CLI, not an agent that must simulate shell use. R16A and R16B share normative operations, artifacts, results, authority boundaries, and lifecycle semantics; they need not share invocation mechanics or presentation.

Conversation itself grants no authority and creates no semantic operation unavailable through the accepted RIL boundary.

## Core interaction model

The agent is a proactive lifecycle guide. When relevant to the active human purpose, it MAY inspect project state, identify blockers and pending work, explain lifecycle state, prepare safe next steps, create non-authoritative proposals, and recommend operations.

The agent MUST NOT interpret the existence of an actionable next step as authorization to perform it.

Read-only investigation is purpose-bounded. The agent MAY autonomously inspect RIL state, durable artifacts, project evidence, and other available project material reasonably relevant to the active request, workflow, blocker, diagnosis, or materiality investigation. Read access does not authorize unrelated exploration.

## Conversational intent

R16B uses context-bound conversational intent. Short affirmations such as `yes`, `proceed`, or `do it` are actionable only when they refer to exactly one immediately preceding, clearly stated operation or one explicitly enumerated closed set of operations.

Conversational intent is narrowly scoped. It does not authorize adjacent operations, resolve ambiguity, or substitute for normative approval, Steward authorization, activation, or authentication.

For broad or high-level requests, the agent MAY infer a likely desired workflow from project state, but before consequential multi-stage execution it MUST state the bounded operational interpretation and obtain intent for that explicit chain. Vague language MUST NOT become open-ended delegation.

A response containing affirmation plus a material modification is a revision request, not approval. The agent MUST NOT approve the previously presented proposal; it prepares the revised proposal or proposal set and presents it again.

## Proposal preparation

Proposal creation is non-authoritative. The agent MAY proactively create immutable proposal artifacts when useful without first obtaining permission merely to formalize a possible transition.

An unapproved proposal has no mutation effect and grants no authority.

The agent MAY autonomously improve understanding and preparation, including diagnosis, investigation of safe alternatives, and preparation of replacement proposals. It MUST NOT autonomously rewrite human intent.

## Conversational approval

Human approval is always approval of an identified immutable proposal, never merely approval of an agent paraphrase.

Before requesting approval, the agent MUST provide a layered presentation containing:

- the material human-readable effect;
- consequential authority implications;
- the exact immutable proposal reference;
- access to the complete normative proposal.

Protected and exceptional operations retain their stronger normative confirmation ceremonies.

Immediately before converting affirmative human intent into an approval artifact, the adapter MUST invoke the accepted D3 proposal-applicability revalidation against the exact immutable proposal and current authoritative project state/evidence.

Only `APPLICABLE` permits normal approval creation to proceed. `STALE`, `BLOCKED`, or `INVALID` MUST NOT produce approval. Revalidation is read-only, non-authoritative, attempt-scoped, and protected against validation/commit races. It MUST NOT rewrite or rebase the proposal.

Apply-time primitive validation remains independently mandatory and authoritative even after successful pre-approval revalidation.

Approval and application remain distinct normative operations. One human response MAY establish intent for both only when application was prospectively disclosed, for example `Approve proposal:X and apply the authorized change?`. If the agent asks only for approval, approval does not imply application intent.

The agent MAY present multiple proposals as one review set. One human response MAY express approval intent for a closed, explicitly enumerated set, but each proposal is independently revalidated and receives its own independently bound approval artifact. `Approve all` never creates open-ended authority.

## Cross-session proposal continuity

Proposal continuity belongs to durable RIL artifacts, not conversational continuity. Any RIL-aware agent MAY resume from an immutable proposal, but MUST independently retrieve and validate it, reconstruct the required layered approval presentation, and obtain fresh human approval.

Another agent's assertion that a proposal was already reviewed is not authority.

Conversational and agent-to-agent handoff is useful orientation only. Any fact affecting a normative operation MUST be independently reconstructed from authoritative project state and durable evidence. If analysis must survive as normative input, it must be persisted through an appropriate accepted evidence/artifact mechanism rather than chat history.

## Operator identity

Conversational operator identity SHOULD be resolved from validated authentication/identity evidence when an accepted mechanism is available. If an unambiguous binding to a registered operator cannot be established, the agent MUST ask rather than infer operator identity from a conversational claim.

Stable project operator identity remains distinct from authentication evidence.

## Steward activation

Role registration, role authorization, and current invocation activation remain distinct.

The agent MAY discover the authorized Steward role and propose acting under it, but authorization itself never establishes activation. Every authority-bearing invocation MUST satisfy the accepted activation-evidence contract.

Activation lifetime and scope are properties of validated activation evidence, not the conversation. Every authority-bearing invocation independently validates that its evidence applies. Conversation/session continuity MUST NOT create persistent Steward activation.

## Reconciliation interaction

A validly activated reconciliation Steward independently exercises the semantic authority assigned to that role. Human operators decide which durable role may hold reconciliation authority; R16B MUST NOT add human approval of every semantic judgment as a second reconciliation authority.

The Steward agent MUST make the disposition, material evidence, conflicts, and uncertainty transparent and inspectable.

Material semantic uncertainty MUST produce an explicit unresolved/blocked disposition rather than a guessed judgment or implicit authority transfer to the human. The agent SHOULD identify the missing, conflicting, or ambiguous evidence required for a defensible subsequent reconciliation.

Humans and agents may improve the evidence state; a human cannot simply dictate the semantic conclusion unless independently acting through a valid authorized Steward mechanism.

## Admission interaction

A validly activated admission Steward MAY perform admission according to the accepted admission contract without an additional conversational human-confirmation requirement. R16B MUST NOT introduce a second admission authority layer.

The agent MUST clearly report the admitted candidate, resulting admission receipt, and material Canon effects. Storage verification remains a distinct operation and MUST NOT be silently folded into admission.

## Bounded lifecycle chaining

Distinct normative operations MAY be chained when prospectively stated human intent explicitly covers the chain and each stage independently satisfies its own authority, activation, evidence, and validation requirements.

For example, `reconcile this candidate and admit it if accepted` permits reconciliation followed by conditional admission. Intent covering only reconciliation stops after reconciliation.

A broad request such as `process this candidate` has no magic protocol meaning. Before consequential multi-stage execution, the agent MUST state its bounded interpretation and obtain context-bound intent for that defined chain.

## Interruption and materiality

Bounded intent MAY survive ordinary pauses and resumptions, but its scope is immutable. The agent MAY satisfy observational or mechanically necessary prerequisites already implied by the authorized workflow.

If continuation requires a new mutation, new human approval, materially different evidence, a different authority holder, a materially changed operation, or expansion beyond the stated chain, the agent MUST stop and obtain the new intent or authority required.

The agent MUST pause before the next consequential operation when newly discovered information would reasonably be expected to affect the human's original decision to authorize that operation or workflow. Routine or immaterial discoveries do not require interruption.

A human MAY explicitly acknowledge newly surfaced material information and continue an otherwise valid bounded workflow. For durable workflows, acknowledgement is recorded through the accepted D1 workflow mechanism. Acknowledgement cannot override normative invalidity, failed validation, missing authority, or a safety invariant.

If the newly surfaced information changes the desired operation, workflow revision rules apply instead.

## Durable workflow intent

Ordinary conversational intent is transient. Cross-session continuation of bounded human intent requires the accepted D1 durable workflow artifact.

A workflow records authenticated bounded intent and progress; it grants no authority. A later agent MAY resume only within its immutable scope and only after independently revalidating authoritative project state and every approval, Steward authorization, activation, evidence, or other requirement applicable to the next operation.

Creation of durable workflow intent requires prospective disclosure. If persistence was not disclosed, conversational intent MUST NOT silently become durable project intent.

Workflow lifecycle, continuation, cancellation, supersession/revision, materiality acknowledgement, retry, auto-advance, concurrency, event binding, and root workflow-control overrides are governed by `reasoning-distiller-workflow-design/1`.

In particular:

- workflow identity identifies one immutable authenticated bounded intent;
- workflow events are append-only and written by the deterministic workflow primitive;
- workflows do not lock or reserve project state;
- workflow continuation permission is not downstream authority;
- terminal lifecycle states are irreversible;
- material workflow revision creates an immutable successor and atomically supersedes the predecessor;
- workflow history binds exact normative operation results rather than duplicating them;
- auto-advance creates execution eligibility, not authority;
- root workflow-control overrides cannot expand intent or bypass underlying normative requirements.

When a workflow becomes blocked, the agent MAY diagnose the condition, identify which original intent remains valid, investigate alternatives, prepare non-authoritative replacement proposals, and recommend a revised bounded workflow. Material scope changes require fresh human intent.

## Operational provenance

Where available and useful, durable operational provenance MAY record agent/runtime identity, model/provider information, session/run identifiers, tool/software versions, human-interface context, and bounded non-secret environment metadata under `reasoning-distiller-provenance/1`.

Provenance is immutable, content-addressed observational evidence:

```text
provenance:<id>
  subject: <canonical typed reference>
  ...operational context...
```

The subject binding lives inside the provenance object and participates in its identity. Existing normative subject artifacts are not rehashed merely to add or correct provenance.

Corrections/enrichment create new provenance artifacts. Provenance IDs are not normative identity anchors and cannot satisfy operator approval, authentication, Steward authorization, activation, reconciliation authority, admission authority, or workflow authority.

Operational provenance is outside Canon.

## Agent identity and authority

Agent/runtime identity is provenance, never authority.

Where useful, RIL may durably record producer/runtime/model/session/tool information, but none of those facts can authorize a normative operation or substitute for operator or Steward evidence.

## Read-only investigation

Read-only does not mean purpose-free. The agent may follow evidence relationships as deeply as reasonably required to fulfill the active request, workflow, blocker diagnosis, or materiality investigation, but MUST NOT use available read access as permission for unrelated exploration.

## Workflow conflict handling

Durable workflows express bounded intent, not resource ownership or reservation.

RIL SHOULD proactively surface known overlap/conflict between active workflows. Before every consequential operation, authoritative state is revalidated.

If another workflow or operation makes the intended transition stale or materially changes its meaning, the affected workflow becomes blocked rather than silently adapting its scope.

The agent MAY diagnose and prepare alternatives, but cannot autonomously rewrite durable human intent.

## Failure and retry

Execution failure does not itself terminate durable workflow intent. Where D1 permits retry, the same materially unchanged in-scope objective may be retried without fresh human intent after current state and all authority/evidence requirements independently revalidate.

Retry preserves intent, not authority evidence.

A materially different recovery path is a revision, not a retry.

## Agent-initiated materiality pause

An operation may remain technically valid while newly discovered information materially changes the human's understanding of its consequences.

In that case the agent MUST pause before the next consequential operation and explain the material information. This is preservation of informed intent, not agent veto authority.

A valid acknowledgement may restore informed intent within unchanged scope. Human acknowledgement cannot override normative invalidity.

## Control return

Whenever control returns to the human after consequential work, the adapter MUST make unambiguous:

- what completed and its material result;
- what requested work did not complete;
- durable artifacts created;
- the current boundary/state, such as completed, blocked, awaiting approval, awaiting activation, unresolved, or interrupted;
- the bounded next actions available.

The presentation MAY remain natural rather than mechanically printing fixed fields. Machine-readable adapters MAY expose the same information structurally.

The agent MUST NOT leave the human reasonably believing a consequential operation occurred when it merely prepared, proposed, approved, or attempted it.

## Cross-adapter invariants

R16A and R16B SHALL preserve the following common semantics:

1. CLI and Human ↔ Agent are peer adapters over the same RIL primitive/orchestration boundary.
2. Conversation creates no unique authority or semantic operation.
3. Proposal, approval, and apply remain distinct.
4. Approval binds to exact immutable proposals.
5. Every fresh approval creation uses the accepted D3 immediately-before proposal applicability revalidation.
6. Apply-time validation remains independently mandatory.
7. Protected/high-risk ceremonies are not weakened by conversational convenience.
8. Steward authorization and activation remain distinct.
9. Operators do not become reconciliation or admission semantic authorities merely by interacting with an agent.
10. Reconciliation and admission remain distinct even when bounded prospective intent chains them.
11. Admission does not imply Canon verification.
12. Durable workflow artifacts, not chat logs, carry cross-session bounded intent.
13. Operational provenance is observational and non-authoritative.
14. Canon remains governed by the accepted admission/storage contracts rather than conversation or provenance.
15. Presentation may differ by adapter; normative result meaning may not.

## Final reconciliation

R16B was finally reconciled against:

- accepted R1–R15 primitive/orchestration contracts;
- amended accepted R16A CLI design;
- accepted D1 durable workflow design;
- accepted D2 operational provenance design;
- accepted and integrated D3 proposal revalidation design.

Result: **PASS — NO OPEN DESIGN DEPENDENCIES OR SEMANTIC CONTRADICTIONS.**

### D1 — resolved

Durable workflow intent, event history, lifecycle/condition projection, continuation/cancellation/revision/materiality policies, auto-advance, root workflow-control overrides, and CLI peer-adapter surface are accepted and integrated.

### D2 — resolved

Operational provenance is accepted as a separate non-authoritative content-addressed artifact whose subject binding is inside the provenance payload. No provenance-binding artifact is required and normative subjects are not rehashed merely for provenance changes.

### D3 — resolved

The common proposal-applicability validator is accepted and integrated. Both R16B conversational approval and R16A `ril approve` use the same immediately-before revalidation semantics, while apply-time validation remains mandatory.

## Non-goals

R16B does not redesign R1–R15 primitive semantics; create a new operator, agent, or Steward authority class; make conversational context normative project state; allow an agent to invent approval/activation; make provenance Canon; define authentication providers; collapse reconciliation/admission; prescribe workflow monitoring infrastructure; or authorize implementation merely by accepting this design contract.

## Acceptance condition

R16B is **accepted**.

Implementation/conformance work SHALL preserve the accepted R1–R16B authority boundaries and demonstrate that the CLI and Human ↔ Agent adapters produce equivalent normative operations/results where they expose the same semantic action; durable workflow behavior conforms to D1; provenance conforms to D2; every fresh approval creation conforms to D3; and control-return behavior never obscures whether consequential action completed, stopped, or merely prepared.
