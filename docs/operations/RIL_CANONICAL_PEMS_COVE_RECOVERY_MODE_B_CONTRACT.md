# RIL Canonical PEMS/COVE Recovery Mode B Contract Freeze

Status: **Normative B0 protocol freeze; implementation and incident semantics absent**

Governing reconciliation: `CANONICAL_PEMS_COVE_RECOVERY_MODE_B_STAGE3_RECONCILED_ARCHITECTURE_ACCEPTED_SEMANTIC_VALUES_BLOCKED`

Governing plan: `docs/proposals/canonical-pems-cove-recovery-mode-b/03-steward-final-plan.md`, original commit `45919508cab9d18a6eab82869514be767edf5c68`.

## Scope and non-authority

This contract freezes the Mode B protocol-generation V2 envelopes, compatibility matrix, stable outcomes, storage namespaces, and Mode A non-regression boundary required by B0. It does not implement B2 or B3, analyze the incident, author lifecycle or dependency values, create a semantic disposition, construct a candidate or plan, approve or execute recovery, mutate Canon or recovery standing, perform admission, change authority state, or continue P3.

The frozen schemas are structural contracts. Schema validity never proves semantic evidence, current R8 activation, protected-root approval, executable closure, current prestate, or recovery authority. Later gates must implement and test those checks independently.

## Protocol family and exact schemas

All Mode B control artifacts are strict UTF-8 JSON objects represented by deterministic compact sorted-key JSON without a trailing LF. Digests are lowercase 64-character SHA-256 hex over the exact named bytes. Unknown object members are rejected.

| Artifact | Contract | Schema |
|---|---|---|
| Damage analysis | `reasoning-distiller-canonical-recovery-damage-analysis/1` | `schemas/canonical-recovery-damage-analysis.schema.json` |
| Semantic disposition | `reasoning-distiller-canonical-recovery-semantic-disposition/1` | `schemas/canonical-recovery-semantic-disposition.schema.json` |
| Disposition result | `reasoning-distiller-canonical-recovery-semantic-disposition-result/1` | `schemas/canonical-recovery-semantic-disposition-result.schema.json` |
| Repair proof | `reasoning-distiller-canonical-recovery-repair-proof/1` | `schemas/canonical-recovery-repair-proof.schema.json` |
| Plan | `reasoning-distiller-canonical-recovery-plan/2`, `mode:B`, `protocol_generation:2` | `schemas/canonical-recovery-plan-v2.schema.json` |
| Root approval | `reasoning-distiller-canonical-recovery-root-approval/2` | `schemas/canonical-recovery-root-approval-v2.schema.json` |
| Journal | `reasoning-distiller-canonical-recovery-journal/2` | `schemas/canonical-recovery-journal-v2.schema.json` |
| Barrier | `reasoning-distiller-canonical-recovery-barrier/2` | `schemas/canonical-recovery-barrier-v2.schema.json` |
| Completion | `reasoning-distiller-canonical-recovery-completion/2` | `schemas/canonical-recovery-completion-v2.schema.json` |
| Recovery result | `reasoning-distiller-canonical-recovery-result/2` | `schemas/canonical-recovery-result-v2.schema.json` |
| Storage verification | `reasoning-distiller-storage-verification-result/3` | `schemas/storage-verification-result-v3.schema.json` |

`schemas/canonical-recovery-mode-b-common.schema.json` contains only shared structural definitions. It is not an artifact contract.

## Compatibility matrix

| Consumer | Accepted family | Required rejection |
|---|---|---|
| Existing Mode A planner, approval validator, executor, barrier reader, completion reader, recovery-result reader, and R14 V2 verifier | exact V1/Mode A contracts only | every Mode B/V2 artifact and every mixed family |
| Future Mode B analyzer | damage analysis `/1` only | candidates, plans, dispositions, or mutation effects |
| Future Mode B disposition primitive | disposition `/1` plus current R8 `semantic_reconciliation` activation | R12 substitution, missing/stale activation, or recovery authorization |
| Future Mode B planner/executor | exact V2 matrix in this contract | V1 coercion, Mode A artifacts, unknown majors, and mixed-generation chains |
| R14 V3 | existing admitted/Mode A recovered chains plus exact Mode B completion `/2` chain | admission reconstruction or implicit downstream opt-in |
| Downstream consumers | only provenance classes explicitly added by their own contract | inherited acceptance of Mode B `VERIFIED_RECOVERED` |

No automatic conversion exists between `/1` and `/2`. Every V2 artifact binds `protocol_generation:2`; every plan-dependent artifact binds the exact plan-v2 digest. Cross-mode, cross-version, cross-generation, cross-candidate, or mixed-family replay fails before publication.

## Frozen namespaces

Mode A paths remain byte- and behavior-unchanged beneath:

```text
project-knowledge/recovery/canonical-pems-cove/
```

Mode B uses disjoint namespaces:

```text
project-knowledge/recovery/canonical-pems-cove-mode-b/
project-knowledge/recovery/canonical-pems-cove-mode-b/damage-analyses/<analysis_sha256>.json
project-knowledge/recovery/canonical-pems-cove-mode-b/semantic-dispositions/<disposition_sha256>.json
project-knowledge/recovery/canonical-pems-cove-mode-b/semantic-disposition-results/<disposition_sha256>.json
project-knowledge/recovery/canonical-pems-cove-mode-b/generations/<generation>/
project-knowledge/recovery/canonical-pems-cove-mode-b/active.json
```

