# Canonical PEMS/COVE Mode A B1 Independent Implementation Review

Disposition: **`CANONICAL_PEMS_COVE_MODE_A_B1_INDEPENDENT_REVIEW_ACCEPT`**

Gate token: **`MODE_A_G9_INDEPENDENT_REVIEW_PASS`**

## Bound review basis

- Repository: `loteque/reasoning-distiller`
- Bounded work unit: Mode B `B1`, Mode A substrate acceptance review only
- Active operational role: fresh independent Reasoning Graph Protocol Engineer
- Coordination control ref: `main`
- Coordination revision resolved at activation: `d46300a54a444cc866717986c1f5b493de3ab13f`
- Engineer directive and chat-transition amendment: read from that exact coordination revision
- Accepted Mode A Stage 3 plan: `c7445be11460a1c20c6b7c98bf39684a1bf41197`
- Accepted Mode A plan path: `docs/proposals/canonical-pems-cove-recovery/03-steward-final-plan.md`
- Mode B Stage 3 architecture plan: `45919508cab9d18a6eab82869514be767edf5c68`
- Mode B Stage 3 plan blob: `e8976adfa83cee4edad1439b85898f72af02d915`
- Exact reviewed candidate: `51ae28dca034cdd431b161a46d0f5cbc1a7e0116`
- Exact reviewed candidate tree: `c523ce99ea2932d070482d1fb14c556773f6405a`
- Candidate branch at activation: `impl/canonical-pems-cove-recovery-g0-20260826@51ae28dca034cdd431b161a46d0f5cbc1a7e0116`
- PR at activation: `#96`, open, draft, unmerged, head `51ae28dca034cdd431b161a46d0f5cbc1a7e0116`
- Candidate runtime/package source inventory digest for `runtime`, `admission`, and `backends` Git tree entries: `sha256:eee372e26515aff2c119a7f5dfa7a9129f7cbe1037c0de2abe6a07276e711958`

The Engineer directive permits generic protocol/framework implementation validation and review. It does not confer Steward authority, canonical semantic identity, admission authority, protected-root approval, recovery authority, merge authority, or authority mutation. No separate RIL activation is required by the governing Mode A G9/B1 review contract for this read-only Engineer review. This review therefore relies on no inferred or transferred activation.

## Independently reconstructed gate

Mode A Stage 3 requires a fresh G9 Engineer review of the exact G0-G8 implementation bundle. Mode B Stage 3 makes that review the first B1 prerequisite and requires it to bind the exact commit/tree, conformance, reader inventory, executable closure, and corrected incident-specific fail-closed result.

The review must establish that:

1. the candidate realizes the frozen Mode A V1 contracts without adding semantic judgment;
2. canonical readers and writers use one guarded shared/exclusive substrate;
3. R14 V2 distinguishes admitted and recovered provenance without converting recovery into admission;
4. the only V1 recipe is the closed missing-top-level-`semantic` insertion;
5. planning is read-only and binds complete consequential closure;
6. protected-root approval is exact and plan-digest-bound;
7. execution revalidates exact inputs and preserves lock, barrier, durability, rollback, retry, and resume guarantees;
8. Section 14 adversarial pressure cases and reader-inventory enforcement close executable behavior; and
9. the corrected incident rehearsal observes the immutable selected PEMS/COVE pair and terminates with zero candidates and `UNSUPPORTED_CANONICAL_DAMAGE`.

Passing B1 gives the exact candidate independent-review evidence only. It does not itself merge the candidate, select an immutable substrate-standing mechanism, or satisfy the distinct merge/standing prerequisite in Mode B Stage 3 Section 7.3.

## Candidate and G0-G8 inspection

The exact commit object independently reports tree `c523ce99ea2932d070482d1fb14c556773f6405a`. The implementation history from the coordination base was inspected commit-by-commit. The resulting candidate contains:

- G0: the normative V1 recovery contract, R13 exceptional-mutation boundary, R14 V2 provenance contract, and barrier state model;
- G1: `runtime/ril_canonical_store.py`, guarded R13/R14 pair access, shared/exclusive locking, barrier validation, and reader-scan enforcement;
- G2: `VERIFIED_ADMITTED` and `VERIFIED_RECOVERED` R14 V2 provenance with R13 valid-base integration;
- G3: the single closed `missing_top_level_semantic_pems2/1` recipe and executable equivalence proof;
- G4: a read-only planner binding the prestate, recipe, evidence inventory, candidate, proof, implementation closure, runtime, contracts, and expected provenance;
- G5: exact protected-root plan approval validation without altering R7/R8;
- G6: recovery execution with apply-time rebuilding/revalidation, preservation, exclusive locking, durable barrier/journal, ordered publication, verification, completion, rollback, retry, and bounded resume;
- G7: the required adversarial conformance matrix, including lock races, crash states, immutable artifacts, retry conflicts, path/symlink attacks, reader scanning, and no unauthorized mutation; and
- G8: corrected immutable incident reconstruction and fail-closed rehearsal.

No Mode B implementation or semantic default is present in the reviewed Mode A implementation. The recipe rejects an existing top-level `semantic` key before candidate construction and has no path for inserting lifecycle or dependency data.

## Reader inventory and canonical-store closure

The package production/runtime scan covers `runtime/` and `context_packaging/`, permits the fixed canonical path literals only in `runtime/ril_canonical_store.py`, and passes on the exact candidate. R13 and R14 acquire the canonical pair through that store. R13 holds an exclusive session over current-base inspection and mutation; R14 holds a shared session through pair snapshot acquisition. Recovery uses the same exclusive substrate.

