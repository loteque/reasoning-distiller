# Canonical PEMS/COVE Recovery Mode B — B3 implementation

This work unit implements only the recovery-specific semantic-disposition
primitive frozen by B0 and required by Section 9 of the accepted Mode B plan.

Entry point: `runtime/ril_canonical_recovery_mode_b_disposition.py`,
`apply_semantic_disposition(project_root, disposition)`.

The primitive validates the strict disposition schema; exact live PEMS/COVE
prestate; immutable damage-analysis, inventory, activation, and row-evidence
references; exact ordered relation coverage; lifecycle and kind-specific data;
and the current R8 `semantic_reconciliation` authorization and activation by
replaying the existing role and authorization histories through R8.

Artifacts use compact sorted-key UTF-8 JSON without a trailing line feed and
are stored under the disjoint Mode B namespaces:

- `semantic-dispositions/<disposition-sha256>.json`
- `semantic-disposition-results/<disposition-sha256>.json`

An identical retry is no-change. A different disposition for the same project,
prestate, and damage-analysis identity fails closed. Accept is
`PASS/ACCEPT_REPAIR`; reject and defer are persisted
`FAIL/SEMANTIC_DISPOSITION_REJECTED` and
`FAIL/SEMANTIC_DISPOSITION_DEFERRED`. Every result has
`candidate_count: 0`.

The identity conflict check and both immutable publications execute under one
store lock, so concurrent conflicting submissions cannot both persist. A
malformed stored disposition identity fails closed as
`SEMANTIC_DISPOSITION_MISMATCH`.

The module cannot construct a candidate, repair proof, recovery plan, root
approval, or recovery transaction. It does not modify R12, Mode A runtime,
Canon, admission, recovery standing, role registry, Steward authorization, or
activation history. It contains no incident lifecycle or dependency-kind
selection.
