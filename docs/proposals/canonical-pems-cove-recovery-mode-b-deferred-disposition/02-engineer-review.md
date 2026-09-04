# Mode B Deferred Semantic Disposition — Stage 2 Engineer Review and Synthesis

Status: **Stage 2 independent review complete; compatible only with required revisions; Stage 3 Steward reconciliation required**

Method: `proposal-review-synthesis/1`

Repository: `loteque/reasoning-distiller`

Operational role: fresh independent Engineer

Coordination control ref: `main`

Coordination revision independently resolved at Stage 2 activation and re-resolved before publication: `a6352fe213a7207bb98b2cd6b1c9eda13d1950bc`

Stage 1 proposal commit: `c2cd579df28764e3e1eae6257ce54e699faec7cd`

Stage 1 artifact: `docs/proposals/canonical-pems-cove-recovery-mode-b-deferred-disposition/01-rpg-engineer-proposal.md`

Live PR #98 separately resolved at review time: open, ready, unmerged, mergeable; head `78cfdbdb7f93ea68f1dee0292dadbe561715ba39`; base `main` at `a6352fe213a7207bb98b2cd6b1c9eda13d1950bc`.

This review is a decision input only. It does not amend the frozen Mode B contract, edit PR #98, establish Steward disposition, implement schemas/runtime, author incident semantic values or a disposition, select B5/B6, create a candidate or plan, or mutate Canon, admission, recovery standing, authority, or protected state.

## 1. Review disposition

The Stage 1 diagnosis is correct: the frozen semantic-disposition `/1` representation cannot durably express the already-defined `DEFER_REPAIR` state for the selected incident without fabricating lifecycle/data values. A versioned unavailable-state representation is therefore justified.

The proposed architecture is **compatible only with required revisions**. The central representation is sound, but five issues must be reconciled before implementation:

1. **Do not silently revise protocol generation 2.** The accepted B0 contract freezes an exact Mode B V2 compatibility matrix. Adding disposition/result `/2`, new namespace behavior, and cross-version dispatch while continuing to call the family protocol generation 2 would change the meaning of a frozen generation after publication. Stage 3 should define a new Mode B protocol generation for chains that consume the new disposition representation, while preserving the complete existing generation-2 matrix unchanged.
2. **Availability evidence must bind at field granularity.** A row-level evidence list is insufficient to prove which evidence supports `lifecycle` availability/unavailability versus `data` availability/unavailability. Each discriminated semantic field state must carry its own immutable evidence references; row rationale may remain shared only as explanatory context.
3. **Rejection cannot require reconstructed repair values by default.** `REJECT_REPAIR` is a terminal negative judgment and may be supportable precisely when one or more repair values are unavailable, contradictory, or unsafe to select. Requiring every value to be available makes rejection impossible in an important pressure case and repeats the structural/semantic conflation that motivated this correction. Stage 3 must define rejection semantics explicitly rather than inherit `/1` completeness.
4. **Cross-version identity and locking must be generation-independent and store-wide.** A disposition identity is project + exact prestate + exact damage analysis, not artifact version. `/1` and the successor representation must share one conflict domain and one atomic lock/transaction boundary. A semantically equivalent artifact encoded under another version is still a different immutable disposition and must conflict unless an explicit migration protocol is separately authorized.
5. **Namespace and scanner behavior must be exact, not optional.** The proposal leaves dedicated versus version-indexed storage open. Stage 3 should select one deterministic layout and require scanners to enumerate every supported disposition generation/version under the same fail-closed conflict check. Otherwise a new directory can become a conflict-evasion channel.

With these amendments, the design cleanly separates epistemic state from PEMS values, preserves complete relation accounting, and keeps semantic disposition candidate-free.

## 2. Governing constraints independently checked

The live B0 contract freezes Mode B as protocol generation V2, freezes semantic disposition/result `/1`, freezes the compatibility matrix and namespaces, requires complete nonempty values for accept/reject/defer, and requires cross-version/cross-generation/mixed-family replay to fail closed. It also states that schema validity is not semantic evidence and that only accepted disposition may later feed a recipe.

The accepted Mode B Stage 3 plan likewise treats the compatibility family as coherent protocol generation V2 and requires every affected relation to be represented exactly once, every inserted value to be evidenced, and missing/rejected/deferred/incomplete disposition to yield zero candidates.

