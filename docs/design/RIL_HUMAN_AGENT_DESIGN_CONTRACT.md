# R16B — RIL Human ↔ Agent Interaction Design Contract

Status: **Draft normative design contract — guided requirements complete; reconciliation dependencies open**

Contract: `reasoning-distiller-ril-human-agent-design/1`

Depends on: accepted R1–R15 primitive/orchestration contracts and accepted R16A `reasoning-distiller-ril-cli-design/1`.

Implementation status: **not authorized; R16B acceptance is blocked on the reconciliation dependencies recorded below.**

## Purpose

R16B defines the Human ↔ Agent interaction adapter over the same Reasoning Distiller orchestration and deterministic primitive semantics exposed by the R16A CLI.

The Human ↔ Agent adapter is a peer adapter to the CLI, not an agent that must simulate shell use. R16A and R16B share normative operations, artifacts, results, authority boundaries, and lifecycle semantics; they need not share invocation mechanics or presentation.

Conversation itself grants no authority and creates no semantic operation unavailable through the accepted RIL boundary.

## Core interaction model

The agent is a proactive lifecycle guide. When relevant to the active human purpose, it MAY inspect project state, identify blockers and pending work, explain lifecycle state, prepare safe next steps, create non-authoritative proposals, and recommend operations.

The agent MUST NOT interpret the existence of an actionable next step as authorization to perform it.

Read-only investigation is purpose-bounded. The agent MAY autonomously inspect RIL state, durable artifacts, project evidence, and other available project material reasonably relevant to the active request, workflow, blocker, diagnosis, or materiality investigation. Read access does not authorize unrelated exploration.

## Conversational intent

R16B uses context-bound conversational intent. Short affirmations such as `yes`, `proceed`, or `do it` are actionable only when they refer to exactly one immediately preceding, clearly stated operation or one explicitly enumerated closed set of operations.

Conversational intent is narrowly scoped. It does not authorize adjacent operations, resolve ambiguity, or substitute for a normative approval, Steward authorization, or activation requirement.

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

Immediately before converting an affirmative conversational response into an approval artifact, the R16B adapter MUST revalidate that the identified proposal remains applicable to authoritative project state. A proposal known to be stale MUST NOT be approved. Apply-time primitive validation remains independently mandatory and authoritative.

Approval and application remain distinct normative operations. One human response MAY establish intent for both only when application was prospectively disclosed, for example `Approve proposal:X and apply the authorized change?`. If the agent asks only for approval, approval does not imply application intent.

The agent MAY present multiple proposals as one review set. One human response MAY express approval intent for a closed, explicitly enumerated set, but each proposal receives its own independently bound approval artifact. `Approve all` never creates open-ended authority.

## Cross-session proposal continuity

Workflow continuity for proposals belongs to durable RIL artifacts, not conversational continuity. Any RIL-aware agent MAY resume from an immutable proposal, but MUST independently retrieve and validate it, reconstruct the required layered approval presentation, and obtain fresh human approval. Another agent's assertion that a proposal was already reviewed is not authority.

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

Material semantic uncertainty MUST produce an explicit unresolved/blocked disposition rather than a guessed judgment or implicit authority transfer to the human. The agent SHOULD identify the missing, conflicting, or ambiguous evidence required for a defensible subsequent reconciliation. Humans and agents may improve the evidence state; a human cannot simply dictate the semantic conclusion unless acting through an independently valid authorized Steward mechanism.

## Admission interaction

A validly activated admission Steward MAY perform admission according to the accepted admission contract without an additional conversational human-confirmation requirement. R16B MUST NOT introduce a second admission authority layer.

The agent MUST clearly report the admitted candidate, resulting admission receipt, and material Canon effects. Storage verification remains a distinct operation and MUST NOT be silently folded into admission.

## Bounded lifecycle chaining

Distinct normative operations MAY be chained when prospectively stated human intent explicitly covers the chain and each stage independently satisfies its own authority, activation, evidence, and validation requirements.

For example, `reconcile this candidate and admit it if accepted` permits reconciliation followed by conditional admission. Intent covering only reconciliation stops after reconciliation.

A broad request such as `process this candidate` has no magic protocol meaning. Before consequential multi-stage execution, the agent MUST state its bounded interpretation and obtain context-bound intent for that defined chain.

## Interruption and materiality

Bounded intent MAY survive ordinary pauses and resumptions, but its scope is immutable. The agent MAY satisfy observational or mechanically necessary prerequisites already implied by the authorized workflow. If continuation requires a new mutation, new human approval, materially different evidence, a different authority holder, a materially changed operation, or expansion beyond the stated chain, the agent MUST stop and obtain the new intent or authority required.

The agent MUST pause before the next consequential operation when newly discovered information would reasonably be expected to affect the human's original decision to authorize that operation or workflow. Routine or immaterial discoveries do not require interruption.

A human MAY explicitly acknowledge newly surfaced material information and continue an otherwise valid bounded workflow. For durable workflows, that acknowledgement is durably associated with the workflow. Acknowledgement cannot override normative invalidity, failed validation, missing authority, or a safety invariant.

If the newly surfaced information changes the desired operation, workflow revision rules apply instead.

