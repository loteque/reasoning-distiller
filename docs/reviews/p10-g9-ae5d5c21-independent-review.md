# P10-G9 Independent Implementation Review

Disposition: **P10_G9_INDEPENDENT_REVIEW_PASS**

G9 gate token: **P10_INDEPENDENT_REVIEW_PASS**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Coordination control ref: `main`
- Coordination revision independently resolved at activation: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Coordination revision re-resolved immediately before disposition write: `80b6e89ad2efe84b088ca06b908a257c449fac15`
- Governing P10 Stage 3 plan: `b435dff827b745d711a5c5a297587a0c4359bed1`
- Governing plan blob: `eae54b9e2c0618faec61acf2f9e4acd942ec063d`
- Exact semantic candidate: `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`
- Exact candidate tree: `81178c5efdc8f1419a068c61a92c0571b28f69fc`
- Candidate branch re-resolved immediately before disposition write: `impl/p10-g9-remediation-20260825@ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`
- Exact Engineer evidence head: `ff09627f8e83abc60f430b378bed342cbeaceb79`
- Engineer evidence branch re-resolved immediately before disposition write: `evidence/p10-g9-ae5d5c21-engineer-20260825@ff09627f8e83abc60f430b378bed342cbeaceb79`
- Evidence PR: `#91`
- Exact successful evidence run: `32933482638`
- Supported-runtime/full evidence job: `98070222524`
- Unsupported-runtime witness job: `98070135523`
- Supported runtime: CPython `3.12.0`, implementation `cpython`, cache tag `cpython-312`
- Unsupported runtime witness: CPython `3.12.1`, implementation `cpython`, cache tag `cpython-312`
- Built package version: `0.0.0-p10-g9-r5`
- Built package content identity: `sha256:bd7d17faa026d3136e8d8be24a7d56dcec5ceace3b7c363310640de1219048fa`
- Built package transport SHA-256: `c7338985caf1a8147c7dd5457b3570e5f9cf6314087c7ac2468915a7d821902e`
- Built package file count: `97`
- Main evidence artifact: `p10-g9-ae5d5c21-evidence-r5`, artifact `9594064390`, artifact digest `sha256:7d3bb98b26e45a19ace3f4c628435e1b540f8f95d95d0d066f960d9db0a39fe0`
- Unsupported-runtime artifact: `p10-g9-unsupported-runtime-r5`, artifact `9594022071`, artifact digest `sha256:7b35ba6301bee1a1520c8f9d90b5bd2a3ec64add55ec8ef0de9d9fa330e8f619`
- Active role: fresh independent Reasoning Graph Protocol Engineer, P10-G9 review only.

The current Engineer directive, Project chat-transition amendment, and proposal-review method were read from the exact live coordination revision before consequential review work. The Engineer directive authorizes protocol/framework validation and review work but does not grant Project Steward authority, canonical semantic identity, admission authority, or canonical mutation authority.

This review establishes no G10 Steward reconciliation, Steward authorization, accepted Steward activation evidence, admission, canonical mutation, authority mutation, or successor-stage standing.

## Independently reconstructed G9 gate

The governing P10 Stage 3 plan requires G9 to be a fresh independent implementation review of the exact semantic candidate and its candidate-bound evidence. The reviewer must challenge, rather than merely endorse, at least:

1. PI-01 through PI-60 with the Stage-3-resolved PASS/FAIL ownership and stable failure classes;
2. installed package closure and package identity;
3. exact supported P9 runtime behavior and fail-closed unsupported-runtime behavior;
4. `/1` compatibility and noninterference;
5. exact prepared-invocation identity across prepare, transport, and finalize;
6. provenance-registry derivation, persistence, validation, and downstream handoff;
7. the fixed production evidence boundary, including exclusion of Project memory, prior chats, prior candidates, ambient repository files, and provider-added context;
8. provider transport preservation and non-promotion of context planes;
9. immutable output behavior and failure ordering; and
10. the explicit non-hostile/reference-runner threat boundary.

