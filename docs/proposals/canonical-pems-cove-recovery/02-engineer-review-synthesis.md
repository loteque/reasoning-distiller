# Canonical PEMS/COVE Recovery - Stage 2 Engineer Review/Synthesis

Status: **Independent review complete; compatible only with required revisions**

Disposition: **`CANONICAL_PEMS_COVE_RECOVERY_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`**

Method: `proposal-review-synthesis/1`

Repository: `loteque/reasoning-distiller`

Coordination control ref: `main`

Coordination revision resolved for this review and re-resolved immediately before this Stage 2 write: `d46300a54a444cc866717986c1f5b493de3ab13f`

Stage 1 proposal commit: `aa8a5e751db0d5fb1472f2879691d4c9d38dd93f`

Stage 1 proposal tree: `66a22ea27a3150ca6cf2845bfe1d106315073876`

Stage 1 proposal blob: `f5bba0bb6e5d2ced5f233aa86ff8a51602cd043c`

Stage 1 proposal path: `docs/proposals/canonical-pems-cove-recovery/01-rpg-engineer-proposal.md`

Blocked canonical PEMS Git blob: `bb7c474e935243b45ff02a5778a94bbcdc654d72`

Paired canonical COVE Git blob: `7ff52fb925a667c4cc1782da9b475dff831e45ef`

Stage: **Stage 2 independent Engineer review and synthesis only**

Authority posture: this artifact is a bounded technical review. It establishes no Project Steward authority, no canonical-recovery authority, no accepted RIL activation, no root approval, no reconciliation, no admission, no recovered standing, no implementation authorization, no Canon mutation, and no P3 continuation. The Engineer role is the operational review role selected by the proposal-review workflow. It does not acquire Steward or root authority by producing this artifact.

## 1. Findings first

### F1. Blocking: the proposal does not yet provide a lawful post-recovery standing path under R14

The central provenance problem is not solved by producing a schema-valid repaired pair plus a recovery record.

Current R14 requires the current canonical PEMS/COVE pair to be backed by at least one immutable ordinary `reasoning-distiller-admission-receipt/1` whose admitted PEMS and COVE hashes exactly match the current canonical bytes. A lossless migration necessarily changes the PEMS hash, and regenerated COVE changes the COVE hash. Existing admission receipts are correctly proposed to remain immutable, so after recovery no ordinary receipt can match the repaired pair.

The present incident makes the gap concrete. Admission commit `95a65e2e036879ce1c7aadc22b19dd5da07106a3` wrote receipt:

`project-knowledge/admission/receipts/35ae25fea959c5567eeb70194889309c0ad89dde0dff8e5400df5ba1653b50ec.json`

That receipt records admitted PEMS SHA-256:

`22beb53b220ea820b65e7a77f1db2be3ecde1aad7de95a4f5523942819511061`

which is the malformed current PEMS hash. A repaired pair must have different hashes. Calling post-write validation "R14-equivalent" avoids the contradiction but does not restore the repository's actual R14 verification contract.

Required revision:

1. version or amend R14 so recovered canonical state has an explicit, mechanically checkable provenance branch;
2. define an immutable recovery completion record as the provenance bridge from exact preserved pre-state to exact repaired post-state;
3. require that bridge to bind the exact pre-state evidence, recovery proposal, protected-root approval, deterministic reconstruction identity, post-state pair, and verification result;
4. preserve provenance class rather than manufacturing an ordinary admission receipt;
5. expose a distinct success class such as recovered verified state rather than pretending recovery was an ordinary admission; and
6. require downstream consumers to consume that recovered-state class only where their governing contract permits it.

A subsequent ordinary R13 admission may create a new ordinary receipt for its own post-state, but recovery itself must not fabricate one.

### F2. Blocking: R13's canonical-mutation exclusivity must be amended explicitly

Current R13 states that admission is the only RIL primitive in its slice allowed to mutate canonical PEMS/COVE project knowledge. Stage 1 proposes a second primitive that performs exactly that mutation while also saying R13 should not be relaxed.

The ordinary R13 preconditions should remain strict, but the exclusivity sentence cannot remain unchanged. Otherwise an accepted recovery executor would still violate the live canonical-mutation contract by construction.

