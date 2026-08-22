# ChatGPT Project Chat-Transition Amendment

Status: **Normative v1 amendment**

Amends:

- `reasoning-distiller-chatgpt-project/1`

Contract:

- `reasoning-distiller-chatgpt-project-chat-transition/1`

## Purpose

Add an explicit proactive chat-transition responsibility to ChatGPT-hosted role work without changing repository role authority, RIL activation, production Distiller evidence, or canonical project-knowledge semantics.

The governing rule is:

> **When the current role reaches a meaningful chat boundary, tell the user before silently continuing across it.**

The reminder exists to preserve semantic role separation and useful context isolation. It is coordination behavior only.

## Chat-boundary conditions

A role SHOULD identify a chat boundary when one or more of the following materially applies:

1. the next consequential work belongs to another role;
2. a proposal or review workflow is moving to a stage that requires semantic independence;
3. an independent review should not inherit conclusions or assumptions from the current conversation;
4. accumulated conversation context would materially bias a fresh activation;
5. the active role has completed the artifact, decision, candidate, reconciliation, or other result that the next role must receive;
6. the work is changing from analysis or review into a separately bounded implementation or governed operation;
7. another repository contract requires a distinct activation or evidence boundary.

A new chat SHOULD NOT be recommended merely because the conversation is long or because a minor subtask changed. Ordinary continuation inside the same role, scope, authority posture, and evidence boundary should remain in the current chat.

## Required reminder behavior

When a meaningful chat boundary is reached, the active interactive role SHOULD:

1. explicitly state that a chat boundary has been reached;
2. identify why continuing in the same chat would weaken role separation, independence, or evidence boundaries;
3. recommend the appropriate next role;
4. recommend a fresh chat or, when stronger independence is required, an isolated ChatGPT Project/context;
5. provide a compact bounded handoff suitable for starting that activation.

A reminder SHOULD occur at the transition point, not repeatedly throughout ordinary same-role work.

## Bounded handoff

The handoff SHOULD include, when applicable:

- repository and resolved revision;
- exact problem and constraints;
- current role and completed scope;
- completed artifact, result, candidate, disposition, or decision input;
- governing contracts and evidence the receiving role requires;
- authority evidence when the receiving operation depends on it;
- unresolved uncertainties and disagreements;
- receiving role and requested scope;
- exact next action the receiving activation should perform.

The handoff is coordination metadata. It does not create project authority, canonical knowledge, or accepted RIL activation evidence.

## Role-directive integration

Interactive ChatGPT hosting of repository roles MUST preserve the role-specific directives.

The current role directives define their local reminder behavior:

- `agents/architect/DIRECTIVE.md`;
- `agents/engineer/DIRECTIVE.md`;
- `agents/steward/DIRECTIVE.md`;
- `agents/distiller/DIRECTIVE.md`.

A role transition must not silently broaden the outgoing or incoming role's authority.

## Distiller production exception

The production Distiller boundary remains controlled by `docs/operations/PRODUCTION_INVOCATION_CONTRACT.md`.

Chat-transition reminders MUST NOT:

- enter the fixed production evidence set merely because they exist in Project context;
- be inserted into the prepared production activation bundle unless independently authorized as explicit evidence by the governing process;
- appear inside raw Distiller candidate bytes;
- appear inside the Distiller structured output contract;
- cause the model-side production activation to search for or infer additional project context.

For production `rd-distill`, any chat-transition reminder belongs to the surrounding interactive coordination layer before or after the model activation.

## Relationship to role activation

A chat-transition reminder, chat title, handoff, fresh chat, isolated Project, or role label is not proof of registered role identity, role authorization, or accepted RIL activation.

Where governed role authority is required, the applicable repository role, authorization, and activation contracts remain controlling.

## Conformance

A ChatGPT-hosted workflow conforms to this amendment when:

1. meaningful cross-role or independence boundaries cause a proactive user-facing transition reminder;
2. same-role ordinary continuation does not produce noisy or unnecessary chat-change prompts;
3. each reminder identifies the next role/context and provides a bounded handoff;
4. reminders do not manufacture authority or activation evidence;
5. independent review receives stronger context isolation when required;
6. production Distiller candidate bytes and structured output remain free of chat-navigation prose;
7. production Distiller evidence remains fixed by its governing invocation contract.