The G9 exit criterion is `P10_INDEPENDENT_REVIEW_PASS` or an equivalent exact PASS. A blocking finding returns work to implementation. G10 is a distinct subsequent Steward stage and is outside this activation.

## Candidate inspection

Candidate `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e` and tree `81178c5efdc8f1419a068c61a92c0571b28f69fc` were inspected independently from the evidence branch.

The P10-G9 semantic remediation relevant to the prior PI-09 blocker is present in `context_packaging/prepare_integration.py`:

- the production consumer contract is frozen to `reasoning-distiller-invocation/2`;
- the production consumer id is frozen to `rd-distill`;
- eligibility validation requires both exact values rather than accepting a mutually consistent but wrong consumer pair; and
- a mismatch fails preflight as `PROFILE_ELIGIBILITY_MISMATCH`.

The candidate-local G9 remediation tests freeze those constants and exercise independent wrong `consumer_contract` and wrong `consumer_id` cases through the production prepare boundary.

The installed-package preflight path also independently verifies the release manifest contract, managed roots, normalized paths, file hashes and modes, required behavior-bearing P9/P10 files, actual installed tree closure, and recomputed package content identity. I found no source-repository fallback in the inspected `/2` package validation path that would permit an omitted or drifted installed behavior file to be silently sourced from ambient repository state.

The exact runtime gate remains CPython `3.12.0` / `cpython-312`. Unsupported micro-version behavior is fail-closed rather than treated as silently equivalent.

## Evidence provenance and separation

PR `#91` is an evidence-only branch over semantic candidate `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`. Its head `ff09627f8e83abc60f430b378bed342cbeaceb79` adds the G9 evidence construction and record; it is not treated as part of the semantic candidate and its own evidence document explicitly states that a fresh independent G9 review is still required.

The successful r5 workflow was inspected at job/log level rather than accepted from a summary marker alone.

The supported-runtime/full job checked out exact detached candidate `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`, asserted tree `81178c5efdc8f1419a068c61a92c0571b28f69fc`, asserted a clean worktree, and ran under exact CPython `3.12.0`.

The evidence scripts were retrieved from the evidence head rather than injected into the semantic candidate checkout. The resulting evidence therefore remains attributable to the evidence construction while the package and runtime behavior under test remain bound to the exact candidate.

## Package closure and exact package execution

The supported-runtime job built package `0.0.0-p10-g9-r5` directly from the exact candidate and observed:

- content identity `sha256:bd7d17faa026d3136e8d8be24a7d56dcec5ceace3b7c363310640de1219048fa`;
- transport SHA-256 `c7338985caf1a8147c7dd5457b3570e5f9cf6314087c7ac2468915a7d821902e`;
- `97` packaged files; and
- `EXACT_PACKAGE_REHYDRATION_PASS files=97` after archive extraction.

The same package content identity and transport digest were independently reproduced in the CPython `3.12.1` unsupported-runtime job before the runtime rejection witness was executed.

This closes the review concern that test execution might be source-tree-only while production depends on a materially different installed package surface.

## PI-01 through PI-60 challenge

The r5 execution ledger contract is `reasoning-distiller-p10-g9-pi-execution-ledger/2`. It binds the exact candidate, exact candidate tree, and governing plan and contains exactly 60 rows.

Observed witness coverage is:

- `21` direct installed-package or candidate-package executions;
- `37` exact pytest node-id mappings; and
- `2` actual unsupported-runtime executions;
- total pressure cases: `60`.

The direct executions include the previously weak or under-proven cases and report exact observed stage, reason code, and exit behavior, including:

- PI-04: `CONTEXT_PACK_IDENTITY_MISMATCH`, preflight;
- PI-05: `RENDERER_PROFILE_DIGEST_MISMATCH`, preflight;
- PI-06: `PROFILE_ELIGIBILITY_REQUIRED`, preflight;
- PI-08: `PROFILE_ELIGIBILITY_MISMATCH`, preflight;
- PI-09: both wrong consumer-contract and wrong consumer-id forms reject as `PROFILE_ELIGIBILITY_MISMATCH`, preflight;
- PI-10: context-pack `/1` supplied to `/2` rejects as `UNSUPPORTED_CONTEXT_PACK`, preflight;
- PI-11: renderer-profile `/1` supplied to `/2` rejects as `UNSUPPORTED_RENDERER_PROFILE`, preflight;
- PI-12: renderer-profile pack mismatch rejects as `RENDERER_PROFILE_PACK_MISMATCH`, preflight;
- PI-13: stale execution binding rejects as `TOOLCHAIN_IDENTITY_MISMATCH`, activation;
- PI-27 through PI-29: ambient/legacy request fields reject as `INVALID_REQUEST`, preflight;
- PI-34: pack, renderer-profile, and eligibility post-prepare drift variants each reject as `SEALED_INPUT_MISMATCH`, validation;
- PI-36: invalid RGP rejects as `RGP_VALIDATION_FAILED`, validation;
- PI-37: both raw-candidate and submission collision variants reject as `IMMUTABLE_OUTPUT_COLLISION`, persistence;
- PI-38: successful `/2` finalization leaves canonical, admission, role, and authority sentinel stores byte-for-byte unchanged;
- PI-39: different invocation IDs over identical sealed context preserve context/provenance identity while producing distinct submission identities;
- PI-41 and PI-42: package/provenance-bridge behavior drift rejects as `PACKAGE_IDENTITY_MISMATCH`, validation;
- PI-44: validator drift rejects as `RGP_VALIDATOR_MISMATCH`, validation; and
- PI-59: changed and then byte-for-byte-restored pack/profile/eligibility inputs may succeed because the exact prepared identities are restored.

The workflow emitted `P10_G9_DIRECT_PI_WITNESSES_PASS`, `P10_G9_PI_COMPOUND_DIRECT_WITNESS_PASS`, `P10_G9_PI01_PI60_EXACT_WITNESS_LEDGER_PASS`, and `P10_G9_PI_COMPOUND_WITNESS_SUPPLEMENT_PASS` only after those concrete witness checks completed.

### Runtime classification challenge

PI-14 retains the immutable-source wording `Fail activation; no silent equivalence`, while Stage 3 resolves the stable failure class to `preflight`. This is not an evidence-ledger inconsistency: the G0 pressure-freeze test explicitly asserts both the inherited wording and the Stage-3-resolved `preflight` ownership, and PI-52 is likewise `preflight`.

The separate unsupported-runtime job actually provisioned CPython `3.12.1`, asserted implementation `cpython`, version `(3, 12, 1)`, and cache tag `cpython-312`, rebuilt and rehydrated the exact candidate package, and executed `test_p10_g7_v2_rejects_actual_unsupported_cpython_runtime`. That test passed and the job emitted `P10_G9_UNSUPPORTED_RUNTIME_WITNESS_PASS`.

Therefore the supported-runtime PASS is not masking a micro-version compatibility gap.

### Prepared identity and provenance handoff challenge

The successful G6 path persists exact raw candidate bytes, ordinary immutable RGP submission, invocation result, prepared invocation, and provenance registry. The invocation result explicitly references the raw candidate, prepared invocation, and provenance registry by locator plus raw/identity digest.

The G1 frozen downstream-handoff contract requires the successful tuple:

1. ordinary immutable RGP submission;
2. `reasoning-distiller-invocation-result/2`;
3. `reasoning-distiller-prepared-invocation/1`; and
4. `reasoning-distiller-context-provenance-registry/1`.

It also requires the result to reference submission, raw candidate, prepared invocation, and provenance registry and explicitly forbids ambient file search when the handoff is incomplete. PI-48 is frozen as `INCOMPLETE_PROVENANCE_HANDOFF` at `reconciliation_handoff`.

This is sufficient for G9 because G10 reconciliation is intentionally not implemented or executed by the reviewer. The candidate proves the companion chain that G10 must consume; G10 remains responsible for independently enforcing its own Steward-side reconciliation contract.

## Fixed production evidence boundary and transport

The exact-node supplements include ambient-memory exclusion and unselected-prior-candidate exclusion, and the broader unaffected suite preserves the P8 authority/memory isolation gates.

