# P10-G5 Engineer execution evidence

## Evidence identity

- Repository: `loteque/reasoning-distiller`
- Coordination control: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`
- Governing plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- Closed G4 semantic base: `e98b11bf82bc6c47f848597e5410b9c603d2ba34`
- G4 Engineer evidence: `1e4343193bc12a921259fd66ec9c3502b00093ab`
- Exact G5 semantic candidate: `22127c82608d8bd23562a29a4f63703ccb872565`
- Evidence trigger commit: `1f2e0599eda58438c38ce8b4e91ff92f75dfe8e0`
- Evidence branch: `evidence/p10-g5-22127c82-engineer-20260825`
- Evidence PR: `#85`
- Successful candidate-bound workflow run: `32906348331`
- Runtime: CPython `3.12.0`, cache tag `cpython-312`
- Disposition: `P10_G5_PROVIDER_TRANSPORT_ENGINEER_EXECUTION_PASS`

## Candidate-bound closure

The successful workflow checked out immutable semantic candidate
`22127c82608d8bd23562a29a4f63703ccb872565` directly in every evidence job.
The pull-request head contained only the evidence workflow; candidate execution
did not depend on the mutable evidence-PR head.

The exact G5 job established all of the following before running the G5 gate:

- checked-out `HEAD` exactly matched the G5 semantic candidate;
- merge-base with the closed G4 base exactly matched
  `e98b11bf82bc6c47f848597e5410b9c603d2ba34`;
- the complete G4-to-G5 semantic delta was exactly:
  - `context_packaging/model_transport.py`;
  - `tests/test_context_packaging_production_integration_p10_g5.py`;
- runtime identity was CPython `3.12.0` / `cpython-312`;
- the G5 implementation and tests compiled before execution.

## Observed successful jobs

Run `32906348331` completed with workflow conclusion `success`. All three
candidate-bound jobs completed successfully:

1. `g5-provider-transport` (`97991209176`)
   - exact immutable-candidate, G4 ancestry, bounded-delta, and runtime checks;
   - exact G5 model-transport/reference-runner conformance gate.

2. `g5-package-prepare-regressions` (`97991209093`)
   - exact candidate assertion;
   - G2 package-closure, G3 provenance-bridge, and G4 preparation regressions;
   - package-builder, package-contract, and installer regressions.

3. `g5-contract-predecessor-regressions` (`97991209137`)
   - G0 pressure/failure freeze regression;
   - G1 protocol/handoff freeze regression;
   - P9 renderer identity, closed-bundle, execution-binding, deterministic
     renderer, and RI-15 remediation regressions;
   - fixed production-invocation regression.

## G5 properties covered by the candidate-bound gate

The G5 gate implements and exercises the frozen
`reasoning-distiller-model-transport/1` boundary without crossing into G6
finalization. Covered properties include:

- exact runner binding to the persisted `reasoning-distiller-prepared-invocation/1`
  identity supplied to the runner;
- exact activation-bundle raw-byte and domain-separated identity continuity from
  the G4 prepared invocation;
- installed-package content-identity continuity after prepare and before provider
  execution;
- support for only the prepared package-owned `reference` adapter, with other
  provider adapters failing closed as `MODEL_TRANSPORT_NONCONFORMING`;
- deterministic construction and schema validation of the frozen
  `reasoning-distiller-model-transport/1` binding and transport identity;
- the installed Distiller directive and frozen activation instruction remaining
  on a distinct `framework_instruction` surface;
- the P9 rendered activation remaining project context with explicit structural
  `control`, `knowledge`, and `operational_evidence` planes;
- exact rendered frame order, base64 payload bytes, payload digests, and plane
  labels preserved without text-sensitive flattening or promotion;
- project context `control` not acquiring provider system or developer authority;
- instruction-shaped knowledge and operational-evidence payloads remaining in
  their original evidence planes;
- exact provenance-registry artifact continuity, stable source IDs, and one-to-one
  frame occurrence mappings preserved into the reference provider request;
- no project memory, prior chats, prior candidates, canonical interpretations,
  ambient repository state, or other project context added by the transport;
- the frozen non-hostile/reference-runner threat model carried exactly, including
  `OUTSIDE_P10` for malicious provider/runner attestation;
- provider-returned model bytes passed back to the caller byte-for-byte without
  parsing, validation, normalization, persistence, or reinterpretation;
- malformed prepared identity, activation-bundle mismatch, installed-package
  drift, unsupported adapter selection, authority promotion, plane flattening,
  extra project context, and non-byte provider output failing before any valid
  G5 result can be claimed;
- package closure includes both `context_packaging/model_transport.py` and the
  frozen `schemas/model-transport.schema.json` artifact;
- no raw-candidate, submission, or invocation-result artifact publication by G5.

## Authority and scope boundary

This artifact is Engineer execution evidence for P10-G5 only. It records an
observed candidate-bound execution result. It does not establish independent
review, Steward reconciliation, tranche closure, admission, canonical standing,
Project authority, role activation, authorization, or any mutation of canonical
or authority state.

No P10-G6 finalization, P10-G7+ implementation, independent review, Steward
reconciliation, admission, canonical mutation, role registration, authority
mutation, or activation-state mutation was performed as part of this evidence.
