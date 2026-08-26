# P10-G9 PI witness remediation Engineer evidence construction

Status: **EVIDENCE CONSTRUCTION ONLY; FRESH INDEPENDENT G9 RE-REVIEW REQUIRED**

Repository: `loteque/reasoning-distiller`

Coordination control: `main@80b6e89ad2efe84b088ca06b908a257c449fac15`

Governing P10 Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`

Plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`

Semantic candidate: `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`

Candidate tree: `81178c5efdc8f1419a068c61a92c0571b28f69fc`

Reviewed prior Engineer evidence head: `cfc314edf2c9d2440eac2a96643766d5fb97cd64`

Evidence PR: `#91`

Independent disposition: `P10_G9_INDEPENDENT_REVIEW_CHANGES_REQUIRED`

Blocking finding: `P10_G9_PI_WITNESS_LEDGER_INSUFFICIENT`

## Engineer diagnosis

The prior G9 execution itself was successful, but its PI-01 through PI-60 ledger used broad suite-file attribution rather than proving a concrete executed or mechanically inspectable witness for each frozen pressure case. Independent review immediately identified PI-05, PI-06, and PI-10 as unproven mappings.

Live inspection found existing fail-closed production branches for those states. Candidate-bound direct execution subsequently exercised the repaired witness harness without exposing a semantic implementation defect. The semantic candidate is therefore preserved unless later exact evidence falsifies it.

This branch is an evidence surface only. It does not alter production semantic bytes in candidate `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`.

## Exact witness construction

The remediation replaces broad suite-file attribution with one traceable witness for every frozen PI case.

Direct candidate/package/runtime execution covers cases whose existing test node did not instantiate the frozen pressure state precisely enough, including:

- PI-04, PI-05, PI-06, PI-08, PI-09, PI-10, PI-11, PI-12, PI-13;
- PI-27, PI-28, PI-29;
- PI-34, PI-36, PI-37, PI-38, PI-39;
- PI-41, PI-42, PI-44, PI-59.

The direct probes install the exact package built from the semantic candidate and exercise the installed `/2` runtime or exact finalization path. They assert the expected stage/reason code, output absence or immutability where applicable, and success invariants for positive cases.

PI-14 and PI-52 use an actual CPython `3.12.1` execution of the exact unsupported-runtime G7 witness. That runtime witness is isolated from the main evidence job so the main tuple remains on CPython `3.12.0` / `cpython-312` for its entire execution.

Every remaining PI case is bound to an exact pytest node ID rather than a broad test file. The generated ledger is derived from the frozen G0 `PRESSURE_CASES` table and fails unless PI-01 through PI-60 are covered exactly once by direct execution, the unsupported-runtime witness, or an exact node-ID mapping.

## Exact evidence tuple

The final G9 evidence workflow must establish all of the following:

1. semantic candidate `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e` and tree `81178c5efdc8f1419a068c61a92c0571b28f69fc`;
2. governing Stage 3 plan and blob above;
3. main evidence runtime CPython `3.12.0` / `cpython-312`;
4. one exact release package built from the semantic candidate, including transport digest, manifest digest, content identity, managed roots, and file count;
5. exact package rehydration before candidate/runtime tests;
6. complete P10 candidate suite;
7. direct PI witness harness execution against the exact package;
8. isolated actual CPython `3.12.1` unsupported-runtime witness for PI-14 and PI-52;
9. mechanically complete exact-witness PI-01 through PI-60 ledger;
10. fixed production `/1` regressions;
11. P1 schema baseline;
12. every P1b negative except inherited PS-19, with selected IDs emitted;
13. inherited PS-19 reproduced alone with its governed known mismatch;
14. unaffected P0-P9 regressions under the already-governed exclusions;
15. package-builder and installer regressions;
16. uploaded package, manifest, runtime record, exact witness scripts and digests, direct witness results, unsupported-runtime log, exact-node log, PI ledger, regression logs, and summary tuple;
17. a final gate marker emitted only after all required evidence has passed.

## Evidence-construction diagnostics

Two intermediate evidence-only runs are retained as diagnostics and are not semantic candidate failures:

- run `32930085320` passed candidate/package setup and the complete P10 suite, then failed before PI execution because the downloaded witness script started with `/tmp` rather than the candidate checkout on `sys.path`;
- run `32930277830` passed the complete P10 suite, the full direct PI witness set, and the actual CPython `3.12.1` unsupported-runtime witness, then failed because repeated `setup-python` use did not restore the shell's active interpreter to `3.12.0`.

The final construction removes that runtime-switch ambiguity by isolating unsupported-runtime execution in its own job and keeping the full evidence job on exact CPython `3.12.0` throughout.

## Candidate versus evidence identity

The semantic candidate remains `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e` with tree `81178c5efdc8f1419a068c61a92c0571b28f69fc` unless exact testing establishes a semantic defect.

The evidence branch head is a separate durable proof identity. It must not be substituted for the production semantic candidate.

A successful evidence workflow is Engineer execution evidence only. It is not an independent G9 PASS disposition.

## Authority and terminal boundary

This work unit performs no G10 Steward reconciliation, admission, canonical mutation, role registration, RIL activation, Steward-authorization mutation, authority mutation, or later P10 gate.

After exact evidence passes, the next consequential work belongs to a **fresh independent P10-G9 implementation reviewer**. That reviewer must independently re-resolve live coordination/contracts and challenge the exact semantic candidate, package/runtime tuple, direct witnesses, and complete PI ledger. This Engineer work unit cannot review or approve its own evidence.
