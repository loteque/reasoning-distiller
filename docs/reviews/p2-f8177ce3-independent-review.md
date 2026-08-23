# P2 Remediation Independent Review — `f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`

## Review identity

- Repository: `loteque/reasoning-distiller`
- Review scope: independent P2 remediation review only
- Live-main contract basis re-resolved before review evidence write: `58b99891e116b5a06dd603810c2b98ea83e328c3`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Exact remediation candidate: `f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`
- Candidate parent: `0aeaa98f6d514092aaf010afae5b1719308ed3bd`
- Candidate tree: `e53a60a58cf36823bc19d5fc25944686290cc49c`
- Candidate-bound workflow run: `32655013500`
- Candidate-bound workflow job: `97232272705`
- Review date: 2026-08-23

This artifact records an independent Engineer review disposition. It does not establish registered role identity, role authority, Steward authorization or activation, reconciliation, admission, production authorization, or P3 completion.

## Governing evidence inspected

The review was reconstructed from live repository evidence rather than prior chat memory:

- `agents/engineer/DIRECTIVE.md@58b99891e116b5a06dd603810c2b98ea83e328c3`
- `docs/governance/PROPOSAL_REVIEW_METHOD.md@58b99891e116b5a06dd603810c2b98ea83e328c3`
- `docs/proposals/context-packaging/FINAL_PLAN.md@0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- `docs/design/CONTEXT_PACKAGING_SOURCE_IDENTITY_CONTRACT.md@f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`
- `docs/design/CONTEXT_PACKAGING_SOURCE_RESOLUTION_P2.md@f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`
- frozen P1b source-binding schema blob `e5d5bc005f7a3dcd4f2f788dd08d49f3b57d4a1e`
- `context_packaging/source_resolver.py@f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`
- `tests/test_context_packaging_source_resolution_p2_regression.py@f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`
- workflow run `32655013500`, job `97232272705`

## Prior blocking finding reconstructed

The parent candidate `0aeaa98f6d514092aaf010afae5b1719308ed3bd` used snapshot-reference equality for operations that required complete-binding equivalence. P1a intentionally defines the canonical immutable fingerprint without `repository_relationship`; that relationship is a separate semantic field used by the `canonical_declares_repository_snapshot` consistency predicate.

Consequently, two canonical bindings could share the same structured source reference and P1a immutable fingerprint while carrying different `repository_relationship` values. In the parent candidate, representative lookup and duplicate acquisition coalescing could collapse those non-equivalent complete bindings. The selected representative could therefore depend on input order and could incorrectly make cross-source consistency appear proven.

This is the binding-equivalence/order-dependence blocker reviewed here.

## Remediation analysis

The exact candidate `f8177ce3d4d5b1c7edf7d3c0088db3d658b12072` changes the equivalence boundary in all three relevant paths:

1. **Binding-set validation fails closed before source acquisition.** `_validate_binding_set` groups bindings by the intentionally narrower snapshot-reference key and rejects the group with `CROSS_SOURCE_CONSISTENCY_UNPROVEN` when any members are not `_same_binding` complete equivalents.
2. **Reference lookup no longer picks an arbitrary representative.** `_find_binding` gathers all matches for one snapshot reference and returns no binding when those matches are not complete equivalents.
3. **Acquisition coalescing uses complete binding equivalence.** `resolve_sources` deduplicates with `_complete_binding_key`, whose canonical-state form adds normalized `repository_relationship` to the P1a snapshot-reference key.

The complete-binding comparator is aligned with the frozen source-binding schema and P1a semantics. For canonical state, the P1a immutable fingerprint contains project/backend address, PEMS identity, optional COVE identity, and the standing-evidence identity set; `repository_relationship` is the remaining permitted canonical binding field that can change consistency semantics while leaving that immutable fingerprint unchanged. The remediation compares that relationship structurally, with only the already-frozen hexadecimal commit normalization.

The narrower snapshot-reference key remains appropriate where the request wire format intentionally references a snapshot without carrying the relationship field. The candidate no longer mistakes that narrower reference identity for proof that every matching complete binding has identical consistency semantics.

The regression suite exercises both conflicting input orders:

- good relationship followed by bad relationship;
- bad relationship followed by good relationship.

Both cases require `CROSS_SOURCE_CONSISTENCY_UNPROVEN` before any adapter acquisition. The same remediation commit also adds multiplicity regressions to ensure the fix does not collapse distinct explicitly permitted canonical snapshots or weaken accepted-standing conflict behavior.

No reviewed candidate change enters P3 selector/closure work, reconciliation/admission, production invocation, or authority validation.

## Candidate-bound execution evidence

Workflow run `32655013500`, job `97232272705` was inspected as candidate-bound execution evidence. It checked out detached commit `f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`, verified the exact candidate identity and frozen contract evidence used by the workflow, and completed the P2/regression/inherited suite with **33/33 PASS**.

The independent reviewer did not claim a separate local or newly executed test run. This disposition relies on the inspected candidate-bound workflow evidence plus independent contract/code/test analysis.

## Findings

Blocking findings: **none**.

The prior binding-equivalence/order-dependence finding is remediated for the exact reviewed candidate. The implementation now fails closed when one snapshot reference corresponds to non-equivalent complete bindings, so request order cannot select a relationship-bearing representative and change the consistency result.

Residual boundary: this finding disposition is bound only to `f8177ce3d4d5b1c7edf7d3c0088db3d658b12072`. Any code-changing descendant requires its own evidence/review binding. This review does not reconcile or admit P2.

## Disposition

**`P2_INDEPENDENT_REVIEW_PASS`**

Candidate `f8177ce3d4d5b1c7edf7d3c0088db3d658b12072` resolves the reviewed binding-equivalence/order-dependence blocker and conforms to the reviewed live P2 contracts within the independent-review scope. No blocking finding remains in that scope.

The candidate is eligible for a separately governed Steward reconciliation step. This disposition is not Steward reconciliation, admission, authorization, or activation, and it does not begin P3.
