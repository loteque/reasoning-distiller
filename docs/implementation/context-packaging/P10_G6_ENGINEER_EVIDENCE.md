# P10-G6 Engineer execution evidence

## Evidence identity

- Repository: `loteque/reasoning-distiller`
- Coordination control: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`
- Governing plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- Closed G5 semantic base: `22127c82608d8bd23562a29a4f63703ccb872565`
- G5 Engineer evidence: `4c03957b48bec1a7df60afe3dce1dedfb9a47320`
- Exact G6 semantic candidate: `ed04d9f711d2c5298b3b86ca5bf5ea6937d4082a`
- Evidence trigger commit: `e78b7308f168b6fad45986f56bedcba4569798bd`
- Evidence branch: `evidence/p10-g6-ed04d9f7-engineer-20260825`
- Evidence PR: `#87`
- Successful candidate-bound workflow run: `32908277963`
- Runtime: CPython `3.12.0`, cache tag `cpython-312`
- Disposition: `P10_G6_FINALIZATION_ENGINEER_EXECUTION_PASS`

## Candidate-bound closure

The successful workflow checked out immutable semantic candidate
`ed04d9f711d2c5298b3b86ca5bf5ea6937d4082a` directly in every evidence job.
The pull-request head contained only the evidence workflow; candidate execution
did not depend on the mutable evidence-PR head.

The exact G6 job established all of the following before running the G6 gate:

- checked-out `HEAD` exactly matched the G6 semantic candidate;
- merge-base with the closed G5 base exactly matched
  `22127c82608d8bd23562a29a4f63703ccb872565`;
- the complete G5-to-G6 semantic delta was exactly:
  - `context_packaging/finalize_integration.py`;
  - `runtime/rd_distill.py`;
  - `tests/test_context_packaging_production_integration_p10_g6.py`;
- runtime identity was CPython `3.12.0` / `cpython-312`;
- the G6 implementation and tests compiled before execution.

## Observed successful jobs

Run `32908277963` completed with workflow conclusion `success`. All three
candidate-bound jobs completed successfully:

1. `g6-finalization` (`97996971094`)
   - exact immutable-candidate, G5 ancestry, bounded-delta, and runtime checks;
   - exact G6 finalization gate, including all six G6 tests.

2. `g6-p10-predecessor-regressions` (`97996971047`)
   - exact candidate assertion;
   - G2 package-closure, G3 provenance-bridge, G4 preparation, and G5 transport regressions;
   - package-builder, package-contract, and installer regressions.

3. `g6-contract-and-legacy-regressions` (`97996970853`)
   - G0 pressure/failure freeze regression;
   - G1 protocol/handoff freeze regression;
   - P9 renderer identity, closed-bundle, execution-binding, deterministic renderer, and RI-15 regressions;
   - fixed production-invocation `/1` regression.

## G6 properties covered by the candidate-bound gate

The G6 gate implements the frozen finalization boundary without crossing into
G7 migration, rollback, or compatibility work. Covered properties include:

- exact provider-returned bytes persisted immutably before parse, RGP validation,
  provenance validation, prepared-invocation verification, registry verification,
  transport-receipt verification, or installed-toolchain rejection;
- malformed raw provider JSON failing as `RAW_CANDIDATE_PARSE_FAILED` only after
  the exact raw bytes are durably preserved;
- exact persisted `reasoning-distiller-prepared-invocation/1` verification rather
  than reconstruction from current sealed inputs;
- exact persisted provenance-registry raw-byte and semantic-identity continuity
  against the prepared invocation, with drift failing closed as
  `PROVENANCE_REGISTRY_MISMATCH`;
- exact G5 `reasoning-distiller-model-transport/1` receipt continuity to the
  prepared invocation, activation bundle, adapter identity, frozen mapping, and
  frozen non-hostile/reference-runner threat boundary;
- installed CPython ABI, Distiller directive, RGP validator bytes, and complete
  package content identity checked against the exact prepared invocation;
- no reopening of sealed pack, renderer profile, profile-eligibility artifact,
  original project evidence, canonical state, project memory, prior chats, prior
  candidates, or ambient project context during finalization;
- ordinary RGP candidate validation through the exact installed validator;
- every candidate provenance source reference resolving within the exact
  prepared/persisted provenance registry, with unresolved references failing as
  `UNRESOLVED_PROVENANCE`;
- ordinary RGP Submission Protocol semantics and deterministic serialization
  preserved for the submission artifact;
- successful `reasoning-distiller-invocation-result/2` companion output linking
  the exact raw candidate, ordinary submission, prepared invocation, and
  provenance registry by locator plus raw and semantic identities;
- legacy production-invocation `/1` dispatch remaining on the existing core path;
- no post-hoc candidate repair, reconciliation, admission, canonical mutation,
  authority mutation, role registration, or activation-state mutation.

## Superseded failed evidence attempt

PR `#86` / run `32908007796` tested predecessor candidate
`ad08fea3be347b63cc4a7d57d4a5be932074624d`. Its predecessor and legacy jobs
passed and five of six G6 tests passed, but one assertion in the G6 test harness
referenced a nonexistent `PrepareResult.serialized_provenance_registry`
attribute. No PASS disposition was claimed for that candidate. The assertion was
corrected to hash the exact persisted registry bytes, producing semantic
candidate `ed04d9f711d2c5298b3b86ca5bf5ea6937d4082a`; fresh candidate-bound run
`32908277963` is the evidence used by this disposition.

## Authority and scope boundary

This artifact is Engineer execution evidence for P10-G6 only. It records an
observed candidate-bound execution result. It does not establish independent
review, Steward reconciliation, tranche closure, admission, canonical standing,
Project authority, role activation, authorization, or any mutation of canonical
or authority state.

No P10-G7+ implementation, independent review, Steward reconciliation,
admission, canonical mutation, role registration, authority mutation, or
activation-state mutation was performed as part of this evidence.
