# Stage 2 Independent Engineer Review and Synthesis: Mode B Relation-Schema Recovery

Status: **Stage 2 independent review complete; architecture compatible only with required revisions and unresolved incident semantics**

Disposition: **`CANONICAL_PEMS_COVE_RECOVERY_MODE_B_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`**

Method: `proposal-review-synthesis/1`

Repository: `loteque/reasoning-distiller`

Coordination control ref: `main`

Coordination revision independently resolved for this review: `d46300a54a444cc866717986c1f5b493de3ab13f`

Mode A implementation candidate independently resolved: `51ae28dca034cdd431b161a46d0f5cbc1a7e0116`

Mode A candidate tree: `c523ce99ea2932d070482d1fb14c556773f6405a`

PR #96 state independently resolved: open, draft, unmerged; head `51ae28dca034cdd431b161a46d0f5cbc1a7e0116`

Accepted Mode A Stage 3 plan: `c7445be11460a1c20c6b7c98bf39684a1bf41197`, `docs/proposals/canonical-pems-cove-recovery/03-steward-final-plan.md`

Stage 1 proposal commit: `8dc0df3d3f61e5f829d23c491a5beb694de0d52c`

Stage 1 proposal tree: `896a9b3b48dbe3eb141bb5ba90af93d188a3cc2a`

Stage 1 proposal blob: `0dedf4a1c067b94620980c1c752c9514ed86a031`

Stage 1 proposal path: `docs/proposals/canonical-pems-cove-recovery-mode-b/01-rpg-engineer-proposal.md`

Review role: **Reasoning Graph Protocol Engineer acting as the independent Stage 2 Engineer**

Authority posture: this is a non-authoritative technical review and synthesis. The Engineer directive permits framework design and review but grants no Steward, semantic-reconciliation, protected-root, recovery-execution, admission, or RIL authority. `proposal-review-synthesis/1` requires a separate Engineer review artifact but does not require R7/R8 activation for this non-authoritative act. No accepted activation is claimed. This artifact does not authorize implementation or recovery.

## 1. Executive assessment

Stage 1 correctly rejects a representation-only repair and correctly separates semantic choice from exceptional mutation authority. Its proposed direction is implementable, but not as written.

The design has four blocking gaps:

1. no immutable evidence currently establishes the missing lifecycle value for any of the 668 relations or the required `dependency_kind` for the seven `depends_on` relations;
2. R12 cannot be reused for the proposed disposition because its normative domain is exactly one immutable Distiller submission beneath `project-knowledge/submissions/` and its disposition vocabulary cannot express field-level canonical repair;
3. versioning only the recovery plan is insufficient because the accepted completion, result, approval validation, barrier validation, and R14 V2 provenance logic are Mode-A/V1-bound as a protocol family;
4. PR #96 remains an unmerged draft, so Mode B cannot normatively reuse its substrate until an immutable Mode A substrate is separately selected and accepted.

The architecture should proceed only after Stage 3 adopts the required contract and sequencing revisions below. Stage 3 may reconcile the architecture, but it must not simultaneously manufacture the incident-specific field values. Those values require a later, separately bounded semantic-disposition act over immutable damage analysis and evidence.

## 2. Independently reconstructed incident facts

The selected PEMS Git blob is `bb7c474e935243b45ff02a5778a94bbcdc654d72`; its independently computed SHA-256 is `22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061`.

Strict inspection establishes:

| Observation | Result |
|---|---|
| Top-level semantic | `pems/2` |
| Records | 802 |
| Relations | 668 |
| `supports` | 661 |
| `depends_on` | 7 |
| Relation key set | exactly `from`, `id`, `kind`, `to` for every relation |
| Missing required fields | `lifecycle` and `data` for every relation |
| Mode A predicate 2 | fails because `semantic` is present |
| Mode A result | `UNSUPPORTED_CANONICAL_DAMAGE` |
| Candidate count | 0 |
| Recovery plan | not computed |
| G10 | unavailable |

The current PEMS/2 schema requires `id`, `kind`, `from`, `to`, `lifecycle`, and `data` on every relation. It additionally requires `data.dependency_kind` when `kind` is `depends_on`. Therefore `data:{}` is schema-valid for the 661 `supports` relations but is not schema-valid for any of the seven `depends_on` relations.

The corrected G8 artifact at the Mode A candidate agrees with these immutable observations and records `CORRECTED_FAIL_CLOSED` / `UNSUPPORTED_CANONICAL_DAMAGE`. The historical blocker that reported missing top-level semantic is contradicted by the immutable PEMS and is not used as incident truth.

Historical A0 evidence proves that the 668 relation identities, endpoints, and kinds were selected and reconciled, and the materializer at commit `95a65e2` deliberately emitted and validated the four-key relation shape. That establishes the source defect mechanism. It does not establish what the omitted lifecycle or dependency-kind values must be.