Required revision:

- amend or version the canonical-mutation rule so R13 remains the only **ordinary admission** mutation primitive;
- define canonical PEMS/COVE recovery as one narrowly specified exceptional mutation path, eligible only when ordinary storage verification proves the current canonical state invalid in an accepted recoverable class;
- make the exception explicit in R13, R14, and the new recovery contract rather than relying on a neighboring contract to imply it; and
- preserve the rule that no ordinary admission transaction may normalize, reinterpret, or repair an invalid base.

### F3. Blocking: adding `canonical_recovery` to R7/R8 is not the smallest safe authority change demonstrated by Stage 1

R7 currently defines **exactly two** Steward scopes:

- `semantic_reconciliation`
- `admission`

R8 validates activation only for those two scopes. Stage 1 proposes widening both primitives with a third independently assignable `canonical_recovery` scope, then also requires protected-root human approval for each exact recovery.

The review does not find sufficient necessity for this new ordinary Steward-authorization surface in v1. R11 already establishes the repository's strongest exceptional-recovery precedent: exceptional continuation is an explicit protected-root human recovery ceremony, not delegated administration. Canonical PEMS/COVE recovery is a different domain and must not be inserted into R11 unchanged, but its authority model can remain domain-specific and root-bound without widening R7/R8.

Recommended Stage 2 synthesis:

- keep R7/R8 unchanged for v1;
- define the new canonical-recovery contract's execution authority directly as an exact protected-root approval over one exact recovery proposal and pre/post state;
- use `semantic_reconciliation` only when actual semantic judgment is required, through an explicitly defined recovery-semantic disposition primitive rather than by pretending candidate-focused R12 already covers the case;
- keep deterministic Mode A free of a second Steward decision when no semantic judgment exists; and
- if Stage 3 requires dual-human control as a policy objective, define that independently and enforce distinct principals/credentials explicitly instead of calling `canonical_recovery` Steward activation plus root approval a "two-key" ceremony.

A root operator and a Steward role may be exercised by the same human. Therefore the Stage 1 construction is a dual-gate mechanism, but it is not proven to be two-person or two-key control.

This finding does not forbid a future dedicated recovery authorization scope. It requires the authority expansion to be justified by a capability separation that cannot be achieved by the narrower root-bound recovery contract.

### F4. Blocking: historical contract reproducibility must bind the exact historical executor path, not only historical schemas and receipts

The incident contains direct evidence that historical artifact existence is not equivalent to historical conformance.

At admission commit `95a65e2e036879ce1c7aadc22b19dd5da07106a3`:

- the PEMS schema blob is `cd7683d704e8aef2842a0c1b25b453fb1dbc8030`;
- that schema already requires top-level `semantic`, `project_id`, `records`, and `relations` and constrains `semantic` to `pems/2`;
- the admission receipt written in the same commit records the currently malformed PEMS hash as admitted output; and
- the current PEMS object with that hash lacks the required top-level `semantic` member.

Therefore Mode B must not reason: "a receipt exists at commit X and schema X is reproducible, so the transition was valid under X." That conclusion is contradicted by the repository evidence.

Required revision:

Historical reconstruction must bind, at minimum:

1. exact admission plan bytes and digest;
2. exact base bytes and hash;
3. exact candidate/disposition inputs;
4. exact executable admission implementation and imported behavior-bearing dependencies;
5. exact schema/validator/serializer/COVE implementation identities;
6. exact package or source closure from which those executable bytes were resolved;
7. exact invocation mode and relevant runtime identity where behavior can vary by runtime;
8. exact produced output hashes; and
9. whether the reproduced transition was conformant to the normative contracts that were in force at that historical revision.

A reproducible **non-conformant** transition remains evidence of what happened. It must not be upgraded into lawful standing by replay.

### F5. Blocking: the proposed journal does not create pair-level crash consistency unless every canonical reader honors a transaction barrier

Atomic replacement of two independent files is not an atomic pair commit. A crash can occur after PEMS replacement and before COVE replacement. A journal makes recovery possible, but concurrent or restarted readers can still observe a split pair unless they are required to check the journal before consuming Canon.

