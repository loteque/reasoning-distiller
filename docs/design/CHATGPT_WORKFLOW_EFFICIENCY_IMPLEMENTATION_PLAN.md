# ChatGPT Governed Workflow Efficiency — Implementation Plan

Status: **Proposed implementation plan**

Evidence revision: `58b99891e116b5a06dd603810c2b98ea83e328c3`

Operational scope: Knowledge Systems Architect planning for ChatGPT-hosted repository coordination.

Authority posture: this document is a design/implementation-planning artifact only. It does not establish registered role identity, RIL activation, Steward authorization, implementation approval, reconciliation, admission, or canonical project knowledge. A branch, pull request, chat label, or user request does not change those boundaries.

## 1. Objective

Reduce avoidable repository reads, prompt duplication, handoff size, and governance prose while preserving the safety properties already required by:

- `agents/architect/DIRECTIVE.md`;
- `docs/operations/CHATGPT_PROJECT_CONTRACT.md`;
- `docs/operations/CHATGPT_PROJECT_CHAT_TRANSITION_AMENDMENT.md`;
- task-specific governing contracts.

The target operating loop is:

```text
Resolve -> Load -> Work -> Revalidate -> Persist
```

The implementation must make the safe path cheaper than ad hoc repetition. Efficiency gains MUST come from better state tracking, immutable-source reuse, compact coordination metadata, and reusable pressure cases. They MUST NOT come from skipping authority checks, trusting ambient memory, broadening evidence sets, collapsing role boundaries, or hiding repository drift.

## 2. Scope boundary

This plan governs the interactive ChatGPT coordination layer around repository work.

It does not change:

- RGP, PEMS/2, or COVE semantics;
- production `rd-distill` evidence or invocation behavior;
- role registration or role authority;
- RIL activation semantics;
- reconciliation or admission;
- project canonical-memory semantics;
- `docs/governance/PROPOSAL_REVIEW_METHOD.md` stage independence;
- the in-flight deterministic context-packaging Stage 1/Stage 2 design question.

The context-packaging proposal may later inform or supersede parts of this coordination design. Until that review is complete, this work MUST remain outside production evidence preparation and MUST NOT define an alternate context-packaging protocol.

## 3. Problems to remove

### P1 — Re-reading immutable evidence

Once exact bytes at `<commit>:<path>` have been read and their blob identity recorded within the same bounded activation, repeated reads of the same immutable object usually add cost without adding safety.

### P2 — Over-resolving mutable refs

A mutable target such as `main` must be resolved when current state matters, especially before consequential analysis and before/after writes. It does not need to be re-resolved before every adjacent reasoning step when no drift-sensitive operation occurred.

### P3 — Repeating authority prose

The same distinctions between coordination role, registered role, authorization, activation, reconciliation, admission, and canonical knowledge are often restated in long prose. The distinctions must remain explicit, but can be encoded in a compact standard posture block.

### P4 — Oversized handoffs

Independent reviews can be biased by large summaries of the outgoing role's reasoning. Handoffs should preserve identities, problem, constraints, authority posture, unresolved questions, and exact next action while omitting prior conclusions that the receiving role should independently reconstruct.

### P5 — Ad hoc evidence discovery

Task-relevant evidence discovery is repeatedly rebuilt conversationally. The system needs a disciplined rule for following explicit normative dependencies without treating model relevance judgment, semantic search, or remembered files as authority.

### P6 — Pressure cases live only in prose

Pressure cases are useful, but long prose makes them harder to compare, test, and reuse. A compact fixture/matrix form should become the reusable conformance backbone.

## 4. Proposed coordination primitives

### 4.1 Stage manifest

Introduce a compact `reasoning-distiller-chatgpt-stage-manifest/1` coordination record.

The manifest is not authority evidence and is not canonical project knowledge. It is a bounded working record for the current interactive activation.

Minimum fields:

```text
contract
repository
resolved_revision
mutable_target_ref
operational_role
scope
governing_contracts
authority_posture
immutable_evidence
mutable_state_revalidation
permitted_outputs
forbidden_outputs
next_boundary
```

`authority_posture` should use explicit state rather than narrative, for example:

```text
registered_role_identity: unknown
role_authorization: unknown
ril_activation: unknown
steward_authority: not_established
reconciliation: out_of_scope
admission: out_of_scope
```

Rules:

1. The manifest records observations; it does not create them.
2. Unknown remains unknown.
3. A role label may populate `operational_role` but MUST NOT populate authority fields.
4. `resolved_revision` must be an immutable commit for consequential repository-dependent work.
5. The manifest is invalid for completion claims until post-write durable identity is observed where a write occurred.
6. The manifest MUST NOT be inserted into production `rd-distill` evidence merely because it exists.

### 4.2 Immutable evidence ledger

