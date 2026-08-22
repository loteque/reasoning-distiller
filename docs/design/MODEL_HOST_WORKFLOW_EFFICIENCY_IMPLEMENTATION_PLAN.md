# Interactive Model Host Governed Workflow Efficiency - Implementation Plan

Status: **Proposed implementation plan**

Evidence revision: `58b99891e116b5a06dd603810c2b98ea83e328c3`

Operational scope: Knowledge Systems Architect planning for interactive model-hosted repository coordination.

Authority posture: this document is a design and implementation-planning artifact only. It does not establish registered role identity, RIL activation, Steward authorization, implementation approval, reconciliation, admission, or canonical project knowledge. A branch, pull request, session label, model-host label, or user request does not change those boundaries.

## 1. Objective

Make governed interactive repository work faster, less repetitive, provider-neutral, and easier to improve over time without weakening repository-state, authority, activation, review-independence, production-evidence, reconciliation, admission, or canonical-memory boundaries.

The target operating loop is:

```text
Resolve -> Load -> Work -> Revalidate -> Persist -> Retro/Handoff
```

The implementation must make the safe path cheaper than ad hoc repetition. Efficiency gains MUST come from better state tracking, immutable-source reuse, compact coordination metadata, provider-neutral contracts, reusable pressure cases, and standardized process retrospectives. They MUST NOT come from skipping authority checks, trusting ambient model memory, broadening evidence sets, collapsing role boundaries, hiding repository drift, or treating process metadata as project-semantic evidence.

This plan adds two explicit requirements to the original efficiency work:

1. replace provider-specific `ChatGPT` terminology in the active repository surface with provider-neutral **Interactive Model Host** terminology;
2. standardize a **Boundary Retro** at every meaningful interactive session boundary governed by the transition contract.

## 2. Terminology

### 2.1 Provider-neutral host term

The normative generic term proposed by this plan is:

- long form: **Interactive Model Host**;
- short form: **Model Host**.

An Interactive Model Host is the interactive environment that hosts a model-assisted repository workflow. Examples may include different commercial or local model products, but no particular provider is part of the generic semantic contract.

The term separates three concepts that MUST remain distinct:

```text
model
  != interactive model host
  != repository authority / project knowledge system
```

A Model Host can supply conversational continuity and tools. Its memory, labels, summaries, or product-specific features do not thereby become repository authority or project evidence.

### 2.2 Session and chat

Provider-neutral contracts SHOULD use **interactive session** or **session** for the bounded conversational work surface.

The phrase **chat retro** MAY remain as informal user-facing vocabulary, but the normative artifact and protocol name is **Boundary Retro**.

### 2.3 Legacy names

The current repository contains active files and contract identifiers using provider-specific `ChatGPT` terminology. Those names are normative at the inspected revision and therefore MUST NOT be silently reinterpreted or mechanically replaced without a migration contract.

The target end state is zero provider-specific `ChatGPT` terminology in the active provider-neutral repository contract surface. Historical Git commits remain historical facts and are not rewritten.

## 3. Scope boundary

This plan governs the interactive Model Host coordination layer around repository work.

It does not change:

- RGP, PEMS/2, or COVE semantics;
- production `rd-distill` evidence or invocation behavior;
- role registration or role authority;
- RIL activation semantics;
- reconciliation or admission;
- project canonical-memory semantics;
- `docs/governance/PROPOSAL_REVIEW_METHOD.md` stage independence;
- the in-flight deterministic context-packaging Stage 1/Stage 2 design question.

The deterministic context-packaging proposal may later inform or supersede parts of this coordination design. Until that review is complete, this work MUST remain outside production evidence preparation and MUST NOT define an alternate context-packaging protocol.

Provider-neutralization is a terminology and host-contract migration. It MUST NOT change authority semantics merely because a provider-specific noun changes.

The Boundary Retro is coordination metadata. It MUST NOT become canonical knowledge, authority evidence, RIL activation evidence, reconciliation evidence, admission evidence, or implicit production Distiller evidence merely because it exists or is persisted.

