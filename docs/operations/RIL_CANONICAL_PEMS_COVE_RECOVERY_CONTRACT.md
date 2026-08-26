# RIL Canonical PEMS/COVE Recovery Contract

Status: **Normative Mode A V1 contract**

Governing reconciliation: `CANONICAL_PEMS_COVE_RECOVERY_STAGE3_RECONCILED_ACCEPTED_MODE_A_V1`

Governing plan: `docs/proposals/canonical-pems-cove-recovery/03-steward-final-plan.md` at commit `c7445be11460a1c20c6b7c98bf39684a1bf41197`.

Contracts:

- `reasoning-distiller-canonical-recovery-plan/1`
- `reasoning-distiller-canonical-recovery-root-approval/1`
- `reasoning-distiller-canonical-recovery-barrier/1`
- `reasoning-distiller-canonical-recovery-completion/1`
- `reasoning-distiller-canonical-recovery-result/1`

## Purpose and authority boundary

This contract defines the sole exceptional V1 mutation path for an already-invalid canonical PEMS/COVE pair. It is separate from ordinary admission, semantic reconciliation, ordinary repair, RIL administrative exceptional recovery, authority administration, and P3.

V1 is **Mode A only**. It performs only a mechanically proven representation-only migration. It does not reconstruct admission lineage, does not add a `canonical_recovery` R7/R8 Steward scope, does not create Steward authority, and does not infer execution authority from a role, chat, branch, repository ownership, activation, or prior success.

Execution authority is one exact protected-root approval over one immutable recovery-plan digest. The deterministic planner and executor confer no authority. No implementation gate, rehearsal, test result, or completion of this contract authorizes a real recovery operation.

Mode B is unsupported in V1. Any case that cannot satisfy the closed Mode A predicate terminates with `UNSUPPORTED_CANONICAL_DAMAGE`. A future Mode B requires a new proposal, independent review/synthesis, and Steward reconciliation.

## Fixed canonical paths and recovery namespace

Canonical paths remain:

```text
project-knowledge/canonical/pems2.jcs.json
project-knowledge/canonical/cove1.jcs.json
```

Recovery state lives beneath:

```text
project-knowledge/recovery/canonical-pems-cove/
```

The durable active barrier is:

```text
project-knowledge/recovery/canonical-pems-cove/active.json
```

Each recovery generation owns an immutable directory:

```text
project-knowledge/recovery/canonical-pems-cove/generations/<generation>/
```

The generation directory SHALL preserve the exact malformed PEMS bytes, exact paired COVE bytes, an evidence inventory/manifest, the immutable recovery plan, root approval, equivalence proof, in-progress journal, and immutable completion record as applicable. Existing ordinary admission plans, receipts, activation evidence, reconciliation dispositions, and candidates remain byte-immutable.

## Artifact encoding and digest rules

All recovery control artifacts are UTF-8 JSON objects. Any artifact declared canonical by this contract uses the repository's deterministic compact sorted-key JSON representation without a trailing LF. SHA-256 digests bind the exact canonical bytes of the named artifact unless a field explicitly binds raw preserved bytes.

Artifact paths, files, directories, and canonical targets used by the recovery implementation MUST satisfy the repository's ordinary-path and non-symlink safety rules. An unsafe, malformed, ambiguous, or conflicting recovery artifact fails closed.

## `reasoning-distiller-canonical-recovery-plan/1`

The planner is read-only. It SHALL emit one canonical plan object. The object SHALL contain, directly or through digest-bound subobjects, all of these consequential bindings:

- `contract`: exactly `reasoning-distiller-canonical-recovery-plan/1`;
- project identity;
- recovery `generation`;
- exact canonical PEMS and COVE paths;
- exact prestate PEMS/COVE SHA-256 values and available Git blob identities;
- exact preserved-evidence inventory digest;
- `mode`: exactly `A`;
- `recipe_id`: exactly `missing_top_level_semantic_pems2/1` for V1;
- exact recipe implementation identity;
- exact candidate PEMS/COVE SHA-256 values;
- equivalence-proof digest;
- exact PEMS schema, validator, serializer, COVE codec, planner, canonical-store, recovery-executor, and behavior-bearing dependency closure identities;
- runtime identity wherever behavior can vary by runtime;
- this recovery-contract identity and the R14 V2 contract identity;
- expected barrier identity;
- expected terminal provenance class: exactly `VERIFIED_RECOVERED`.