Within the stage manifest, maintain an `immutable_evidence` ledger containing exact evidence identities already read in the current activation:

```text
path
commit
blob_sha
read_status
purpose
```

Reuse rule:

- same commit + same path + same blob SHA + bytes already present in the current activation -> reuse rather than refetch;
- different commit, unresolved ref, missing bytes, incomplete prior read, or task-relevant section not actually loaded -> fetch;
- fresh/isolated receiving activation -> identities may be carried, but required bytes must be independently loaded unless the governing contract explicitly permits supplied frozen evidence.

This is activation-local evidence reuse, not cross-chat memory trust.

### 4.3 Mutable-ref revalidation policy

Default mutable-ref checkpoints:

1. **Resolve** at consequential activation start.
2. **Revalidate** immediately before a consequential repository write when drift could matter.
3. **Observe** the durable result after the write.

Additional resolution is required when:

- the user explicitly asks for current state;
- a tool result indicates drift;
- a dependency is discovered on another mutable ref;
- a governing contract requires a tighter checkpoint.

A mutable branch MUST NOT be treated as unchanged merely because no contradictory chat message appeared.

### 4.4 Explicit dependency-following rule

Do not introduce semantic search, embedding relevance, or hidden model ranking as a deterministic governance mechanism.

For the coordination layer, discovery proceeds from:

1. the explicit user task;
2. the active role directive;
3. the directly governing task contract;
4. explicit normative references named by those live sources;
5. repository-owned state explicitly required by those contracts.

The assistant may recognize that a task needs another contract, but any consequential claim must be grounded by actually reading that source. Remembered filenames are navigation hints only.

Future automation MAY add structured dependency metadata to normative documents, but path presence or dependency listing MUST NOT itself create authority. If structured dependency metadata is introduced, it must be reviewed as coordination metadata and must fail closed on missing required references.

### 4.5 Compact authority posture

Standardize a short human-readable block for ordinary updates and handoffs:

```text
role: <coordination role>
scope: <bounded task>
authority: <none required | unknown | exact governed requirement>
activation: <not required | unknown | exact evidence id>
forbidden: <bounded list>
```

The compact block replaces repeated explanatory paragraphs only when it preserves the same distinctions. If authority state is ambiguous or conflicting, expand the explanation rather than compressing it.

### 4.6 Minimal bounded handoff

Default handoff for a non-independent receiving role:

```text
repository + resolved revision
problem + constraints
outgoing role + completed artifact/result
exact durable identities
governing contracts needed next
authority posture
unresolved questions
receiving role + exact next action
```

For independence-sensitive review, omit outgoing reasoning summaries and recommendations unless the governing review contract requires them. Supply the complete frozen artifact and original problem instead.

A handoff must never imply that the receiving role is activated or authorized.

### 4.7 Pressure-case matrix

Represent reusable coordination pressure cases with columns:

```text
case_id
scenario
input_state
required_reads
expected_behavior
expected_failure_or_boundary
authority_effect
production_evidence_effect
```

The matrix is the source for executable or semi-executable fixtures where practical.

Initial cases MUST include:

1. role label claims Steward authority;
2. prior chat says a change was approved;
3. same immutable contract requested twice in one activation;
4. immutable path identity changes because commit changes;
5. `main` moves before write;
6. target branch does not move before write;
7. post-write commit cannot be observed;
8. fresh independent review receives prior reasoning summary;
9. fresh independent review receives only original problem + frozen artifact;
10. handoff claims accepted activation but provides no governed evidence;
11. missing explicitly referenced governing contract;
12. contradictory authority evidence;
13. uploaded snapshot conflicts with live repository;
14. remembered filename no longer exists;
15. chat-transition prose is about to enter production Distiller evidence;
16. helper proposes a contract but no live read occurred;
17. same-role minor subtask change incorrectly triggers a new-chat recommendation;
18. actual cross-role or independence boundary fails to trigger a handoff;
19. output branch collides with existing different content;
20. main changes after analysis but before persistence.

## 5. Implementation artifacts

Subject to implementation-time repository inspection, the preferred artifact set is:

```text
docs/design/CHATGPT_WORKFLOW_EFFICIENCY_IMPLEMENTATION_PLAN.md
schemas/chatgpt-stage-manifest.schema.json
docs/operations/CHATGPT_WORKFLOW_EFFICIENCY_AMENDMENT.md
docs/testing/CHATGPT_WORKFLOW_EFFICIENCY_PRESSURE_CASES.md
tests/fixtures/chatgpt-workflow-efficiency/
tests/test_chatgpt_stage_manifest.py
tests/test_chatgpt_workflow_efficiency_contract.py
```

Optional helper tooling may be added only after the contract and fixture semantics are stable. Any helper must remain coordination-only and must not become a hidden authority or evidence resolver.

