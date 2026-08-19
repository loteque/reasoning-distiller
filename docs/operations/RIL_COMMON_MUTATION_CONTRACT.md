# RIL Common Mutation Substrate Contract

Status: **Normative v1 primitive contract**

Implements architecture gates **R1-R3** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contracts:

- `reasoning-distiller-proposal/1`
- `reasoning-distiller-approval/1`
- `reasoning-distiller-mutation-event/1`
- `reasoning-distiller-projection-status/1`
- `reasoning-distiller-operation-result/1`

## Purpose

Provide one deterministic transaction substrate for later operator-registry, role-registry, and Steward-authorization primitives.

```text
current state + requested transition
        ↓
proposal
        ↓ SHA-256
human approval artifact
        ↓ exact digest binding
apply
        ↓
append-only event
        ↓ replay
current projection
```

This substrate grants no project, Steward, reconciliation, admission, or protocol-governance authority.

## Canonical JSON and identity

All substrate artifacts use UTF-8 canonical JSON:

- object keys sorted lexicographically;
- separators `,` and `:` with no insignificant whitespace;
- Unicode emitted directly (`ensure_ascii=false`);
- exactly one trailing LF;
- no NaN or Infinity values.

Artifact identity is `sha256:<lowercase-hex>` over those exact canonical bytes.

## Proposal

A proposal is intent only and MUST NOT mutate state.

Required fields:

```json
{
  "contract": "reasoning-distiller-proposal/1",
  "domain": "<domain>",
  "operation": "<operation>",
  "basis_digest": "sha256:...",
  "change": {}
}
```

`basis_digest` is the digest of the exact current semantic projection used to plan the transition. The proposal digest is calculated over the complete canonical proposal.

## Approval

An approval is durable evidence that a human operator approved one exact proposal.

Required fields:

```json
{
  "contract": "reasoning-distiller-approval/1",
  "proposal_digest": "sha256:...",
  "operator_id": "operator:...",
  "authentication": {"method": "..."}
}
```

`authentication` is structured and extensible. This contract does not itself decide whether a particular authentication method is sufficient; domain/operator policy does that later.

An approval for proposal X MUST NOT validate for proposal Y.

## Mutation event

A successful transition appends exactly one immutable event:

```json
{
  "contract": "reasoning-distiller-mutation-event/1",
  "sequence": 1,
  "domain": "<domain>",
  "operation": "<operation>",
  "proposal_digest": "sha256:...",
  "approval_digest": "sha256:...",
  "basis_digest": "sha256:...",
  "result_digest": "sha256:...",
  "result_state": {}
}
```

Events are authoritative. Projections are derived. Event filenames are zero-padded sequence numbers plus `.json` and MUST be created exclusively; existing event files are never overwritten.

## Replay and projection

Replay processes events in ascending sequence order and validates:

1. contiguous sequence numbers beginning at 1;
2. event contract identity;
3. each event `basis_digest` equals the replayed state digest immediately before it;
4. each `result_digest` equals the digest of `result_state`;
5. a consumed approval/proposal pair is not reused to create a second transition.

Projection status is one of:

- `VALID`: persisted projection equals replay;
- `REBUILDABLE`: projection missing and replay history valid;
- `CONFLICT`: projection exists but differs from replay, or history is invalid.

A missing projection may be rebuilt automatically. A conflicting projection MUST NOT be overwritten by normal apply/rebuild behavior.

## Apply semantics

Apply MUST preflight proposal, approval, event history, and projection before mutation.

Expected outcomes:

- exact proposal + matching approval + basis current → append event, rebuild projection, `PASS/APPLIED`;
- same proposal/approval + resulting state still current → `PASS/NO_CHANGE`;
- same approval after state changed beyond its original transition → `FAIL/APPROVAL_ALREADY_CONSUMED`;
- approval bound to another proposal → `FAIL/APPROVAL_MISMATCH`;
- proposal basis is stale → `FAIL/STALE_BASIS`;
- conflicting projection/history → fail closed.

## Operation result

All common primitives return a machine-readable envelope:

```json
{
  "contract": "reasoning-distiller-operation-result/1",
  "status": "PASS|FAIL",
  "outcome": "<stable-code>",
  "detail": "optional human-readable detail"
}
```

Exit status convention for CLI reference implementations:

- `0`: PASS, including idempotent `NO_CHANGE`;
- `2`: expected contract/precondition/conflict failure;
- `1`: unexpected internal failure.

## Storage ownership

The substrate owns only paths explicitly supplied by a domain primitive for:

```text
<domain>/events/
<domain>/current.json
```

Proposal and approval artifacts are supplied/persisted by the caller/domain workflow and remain durable evidence. The substrate MUST NOT delete them after use.

## Conformance gate

R1-R3 PASS requires tests proving:

1. canonical JSON and digest determinism;
2. planning/proposal creation performs no mutation;
3. exact proposal-to-approval binding;
4. mismatch rejection;
5. exclusive append-only event creation;
6. deterministic replay;
7. event-chain corruption detection;
8. missing projection classification/rebuild;
9. conflicting projection fail-closed behavior;
10. idempotent retry after successful apply;
11. consumed approval cannot authorize a later transition;
12. no authority/canonical protocol semantics are introduced by the substrate.