PR #98 is not the architecture authority for this review. It is separately relevant implementation evidence. Its current head contains the hardened `/1` B3 behavior, including fail-closed validation of stored dispositions before identity comparison. The successor design should preserve that property across all supported stores rather than weaken it during version dispatch.

## 3. Versioning synthesis

### 3.1 Artifact version versus protocol generation

Stage 1 correctly rejects mutation of `/1` in place. It does not, however, close the larger generation question.

Protocol generation is the compatibility identity of the whole recovery chain, not merely a plan field. B0 deliberately froze the exact generation-2 matrix before incident semantics. A new semantic-disposition representation changes:

- the accepted disposition contract;
- the disposition-result contract;
- reader/dispatcher behavior;
- immutable storage discovery;
- cross-version conflict rules;
- future repair-proof/plan references and validation obligations.

Those are compatibility semantics, not a local schema patch. Therefore Stage 2 recommends:

- preserve the complete existing Mode B protocol-generation-2 family exactly as frozen;
- introduce the unavailable-capable disposition as part of a **new Mode B protocol generation** selected by Stage 3;
- allow the existing damage-analysis `/1` artifact to be referenced by the new generation only if Stage 3 explicitly declares it generation-neutral input and the successor schemas bind its exact digest/contract;
- define successor disposition/result contract versions explicitly within that new generation;
- require every future repair proof, plan, approval, journal, barrier, completion, recovery result, and R14 verification chain to name and validate the exact generation selected by Stage 3;
- prohibit mixed generation-2/successor chains except for inputs explicitly declared generation-neutral by the reconciled contract.

This costs more schema naming now, but B6-B12 are not implemented, so this is the cheapest point to make the compatibility boundary honest. Reusing the label `protocol_generation:2` while changing its accepted family would turn a frozen generation into a moving target.

### 3.2 Result version

The disposition result should version with the disposition representation. A `/1` result referencing a successor disposition would make the result contract's interpretation depend on an external artifact version and would weaken exact-family closure. Stage 2 therefore agrees with Stage 1 that the result contract must advance together with the disposition contract.

## 4. Availability-state model

The `AVAILABLE(value) | UNAVAILABLE` discrimination is preferable to `null`, sentinel strings, omitted members, or an empty value table. It preserves the distinction between protocol knowledge state and PEMS semantics.

Required refinement: availability is **field-specific**, not merely row-specific. A relation judgment should contain independently discriminated `lifecycle` and `data` fields. Each field state should bind immutable evidence and, for `UNAVAILABLE`, a nonempty rationale explaining why the cited evidence does not establish a value. Conceptually:

```text
relation_judgment
  identity: relation_id, from, to, kind
  lifecycle:
    AVAILABLE(value, evidence[])
    | UNAVAILABLE(evidence[], rationale)
  data:
    AVAILABLE(value, evidence[])
    | UNAVAILABLE(evidence[], rationale)
  rationale: optional/non-authoritative row synthesis
```

The exact JSON shape belongs to Stage 3/D1, not this review. The invariant is that evidence supporting one field cannot silently stand in for another field's epistemic state.

For `depends_on`, `data: AVAILABLE` must contain a complete schema-valid `dependency_kind`; `data: UNAVAILABLE` must contain no semantic data value. For other relation kinds, `AVAILABLE({})` may be structurally possible under the current PEMS data schema, but it still requires evidence that the empty object is the intended complete semantic data. Absence in the damaged source is not such evidence.

Partial objects must not be introduced as a third implicit state. If the complete kind-specific data required by the target PEMS schema is not established, the field is `UNAVAILABLE`. If future schemas need partial knowledge, that is a separate protocol pressure case.

## 5. Evidence granularity and immutability

Stage 1's row-level `evidence` is too coarse for auditability and adversarial validation. The successor contract should require:

- immutable artifact references on each lifecycle state and each data state;
- exact digest/path identity under the repository's artifact-reference contract;
- evidence sufficient to reconstruct why the state is `AVAILABLE` or `UNAVAILABLE`, without treating a rationale as evidence;
- no mutable branch/ref-only citation as semantic support;
- exact evidence ordering or canonical set semantics, whichever Stage 3 freezes;
- field evidence that cannot be swapped between relations or between lifecycle/data without invalidating the artifact.

Closed evidence groups may still be used for compression if the group itself is immutable, names its exact member evidence, and each field references the group by digest. Compression must not erase field-to-evidence attribution.

