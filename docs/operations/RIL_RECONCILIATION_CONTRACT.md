# RIL Reconciliation Contract

Status: **Normative v1 primitive contract**

Implements architecture gate **R12** from `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`.

Contracts:

- `reasoning-distiller-reconciliation-assessment/1`
- `reasoning-distiller-reconciliation-disposition/1`
- `reasoning-distiller-reconciliation-result/1`

## Purpose

R12 records an immutable semantic reconciliation disposition for one immutable Distiller submission under an authorized and activated reconciliation Steward role.

R12 does **not** perform admission and MUST NOT mutate canonical PEMS/COVE state.

## Preconditions

A reconciliation apply requires:

1. a candidate submission file beneath `project-knowledge/submissions/`;
2. candidate bytes are normal, non-symlink, canonical JSON;
3. valid activation evidence accepted for `semantic_reconciliation` by R8;
4. an assessment satisfying this contract;
5. no existing conflicting disposition for the same candidate digest.

## Assessment

```json
{
  "contract": "reasoning-distiller-reconciliation-assessment/1",
  "semantic_status": "COMPATIBLE|INCOMPATIBLE|REVISION_REQUIRED",
  "admission_recommendation": "RECOMMEND|DO_NOT_RECOMMEND|DEFER",
  "rationale": "human/agent supplied semantic rationale"
}
```

Allowed combinations are intentionally constrained:

- `COMPATIBLE` → `RECOMMEND` or `DEFER`
- `INCOMPATIBLE` → `DO_NOT_RECOMMEND`
- `REVISION_REQUIRED` → `DEFER`

The primitive validates and records the Steward assessment. It does not manufacture semantic judgment itself.

## Disposition

A successful reconciliation writes one immutable candidate-bound disposition:

```json
{
  "contract": "reasoning-distiller-reconciliation-disposition/1",
  "candidate_digest": "sha256:...",
  "candidate_path": "project-knowledge/submissions/...",
  "role_id": "...",
  "invocation_id": "...",
  "activation_digest": "sha256:...",
  "assessment": { ... }
}
```

The canonical disposition path is:

```text
project-knowledge/reconciliation/dispositions/<candidate-sha256-hex>.json
```

Activation evidence is also persisted immutably by digest under:

```text
project-knowledge/reconciliation/activation-evidence/<activation-sha256-hex>.json
```

## Immutability and retry

- The same candidate + same activation + same assessment is idempotent and returns `PASS/NO_CHANGE`.
- A different disposition for an already reconciled candidate returns `FAIL/DISPOSITION_CONFLICT`.
- Existing evidence artifacts with different bytes at the same digest path fail closed.
- Candidate bytes are re-read during apply; mutation of the candidate changes its digest and therefore its identity.

## Authority boundary

R12 delegates authority validation to R8. The activation artifact must be accepted for the `semantic_reconciliation` scope at apply time. A role name alone is insufficient.

R12 MUST NOT:

- authorize a Steward;
- alter role or operator registries;
- create admission authority;
- invoke admission;
- mutate canonical PEMS/COVE stores.

## Conformance gate

R12 PASS requires tests proving:

1. canonical candidate identity;
2. candidate path confinement beneath project submissions;
3. activation authority is required;
4. unauthorized/wrong-role activation is rejected;
5. assessment contract and allowed combinations are enforced;
6. successful immutable disposition creation;
7. activation evidence persistence;
8. idempotent retry;
9. conflicting second disposition is rejected;
10. candidate mutation changes identity rather than rewriting prior disposition;
11. no PEMS/COVE/admission state is created or modified.
