# ChatGPT Project Integration Contract

Status: **Normative v1 operational integration contract**

Contract:

- `reasoning-distiller-chatgpt-project/1`

## Purpose

Define the safe operating boundary between a ChatGPT Project and the live `loteque/reasoning-distiller` repository.

The ChatGPT Project is an interactive coordination and working-context surface. It is not a second project knowledge package, not an authority registry, not a canonical memory backend, and not an alternate Distiller or Steward implementation.

The central invariant is:

> **Project memory is orientation, never authority.**

This contract preserves the repository's existing authority, activation, production-invocation, reconciliation, and admission boundaries while allowing ChatGPT Projects to provide useful conversational continuity around them.

## 1. Scope

This contract governs ChatGPT Project setup and ChatGPT-hosted work involving this repository, including:

- repository orientation and navigation;
- architecture and engineering discussion;
- role-bounded proposal/review workflows;
- implementation coordination;
- repository reads and writes performed through available tools;
- preparation for governed Reasoning Distiller operations.

This contract does not redefine:

- RGP semantics;
- role registration or role authority;
- Steward authorization;
- RIL activation evidence;
- `rd-distill` evidence or invocation semantics;
- reconciliation or admission;
- canonical project knowledge.

Where another repository contract governs a domain operation, that contract remains controlling.

## 2. Recommended ChatGPT Project configuration

Use one primary ChatGPT Project for ordinary governed development.

Recommended configuration:

| Setting | Required operating posture |
|---|---|
| Memory | Use project-only memory when available. |
| Repository access | Prefer a live GitHub connection to `loteque/reasoning-distiller`. |
| Project instructions | Keep them small and limited to stable operating invariants. |
| Uploaded repository files | Avoid using uploaded snapshots as the primary source for mutable repository state. |
| Chats | Prefer fresh chats for consequential role/task activations. |
| Independent review | Use an isolated project/context when independence materially matters. |

The Project may retain conversational continuity, but that continuity has no project-semantic standing merely because it is remembered.

## 3. Repository-state resolution

Repository-dependent work MUST resolve the live repository state before relying on mutable repository facts.

For consequential work, the activation SHOULD identify the exact commit/ref inspected.

At minimum:

1. resolve the current target branch or explicit requested ref;
2. read the live task-relevant contracts, directives, and project-owned state;
3. bind conclusions that depend on repository state to the revision actually inspected;
4. re-resolve the target ref before a consequential write when drift would matter;
5. verify the resulting repository state after the write before claiming completion.

A mutable branch name alone is not durable evidence of the bytes that were inspected.

Live repository access establishes current repository bytes. It does **not** by itself grant those bytes normative authority. Normative standing remains governed by the repository's source-resolution, governance, authority, and admission contracts.

## 4. Context and authority boundary

The following may help the assistant reason, but MUST NOT be treated as project authority, approval, canonical knowledge, or current repository state merely because they are present:

- ChatGPT Project memory;
- earlier chats in the same Project;
- assistant summaries;
- uploaded repository snapshots;
- chat titles or role labels;
- successful tests;
- implementation state;
- absence of contradictory evidence.

Explicit user instructions direct the current interaction, but project-semantic authority MUST still be recognized according to the governing repository contracts and accepted authority evidence for the operation being attempted.

Unknown authority MUST remain unknown. The assistant MUST NOT fill an authority gap from role names, conversational history, repository file names, or inferred intent.

## 5. Project instructions kernel

The primary ChatGPT Project SHOULD use a small instruction kernel equivalent to the following:

```text
This Project works on the live GitHub repository:
loteque/reasoning-distiller

Project memory, prior chats, summaries, and uploaded repository snapshots are
orientation only. They do not create authority, approval, evidence, canonical
knowledge, or current repository state.

For repository-dependent work:

1. Resolve the live repository revision before relying on mutable repository state.
2. Read the live task-relevant repository contracts and role directive.
3. Bind consequential analysis to the commit/ref actually inspected.
4. Never silently broaden a role's authority.
5. Never infer project authority from a role name, file name, repository state,
   previous chat, successful test, or absence of contradictory evidence.
6. Distinguish observations, proposals, decisions, authority, and execution.
7. Preserve Distiller, Steward, activation, reconciliation, admission, and
   deterministic-executor boundaries defined by the repository.
8. If required authority or evidence is absent, classify it as unknown and
   report the boundary rather than inventing or assuming it.
9. Do not claim that code, tests, commands, reviews, admissions, or repository
   changes occurred unless they were actually observed or performed.
10. For consequential work, identify the active operational role and task scope.
11. Use explicit bounded handoffs when changing roles for consequential work.
12. Prefer live GitHub content over uploaded repository snapshots.
```

This kernel is intentionally thin. Role directives and mutable governance belong in the repository and should be read live when needed.

## 6. Role-bounded chats

A ChatGPT chat may be used as a bounded activation surface for architecture, engineering, review, or coordination work.

For consequential work, the assistant SHOULD make the operational role and scope explicit, for example:

```text
repository: loteque/reasoning-distiller
resolved_revision: <commit>
operational_role: engineer
scope: review <artifact or question>
authority_required: none | <scope governed elsewhere>
```

This header is coordination metadata only. It is not a RIL activation artifact and grants no role authority.

Fresh chats are preferred when prior conversational conclusions could bias a distinct role activation.

A long-lived orientation chat may be used for navigation and state questions, but SHOULD NOT become the implicit source of truth for later consequential decisions.

## 7. Role activation is not a chat label

