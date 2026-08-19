# RIL Common Mutation Substrate Contract

Status: **Normative v1 primitive contract — amended for R17 authority grants**

Implements architecture gates **R1-R3** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contracts:

- `reasoning-distiller-proposal/1`
- `reasoning-distiller-approval/1`
- `reasoning-distiller-approval/2`
- `reasoning-distiller-mutation-event/1`
- `reasoning-distiller-projection-status/1`
- `reasoning-distiller-operation-result/1`

Depends on accepted R17 `reasoning-distiller-authority-grant/1` for grant-derived approval semantics.

## Purpose

Provide one deterministic transaction substrate for later operator-registry, role-registry, and Steward-authorization primitives.

```text
current state + requested transition
        ↓
proposal
        ↓ SHA-256
exact approval artifact
        ↓ exact digest binding
apply
        ↓
append-only event
        ↓ replay
current projection
```

Approval authority may come from direct authenticated operator assent or, where the operation contract explicitly permits delegation, an accepted bounded `authority-grant:<id>`. The substrate itself grants no project, Steward, reconciliation, admission, or protocol-governance authority.

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

A proposal does not become delegable merely because an adapter labels it as such. Delegability, stable `operation_class`, authority-relevant target fields, and supported grant predicates are published by the governing domain primitive contract. Operations without such an accepted declaration are non-delegable by default.

## Approval v1 — direct operator assent

`reasoning-distiller-approval/1` remains valid durable evidence that a human operator directly approved one exact proposal.

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

## Approval v2 — explicit authority basis

R17 adds `reasoning-distiller-approval/2`, which preserves exact proposal binding while making the authority basis explicit.

A direct-operator approval has the conceptual form:

```json
{
  "contract": "reasoning-distiller-approval/2",
  "proposal_digest": "sha256:...",
  "authority_basis": {
    "kind": "direct-operator",
    "operator_id": "operator:...",
    "authentication": {"method": "..."}
  }
}
```

A grant-derived approval has the conceptual form:

```json
{
  "contract": "reasoning-distiller-approval/2",
  "proposal_digest": "sha256:...",
  "authority_basis": {
    "kind": "authority-grant",
    "grant": "authority-grant:<id>",
    "grant_event": "authority-grant-event:<id>"
  }
}
```

Both approval forms bind exactly one immutable proposal. An approval for proposal X MUST NOT validate for proposal Y.

The grant-derived form does not assert that a human reviewed the exact proposal at issuance time. It records that an earlier authenticated human grant, plus deterministic accepted grant validation, authorized issuance for that exact proposal.

Consumers and audit surfaces MUST preserve the distinction between direct assent and grant-derived authority.

## Grant-derived approval issuance

Grant-derived approval issuance is an accepted primitive path only when the governing operation contract declares the proposal operation class delegable.

Before issuance, the primitive/orchestration layer MUST establish all of the following against exact current state:

1. D3 proposal applicability is `APPLICABLE`;
2. the selected `authority-grant:<id>` is ACTIVE and bound to the applicable workflow;
3. the complete exact proposal is `WITHIN_GRANT` under the accepted R17 scope validator;
4. workflow materiality state permits progression;
5. grant finite limits/capacity permit issuance;
6. the grant and workflow normative heads/state bindings remain current.

Grant-scope validation, grant availability/limit accounting, creation of the resulting `approval/2`, and append of the grant's `core/approval-issued` event MUST be atomic with respect to grant normative state. A stale race fails rather than rebasing or silently choosing different authority.

If no applicable grant exists, grant validation is outside scope, or grant selection is materially ambiguous, no grant-derived approval is created. The caller returns to the ordinary proposal-specific approval boundary.

Grant consumption occurs when the grant-derived approval is issued. Later apply failure does not restore consumed grant capacity. Reuse of the same valid approval for an accepted idempotent retry does not consume an additional grant unit.

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

Mutation events bind the exact approval artifact used. They do not reinterpret or flatten its authority basis.

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

Apply MUST preflight proposal, approval, event history, projection, and the governing domain's authority rules before mutation.

For `approval/1`, existing direct-human validation remains unchanged.

For `approval/2` with `authority_basis.kind = direct-operator`, apply validates the same operator authority policy using the nested direct authority evidence.

For `approval/2` with `authority_basis.kind = authority-grant`, apply MUST validate that:

- the governing operation contract permits grant-derived approval for this proposal operation class;
- the approval binds the exact proposal;
- the referenced grant issuance event exists, is valid, and binds this grant, proposal, and approval;
- the grant-derived approval was validly issued under the accepted R17 primitive.

Apply does not rerun grant consumption and MUST NOT require the grant still be ACTIVE merely because the approval was validly issued before later revocation. Revocation prevents future issuance; it does not erase already-issued approvals. Any separate approval invalidation rule must be defined explicitly by the applicable contract.

Apply-time proposal/basis/state validation remains independently mandatory for all authority bases.

Expected outcomes include:

- exact proposal + valid matching approval + basis current → append event, rebuild projection, `PASS/APPLIED`;
- same proposal/approval + resulting state still current → `PASS/NO_CHANGE`;
- same approval after state changed beyond its original transition → `FAIL/APPROVAL_ALREADY_CONSUMED`;
- approval bound to another proposal → `FAIL/APPROVAL_MISMATCH`;
- invalid/missing grant issuance evidence → fail closed;
- non-delegable operation presented with grant-derived approval → fail closed;
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

Authority-grant definition/event storage belongs to the R17 grant primitive, not to this common mutation substrate.

## R17 integration invariant

R17 authority grants are an alternate human-derived authority basis for exact approval issuance, not an alternate mutation path.

The normal transaction remains:

```text
proposal
  ↓
exact approval (direct or grant-derived)
  ↓
apply-time validation
  ↓
append-only mutation event
```

No agent/runtime identity may itself occupy `authority_basis`.

## Conformance gate

R1-R3/R17 integration PASS requires tests proving:

1. canonical JSON and digest determinism;
2. planning/proposal creation performs no mutation;
3. exact proposal-to-approval binding;
4. direct approval mismatch rejection;
5. grant-derived approval cannot issue for an unamended/non-delegable operation;
6. grant-derived issuance atomically binds grant event, proposal, and approval;
7. grant revocation racing with issuance has exactly one authoritative winner;
8. a later grant revocation does not rewrite an already-issued approval;
9. apply validates grant issuance evidence and still performs full apply-time state validation;
10. exclusive append-only event creation;
11. deterministic replay;
12. event-chain corruption detection;
13. missing projection classification/rebuild;
14. conflicting projection fail-closed behavior;
15. idempotent retry after successful apply;
16. consumed approval cannot authorize a later transition;
17. no agent, workflow, or grant creates Steward/reconciliation/admission/protocol authority beyond its accepted scope.
