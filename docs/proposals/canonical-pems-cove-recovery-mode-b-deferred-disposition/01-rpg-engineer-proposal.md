# Mode B Deferred Semantic Disposition — Stage 1 RPG Engineer Proposal

Status: **Stage 1 independent proposal complete; fresh independent Engineer review required**

Method: `proposal-review-synthesis/1`

Repository: `loteque/reasoning-distiller`

Operational role: RPG Engineer

Coordination control ref: `main`

Coordination revision: `a6352fe213a7207bb98b2cd6b1c9eda13d1950bc`

Inspected Mode B B2/B3 candidate: `78cfdbdb7f93ea68f1dee0292dadbe561715ba39`

Candidate tree: `4f3f4e4cde99e758035a7b3402892e645ed08cd9`

Candidate PR at inspection: #98, open, ready, unmerged, mergeable

## 1. Evidence and governing inputs

The proposal is bound to these exact inputs:

| Input | Revision | Git blob |
|---|---|---|
| `agents/engineer/DIRECTIVE.md` | coordination revision | `93d2397c1a94c15307af4754c19f56bc2e16a0a9` |
| `docs/operations/PROJECT_CHAT_TRANSITION_AMENDMENT.md` | coordination revision | `231158be0f93fcf67b603911261c94c289a7599d` |
| `docs/governance/PROPOSAL_REVIEW_METHOD.md` | coordination revision | `1463c056c6cd7409b2c5f4a7925028de3658fdb6` |
| `docs/operations/RIL_CANONICAL_PEMS_COVE_RECOVERY_MODE_B_CONTRACT.md` | coordination revision | `4634e6868448b4eaf20ebdb5a24350201da2a3a9` |
| `docs/proposals/canonical-pems-cove-recovery-mode-b/03-steward-final-plan.md` | coordination revision | `e8976adfa83cee4edad1439b85898f72af02d915` |
| `schemas/canonical-recovery-semantic-disposition.schema.json` | B2/B3 candidate | `9b8f16aa601948e5b4e696ebd0b02843ca64740d` |
| `schemas/canonical-recovery-semantic-disposition-result.schema.json` | B2/B3 candidate | `c0d7f44258247e0a738e9eeaa18432c72a3c1556` |
| `runtime/ril_canonical_recovery_mode_b_disposition.py` | B2/B3 candidate | `2cc94dd64b73e8a5baa00491ab9543f4a6dbf4ef` |

The completed B5 activation supplied no disposition artifact and no semantic values. Its incident evidence reports 668 affected relations; lifecycle and `data` unavailable for all 668; and `dependency_kind` unavailable for all seven `depends_on` relations. This proposal treats that report as the selected problem statement, not as authority to invent or publish incident values.

## 2. Problem and decision requested

The frozen `/1` contract defines `SEMANTIC_EVIDENCE_INSUFFICIENT`, `DEFER_REPAIR`, and zero-candidate terminal behavior. It simultaneously requires every outcome, including `DEFER_REPAIR`, to contain a complete nonempty value table in which every affected relation has a schema-valid lifecycle and complete kind-specific data. Therefore the protocol cannot durably encode the exact insufficiency state it defines unless the Steward fabricates the missing semantics.

Structural validation and semantic sufficiency are distinct. A structurally valid deferral must be able to prove complete affected-relation accounting while explicitly recording which semantic fields are unavailable. It must not masquerade absence as a valid PEMS semantic value.

The requested decision is whether to add a versioned disposition representation that can durably encode that distinction without weakening accepted-repair requirements or any recovery authority boundary.

## 3. Recommendation

Introduce a new semantic-disposition artifact version rather than changing the meaning of the frozen `/1` bytes:

- `reasoning-distiller-canonical-recovery-semantic-disposition/2`;
- `reasoning-distiller-canonical-recovery-semantic-disposition-result/2`;
- a revised compatibility-matrix entry and distinct version-aware storage/reader rules.

Version `/2` replaces the ambiguous `values` table with a complete ordered `relation_judgments` table. Every affected relation still appears exactly once and in damage-analysis order. Each row always binds its relation identity, endpoints, kind, immutable evidence, and rationale. Semantic fields are represented as a closed discriminated state:

```text
relation judgment
  identity: relation_id, from, to, kind
  lifecycle: AVAILABLE(value) | UNAVAILABLE
  data: AVAILABLE(value) | UNAVAILABLE
  evidence: one or more immutable artifact references
  rationale: nonempty explanation
```

For `depends_on`, `data: AVAILABLE` must contain a schema-valid `dependency_kind`. `data: UNAVAILABLE` records that the complete kind-specific data is unavailable and therefore carries no `dependency_kind` value. Other relation kinds must neither carry nor imply `dependency_kind`. The final schema should use `oneOf`-style closed variants so `UNAVAILABLE` cannot contain a value and `AVAILABLE` cannot omit one.

Outcome constraints are normative and validated both structurally where possible and against the bound damage analysis at application time:

| Outcome | Permitted row states | Result | Candidate count |
|---|---|---|---|
| `ACCEPT_REPAIR` | every lifecycle and data state is `AVAILABLE` | `PASS/ACCEPT_REPAIR` | 0 |
| `DEFER_REPAIR` | at least one required semantic field is `UNAVAILABLE`; other fields may be supported and available | `FAIL/SEMANTIC_DISPOSITION_DEFERRED` or the existing stable insufficiency outcome as reconciled below | 0 |
| `REJECT_REPAIR` | retain the current complete-value requirement pending explicit Stage 2/Stage 3 disposition | `FAIL/SEMANTIC_DISPOSITION_REJECTED` | 0 |

This proposal does **not** broaden `REJECT_REPAIR`. A rejection may have policy reasons that do not require reconstruction of repair values, but that is a separate semantic decision. Stage 2 should test whether symmetry is necessary; absent a demonstrated pressure case and Steward acceptance, `/2` rejection rows remain fully available. This keeps the correction limited to the observed deferral contradiction.

## 4. Outcome reconciliation

The frozen vocabulary contains both `SEMANTIC_EVIDENCE_INSUFFICIENT` and `SEMANTIC_DISPOSITION_DEFERRED`, but the implemented B3 result currently uses the latter for a published defer artifact. Preserve both meanings:

- `SEMANTIC_EVIDENCE_INSUFFICIENT`: no structurally valid disposition can be published, or supplied evidence cannot support even a complete accounting/rationale binding;
- `SEMANTIC_DISPOSITION_DEFERRED`: a valid `/2` disposition durably accounts for every affected relation and explicitly records one or more unavailable semantic fields.

Thus the present incident, if later reconsidered under a valid activation, can produce a durable `/2` `DEFER_REPAIR` artifact and `SEMANTIC_DISPOSITION_DEFERRED` result without supplying semantic values. This proposal does not perform that act.

## 5. Invariants and boundaries

The correction must preserve all of the following:

1. Damage analysis remains structural, complete, deterministic, read-only, and candidate-free.
2. Semantic unavailability is not a PEMS lifecycle, relation-data value, or `dependency_kind`.
3. Every affected relation is accounted for exactly once and in canonical damage-analysis order for every disposition outcome.
4. Every availability assertion, unavailability assertion, row rationale, and overall uncertainty treatment is bound to immutable evidence.
5. Only `ACCEPT_REPAIR` with every required field `AVAILABLE` can be consumed by a recipe.
6. Deferral, rejection, insufficiency, absence, mismatch, invalidity, or conflict produces zero candidates.
7. Canonical compact sorted-key UTF-8 JSON without trailing LF and digest-addressed immutable publication remain mandatory.
8. Identical retry remains no-change; any different disposition for the same project/prestate/damage-analysis identity fails closed across `/1` and `/2`.
9. Malformed, noncanonical, duplicate-key, misnamed, digest-mismatched, unknown-version, or mixed-version stored artifacts fail closed before identity comparison.
10. R8 `semantic_reconciliation` activation is replayed exactly. No R7/R8 scope or authority assignment changes.
11. R12 remains submission-specific and unchanged.
12. Disposition remains unable to construct candidates, proofs, plans, approvals, completions, or recovery results.
13. Canon, admission, recovery standing, role registry, authorization histories, and protected state remain unchanged.
14. Mode A contracts, readers, paths, outcomes, and behavior remain byte/behavior compatible.
15. B5 does not authorize B6; only a separately governed accepted disposition can make candidate construction eligible.

