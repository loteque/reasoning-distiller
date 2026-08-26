# Stage 1 RPG Engineer Proposal: Governed Exceptional Canonical PEMS/COVE Recovery and Migration

Status: **Stage 1 independent proposal only** under `proposal-review-synthesis/1`

Coordination control: `main`

Coordination revision inspected: `d46300a54a444cc866717986c1f5b493de3ab13f`

Proposed contract family: `reasoning-distiller-canonical-pems-cove-recovery/1`

Proposed normative target if later accepted: `docs/operations/RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md`

This document is not an approval, Steward reconciliation, authority assignment, accepted activation artifact, recovery authorization, admission, canonical mutation, P3 restart, or implementation plan with present authority. Stage 2 and Stage 3 remain separate governed activations.

## 1. Problem and decision requested

The live repository contains an already-existing canonical PEMS/COVE pair for which the PEMS object is not valid under the current normative PEMS/2 contract. The exact PEMS Git blob inspected is:

`bb7c474e935243b45ff02a5778a94bbcdc654d72`

The paired COVE Git blob inspected is:

`7ff52fb925a667c4cc1782da9b475dff831e45ef`

The PEMS blob is parseable JSON but begins with `project_id` and does not contain the required top-level `semantic: "pems/2"` member. The current PEMS SHA-256 reported by the blocked evaluation is `22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061`.

Existing live contracts do not provide a lawful mutation path for this state:

- R11 exceptional recovery supports only `operator_registry`, `role_registry`, and `steward_authorization` administrative histories.
- R13 admission is the ordinary primitive allowed to mutate canonical PEMS/COVE, but it requires a valid normalized current PEMS/2 base and an exact admission transaction.
- the Project Identity and First-Admission Amendment requires canonical PEMS/COVE to pass PEMS/2 validity and deterministic COVE verification after admission.
- R7 defines only `semantic_reconciliation` and `admission` Steward scopes; R8 validates activation only for those scopes.

The decision requested is whether to add a distinct, generic, fail-closed exceptional recovery primitive for an **already-invalid canonical PEMS/COVE pair**, without weakening R13 or treating existing authority as a wildcard.

## 2. Recommendation

Add a new package-owned recovery primitive and contract family dedicated to canonical PEMS/COVE recovery. It MUST be separate from both R11 administrative-history recovery and R13 ordinary admission.

The primitive should use a two-key authority ceremony:

1. a newly explicit, independently assignable Steward scope named `canonical_recovery`, with accepted activation evidence for the exact recovery invocation; and
2. protected-root human approval bound to the exact recovery proposal, exact malformed pre-state fingerprint, exact deterministic migration recipe, exact proposed repaired pair, and exact standing-reconciliation evidence.

The recovery primitive MUST restore a valid canonical pair without admitting new knowledge, rewriting old admission artifacts, silently granting standing, or reinterpreting PEMS/COVE semantics. Existing `semantic_reconciliation` and `admission` authority MUST NOT satisfy `canonical_recovery` checks.

For the present incident, the first preferred reconstruction mode is a **lossless, package-owned migration recipe** applied to the exact malformed PEMS bytes, but only if implementation-time validation proves that the recipe changes only contract-envelope representation and preserves all semantic records, relations, identities, lifecycle states, and provenance. The proposal does not assume that this proof will succeed.

If lossless migration cannot be proven, a second bounded mode may reconstruct from immutable admission evidence by following a unique hash-linked admission lineage. Ambiguity, missing artifacts, forks, historical-contract incompatibility, or untraceable current content MUST fail closed rather than invite semantic inference.

COVE MUST never be repaired independently. The repaired COVE is regenerated deterministically from the repaired PEMS and must round-trip exactly.

## 3. Boundary and dependency direction