## 6. Rejection semantics pressure case

Stage 1 intentionally leaves `REJECT_REPAIR` complete-value-only. Stage 2 recommends changing that.

Pressure case: immutable evidence proves that two authoritative historical sources disagree on a relation's lifecycle and no governing evidence selects either value. A Steward may have enough evidence to conclude that this repair attempt must not proceed, while lacking authority/evidence to choose the lifecycle. Requiring a complete lifecycle merely to publish `REJECT_REPAIR` would force fabrication or make the negative judgment unrecordable.

Stage 3 should distinguish outcomes by decision meaning, not by whether all values happen to be known:

- `ACCEPT_REPAIR`: every required semantic field is `AVAILABLE`, and all other acceptance predicates pass.
- `DEFER_REPAIR`: at least one required field may be `UNAVAILABLE`; the judgment intentionally postpones repair pending future evidence or decision.
- `REJECT_REPAIR`: fields may be `AVAILABLE` or `UNAVAILABLE`; immutable evidence and rationale establish an affirmative decision that this repair must not proceed under the bound damage/prestate identity.

Both reject and defer remain terminal, candidate-free results. The difference is governance intent and evidence-supported disposition, not completeness of a hypothetical repair value table. Stage 3 must freeze the exact distinction so rejection cannot become a generic escape hatch for evidence insufficiency.

`SEMANTIC_EVIDENCE_INSUFFICIENT` should remain a pre-publication/application failure when the supplied material cannot support a valid complete accounting and evidence-bound judgment. `SEMANTIC_DISPOSITION_DEFERRED` and `SEMANTIC_DISPOSITION_REJECTED` should require valid published disposition artifacts.

## 7. Namespace and cross-version conflict handling

Stage 2 recommends a version/generation-indexed immutable layout under the existing Mode B root, with an explicit shared conflict domain. Exact path names remain a Stage 3 decision, but the architecture should have these properties:

```text
.../canonical-pems-cove-mode-b/
  dispositions/<generation>/<contract-version>/<digest>.json
  disposition-results/<generation>/<contract-version>/<digest>.json
  disposition.lock
```

The important property is not the spelling. All supported disposition stores must be scanned and validated while holding the same store-wide lock. Before identity comparison, every discovered artifact must pass ordinary-file, filename/digest, UTF-8, duplicate-key, canonical-encoding, exact-version schema, and namespace/version consistency checks. Any malformed supported-store entry fails closed.

Conflict identity remains `(project, prestate, damage_analysis)` across generations and artifact versions. The following are conflicts, not retries:

- `/1` accept versus successor accept with equivalent values;
- `/1` defer versus successor defer;
- successor defer versus successor reject;
- two successor artifacts differing only in evidence, rationale, availability state, activation, or encoding identity.

Identical retry means identical exact artifact bytes in the exact contract family. Cross-version semantic equivalence is not identical retry and must not be inferred.

A later migration/withdrawal/supersession mechanism, if ever desired, needs its own governed artifact. Deleting or ignoring the earlier immutable disposition is not migration.

## 8. Required adversarial coverage

Stage 1's test list is strong but should be extended. D3 must include at least these additional pressure cases:

1. concurrent `/1` and successor submissions for the same identity, proving exactly one immutable disposition can win under the shared lock;
2. two successor contract versions/generations racing for the same identity;
3. a malformed artifact in any supported version/generation namespace blocking publication before identity comparison;
4. namespace/version mismatch, including a valid `/1` artifact placed in a successor directory and vice versa;
5. scanner-evasion attempts using unexpected subdirectories, symlinks, non-ordinary entries, digest-shaped names with wrong content, and unsupported versions;
6. cross-version semantically equivalent artifacts proving they conflict rather than count as retry;
7. field-evidence substitution: lifecycle evidence swapped with data evidence, or evidence from relation A attached to relation B;
8. `UNAVAILABLE` with mutable or missing evidence, empty rationale, or evidence that actually names a semantic value but the artifact suppresses it;
9. `AVAILABLE` whose cited evidence does not bind the asserted value, tested at application validation rather than schema-only validation;
10. reject with unavailable fields and evidence-supported affirmative rejection;
11. defer with unavailable fields and evidence-supported postponement;
12. reject/defer outcome confusion, proving a result cannot relabel one valid artifact as the other;
13. future-consumer downgrade: successor accepted disposition presented to a generation-2 repair-proof/planner must fail before candidate construction;
14. generation-2 `/1` behavior remains byte/behavior unchanged, including current malformed-store and concurrency protections;
15. Mode A remains completely blind to all Mode B successor namespaces and artifacts.