The plan digest is the single authority-binding digest. Repeated high-value hashes in an approval are informational only unless they are checked for exact consistency with the approved plan.

## `reasoning-distiller-canonical-recovery-root-approval/1`

Root approval SHALL be a canonical immutable object containing:

- `contract`: exactly `reasoning-distiller-canonical-recovery-root-approval/1`;
- exact project identity;
- exact recovery generation;
- exact recovery-plan SHA-256;
- exact protected-root identity under the live root contract;
- authentication method `human_confirmation`;
- confirmation `AUTHORIZE_CANONICAL_PEMS_COVE_RECOVERY`;
- approval evidence sufficient for the live protected-root contract.

At apply time the implementation MUST re-establish the live protected-root identity and validate this exact approval binding. Delegated Steward authority, R7/R8 activation, repository ownership, or a prior approval for another generation is insufficient. Approval replay against another plan, generation, prestate, candidate, or executor closure fails closed.

## Closed Mode A recipe registry

V1 contains exactly one recipe family:

```text
missing_top_level_semantic_pems2/1
```

Let `S_raw` be the exact approved prestate PEMS bytes, `S` the strict UTF-8 JSON object parsed from those bytes, and `T` the repaired object. Eligibility requires all of the following:

1. `S_raw` SHA-256 and any bound Git blob identity exactly match the plan.
2. `S` is a JSON object with no top-level `semantic` key.
3. No alternate or conflicting semantic/profile discriminator exists.
4. `S` has the expected project identity, `records`, and `relations` structure.
5. `T` is produced only by deep-copying `S` and inserting top-level `"semantic":"pems/2"`.
6. Removing only that top-level member from `T` yields an object deeply equal to `S`, preserving array order and every nested value.
7. Current package PEMS normalization of `T` changes no semantic graph element, record/relation sequence, or nested value beyond deterministic object-key serialization.
8. `T` validates under the exact plan-bound current PEMS/2 schema.
9. `T` passes the exact plan-bound package PEMS semantic/integrity validator, including project identity, provenance, relation endpoints, derived premises, and contradiction ordering.
10. Prestate COVE parses and decodes exactly to `S`.
11. Candidate PEMS bytes are the exact approved normalized/JCS bytes for `T`.
12. Candidate COVE is generated only from `T` using the exact approved `cove/1 | pems/2 | jcs/1` implementation.
13. Candidate COVE decodes exactly to `T` and reserialization reproduces candidate PEMS bytes exactly.
14. Repeated candidate PEMS/COVE generation is byte-identical.
15. The equivalence proof records every predicate result and the exact schema/validator/serializer/codec identities.

Any extra data edit, inferred field, dropped field, reordered semantic item, semantic repair, reconstructed receipt contribution, or judgment call is outside V1 and returns `UNSUPPORTED_CANONICAL_DAMAGE`.

PEMS is the semantic source of the repaired pair. Prestate COVE is only a consistency witness. Poststate COVE is regenerated from repaired PEMS only.

## `reasoning-distiller-canonical-recovery-barrier/1`

`active.json` SHALL be a canonical object containing:

- `contract`: exactly `reasoning-distiller-canonical-recovery-barrier/1`;
- exact project identity;
- exact generation;
- exact recovery-plan digest;
- exact prestate PEMS/COVE paths and SHA-256 values;
- exact intended poststate PEMS/COVE SHA-256 values;
- transaction state from the closed implementation state machine;
- exact generation-journal path and digest binding required for the current state.

Any existence of `active.json` blocks normal canonical consumption and ordinary canonical mutation. A symlink, non-regular file, malformed object, unknown contract, unexpected transaction state, or digest inconsistency at the barrier path is `CANONICAL_RECOVERY_BARRIER_INVALID`, never equivalent to no barrier.

A crash may release the process lock but does not clear the durable barrier.

## Locking and canonical-reader rule

All supported package canonical I/O SHALL use one shared canonical-store synchronization boundary.

- normal readers acquire a shared lock before barrier inspection and hold it through both canonical reads and snapshot hash establishment;
- R13 mutation acquires an exclusive lock from current-base read through canonical publication and receipt commit;
- recovery acquires an exclusive lock before apply-time prestate revalidation and holds it through completion or verified rollback;
- inability to obtain the required lock fails closed rather than permitting an unguarded pair read.