```text
package PEMS/COVE contracts + validators + migration recipes
                         |
                         v
read-only recovery planner
  - exact malformed pre-state
  - damage evidence
  - immutable admission evidence
  - deterministic reconstruction
  - standing analysis
                         |
                         v
recovery proposal + candidate pair + evidence fingerprint
                         |
             +-----------+-----------+
             |                       |
             v                       v
canonical_recovery Steward      protected root Human
activation + disposition        exact proposal approval
             |                       |
             +-----------+-----------+
                         |
                         v
deterministic recovery executor
  - revalidate all inputs
  - preserve malformed bytes
  - journaled pair publication
  - rollback on failure
                         |
                         v
R14-equivalent storage verification
                         |
                         v
immutable recovery completion record
                         |
                         v
ordinary R13 may become usable again
P3 remains separately gated
```

Dependency rules:

- PEMS/COVE normative semantics remain package-owned and upstream of project recovery state.
- the planner and executor consume validators and codecs; they do not redefine them.
- project recovery evidence may bind package contract identities but may not fork package schemas.
- root approval is administrative authorization for an exact exceptional transition, not semantic authorship.
- a recovery Steward may approve a recovery transition only within the new explicit scope.
- semantic ambiguity is routed to separately authorized `semantic_reconciliation`; it is not solved by the deterministic executor.
- `admission` authority remains unused during recovery and resumes only after recovery is complete.

## 4. Proposed contract additions

### 4.1 Steward authorization and activation

R7/R8 should be versioned or amended to recognize a third independent scope:

```text
semantic_reconciliation
admission
canonical_recovery
```

The new scope begins unassigned. No existing assignment migrates into it automatically. Assigning it requires the ordinary protected Steward-authorization ceremony. R8 activation for `canonical_recovery` must prove the same registered-role, role-availability, exact-assignment, and exact-invocation properties as the existing scopes.

This proposal does not authorize any role for that scope.

### 4.2 Recovery proposal

Define `reasoning-distiller-canonical-recovery-proposal/1` as canonical JSON containing at least:

- project identity digest;
- exact target canonical paths;
- exact malformed PEMS raw SHA-256 and optional VCS blob identity;
- exact malformed COVE raw SHA-256 and optional VCS blob identity;
- exact combined pre-state pair fingerprint;
- exact damage-classification evidence and validator identity;
- reconstruction mode;
- exact migration recipe identifier and content digest, or exact admission-lineage reconstruction inputs;
- exact proposed normalized PEMS SHA-256;
- exact proposed deterministic COVE SHA-256;
- exact admission-evidence inventory digest;
- exact standing-analysis digest;
- any required semantic-reconciliation artifact digest;
- expected project state / concurrency guard;
- recovery generation identifier.

Planning is read-only with respect to canonical state and authority state.

### 4.3 Recovery disposition

Define `reasoning-distiller-canonical-recovery-disposition/1` produced only by an authorized and activated `canonical_recovery` Steward. It binds the exact proposal digest and records `RECOVER` or `REJECT` plus bounded rationale and unresolved conditions.

A disposition grants no root approval and performs no mutation.

### 4.4 Protected-root approval

Reuse the common approval substrate where possible, but require a recovery-specific protected confirmation such as:

`AUTHORIZE_CANONICAL_PEMS_COVE_RECOVERY`

The approval must be issued by the currently established protected root operator, use explicit human-confirmation evidence, and bind:

- proposal digest;
- recovery disposition digest;
- malformed pair fingerprint;
- proposed repaired pair fingerprint;
- standing-analysis digest;
- migration recipe digest;
- recovery generation.

A delegated operator is insufficient for v1. Root approval does not create Steward authority and does not waive activation validation.

### 4.5 Recovery completion record

Define `reasoning-distiller-canonical-recovery-record/1` as immutable evidence of one attempted approved transition. A successful record binds pre-state, post-state, proposal, disposition, activation, root approval, standing analysis, migration recipe, executor identity, verification results, and recovery generation.

Exact retry of the same successful recovery may return `PASS/NO_CHANGE`. A different proposed recovery for the same pre-state and generation must fail with a conflict rather than overwrite history.

## 5. Deterministic reconstruction

The executor MUST NOT use model inference, network lookup, repository-name inference, undocumented defaults, or hand-edited semantic content.

