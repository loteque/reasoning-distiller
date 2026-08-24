# P6 Independent Review: Persistence Adapter

Disposition: **P6_INDEPENDENT_REVIEW_CHANGES_REQUIRED**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision independently resolved before review: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Coordination revision re-resolved immediately before this review write: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing plan commit: `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`
- Governing plan blob: `8474d2da42f863f0a190fd80292085176d3f97f0`
- Closed P5 semantic base: `d96071ab833179948e5f9526cdb63c15c6451ff4`
- Exact P6 semantic candidate: `99724c025d09714c7d369ddeda0a33be8078f602`
- Candidate persistence-adapter blob: `808903dd2c5aced74ced4a28992c0d6145bdfdaf`
- Engineer execution evidence: `99911c51bb6858a4732f35afe054c800d0b99acc`
- Engineer disposition: `P6_PERSISTENCE_ADAPTER_ENGINEER_EXECUTION_PASS`
- Active review role: fresh independent Reasoning Graph Protocol Engineer, P6 review only.

The current Engineer directive and Project chat-transition amendment were read from the live coordination revision. This review establishes no Steward authority, reconciliation, admission, canonical standing, authorization, activation, or P7+ successor scope.

## Independent reconstruction of the P6 gate

The approved P6 gate is an optional persistence operation separated from the pure P5 builder. It may publish immutable derived-artifact bytes only outside canonical, admission, reconciliation, authorization, role, activation-evidence, and other authority/canonical lifecycle stores. Exact replay must return `NO_CHANGE`; different existing bytes must fail collision without overwrite; persistence/cache state must not affect P5 semantic bytes; and storage must not grant semantic or canonical standing.

The approved invariants also require persistence to remain separate from pure build, immutable/idempotent, and bounded to the caller-selected derived-artifact location. Missing authority/canonical-standing evidence remains missing rather than inferred.

## Candidate and bound-evidence inspection

The candidate is four commits ahead of the closed P5 base and changes exactly:

- `context_packaging/__init__.py`;
- `context_packaging/persistence_adapter.py`;
- `tests/test_context_packaging_persistence_adapter_p6.py`.

The P5 builder and P5 test blobs are preserved as recorded by the Engineer evidence.

The Engineer workflow run `32747648308` completed successfully. Its workflow definition checks out exact candidate `99724c025d09714c7d369ddeda0a33be8078f602`, verifies the P6 and preserved P5 blobs, runs the exact eight-case P6 suite under both pytest and unittest, runs unaffected P0-P5 regressions, and preserves inherited reds separately. The durable execution manifest records 8/8 P6 PASS under each harness, unaffected P0-P5 regression PASS, and no additional P6-local failure in the standing CI observation.

This review independently inspected the workflow definition and durable manifest rather than treating the Engineer disposition alone as sufficient evidence.

## Independent executable pressure tests

The exact `context_packaging/persistence_adapter.py` candidate bytes were reconstructed locally from the live GitHub candidate and verified with `git hash-object` to equal blob `808903dd2c5aced74ced4a28992c0d6145bdfdaf` before execution.

Positive checks reproduced the intended basic behavior:

- first exact-byte publication returns `PERSISTED`;
- exact replay returns `NO_CHANGE`;
- different existing bytes raise `ImmutableOutputCollisionError` without overwrite.

Two additional P6-local pressure probes failed the gate.

## Blocking finding 1: lifecycle-store exclusion is optional rather than fail-closed

`persist_immutable_artifact` declares:

```python
prohibited_roots: Sequence[str | os.PathLike[str]] = ()
```

The adapter treats `output_root` as a caller-declared derived-artifact boundary, but no required machine-checkable evidence establishes that the selected root is actually outside canonical/authority lifecycle stores. The only concrete lifecycle exclusion is the optional `prohibited_roots` sequence.

Independent probe:

1. create a directory named as a canonical lifecycle location;
2. pass that directory as `output_root`;
3. omit `prohibited_roots`;
4. request a new artifact write.