The preferred change strategy is an amendment to the current ChatGPT Project contract rather than silently rewriting its meaning in place. A later consolidation into a new major/minor contract version may occur only after conformance evidence exists.

## 6. Gate sequence

### G0 — Freeze baseline and pressure cases

Before semantic expansion, capture representative coordination scenarios and the initial pressure-case matrix.

Measure at minimum:

- number of repository reads required by the documented workflow;
- duplicate reads of identical immutable evidence;
- mutable-ref resolutions;
- handoff size;
- repeated authority explanation blocks;
- whether role/authority/evidence boundaries were preserved.

The baseline MAY use synthetic fixtures or durable repository-owned examples. Chat history itself is not canonical evidence.

PASS:

- pressure cases cover the known safety failures and efficiency waste;
- metrics can be compared before and after;
- no production or authority semantics have changed.

### G1 — Stage-manifest contract and schema

Define `reasoning-distiller-chatgpt-stage-manifest/1` and its JSON schema.

PASS:

- unknown authority states are representable;
- role label cannot satisfy authority fields;
- immutable evidence records bind commit/path/blob;
- mutable target is distinct from resolved immutable revision;
- permitted/forbidden outputs and next boundary are explicit;
- schema contains no field that can be interpreted as granting authority merely by presence.

### G2 — Immutable-evidence reuse conformance

Add fixtures proving exact immutable evidence can be reused inside one activation without repeated repository reads, while cross-revision and fresh-activation cases still fetch when required.

PASS:

- identical immutable evidence is not redundantly fetched in the same activation;
- changed revision always invalidates reuse unless exact same immutable object is independently proven;
- fresh independent activation does not trust ambient prior-chat bytes;
- incomplete reads are not treated as complete evidence.

### G3 — Mutable-ref checkpoint conformance

Encode the Resolve -> Load -> Work -> Revalidate -> Persist lifecycle in the amendment and fixtures.

PASS:

- consequential work begins with live resolution;
- no unnecessary branch polling occurs during stable same-role work;
- drift-sensitive writes re-resolve immediately before mutation;
- detected drift causes re-evaluation or fail-closed behavior rather than silent write;
- post-write durable identity is observed before completion claim.

### G4 — Compact authority posture

Introduce the standardized posture block and tests/examples for unknown, no-authority-required, and governed-authority-required tasks.

PASS:

- compression never converts unknown to accepted;
- registration, authorization, activation, reconciliation, and admission remain distinguishable;
- expanded explanation is required on conflict/ambiguity;
- role labels remain coordination metadata.

### G5 — Minimal handoff templates

Add normal and independence-sensitive handoff templates.

PASS:

- normal handoff preserves exact artifact/evidence identities and next action;
- independent handoff omits unnecessary outgoing reasoning while preserving the complete frozen proposal/artifact;
- handoff cannot be mistaken for RIL activation or project approval;
- transition reminders remain outside production candidate/evidence bytes.

### G6 — Explicit dependency-following guidance

Document the dependency-following rule and add pressure fixtures for explicit normative references, missing references, stale remembered paths, and task-specific additional evidence.

PASS:

- no semantic search or hidden model ranking is required;
- explicit referenced contracts are actually read before consequential reliance;
- missing required reference fails closed;
- repository path/name alone is never treated as authority;
- no task-profile/catalog mechanism is introduced that would pre-empt the separate deterministic context-packaging design review.

### G7 — Role-directive integration

Only after G1-G6 pass, update interactive role directives as needed to point to the efficiency amendment and stage-manifest discipline.

PASS:

- Architect, Engineer, Steward, and Distiller local boundaries remain unchanged;
- transition responsibility is not broadened into authority;
- production Distiller directive remains free of chat-navigation contamination;
- same-role ordinary continuation does not trigger noisy handoffs.

### G8 — Cross-workflow regression

Run the pressure suite across at least:

- architecture/design task;
- ordinary engineering implementation task;
- independent proposal review;
- Steward-governed operation where activation evidence is required;
- production `rd-distill` preparation boundary.

PASS:

- efficiency rules never weaken a stricter task-specific contract;
- production evidence remains fixed;
- independent review remains isolated;
- authority-sensitive operations still revalidate authority/activation as required;
- no canonical project-memory mutation is introduced.

### G9 — Efficiency acceptance

Compare the G8 workflows to G0 baseline.

Target acceptance:

- zero avoidable duplicate reads of the exact same immutable evidence inside a bounded activation;
- mutable-ref resolution reduced to required checkpoints plus explicit drift-triggered checks;
- routine authority posture expressed in a compact block without semantic loss;
- independence-sensitive handoffs contain no unnecessary outgoing reasoning summary;
- no increase in false authority, stale-state, production-evidence, or role-boundary failures;
- no task-specific contract is bypassed to meet an efficiency target.