## 3. Findings by severity

### 3.1 Blockers

| ID | Blocker | Required resolution |
|---|---|---|
| B-1 | Missing semantic values are unproven. Neither the canonical pair nor its COVE witness supplies lifecycle or relation data. | Produce immutable evidence and a separately authorized semantic disposition specifying lifecycle for every affected relation and `dependency_kind` for every `depends_on` relation. If evidence cannot support a value, reject or defer the incident repair. |
| B-2 | Existing R12 is candidate-submission-specific. Reusing it would violate its preconditions, storage paths, disposition shape, and candidate identity semantics. | Define a new domain primitive for canonical-repair semantic dispositions. It may validate R8 activation for the existing `semantic_reconciliation` scope only after the governing contracts explicitly declare that applicability. Do not call the new artifact an R12 disposition. |
| B-3 | Mode B changes more than the plan contract. Mode A V1 freezes plan, approval, barrier, completion, result, outcomes, and R14 bindings as one coherent protocol. | Version the complete affected protocol family or define explicit cross-version compatibility for every consumer. A plan-v2-only change is insufficient. |
| B-4 | The reusable Mode A substrate has no accepted durable implementation standing. PR #96 is open, draft, and unmerged. | Before Mode B implementation, independently accept and identify an immutable Mode A substrate commit/tree, normally by completing the Mode A review/merge workflow or by an equally explicit governed selection. Stage 3 must not treat the current PR head as accepted merely because it is cited. |

### 3.2 Required amendments

| ID | Stage 1 area | Required amendment |
|---|---|---|
| R-1 | Semantic disposition | Split architectural Stage 3 reconciliation from the later incident-specific semantic disposition. Stage 3 may accept a contract design; it must not populate 668 repairs without the required evidence and a distinct bounded activation. |
| R-2 | Authority | Amend the applicable R7/R8/domain contracts to state explicitly that `semantic_reconciliation` may validate this new disposition operation. Preserve R7's closed scope vocabulary and do not broaden R12. If the Steward declines that interpretation, introduce a new scope only through a separate authority-design cycle; do not infer it here. |
| R-3 | Disposition payload | Bind the exact damage-analysis digest, prestate pair identities, schema identity, ordered relation identity set, per-relation inserted values, evidence references/digests, rationale, role, invocation, and accepted activation digest. Digest-only expansion is acceptable only if the canonical table is immutable, path-bound, independently retrievable, and validated as part of the disposition. |
| R-4 | Recipe boundary | Make the first recipe incident/project-owned. The package may provide a generic deterministic disposition-application kernel, but it must not publish project-specific missing-field defaults as generic PEMS semantics without independent pressure cases and a separate generic-semantic review. |
| R-5 | Versioning | Prefer a coherent Mode B protocol generation, provisionally `canonical-recovery-plan/2` plus explicitly compatible or versioned approval, barrier/journal, proof, completion, result, and R14 validators. Freeze an exact compatibility matrix at B0. |
| R-6 | Damage closure | The analyzer must enumerate the complete JSON Schema error set, duplicate IDs, endpoint integrity, project identity, COVE equality, normalization effects, and all current semantic/integrity validator results that can run without inventing missing values. Post-repair validation must fail closed on any additional defect. |
| R-7 | Provenance | Recovery-native provenance is sufficient for the recovery transaction if R14 and each downstream consumer explicitly accept the new completion version. It does not reconstruct or validate historical admission lineage. Preserve historical admission artifacts unchanged and record the known source defect. |
| R-8 | Gate ordering | Implement and independently review the damage analyzer and disposition contract before any incident disposition is authored. The deterministic candidate/planner gates follow only after an accepted disposition exists. |
| R-9 | Failure vocabulary | Distinguish `SEMANTIC_EVIDENCE_INSUFFICIENT`, `SEMANTIC_DISPOSITION_REJECTED`, and contract/activation failures from structural mismatch and candidate-validation failures. A rejected/deferred semantic decision is not `ADDITIONAL_DAMAGE`. |
| R-10 | Candidate count | The planner must produce exactly zero or one candidate. Zero is the normal result for missing, rejected, stale, incomplete, or unsupported semantic disposition; more than one is a deterministic failure. |

### 3.3 Recommendations