Two reconstruction modes are proposed.

### 5.1 Mode A: lossless canonical migration

A package-owned migration recipe is a versioned deterministic transform with:

- an exact input contract predicate;
- an exact output contract;
- an allowlist of representation changes;
- rejection rules;
- canonical serializer identity;
- tests proving deterministic output and semantic preservation.

For an envelope-level defect such as a legacy discriminator key, a recipe may be allowed to change that discriminator only if all other required PEMS/2 structure and semantic invariants validate after the transform and no conflicting current field exists.

The migration proof MUST compare the full semantic graph before and after under an explicit projection that excludes only the approved representation-level changes. Record IDs, relation IDs, record kinds, lifecycle states, data, provenance, and relation endpoints must remain exact unless the particular approved recipe explicitly and normatively defines another lossless representation mapping.

If the current malformed object cannot satisfy the recipe's exact precondition, Mode A fails closed.

### 5.2 Mode B: admission-lineage reconstruction

When Mode A cannot be proven, reconstruction may use only immutable project identity, admission plans, admission receipts, reconciliation dispositions, activation evidence, and package contract implementations explicitly identified by the recovery proposal.

The reconstruction engine MUST derive a unique lineage by matching each receipt's `base_pems_sha256` to the preceding admitted-state hash and each `admitted_pems_sha256` to the exact plan result. It must begin from a valid project-seeded PEMS/2 base or another explicitly proven valid checkpoint.

Any missing plan/receipt/disposition, duplicate successor, fork, cycle, hash mismatch, contract-version ambiguity, non-reproducible historical transform, or content with no admissible provenance terminates the reconstruction with failure.

Mode B is not permission to replay historical intent under today's semantics when historical semantics differ. Historical contract identity must be explicit and reproducible.

## 6. Preservation of malformed state

Git history alone is useful provenance but is not sufficient as the sole recovery-preservation mechanism because ordinary path mutation makes the malformed files no longer current.

Before canonical publication, recovery must preserve byte-for-byte copies beneath a dedicated append-only generation directory, for example:

```text
project-knowledge/recovery/canonical-pems-cove/
  generations/
    00000001/
      prestate/
        pems2.raw
        cove1.raw
      damage.json
      admission-inventory.json
      standing-analysis.json
      proposal.json
      recovery-disposition.json
      root-approval.json
      result.json
```

The prestate manifest records raw SHA-256, byte length, canonical path, optional Git blob OID, and target repository revision. The copied bytes must hash exactly to the pre-state bytes immediately before mutation.

Recovery MUST NOT delete, rewrite, or normalize the preserved malformed bytes. Old admission plans, activation evidence, receipts, reconciliation dispositions, and candidate artifacts remain immutable in their existing locations.

## 7. Admission receipts, provenance, and standing reconciliation

Recovery must treat existing admission receipts as immutable historical claims, not documents to be repaired.

Create a separate deterministic `reasoning-distiller-canonical-recovery-standing-analysis/1` overlay. For every receipt that participates in the candidate lineage, record at least:

- receipt identity and digest;
- candidate and disposition identities;
- recorded base PEMS hash;
- recorded admitted PEMS/COVE hashes;
- whether the receipt is cryptographically and structurally valid;
- whether its before/after state can be reproduced;
- whether it is on the unique reconstructed lineage;
- whether its admitted semantic contribution is present, later superseded, absent, or unresolved in the repaired state;
- the exact evidence for that classification.

The overlay does not edit receipts and does not manufacture current standing.

Mechanically provable classifications may be produced by the planner. Any classification requiring a semantic judgment about whether historical admitted knowledge should remain current must be resolved by a separate artifact produced under valid `semantic_reconciliation` authority and activation. That artifact is an input to the recovery proposal and is digest-bound to root approval.

Recovery completion must fail if any lineage-critical receipt, provenance edge, or current semantic contribution remains `UNRESOLVED` or `CONFLICT`.

