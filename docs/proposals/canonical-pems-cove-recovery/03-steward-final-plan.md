# Canonical PEMS/COVE Recovery - Stage 3 Steward Final Plan

Status: **Stage 3 reconciliation complete; V1 accepted as Mode A only**

Disposition: **`CANONICAL_PEMS_COVE_RECOVERY_STAGE3_RECONCILED_ACCEPTED_MODE_A_V1`**

Method: `proposal-review-synthesis/1`

Repository: `loteque/reasoning-distiller`

Coordination control ref: `main`

Coordination revision independently resolved for this reconciliation and re-resolved immediately before this Stage 3 write: `d46300a54a444cc866717986c1f5b493de3ab13f`

Stage 1 proposal commit: `aa8a5e751db0d5fb1472f2879691d4c9d38dd93f`

Stage 1 proposal blob: `f5bba0bb6e5d2ced5f233aa86ff8a51602cd043c`

Stage 1 proposal path: `docs/proposals/canonical-pems-cove-recovery/01-rpg-engineer-proposal.md`

Stage 2 review commit: `83ba1ca779c0a4806730b84e5aa15764e1a469b2`

Stage 2 review blob: `ff0faa31d2a83ef0c1b6309190c19f2216ac7465`

Stage 2 disposition: `CANONICAL_PEMS_COVE_RECOVERY_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`

Blocked canonical PEMS Git blob: `bb7c474e935243b45ff02a5778a94bbcdc654d72`

Paired canonical COVE Git blob: `7ff52fb925a667c4cc1782da9b475dff831e45ef`

Blocked canonical PEMS SHA-256: `22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061`

Operational role for this Stage 3 act: `steward:default`, scope `semantic_reconciliation`.

Invocation activation result: `PASS/ACTIVATION_ACCEPTED` for invocation `canonical-pems-cove-recovery-stage3-20260826T1211-0700`, activation digest `sha256:ff6a77c5d3457bb0a341f81d695774bfaea647648e604842eaec4c3a9b6c0ee3`.

Authority boundary: this reconciliation establishes the accepted semantic design and implementation gates only. It grants no canonical-recovery execution authority, no protected-root approval, no admission authority, no authority mutation, no Canon mutation, and no P3 continuation.

## 1. Steward disposition

The Stage 1 architectural core is accepted only with the Stage 2 revisions incorporated below.

V1 SHALL provide one narrow exceptional recovery path for an already-invalid canonical PEMS/COVE pair when, and only when, a closed deterministic representation-only migration is mechanically proven lossless. For the current incident, the only V1 recipe class is the exact missing-top-level-`semantic` repair described in this plan.

V1 SHALL NOT implement admission-lineage reconstruction, SHALL NOT add a `canonical_recovery` R7/R8 Steward scope, SHALL NOT use COVE as semantic authority, SHALL NOT fabricate or rewrite ordinary admission receipts, and SHALL NOT permit any semantic judgment inside the deterministic recovery executor.

If the exact incident cannot satisfy the closed Mode A predicate, the governed outcome is `UNSUPPORTED_CANONICAL_DAMAGE`. There is no fallback to Mode B in V1.

## 2. Recommendations and final reconciliation

### 2.1 Stage 1 RPG Engineer recommendation

Stage 1 recommended a separate canonical PEMS/COVE recovery primitive, exact malformed-state preservation, deterministic Mode A migration with Mode B lineage reconstruction as fallback, a new `canonical_recovery` R7/R8 scope plus protected-root approval, immutable standing analysis, journaled pair publication, recovery-aware verification, and a separate P3 continuation boundary.

### 2.2 Stage 2 Engineer recommendation

Stage 2 found the design compatible only after required revisions. It required an explicit recovered-state R14 provenance branch, an explicit R13 exceptional-mutation exception, no new R7/R8 recovery scope in V1, full historical executor closure for any future Mode B, a package-wide crash barrier, an executable Mode A equivalence predicate, Mode A only in V1, COVE as witness only, precise receipt classifications, reordered recovery gates, one digest-bound root approval object, and expanded adversarial conformance.

### 2.3 Steward decision