## 4. Problems to remove

### P1 - Re-reading immutable evidence

Once exact bytes at `<commit>:<path>` have been read and their blob identity recorded within the same bounded activation, repeated reads of the same immutable object usually add cost without adding safety.

### P2 - Over-resolving mutable refs

A mutable target such as `main` must be resolved when current state matters, especially before consequential analysis and before or after writes. It does not need to be re-resolved before every adjacent reasoning step when no drift-sensitive operation occurred.

### P3 - Repeating authority prose

The same distinctions between coordination role, registered role, authorization, activation, reconciliation, admission, and canonical knowledge are often restated in long prose. The distinctions must remain explicit, but can be encoded in a compact standard posture block.

### P4 - Oversized handoffs

Independent reviews can be biased by large summaries of the outgoing role's reasoning. Handoffs should preserve identities, problem, constraints, authority posture, unresolved questions, and exact next action while omitting prior conclusions that the receiving role should independently reconstruct.

### P5 - Ad hoc evidence discovery

Task-relevant evidence discovery is repeatedly rebuilt conversationally. The system needs a disciplined rule for following explicit normative dependencies without treating model relevance judgment, semantic search, or remembered files as authority.

### P6 - Pressure cases live only in prose

Pressure cases are useful, but long prose makes them harder to compare, test, and reuse. A compact fixture or matrix form should become the reusable conformance backbone.

### P7 - Provider coupling in generic contracts

Provider-specific product names in generic coordination contracts create unnecessary coupling and make otherwise generic governance appear product-bound.

### P8 - No standardized process retro at boundaries

The existing transition mechanism requires bounded handoffs, but process lessons can be lost or repeatedly rediscovered. A standardized Boundary Retro should capture what worked, friction, safety checks, and reusable improvements without polluting the receiving role's evidence boundary.

## 5. Proposed coordination primitives

### 5.1 Stage manifest

Introduce a compact provider-neutral coordination record:

`reasoning-distiller-interactive-model-stage-manifest/1`

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
7. The manifest MUST NOT depend on provider-specific hidden state to be valid.

### 5.2 Immutable evidence ledger

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
- fresh or isolated receiving activation -> identities may be carried, but required bytes must be independently loaded unless the governing contract explicitly permits supplied frozen evidence.

This is activation-local evidence reuse, not cross-session memory trust.

### 5.3 Mutable-ref revalidation policy

Default mutable-ref checkpoints:

1. **Resolve** at consequential activation start.
2. **Revalidate** immediately before a consequential repository write when drift could matter.
3. **Observe** the durable result after the write.

Additional resolution is required when:

- the user explicitly asks for current state;
- a tool result indicates drift;
- a dependency is discovered on another mutable ref;
- a governing contract requires a tighter checkpoint.

A mutable branch MUST NOT be treated as unchanged merely because no contradictory session message appeared.

### 5.4 Explicit dependency-following rule

Do not introduce semantic search, embedding relevance, or hidden model ranking as a deterministic governance mechanism.

For the coordination layer, discovery proceeds from:

1. the explicit user task;
2. the active role directive;
3. the directly governing task contract;
4. explicit normative references named by those live sources;
5. repository-owned state explicitly required by those contracts.

A model may recognize that a task needs another contract, but any consequential claim must be grounded by actually reading that source. Remembered filenames are navigation hints only.

Future automation MAY add structured dependency metadata to normative documents, but path presence or dependency listing MUST NOT itself create authority. If structured dependency metadata is introduced, it must be reviewed as coordination metadata and must fail closed on missing required references.

### 5.5 Compact authority posture

Standardize a short human-readable block for ordinary updates and handoffs:

```text
role: <coordination role>
scope: <bounded task>
authority: <none required | unknown | exact governed requirement>
activation: <not required | unknown | exact evidence id>
forbidden: <bounded list>
```

The compact block replaces repeated explanatory paragraphs only when it preserves the same distinctions. If authority state is ambiguous or conflicting, expand the explanation rather than compressing it.

### 5.6 Minimal bounded handoff

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