A missing receipt must never be reconstructed retroactively and presented as an ordinary R13 receipt. If historical evidence is incomplete, the gap remains explicit evidence and the recovery blocks unless a later governance decision defines a different lawful mechanism.

## 8. PEMS and COVE identity

PEMS is the semantic source for the repaired pair. COVE is deterministic derived representation.

Required invariants:

1. repaired PEMS conforms to current normative PEMS/2 and project identity rules;
2. repaired PEMS bytes are deterministic compact sorted-key JSON with no trailing LF, matching the package normalization contract;
3. repaired COVE is generated only from the repaired PEMS using the exact approved package codec;
4. repaired COVE identifies the expected `cove/1 | pems/2 | jcs/1` tuple;
5. decoding repaired COVE yields the exact repaired PEMS object;
6. reserializing that decoded object yields the exact repaired PEMS bytes;
7. recovery proposal and result bind both hashes as one pair fingerprint;
8. independent migration or hand repair of COVE is forbidden.

If the malformed pre-state COVE does not decode to the malformed pre-state PEMS exactly, that mismatch is separate damage evidence and must be incorporated into the proposal. It may not be silently resolved by choosing one side as authoritative without the approved recovery method.

## 9. Mutation, crash safety, and rollback

Recovery is exceptional, so partial publication must be treated as a first-class failure mode.

The executor should use a journaled transaction:

1. acquire an exclusive recovery lock;
2. re-read canonical PEMS/COVE and verify the exact approved pre-state fingerprint;
3. revalidate role availability, `canonical_recovery` assignment, activation evidence, root identity, approval binding, migration recipe, admission inventory, and standing analysis;
4. preserve and fsync exact malformed pre-state bytes and evidence;
5. materialize repaired PEMS/COVE in temporary files and run full verification before publication;
6. write and fsync an in-progress journal containing exact pre/post hashes and recovery generation;
7. replace the canonical pair using the narrowest available transactional sequence;
8. immediately perform full post-write verification;
9. on success, write the immutable completion record and clear the in-progress marker;
10. on any publication or post-write failure, restore both exact malformed pre-state byte sequences, verify their hashes, write a durable failed/rolled-back result, and keep P3 blocked.

A crash with an in-progress journal is a global blocker for admission, recovery retry, and P3. The next recovery invocation may only:

- prove that both canonical files already equal the exact approved post-state and finish the exact same approved transaction; or
- restore both exact preserved pre-state files and record rollback.

It may not improvise a third state.

If exact rollback cannot be proven, return a terminal failure such as `CANONICAL_RECOVERY_INDETERMINATE`; no ordinary admission or P3 continuation is allowed.

No force-push, history rewrite, or deletion of failure evidence is part of this contract.

## 10. Failure classes

The contract should define stable fail-closed classes, including at least:

- `RECOVERY_NOT_REQUIRED`: current pair passes ordinary storage verification;
- `UNSUPPORTED_CANONICAL_DAMAGE`: damage has no approved deterministic recipe or reconstructable lineage;
- `CANONICAL_PRESTATE_MISMATCH`: current bytes differ from the approved fingerprint;
- `RECOVERY_SCOPE_UNASSIGNED`;
- `RECOVERY_ROLE_UNAVAILABLE`;
- `RECOVERY_ACTIVATION_INVALID`;
- `ROOT_RECOVERY_APPROVAL_REQUIRED`;
- `ROOT_RECOVERY_APPROVAL_MISMATCH`;
- `MIGRATION_RECIPE_MISMATCH`;
- `ADMISSION_EVIDENCE_GAP`;
- `ADMISSION_LINEAGE_AMBIGUOUS`;
- `STANDING_RECONCILIATION_REQUIRED`;
- `STANDING_RECONCILIATION_CONFLICT`;
- `PEMS_RECOVERY_INVALID`;
- `COVE_RECOVERY_MISMATCH`;
- `RECOVERY_PUBLICATION_FAILED_ROLLED_BACK`;
- `CANONICAL_RECOVERY_INDETERMINATE`;
- `RECOVERY_CONFLICT`.