Observed result: **`PERSISTED`**, and the artifact bytes were created in that lifecycle-like root.

The candidate test and Engineer pressure probe cover only the positive case where the caller already supplies the lifecycle root in `prohibited_roots`. They do not test the omitted-boundary case.

### Why this blocks P6

The approved plan permits persistence only to a caller-selected location that is explicitly outside canonical, admission, reconciliation, authorization, role, and activation-evidence stores. A default-empty exclusion set allows the persistence primitive to proceed when that required outside-lifecycle condition is not established. Under the project's fail-closed/unknown-state posture, absence of the boundary declaration cannot be converted into permission to write.

### Required remediation

Make the lifecycle/derived-artifact boundary explicit and required at the persistence API boundary rather than silently defaulting to no exclusions. The exact representation is an implementation choice, but a call lacking sufficient boundary evidence must fail closed. Add a regression proving that lifecycle exclusion cannot be omitted and still yield `PERSISTED` for a lifecycle target.

This finding does not require path-name inference by the generic adapter; project-specific lifecycle roots/boundary evidence remain caller supplied.

## Blocking finding 2: parent-directory swap can escape `output_root`

The implementation resolves the target parent, checks that resolved parent is under `output_root`, then later publishes using path-based `os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, ...)`.

That creates a time-of-check/time-of-use gap. The directory path can change after the containment check and before the publication syscall.

Independent deterministic pressure probe:

1. create `output_root/sub` and a separate `outside` directory;
2. request `relative_path='sub/pack.bin'`;
3. immediately before the candidate's real `os.open`, rename the checked `sub` directory and replace the lexical `sub` path with a symlink to `outside`;
4. allow the candidate's original `os.open` to continue.

Observed result:

- adapter returned **`PERSISTED`**;
- `outside/pack.bin` was created with the requested bytes;
- the publication escaped the declared output root.

### Why this blocks P6

P6 is specifically a bounded immutable write operation. A successful write outside the checked output boundary violates the persistence boundary and can bypass any lifecycle-store separation established by the earlier path check. The existing `../` and pre-existing-target-symlink tests do not cover parent replacement between check and write.

### Required remediation

Anchor publication to a stable checked directory handle or equivalent race-resistant filesystem primitive, and prevent symlink/reparse traversal at publication time. The implementation must ensure that the object actually created is beneath the verified output boundary at the moment of mutation, not only at an earlier pathname check. Add a deterministic parent-swap regression.

## Non-blocking observations

- Exact replay/collision semantics are otherwise sound in the ordinary no-race case inspected.
- The adapter returns only status, digest, and byte count; storage path naming does not itself synthesize authority/canonical-standing fields.
- The P5 builder remains separate from this persistence module, and the Engineer evidence demonstrates that output presence does not alter a successful P5 build.
- The inherited P1b classifier mismatch, legacy runtime-isolation mutable schema reference, extraction-parity directive mismatch, and the amendment-era P5 transition sentinel remain separate from these P6-local findings.

## Independent review disposition

**P6_INDEPENDENT_REVIEW_CHANGES_REQUIRED**

Candidate `99724c025d09714c7d369ddeda0a33be8078f602` does not satisfy the P6 persistence boundary because:

1. required outside-lifecycle-store evidence can be omitted while publication still succeeds; and
2. a checked in-root parent path can be replaced before publication, allowing the actual write to escape `output_root`.

The Engineer execution evidence remains valid as evidence for the tested behaviors it records, but its passing suite is not sufficient to close P6 in the presence of these independent blocking cases.

P6 is **not closed**. Steward reconciliation must not begin on this candidate as an accepted P6 implementation, and P7+ must not begin from this review.

## Exact next action

Receiving role: fresh Reasoning Graph Protocol / implementation Engineer.

Remediate only the two P6-local blockers above on top of the closed P5 basis, add regressions for omitted boundary evidence and parent-directory replacement, preserve P5 purity and all existing P6 semantics, produce a new immutable P6 candidate with candidate-bound execution evidence, then hand that exact candidate to a fresh independent P6 review activation.