Damage analysis and semantic disposition storage is immutable and content-addressed. Identical retry is no-change. A different artifact at an occupied identity or a conflicting disposition for the same analysis/prestate identity fails closed. B0 creates none of these paths.

## Damage analysis and semantic disposition boundary

Damage analysis `/1` is read-only, prestate-bound, complete, deterministic, and candidate-free. It binds the exact PEMS/COVE paths and byte identities, available Git blobs, schema/validator/normalizer/COVE codec identities, ordered relation-set digest, complete schema-error observations, integrity observations, blocked checks, and immutable evidence inventory.

Semantic disposition `/1` records one project-scoped semantic judgment. It binds the exact project, prestate, analysis, behavior identities, ordered relation set, current R8 activation artifact and digest for requested scope `semantic_reconciliation`, rationale, uncertainty treatment, and a complete ordered value table. Its outcome is exactly `ACCEPT_REPAIR`, `REJECT_REPAIR`, or `DEFER_REPAIR`.

Only `ACCEPT_REPAIR` may be consumed by a later recipe. Reject, defer, insufficiency, absence, structural invalidity, mismatch, or conflicting retry yields zero candidates. The semantic-disposition operation cannot construct a candidate or plan and cannot authorize recovery. R12 contracts and storage remain unchanged.

The value table contains exactly one row per affected relation. Every row binds relation ID, endpoints, kind, lifecycle, complete kind-specific data, evidence references, and rationale. No schema default exists. B0 intentionally contains no incident row and selects no lifecycle or `dependency_kind` value.

## Plan, approval, execution, and provenance boundary

Repair proof `/1` proves only exact closed insertion from a disposition-accepted prestate to one candidate pair. Plan `/2` binds that proof, the accepted disposition, exact prestate/candidate, recipe, closure, contracts, and expected Mode B provenance. It does not create authority.

Root approval `/2` is a separate protected-root act over one exact plan-v2 digest. Its invocation and confirmation are distinct from semantic disposition. Approval cannot add or modify semantic values. Same-principal use may be recorded, but V2 does not enforce a different-human rule.

Barrier, journal, completion, result, and R14 V3 preserve the Mode A lock, preservation, fsync, atomic publication, rollback, retry, and indeterminate-state guarantees. Completion `/2` is recovery-native provenance and never admission provenance. R14 V3 identifies protocol generation, provenance class, completion, disposition, and repair-proof paths/digests.

## Stable Mode B outcomes

The complete B0-frozen Mode B-specific vocabulary is:

```text
SEMANTIC_EVIDENCE_INSUFFICIENT
SEMANTIC_DISPOSITION_REQUIRED
SEMANTIC_DISPOSITION_REJECTED
SEMANTIC_DISPOSITION_DEFERRED
SEMANTIC_DISPOSITION_INVALID
SEMANTIC_DISPOSITION_MISMATCH
SEMANTIC_ACTIVATION_INVALID
MODE_B_DAMAGE_SET_MISMATCH
MODE_B_ADDITIONAL_DAMAGE
MODE_B_RECIPE_MISMATCH
MODE_B_REPAIR_PROOF_INVALID
MODE_B_CANDIDATE_INVALID
MODE_B_PROTOCOL_VERSION_MISMATCH
MODE_B_CROSS_MODE_REPLAY
MODE_B_MULTIPLE_CANDIDATES
```

Recovery result `/2` additionally reuses the applicable V1 execution outcomes named by the Mode A contract: `RECOVERED`, `CANONICAL_PRESTATE_MISMATCH`, `ROOT_RECOVERY_APPROVAL_REQUIRED`, `ROOT_RECOVERY_APPROVAL_MISMATCH`, `RECOVERY_PLAN_MISMATCH`, `EXECUTOR_CLOSURE_MISMATCH`, `PEMS_RECOVERY_INVALID`, `COVE_PRESTATE_MISMATCH`, `COVE_RECOVERY_MISMATCH`, `CANONICAL_RECOVERY_BUSY`, `CANONICAL_RECOVERY_ACTIVE`, `CANONICAL_RECOVERY_BARRIER_INVALID`, `RECOVERY_PUBLICATION_FAILED_ROLLED_BACK`, `CANONICAL_RECOVERY_INDETERMINATE`, `RECOVERY_CONFLICT`, and `NO_CHANGE`.

Evidence insufficiency, rejection, and deferral are semantic outcomes, not canonical-damage classifications. Every prepublication failure leaves Canon, recovery standing, admission, and authority state unchanged.

## Exact Mode A non-regression boundary

1. `docs/operations/RIL_CANONICAL_PEMS_COVE_RECOVERY_CONTRACT.md`, all V1 contract strings, runtime constants, serializers, result vocabularies, paths, readers, validators, planners, approval logic, and executor behavior remain unchanged.
2. Mode A continues to accept only its exact `/1` family and R14 `/2`; it performs no `/2` or Mode B discovery or coercion.
3. The immutable incident pair continues to produce `UNSUPPORTED_CANONICAL_DAMAGE` with zero candidates and no plan under Mode A.
4. B0 adds no runtime reader or writer and creates no recovery, Canon, admission, reconciliation, activation, or authority artifact.
5. Later Mode B implementation must use separate entry points or explicit version dispatch that first rejects mixed families; it must not weaken Mode A checks.

## B0 terminal condition

B0 is complete only when every schema above is meta-schema valid, positive structural examples validate, hostile unknown-field/version/mode/cross-family examples fail, the namespace and outcome sets are machine-checked, and the existing Mode A recovery suites remain unchanged and passing. Completion of B0 does not select B2 or B3.