Stage 1 names R13 and P3 as blocked by an active or indeterminate recovery, but this must be a package-wide canonical-read invariant, not a local convention.

Required revision: choose and specify one of these strategies:

**A. Single atomic generation pointer**

Write a complete versioned PEMS/COVE generation and atomically change one manifest/pointer that defines the current generation.

**B. Durable transaction barrier over the existing fixed canonical paths**

Before any canonical replacement:

1. write and fsync a recovery journal/barrier containing exact pre/post fingerprints and transaction generation;
2. fsync the parent directory;
3. require every package primitive that reads canonical PEMS/COVE to fail closed while that barrier exists;
4. publish each canonical file with file and directory durability rules;
5. verify the complete post-state;
6. write and fsync the immutable completion record;
7. only then atomically clear/complete the barrier and fsync its directory.

On restart, the only allowed operations are exact completion of the approved post-state or exact restoration of the preserved pre-state. If neither can be proven, recovered state remains globally indeterminate.

The final design must enumerate the canonical consumers that honor this barrier. It is insufficient to name only the recovery executor.

### F6. Required: Mode A needs an executable semantic-equivalence predicate, not a narrative claim of losslessness

Mode A is the correct first path for the present incident if, and only if, a package-owned recipe can prove the defect is representation-only.

For the missing-`semantic` incident, a candidate recipe should be eligible only after the planner proves all of the following against the exact blocked blob:

- the input is parseable JSON;
- the absent discriminator is the exact declared defect;
- no conflicting `semantic` field exists;
- all remaining top-level structure is accepted by the recipe's frozen input predicate;
- every record, relation, ID, lifecycle value, provenance object, relation endpoint, project identity binding, and semantic integrity condition is unchanged under the approved projection;
- the candidate obtained by the recipe validates under current normative PEMS/2;
- regenerated COVE round-trips exactly to the candidate PEMS; and
- repeated execution produces the exact same candidate bytes.

The semantic-preservation proof should compare explicit projections or exact graph components, not infer equivalence from "the validator passes after adding one field."

### F7. Required: v1 should implement Mode A first and defer Mode B unless Mode A is proven insufficient

Stage 1's Mode B is substantially larger than a canonical migration primitive. It reconstructs state from historical admissions, classifies receipt standing, reproduces historical execution, handles forks/gaps, and may require semantic reconciliation. That is a second recovery architecture hiding inside the first.

The present incident has an exact parseable canonical PEMS object and an apparent representation-level defect. There is no demonstrated need to implement historical-lineage reconstruction before attempting a rigorously proven lossless migration.

Required sequencing change:

- freeze and implement Mode A only in the first recovery contract version;
- require an incident-specific read-only rehearsal against exact blobs `bb7c474e935243b45ff02a5778a94bbcdc654d72` and `7ff52fb925a667c4cc1782da9b475dff831e45ef`;
- if the rehearsal cannot prove Mode A lossless, stop with an explicit unsupported-damage disposition;
- route Mode B through a separate proposal/review/reconciliation cycle, or at minimum a separately frozen later gate whose historical execution and standing semantics are independently reviewable.

This reduces implementation and authority surface at the moment of highest operational risk.

### F8. Required: pre-state COVE may be a consistency witness, never a semantic repair source

Stage 1 correctly keeps repaired PEMS upstream of repaired COVE. Tighten the recovery rule:

- Mode A may use pre-state COVE only to test whether it decodes exactly to the malformed pre-state PEMS;
- exact decode equality is corroborating evidence that the pair represented the same malformed object;
- COVE must never supply a missing PEMS semantic field, record, relation, identity, provenance edge, or lifecycle value;
- if pre-state COVE does not decode exactly to pre-state PEMS, Mode A is ineligible because the damage is no longer a one-sided representation defect; and
- any later Mode B must treat COVE as evidence bytes, not independent semantic authority.

### F9. Required: receipt analysis must distinguish immutable historical claims from normative standing

Stage 1's standing-analysis overlay is a good direction, but the classifications need a stronger separation.

For each receipt on a selected lineage, distinguish at least:

- artifact structural validity;
- digest/path identity validity;
- exact input/output reproducibility;
- historical executor reproducibility;
- conformance to the normative contracts at the claimed historical transition;
- relationship to the preserved malformed pre-state;
- semantic contribution relationship to the repaired state; and
- current provenance relevance.