The Stage 2 revisions are accepted. The Stage 1 proposal is superseded where it conflicts with this final plan. The accepted design is intentionally smaller than Stage 1: a root-bound, representation-only, PEMS-first recovery path with recovery-native provenance and no ordinary Steward authorization expansion.

## 3. Stage 2 finding disposition

| Finding | Steward disposition | V1 consequence |
|---|---|---|
| F1 recovered standing under R14 | ACCEPT | R14 gains an explicit recovered provenance branch; no ordinary receipt is fabricated. |
| F2 R13 mutation exclusivity | ACCEPT | R13 remains the only ordinary admission mutator; the new recovery contract is its sole named exceptional canonical-pair mutation path. |
| F3 new R7/R8 recovery scope | ACCEPT STAGE 2 / REJECT STAGE 1 EXPANSION | R7/R8 stay unchanged in V1. Exact protected-root approval is the operation-specific execution authority. |
| F4 historical executor reproducibility | ACCEPT, DEFER EXECUTION TO FUTURE MODE B | V1 does not reconstruct standing from historical admission execution. Any future Mode B must bind exact historical executor closure and normative conformance. |
| F5 pair crash consistency | ACCEPT, STRATEGY B | Use a durable transaction barrier over fixed canonical paths plus shared/exclusive canonical-store locking. |
| F6 executable Mode A equivalence | ACCEPT | Closed predicate defined in Section 7. |
| F7 Mode A only | ACCEPT | Mode B is out of V1 and requires a new proposal -> independent review -> Steward reconciliation cycle. |
| F8 COVE witness only | ACCEPT | Prestate COVE must decode exactly to prestate PEMS or Mode A is ineligible; poststate COVE is regenerated from repaired PEMS only. |
| F9 receipt semantics | ACCEPT | Existing receipts remain immutable historical claims. V1 preserves and inventories them but does not upgrade non-conformant historical claims into standing. |
| F10 gate ordering | ACCEPT | CR0-CR13 are frozen in Section 13 without ordinary-receipt circularity. |
| F11 one approval digest | ACCEPT | Root approval binds one canonical recovery-plan digest containing all consequential inputs. |
| F12 adversarial tests | ACCEPT | Required tests are frozen in Section 14, including live race/TOCTOU cases. |

## 4. Resolution of the five Stage 2 disagreements

### D1. Authority placement

Resolved in favor of the narrower Stage 2 model.

V1 SHALL NOT add `canonical_recovery` to R7 or R8. Recovery execution authority is a domain-specific protected-root approval over exactly one immutable recovery plan. The deterministic executor has no independent authority and cannot infer approval from role, chat, branch, repository ownership, or prior success.

This is a single operation-specific root authorization ceremony, not a claimed two-person or two-key control. A future policy may add distinct-principal requirements through a separately reviewed authority design.

### D2. Mode B timing

Resolved in favor of Stage 2. V1 is Mode A only.

Admission-lineage reconstruction is deferred. Any future Mode B requires its own proposal, independent review/synthesis, Steward reconciliation, exact historical executor-closure model, and new acceptance gates. V1 MUST terminate rather than silently reconstruct when Mode A is not mechanically provable.

### D3. Recovered R14 standing

Resolved by versioning the storage-verification result semantics.

The recovery implementation SHALL introduce `reasoning-distiller-storage-verification-result/2` with two positive provenance classes:

- `PASS/VERIFIED_ADMITTED`, backed by an exact ordinary admission receipt;
- `PASS/VERIFIED_RECOVERED`, backed by an exact immutable canonical-recovery completion record.

Both classes require the same current PEMS/2 schema/integrity/normalization and COVE exactness checks. The provenance proof differs. A recovery completion record is never an admission receipt.

R14 V2 SHALL report `provenance_class` and exact provenance artifact paths/digests. Downstream consumers may accept `VERIFIED_RECOVERED` only where their governing contract explicitly allows it.

### D4. Crash mechanism

Resolved as Stage 2 Strategy B: durable transaction barrier over the existing fixed paths.

V1 SHALL NOT migrate Canon to a generation-pointer storage model. The fixed canonical paths remain:

- `project-knowledge/canonical/pems2.jcs.json`
- `project-knowledge/canonical/cove1.jcs.json`

Safety requires both a durable crash barrier and a concurrency lock protocol, as defined in Section 10.

### D5. Semantic-reconciliation reuse

Resolved by excluding semantic judgment from V1 Mode A.

No new per-recovery semantic-reconciliation artifact is required for V1. The closed Mode A predicate must prove that the only semantic-object delta is insertion of the required top-level discriminator. If any judgment is needed about historical knowledge, lifecycle, provenance, identity, relation meaning, supersession, or whether content should remain current, Mode A is ineligible and recovery stops.

A future Mode B proposal may define a dedicated recovery-semantic disposition contract under valid `semantic_reconciliation` authority. Existing candidate-focused R12 SHALL NOT be silently repurposed.

## 5. Approved V1 invariants

1. Valid Canon never enters exceptional recovery.
2. Ordinary R13 never parses, normalizes, reinterprets, or repairs an invalid canonical base.
3. R11 administrative recovery domains remain unchanged.
4. V1 recovery is representation-only and Mode A only.
5. Root approval is exact, direct, explicit, operation-specific, and digest-bound.
6. R7/R8 are unchanged by V1.
7. The deterministic planner and executor confer no authority.
8. PEMS is the semantic source of the repaired pair.
9. Prestate COVE is only a consistency witness; it is never a repair source.
10. Poststate COVE is generated only from the repaired PEMS with the approved package codec.
11. Existing admission plans, receipts, activation evidence, reconciliation dispositions, and candidates remain byte-immutable.
12. Recovery creates a new provenance class instead of manufacturing ordinary admission standing.
13. Exact malformed prestate bytes are preserved before any canonical publication.
14. Every supported package canonical reader honors one shared canonical-store lock/barrier contract.
15. An active, malformed, or indeterminate recovery barrier blocks ordinary canonical consumption and mutation.
16. Exact retry is idempotent; conflicting retry fails closed.
17. Recovery success is necessary evidence for later P3 re-evaluation but does not authorize or restart P3.
18. No implementation gate authorizes the real recovery operation.

## 6. Contract and ownership changes

### 6.1 New recovery contract

Add a normative `RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md` defining:

- `reasoning-distiller-canonical-recovery-plan/1`;
- `reasoning-distiller-canonical-recovery-root-approval/1`;
- `reasoning-distiller-canonical-recovery-barrier/1`;
- `reasoning-distiller-canonical-recovery-completion/1`;
- `reasoning-distiller-canonical-recovery-result/1`;
- the closed Mode A recipe registry and stable failure outcomes;
- protected-root approval rules;
- exact preservation, locking, journal, publish, rollback, retry, and provenance rules.

The new contract owns only exceptional recovery of the canonical PEMS/COVE pair. It does not own admission, semantic reconciliation, ordinary repair, authority administration, or P3.

### 6.2 R13 amendment

Amend `RIL_ADMISSION_CONTRACT.md` narrowly:

- admission remains the only **ordinary admission** primitive allowed to mutate canonical PEMS/COVE;
- `RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md` is the sole explicit exceptional mutation path;
- R13 refuses any active/invalid recovery barrier;
- R13 may use a valid `VERIFIED_RECOVERED` current pair as an ordinary valid base only after the recovery transaction is complete and the barrier is absent;
- R13 still requires independent valid admission activation for any subsequent admission mutation;
- invalid Canon never becomes an R13 base.

No admission receipt/result contract is redefined as recovery evidence.

### 6.3 R14 V2

Version storage verification as described in D3. Content validation remains package-owned and identical across provenance classes. A recovered PASS requires an immutable completion record that binds the exact current pair and a complete recovery provenance chain.

### 6.4 Canonical-store primitive

Introduce one package-owned low-level canonical-store module, for example `runtime/ril_canonical_store.py`, and move supported canonical pair I/O behind it.

At minimum it owns:

- safe canonical path resolution;
- shared/exclusive project-knowledge locking;
- active-barrier detection and validation;
- guarded pair snapshot reads;
- durable canonical publication helpers;
- directory fsync rules;
- explicit internal verification reads during a recovery transaction.