Tests must distinguish schema conformance from evidence sufficiency. A structurally valid `AVAILABLE` assertion with wrong evidence must still fail at application time.

## 9. Synthesized implementation sequence

Subject to Stage 3 reconciliation, Stage 2 recommends this order:

1. **D0 — Steward reconciliation.** Decide the new protocol generation, exact successor disposition/result versions, rejection semantics, evidence granularity, namespace layout, and generation-neutral inputs. No implementation.
2. **D1 — Contract freeze.** Add successor schemas, exact compatibility matrix, stable outcome combinations, namespace rules, generation dispatch, shared conflict identity/lock rules, and future-consumer version bindings. Preserve generation 2 and Mode A byte-for-byte.
3. **D2 — Validator/storage implementation.** Implement strict canonical dispatch, per-field evidence validation, exact damage coverage/order, R8 activation replay, store-wide scanning, cross-generation conflict exclusion, and atomic disposition/result publication. No incident disposition.
4. **D3 — Adversarial conformance.** Run the Stage 1 cases plus the additional cases in this review, including concurrency and downgrade pressure.
5. **D4 — Fresh independent implementation review.** Bind the exact D1-D3 candidate and verify generation-2 and Mode A non-regression.
6. **D5 — Separately governed incident reconsideration.** Only after D4 PASS may a newly and validly activated Steward reconsider whether the incident supports a successor `DEFER_REPAIR` or `REJECT_REPAIR` disposition. This does not select candidate construction.

## 10. Findings classification

### Blockers for Stage 3 approval without amendment

- Reusing protocol generation 2 for a changed accepted disposition/result family would violate the frozen compatibility identity.
- Row-level evidence alone does not establish field-specific availability/unavailability.
- Leaving cross-version namespace/scanning behavior optional permits conflict-domain ambiguity.

### Required amendments

- Advance the Mode B protocol generation for chains consuming the unavailable-capable disposition.
- Advance disposition and disposition-result contracts together.
- Bind immutable evidence to each lifecycle/data availability state.
- Permit evidence-supported rejection without requiring fabricated complete repair values, while defining reject versus defer precisely.
- Freeze one namespace layout and one generation-independent conflict identity with a shared atomic lock.
- Extend adversarial coverage as specified above.

### Recommendations

- Treat damage analysis `/1` as reusable generation-neutral evidence only if Stage 3 explicitly freezes that property.
- Prefer field-level evidence-group references over duplicated large evidence arrays when a canonical immutable group preserves attribution.
- Keep partial semantic objects out of this correction; use only complete `AVAILABLE` or value-free `UNAVAILABLE` states.

### Optional improvements

- Add explicit machine-readable reason codes for `UNAVAILABLE` only if Stage 3 can define a small closed vocabulary without pretending those codes are evidence. Free-form rationale remains explanatory.

## 11. Stage 2 recommendation to the Steward

**Accept the Stage 1 problem diagnosis and core availability-state architecture, but require the amendments in this review.** In particular, do not amend the meaning of protocol generation 2. Establish a successor Mode B generation whose disposition/result contracts can represent field-level epistemic availability, whose reject/defer semantics are explicit, and whose storage conflict domain spans all supported generations atomically.

The existing `/1` contract and PR #98 remain evidence and compatibility baselines. They are not to be rewritten by this review.

## 12. Terminal boundary and handoff

Stage 2 is complete when this separate immutable review artifact is published and identified by exact commit/blob. This review stops before Stage 3 reconciliation, contract changes, implementation, B5, B6, incident disposition, candidate generation, or protected-state changes.

Required receiving role: **Project Engineering Steward**, in a fresh isolated activation for Stage 3 reconciliation under `proposal-review-synthesis/1`.

The Steward must independently resolve live `main`, read the current Steward directive and chat-transition amendment, inspect the exact Stage 1 proposal and this exact Stage 2 artifact, separately resolve PR #98, reconcile the disagreements explicitly, and publish a separate final plan. The handoff creates no Steward authority, activation evidence, approval, or successor implementation selection.