The lock substrate SHALL NOT require a read-only verifier to create a lock file. Every package production/runtime reader of the fixed canonical paths must use the canonical-store boundary. External programs that bypass package APIs are unsupported concurrent consumers.

## Preservation, publication, and rollback

Before any canonical publication, recovery SHALL durably preserve the exact malformed pair and required evidence and bind that inventory into the approved plan.

While holding the exclusive canonical lock, apply SHALL follow this ordering class:

1. revalidate live protected-root authority and exact approval;
2. re-read Canon and prove exact approved prestate;
3. preserve and fsync exact prestate bytes and immutable evidence;
4. materialize candidate PEMS/COVE in same-filesystem temporary files and finish prepublication checks;
5. create and fsync the per-generation in-progress journal;
6. create and fsync `active.json`, then fsync its parent directory;
7. publish PEMS using file fsync, atomic replace, and canonical-directory fsync;
8. publish COVE using file fsync, atomic replace, and canonical-directory fsync;
9. verify the complete pair content without ordinary-receipt circularity;
10. write and fsync the immutable completion record and generation directory;
11. obtain R14 V2 `PASS/VERIFIED_RECOVERED` against that exact completion record;
12. clear or atomically complete the barrier only after that recovered PASS and fsync the barrier parent;
13. release the exclusive lock.

If safe exact rollback is possible, rollback restores both exact raw prestate byte sequences and verifies their hashes before the barrier may be cleared. A rollback hash mismatch, incomplete or conflicting transaction, or state whose exact classification cannot be proven leaves an indeterminate barrier and fails closed.

## `reasoning-distiller-canonical-recovery-completion/1`

A successful generation SHALL contain one immutable canonical completion object that binds:

- `contract`: exactly `reasoning-distiller-canonical-recovery-completion/1`;
- exact project identity and generation;
- exact recovery-plan digest;
- exact root-approval path and digest;
- exact preserved-evidence inventory path and digest;
- exact equivalence-proof path and digest;
- exact prestate PEMS/COVE SHA-256 values and available Git blob identities;
- exact poststate PEMS/COVE SHA-256 values;
- exact recipe and executable/dependency closure identities from the plan;
- exact recovery contract and R14 V2 identities;
- terminal provenance class exactly `VERIFIED_RECOVERED`;
- the completed transaction/journal identity needed to prove publication reached the exact poststate.

The completion object is recovery-native provenance. It is never an ordinary admission receipt and does not retroactively validate, rewrite, or relabel historical receipts.

## R14 V2 provenance model

`reasoning-distiller-storage-verification-result/2` has exactly two positive provenance classes:

- `PASS/VERIFIED_ADMITTED`, backed by an exact ordinary `reasoning-distiller-admission-receipt/1` matching the current pair;
- `PASS/VERIFIED_RECOVERED`, backed by an exact immutable `reasoning-distiller-canonical-recovery-completion/1` matching the current pair and complete recovery provenance chain.

Both positive classes require identical current PEMS/2 schema, semantic/integrity, normalization, canonical-byte, COVE exactness, and COVE round-trip checks. Only the provenance proof differs.

R14 V2 SHALL report `provenance_class` plus exact provenance artifact path(s) and digest(s). A recovered completion is never accepted as an admission receipt. Downstream consumers may accept `VERIFIED_RECOVERED` only when their governing contract explicitly permits it.

## `reasoning-distiller-canonical-recovery-result/1`

Every planner/apply/retry terminal result SHALL identify:

- `contract`: exactly `reasoning-distiller-canonical-recovery-result/1`;
- `status`: `PASS` or `FAIL`;
- stable `outcome`;
- project identity;
- generation when one is bound;
- recovery-plan digest when one is bound;
- exact current or terminal pair hashes when safely established;
- completion path/digest for a completed recovery.

A completed apply returns `PASS` with outcome `RECOVERED`. An exact already-completed retry returns `PASS/NO_CHANGE` only when plan, approval, poststate, and completion evidence are identical. All other terminal conditions use the stable outcome vocabulary below.

## Stable V1 outcome vocabulary

V1 freezes these outcomes:

```text
RECOVERED
RECOVERY_NOT_REQUIRED
UNSUPPORTED_CANONICAL_DAMAGE
CANONICAL_PRESTATE_MISMATCH
ROOT_RECOVERY_APPROVAL_REQUIRED
ROOT_RECOVERY_APPROVAL_MISMATCH
RECOVERY_PLAN_MISMATCH
MIGRATION_RECIPE_MISMATCH
EXECUTOR_CLOSURE_MISMATCH
PEMS_RECOVERY_INVALID
COVE_PRESTATE_MISMATCH
COVE_RECOVERY_MISMATCH
CANONICAL_RECOVERY_BUSY
CANONICAL_RECOVERY_ACTIVE
CANONICAL_RECOVERY_BARRIER_INVALID
RECOVERY_PUBLICATION_FAILED_ROLLED_BACK
CANONICAL_RECOVERY_INDETERMINATE
RECOVERY_CONFLICT
NO_CHANGE
```

V1 SHALL NOT define `RECOVERY_SCOPE_UNASSIGNED`, `RECOVERY_ROLE_UNAVAILABLE`, or `RECOVERY_ACTIVATION_INVALID`, because V1 adds no R7/R8 recovery scope.

## Idempotence and retry

Exact retry is idempotent. `NO_CHANGE` is allowed only when the identical generation, recovery plan, root approval, poststate pair, and immutable completion evidence all verify exactly. The same generation with a different plan, approval, candidate/poststate, or completion evidence is `RECOVERY_CONFLICT`.

An active or indeterminate transaction may be resumed or rolled back only when the exact durable barrier, journal, preserved evidence, plan, approval, and observed filesystem state mechanically identify one safe action. Ambiguity fails closed.

## Frozen CR0-CR13 gates

| Gate | Requirement |
|---|---|
| CR0 | This normative contract/R13 amendment/R14 V2 contract freeze is present and Mode B is unsupported. |
| CR1 | Exact implementation bundle and adversarial conformance suite pass, including reader-inventory enforcement. |
| CR2 | Project identity and malformed pair fingerprints exactly match the plan. |
| CR3 | Ordinary verification proves Canon invalid in the one accepted Mode A class; valid Canon yields `RECOVERY_NOT_REQUIRED`. |
| CR4 | Exact malformed pair and required evidence are durably preserved and digest-bound. |
| CR5 | The closed recipe produces one candidate and a complete equivalence proof. |
| CR6 | Candidate PEMS passes exact current schema, integrity, project identity, and normalization rules. |
| CR7 | Candidate COVE is derived only from candidate PEMS, round-trips exactly, and prestate COVE matched prestate PEMS. |
| CR8 | Protected root directly approves the exact immutable recovery-plan digest, including executor closure and generation. |
| CR9 | No semantic judgment is required. Any required judgment makes Mode A ineligible. |
| CR10 | Apply-time exclusive-lock revalidation repeats CR2-CR9 and establishes the durable active barrier before publication. |
| CR11 | Durable pair publication and complete poststate content verification succeed without ordinary-receipt circularity. |
| CR12 | Immutable recovery completion matches the exact observed poststate. |
| CR13 | R14 V2 returns `PASS/VERIFIED_RECOVERED`, after which the barrier may be safely cleared. |

P3 is outside CR0-CR13. Recovery completion neither selects, authorizes, nor resumes P3.

## R13 relationship

R13 remains the sole ordinary admission mutation primitive. This contract is the sole named exceptional canonical-pair mutation path. Invalid Canon is never an R13 base. After a recovery transaction is complete, the barrier is absent, and R14 V2 verifies `VERIFIED_RECOVERED`, R13 may use that valid current pair as an ordinary admission base, subject to independent valid admission activation and all ordinary R13 guards.

No admission receipt/result contract is redefined as recovery evidence.

## Forbidden behavior

V1 recovery MUST NOT:

- enter recovery for valid canonical state;
- implement or fall back to Mode B;
- perform semantic judgment or semantic reconciliation;
- create, rewrite, relabel, or fabricate an ordinary admission receipt;
- create or mutate R7/R8 Steward authorization or activation state;
- use COVE as semantic authority;
- derive repaired content from historical receipt replay;
- mutate ordinary historical evidence;
- read or publish an unguarded canonical pair;
- clear a malformed, conflicting, or indeterminate barrier as though no recovery were active;
- authorize the real recovery operation merely because implementation, tests, rehearsal, or review pass;
- begin, authorize, or resume P3.