Normal package code MUST NOT directly open the two fixed canonical files.

### 6.5 Context-packaging boundary

P2/P3 remain immutable-snapshot consumers. The generic `context_packaging/source_resolver.py` remains read-only and adapter-driven.

Any package-owned adapter that acquires the live canonical snapshot SHALL acquire it through the shared canonical-store guarded read. After the snapshot bytes and exact digest binding are produced, downstream P2/P3/context-pack code operates only on immutable bytes and does not need a second live barrier check.

Production `rd-distill` remains outside the live Canon acquisition boundary and its fixed production evidence set is unchanged.

## 7. Closed Mode A eligibility and equivalence predicate

V1 freezes one incident recipe family: `missing_top_level_semantic_pems2/1`.

Let `S_raw` be the exact approved prestate PEMS bytes, `S` the strict UTF-8 JSON object parsed from those bytes, and `T` the candidate repaired object.

The recipe is eligible only if every condition below is mechanically true:

1. `S_raw` SHA-256 and optional Git blob identity exactly match the approved prestate.
2. `S` is a JSON object and contains no top-level `semantic` key.
3. There is no alternate or conflicting field that purports to define a different semantic/profile discriminator.
4. `S` contains the expected project identity, `records`, and `relations` structure required by the incident recipe.
5. `T` is constructed only by deep-copying `S` and inserting exactly `"semantic":"pems/2"` at the top level.
6. Removing only top-level `semantic` from `T` yields an object deeply equal to `S`, including array order and every nested value.
7. Current package PEMS normalization applied to `T` does not alter the record/relation object sequence or any nested value other than deterministic object-key serialization. If normalization would reorder semantic graph elements relative to `S`, this V1 recipe is ineligible.
8. `T` validates under the exact approved current PEMS/2 JSON schema.
9. `T` passes the exact approved package PEMS semantic/integrity validator, including project identity, provenance, relation endpoint, derived-premise, and contradiction-order requirements.
10. Prestate COVE parses and decodes exactly to `S`. Any prestate PEMS/COVE disagreement makes Mode A ineligible.
11. Candidate PEMS bytes are exact approved JCS/normalization bytes for `T`.
12. Candidate COVE is generated only from `T` with the exact approved `cove/1 | pems/2 | jcs/1` implementation.
13. Candidate COVE decodes exactly to `T` and reserialization reproduces the exact candidate PEMS bytes.
14. Repeating candidate PEMS and COVE generation produces byte-identical outputs.
15. The equivalence proof records every checked invariant and the exact schema/validator/serializer/codec identities.

Any additional data edit, semantic repair, inferred field, dropped field, reordered semantic item, reconstructed receipt contribution, or judgment call is outside V1 and fails `UNSUPPORTED_CANONICAL_DAMAGE`.

## 8. Recovery plan and root approval identity

The read-only planner SHALL emit one canonical `reasoning-distiller-canonical-recovery-plan/1` object. Its digest domain SHALL contain every consequential input, including:

- project identity;
- exact canonical paths;
- prestate PEMS/COVE SHA-256 and available Git blob identities;
- exact preserved-evidence inventory digest;
- Mode A recipe ID and recipe implementation identity;
- exact candidate PEMS/COVE hashes;
- equivalence-proof digest;
- exact schema, validator, serializer, COVE codec, planner, canonical-store, recovery-executor, and behavior-bearing dependency closure identities;
- runtime identity where behavior can vary by runtime;
- recovery contract and R14 V2 identities;
- recovery generation;
- expected barrier identity;
- expected terminal provenance class `VERIFIED_RECOVERED`.

Protected-root approval SHALL bind the single recovery-plan digest. Repeating high-value hashes in the approval for readability is allowed only when implementation checks they are consistent with the plan.

At apply time, protected-root identity and the exact approval binding are revalidated under the live governing root contract. No prompt, role label, repository ownership, or prior activation substitutes for this approval.

## 9. Preserved evidence and receipt treatment

Before canonical publication, persist exact malformed prestate bytes and immutable manifests beneath:

`project-knowledge/recovery/canonical-pems-cove/generations/<generation>/`