A receipt can be byte-valid and hash-consistent while describing a non-conformant admission result. The current incident appears to require exactly that distinction.

Recovery must not rewrite, replace, or retroactively invalidate historical receipt bytes. It may record that a receipt's claimed transition was non-conformant under the governing historical contract.

### F10. Required: CR0-CR13 must be reordered around content verification, recovery evidence, and recovered standing

The Stage 1 gate structure is useful but presently contains a circularity: R14 requires receipt-backed current state, while the recovery record is written after "R14-equivalent" verification.

Recommended gate synthesis:

| Gate | Stage 2 required meaning |
|---|---|
| CR0 | Stage 3 accepts the architecture and exact implementation gates. |
| CR1 | Exact implementation bundle and adversarial conformance suite pass. |
| CR2 | Exact project identity and malformed PEMS/COVE pre-state fingerprints match. |
| CR3 | Ordinary current R14 fails in an explicitly eligible recoverable class; valid Canon is never routed to recovery. |
| CR4 | Exact malformed bytes and selected evidence are preserved durably and digest-bound. |
| CR5 | The approved Mode A recipe produces exactly one candidate and its lossless projection proof passes. |
| CR6 | Candidate PEMS passes current schema, integrity, project identity, and deterministic normalization. |
| CR7 | Candidate COVE is generated only from candidate PEMS and exact round-trip identity passes. |
| CR8 | Required protected-root recovery approval binds exact proposal, pre/post pair, recipe, executor/package identity, and recovery generation. |
| CR9 | Any separately required semantic-reconciliation evidence is valid and exact; Mode A should normally require none. |
| CR10 | Apply-time revalidation repeats all mutable preconditions and establishes the durable global recovery barrier. |
| CR11 | Publication completes and pair-content verification passes without relying on an ordinary admission receipt. |
| CR12 | Immutable recovery completion record is durably written and exactly matches the observed post-state. |
| CR13 | Recovery-aware storage verification validates the post-state and its recovery provenance; ordinary R13 can consume the repaired PEMS as a valid base without performing an admission. |

P3 remains outside these gates. Recovery success is evidence for a later P3 decision, not P3 authority.

### F11. Recommendation: bind root approval to one canonical recovery-plan digest and the executable closure

Stage 1 binds many individual fields into root approval. The stronger and simpler rule is that the approval binds one canonical recovery proposal digest whose digest domain already includes every consequential input, including:

- pre-state pair fingerprint;
- exact recovery mode and recipe;
- expected post-state pair fingerprint;
- package/executor/validator/codec identities;
- preserved-evidence inventory;
- any semantic-reconciliation input;
- concurrency basis/generation; and
- expected result class.

The approval may repeat high-value hashes for operator readability, but repeated fields must be consistency-checked against the proposal rather than treated as independent truth.

### F12. Required: adversarial tests must prove the new boundaries, not only happy-path migration

Before any real recovery, conformance must cover at least:

1. valid current Canon refuses recovery;
2. stale pre-state hash refuses recovery;
3. malformed or mismatched root approval refuses recovery;
4. approval replay against another generation refuses recovery;
5. altered recipe or executor identity after approval refuses recovery;
6. migration changes one undeclared semantic byte and is rejected;
7. COVE does not decode to pre-state PEMS and Mode A is rejected;
8. historical receipt exists but historical transition is non-conformant;
9. recovery post-state lacks a valid recovery provenance bridge and recovered R14 fails;
10. crash before first canonical rename;
11. crash between PEMS and COVE publication;
12. crash after pair publication but before completion record;
13. crash after completion record but before transaction-barrier clear;
14. concurrent R13/R14/P3 or other canonical reader sees active barrier and fails closed;
15. exact retry after success returns no-change only for the exact approved transaction;
16. conflicting retry fails closed;
17. rollback bytes differ from preserved pre-state and becomes indeterminate;
18. missing or corrupted preserved evidence blocks completion; and
19. no recovery path creates an ordinary admission receipt or silently changes Steward authorization.

## 2. Stage 1 elements accepted by this review