Provider conformance tests establish that the reference runner preserves exact prepared frames and raw bytes, does not promote instruction-shaped content across planes, rejects unsupported/non-conforming provider mappings, and preserves the plan's non-hostile/reference-runner threat boundary. PI-60 correctly states that cryptographic detection of a malicious lying runner is outside P10 rather than claiming unsupported assurance.

No Project memory, prior chats, assistant recollection, unrelated repository files, prior candidates, canonical-state interpretations, or hidden reasoning are added to the production `/2` evidence set by the inspected candidate path.

## `/1` compatibility and unaffected regressions

Observed execution includes:

- complete P10 collection: `57` tests;
- supported-runtime P10 result: `56 passed, 1 skipped`, where the runtime-specific skip is separately exercised under CPython `3.12.1`;
- fixed production `/1` suite: `12 passed`;
- P10 G1 protocol-schema baseline: `9 passed`;
- unaffected P0-P9 regression selection: `214 passed, 2 deselected, 162 subtests passed`;
- package-builder and installer regression selection: `36 passed, 11 subtests passed`.

The inherited P1b PS-19 classifier mismatch is separately reproduced as `PLANE_CLASSIFICATION_CONFLICT` versus `UNKNOWN_SEMANTICS_FIELD`. It remains an inherited known mismatch and is not reclassified here as a P10-local defect or as a fixed condition.

## Review findings

### Blocking findings

None.

### Closed evidence blocker

`P10_G9_PI_WITNESS_LEDGER_INSUFFICIENT`: **CLOSED** for exact candidate `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e` and exact Engineer evidence `ff09627f8e83abc60f430b378bed342cbeaceb79`.

The r5 evidence no longer relies on broad suite-file attribution for the complete PI matrix. Every PI row is bound to a direct execution, an exact pytest node, or an actual unsupported-runtime execution, with compound supplements for multi-form cases including PI-34 and PI-37.

### PI-09 remediation finding

The production eligibility consumer is now bound to the exact intended invocation consumer, and mutually consistent wrong consumer-contract/id values fail preflight. The prior consumer-binding semantic defect is closed in the exact candidate.

### Non-blocking inherited red

PS-19 remains independently reproduced and unchanged. This review does not claim that inherited classifier mismatch is fixed.

## Independent review disposition

**P10_G9_INDEPENDENT_REVIEW_PASS**

Gate token: **P10_INDEPENDENT_REVIEW_PASS**

Exact candidate `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e`, tree `81178c5efdc8f1419a068c61a92c0571b28f69fc`, satisfies the independently reconstructed P10-G9 gate on the inspected implementation, package closure, exact supported runtime, actual unsupported runtime, complete PI-01 through PI-60 witness ledger, `/1` compatibility evidence, prepared identity, provenance handoff, transport boundaries, and unaffected regressions.

No P10-G9-local blocking finding was identified.

This review did not rerun or reconstruct the Engineer workflow and does not claim an independent execution run of its own. The disposition rests on independent contract reconstruction, candidate inspection, adversarial challenge of the witness mappings and weak-looking pressure cases, and direct inspection of the already candidate-bound exact-runtime and unsupported-runtime execution logs.

## Terminal boundary and bounded handoff

This independent-review activation ends with the P10-G9 disposition and durable review artifact. It does **not** perform P10-G10 Steward reconciliation, establish Steward authorization or accepted Steward activation evidence, admit knowledge, mutate canonical state, mutate authority, or begin any successor implementation.

If continuation is selected, the next consequential stage belongs to a **fresh Project Engineering Steward activation scoped only to P10-G10 closure**. That activation must independently re-resolve live coordination, establish whatever Steward authority and accepted activation evidence the live repository contracts require, and reconcile exact candidate `ae5d5c21de1f646b7b7c4450a1f9e8db6fcbcf0e` against this durable independent-review evidence and exact Engineer evidence `ff09627f8e83abc60f430b378bed342cbeaceb79`.

This handoff does not itself create Steward authority or accepted activation evidence.