At minimum preserve:

- `prestate/pems2.raw`;
- `prestate/cove1.raw`;
- prestate raw hashes, byte counts, canonical paths, and available Git blob IDs;
- the recovery plan;
- root approval;
- equivalence proof;
- selected receipt/admission evidence inventory;
- executor/package closure manifest;
- result/completion records.

Preserved malformed bytes are never normalized or rewritten.

Existing ordinary admission receipts remain immutable historical claims. V1 may classify their structural validity, recorded hashes, and relation to the exact prestate for evidence inventory purposes. V1 does not rely on historical receipt replay to derive repaired content and does not claim that a reproducible non-conformant historical transition was normatively valid.

The recovery completion record provides current recovered-state provenance by proving a lossless bridge from the exact preserved current prestate to the exact repaired poststate. It does not retroactively repair historical receipts.

## 10. Canonical concurrency, crash barrier, and reader inventory

### 10.1 Shared/exclusive lock protocol

Supported package canonical I/O SHALL synchronize using one lock on the ordinary non-symlink `project-knowledge/` directory descriptor, or an implementation-equivalent non-mutating lock substrate proven by conformance tests. The implementation SHALL NOT require a read-only verifier to create a lock file.

- ordinary canonical readers acquire a shared lock before barrier check and hold it through reading both canonical files and establishing their snapshot hashes;
- R13 canonical mutation acquires an exclusive lock for its current-base read through canonical publication and receipt-commit boundary;
- canonical recovery acquires an exclusive lock before apply-time prestate revalidation and holds it through completion or verified rollback;
- inability to obtain the required lock fails closed with a stable busy/conflict outcome rather than reading an unguarded pair.

The shared lock closes the race in which a reader could observe “no barrier,” then have recovery create a barrier and replace one file before the reader obtains the second file.

### 10.2 Durable barrier

The durable active barrier is:

`project-knowledge/recovery/canonical-pems-cove/active.json`

Its contract is `reasoning-distiller-canonical-recovery-barrier/1` and it binds the recovery generation, plan digest, exact prestate pair, exact intended poststate pair, and transaction state.

Any existence of `active.json` blocks normal canonical consumption. A symlink, non-regular file, malformed object, unknown contract, or digest inconsistency at the barrier path fails closed as a barrier conflict; it is never ignored as “no active recovery.”

### 10.3 Supported canonical readers

The implementation SHALL migrate and test at least these live reader classes:

1. `runtime/ril_admission.py`, which currently reads and writes the fixed canonical pair;
2. `runtime/ril_storage_verification.py`, which currently reads the fixed pair and provenance evidence;
3. any package-owned adapter that acquires live `canonical_state` bytes for context packaging before `source_resolver`/P3;
4. the recovery planner/executor itself, through privileged canonical-store APIs that require the appropriate lock and transaction state.

`context_packaging/source_resolver.py` and P3 remain immutable-byte consumers after guarded acquisition. `runtime/ril_status.py` is not currently a canonical pair reader.

A repository conformance test SHALL mechanically reject direct package production/runtime references to the fixed canonical paths outside the canonical-store module and explicitly reviewed recovery internals. The preferred implementation has even recovery internals call canonical-store APIs so the fixed-path whitelist can remain one module.

Unmodified external programs that bypass package APIs and read repository files directly are outside the enforceable package lock protocol. They receive no supported canonical-consumer guarantee and must not be described as safely concurrent readers.

## 11. Durable publication and crash recovery

While holding the exclusive canonical lock, recovery SHALL perform this exact class of sequence:

1. revalidate live root authority and exact root approval;
2. re-read canonical PEMS/COVE and prove the approved prestate fingerprint;
3. preserve and fsync exact prestate bytes and required immutable evidence;
4. materialize candidate PEMS/COVE in same-filesystem temporary files and complete all prepublication content checks;
5. create and fsync the per-generation in-progress journal;
6. create and fsync `active.json`, then fsync its parent directory;
7. publish PEMS with file fsync, atomic rename/replace, then canonical-directory fsync;
8. publish COVE with file fsync, atomic rename/replace, then canonical-directory fsync;
9. verify the complete pair content without requiring an ordinary receipt;
10. write and fsync the immutable recovery completion record and generation directory;
11. verify R14 V2 as `PASS/VERIFIED_RECOVERED` against that exact completion record;
12. remove or atomically complete the active barrier only after the recovered PASS, then fsync the barrier parent directory;
13. release the exclusive lock.