### 5.7 Boundary Retro

Introduce a provider-neutral coordination contract:

`reasoning-distiller-model-host-boundary-retro/1`

A Boundary Retro is produced when a **meaningful interactive session boundary** is reached under the governing transition rules. It is not produced merely because a conversation is long or a minor subtask changes.

The retro and handoff are intentionally different artifacts:

```text
Boundary Retro
  -> learns from the outgoing workflow

Bounded Handoff
  -> carries only what the receiving activation needs
```

Minimum structured fields:

```text
contract
repository
resolved_revision
boundary_reason
outgoing_role
completed_scope
durable_artifacts
what_worked
friction_or_waste
safety_checks_that_mattered
reusable_process_improvements
unresolved_process_risks
authority_posture
independence_sensitive
receiving_role
next_action
handoff_reference
```

Rules:

1. The retro records process observations, not project-semantic decisions.
2. The retro MUST distinguish observed facts from suggestions for future process improvement.
3. Successful tests, commits, role labels, or user satisfaction MUST NOT be summarized as project approval unless approval was independently established by the governing contract.
4. The retro MUST NOT grant or imply role registration, authorization, activation, reconciliation, admission, or canonical standing.
5. The retro MUST NOT silently enter production `rd-distill` evidence, raw candidate bytes, or structured Distiller output.
6. For an independence-sensitive receiving activation, the retro MUST remain outside the receiving clean-room context unless the governing review contract explicitly requires it.
7. The bounded handoff may reference the retro for ordinary continuation, but an independent reviewer MUST NOT be required to consume the retro before forming an independent view.
8. If persisted, the persistence class must explicitly remain coordination or process evidence unless another governed mechanism separately changes its standing.
9. The retro should be concise enough to be routine. Verbosity is a conformance concern because an oversized retro can recreate the handoff-bias problem.
10. If no meaningful boundary exists, no retro is required.

Recommended human-readable Boundary Retro template:

```text
Boundary Retro
- Completed: <scope/result and durable identity>
- Worked well: <1-3 process observations>
- Friction: <1-3 avoidable costs or ambiguities>
- Safety checks that mattered: <only checks that materially affected the work>
- Improve next time: <concrete reusable changes>
- Unresolved process risks: <none | bounded list>
- Next boundary: <receiving role and action>
```

The structured record, if implemented, is the stable machine-facing representation. The human-readable form is a projection and MUST NOT acquire extra semantics.

### 5.8 Pressure-case matrix

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

Initial cases MUST include:

1. role label claims Steward authority;
2. prior session says a change was approved;
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
15. transition prose is about to enter production Distiller evidence;
16. helper proposes a contract but no live read occurred;
17. same-role minor subtask change incorrectly triggers a new-session recommendation;
18. actual cross-role or independence boundary fails to trigger a handoff;
19. output branch collides with existing different content;
20. main changes after analysis but before persistence;
21. provider-specific product name appears in a new generic contract surface;
22. migration changes authority or evidence meaning while changing terminology;
23. stale legacy contract identifier remains referenced after provider-neutral migration;
24. Model Host implementation depends on a product-specific memory feature without declaring it;
25. Boundary Retro converts a successful test into an approval claim;
26. Boundary Retro is injected into an independent Stage 2 review context;
27. Boundary Retro is inserted into production Distiller evidence or candidate bytes;
28. Boundary Retro is treated as RIL activation evidence;
29. meaningful cross-role boundary omits the required retro;
30. minor same-role continuation produces a noisy retro;
31. retro records stale pre-write revision after a durable write;
32. handoff and retro disagree about the durable artifact identity;
33. retro contains an unresolved suggestion that is later treated as an accepted project decision;
34. provider-neutral migration leaves a case-insensitive `chatgpt` occurrence in the active generic contract surface;
35. a compatibility mechanism requires retaining a provider-specific active contract identifier, conflicting with the zero-occurrence target.

## 6. Provider-neutral terminology migration protocol

Provider-neutralization MUST be implemented as a governed migration rather than a blind text replacement.

### 6.1 Inventory

