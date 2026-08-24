# P6 Independent Review: Remediated Persistence Adapter

Disposition: **P6_INDEPENDENT_REVIEW_PASS**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision independently resolved before review: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Coordination revision re-resolved immediately before review disposition: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Closed P5 semantic base: `d96071ab833179948e5f9526cdb63c15c6451ff4`
- Prior rejected P6 candidate: `99724c025d09714c7d369ddeda0a33be8078f602`
- Prior independent review evidence: `8477717ef909bc06c2f25d5965a93107f61a9340`
- Prior disposition: `P6_INDEPENDENT_REVIEW_CHANGES_REQUIRED`
- Exact remediated P6 candidate: `091e9ac97f0a068045acbcc57e90a934d24f9f7a`
- Persistence-adapter blob: `58350007067f0443b65758992b1a17323123271d`
- P6 test blob: `e067ba772e9323c2a3bdfd93ddf343c4fadf2a28`
- P5 builder blob preserved: `c7a87dae852de2cb58393fa3bc6dd9241a2155f0`
- P5 test blob preserved: `5fd7fc17a01877f4add060357a6b28ee0eb0e096`
- Engineer execution evidence: `0bb93c9f31de65ba4fae9d0c3c815f7d44d0fdc8`
- Engineer execution-manifest blob: `22681eeaf3d267453497961934420d85238fcd17`
- Active role: fresh independent Reasoning Graph Protocol Engineer, P6 review only.

The current Engineer directive, Project chat-transition amendment, and proposal-review method were read from the exact live coordination revision. This review establishes no Steward authority, reconciliation, admission, canonical standing, authorization, activation, or P7+ successor scope.

## Independent reconstruction of the P6 gate

The governing plan makes P6 a separate optional persistence operation layered after the pure P5 builder. The P6 operation must remain outside authority/canonical lifecycle stores; exact replay must return `NO_CHANGE`; different existing bytes must fail immutable collision without overwrite; storage must grant no semantic or canonical standing; and persistence state must not change P5 semantic bytes.

The governing persistence, immutability, read-only, unknown-state, and production-boundary invariants remain applicable. Missing boundary evidence must therefore remain missing rather than being interpreted as permission to write.

## Prior blocking findings reconstructed

The prior independent review reproduced two P6-local blockers in candidate `99724c025d09714c7d369ddeda0a33be8078f602`:

1. `P6_LIFECYCLE_BOUNDARY_EVIDENCE_OPTIONAL`: lifecycle-store exclusion could be omitted because `prohibited_roots` defaulted to an empty sequence, allowing publication when the required outside-lifecycle boundary was not established.
2. `P6_PARENT_REPLACEMENT_PUBLICATION_ESCAPE`: the implementation checked a resolved parent path and later published through pathname-based `os.open`, permitting the checked parent to be replaced with a symlink before publication and redirecting the write outside `output_root`.

These findings were treated as review inputs, not as predetermined remediation conclusions.

## Candidate inspection

The remediated candidate is exactly one commit above the rejected P6 candidate. The remediation commit changes only:

- `context_packaging/persistence_adapter.py`; and
- `tests/test_context_packaging_persistence_adapter_p6.py`.

Across the closed P5 base to the remediated P6 candidate, the semantic diff remains limited to:

- `context_packaging/__init__.py`;
- `context_packaging/persistence_adapter.py`; and
- `tests/test_context_packaging_persistence_adapter_p6.py`.

The closed P5 builder and P5 test blobs remain byte-identical to their closed P5 identities.

The exact remediated adapter now requires explicit caller-supplied lifecycle-boundary evidence. `prohibited_roots=None` raises `PersistenceBoundaryError` before output-root resolution or publication. An explicit empty sequence remains representable when the caller's complete lifecycle-boundary set is actually empty.

Publication and replay are anchored to an opened, verified output-root directory descriptor. The implementation opens the root with no-follow/directory constraints, verifies the descriptor refers to the same device/inode observed during root verification, and then performs target create/read through Linux `openat2` with `RESOLVE_BENEATH`, `RESOLVE_NO_SYMLINKS`, and `RESOLVE_NO_MAGICLINKS`. Unsupported platforms or kernels fail closed rather than falling back to unsafe pathname publication.

Create uses exclusive creation. Existing targets are opened through the same beneath/no-symlink boundary and are accepted only as regular files. Exact bytes return `NO_CHANGE`; different bytes raise `ImmutableOutputCollisionError`. Missing parents are not created.

## Independent source and regression inspection

The exact ten-case P6 suite covers:

- first immutable publication and exact replay;
- immutable collision without overwrite;
- traversal escape rejection;
- explicit prohibited lifecycle-store rejection;
- omitted lifecycle-boundary evidence fail-closed behavior;
- deterministic parent-directory replacement pressure;
- absence of semantic standing in result metadata;
- non-byte input rejection before write;
- no implicit parent creation; and
- persistence/output presence not changing successful P5 pack bytes.

The parent-replacement regression reproduces the material shape of the prior blocker: after the output-root descriptor is opened, the checked `sub` directory is renamed outside the root and its lexical path is replaced by a symlink to an outside directory. The remediated adapter must raise `PersistenceBoundaryError` and create the target in neither the outside directory nor the moved original parent.

## Fresh exact-candidate execution

This review did not treat the implementation Engineer disposition or manifest as sufficient evidence. I independently inspected the exact candidate source, test source, candidate/evidence identities, prior blocking review, and workflow commands, then triggered a fresh rerun of the candidate-bound P6 workflow.

Fresh rerun observations:

- workflow run: `32750484738`
- fresh rerun job: `97518120191`
- checked-out detached candidate: `091e9ac97f0a068045acbcc57e90a934d24f9f7a`
- persistence-adapter blob verification: PASS, `58350007067f0443b65758992b1a17323123271d`
- P6 test blob verification: PASS, `e067ba772e9323c2a3bdfd93ddf343c4fadf2a28`
- closed P5 builder/test blob preservation: PASS
- exact P6 pytest suite: **10/10 PASS**
- exact P6 unittest suite: **10/10 PASS**
- unaffected P0-P5 regressions: **136 passed, 1 inherited transition sentinel deselected, 160 subtests passed**
- fresh rerun artifact: `9530223776`

The fresh direct pressure probes produced:

- `P6_IDEMPOTENT_REPLAY_PASS status=NO_CHANGE`
- `P6_IMMUTABLE_COLLISION_PASS code=IMMUTABLE_OUTPUT_COLLISION`
- `P6_OMITTED_BOUNDARY_EVIDENCE_FAIL_CLOSED_PASS`
- `P6_PARENT_SWAP_FAIL_CLOSED_PASS`

The fresh parent-swap probe verified that no artifact was written either outside the output root or into the moved original parent.

## Prior blocker dispositions

### Blocker 1: lifecycle-store boundary evidence omission

**REMEDIATED.**

The API no longer converts omission into an empty exclusion set. Omitted lifecycle-boundary evidence raises `PersistenceBoundaryError` before any write. The exact candidate regression and the fresh pressure execution both reproduced the omitted-evidence case and observed fail-closed/no-write behavior.

### Blocker 2: parent-directory replacement escape

**REMEDIATED.**

The publication path is now resolved by the kernel relative to a verified output-root descriptor under resolve-beneath/no-symlink constraints. The deterministic prior attack shape now fails closed, and fresh execution observed no target creation outside the root or in the moved parent.

No unsafe pathname fallback is used when the required race-resistant primitive is unavailable.

## Inherited reds preserved separately

The fresh rerun retained the previously classified non-P6-local reds rather than converting them into passing evidence:

1. `P1B_PS19_CLASSIFIER_MISMATCH`;
2. `EXPECTED_AMENDMENT_TO_P5_TRANSITION_SENTINEL`;
3. `LEGACY_V1_RUNTIME_ISOLATION_MUTABLE_SCHEMA_REFERENCE`; and
4. `EXTRACTION_PARITY_DISTILLER_DIRECTIVE_MISMATCH` remains separately reproduced by the extraction-parity check.

No additional P6-local failure was observed.

## Independent review disposition

**P6_INDEPENDENT_REVIEW_PASS**

Candidate `091e9ac97f0a068045acbcc57e90a934d24f9f7a` satisfies the independently reconstructed P6 persistence-adapter gate on the inspected and freshly executed evidence. Both prior blocking findings are remediated, exact replay/collision semantics remain correct, P5 purity is preserved, and no new P6-local blocker was identified.

This independent PASS does not itself close P6. P6 Steward reconciliation is not established by this review, and this review performs no Steward operation.

P7+, admission, canonical mutation, authority mutation, or activation work must not begin from this review without the separately required selection and governance boundary.

## Terminal boundary and next role

The independent P6 review work unit is complete. A meaningful role boundary has been reached because any P6 reconciliation belongs to the Project Engineering Steward rather than this independent Engineer activation.

If continuation is explicitly selected, the receiving role should be a fresh Project Engineering Steward scoped only to reconciliation of exact candidate `091e9ac97f0a068045acbcc57e90a934d24f9f7a` against this independent review and the bound Engineer evidence. Required Steward authority and activation must be independently established under the live repository contracts; this review, branch, handoff, or role label does not create them.

Stop before P7+ or any other successor work unit.