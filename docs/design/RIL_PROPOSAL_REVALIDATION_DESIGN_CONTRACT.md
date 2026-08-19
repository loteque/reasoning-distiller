# R16B-D3 — Pre-Approval Proposal Revalidation Design Contract

Status: **Normative dependency design contract — accepted and integrated**

Contract: `reasoning-distiller-proposal-revalidation/1`

Depends on: accepted R1–R15 proposal/approval/application primitives, amended R16A `reasoning-distiller-ril-cli-design/1`, accepted R16B-D1 workflow design, accepted R16B-D2 provenance design, and R16B `reasoning-distiller-ril-human-agent-design/1`.

Implementation status: **not authorized by this document alone.**

## Purpose

This contract resolves R16B dependency D3 by defining the accepted deterministic interface used to revalidate an immutable proposal immediately before an adapter converts human assent into a normative approval artifact.

Pre-approval revalidation prevents an adapter from knowingly creating fresh approval for a proposal whose applicability has already become stale. It is a compatible strengthening of the interaction boundary and does not replace mandatory apply-time primitive validation.

## Core rule

Immediately before creating an approval artifact, an approval-capable adapter MUST invoke the accepted proposal-applicability validator against:

- the exact immutable `proposal:<id>` being approved; and
- current authoritative project state/evidence material to that proposal.

The validator is deterministic, read-only, non-authoritative, and common across adapters. The Human ↔ Agent adapter MUST NOT implement its own semantic freshness rules.

## Validation result

The validator returns a structured deterministic result with one of these primary classifications:

```text
APPLICABLE
STALE
BLOCKED
INVALID
```

Semantics:

- `APPLICABLE` — the proposal remains eligible to receive a new approval under current authoritative state, subject to all independent approval/authentication requirements.
- `STALE` — authoritative state has advanced or changed such that the exact proposal no longer describes an applicable transition. A fresh approval MUST NOT be created for it.
- `BLOCKED` — applicability cannot presently be established because required authoritative evidence/state is unavailable, unresolved, or otherwise prevents a defensible validation. Approval MUST NOT be created while blocked.
- `INVALID` — the proposal itself or its required bindings fail the accepted proposal contract. Approval MUST NOT be created.

The result SHALL identify the exact proposal, classification, material authoritative bindings/checks used, and a machine-readable reason set sufficient for adapters to explain the boundary without inventing semantics.

## No authority

An `APPLICABLE` result grants no authority and is not approval.

It cannot substitute for authenticated operator assent, protected-root or exceptional approval ceremony, proposal-specific approval rules, Steward authorization or activation, apply-time validation, or any safety/integrity invariant.

The validator answers only whether the exact immutable proposal is presently applicable enough to be considered for approval.

## Approval creation boundary

Approval creation MUST bind to the exact immutable proposal already presented for approval. Revalidation MUST NOT rewrite, repair, rebase, broaden, narrow, or replace that proposal.

If the validator returns `STALE`, `BLOCKED`, or `INVALID`, the adapter MUST NOT convert prior affirmative human intent into an approval artifact.

The adapter MAY explain the result, investigate read-only causes, or prepare a new non-authoritative proposal where otherwise permitted. Any materially different replacement proposal requires its own layered presentation and fresh human approval intent.

## Immediately-before semantics and race handling

“Immediately before” means revalidation is part of the approval-creation attempt, not an earlier conversational preview check.

The approval primitive MUST protect the relevant state binding against a check/use race. The accepted implementation may do this by atomic validation-plus-creation or by requiring the approval creation request to carry the validator's exact authoritative state/material bindings and rejecting the request if those bindings are no longer current.

A state change after conversational assent but before approval commit therefore cannot silently produce approval against a stale proposal.

Adapters MUST NOT automatically retry by approving after a materially changed revalidation. They must return control at the appropriate boundary.

## Validation evidence lifetime

A revalidation result is attempt-scoped evidence, not durable standing authority. It MUST NOT be treated as a reusable freshness certificate for later approval attempts.

A later approval attempt performs a fresh revalidation against then-current authoritative state.

Implementations MAY persist diagnostic/audit evidence of a validation attempt where useful, including non-authoritative provenance under D2, but persistence does not extend validity.

## Conversational approval

For R16B, a short affirmative response is actionable only under the existing context-bound intent rules and only for the exact proposal or explicitly enumerated closed proposal set that was presented.

After such assent and before each approval artifact is created:

```text
human assent
    ↓
exact proposal identity
    ↓
proposal applicability revalidation
    ├── APPLICABLE → perform normal approval ceremony/creation
    └── STALE/BLOCKED/INVALID → no approval; return boundary
```

For a closed set of proposals, each proposal is independently revalidated and receives its own independently bound approval artifact. Failure of one proposal MUST NOT be hidden by successful validation of another.

D3 does not create atomic multi-proposal approval semantics.

## CLI and peer-adapter consistency

The validator is shared RIL orchestration/primitive semantics, not a conversation-only check.

R16B MUST use it, and amended R16A `ril approve <proposal>` invokes the same applicability revalidation as part of its approval-creation attempt.

This keeps approval behavior consistent across peer adapters and avoids a proposal being knowingly stale in one adapter but approvable in another merely because of interface choice.

This does not collapse proposal, approval, and apply. `ril approve` still creates approval only; `ril apply` remains a separate operation.

## Apply-time validation remains authoritative

Every apply operation MUST independently perform the complete validation required by the underlying normative primitive at application time.

A proposal may be `APPLICABLE` at approval creation and become stale before apply. In that case apply MUST fail or return the accepted stale/inapplicable result; approval does not freeze project state, reserve resources, or waive validation.

```text
pre-approval revalidation
  = do not knowingly approve stale intent

apply-time validation
  = determine whether mutation is valid now
```

Neither replaces the other.

## Workflows

A workflow reaching `AWAITING_APPROVAL` may surface an exact proposal for approval. Approval creation within or alongside the workflow uses this same D3 validator.

An `APPLICABLE` result does not advance workflow state by itself. A created approval and any subsequent apply/result binding remain distinct normative facts.

If revalidation fails because workflow-relevant authoritative state materially changed, the workflow primitive/orchestrator projects the applicable blocked/materiality condition according to D1; D3 itself does not rewrite workflow intent.

## Inspection and diagnostics

Revalidation is read-only and MUST NOT repair or mutate project state. Its structured result SHOULD expose enough reason/binding information for human and JSON adapters to explain why approval was permitted or refused.

A transient validation result need not introduce a new globally inspectable artifact family. If durably recorded for audit, that record remains non-authoritative operational evidence and cannot become approval or freshness authority.

## Reconciliation findings

D3 was reconciled against accepted R1–R15, amended R16A, accepted D1, accepted D2, and R16B.

Result: **SEMANTIC PASS — INTEGRATION COMPLETE.**

No contradiction was found with immutable proposal identity, exact proposal binding, proposal/approval/apply separation, protected approval ceremonies, workflow semantics, provenance non-authority, or apply-time validation.

### Integration amendment D3-I1 — resolved

Amended R16A now requires `ril approve <proposal>` to invoke the same immediately-before applicability revalidation before creating approval.

This strengthens the shared approval adapter boundary without changing the meaning of approval or application.

## D3 resolution status

R16B dependency D3 is **RESOLVED**.
