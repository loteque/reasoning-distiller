# P10-G4 Engineer execution evidence

## Evidence identity

- Repository: `loteque/reasoning-distiller`
- Coordination control: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`
- Governing plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- Closed G3 base: `48e272e35f902a9f6e0ee4111e6220cbcef1d7cd`
- Exact G4 semantic candidate: `e98b11bf82bc6c47f848597e5410b9c603d2ba34`
- Evidence trigger commit: `7b8e76e9549205ca26d45d551e82b8f7be60a236`
- Evidence branch: `evidence/p10-g4-e98b11bf-engineer-r2-20260825`
- Evidence PR: `#84`
- Successful candidate-bound workflow run: `32905037478`
- Runtime: CPython `3.12.0`, cache tag `cpython-312`
- Disposition: `P10_G4_PREPARE_INTEGRATION_ENGINEER_EXECUTION_PASS`

## Candidate-bound closure

The successful workflow checked out immutable semantic candidate
`e98b11bf82bc6c47f848597e5410b9c603d2ba34` directly in every evidence job.
The pull-request head contained only the evidence workflow; the tests did not
execute the mutable evidence-PR head.

The exact G4 job established all of the following before running the G4 gate:

- checked-out `HEAD` exactly matched the G4 candidate;
- merge-base with the closed G3 base exactly matched
  `48e272e35f902a9f6e0ee4111e6220cbcef1d7cd`;
- the complete G3-to-G4 semantic delta was exactly:
  - `context_packaging/prepare_integration.py`;
  - `runtime/rd_distill.py`;
  - `tests/test_context_packaging_production_integration_p10_g4.py`;
- runtime identity was CPython `3.12.0` / `cpython-312`;
- the G4 implementation and tests compiled before execution.

## Observed successful jobs

Run `32905037478` completed with workflow conclusion `success`. All three
candidate-bound jobs completed successfully:

1. `g4-prepare-integration` (`97987131062`)
   - exact immutable-candidate, G3 ancestry, bounded-delta, and runtime checks;
   - exact G4 prepare-integration regression gate.

2. `g4-package-persistence-regressions` (`97987130932`)
   - exact candidate assertion;
   - G2 package-closure regression;
   - G3 provenance-bridge regression;
   - P6 immutable-persistence regression;
   - package-builder, package-contract, and installer regressions.

3. `g4-predecessor-regressions` (`97987130685`)
   - G0 pressure/failure freeze regression;
   - G1 protocol/handoff freeze regression;
   - G2 package-closure regression;
   - G3 provenance-bridge regression;
   - P9 renderer identity, closed-bundle, execution-binding, deterministic
     renderer, and RI-15 remediation regressions;
   - fixed production-invocation regression, including legacy isolated `/1`
     preparation compatibility.

## G4 properties covered by the candidate-bound gate

The G4 gate exercises deterministic production preparation against the frozen
G1 schemas and the closed G2/G3/P9/P6 boundaries. Covered properties include:

- strict `reasoning-distiller-invocation/2` request shape and sealed locators;
- normalized project-relative path handling and fail-closed path/symlink checks;
- pairwise output-path collision checks and sealed-input/output separation;
- the sealed context pack remaining the sole project-evidence root during G4;
- no reopening of original repository evidence named by sealed source bindings;
- exact context-pack raw-byte digest and declared pack-identity validation;
- exact renderer-profile raw-byte, profile, pack-profile, and P9 execution-binding
  validation;
- exact eligibility-artifact raw-byte, eligible-decision, profile, and sealed-pack
  summary validation;
- exact CPython `3.12.0` / `cpython-312` runtime enforcement;
- installed-package manifest, content identity, required behavior-bearing files,
  file bytes/modes, and managed-root closure validation;
- rendering only through the closed P9 renderer;
- provenance derivation only through the closed G3 provenance bridge;
- immutable provenance-registry persistence through the existing P6 boundary;
- construction of the frozen `reasoning-distiller-activation-bundle/2`, including
  exact installed Distiller directive bytes, the frozen activation instruction,
  rendered activation, provenance registry, and domain-separated identity;
- construction of `reasoning-distiller-prepared-invocation/1` with continuity
  across request, pack, profile, eligibility, installed package, directive,
  validator, provenance registry, rendered activation, P9 execution binding,
  runtime ABI, activation bundle, and model-transport identity;
- immutable prepared-invocation persistence through the existing P6 boundary;
- exact activation-bundle bytes emitted by `/2` preparation and bound by the
  prepared-invocation raw digest;
- no raw-candidate, submission, or invocation-result publication by G4;
- deterministic replay yielding exact bytes and immutable `NO_CHANGE` outcomes;
- fail-closed context-pack drift, eligibility rejection, installed-package
  tamper, prepared-output collision, and provenance-registry collision behavior;
- production CLI normalization of provenance-registry persistence collision to
  `IMMUTABLE_OUTPUT_COLLISION` rather than `INTERNAL_ERROR`;
- explicit `/2` dispatch without changing the untouched legacy `/1` core;
- absence of provider/model execution, finalization, admission, or canonical
  mutation from the G4 prepare implementation.

## Superseded first candidate and failed evidence

The first G4 semantic candidate,
`0e122816ea09271a54660bb218bce8d49986dcf1`, was exercised by candidate-bound
workflow run `32904519892` through evidence trigger commit
`3698df30ee7265476048e0bd4c26e4cd06d87e7d` and PR `#83`. That run is not PASS
evidence and is superseded by the candidate and run recorded above.

The first run exposed two concrete defects:

- the G4 schema-validation test registry omitted a referenced schema resource;
- legacy isolated `/1` preparation imported the new G4 package before request
  contract dispatch, violating the existing isolated-runtime compatibility
  boundary.

The remediated candidate loads the complete local schema registry for the G4
schema gate, inspects request contract before importing the G4 package, and adds
an adversarial production-CLI provenance-registry collision check. The successful
run `32905037478` re-executed the G4 gate and predecessor/package/persistence
regressions against that exact remediated candidate.

## Authority and scope boundary

This artifact is Engineer execution evidence for P10-G4 only. It records an
observed candidate-bound execution result. It does not establish independent
review, Steward reconciliation, tranche closure, admission, canonical standing,
Project authority, role activation, authorization, or any mutation of canonical
or authority state.

No P10-G5 provider/model transport execution, P10-G6 finalization, P10-G7+
implementation, independent review, Steward reconciliation, admission, canonical
mutation, role registration, authority mutation, or activation-state mutation
was performed as part of this evidence.