A crash releases the process lock but leaves the durable barrier. Subsequent supported readers acquire their shared lock, observe the barrier, and fail closed.

A recovery restart with an active barrier may do only one of two things under the exclusive lock:

- prove the exact approved poststate and exact durable completion evidence, finish that same transaction, and clear the barrier; or
- restore both exact preserved prestate byte sequences, verify their hashes, write a durable rolled-back result, and clear the barrier only after exact restoration is proven.

If neither exact state can be established, leave the barrier active and return `CANONICAL_RECOVERY_INDETERMINATE`.

## 12. Stable V1 outcomes

The recovery family SHALL freeze at least these stable outcomes:

- `RECOVERY_NOT_REQUIRED`;
- `UNSUPPORTED_CANONICAL_DAMAGE`;
- `CANONICAL_PRESTATE_MISMATCH`;
- `ROOT_RECOVERY_APPROVAL_REQUIRED`;
- `ROOT_RECOVERY_APPROVAL_MISMATCH`;
- `RECOVERY_PLAN_MISMATCH`;
- `MIGRATION_RECIPE_MISMATCH`;
- `EXECUTOR_CLOSURE_MISMATCH`;
- `PEMS_RECOVERY_INVALID`;
- `COVE_PRESTATE_MISMATCH`;
- `COVE_RECOVERY_MISMATCH`;
- `CANONICAL_RECOVERY_BUSY`;
- `CANONICAL_RECOVERY_ACTIVE`;
- `CANONICAL_RECOVERY_BARRIER_INVALID`;
- `RECOVERY_PUBLICATION_FAILED_ROLLED_BACK`;
- `CANONICAL_RECOVERY_INDETERMINATE`;
- `RECOVERY_CONFLICT`;
- `NO_CHANGE` for an exact already-completed retry.

V1 SHALL NOT define `RECOVERY_SCOPE_UNASSIGNED`, `RECOVERY_ROLE_UNAVAILABLE`, or `RECOVERY_ACTIVATION_INVALID`, because V1 deliberately does not add an R7/R8 recovery scope.

## 13. Frozen CR0-CR13 gates

| Gate | Requirement | Failure effect |
|---|---|---|
| CR0 | This Stage 3 plan and exact V1 contract set are frozen. | no implementation/recovery |
| CR1 | Exact implementation bundle plus adversarial conformance suite passes, including canonical-reader inventory enforcement. | no recovery |
| CR2 | Exact target project identity and malformed PEMS/COVE fingerprints match the recovery plan. | stale/conflict |
| CR3 | Ordinary current-state verification proves Canon invalid in the one accepted Mode A recoverable class; valid Canon returns `RECOVERY_NOT_REQUIRED`. | no recovery |
| CR4 | Exact malformed PEMS/COVE and required evidence are durably preserved and digest-bound. | no canonical write |
| CR5 | Closed Mode A recipe produces exactly one candidate and full equivalence proof. | unsupported damage |
| CR6 | Candidate PEMS passes exact current schema, semantic/integrity, project identity, and normalization rules. | no canonical write |
| CR7 | Candidate COVE is generated only from candidate PEMS and exact round-trip identity passes; prestate COVE witness also matched prestate PEMS. | no canonical write |
| CR8 | Protected root directly approves the exact immutable recovery-plan digest, including executor closure and generation. | no canonical write |
| CR9 | V1 proves no semantic judgment is required. Any required semantic judgment makes Mode A ineligible. | unsupported damage |
| CR10 | Apply-time revalidation under exclusive lock repeats CR2-CR9 and establishes the durable active barrier before publication. | stale/conflict |
| CR11 | Durable pair publication succeeds and complete poststate content verification passes without ordinary-receipt circularity. | rollback or indeterminate block |
| CR12 | Immutable recovery completion record durably matches the exact observed poststate. | recovery incomplete |
| CR13 | R14 V2 returns `PASS/VERIFIED_RECOVERED`; barrier is then safely cleared. Ordinary R13 can consume the repaired valid base without performing an admission. | recovery incomplete / ordinary admission blocked |