## 6. Compatibility, versioning, and migration

Changing `/1` in place is rejected. The B0 contract is already on `main`, and the B3 `/1` implementation has an independently reviewed candidate. Even though no incident disposition was published, silently widening `/1` would make identical contract strings accept different structures and would undermine immutable reader expectations.

The migration is additive and fail-closed:

- preserve the `/1` schema and reader semantics for complete-value artifacts;
- add `/2` schemas and an explicit `/2` entry point or version dispatch that rejects mixed families before deeper validation;
- use a distinct `/2` namespace, or a version-indexed namespace whose scanners validate each file against its declared exact schema;
- enforce the same cross-version disposition identity lock so one analysis/prestate identity cannot acquire conflicting `/1` and `/2` judgments;
- do not rewrite, reinterpret, or auto-upgrade `/1` artifacts;
- permit an explicitly validated `/1` complete-value disposition to remain `/1`; there is no lossless migration from an unavailable `/2` row to `/1`;
- revise future B6/B7 consumers before implementation so their accepted-disposition reference explicitly names the supported contract version;
- retain Mode B protocol generation `2` only if Stage 2 proves that artifact-version negotiation and compatibility closure are sufficient. Otherwise Stage 3 must require a new protocol generation rather than partially mixing families.

Because B6-B12 are not implemented and no B5 disposition exists, the practical migration surface is the B3 candidate, its B0 tests, schemas, compatibility matrix, and future consumers. PR #98 must not be edited by this Stage 1 proposal.

## 7. Dependency direction

```text
immutable B2 damage analysis + evidence inventory
                    |
                    v
      /2 semantic-disposition validator
        | structural envelope and coverage
        | R8 activation replay
        | evidence/rationale bindings
        ` availability-state semantics
                    |
          +---------+----------+
          |                    |
   ACCEPT + all available   any terminal failure
          |                    |
 future recipe eligibility    zero candidates
