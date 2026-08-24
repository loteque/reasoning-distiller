# P7 Independent Review: Remediated Reproducibility Gate

Disposition: **P7_INDEPENDENT_REVIEW_PASS**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision independently resolved before review: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Coordination revision re-resolved immediately before disposition: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Prior rejected P7 candidate: `987220cdac4e060d524dfbf9fb188490e734cf91`
- Prior disposition: `P7_INDEPENDENT_REVIEW_CHANGES_REQUIRED`
- Prior blocking finding under review: `P7_SOURCE_RESOLVER_DEPENDENCY_IDENTITY_UNBOUND`
- Exact remediated P7 candidate: `d4557ef183731304401444f42cf62819cae567af`
- Exact candidate parent: `987220cdac4e060d524dfbf9fb188490e734cf91`
- Candidate branch re-resolved before disposition: `implement/context-packaging-p7-remediation-v3@d4557ef183731304401444f42cf62819cae567af`
- Engineer evidence commit: `e2d7cae372c459088becff6b9d4b11753936fbe4`
- Engineer evidence PR: `#76`
- Candidate-bound evidence run: `32790685632`
- `pack_builder.py` blob: `167602c87ea1766ae9978ed8a67098613e1f96ff`
- `pack_builder_v1.py` blob: `b0e806e966598e6d819b6d52c643efa23cdb6ef9`
- `source_resolver.py` blob: `11da98c213e783ed4c31f88392eb6a5634c9643e`
- P7 reproducibility test blob: `6e7eaba6ecdcc7c44cd050bc5cdac969bbddce78`
- Source-resolver adversarial test blob: `0ad6e3b99f8c9b87bf41d54e0ea269e552c1393e`
- Active role: fresh independent Reasoning Graph Protocol Engineer, P7 review only.

The current Engineer directive, Project chat-transition amendment, and proposal-review method were read from the exact live coordination revision. This review establishes no Steward authority, reconciliation, admission, canonical standing, authorization, activation, or P8+ successor scope.

## Independent reconstruction of the P7 gate

The governing plan makes P7 the reproducibility gate. Contracted-equivalent inputs must remain byte-identical across host perturbations including locale, ordering, filesystem enumeration, path separators, Unicode environment, temporary paths, and toolchain identities. Incompatible behavior-bearing toolchain changes must be visible rather than silently replay-equivalent.

The governing replay-identity requirement binds behavior identity for the builder/toolchain by immutable artifact identity or package content identity that fixes the implementation bytes. Because `pack_builder.py` delegates behavior into project-owned helper modules, a top-level builder identity is sufficient only when those transitive behavior-bearing bytes are themselves fixed and verified.

## Prior blocking finding reconstructed

The prior rejected candidate had already bound `pack_builder_v1.py`, but the executed builder graph still imported and used `context_packaging/source_resolver.py` while the top-level builder identity did not transitively fix those resolver bytes. A changed resolver could therefore alter source identity behavior while leaving the recorded top-level builder artifact unchanged.

The review question was not whether the remediation merely hashed a neighboring pathname. The required question was whether the immutable top-level behavior identity now transitively fixes the actual project-owned resolver behavior used by the build, and whether a mismatch fails closed.

## Candidate inspection

The exact remediation commit is one commit above the rejected candidate and changes only:

- `.gitattributes`;
- `context_packaging/pack_builder.py`; and
- `tests/test_context_packaging_reproducibility_p7_source_resolver_identity.py`.

`source_resolver.py` is now marked `-text`, preserving its identity-bearing bytes across host checkout normalization.

The exact `pack_builder.py` bytes now contain two transitive pins:

- `_PACK_BUILDER_V1_BLOB = b0e806e966598e6d819b6d52c643efa23cdb6ef9`; and
- `_SOURCE_RESOLVER_BLOB = 11da98c213e783ed4c31f88392eb6a5634c9643e`.

The P7 `/2` build path invokes `_verify_pack_builder_v1_identity()` and `_verify_source_resolver_identity()` before semantic build work. The resolver verifier reads the module identified by `context_packaging.source_resolver.__file__`, computes its Git blob identity from raw bytes, and fails with `TOOLCHAIN_IDENTITY_MISMATCH` if it differs from the pinned resolver blob.

The verifier also requires both executed `_snapshot_key` bindings, the direct `pack_builder.py` binding and the delegated `pack_builder_v1.py` binding, to be the exact function object exported by the pinned `source_resolver` module. This prevents the remediation from succeeding merely because an unrelated file at the resolver pathname has the expected digest while the builder graph executes a separately rebound `_snapshot_key` implementation.

The project-owned transitive helper graph used by `_snapshot_key`, including source-reference and fingerprint helpers, is defined in the same pinned `source_resolver.py` artifact. That module imports only standard-library facilities; no further repository-owned implementation dependency below this resolver behavior was identified.

The existing pack-builder component remains the recorded top-level behavior artifact. Because its exact bytes now contain the immutable helper and resolver blob pins, the recorded top-level builder identity transitively fixes those dependency identities. Runtime verification enforces the expected dependency bytes before the build proceeds.

## Adversarial regression inspection