P3 remains outside CR0-CR13. Recovery completion does not select, authorize, or resume P3.

## 14. Required adversarial conformance

Before incident rehearsal, tests SHALL prove at least:

1. valid canonical state never enters recovery;
2. any prestate hash/blob drift fails before mutation;
3. wrong/missing protected-root identity fails;
4. approval replay against another generation fails;
5. altered recovery plan, recipe, candidate, executor, schema, validator, serializer, codec, or behavior-bearing dependency fails;
6. any semantic delta beyond the single allowed discriminator insertion fails;
7. prestate COVE disagreement makes Mode A ineligible;
8. malformed or missing recovered provenance prevents `VERIFIED_RECOVERED`;
9. no ordinary receipt is created, rewritten, or relabeled by recovery;
10. no R7/R8 authority state is created or mutated by recovery;
11. crash before PEMS publication leaves exact prestate;
12. crash after PEMS publication and before COVE publication is blocked by durable barrier and supports only exact roll-forward/rollback;
13. crash after pair publication but before completion record remains blocked;
14. crash after completion record but before barrier clear can finish only the same exact transaction;
15. rollback restores both exact raw prestate byte sequences;
16. rollback hash mismatch leaves an indeterminate barrier;
17. exact successful retry returns `NO_CHANGE` only for identical plan/approval/poststate/completion evidence;
18. same generation with different plan or poststate fails `RECOVERY_CONFLICT`;
19. corrupted preserved evidence blocks completion/retry;
20. a reader holding the shared lock prevents recovery publication from beginning;
21. an exclusive recovery lock prevents a new supported reader from obtaining an unguarded snapshot;
22. a crash releases the process lock but the durable barrier still blocks readers;
23. R13 admission and recovery cannot mutate Canon concurrently;
24. static package-source conformance rejects a newly introduced direct fixed-path canonical reader outside the canonical-store boundary;
25. context-pack canonical snapshot acquisition fails closed while recovery is active, while downstream immutable P2/P3 processing remains independent of live Canon after snapshot acquisition.

## 15. Implementation sequence

### G0 - Contract freeze

Implement only normative contracts/schemas/outcome vocabulary from this plan. Explicitly mark Mode B unsupported. Freeze the one Mode A incident recipe and R14 V2 provenance model.

### G1 - Guarded canonical store

Implement shared/exclusive locking, barrier validation, guarded pair reads, durable publish helpers, and the static direct-reader inventory test. Migrate R13/R14 and package-owned live canonical snapshot acquisition to this boundary before implementing recovery publication.

### G2 - R13/R14 integration

Amend R13's exclusivity language and runtime barrier behavior. Implement R14 V2 with `VERIFIED_ADMITTED` and `VERIFIED_RECOVERED`, preserving identical PEMS/COVE content validation across both provenance classes.

### G3 - Closed Mode A recipe

Implement `missing_top_level_semantic_pems2/1` and the exact equivalence proof. No free-form migration callback or general field-transform DSL is allowed in V1.

### G4 - Read-only planner

Fingerprint the exact malformed pair, verify prestate COVE witness, construct the single candidate pair, collect immutable evidence inventory, bind executable closure, and emit the canonical recovery plan. Planning performs no repository project-state mutation except writing separately selected derived rehearsal artifacts outside Canon/recovery standing stores where governing test contracts permit.

### G5 - Protected-root approval validation

Implement exact recovery-plan approval validation under the existing protected-root authority model without modifying R7/R8.

### G6 - Recovery executor

Implement exact prestate preservation, exclusive locking, durable active barrier, apply-time revalidation, pair publication, completion record, exact rollback, and retry semantics. The executor remains unusable without valid exact root approval.

### G7 - Adversarial conformance

Execute the full Section 14 suite on the exact candidate implementation bundle and supported runtime.

### G8 - Incident-specific read-only rehearsal