The following Stage 1 architecture should survive into Stage 3 unless conflicting evidence is introduced:

1. **A separate canonical PEMS/COVE recovery contract is necessary.** R11's supported administrative domains do not include PEMS/COVE, and ordinary R13 cannot lawfully repair an invalid base.
2. **Recovery must preserve the malformed state byte-for-byte.** Git history alone should not be the only preservation mechanism for the exceptional transaction.
3. **Planning and rehearsal must be read-only.** No authority, Canon, admission, or recovery state should change while determining whether a deterministic repair exists.
4. **PEMS remains semantically upstream of COVE.** Repaired COVE is generated from repaired PEMS and is never independently edited.
5. **Old admission and reconciliation evidence remains immutable.** Recovery adds evidence; it does not rewrite history to make earlier operations appear conformant.
6. **Ordinary R13 remains strict.** Recovery restores a valid base instead of teaching ordinary admission to normalize invalid state.
7. **Root approval must be exact and fail closed.** An exceptional canonical mutation requires explicit protected-human authorization bound to exact bytes and evidence.
8. **Apply-time revalidation is mandatory.** Approval cannot freeze mutable project state or waive later validation.
9. **Recovery conflict and indeterminate states must be explicit.** The executor cannot improvise after a partial publication.
10. **P3 remains separately blocked.** A successful recovery does not restart the evaluation or create P3 authority.

## 3. Stage 1 proposal outcome

Stage 1 is **architecturally compatible but not implementation-ready**.

The proposal correctly identifies a real governance gap and selects the correct broad shape: a separate exceptional canonical recovery primitive, deterministic reconstruction, preserved malformed evidence, PEMS-first repair, root-bound authorization, fail-closed publication, and explicit post-recovery verification.

However, implementation against the current Stage 1 text would create unresolved contradictions with live R7/R8, R13, and R14 and would overcommit to a second historical-lineage recovery mode before the incident has proven that mode necessary.

No implementation should begin from Stage 1 plus this review until Stage 3 explicitly reconciles the required revisions.

## 4. Stage 2 architecture synthesis

### 4.1 Authority and ownership

Recommended v1 ownership:

| Concern | Owner / authority |
|---|---|
| PEMS/2 schema, validation, normalization, migration recipe | Package-owned PEMS/COVE implementation |
| Read-only incident planner and lossless proof | Generic recovery package primitive |
| Semantic judgment, only if required | Existing `semantic_reconciliation` authority through a new explicitly defined recovery-semantic artifact contract |
| Exact exceptional mutation approval | Currently established protected root under the new recovery contract |
| Deterministic recovery execution | Recovery executor, possessing no independent authority and consuming exact approved evidence |
| Ordinary future admission | Existing R13 `admission` authority and activation |
| Recovered-state storage verification | Versioned/amended R14 consuming recovery provenance |
| P3 continuation | Separate later P3 activation and governing evaluation |

The deterministic executor is not an authority principal. It performs only the exact transition approved by the governing recovery contract.

### 4.2 Recommended v1 data flow

```text
invalid canonical PEMS/COVE
        |
        v
read-only damage classification
        |
        v
package-owned Mode A recipe + lossless proof
        |
        v
exact recovery proposal
        |
        +--> optional semantic-reconciliation input only if genuinely needed
        |
        v
protected-root exact approval
        |
        v
durable transaction barrier + preserved pre-state
        |
        v
deterministic pair publication
        |
        v
pair-content verification
        |
        v
immutable recovery completion record
        |
        v
recovery-aware R14 verification
        |
        v
R13 may again consume a valid base
P3 remains separately gated
```

### 4.3 Recommended v1 scope

V1 should cover **lossless canonical migration only**.

It should not attempt to reconstruct absent semantic knowledge from receipts, COVE, repository history, model inference, current-policy inference, or best-effort lineage replay. If the exact malformed pair cannot be transformed losslessly by an approved package recipe, v1 returns an unsupported-damage result and stops.

Mode B remains a valid future research/proposal direction, but the repository evidence shows it needs its own treatment of non-conformant historical admissions and executable provenance.

## 5. Receipt and standing synthesis

The repaired state must preserve three separate truths:

1. **what historical receipts claimed;**
2. **what historical execution and contracts can actually prove;** and
3. **what current canonical state is verified after recovery.**

Do not collapse those truths into one boolean "standing" field.

A recovery completion record should establish only this exceptional transition:

```text
exact preserved malformed pair
        +
exact approved lossless recipe
        +
exact root authorization
        +
exact executor/package identity
        +
exact verified repaired pair
        =
verified recovery provenance
```

It does not turn the recovery into an admission and does not retroactively repair earlier receipts.

## 6. PEMS/COVE trust-direction synthesis

The final contract should state the trust rule in one sentence:

> PEMS is the only semantic input to repair; COVE may corroborate pair consistency, and the post-recovery COVE is always regenerated from the approved repaired PEMS.

For Mode A, a pre-state COVE mismatch is not a reason to prefer PEMS silently. It is a reason to reject the Mode A eligibility claim and classify the damage as broader than the approved recipe.

## 7. Crash-consistency synthesis

Stage 3 should require a transaction barrier visible to every canonical consumer unless it selects a single-pointer generation design.

For the existing fixed-path design, the minimally sufficient ordering is:

1. verify exact pre-state;
2. preserve exact pre-state and fsync it;
3. materialize and fully validate candidate pair;
4. create PREPARED journal/barrier and fsync file plus parent directory;
5. publish PEMS and fsync;
6. publish COVE and fsync;
7. verify pair content;
8. write and fsync completion record;
9. run recovery-aware storage verification;
10. atomically mark transaction complete/remove active barrier and fsync parent directory.

Every canonical reader must check the barrier before accepting the pair. Recovery after crash is exact roll-forward or exact rollback only.

## 8. Required contract changes before implementation

Stage 3 should not authorize implementation until the final plan identifies exact versioned changes for:

1. new canonical PEMS/COVE recovery contract;
2. explicit R13 exceptional-mutation exception while preserving ordinary-base strictness;
3. recovery-aware R14 provenance/verification semantics;
4. package-owned Mode A recipe contract and semantic-preservation proof;
5. protected-root recovery approval contract and exact confirmation;
6. transaction barrier/journal contract honored by canonical readers;
7. recovery completion-record contract;
8. stable recovery failure classes;
9. optional recovery-semantic reconciliation contract only if the selected mode can require semantic judgment; and
10. conformance tests and incident-specific read-only rehearsal evidence.

R7/R8 should remain unchanged in the Stage 2 recommendation unless Stage 3 records a specific reason to accept the Stage 1 authority expansion instead.

## 9. Unresolved disagreements for Stage 3

Stage 3 must explicitly reconcile these points rather than describing them as consensus:

1. **Authority placement.** Stage 1 recommends a new `canonical_recovery` R7/R8 Steward scope plus root approval. Stage 2 recommends root-bound domain-specific recovery authority without widening R7/R8 for v1.
2. **Mode B timing.** Stage 1 proposes both lossless migration and admission-lineage reconstruction in the same contract family. Stage 2 recommends Mode A only for v1 and a later separately reviewed Mode B if necessary.
3. **Recovered R14 standing.** Stage 1 leaves open whether recovery evidence becomes a direct R14 input or a sibling verifier. Stage 2 requires a normative recovered-state verification path that preserves provenance class; the exact versioning mechanism remains for Stage 3.
4. **Crash mechanism.** Stage 1 proposes journaled pair replacement. Stage 2 accepts that only if every canonical reader is governed by a durable transaction barrier; otherwise use a single atomic generation pointer.
5. **Semantic-reconciliation reuse.** Stage 1 proposes a separate semantic-reconciliation artifact when historical semantic judgment is needed. Stage 2 agrees with the authority class but requires an explicit new recovery-semantic artifact contract rather than assuming candidate-focused R12 already applies.

## 10. Residual risks after required revisions

Even with the revisions above, these risks remain:

- a supposedly lossless migration recipe may accidentally encode semantic policy;
- recovery-aware R14 can become an alternate admission path if its provenance requirements are too weak;
- a transaction barrier can be bypassed by an unmodified or out-of-package canonical reader;
- historical receipt inconsistencies may reveal additional implementation defects beyond the missing discriminator;
- a generic recovery primitive can become a broad repair escape hatch if eligibility classes are not closed and recipe-specific;
- later Mode B design may face irreducible historical execution ambiguity; and
- recovery success may be mistaken by downstream coordination as permission to resume P3 without its own fresh decision.