The metrics are guardrails, not authority. Safety failures block acceptance regardless of efficiency improvement.

### G10 — Contract consolidation decision

After conformance evidence exists, decide whether to:

1. retain the efficiency amendment beside `reasoning-distiller-chatgpt-project/1`; or
2. issue a reviewed successor ChatGPT Project contract incorporating the proven behavior.

Do not rewrite the existing normative contract merely to make the document set look cleaner before conformance is established.

## 7. Dependency order

```text
G0
 ↓
G1
 ↓
G2 ─┐
G3  │
G4  ├─> G6 -> G7 -> G8 -> G9 -> G10
G5 ─┘
```

G2-G5 may proceed in parallel after G1 because they share the stage-manifest vocabulary but exercise different semantics.

No role-directive change should precede stable contract/fixture semantics.

## 8. Implementation work packets

### WP-A — Contract substrate

Deliver:

- stage-manifest schema;
- efficiency amendment draft;
- authority-posture vocabulary;
- lifecycle/checkpoint definition.

Primary role: Architect/Engineer according to the live task split at implementation time.

### WP-B — Pressure fixtures and validation

Deliver:

- pressure-case matrix;
- manifest valid/invalid fixtures;
- immutable-reuse fixtures;
- drift/revalidation fixtures;
- handoff fixtures;
- production-boundary negative fixtures.

Primary role: Engineer.

### WP-C — Interactive role integration

Deliver bounded directive updates and examples for Architect, Engineer, Steward, and Distiller.

Primary role: role-directive owner under live repository governance. Do not infer authority from this plan.

### WP-D — Regression and measurement

Run representative workflows and record exact commit/test evidence.

Primary role: Engineer/validation operator under live contracts.

### WP-E — Consolidation

Decide whether the amendment remains separate or is incorporated into a successor ChatGPT Project contract.

Primary role: governed design/reconciliation path appropriate to the repository at that time.

## 9. Stop conditions

Implementation must stop and return to design review if any change would:

- treat ChatGPT memory as repository or canonical state;
- let a role label populate authority or activation status;
- reuse bytes across revisions without exact immutable identity;
- rely on an incomplete prior read as full evidence;
- skip a task-specific required authority or activation validation;
- allow a stage manifest or handoff to become production Distiller evidence implicitly;
- turn dependency discovery into semantic search or hidden relevance ranking;
- create an alternate deterministic context-packaging protocol while that design remains unresolved;
- weaken independent proposal review isolation;
- change reconciliation/admission/canonical-memory semantics;
- permit a completion claim without observing the durable result;
- optimize tool-call count by omitting a safety-critical read or revalidation.

## 10. Acceptance criteria

The improvement is ready for ordinary governed use when all of the following are proven:

1. A consequential activation can be summarized by one compact stage manifest.
2. Exact immutable evidence is read once per bounded activation unless a documented exception applies.
3. Mutable refs are resolved at meaningful checkpoints rather than polled reflexively.
4. Drift before write is detected and handled explicitly.
5. Post-write durable identity is required before completion claims.
6. Routine authority posture is compact but semantically complete.
7. Unknown authority remains unknown.
8. Handoffs are shorter and independence-sensitive handoffs avoid prior-reasoning contamination.
9. Explicit normative dependencies are followed from live repository sources.
10. Missing required references fail closed.
11. Pressure cases exist before directive/contract rollout.
12. The production `rd-distill` evidence boundary is unchanged.
13. No RIL authority, activation, reconciliation, admission, or canonical-memory rule is broadened.
14. The deterministic context-packaging review is not pre-empted or silently implemented by this work.
15. Regression evidence binds tests/results to exact repository commits.
16. Efficiency metrics improve without a safety regression.

## 11. Recommended first implementation slice

The smallest useful slice is G0-G3:

1. create the pressure-case matrix;
2. define and schema-validate the stage manifest;
3. implement immutable-evidence reuse rules in fixtures/examples;
4. implement mutable-ref checkpoint rules in fixtures/examples;
5. prove drift and post-write verification behavior.

This slice captures most of the expected repository-call savings without touching role directives, production Distiller behavior, or independent-review semantics.

Only after G0-G3 pass should compact authority blocks and handoff templates become normative coordination guidance.

## 12. Completion and handoff boundary

This planning artifact is complete when durably persisted and its exact commit/ref is observed.

The next consequential work is implementation and conformance, not further Architect planning. That is a meaningful chat boundary. The receiving Engineer should begin from the exact plan artifact and current live repository contracts, re-resolve `main`, verify that no intervening contract change supersedes this plan, and execute G0 first.

The receiving activation must not treat this plan, its branch, or its handoff as implementation authority, accepted RIL activation, or project approval.