The new source-resolver regression preserves the recorded top-level `pack_builder` component, copies `source_resolver.py` to a temporary path, appends a behavior-bearing `_snapshot_key` mutation, patches only the resolver module's `__file__` to that changed artifact, and invokes the same P5/P7 build path.

The expected result is fail-closed `TOOLCHAIN_IDENTITY_MISMATCH` at the toolchain stage with dependency-identity diagnostics. This is the material adversarial shape required by the prior blocker: dependency bytes change while the recorded top-level builder component remains constant.

The earlier adversarial regression for `pack_builder_v1.py` remains present and passing, so both identified project-owned transitive builder dependencies are covered.

## Candidate-bound execution evidence inspected

This review did not treat the Engineer summary alone as proof. I independently inspected the exact candidate source, exact regression source, evidence-workflow binding, workflow job results, and logs for run `32790685632`.

Observed candidate-bound evidence:

- exact candidate checkout: `d4557ef183731304401444f42cf62819cae567af`
- exact parent check: `987220cdac4e060d524dfbf9fb188490e734cf91`
- transitive identity marker: `P7_PACK_BUILDER_TRANSITIVE_IDENTITY_BOUND`
- exact P7 pytest suite: 6 passed, 2 subtests passed
- exact P7 unittest suite: 6 tests, all PASS
- `test_pack_builder_transitive_identity_rejects_changed_dependency`: PASS
- `test_behavior_bearing_source_resolver_mutation_fails_closed`: PASS
- unaffected context-packaging regressions: 150 passed, 2 deselected, 160 subtests passed
- Linux host probe: PASS
- Windows host probe: PASS
- cross-host comparison: `P7_CROSS_HOST_BYTE_IDENTITY_PASS`
- cross-host serialized pack digest: `sha256:54b6aa00d85cb8f2856785de334ba6c499a2961c06f58c65a2c49a15ff5260d6`
- cross-host pack identity digest: `sha256:158d3cd07c6bdc7839ea217b8f09a69e1d9763cd8f239d9e5fc347b93bb49bde`

No new independent workflow rerun was created by this review. The PASS is based on independent reconstruction and source/evidence inspection of the exact immutable candidate and its already candidate-bound execution evidence, not on a claim that this review executed a fresh run.

## Inherited reds preserved separately

Repository-wide checks attached to the evidence PR remain red in areas not introduced by this remediation. They are not converted into P7 PASS evidence:

1. `P1B_PS19_CLASSIFIER_MISMATCH`: expected `UNKNOWN_SEMANTICS_FIELD`, observed `PLANE_CLASSIFICATION_CONFLICT`; the P7 evidence workflow reproduces this separately.
2. The reconciled-v2 transition sentinel requiring the P5 runtime implementation blob to remain unchanged is red because P7 intentionally changes the builder implementation after the P5 freeze; the candidate-bound P7 regression workflow deselects this known transition sentinel rather than pretending it passes.
3. The existing runtime-isolation audit red on the mutable schema reference in `schemas/context-pack.schema.json` remains outside this source-resolver remediation and is not resolved here.
4. Extraction parity remains red on the pre-existing Distiller directive frozen-blob mismatch and is not resolved here.

None of these reds originates in the three-file `987220cd... -> d4557ef...` remediation delta. No additional P7-local failure was identified.

## Blocking finding disposition

### `P7_SOURCE_RESOLVER_DEPENDENCY_IDENTITY_UNBOUND`

**REMEDIATED.**

The current top-level builder artifact transitively fixes the exact `source_resolver.py` Git blob; the live build path verifies those bytes before behavior proceeds; both executed `_snapshot_key` bindings must be the exact function object from that pinned module; the resolver's repository-owned helper behavior is contained within that same pinned file; host checkout normalization is disabled for the identity-bearing artifact; and the candidate-bound adversarial regression demonstrates fail-closed behavior when the resolver dependency changes while the recorded top-level builder component remains constant.

I do not elevate hypothetical hostile in-process monkeypatching or import-hook replacement into a P7 blocker. The governing P7/R7 contract requires immutable implementation/toolchain identity and visible incompatible changes; it does not establish runtime-memory attestation as part of this gate.

## Independent review disposition

**P7_INDEPENDENT_REVIEW_PASS**

Candidate `d4557ef183731304401444f42cf62819cae567af` satisfies the independently reconstructed P7 reproducibility gate on the inspected immutable source and candidate-bound execution evidence. The prior `P7_SOURCE_RESOLVER_DEPENDENCY_IDENTITY_UNBOUND` blocker is closed, cross-host exact-byte identity is established by the bound run, and no new P7-local blocking finding was identified.

This PASS does not itself close P7. P7 Steward reconciliation is not established by this review, and this review performs no Steward operation.

No P8+, admission, canonical mutation, authority mutation, or activation work begins from this review.

## Terminal boundary and next role

The independent P7 review work unit is complete. A meaningful role boundary has been reached because any P7 reconciliation belongs to a separately activated Project Engineering Steward rather than this independent Engineer activation.

If continuation is selected, the receiving role should be a fresh Project Engineering Steward scoped only to reconciliation of exact candidate `d4557ef183731304401444f42cf62819cae567af` against this independent review and the bound Engineer evidence. Required Steward authority and activation must be independently established from the live repository contracts. No P8+ work should begin until that reconciliation boundary is satisfied.