All of these should remain fail-closed.

## 11. Required implementation sequence after Stage 3, if accepted

This is synthesis for Stage 3, not present implementation authorization.

1. **G0 - Contract freeze:** freeze recovery proposal/result, root approval, completion record, recovered R14 semantics, transaction barrier, outcomes, and explicit R13 exception. Do not add Mode B.
2. **G1 - Mode A recipe framework:** implement package-owned exact-input recipes and semantic-equivalence projections.
3. **G2 - Read-only planner:** fingerprint exact malformed pair, verify COVE witness behavior, choose one exact eligible recipe, and emit candidate plus proof with no mutation.
4. **G3 - Recovered provenance verifier:** validate the exact chain from preserved malformed state through approval and completion record to repaired pair.
5. **G4 - Protected-root recovery ceremony:** bind one exact proposal/executable closure/generation to explicit human confirmation. No R7/R8 scope change under the Stage 2 recommendation.
6. **G5 - Transaction barrier and executor:** implement prestate preservation, apply-time revalidation, durable barrier, pair publication, exact rollback/roll-forward, and completion record.
7. **G6 - R13/R14 integration:** enforce ordinary R13 strictness plus the explicit exceptional mutation exclusion, and make R14 verify recovered provenance without manufacturing admission.
8. **G7 - Adversarial conformance:** inject stale state, altered recipes, authority mismatch, COVE mismatch, semantic drift, every crash boundary, concurrent readers, retry conflicts, and indeterminate rollback.
9. **G8 - Exact incident rehearsal:** run read-only against immutable copies of blobs `bb7c474e935243b45ff02a5778a94bbcdc654d72` and `7ff52fb925a667c4cc1782da9b475dff831e45ef`; require one exact candidate pair and complete lossless proof.
10. **G9 - Independent implementation review:** independently review exact candidate implementation and candidate-bound evidence before any real recovery ceremony.
11. **G10 - Governed recovery operation:** separate activation/invocation with exact protected-root approval. This gate is not authorized by Stage 2.
12. **G11 - Post-recovery handoff:** record durable recovered-state verification and stop. P3 receives a separate bounded handoff and independently decides whether to continue.

If G8 cannot prove Mode A, stop. Do not silently begin Mode B.

## 12. Stage 2 definition of done for a Stage 3 final plan

A Stage 3 plan is implementation-ready only if it makes all of these determinate:

- the exact exceptional authority model and why it is the smallest sufficient change;
- the explicit R13 mutation exception;
- the recovered R14 provenance and success semantics;
- the closed Mode A eligibility predicate;
- the exact semantic-equivalence proof;
- PEMS-first and COVE-witness-only trust direction;
- the package/executable identity bound to approval;
- the transaction barrier honored by all canonical readers;
- durable crash recovery ordering;
- receipt classification semantics that do not manufacture historical conformance;
- stable CR gates with no circular receipt dependency;
- adversarial conformance cases;
- the exact incident rehearsal requirement; and
- the terminal boundary before real recovery and before P3.

## 13. Stage 2 terminal boundary

Disposition: **`CANONICAL_PEMS_COVE_RECOVERY_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`**.

This review accepts the necessity of a separate governed exceptional canonical PEMS/COVE recovery mechanism but requires the authority, mutation, recovered-standing, historical-provenance, crash-consistency, reconstruction-scope, and verification revisions above before implementation.

No Stage 1 bytes were edited. No recovery was performed. No Canon, admission, authority, activation, or P3 state was mutated by this review.

The next consequential work belongs to a fresh Project Engineering Steward activation scoped only to Stage 3 reconciliation under `docs/governance/PROPOSAL_REVIEW_METHOD.md`. The Steward must independently establish whatever current repository authorization and accepted activation evidence the live contracts require before issuing any project-scoped reconciliation. Stage 3 should reconcile the complete Stage 1 proposal and this complete Stage 2 review, produce a separate final plan, and stop before implementation or recovery.