Every failure before publication must leave canonical bytes unchanged. Every failure after publication begins must either restore and verify the exact pre-state or remain globally blocked as indeterminate.

## 11. Verification gates

The following gates are proposed before any recovery operation can be considered successful.

| Gate | Requirement | Failure effect |
|---|---|---|
| CR0 | Stage 3 has accepted the recovery architecture and exact implementation gates | no implementation or recovery |
| CR1 | implementation and adversarial conformance tests pass for the exact executor/codec/validator bundle | no recovery |
| CR2 | exact target project identity and malformed PEMS/COVE pre-state fingerprints match | fail stale/conflict |
| CR3 | ordinary R14-equivalent verification proves the current pair is invalid and the damage class is eligible | fail or use ordinary path |
| CR4 | malformed PEMS/COVE bytes and all selected immutable admission evidence are preserved and digest-bound | no canonical write |
| CR5 | deterministic reconstruction produces exactly one candidate PEMS and standing analysis has no unresolved lineage-critical state | no canonical write |
| CR6 | candidate PEMS validates against normative PEMS/2 and approved migration-preservation invariants | no canonical write |
| CR7 | candidate COVE is regenerated from candidate PEMS and exact round-trip identity passes | no canonical write |
| CR8 | `canonical_recovery` authorization and exact invocation activation are accepted | no canonical write |
| CR9 | protected root approves the exact proposal, disposition, candidate pair, migration recipe, and standing analysis | no canonical write |
| CR10 | apply-time revalidation repeats CR2-CR9 immediately before publication | stale state fails |
| CR11 | journaled publication succeeds and post-state R14-equivalent verification passes | rollback or indeterminate block |
| CR12 | immutable recovery record matches exact post-state and exact retry is idempotent | recovery incomplete |
| CR13 | ordinary R13 read-only base validation can consume the repaired normalized PEMS/COVE state without mutation | ordinary admission remains blocked if not |

P3 has an additional boundary: **CR13 does not itself restart or authorize P3.** The P3 governing evaluation must separately observe a durable successful recovery record, re-resolve the live repository state, confirm no additional blocker exists, and explicitly select P3 continuation. Recovery completion is necessary evidence, not automatic P3 authority.

## 12. Concurrency and idempotence

Every proposal is bound to exact pre-state hashes and a recovery generation. Apply-time revalidation must compare-and-fail on drift.

Exact retry semantics:

- exact approval + exact successful post-state + exact completion record: `PASS/NO_CHANGE`;
- same pre-state/generation + different proposal or candidate pair: `FAIL/RECOVERY_CONFLICT`;
- approved pre-state no longer current: `FAIL/CANONICAL_PRESTATE_MISMATCH`;
- in-progress journal: only exact completion or exact rollback path is eligible.

Recovery never merges concurrent canonical mutations. R13 and P3 must treat an active or indeterminate recovery transaction as a blocker.

## 13. Why this is separate from R11 and R13

### Do not extend R11 by naming PEMS/COVE as another domain

R11 recovers append-only administrative event histories by approving an explicit continuation state. Canonical PEMS/COVE are not administrative registries, are coupled package-defined semantic representations, and already have admission/verification/provenance semantics that R11 does not reconcile. Reusing R11 unchanged would erase important domain boundaries.

The new contract may reuse R11's strongest ceremony ideas: damaged-state preservation, protected-root approval, explicit digest-bound continuation, deterministic recovery records, and fail-closed replay. It should not pretend the domains are equivalent.

### Do not relax R13

R13's valid-base and exact-base-hash requirements are a trust boundary. Allowing R13 to parse or normalize an invalid current base would turn ordinary admission into an implicit recovery mechanism and would make every future admission responsible for historical corruption.

Recovery should restore R13's preconditions, not weaken them.

## 14. Alternatives considered

### A. Hand-edit the malformed canonical PEMS and regenerate COVE

Rejected. This has no deterministic authority/provenance chain, can silently alter semantics, and bypasses standing reconciliation.

### B. Roll the repository back to the last known valid canonical commit

