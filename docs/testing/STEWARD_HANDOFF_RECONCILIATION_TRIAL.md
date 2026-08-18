# Steward Handoff / Reconciliation Trial

Status: **Durable test specification — execution requires project-authorized Steward**

## Motivation

Live model activation has proven candidate production through immutable submission. The next independent boundary is governance:

> Can an immutable Distiller submission be handed to a project-authorized Steward, reconciled against explicit project state, and returned as a durable Steward disposition without allowing the Distiller or orchestration layer to exercise reconciliation or admission authority?

This trial tests reconciliation authority. It does not grant admission merely because reconciliation succeeds.

## Authority invariant

**Reconciliation authority lies with the Steward. The Distiller has no reconciliation or admission authority. Orchestration does not acquire either authority by coordinating the handoff.**

The trial MUST stop rather than manufacture a Steward identity or authority grant.

## Inputs

The measured invocation requires:

1. an immutable `rgp/1` candidate submission produced by the Distiller;
2. explicit project-owned reconciliation state against which the candidate is evaluated;
3. a project-authorized Steward invocation;
4. provenance identifying the candidate and reconciliation-state inputs.

The trial MUST NOT treat repository presence, a role name, CI execution, or this specification as an authority grant.

## Measured procedure

1. Verify the candidate submission is immutable and valid under its declared protocol.
2. Snapshot/digest the project-owned reconciliation inputs before Steward activation.
3. Verify that no Distiller output claims reconciliation, admission, or canonical mutation.
4. Hand the candidate plus explicit reconciliation state to the project-authorized Steward.
5. Require the Steward to evaluate semantic equivalence, conflict, supersession, provenance, project ownership, and admissibility implications according to the project's rules.
6. Persist the Steward's reconciliation disposition as project-owned governance evidence.
7. Verify the disposition identifies the candidate and reconciliation-state identities it evaluated.
8. Verify the candidate submission remains byte-for-byte unchanged.
9. Verify the Distiller installation and generic framework remain unchanged.
10. Verify no PEMS/COVE/canonical mutation occurs unless a separate authorized admission operation is explicitly invoked.
11. Verify orchestration artifacts do not themselves claim Steward authority.
12. Preserve measured evidence and emit a trial disposition.

## PASS criteria

| Property | Requirement |
|---|---|
| Candidate integrity | immutable candidate is unchanged |
| Steward authority | reconciliation is performed only by an explicitly project-authorized Steward |
| Input identity | disposition binds candidate and reconciliation-state identities |
| Semantic reconciliation | Steward records accept/reject/amend/supersede implications under project rules |
| Distiller boundary | Distiller performs no reconciliation/admission |
| Orchestrator boundary | coordination confers no authority |
| Admission separation | reconciliation alone does not mutate PEMS/COVE/canonical state |
| Provenance | durable evidence identifies all evaluated inputs |

## STOP conditions

The trial records a blocked/product/governance finding and stops if:

- no explicit project-authorized Steward can be established;
- project reconciliation rules/state are unavailable or ambiguous;
- the candidate identity cannot be verified;
- reconciliation would require inventing project facts or authority;
- the only available path couples reconciliation to automatic admission.

A STOP is preferable to silently widening authority.

## Output boundary

A successful trial ends at a durable Steward reconciliation disposition:

```text
immutable Distiller submission
        ↓
project-authorized Steward
        ↓
semantic reconciliation
        ↓
durable Steward disposition
        ↓
STOP — no admission implied
```

The next independent gate is **authorized admission and PEMS/COVE storage**, exercised only under the consuming project's admission contract.