1. Treat lifecycle as per-relation data in the disposition even if one uniform value is eventually justified. A uniform rule may compress representation, but its expansion must be digest-bound and reviewable.
2. For each `depends_on`, require one of the schema-accepted `dependency_kind` values supported by exact historical/domain evidence; never derive it merely from the relation kind.
3. Require the semantic-disposition author and protected-root approver to perform distinct recorded acts. Distinct human principals are desirable for this incident but are not established as a current contract requirement; Stage 3 should state whether it adopts that stronger policy.
4. Preserve a source-defect record identifying the A0 materializer's four-key projection and its self-check. This explains provenance without rewriting the historical receipt or claiming the receipt was valid under current verification.
5. Keep COVE a consistency witness pre-repair and a PEMS-derived encoding post-repair. It supplies no missing semantic values.
6. Require an independent implementation review after the exact Mode B candidate, protocol closure, and incident rehearsal identities exist.

### 3.4 Optional improvements

1. Add a compact human-readable report generated from the canonical disposition table for reviewing all 668 rows; the canonical table remains authoritative.
2. Add a machine-readable compatibility matrix mapping each Mode A/Mode B artifact version to every validator and executor that consumes it.
3. Generalize the package kernel only after at least one additional pressure case demonstrates reuse beyond this incident.

## 4. Required authority design

The existing `semantic_reconciliation` scope is semantically the closest existing authority, but scope name similarity is not sufficient. R7 defines the assignment; R8 validates an invocation for a requested scope; R12 defines one specific candidate-reconciliation operation. None currently defines a canonical-repair semantic-disposition operation.

The least-expansive design is:

1. retain the closed R7 scope vocabulary;
2. add a new normative domain contract, provisionally `reasoning-distiller-canonical-recovery-semantic-disposition/1`;
3. amend R8 or an explicitly governing integration contract to permit that domain primitive to request `semantic_reconciliation` activation;
4. validate the live role registry, authorization assignment, authoritative histories, and exact activation at disposition apply time;
5. persist the activation evidence and immutable disposition in a recovery-specific namespace;
6. state explicitly that this act neither invokes R12 nor authorizes mutation.

This is a required contract clarification, not an inferred expansion of R12. If Stage 3 finds that `semantic_reconciliation` was intended only for R12 submissions, Mode B is blocked pending a separate authority-scope design and human-approved R7 evolution.

## 5. Plan-family and compatibility synthesis

Stage 1 is correct not to overload `reasoning-distiller-canonical-recovery-plan/1`, whose contract freezes `mode:A` and one recipe. A `/2` plan is preferable to an unrelated plan name because the transaction purpose and authority binding remain canonical recovery. However, `/2` must be introduced as part of a coherent protocol generation.

At B0, freeze a matrix covering at least:

| Artifact/consumer | Mode A | Mode B requirement |
|---|---|---|
| Plan | `/1`, `mode:A` | `/2`, `mode:B`, disposition and repair-proof bindings |
| Root approval | `/1` only if its validator explicitly accepts plan `/2`; otherwise version | Must bind exactly one plan-v2 digest and reject cross-mode replay |
| Barrier/journal | `/1` only if semantically unchanged and validators are version-aware | Must bind plan version and exact semantic-disposition/proof chain |
| Completion | Version or explicitly extend | Must bind disposition, damage analysis, repair proof, and plan-v2 closure |
| Result | Version or freeze a versioned outcome extension | Must distinguish semantic-evidence and Mode B failures |
| R14 | Extend/version recovered-provenance validation | Must verify the exact Mode B completion chain and current pair |
| Executor | Versioned closure | Must reject unsupported artifact-version combinations before publication |

Mode A behavior and its closed failure result must remain byte/behavior compatible. No Mode B artifact may be accepted by a Mode A-only executor.

## 6. Provenance and historical evidence

Full admission-lineage reconstruction is not required to authorize an exceptional recovery transaction. The accepted Mode A architecture already defines `VERIFIED_RECOVERED` as distinct from `VERIFIED_ADMITTED`; Mode B should preserve that separation.

Historical evidence is nevertheless relevant to the semantic choice:

- the A0 candidate and Steward dispositions support the exact relation endpoints and kinds;
- the admission materializer demonstrates that omission of lifecycle/data was systematic and intentional in implementation shape;
- current compatibility fixtures show possible `depends_on` classifications such as `conditional_validity` and `legacy_untyped`;
- none of those facts alone proves which classification applies to each incident relation or what lifecycle each relation has now.

Therefore the historical lineage should be investigated as semantic evidence, not reconstructed as a replacement admission receipt. If it cannot establish the missing values, the correct outcome is deferred or rejected repair, not a plausible default.

## 7. Revised implementation sequence

This sequence is prospective and requires Stage 3 acceptance before implementation:

1. **B0 — Steward architecture reconciliation.** Select the authority design, protocol-version family, substrate prerequisite, project/package boundary, invariants, and gates. Do not decide incident field values without evidence.
2. **B1 — Mode A substrate prerequisite.** Complete the independent acceptance/merge or other explicit governed selection of the exact reusable Mode A implementation substrate.
3. **B2 — Read-only damage analyzer and evidence inventory.** Enumerate the exact defect set and immutable historical evidence without constructing a candidate.
4. **B3 — Disposition-domain contract and validator.** Implement recovery-specific disposition storage, R8 validation, rejection/defer semantics, and adversarial tests; no incident disposition yet.
5. **B4 — Independent B2/B3 review.** Confirm damage closure, authority boundaries, and evidence sufficiency interface.
6. **B5 — Separately activated semantic disposition.** An authorized `semantic_reconciliation` Steward accepts, rejects, or defers exact per-relation values against the immutable B2 evidence. This is a distinct bounded act from Stage 3 architecture reconciliation.
7. **B6 — Closed project-owned recipe and repair proof.** Deterministically apply only an accepted disposition; prove deletion equality and unchanged content.
8. **B7 — Versioned planner and protocol integration.** Produce at most one candidate and one plan, bind the full artifact and executable closure, and preserve Mode A compatibility.
9. **B8 — Adversarial conformance.** Exercise stale/wrong activation and disposition, incomplete tables, invalid dependency kinds, extra damage, COVE mismatch, version confusion, drift, rollback, retry, and cross-mode replay.
10. **B9 — Incident-specific read-only rehearsal.** Against immutable copies only, compute zero or one candidate/plan and publish immutable evidence; create no approval and mutate no Canon.
11. **B10 — Fresh independent implementation review.** Review the exact implementation candidate, closure, conformance, and rehearsal.
12. **B11 — Governed recovery operation.** Separately selected; requires fresh protected-root approval over the exact plan. Outside implementation scope.
13. **B12 — Post-recovery verification and terminal handoff.** Require exact recovered provenance and stop before P3.

## 8. Acceptance criteria for a Stage 3 final plan

The final plan must make all of the following explicit:

1. Mode A remains closed, unchanged, and rejects this incident;
2. architecture reconciliation and incident semantic disposition are separate acts;
3. R12 is not reused or broadened;
4. the exact contract that permits R8 `semantic_reconciliation` validation for the new disposition is identified;
5. no missing lifecycle or dependency-kind value is inferred from schema validity, naming, conventions, or implementation convenience;
6. all 668 relations are covered exactly once by an accepted disposition or no candidate is produced;
7. every `depends_on` has an explicitly evidenced, schema-valid `dependency_kind`;
8. the complete affected protocol family is versioned or has explicit compatibility rules;
9. Mode A-only components reject Mode B artifacts;
10. the exact Mode A substrate prerequisite and acceptance condition are specified;
11. the initial recipe is project-owned and generic package semantics are not expanded without pressure cases;
12. damage analysis proves the complete pre-repair defect set and post-repair validation fails on latent defects;
13. candidate and plan multiplicity is exactly zero or one;
14. semantic disposition cannot authorize mutation;
15. protected-root approval cannot author or alter semantic values;
16. recovery-native provenance remains distinct from admission provenance;
17. historical artifacts remain byte-immutable and the known source defect is recorded without rewriting standing;
18. publication preserves the accepted lock, barrier, durability, rollback, retry, and exact-base guarantees;
19. implementation, review, and rehearsal create no real-recovery authority;
20. recovery neither selects nor resumes P3.

## 9. Unresolved questions for Stage 3

1. Does the project possess immutable evidence sufficient to classify lifecycle for all 668 relations and `dependency_kind` for each of the seven `depends_on` relations? Current review evidence does not establish those values.
2. Will Stage 3 explicitly extend use of the existing `semantic_reconciliation` scope to the new domain primitive, or require a separate authority-design cycle?
3. Which exact commit/tree will become the accepted reusable Mode A substrate, and by what governed acceptance event?
4. Which members of the Mode B protocol family require new contract versions versus explicit backward-compatible amendments?
5. Will distinct human principals be required for semantic disposition and protected-root approval, or only distinct recorded acts?
6. Which downstream consumers are permitted to accept the Mode B recovered provenance class?

## 10. Stage 2 terminal boundary

Stage 2 is complete with disposition `CANONICAL_PEMS_COVE_RECOVERY_MODE_B_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`.

No Mode B implementation, incident semantic disposition, candidate pair, recovery plan, protected-root approval, Canon mutation, recovery-standing mutation, admission, authority mutation, G10/B11 operation, or P3 continuation was performed.

This is a terminal boundary for the Stage 2 bounded work unit. The next consequential work belongs to a fresh authorized Project Engineering Steward performing Stage 3 reconciliation under `proposal-review-synthesis/1`. Strong context isolation is appropriate. This artifact and its handoff do not establish Steward identity, authorization, activation, approval, or repository truth.