Before mutation, produce a complete active-tree inventory of case-insensitive occurrences of:

```text
ChatGPT
chatgpt
CHATGPT
```

Classify every occurrence as one of:

- normative contract prose;
- normative contract identifier;
- repository path or filename;
- role directive;
- schema identifier or field;
- test or fixture;
- workflow or package metadata;
- documentation example;
- historical quotation or intentionally provider-specific example;
- generated or vendored content.

The inventory is evidence for migration completeness, not authority.

### 6.2 Target contract names

Subject to implementation-time contract review, preferred provider-neutral successors are:

```text
reasoning-distiller-interactive-model-host/1
reasoning-distiller-interactive-model-host-chat-transition/1
reasoning-distiller-interactive-model-stage-manifest/1
reasoning-distiller-model-host-boundary-retro/1
```

Preferred active paths include:

```text
docs/operations/INTERACTIVE_MODEL_HOST_CONTRACT.md
docs/operations/INTERACTIVE_MODEL_HOST_CHAT_TRANSITION_AMENDMENT.md
docs/design/MODEL_HOST_WORKFLOW_EFFICIENCY_IMPLEMENTATION_PLAN.md
schemas/model-host-stage-manifest.schema.json
docs/operations/MODEL_HOST_WORKFLOW_EFFICIENCY_AMENDMENT.md
docs/testing/MODEL_HOST_WORKFLOW_EFFICIENCY_PRESSURE_CASES.md
tests/fixtures/model-host-workflow-efficiency/
tests/test_model_host_stage_manifest.py
tests/test_model_host_workflow_efficiency_contract.py
```

These names are proposed implementation targets, not current repository facts.

### 6.3 Semantic preservation

Every renamed or successor contract MUST preserve the pre-migration safety meaning unless a separately reviewed semantic change explicitly says otherwise.

Provider-neutralization MUST NOT:

- turn host memory into evidence;
- turn a role label into authority;
- weaken repository-state resolution;
- weaken clean-room independent review;
- broaden production Distiller evidence;
- merge authorization and activation;
- change reconciliation or admission semantics;
- create provider-specific hidden dependencies.

### 6.4 Compatibility and zero-occurrence target

The target active-tree state is no provider-specific `ChatGPT` terminology in generic repository-owned contract surfaces.

If an existing public or installed consumer contract requires compatibility with a legacy provider-specific identifier, implementation MUST stop and determine a migration mechanism before deleting or aliasing it. A compatibility alias is not automatically acceptable because retaining the legacy literal may conflict with the zero-occurrence requirement.

Possible resolutions include a major-version migration, an external migration note, or a bounded compatibility window. The correct choice depends on live consumer and packaging contracts and MUST be decided from repository evidence.

Git history is not rewritten merely to eliminate historical occurrences.

### 6.5 Completion proof

Provider-neutral migration is complete only when:

1. all active generic contract surfaces use provider-neutral terminology;
2. all active internal references resolve;
3. package/install/test surfaces remain conformant;
4. case-insensitive repository-tree search demonstrates the agreed zero-occurrence target, subject only to explicitly governed exceptions if any are accepted;
5. cross-host fixtures demonstrate no provider-specific feature is semantically required;
6. authority and evidence pressure cases behave identically before and after the terminology migration.

## 7. Implementation artifacts

Subject to implementation-time repository inspection, the preferred target artifact set is:

```text
docs/design/MODEL_HOST_WORKFLOW_EFFICIENCY_IMPLEMENTATION_PLAN.md
schemas/model-host-stage-manifest.schema.json
docs/operations/MODEL_HOST_WORKFLOW_EFFICIENCY_AMENDMENT.md
docs/testing/MODEL_HOST_WORKFLOW_EFFICIENCY_PRESSURE_CASES.md
schemas/model-host-boundary-retro.schema.json
tests/fixtures/model-host-workflow-efficiency/
tests/test_model_host_stage_manifest.py
tests/test_model_host_workflow_efficiency_contract.py
tests/test_model_host_boundary_retro.py
```