```

The analyzer does not depend on the disposition representation. The `/2` validator depends on immutable analyzer output. Future recipe/planner code depends only on a validated accepted result and must never interpret unavailable rows as defaults.

## 8. Ordered implementation gates

Each gate is terminal on failure and does not select its successor automatically.

1. **D0 — Contract reconciliation.** Complete Stage 2 independent review and Stage 3 Steward disposition. Decide `/2` versus protocol-generation increment and explicitly decide, without inference, whether rejection may contain unavailable fields.
2. **D1 — Schema and compatibility freeze.** Add `/2` disposition/result schemas, closed availability variants, outcome conditionals, compatibility matrix, stable outcomes, namespaces, and cross-version identity rules. Preserve `/1` and Mode A byte-for-byte.
3. **D2 — Validator implementation.** Add version-aware canonical decoding, full schema validation, exact coverage/order, evidence binding, activation replay, storage validation, cross-version conflict exclusion, and atomic publication. No incident disposition.
4. **D3 — Adversarial conformance.** Prove structural-versus-semantic separation, outcome constraints, canonical storage, concurrency, replay rejection, and zero-candidate closure across `/1` and `/2`.
5. **D4 — Fresh independent implementation review.** Review the exact D1-D3 candidate and Mode A non-regression. Failure returns to a fresh remediation activation.
6. **D5 — Separately selected B5 reconsideration.** Only after D4 PASS, a newly activated Steward may decide whether to publish an incident `/2` deferral. No candidate, plan, or B6 work is included.

## 9. Adversarial acceptance tests

Acceptance must prove at least:

1. A `/2` deferral with all 668 relations in exact order, all incident-unavailable fields marked `UNAVAILABLE`, immutable evidence/rationale bindings, and no semantic values validates and returns zero candidates.
2. Missing, duplicated, reordered, or identity/endpoints/kind-altered rows fail as damage-set mismatch.
3. `ACCEPT_REPAIR` with any `UNAVAILABLE` field fails structurally or semantically before publication.
4. `DEFER_REPAIR` with no unavailable required field fails as invalid rather than becoming a disguised accepted judgment.
5. An `UNAVAILABLE` lifecycle carrying a lifecycle value fails; an `AVAILABLE` lifecycle omitting a value fails.
6. `data: UNAVAILABLE` carrying `dependency_kind`, qualifier, an empty fabricated object, or another value fails.
7. `data: AVAILABLE` for `depends_on` without a valid `dependency_kind` fails; a non-`depends_on` row carrying `dependency_kind` fails.
8. Unknown availability states, unknown members, duplicate JSON keys, noncanonical JSON, trailing bytes, and filename/content-digest mismatch fail closed.
9. Missing or mutable evidence references and empty row/overall rationales fail closed.
10. `/1` examples and behavior remain unchanged; `/1` readers reject `/2`, `/2` readers reject `/1` unless explicit dispatch selected it, and mixed envelopes fail.
11. Conflicting `/1` and `/2` dispositions for one identity are atomically exclusive under concurrency; identical retry of either exact artifact is no-change.
12. Every defer, reject, insufficiency, invalidity, mismatch, and conflict result has `candidate_count: 0` and creates no recipe, proof, plan, approval, or protected-state mutation.
13. Wrong/stale R8 role, scope, invocation, activation artifact, digest, prestate, analysis, or evidence binding fails closed.
14. Mode A focused and full recovery/R14 suites remain byte/behavior compatible and reject Mode B `/2` and mixed-family artifacts.
15. No reader discovers unavailable fields as PEMS values, supplies defaults, or promotes them into a candidate.

## 10. Risks and alternatives

| Option | Disposition | Reason |
|---|---|---|
| Mutate `/1` in place | reject | changes meaning beneath a frozen contract string and reviewed implementation |
| Publish an empty values table | reject | loses complete affected-relation accounting |
| Use `null`, `unknown`, or sentinel strings as lifecycle/data values | reject | conflates protocol epistemic state with PEMS semantics and risks downstream coercion |
| Put unavailable fields only in overall rationale | reject | not machine-checkable per relation and cannot prove complete accounting |
| Treat missing values as rejection | reject for this correction | changes the selected terminal judgment and obscures evidence insufficiency |
| Add unavailable representation to rejection immediately | defer to Stage 2/3 | plausible, but not required by the demonstrated incident and would broaden semantics |
| New disposition `/2` within protocol generation 2 | recommend subject to Stage 2 compatibility proof | narrowest additive correction while B6-B12 are absent |
| Increment the whole Mode B protocol generation | fallback | required if compatibility closure cannot prevent mixed-chain ambiguity |

## 11. Unresolved questions for Stage 2

1. Can disposition `/2` remain inside Mode B protocol generation 2 without ambiguity in every future B6-B12 reference, or must the entire family increment?
2. Should the stable result contract use `/2`, or can `/1` safely express a result referencing a `/2` disposition? This proposal recommends `/2` for explicit closure.
3. Is one evidence set sufficient for multiple unavailable fields on a row, or must each field bind a distinct evidence group? The implementation should prefer field-level bindings if auditability is not prohibitively verbose.
4. Does a demonstrated rejection pressure case justify unavailable fields for `REJECT_REPAIR`, or should rejection remain a complete semantic judgment?
5. Should `/2` use a dedicated namespace or a version-indexed directory? Either must preserve cross-version conflict detection and fail-closed scanning.

## 12. Definition of done and terminal boundary

Stage 1 is complete when this immutable proposal is published and identified by exact commit, tree, and blob. It proposes a coherent unavailable-value representation, keeps complete relation accounting, preserves structural/semantic separation and all authority boundaries, analyzes `/1` compatibility, and defines ordered gates and adversarial proof obligations.

This artifact does not amend the contract, approve architecture, implement schemas/runtime, modify PR #98, author incident values or a B5 disposition, activate B5, begin B6, create candidates/proofs/plans, alter R12, or mutate protected state.

The required next activation is a fresh independent Engineer in an isolated context for Stage 2 review and synthesis of the original problem, constraints, exact governing inputs, and this complete proposal. Stage 2 must challenge versioning closure, unavailable-state modeling, evidence granularity, rejection semantics, conflict identity, and test completeness. It must publish a separate immutable artifact and stop before Stage 3. This handoff does not itself select or authorize Stage 2 unless the governing activation mechanism establishes that successor.