A prompt such as "act as the Steward," a chat named `STEWARD`, a Project instruction, or remembered role context does not establish registered role identity, Steward authorization, or accepted RIL activation evidence.

Operations requiring governed role authority MUST satisfy the applicable repository contracts, including `docs/operations/RIL_ACTIVATION_EVIDENCE_CONTRACT.md` where applicable.

In particular:

```text
chat/project role label
    != registered role
    != authorized role
    != accepted RIL activation
```

The ChatGPT Project MUST NOT collapse these distinctions.

## 8. Role transitions and handoffs

Consequential role transitions SHOULD use explicit bounded handoffs rather than silent role switching inside one continuous activation.

A handoff SHOULD preserve:

- the exact problem and constraints;
- the inspected repository revision;
- the prior role's complete artifact or decision input;
- governing evidence and contracts required by the receiving role;
- unresolved uncertainties and disagreements;
- the receiving role's scope and boundaries.

The receiving role MUST reason within its own mandate rather than treating the prior role's conclusions as established fact merely because they are present in conversation history.

## 9. Independent proposal review

When `docs/governance/PROPOSAL_REVIEW_METHOD.md` applies, the three stages remain separate semantic activations:

```text
Stage 1: RPG Engineer proposal
Stage 2: independent Engineer review/synthesis
Stage 3: Project Engineering Steward reconciliation/final plan
```

For high-consequence reviews, Stage 2 SHOULD run in an isolated ChatGPT Project or otherwise isolated context containing only the frozen problem, constraints, complete Stage-1 artifact, and explicitly supplied governing evidence.

This clean-room isolation is stronger than merely opening a new chat inside a Project whose memory may contain Stage-1 conclusions.

For routine implementation, mechanical refactors, typo fixes, or already-determined changes, the heavier review topology is not required unless another contract requires it.

## 10. Production Distiller boundary

Ambient ChatGPT Project context MUST NOT silently broaden a production `rd-distill` evidence set.

For production invocation, `docs/operations/PRODUCTION_INVOCATION_CONTRACT.md` remains controlling.

The model-side reasoning boundary is the prepared activation bundle produced from the explicit invocation request and fixed evidence set.

The following MUST NOT be implicitly injected into production distillation merely because ChatGPT knows them:

- prior Project chats;
- Project memory;
- assistant recollections;
- unrelated repository files;
- prior candidates or dispositions;
- canonical-state interpretations;
- hidden reasoning traces.

If conversational material is intended to become evidence, it must first be made an explicit source through the appropriate project-owned evidence/source process and then included by the production invocation contract.

## 11. Repository writes and completion claims

A ChatGPT Project may coordinate repository writes only through an available write-capable tool or execution environment.

The assistant MUST NOT claim that a change was committed, pushed, merged, tested, admitted, or otherwise completed until that result has been directly observed.

For consequential writes:

1. inspect the target state;
2. perform the bounded write;
3. observe the resulting commit/ref or other durable result;
4. report the exact durable identity when available.

A conversational intention to write is not a repository mutation.

## 12. Durable knowledge boundary

A conclusion reached in ChatGPT becomes durable project knowledge only through the repository's existing governed project-knowledge mechanisms.

Chat history is not an alternate canonical backend.

The lifecycle is therefore:

```text
conversation / analysis / implementation discussion
                |
                v
        explicit governed artifact
                |
                v
  existing project reconciliation/admission path
                |
                v
      canonical project knowledge
```

The ChatGPT Project may help create candidate artifacts, but it does not bypass Steward reconciliation, authorization, admission, or backend contracts.

## 13. Uploaded files

Uploaded Project files are snapshots unless the platform explicitly provides a live source.

For repository-owned mutable material:

- prefer live repository reads;
- do not assume an uploaded copy matches the current repository;
- when an uploaded snapshot is deliberately used as frozen evidence, identify it as such and bind conclusions to that snapshot rather than silently treating it as current `main`.

A stale uploaded governance document MUST NOT override a newer live repository contract.

## 14. Failure and stop conditions

The assistant SHOULD stop or narrow the operation when any of the following materially affects correctness:

- the repository revision cannot be resolved;
- live repository state conflicts with remembered or uploaded state;
- required evidence is absent;
- required role authority or RIL activation cannot be established;
- a requested operation would cross Distiller, Steward, reconciliation, admission, or deterministic-executor boundaries;
- the intended review requires independence that the current context cannot credibly provide;
- a write result cannot be verified;
- a production Distiller activation would require silently broadening its evidence set.

Stopping at a boundary is preferable to manufacturing continuity, authority, or evidence.

## 15. Conformance checklist

A ChatGPT Project setup conforms to this contract when:

1. live repository state is preferred over mutable uploaded snapshots;
2. Project memory is explicitly non-authoritative;
3. consequential repository reasoning is revision-bound;
4. role labels do not masquerade as registration, authorization, or RIL activation;
5. role transitions are bounded where semantic separation matters;
6. independent review can be isolated when required;
7. production `rd-distill` receives only its explicit activation bundle/evidence boundary;
8. repository writes are not claimed before observation;
9. ChatGPT conversation history cannot directly become canonical project knowledge;
10. existing repository governance and authority contracts remain controlling.

## 16. Non-goals

This contract does not define a new ChatGPT-specific authority model, memory backend, canonical store, RGP variant, role registry, Steward implementation, evidence format, model transport, or repository write protocol.

It exists only to prevent the convenience of a persistent conversational workspace from eroding the explicit boundaries already defined by Reasoning Distiller.