The current file path remains legacy during this planning branch because changing the active normative provider-specific contracts is part of the migration itself. Implementation should rename this plan together with the governed migration rather than creating two competing active plans.

Optional helper tooling may be added only after contract and fixture semantics are stable. Any helper must remain coordination-only and must not become a hidden authority or evidence resolver.

## 8. Gate sequence

### G0 - Freeze baseline and pressure cases

Before semantic expansion, capture representative coordination scenarios and the pressure-case matrix.

Measure at minimum:

- repository reads required by the documented workflow;
- duplicate reads of identical immutable evidence;
- mutable-ref resolutions;
- handoff size;
- repeated authority explanation blocks;
- current provider-specific terminology inventory size;
- whether a meaningful boundary generated a retro;
- retro size and whether it contaminated receiving context;
- whether role, authority, evidence, and independence boundaries were preserved.

PASS requires:

- pressure cases cover known safety failures and efficiency waste;
- provider-coupling and retro pressure cases are included before semantic expansion;
- metrics can be compared before and after;
- no production or authority semantics have changed.

### G1 - Provider-neutral vocabulary inventory and migration contract

Produce the repository-wide inventory and define the migration from provider-specific active terms to Interactive Model Host terms.

PASS requires:

- every active-tree occurrence is classified;
- successor contract IDs and paths are explicit;
- compatibility requirements are discovered rather than guessed;
- semantic-preservation rules are explicit;
- the zero-occurrence target and any possible exception process are explicit;
- no rename has silently changed authority or evidence semantics.

### G2 - Provider-neutral stage-manifest contract and schema

Define `reasoning-distiller-interactive-model-stage-manifest/1` and its JSON schema.

PASS requires:

- unknown authority states are representable;
- role label cannot satisfy authority fields;
- immutable evidence records bind commit, path, and blob;
- mutable target is distinct from resolved immutable revision;
- permitted and forbidden outputs plus next boundary are explicit;
- schema contains no field that can grant authority merely by presence;
- schema has no product-specific requirement.

### G3 - Immutable-evidence reuse conformance

Add fixtures proving exact immutable evidence can be reused inside one activation without repeated repository reads, while cross-revision and fresh-activation cases still fetch when required.

PASS requires:

- identical immutable evidence is not redundantly fetched in the same activation;
- changed revision invalidates reuse unless the same immutable object is independently proven;
- fresh independent activation does not trust ambient prior-session bytes;
- incomplete reads are not treated as complete evidence.

### G4 - Mutable-ref checkpoint conformance

Encode `Resolve -> Load -> Work -> Revalidate -> Persist` in the provider-neutral coordination amendment and fixtures.

PASS requires:

- consequential work begins with live resolution;
- no unnecessary branch polling occurs during stable same-role work;
- drift-sensitive writes re-resolve immediately before mutation;
- detected drift causes re-evaluation or fail-closed behavior rather than silent write;
- post-write durable identity is observed before completion claim.

### G5 - Compact authority posture

Introduce the standardized posture block and tests or examples for unknown, no-authority-required, and governed-authority-required tasks.

PASS requires:

- compression never converts unknown to accepted;
- registration, authorization, activation, reconciliation, and admission remain distinguishable;
- expanded explanation is required on conflict or ambiguity;
- role labels remain coordination metadata.

### G6 - Minimal handoff templates

Add normal and independence-sensitive handoff templates.

PASS requires:

- normal handoff preserves exact artifact and evidence identities plus next action;
- independent handoff omits unnecessary outgoing reasoning while preserving the complete frozen proposal or artifact;
- handoff cannot be mistaken for RIL activation or project approval;
- transition prose remains outside production candidate and evidence bytes.

### G7 - Explicit dependency-following guidance

Document the dependency-following rule and add pressure fixtures for explicit normative references, missing references, stale remembered paths, and task-specific additional evidence.

PASS requires:

- no semantic search or hidden model ranking is required;
- explicit referenced contracts are actually read before consequential reliance;
- missing required reference fails closed;
- repository path or name alone is never treated as authority;
- no task-profile or catalog mechanism pre-empts the separate deterministic context-packaging review.

