# RIL Activation Interactive Fast-Path Contract

Status: **Normative v1 public orchestration contract**

Contract:

- `reasoning-distiller-ril-activation-fast-path/1`

## Purpose

Expose the existing `reasoning-distiller-role-activation/1` primitive as a standalone public `ril activation run` operation for interactive coordination.

The fast path is orchestration only. It does not replace, weaken, extend, or reinterpret the activation primitive. It does not add authority, authorization, reconciliation, admission, mutation, persistence, candidate, or review semantics.

## Public command

```text
ril activation run \
  --role <ROLE_ID> \
  --scope <SCOPE> \
  --invocation-id <INVOCATION_ID> \
  --source <SOURCE>
```

`SCOPE` is validated by the existing activation primitive. V1 therefore accepts only the authority scopes accepted by that primitive: `semantic_reconciliation` and `admission`.

The CLI MUST NOT pre-interpret an unknown scope into a different result. Primitive validation owns `UNKNOWN_SCOPE` and the other activation outcomes.

## Operation

For one invocation, the public operation MUST:

1. discover the project root using the existing `ril` CLI project-discovery rules;
2. construct the exact `reasoning-distiller-role-activation/1` `explicit_declaration` artifact from `role`, `invocation-id`, and `source`;
3. validate that artifact against the current role registry and current Steward authorization for the requested scope;
4. return the exact activation artifact, its canonical digest, and the primitive validation result.

The public CLI result status and outcome MUST mirror the primitive validation status and outcome. A failed activation MUST NOT be hidden inside a top-level `PASS/OK` result.

## Fast-path boundary

No candidate, proposal, independent review, review disposition, reconciliation artifact, admission artifact, or P5 artifact is a prerequisite for activation validation.

This absence of a candidate/review prerequisite is not a bypass of downstream governance. The fast path only makes the existing read-only activation primitive directly callable. Reconciliation and admission retain all of their existing prerequisites and semantics.

An accepted activation is point-in-time evidence for the supplied invocation context. It is not a durable capability, lease, authorization, or transferable authority token. A later governed operation that relies on activation MUST receive or bind the exact activation artifact/digest and MUST apply the existing downstream validation rules against then-current repository authority state.

If role availability or Steward authorization changes after a fast-path run, the prior artifact does not preserve the prior authority state.

## Storage and mutation

`ril activation run` MUST be read-only.

It MUST NOT:

- persist the activation artifact;
- register, enable, disable, select, or otherwise mutate a role;
- assign, reassign, or revoke Steward authorization;
- create or broaden authority;
- perform reconciliation or admission;
- mutate canonical project knowledge;
- create a candidate, review, disposition, receipt, or other governed semantic artifact.

A caller may retain the returned activation artifact and digest as invocation provenance, subject to the existing activation and downstream domain contracts.

## Failure semantics

All activation failures remain fail-closed and are owned by the existing primitive, including:

- `INVALID_ACTIVATION_EVIDENCE`;
- `UNSUPPORTED_ACTIVATION_METHOD`;
- `UNKNOWN_SCOPE`;
- `ROLE_NOT_FOUND`;
- `ROLE_UNAVAILABLE`;
- `SCOPE_UNASSIGNED`;
- `ROLE_NOT_AUTHORIZED_FOR_SCOPE`;
- role-registry or Steward-authorization projection/history conflicts.

Interactive role labels, chat titles, handoffs, coordination metadata, or a request to act as a role do not themselves satisfy activation evidence and do not create registration or authorization.

## Conformance

The fast path is conformant only if tests prove at least:

1. the public parser accepts `ril activation run` with explicit role, scope, invocation id, and source;
2. a currently authorized available role returns top-level `PASS/ACTIVATION_ACCEPTED` and the exact activation artifact/digest;
3. no candidate or review artifact is required for activation;
4. repeated validation is deterministic and mutation-free;
5. reconciliation and admission scopes remain independent;
6. primitive failures are promoted to the public top-level status/outcome rather than wrapped in `PASS/OK`;
7. unknown scope and projection conflicts remain fail-closed;
8. a previously accepted artifact loses validity when current authorization is reassigned;
9. quiet output can identify the exact activation digest without persisting the artifact.