Repository `evaluation/relationship_discovery_admission.py` contains direct project-analysis reads, but it is outside the package production/runtime boundary frozen by the accepted plan and the recovery contract. It is not packaged as a supported concurrent canonical consumer. No package production/runtime bypass was identified.

The lock uses the already-existing project root directory inode, so a read-only verifier does not create a lock file. An active, malformed, or indeterminate barrier blocks ordinary reads. Static and live adversarial tests cover the no-barrier/read race, reader/recovery lock contention, crash lock release with persistent barrier, and shared R13/recovery exclusivity.

## Executable closure and conformance

Review execution used a fresh isolated Python 3.12 virtual environment with the candidate workflow dependencies:

- `pytest`
- `jsonschema==4.25.1`
- `referencing`
- `PyYAML==6.0.2`

Observed results on exact candidate `51ae28dca034cdd431b161a46d0f5cbc1a7e0116`:

- corrected G8 isolated rehearsal: `1 passed`;
- candidate workflow regression command: `778 passed, 17 skipped, 2 deselected, 249 subtests passed`;
- Python compilation of `runtime/` and `tests/`: PASS;
- `git diff --check` against the implementation base: PASS.

The two deselections are explicit inherited context-packaging assertions in the candidate workflow:

1. PS-19 expects `UNKNOWN_SEMANTICS_FIELD` while the current integrated behavior is `PLANE_CLASSIFICATION_CONFLICT`;
2. a P5 blob-freeze assertion expects a pre-integration `pack_builder.py` identity.

The workflow separately witnesses their superseded/inherited status. Neither assertion is changed by the Mode A recovery implementation, and neither is used to conceal a recovery-local failure.

A first non-isolated local run additionally failed two runtime-isolation cases because dependencies installed into the invoking user's site directory became unavailable after those tests intentionally changed `HOME`. Re-execution in the isolated environment placed dependencies inside the interpreter environment and passed the exact candidate workflow. This was an execution-environment defect, not candidate behavior.

The executable recovery closure is represented in candidate code and plan artifacts by exact SHA-256 identities for schema, semantic validator, normalizer/serializer, COVE codec, recipe, planner, canonical store, recovery executor, recovery contract, and R14 V2 contract. Planner and executor recompute and compare those identities; apply-time planning must reproduce the approved plan and evidence inventory bytes exactly.

## Corrected incident-specific result

The rehearsal binds:

- PEMS Git blob `bb7c474e935243b45ff02a5778a94bbcdc654d72`;
- PEMS SHA-256 `22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061`;
- COVE Git blob `7ff52fb925a667c4cc1782da9b475dff831e45ef`;
- COVE SHA-256 `ce1f6dd7fe8889ce1bf126f7ec161b08fdc19a1705a2d5be350ed80b7d197e24`.

The selected immutable PEMS has top-level `semantic:"pems/2"`. Its relations lack schema-required `lifecycle` and `data`; the source workflow emitted generic `PEMS_SCHEMA_INVALID`, not a missing-semantic diagnosis. The corrected G8 evidence preserves the contradicted historical artifact rather than rewriting it.

The exact Mode A recipe rejects predicate 2 because `semantic` is already present. The independently exercised stable result is:

- R14: `FAIL/PEMS_SCHEMA_INVALID`;
- candidate count: `0`;
- recovery plan: not computed;
- root approval: not created;
- recovery/G10/P3: not performed;
- terminal outcome: `UNSUPPORTED_CANONICAL_DAMAGE`;
- G8 disposition: `G8_INCIDENT_REHEARSAL_BLOCKED_UNSUPPORTED_CANONICAL_DAMAGE`.

This is the required fail-closed behavior. The candidate does not infer lifecycle or `dependency_kind` values and provides no Mode B fallback.

## Findings

### Blocking findings

None.

### Prior Mode A blocker disposition

The prior G8 evidence-provenance blocker is closed by the corrected artifact and executable rehearsal at the exact candidate. The immutable selected pair, source failure class, current schema defect, recipe predicate failure, zero-candidate result, and mutation guards are mutually consistent.

No unresolved Mode A-local contract, conformance, reader-inventory, closure, or incident fail-closed blocker was identified.

### Remaining standing boundary

PR #96 remains open, draft, and unmerged at review time. Therefore this review satisfies Mode B Stage 3 Section 7.1 and finds Section 7.2 resolved for the exact candidate, but it does not itself satisfy Section 7.3. The exact reviewed commit must still be merged through its separately applicable governed workflow, or an equally explicit repository-governed immutable substrate-selection artifact must establish its standing.

## Independent disposition

**`CANONICAL_PEMS_COVE_MODE_A_B1_INDEPENDENT_REVIEW_ACCEPT`**

Gate token: **`MODE_A_G9_INDEPENDENT_REVIEW_PASS`**

Exact candidate `51ae28dca034cdd431b161a46d0f5cbc1a7e0116`, tree `c523ce99ea2932d070482d1fb14c556773f6405a`, satisfies its independently reconstructed G0-G9 implementation-review gate for Mode A V1. It is eligible to enter its separately governed merge/immutable-standing workflow.

This disposition does not approve or perform a merge. It does not establish final Mode B substrate standing while Section 7.3 remains unsatisfied. It does not implement or select B0, implement Mode B, author incident semantics, create a semantic disposition, construct a Mode B candidate or plan, approve protected-root recovery, mutate Canon/recovery/admission/authority state, perform recovery, or continue P3.

## B1 terminal boundary

B1 terminates with durable independent acceptance evidence for the exact candidate and an explicit remaining Section 7.3 standing boundary.

Any merge or immutable substrate-standing act belongs to a separately applicable governed workflow and must independently re-resolve live state and its own authorization. Completion of B1 does not select B0 or any other successor work unit.