### G8 - Boundary Retro contract and independence firewall

Define `reasoning-distiller-model-host-boundary-retro/1`, its structured schema if persistence is warranted, and its human-readable projection.

PASS requires:

- every meaningful session boundary produces the standardized retro unless a stricter governing contract explicitly forbids it;
- ordinary same-role continuation does not produce noisy retros;
- retro and handoff remain semantically distinct;
- retro records durable identities actually observed;
- retro does not convert tests, commits, labels, or user intent into approval;
- retro has no authority or activation effect;
- retro is excluded from clean-room independent review context by default;
- retro never enters production `rd-distill` evidence, candidate bytes, or structured output implicitly;
- retro suggestions remain suggestions until separately accepted;
- compact projection remains materially equivalent to structured fields.

### G9 - Role-directive integration

Only after G1-G8 pass, update interactive role directives as needed to point to provider-neutral coordination contracts, stage-manifest discipline, Boundary Retro responsibility, and handoff rules.

PASS requires:

- Architect, Engineer, Steward, and Distiller local boundaries remain unchanged;
- transition responsibility is not broadened into authority;
- the production Distiller directive remains free of navigation or retro contamination;
- same-role ordinary continuation does not trigger noisy handoffs or retros;
- provider-specific host assumptions are absent from generic role behavior.

### G10 - Cross-workflow and cross-host regression

Run the pressure suite across at least:

- architecture or design task;
- ordinary engineering implementation task;
- independent proposal review;
- Steward-governed operation where activation evidence is required;
- production `rd-distill` preparation boundary;
- at least two distinct Model Host adapters or provider-neutral simulated host fixtures.

PASS requires:

- efficiency rules never weaken a stricter task-specific contract;
- production evidence remains fixed;
- independent review remains isolated;
- authority-sensitive operations still revalidate authority and activation as required;
- no canonical project-memory mutation is introduced;
- equivalent host inputs produce equivalent coordination semantics;
- no host-specific memory or UI feature is required for conformance.

### G11 - Efficiency and provider-neutral acceptance

Compare G10 workflows to the G0 baseline.

Target acceptance:

- zero avoidable duplicate reads of the exact same immutable evidence inside a bounded activation;
- mutable-ref resolution reduced to required checkpoints plus explicit drift-triggered checks;
- routine authority posture expressed in a compact block without semantic loss;
- independence-sensitive handoffs contain no unnecessary outgoing reasoning summary;
- meaningful boundaries produce concise standardized retros;
- independent receiving contexts do not inherit retro reasoning;
- active generic contract surface satisfies the provider-neutral occurrence target;
- no increase in false authority, stale-state, production-evidence, or role-boundary failures;
- no task-specific contract is bypassed to meet an efficiency or portability target.

Safety failures block acceptance regardless of efficiency improvement.

### G12 - Contract consolidation and legacy-name removal decision

After conformance evidence exists, decide whether to:

1. retain provider-neutral amendments beside the predecessor contracts for a bounded migration window;
2. consolidate them into a new provider-neutral contract version and remove superseded active files;
3. perform a package/version migration if consumers require it.

PASS requires:

- one unambiguous active generic contract family;
- all internal references resolve;
- legacy provider-specific active names are removed to the extent required by the accepted migration rule;
- no compatibility behavior silently preserves obsolete authority semantics;
- resulting durable commit and conformance evidence are recorded.

## 9. Dependency direction

The desired dependency direction is:

```text
repository task + live role directive + governing contracts
                    |
                    v
          provider-neutral stage manifest
                    |
                    v
   immutable evidence ledger + explicit live reads
                    |
                    v
             bounded role work
                    |
                    v
       revalidate -> persist -> observe
                    |
                    v
          Boundary Retro + Handoff
```

Forbidden reverse dependencies include:

```text
Model Host memory -> repository authority
Boundary Retro -> project decision
Boundary Retro -> RIL activation
Boundary Retro -> production Distiller evidence
handoff -> receiving-role authority
provider product feature -> generic protocol meaning
process metric -> project approval
```