Not a general solution. It can discard later legitimate admissions, receipts, evidence, and unrelated repository changes. A prior valid state may be evidence or a reconstruction checkpoint, but rollback must itself be an explicitly approved recovery result and cannot be inferred from Git history alone.

### C. Treat current COVE as the independent truth and decode it over PEMS

Rejected as a default. R13 defines PEMS and COVE as deterministic counterparts. COVE is not independent semantic authority. A mismatch between the two is damage to be explained, not permission to pick one silently.

### D. Rebuild only by replaying admission receipts

Useful as a fallback, but too restrictive as the sole design. A parseable canonical state may admit a simpler provably lossless migration. Receipt replay may also encounter historical contract-version gaps. Both modes should remain deterministic and fail closed.

### E. Let existing `admission` or `semantic_reconciliation` authorization perform recovery

Rejected. Neither scope currently authorizes exceptional canonical recovery. Treating either as sufficient would silently broaden authority. A new explicit scope keeps recovery independently assignable and auditable.

## 15. Risks

1. **Migration recipes can become semantic back doors.** Mitigation: package-owned versioned recipes, explicit allowed-change projections, exact digests, adversarial tests, no free-form transforms.
2. **Historical receipts may not form a reproducible chain.** Mitigation: deterministic graph construction and hard failure on gaps/forks rather than best-effort replay.
3. **A dedicated recovery scope increases authority surface.** Mitigation: scope begins unassigned, root approval is additionally required, no cross-scope fallback, and exact invocation activation is mandatory.
4. **Filesystem crashes can split the pair.** Mitigation: preserved prestate, transaction journal, exact complete-or-rollback semantics, and a global indeterminate blocker.
5. **Recovery could accidentally manufacture current standing.** Mitigation: immutable receipts remain unchanged, standing is a separate evidence overlay, semantic ambiguity requires separately authorized reconciliation, unresolved state blocks completion.
6. **Incident-specific assumptions may leak into generic RGP/RIL behavior.** Mitigation: the primitive is generic over exact PEMS/COVE contract identities and migration recipes; `reasoning-distiller`-specific content appears only in project-owned evidence.
7. **P3 could resume too early.** Mitigation: recovery record is evidence only; P3 requires a separately selected continuation after live-state revalidation.

## 16. Proposed implementation sequence after Stage 3 acceptance

This sequence is prospective only. It is not authorized by this Stage 1 proposal.

1. **G0 - Contract freeze.** Define recovery proposal, disposition, standing-analysis, record, stable outcomes, and the new authorization scope.
2. **G1 - Migration recipe registry.** Implement package-owned deterministic migration descriptors and semantic-preservation pressure tests.
3. **G2 - Read-only planner.** Fingerprint malformed pair, inventory admission evidence, construct unique lineage, and emit candidate pair without mutation.
4. **G3 - Standing analysis.** Implement deterministic receipt/provenance mapping and unresolved-state classification.
5. **G4 - Authority integration.** Amend R7/R8 for the independent `canonical_recovery` scope and add protected-root exact approval binding.
6. **G5 - Recovery executor.** Implement apply-time revalidation, preserved prestate, locking, journal, deterministic publish, and exact rollback.
7. **G6 - Storage verification integration.** Require post-state PEMS validity, project identity, COVE round-trip, and recovery-record consistency.
8. **G7 - Adversarial conformance.** Test stale prestate, forged/missing approval, wrong scope, wrong activation, altered recipe, receipt gaps/forks, COVE mismatch, crash points, rollback failure, duplicate recovery, and concurrent R13/P3 attempts.
9. **G8 - Incident-specific read-only rehearsal.** Against an immutable copy of the exact blocked state, prove the selected migration recipe or lineage reconstruction produces one valid repaired pair and complete standing analysis. No Canon mutation.
10. **G9 - Governed recovery operation.** Only after independent implementation evidence, required authority assignment, accepted activation, exact root approval, and a separately selected recovery invocation. This is outside implementation itself.
11. **G10 - Post-recovery verification / P3 handoff.** Produce durable recovery verification evidence, then stop. A fresh P3 activation decides whether its own prerequisites are satisfied.