Against an immutable copy of blocked PEMS blob `bb7c474e935243b45ff02a5778a94bbcdc654d72` and paired COVE blob `7ff52fb925a667c4cc1782da9b475dff831e45ef`, prove CR2-CR9 and compute the exact expected repaired pair and recovery-plan identity. Do not mutate the live canonical paths.

If this rehearsal cannot prove the closed Mode A predicate, stop with `UNSUPPORTED_CANONICAL_DAMAGE`. Do not begin Mode B.

### G9 - Fresh independent implementation review

A fresh independent Engineer reviews the exact implementation candidate, exact conformance evidence, reader inventory, executable closure, and G8 rehearsal. Any blocker returns to a fresh implementation Engineer.

### G10 - Governed recovery operation, outside this Stage 3 execution scope

A real recovery operation requires a separately selected invocation, live re-resolution, the exact reviewed implementation bundle, exact incident plan, and fresh direct protected-root approval. This Stage 3 artifact does not grant or perform that operation.

### G11 - Post-recovery handoff, outside this Stage 3 execution scope

After a real recovery, independently verify the durable `VERIFIED_RECOVERED` state and stop. A fresh P3 work unit must re-resolve the repository, bind the recovery evidence, and determine whether P3's own prerequisites are satisfied.

## 16. Definition of done

The V1 implementation is not ready for a real recovery until evidence proves all of the following:

1. R13's exceptional mutation exception is explicit and narrow;
2. R14 V2 has mechanically distinct admitted and recovered provenance classes;
3. recovery completion can never be mistaken for an ordinary admission receipt;
4. no R7/R8 recovery authority surface was added;
5. protected-root approval binds one exact recovery plan;
6. the Mode A predicate has no semantic judgment branch;
7. prestate COVE must match prestate PEMS exactly;
8. repaired PEMS is the sole source for repaired COVE;
9. every supported package live Canon reader is guarded by the shared/exclusive canonical-store protocol;
10. the durable barrier closes crash windows and the lock closes live TOCTOU windows;
11. canonical publication includes required file and parent-directory durability;
12. preserved malformed bytes remain exact and immutable;
13. old admission/reconciliation evidence remains byte-identical;
14. exact retry/no-change/conflict semantics are proven;
15. rollback and indeterminate behavior are proven at every pair-split crash boundary;
16. G8 produces exactly one valid incident candidate or terminates unsupported;
17. a fresh independent implementation review passes the exact candidate/evidence bundle;
18. no live recovery, Canon mutation, authority mutation, admission, or P3 continuation has been smuggled into implementation evidence.

## 17. Remaining uncertainties and explicitly deferred decisions

1. Mode B admission-lineage reconstruction is deliberately unresolved for V1 and requires a new three-stage proposal workflow.
2. A future distinct-principal or multi-person recovery policy is not established by this plan.
3. External programs that bypass package canonical APIs cannot be made safe by an advisory package lock; they are unsupported concurrent consumers.
4. Historical receipt/executor inconsistencies remain evidence to preserve and investigate. V1 Mode A does not convert them into normative standing.
5. Exact root-approval UX and CLI surface may be selected during G0/G5 only if it preserves the existing root authority contract and all bindings frozen here. It may not introduce a new delegated recovery authority class.

None of these uncertainties blocks implementation of the accepted Mode A V1 design. Items 1 and 2 are explicitly outside V1 rather than silently resolved.

## 18. Exact next governed action and terminal boundary

This Stage 3 reconciliation is complete at this artifact.

The next consequential work belongs to a **fresh implementation Engineer** scoped only to G0-G8 of this final plan, followed by a fresh independent Engineer for G9. Before acting, that Engineer must independently re-resolve live repository state and establish whatever implementation authority/evidence the then-current repository contracts require. This handoff does not itself create that authority.

No real G10 recovery operation is authorized here. No Canon mutation, authority mutation, admission, root approval, or P3 continuation belongs to this activation.

A fresh chat is appropriate for the receiving implementation Engineer because the proposal/review/Steward reconciliation artifact is now complete and the next consequential stage changes from governed semantic reconciliation to separately bounded implementation.