## 10. Work packets

### WP-A - Baseline and pressure suite

Gates: G0

Primary scope: Architect + Engineer

Deliverables:

- baseline measurements;
- initial provider-neutral and retro pressure cases;
- reusable fixture format.

### WP-B - Provider-neutral migration design

Gates: G1

Primary scope: Architect + Engineer

Deliverables:

- complete occurrence inventory;
- migration map;
- compatibility assessment;
- semantic-preservation table;
- zero-occurrence acceptance rule.

### WP-C - Core coordination substrate

Gates: G2-G4

Primary scope: Engineer after applicable governance and activation requirements are satisfied.

Deliverables:

- stage-manifest schema;
- immutable-evidence reuse fixtures;
- mutable-ref checkpoint fixtures and contract text.

### WP-D - Compact coordination contracts

Gates: G5-G7

Primary scope: Architect + Engineer

Deliverables:

- authority posture;
- normal and independent handoff templates;
- explicit dependency-following guidance.

### WP-E - Boundary Retro

Gates: G8

Primary scope: Architect + Engineer

Deliverables:

- Boundary Retro contract;
- optional schema if persistence is accepted;
- compact human-readable projection;
- independence firewall fixtures;
- production-evidence exclusion fixtures.

### WP-F - Role integration

Gates: G9

Primary scope: applicable role-directive owners under repository governance.

Deliverables:

- provider-neutral role-directive references;
- boundary-retro responsibility;
- no change to role authority.

### WP-G - Cross-host regression and acceptance

Gates: G10-G11

Primary scope: Engineer

Deliverables:

- cross-workflow suite;
- cross-host equivalence fixtures;
- baseline comparison;
- provider-neutral occurrence proof.

### WP-H - Consolidation

Gates: G12

Primary scope: governance or architecture decision under applicable live contract.

Deliverables:

- accepted consolidation path;
- legacy-name removal;
- durable completion evidence.

## 11. Stop conditions

Implementation MUST stop for design or governance review if any gate requires:

- trusting ambient Model Host memory as repository evidence;
- a model relevance judgment to determine authority or required deterministic evidence;
- treating the stage manifest as authority;
- treating the Boundary Retro as authority, activation, reconciliation, admission, or canonical knowledge;
- injecting the retro or handoff into production Distiller evidence merely because it exists;
- weakening independent review by feeding outgoing retros or reasoning into a clean-room review;
- changing current `rd-distill` fixed-evidence behavior without its own versioned contract change;
- silently changing existing role authority during terminology migration;
- requiring a provider-specific hidden feature for a generic contract;
- retaining stale legacy identifiers without an explicit compatibility decision;
- rewriting Git history merely to erase provider terminology;
- mutating canonical project knowledge through the coordination layer;
- claiming completion when the resulting durable repository state was not observed.

## 12. Migration and compatibility rules

1. The inspected provider-specific contracts remain controlling until a durable provider-neutral successor is accepted under repository governance.
2. New artifacts created by this work SHOULD use provider-neutral names from the start where that does not conflict with current normative references.
3. Existing provider-specific normative identifiers MUST NOT be silently redefined in place if consumers could depend on their identity.
4. The implementation must inspect package, install, test, workflow, and documentation references before removing a legacy identifier.
5. Provider-neutral terminology does not authorize semantic changes.
6. Historical Git commits are not migrated.
7. A compatibility shim, if needed, must be explicit, bounded, tested, and reconciled with the zero-occurrence target.
8. The current legacy filename for this plan is temporary planning transport, not the desired final provider-neutral path.

## 13. Acceptance criteria

The complete improvement program is acceptable only when all of the following hold:

1. The active generic coordination contract family is provider-neutral.
2. A repository-tree inventory proves the accepted provider-specific zero-occurrence target or documents an explicitly governed exception.
3. The same generic coordination semantics can be exercised by more than one Model Host implementation or neutral fixture.
4. No Model Host memory, role label, chat title, summary, or product feature becomes authority or project evidence by presence.
5. The stage manifest records but never creates authority state.
6. Exact immutable evidence is reused safely inside one bounded activation without unnecessary refetches.
7. Mutable refs are resolved at the required checkpoints and drift is handled fail-closed.
8. Compact authority posture preserves registration, authorization, activation, reconciliation, and admission distinctions.
9. Handoffs are smaller while preserving exact durable identities and next action.
10. Independent review receives only the context permitted by its governing contract and does not inherit Boundary Retro reasoning by default.
11. Every meaningful Model Host session boundary produces a standardized Boundary Retro and bounded handoff where applicable.
12. Minor same-role continuation does not produce unnecessary retros or session transitions.
13. Boundary Retro process observations never become approval, authority, activation, reconciliation, admission, canonical knowledge, or production evidence by implication.
14. Production Distiller fixed-evidence and candidate boundaries remain unchanged unless separately versioned and governed.
15. Pressure cases are executable or mechanically checkable before broad semantic expansion.
16. No efficiency target can override a safety failure.
17. Consequential writes are revalidated against mutable state and durable results are observed before completion claims.

## 14. Non-goals

This plan does not:

- select the best model or Model Host provider;
- require all Model Hosts to expose identical UI or memory features;
- make model output deterministic;
- define deterministic task context packaging for production Distiller;
- create a semantic-search evidence resolver;
- grant role authority;
- define RIL activation evidence;
- reconcile proposals;
- perform admission;
- turn process retrospectives into canonical memory;
- rewrite repository history.

## 15. Unresolved questions

1. Do any installed package consumers depend externally on the current provider-specific contract IDs or filenames?
2. Should provider-neutralization use a major contract version, a replacement contract family, or another migration mechanism supported by the live package contracts?
3. Can the active-tree zero-occurrence target be absolute, or are there repository-owned historical/example fixtures that must retain a provider name as quoted data?
4. Should the Boundary Retro structured record be ephemeral coordination state, a durable repository artifact, or only a human-readable chat projection?
5. If durable retros are permitted, where do they live so repository presence cannot be mistaken for canonical knowledge?
6. Should retro schemas permit references to durable artifacts only, or also immutable external evidence identities?
7. What maximum size keeps Boundary Retros useful without recreating oversized handoffs?
8. Which transition categories, if any, should suppress a retro because a stricter clean-room contract demands no outgoing process context at all?
9. How should Model Host conformance be tested when a provider exposes no persistent session-memory feature? The generic contract should not require one.
10. Should role directives emit retro responsibility directly or reference a single provider-neutral transition contract to avoid repeated wording?

These questions are implementation inputs, not permission to guess. Missing required answers remain unknown until resolved by live evidence or the appropriate governed decision.

## 16. Recommended first implementation slice

After the applicable implementation boundary is entered, perform **G0 through G4** first:

```text
G0 pressure cases + baseline
 -> G1 provider-neutral inventory/migration contract
 -> G2 provider-neutral stage manifest
 -> G3 immutable evidence reuse
 -> G4 mutable-ref checkpoints
```

Do not begin role-directive rewrites, broad legacy-name deletion, or Boundary Retro persistence before the earlier gates establish the migration and coordination substrate.

G8 may define the retro contract after G5-G7 stabilize the posture, handoff, and dependency semantics. This prevents the retro from becoming a second ad hoc handoff format.

## 17. Implementation boundary and handoff

This plan is ready to be reviewed and implemented only through the repository's applicable role and governance boundaries.

The planning artifact itself does not authorize implementation.

The receiving implementation activation should:

1. resolve current `main`;
2. read the live Engineer directive and task-relevant governing contracts;
3. verify this plan has not been superseded;
4. begin at G0;
5. stop on any gate failure or authority ambiguity;
6. re-resolve the target ref before consequential writes;
7. observe and report durable results;
8. produce the standardized Boundary Retro and bounded handoff at the next meaningful session boundary once the retro contract itself has been implemented and accepted.

Until G8 is implemented, the existing live transition contract controls boundary behavior.
