# P10-G9 remediation Engineer evidence construction

Status: **EVIDENCE CONSTRUCTION ONLY; INDEPENDENT G9 RE-REVIEW REQUIRED**

Repository: `loteque/reasoning-distiller`

Coordination control: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`

Governing P10 Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`

Plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`

Reviewed semantic candidate: `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`

Candidate tree: `81178c5efdc8f1419a068c61a92c0571b28f69fc`

Prior Engineer evidence head: `99da31f907093be6ad53aee7e9d5db249f5cd3d0`

Prior evidence PR: `#90`

Prior independent disposition: `P10_G9_INDEPENDENT_REVIEW_CHANGES_REQUIRED`

Blocking finding: `P10_G9_REMEDIATED_CANDIDATE_BOUND_EVIDENCE_NOT_FULLY_ESTABLISHED`

## Engineer diagnosis

The inspected semantic candidate contains substantive code/harness remediations for the two prior semantic mechanisms:

- `P10_PI09_ELIGIBILITY_CONSUMER_UNBOUND`: the `/2` prepare path now validates the eligibility consumer contract and consumer ID against the frozen production constants `reasoning-distiller-invocation/2` and `rd-distill`, rather than merely comparing two mutually mutable input artifacts.
- `P10_G8_PS19_BASELINE_MASKS_LATER_NEGATIVE_REGRESSIONS`: the corrected evidence harness executes every P1b negative other than inherited PS-19 independently, then reproduces PS-19 alone as the inherited baseline mismatch.

The remaining G9 blocker is therefore treated as an **evidence-construction gap unless the new complete proof exposes a semantic defect**. This evidence branch does not change production behavior.

## Exact proof construction

`.github/workflows/p10-g9-ae5d5c21-engineer-evidence.yml` is bound to the exact semantic candidate and candidate tree above. It intentionally checks out the semantic candidate rather than the evidence branch head.

The workflow must establish all of the following on one exact tuple:

1. exact candidate commit and tree;
2. exact CPython `3.12.0` / `cpython-312` runtime;
3. one release package built from that candidate as `0.0.0-p10-g9-r1`;
4. package transport digest, manifest digest, managed roots, file count, and `content_identity`;
5. exact package rehydration before P10/runtime regressions;
6. complete P10 G0-G7 plus G9-remediation candidate suite;
7. installed `rd-distill prepare` PI-09 adversarial execution for both wrong consumer-contract and wrong consumer-ID variants, with both pack and eligibility inputs made mutually consistent and request digests updated;
8. fail-closed PI-09 result at the public installed entrypoint: exit `2`, stage `preflight`, reason `PROFILE_ELIGIBILITY_MISMATCH`, with no prepared invocation or provenance registry persisted;
9. a mechanically complete PI-01 through PI-60 ledger derived from the frozen G0 table, with every ID attached to executed P10 witness suites and PI-09 attached to the installed-entrypoint witness;
10. fixed production `/1` regressions;
11. P1 schema baseline;
12. every P1b negative except inherited PS-19 in one independent invocation whose selected IDs are emitted into the evidence;
13. inherited PS-19 reproduced alone and required to show the known `PLANE_CLASSIFICATION_CONFLICT` versus `UNKNOWN_SEMANTICS_FIELD` mismatch;
14. unaffected P0-P9 regressions with only the two already-governed exclusions used by G8;
15. package-builder and installer regressions;
16. one uploaded evidence artifact containing the exact tuple, logs, package/manifest, PI ledger, P1/P1b records, and status matrix.

## Candidate versus evidence identity

No production semantic change is made by this remediation work unit unless the candidate-bound proof fails in a way that establishes a new semantic defect.

Accordingly:

- semantic candidate remains `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`;
- semantic candidate tree remains `81178c5efdc8f1419a068c61a92c0571b28f69fc`;
- the evidence branch is a separate durable proof surface and must not be mistaken for a new production semantic candidate;
- a successful workflow execution is Engineer execution evidence only, not an independent G9 PASS disposition.

## Authority and terminal boundary

This work unit performs no G10 Steward reconciliation, admission, canonical mutation, role registration, RIL activation, Steward-authorization mutation, authority mutation, or later P10 gate.

If the new exact proof passes, the next consequential work belongs to a **fresh independent P10-G9 implementation reviewer**. That reviewer must independently re-resolve live coordination/contracts and challenge the exact semantic candidate against the new bound evidence. This Engineer work unit cannot issue `P10_INDEPENDENT_REVIEW_PASS` for its own evidence.
