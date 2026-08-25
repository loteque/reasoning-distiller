# P10-G3 Engineer execution evidence

## Evidence identity

- Repository: `loteque/reasoning-distiller`
- Coordination control: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`
- Governing plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- Closed G2 base: `95eac1148744d90b9074cbdfce82edfe4751f87a`
- Exact G3 semantic candidate: `48e272e35f902a9f6e0ee4111e6220cbcef1d7cd`
- Evidence trigger commit: `af6cebe1f046be011882c85bf01e90c09925aa9f`
- Evidence branch: `evidence/p10-g3-48e272e3-engineer-20260825`
- Evidence PR: `#82`
- Accepted candidate-bound workflow run: `32896730036`
- Runtime: CPython `3.12.0`, cache tag `cpython-312`
- Disposition: `P10_G3_PROVENANCE_BRIDGE_ENGINEER_EXECUTION_PASS`

## Candidate-bound closure

The accepted workflow checked out the immutable semantic candidate
`48e272e35f902a9f6e0ee4111e6220cbcef1d7cd` directly in every evidence job.
The pull-request head contained only the evidence workflow; the tests did not
execute the mutable PR head.

The exact G3 job established all of the following before running the G3 gate:

- checked-out `HEAD` exactly matched the G3 candidate;
- merge-base with G2 exactly matched
  `95eac1148744d90b9074cbdfce82edfe4751f87a`;
- the complete G2-to-G3 semantic delta was exactly:
  - `.gitattributes`;
  - `context_packaging/__init__.py`;
  - `context_packaging/provenance_bridge.py`;
  - `docs/implementation/context-packaging/P10_G3_PROVENANCE_BRIDGE.md`;
  - `tests/test_context_packaging_production_integration_p10_g3.py`;
- runtime identity was CPython `3.12.0` / `cpython-312`.

## Observed successful jobs

Run `32896730036` completed with workflow conclusion `success`. All three jobs
completed successfully:

1. `g3-provenance-bridge`
   - exact immutable-candidate, ancestry, bounded-delta, and runtime assertions;
   - exact G3 provenance regression gate.

2. `g3-package-regressions`
   - exact candidate assertion;
   - G2 installed-package closure regression;
   - P6 immutable persistence regression;
   - package-builder and installer regressions.

3. `g3-predecessor-regressions`
   - G0 pressure/failure freeze regression;
   - G1 protocol/handoff freeze regression;
   - G2 package-closure regression;
   - P9 renderer identity, closed-bundle, execution-binding, deterministic
     renderer, and RI-15 remediation regressions;
   - fixed production-invocation regression.

## G3 properties covered by the candidate-bound gate

The G3 gate exercises the provenance bridge against the frozen G1 identity
rules and adversarial closure conditions, including:

- binding-derived stable source IDs using the frozen provenance-binding domain;
- complete stable source records for repository-control, package-control,
  canonical-state, and operational-evidence sources;
- stable source records remaining unchanged across different pack-local
  positions;
- distinct immutable source snapshots producing distinct source identities;
- pack-local occurrence records binding exact pack identity, rendered frame,
  plane, item index, and source ID;
- exact rendered metadata and plane-item frame closure over the sealed pack;
- exact model-visible payload digest agreement with the resolved source binding;
- unresolved or ambiguous frame/source resolution failing closed;
- forced same-source-ID/different-record collision failing closed with
  `PROVENANCE_SOURCE_COLLISION`;
- reordered or missing model-visible frames failing closed;
- deterministic provenance-registry identity using the frozen registry domain;
- immutable registry persistence through the existing P6 publication boundary;
- registry-identity tampering being rejected before persistence.

## Authority and scope boundary

This evidence is Engineer execution evidence for P10-G3 only. It records an
observed candidate-bound execution result. It does not establish Steward
reconciliation, admission, canonical standing, Project authority, role
activation, authorization, or any mutation of canonical or authority state.

No P10-G4 prepare integration, provider transport, finalization, reconciliation,
admission, canonical mutation, or authority mutation was performed as part of
this evidence.