## Durable workflow intent

Ordinary conversational intent is transient. Cross-session continuation of bounded human intent requires an explicit durable workflow artifact.

A workflow artifact records intent and progress; it grants no authority. A later agent MAY resume only within its recorded scope and only after independently revalidating authoritative project state and every approval, Steward authorization, activation, evidence, or other requirement applicable to the next operation.

Creation of a durable workflow requires prospective disclosure. The agent MAY include persistence in the bounded workflow presentation, and a clear affirmative response permits creation. If persistence was not disclosed, conversational intent MUST NOT silently become durable project intent.

Cancellation preserves the workflow artifact and records it as cancelled/ineligible for continuation. Cancellation revokes outstanding workflow intent; it does not delete history or reverse completed normative operations. Any desired reversal is a new operation under its applicable authority rules.

Workflow artifacts express bounded intent, not resource ownership, reservation, locking, or project authority. RIL SHOULD proactively detect known overlap/conflict between active workflows. Before every consequential operation the agent revalidates authoritative state. If another workflow or operation makes the intended transition stale or materially changes its meaning, the affected workflow becomes blocked rather than silently adapting.

When blocked, the agent MAY diagnose the condition, identify which original intent remains valid, investigate alternatives, prepare non-authoritative replacement proposals, and recommend a revised bounded workflow. Material workflow scope changes require fresh human intent.

The exact workflow artifact schema, lifecycle, persistence primitive, and relationship to R16A inspection surfaces remain an open dependency and are not invented by this draft.

## Agent provenance

Where available and useful, durable operational evidence MAY preserve agent provenance such as agent/runtime identity, model/provider information, session/run identifiers, and tool/version information.

Agent provenance grants no RIL authority and cannot satisfy operator approval, Steward authorization, or activation requirements. Operational provenance is not canonical project knowledge.

The exact normative attachment/envelope mechanism for this provenance remains an open dependency and is not invented by this draft.

## Control return

Whenever control returns to the human after consequential work, the conversational adapter MUST make unambiguous:

- what completed and its material result;
- what requested work did not complete;
- durable artifacts created;
- the current boundary/state, such as completed, blocked, awaiting approval, awaiting activation, unresolved, or interrupted;
- the bounded next actions available.

The presentation MAY remain natural rather than mechanically printing fixed fields. Machine-readable adapters MAY expose the same information structurally.

The agent MUST NOT leave the human reasonably believing a consequential operation occurred when it merely prepared, proposed, approved, or attempted it.

## Reconciliation with R16A

R16B was reconciled against accepted `reasoning-distiller-ril-cli-design/1`.

Result: **PASS WITH 3 DESIGN DEPENDENCIES — no semantic contradiction found.**

The following cross-adapter invariants reconcile cleanly:

1. R16A and R16B are peer adapters over the same RIL semantics.
2. Proposal, approval, and apply remain distinct even when one prospectively disclosed conversational response supplies intent for approval plus application.
3. Approval remains bound to exact immutable proposals.
4. Protected/high-risk confirmation ceremonies are not weakened.
5. Steward authorization and activation remain distinct and activation is never inferred from conversational/session identity.
6. Operators do not become reconciliation or admission semantic authorities merely because they interact conversationally.
7. Reconciliation and admission remain distinct operations and may only be chained through bounded prospective intent.
8. Admission does not silently imply Canon verification.
9. Agent identity/provenance does not create authority.
10. Durable artifacts rather than chat history carry cross-session normative workflow state.

### Open dependency D1 — durable workflow primitive/artifact

R16B decisions introduce typed durable workflow intent (`workflow:<id>`), progress, cancellation, blocking, interruption acknowledgement, and cross-session resumption. R16A and R1–R15 do not currently define that artifact/primitive family.

This is compatible with R16A because workflows explicitly grant no authority, but R16B acceptance requires an explicit workflow primitive/artifact contract rather than implementation as hidden conversational state.

### Open dependency D2 — agent provenance attachment

R16B permits durable non-authoritative agent/runtime/model/session provenance. R16A permits operational evidence but does not define where such provenance attaches.

R16B acceptance requires an explicit decision whether provenance is represented by common artifact-envelope metadata, separate operational evidence, or contract-specific fields. Whatever mechanism is chosen MUST remain non-authoritative and outside Canon.

### Open dependency D3 — pre-approval proposal revalidation

R16B requires proposal applicability to be revalidated immediately before conversational approval creation. R16A requires exact proposal binding and apply-time validation but does not require this adapter-level freshness check.

This is a compatible strengthening, not a contradiction. The dependency is to define the accepted validation interface/result used by the Human ↔ Agent adapter and to make explicit that pre-approval revalidation never replaces mandatory apply-time primitive validation.

## Acceptance gate

R16B SHALL NOT be marked accepted until D1, D2, and D3 are resolved and incorporated into the applicable durable design/primitive contracts.

After those dependencies are resolved, reconciliation against R16A MUST be rerun. If no contradiction remains, this document may be promoted from draft to **Normative design contract — accepted**.

R16B acceptance does not by itself authorize UX implementation. Implementation slicing remains subject to the accepted primitive/conformance gates shared with R16A.