## 17. Acceptance criteria

A final accepted design should require tests and evidence proving all of the following:

1. valid canonical PEMS/COVE is never routed through exceptional recovery;
2. invalid canonical state cannot be passed to ordinary R13 as if it were valid;
3. R11 administrative domains remain unchanged;
4. `canonical_recovery` is an independent, initially unassigned authority scope;
5. registration, role name, chat label, `admission`, or `semantic_reconciliation` assignment cannot satisfy recovery authority;
6. activation evidence is bound to the exact authorized recovery role and invocation;
7. protected-root human approval is additionally required and bound to exact recovery bytes and evidence;
8. planning performs no canonical or authority mutation;
9. malformed PEMS/COVE bytes are preserved exactly before canonical replacement;
10. deterministic migration recipes cannot alter undeclared semantic content;
11. admission-lineage reconstruction fails on missing, forked, cyclic, stale, or non-reproducible evidence;
12. old admission receipts/plans/dispositions remain byte-identical and immutable;
13. standing analysis never manufactures an ordinary R13 receipt or silently promotes unresolved history;
14. semantic ambiguity requires separate valid semantic-reconciliation evidence;
15. repaired PEMS passes normative PEMS/2, project identity, graph, and normalization checks;
16. repaired COVE is derived only from repaired PEMS and exact round-trip identity passes;
17. apply-time drift is detected immediately before publication;
18. every injected publication failure either restores the exact malformed pair or produces an explicit indeterminate global block;
19. exact successful retry is idempotent and conflicting retry fails closed;
20. recovery completion record binds exact pre/post pair, authority, approval, migration, standing, and verification identities;
21. ordinary R13 can again validate the repaired pair as a canonical base without performing an admission;
22. recovery success does not itself perform admission, create candidate standing, mutate authority, or restart P3;
23. P3 cannot resume until its own fresh activation observes the durable recovery completion and explicitly revalidates its prerequisites.

## 18. Unresolved questions for Stage 2 challenge

Stage 2 should independently challenge at least these points rather than treating them as settled:

1. whether adding `canonical_recovery` to R7/R8 is the smallest safe authority change, or whether recovery authority should live in a separate contract to avoid widening ordinary Steward authorization;
2. whether v1 should implement both reconstruction modes or intentionally ship lossless migration first and defer admission-lineage reconstruction;
3. what exact package contract should define the migration-recipe registry and semantic-preservation projection;
4. how historical serializer/validator identity is proven for Mode B without introducing source-repository fallback;
5. whether every receipt must be classified or only the unique lineage reaching the malformed current state;
6. whether a recovery-specific semantic-reconciliation artifact can safely reuse the existing `semantic_reconciliation` scope without changing R12's candidate-focused contract;
7. what crash-consistency mechanism is portable enough to make the pair-and-record transaction trustworthy across supported runtimes;
8. whether the present incident is provably envelope-only or contains additional PEMS/COVE or receipt inconsistencies that require a different recipe;
9. whether a successful recovery record should become a direct input to R14 or remain a sibling evidence artifact checked by a new recovery verifier;
10. the exact durable P3 readiness artifact and owner. This proposal requires a separate post-recovery P3 decision but does not invent that authority.

## 19. Stage 1 terminal boundary

This proposal recommends a separate generic exceptional canonical PEMS/COVE recovery primitive with deterministic reconstruction, byte-preserved damaged evidence, immutable admission evidence, explicit standing reconciliation, paired PEMS/COVE identity, dedicated recovery authority plus protected-root approval, journaled rollback, and explicit verification gates.

No recovery has been performed. No canonical state, admission artifact, authority assignment, activation evidence, or P3 state has been mutated by this proposal. Under `proposal-review-synthesis/1`, this Stage 1 artifact must remain immutable after submission. The next consequential step is a fresh, independent Stage 2 Engineer review and synthesis that receives the original problem and constraints plus this complete proposal.