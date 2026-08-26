# Deterministic Task Context Packaging - Stage 1 Proposal

Status: **Proposed**
Method: `proposal-review-synthesis/1`
Repository: `loteque/reasoning-distiller`
Evidence revision: `58b99891e116b5a06dd603810c2b98ea83e328c3`
Stage: **Stage 1 independent proposal**
Proposal-author scope: **Reasoning Graph Protocol Engineer**

Authority posture: this artifact is a technical proposal. It does not establish registered role identity, Steward authorization, accepted RIL activation, reconciliation, admission, canonical knowledge, or project approval. The role label above is coordination metadata for this Stage 1 work.

## Problem

Reasoning Distiller needs a deterministic task-specific mechanism that can prepare bounded AI activation context from two fundamentally different sources:

1. repository controls, such as package-owned protocols, directives, schemas, and operational contracts; and
2. admitted canonical project knowledge represented in PEMS/2, with COVE/1 available as a deterministic encoding where appropriate.

The mechanism must not turn ambient ChatGPT memory, prior conversations, hidden model relevance judgments, role labels, repository path names, or authority-like prose into evidence or authority. It must be replayable after repository and canonical state are resolved, explain exactly why each item entered the pack, preserve PEMS/2 semantics and provenance, and fail closed when required state cannot be established.

The mechanism is a packaging primitive, not a semantic-reconciliation primitive, authority engine, admission primitive, canonical-memory backend, or model-driven retrieval system.

## Decision requested

Adopt a versioned **deterministic task context pack** protocol with an explicit task profile/request, deterministic selectors, separate control/knowledge/operational-evidence planes, a selection-provenance ledger, exact source identities, and an optional lossless COVE/1 encoding of the selected PEMS/2 knowledge projection.

Do not change production `rd-distill` behavior as part of this proposal. Any production integration must be explicit, versioned, and reviewed after the packaging primitive itself passes its conformance gates.

## Governing evidence and inspected state

All mutable repository evidence below was inspected at commit `58b99891e116b5a06dd603810c2b98ea83e328c3`.

| Evidence | Blob identity | Relevance |
|---|---|---|
| `agents/engineer/DIRECTIVE.md` | `463cc2e390ebe412de8075d13cf2fcf879764f32` | Engineer scope; pressure cases before semantic expansion; generic protocol boundary |
| `docs/governance/PROPOSAL_REVIEW_METHOD.md` | `1463c056c6cd7409b2c5f4a7925028de3658fdb6` | Stage separation; durable immutable Stage 1 proposal; independent Stage 2 |
| `docs/operations/CHATGPT_PROJECT_CONTRACT.md` | `04634c27dc5cd19ceaf5eab49fd4460717ec4014` | Project memory is orientation only; live-state and authority boundaries; fixed production evidence |
| `docs/operations/CHATGPT_PROJECT_CHAT_TRANSITION_AMENDMENT.md` | `27ba98e89ff1c650cf5cfb6fe152919a2f1707af` | Independent review/context boundary; handoff is not authority or activation |
| `docs/operations/PRODUCTION_INVOCATION_CONTRACT.md` | `d7fb9bda7ffcc358fccd01ee5fcea731e99db8b6` | Fixed explicit `rd-distill` evidence set; no automatic evidence discovery |
| `docs/operations/RIL_ACTIVATION_EVIDENCE_CONTRACT.md` | `cf5a01f80dd12d1edd1a0ac814963a2d5ddac062` | Activation is read-only, invocation-bound, independent of registration/authorization, and grants no authority |
| `docs/operations/RIL_RECONCILIATION_CONTRACT.md` | `316385a1866730d9f37ab348e5140c93297131c9` | Reconciliation requires accepted activation; does not admit or mutate canonical PEMS/COVE |
| `docs/operations/RIL_ADMISSION_CONTRACT.md` | `a4565ca300dac1afa8f1dd9e04641f246ad46970` | Admission is the only RIL primitive in this slice allowed to mutate canonical PEMS/COVE |
| `docs/design/RD_INIT_DESIGN_CONTRACT.md` | `e813a1a99aae240edd2b45fa054b2b548bc70be3` | Deterministic primitive substrate; explicit evidence; package-owned RGP/PEMS/COVE; no hidden primitive semantics |
| `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md` | `ff5c9ac8eed89c89d5d475d39111e00ecd90f219` | Primitive dependency direction; package/project state split; authority separation |
| `backends/pems-cove/pems-v2.schema.json` | `cd7683d704e8aef2842a0c1b25b453fb1dbc8030` | Normative PEMS/2 structural schema |
| `backends/pems-cove/validate_pems2_contract.py` | `d615bf2e95d3721b0ca312075cc0c39522f0a896` | Deterministic semantic/graph integrity checks without canonical mutation |
| `admission/apply_admission_transaction.py` | `0f0117a7770f1928e41bd76082d9a572102e823a` | Executable COVE/1 encoding and PEMS normalization/round-trip contract surface |
| `admission/apply_admission_transaction_v2.py` | `01cd344a95e73a1be695dcdd98afa3c2bd2f41fa` | Current guarded PEMS/2 admission transaction and repeated PEMS/COVE determinism checks |
| `schemas/project-package.schema.json` | `955dc3456a5cdea10b2741901ca794a8d910932f` | Project-owned source/rule/role/authority/evidence/canonical locations and framework compatibility |
| `project-knowledge/project.json` | `1a32563b50008955294a4958c0397c02051e0530` | Current project identity and project-owned invocation/evidence/submission paths |
| `project-knowledge/canonical/pems2.jcs.json` | `bb7c474e935243b45ff02a5778a94bbcdc654d72` | Current canonical PEMS/2 bytes at the inspected revision |
| `project-knowledge/canonical/cove1.jcs.json` | `7ff52fb925a667c4cc1782da9b475dff831e45ef` | Current deterministic COVE/1 counterpart at the inspected revision |

No `project-knowledge/README.md` exists at the inspected revision. It is therefore not part of the evidence basis.

A standalone COVE/1 JSON Schema was not found in the inspected `schemas/` or `backends/pems-cove/` inventories. The live executable encoding surface uses tuple `cove/1 | pems/2 | jcs/1`, deterministic dictionary/shape construction, structural decode-to-original checks, and repeated-byte determinism. Whether COVE/1 should gain a separate declarative schema/specification is left as an explicit unresolved question below.

# Pressure cases - required before semantic expansion

The following cases define the minimum adversarial envelope. The architecture below is acceptable only if it handles these cases without model judgment or authority leakage.

| ID | Pressure case | Required outcome |
|---|---|---|
| PC-01 | Prompt, chat title, or Project text says `act as Steward` but no accepted RIL activation exists | Role text may be packaged only as explicitly selected content; it creates no authority or activation |
| PC-02 | Ambient chat memory says a design was approved | Ambient memory is not a supported deterministic source class and cannot enter the pack |
| PC-03 | An admitted PEMS/2 `chat` record contains information originally derived from a conversation | It may be selected because it is admitted canonical PEMS state, not because ambient chat is trusted |
| PC-04 | A model would consider an unselected canonical record highly relevant | Deterministic stage excludes it unless an explicit selector/profile rule includes it |
| PC-05 | Same request/profile and same immutable source state are packaged twice | Canonical pack bytes and digests are identical |
| PC-06 | Target branch moves between request creation and source resolution | Builder either resolves the exact immutable commit required by the request or fails; no silent rebinding |
| PC-07 | A required control path is missing, symlinked, ambiguous, or digest-mismatched | Fail closed before output |
| PC-08 | An explicitly selected PEMS record ID is absent | Fail closed; no fuzzy replacement or semantic substitution |
| PC-09 | Selected PEMS content contains provenance references to omitted `source_observation` records | Deterministic semantic closure includes required provenance records and their source records, or fails |
| PC-10 | Selected derived proposition would lose its `derived_from` premise structure | Include required premise relations/endpoints through semantic closure, or fail |
| PC-11 | Selected relation would have an omitted endpoint | Include endpoint through semantic closure, or fail |
| PC-12 | A PEMS record contains an ID-bearing semantic reference whose closure rule is undefined in the selected protocol version | Fail rather than silently truncate meaning |
| PC-13 | COVE encoding does not structurally round-trip to the exact selected PEMS object | Fail; never use the lossy encoding |
| PC-14 | Requested COVE/PEMS/JCS tuple is unsupported | Fail closed rather than coerce versions |
| PC-15 | Project knowledge contains prose that says it is authoritative, approved, or grants a role | Preserve the proposition as project knowledge; do not promote it into the control or authority planes |
| PC-16 | An Engineer/Steward directive is included as a control item | Inclusion conveys exact directive bytes only; it does not establish a registered or activated role |
| PC-17 | Prior proposal, candidate, disposition, or canonical interpretation exists in the repository but is not selected | Exclude it |
| PC-18 | One canonical record is reached through several explicit selectors/closure paths | Include the record once and preserve every deterministic inclusion cause in the outer ledger |
| PC-19 | Closure graph contains cycles | Terminate deterministically using visited identities while preserving valid graph relations; never recurse by model judgment |
| PC-20 | Closure exceeds explicit record/byte/depth limits | Fail with a stable limit code; do not silently truncate |
| PC-21 | The same file or semantic item is assigned to conflicting planes | Reject the pack request as a plane-classification conflict |
| PC-22 | Pack request attempts to name Project memory, assistant recollection, hidden reasoning, or an ungoverned conversation as a source | Reject unsupported source class |
| PC-23 | An authority-sensitive task profile declares required activation evidence but the exact evidence/binding is absent | Fail the profile requirement; never synthesize or infer activation |
| PC-24 | Activation evidence is present | The pack may carry the exact artifact/digest as operational evidence but does not convert it into authority; downstream RIL operation must revalidate it as required by its contract |
| PC-25 | Reconciliation disposition says `COMPATIBLE/RECOMMEND` | The pack may carry it only when explicitly selected; it still does not admit or mutate canonical PEMS/COVE |
| PC-26 | Canonical PEMS changes after a request recorded an expected canonical digest | Fail stale-state validation; do not silently rebuild against newer semantics |
| PC-27 | Control repository commit and canonical snapshot come from separately identified immutable states | Record both identities; if the selected profile requires a relationship that cannot be proven, fail |
| PC-28 | Output path already contains different bytes | Fail immutable-output collision; exact replay may return `NO_CHANGE` |
| PC-29 | Filesystem enumeration order, map order, or host locale differs | Canonical sorting/serialization produces identical pack bytes |
| PC-30 | Current `rd-distill prepare` is invoked without explicitly declaring the generated pack as evidence | Packer output is not injected. Current production evidence remains unchanged |

These pressure cases are part of the proposed protocol contract, not optional implementation examples.

# Proposed architecture

## 1. Separate planning from deterministic packaging

The core split is:

```text
human / governed agent / workflow
        |
        | produces explicit, reviewable selection intent
        v
context profile + pack request
        |
        | deterministic primitive boundary begins here
        v
resolve exact state -> validate -> select -> semantic closure -> encode -> hash
        |
        v
immutable deterministic context pack
        |
        v
explicit downstream activation consumer
```

A human or AI may help *author* a request before this boundary. That upstream act can use judgment. The judgment must become explicit request/profile bytes with provenance before deterministic packaging begins. The builder itself must not perform relevance ranking, semantic search, embeddings, hidden query expansion, summarization, or model calls.

## 2. Two input contracts

### `reasoning-distiller-context-profile/1`

A versioned profile defines the deterministic recipe for a class of tasks. It declares:

- profile identity and version;
- compatible pack/request contracts;
- required source classes and plane assignments;
- required control slots;
- allowed knowledge selector forms;
- required PEMS semantic-closure rules;
- optional required operational-evidence slots;
- compatible PEMS/COVE/JCS tuples;
- deterministic size/count/depth limits;
- output/rendering policy identifiers.

A profile is a recipe, not authority. Its presence in a repository does not make it governing unless the caller has an independent reason to select that profile.

### `reasoning-distiller-context-pack-request/1`

A request instantiates one profile with exact source identities. Minimum proposed fields:

```json
{
  "contract": "reasoning-distiller-context-pack-request/1",
  "profile": {
    "id": "...",
    "locator": "...",
    "digest": "sha256:..."
  },
  "repository": {
    "repository": "owner/name",
    "commit": "<40-hex>"
  },
  "control_selectors": [],
  "knowledge": {
    "semantic": "pems/2",
    "snapshot_locator": "...",
    "snapshot_digest": "sha256:...",
    "record_ids": [],
    "relation_ids": []
  },
  "operational_evidence": [],
  "output_profile": {
    "pack_contract": "reasoning-distiller-context-pack/1",
    "serializer": "jcs/1",
    "knowledge_encoding": "pems/2|cove/1"
  }
}
```

Exact schema spelling should be frozen during implementation gate P1. The semantic requirements in this proposal matter more than the illustrative field names.

## 3. Deterministic resolver

The resolver accepts only source classes defined by the profile/request schema. V1 should support, at minimum:

- exact repository file at exact repository commit, with content digest;
- exact project configuration/package artifact, with digest;
- exact canonical PEMS/2 snapshot, with digest;
- exact governed operational-evidence artifact, with digest.

Unsupported classes fail. Chat memory, model memory, assistant recollection, semantic-search results, hidden reasoning, and implicit `main` are not V1 source classes.

Resolution must reject path escape, unsafe symlinks where filesystem resolution is used, digest mismatch, unsupported versions, missing required slots, and output collisions.

## 4. Strict plane separation

The pack has three explicit planes so that the required control/knowledge separation is not weakened by authority evidence:

### Control plane

Contains only exact selected package/repository controls such as:

- normative contracts;
- schemas;
- role directives;
- versioned task profiles;
- other explicitly selected control artifacts.

A control item carries source identity and bytes. Its path/name does not independently establish authority.

### Knowledge plane

Contains only a PEMS/2 semantic projection derived from an exact canonical PEMS/2 snapshot by explicit selectors plus deterministic semantic closure.

The projection preserves:

- record IDs and kinds;
- lifecycle state;
- record data;
- PEMS provenance unchanged;
- relation IDs, kinds, endpoints, lifecycle, data, and provenance;
- project identity required by the PEMS contract;
- required referenced semantic records.

The builder must not rewrite proposition statements, reclassify source authority, infer supersession, repair provenance, change epistemic roles, or manufacture missing relations.

### Operational-evidence plane

Contains exact governed artifacts such as RIL activation evidence or existing reconciliation dispositions only when the selected profile/request explicitly requires them.

This plane is deliberately not merged into either control or canonical knowledge. Carrying an artifact is not equivalent to accepting it. Downstream authority-bearing primitives retain their own validation/revalidation responsibilities.

## 5. PEMS/2 semantic closure

Selection starts from exact record/relation IDs. A versioned `pems/2` reference descriptor then computes the minimum graph closure needed to avoid semantic breakage.

V1 closure must at least cover the invariants already enforced by the live PEMS/2 contract:

1. `project_id` resolves to the included project record;
2. included relation endpoints resolve to included records;
3. every included provenance reference resolves to an included `source_observation`;
4. every included `source_observation.data.source_id` resolves to an included `source` record;
5. every included derived proposition retains its required `derived_from` premise relation(s) and premise endpoint(s);
6. PEMS relation and record identities remain unique;
7. contradiction ordering and other PEMS graph invariants remain valid.

PEMS contains additional ID-bearing fields such as `about_ids`, supersession links, validation targets, continuation references, and domain-specific references. P1 must freeze an explicit per-field closure policy before implementation. If a selected item contains a reference whose V1 closure semantics are not defined, the builder fails rather than guessing whether omission is harmless.

After closure, the selected document must pass the package-owned PEMS/2 structural schema and semantic validator. Passing validation does not admit anything because the source is already canonical and the operation is read-only projection.

## 6. Preserve two different kinds of provenance

PEMS provenance and packaging provenance answer different questions and must remain separate.

**PEMS semantic provenance** answers questions such as: what source observation supports this proposition or relation? It is copied unchanged from canonical PEMS records.

**Pack selection provenance** answers: why did this already-existing item enter this activation pack?

For every packed item, the outer ledger records one or more inclusion causes:

- explicit request selector ID;
- profile rule ID;
- semantic-closure rule ID;
- parent item/reference that triggered closure;
- exact source repository/commit/blob or canonical snapshot digest;
- item-level record/relation ID where applicable.

When an item is reached through multiple causes, all causes are preserved in canonical order. The ledger never writes those causes into PEMS `provenance`.

## 7. Pack output contract

Define `reasoning-distiller-context-pack/1` as canonical JCS metadata plus payloads. A logical V1 envelope is:

```json
{
  "contract": "reasoning-distiller-context-pack/1",
  "build": {
    "profile_digest": "sha256:...",
    "request_digest": "sha256:...",
    "repository_commit": "...",
    "canonical_pems_digest": "sha256:...",
    "builder_contract": "..."
  },
  "control_plane": {"items": []},
  "operational_evidence": {"items": []},
  "knowledge_plane": {
    "semantic": "pems/2",
    "pems": {},
    "cove": {}
  },
  "inclusion_ledger": [],
  "limits": {},
  "digests": {}
}
```

The exact schema belongs to P1. Required deterministic behavior is:

- canonical ordering of selectors, items, causes, records, and relations;
- canonical JCS serialization for pack metadata;
- content digests for every source and payload;
- no timestamps generated from wall-clock time inside canonical pack identity unless the timestamp is an explicit request input;
- same exact inputs produce identical pack bytes;
- exact replay to an existing identical output is idempotent;
- different existing output bytes are never overwritten.

## 8. COVE/1 projection

COVE/1 is treated as a deterministic encoding of the selected PEMS/2 semantic object, not as a second source of semantic truth and not as a selection mechanism.

When requested and supported:

1. produce normalized selected PEMS/2;
2. encode using accepted tuple `cove/1 | pems/2 | jcs/1`;
3. structurally decode COVE;
4. require decoded object to equal the selected PEMS object exactly;
5. regenerate and require repeated COVE/JCS bytes to be identical;
6. record both PEMS and COVE digests.

If COVE encoding or round-trip fails, the build fails. The builder must not use COVE to erase PEMS record types, provenance, lifecycle, or graph semantics.

## 9. Read-only authority boundary

The context-pack primitive has no authority-bearing operation.

It MUST NOT:

- register or authorize roles;
- claim accepted activation from a role label;
- issue RIL activation evidence;
- treat an activation artifact as authority without the downstream RIL validator;
- reconcile a candidate;
- create or modify a reconciliation disposition;
- create admission authority;
- invoke admission;
- mutate canonical PEMS/COVE;
- update operator/role/Steward-authority projections;
- reinterpret project-owned authority state.

If a profile requires operational evidence, the builder verifies presence, identity, contract shape, and digest according to the profile. Any authority-bearing downstream operation still performs the validation/revalidation mandated by its own RIL contract.

## 10. Production invocation boundary

Current `reasoning-distiller-invocation/1` fixes the `rd-distill prepare` inputs to the installed Distiller directive, explicit evidence bytes, source registry, and optional source context. It prohibits automatic evidence discovery and implicit canonical-state interpretation.

Therefore V1 context packaging is an upstream primitive. It cannot be called invisibly by current `rd-distill prepare`.

A downstream caller may use a generated pack only through an explicit evidence mechanism already permitted by the applicable invocation request, with the pack represented as explicit fixed evidence. However, preserving source-level provenance across an internally multiplexed pack may require a future invocation/source-registry contract revision. Stage 1 does not decide or implement that revision.

Any future native integration must:

- be explicitly versioned;
- preserve the fixed-evidence principle;
- make pack identity visible in the request;
- preserve source-registry provenance semantics;
- add no automatic canonical lookup;
- pass production evidence-boundary tests before release.

# Dependency direction

```text
package-owned normative contracts
        +
explicit task profile
        +
explicit pack request
        +
exact project configuration
        +
exact admitted canonical PEMS snapshot
        +
optional exact governed operational evidence
        |
        v
read-only deterministic context-pack primitive
        |
        +--> validated PEMS/2 projection
        +--> optional lossless COVE/1 encoding
        +--> inclusion/provenance ledger
        +--> canonical pack digest
        |
        v
explicit downstream activation consumer
```

Forbidden reverse dependencies:

```text
ambient chat/model relevance  -X-> deterministic selector
context pack                  -X-> authority registry
context pack                  -X-> reconciliation
context pack                  -X-> admission/canonical mutation
COVE encoding                 -X-> redefine PEMS semantics
consuming project             -X-> fork package-owned PEMS/COVE
activation consumer           -X-> silently broaden pack sources
```

# Invariants

1. **Resolved-state invariant:** every mutable repository source is bound to an immutable commit/blob before packaging.
2. **Explicit-intent invariant:** every root inclusion originates from an explicit profile/request rule.
3. **No-hidden-relevance invariant:** deterministic packaging contains no model call, semantic search, embedding lookup, relevance score, or hidden query expansion.
4. **Plane invariant:** control, canonical knowledge, and operational evidence are separately typed and cannot be silently promoted across planes.
5. **PEMS integrity invariant:** selected knowledge remains a valid PEMS/2 semantic graph with unchanged selected record/relation semantics and provenance.
6. **Selection-provenance invariant:** every included item has at least one reproducible inclusion cause outside PEMS semantic provenance.
7. **Authority invariant:** a pack never creates, grants, activates, reconciles, admits, or approves.
8. **Canonical-state invariant:** packaging is read-only and cannot mutate admitted PEMS/COVE.
9. **COVE losslessness invariant:** COVE is emitted only when it round-trips to the exact selected PEMS object.
10. **Determinism invariant:** fixed profile/request/source bytes produce byte-identical canonical pack output.
11. **Fail-closed invariant:** missing, ambiguous, stale, incompatible, unresolvable, or conflicting required state produces no successful pack.
12. **Production-boundary invariant:** pack generation never silently expands the current `rd-distill` evidence set.
13. **Unknown-state invariant:** missing authority/activation/reproducibility evidence is reported as missing/unknown, never inferred from absence of contradiction.
14. **Immutability invariant:** an existing different output is never overwritten; exact replay is idempotent.

# Failure model

V1 should expose stable machine-readable failure classes. Proposed minimum set:

| Code | Meaning |
|---|---|
| `UNSUPPORTED_PROFILE` | profile contract/version not supported |
| `UNRESOLVED_REPOSITORY_REF` | required immutable repository identity cannot be resolved |
| `SOURCE_NOT_FOUND` | required path/artifact absent |
| `SOURCE_DIGEST_MISMATCH` | observed bytes differ from request/profile digest |
| `UNSUPPORTED_SOURCE_CLASS` | request names ambient/implicit/unknown source type |
| `MISSING_REQUIRED_CONTROL` | profile-required control slot absent |
| `MISSING_REQUIRED_OPERATIONAL_EVIDENCE` | profile requires exact governed evidence but it is absent |
| `PLANE_CLASSIFICATION_CONFLICT` | same source/item assigned incompatibly across planes |
| `CANONICAL_SNAPSHOT_MISMATCH` | canonical PEMS bytes do not match bound identity |
| `PEMS_SCHEMA_INVALID` | source/projection fails PEMS/2 structural validation |
| `PEMS_SEMANTIC_INVALID` | PEMS graph/provenance invariants fail |
| `PEMS_SELECTOR_NOT_FOUND` | explicit record/relation ID absent |
| `PEMS_CLOSURE_UNDEFINED` | selected semantic reference has no defined V1 closure rule |
| `PEMS_CLOSURE_LIMIT` | deterministic closure exceeds declared bound |
| `UNSUPPORTED_COVE_TUPLE` | encoding tuple not accepted |
| `COVE_ROUNDTRIP_FAILED` | COVE does not decode to exact PEMS object |
| `NONDETERMINISTIC_OUTPUT` | repeated generation from fixed inputs differs |
| `OUTPUT_COLLISION` | target exists with different bytes |

Diagnostics may explain failures, but diagnostics must not alter successful canonical pack identity.

# Versioning and compatibility

Proposed independent version axes:

- `reasoning-distiller-context-profile/1`
- `reasoning-distiller-context-pack-request/1`
- `reasoning-distiller-context-pack/1`
- `pems/2`
- optional `cove/1`
- `jcs/1`
- a versioned PEMS reference-closure descriptor associated with the supported PEMS major.

Compatibility rules:

1. unknown major versions fail;
2. changing selector meaning, closure rules, plane semantics, or canonical ordering requires a contract/version change;
3. additive optional metadata may be compatible only when it does not change canonical identity semantics for the existing contract;
4. support for a new PEMS/COVE tuple must be explicit, never inferred;
5. production invocation integration has its own version axis and cannot be smuggled in as a context-pack minor change.

# Evaluation gates

Pressure-case fixtures are P0 and precede implementation.

| Gate | Work | Exit criterion |
|---|---|---|
| P0 | Freeze pressure cases PC-01 through PC-30 | Fixtures exist with expected PASS/FAIL outcomes before semantic expansion |
| P1 | Freeze profile/request/pack schemas, plane model, failure codes, PEMS reference-closure descriptor | Schemas/examples validate; unresolved reference fields fail by construction |
| P2 | Implement exact source resolver | Commit/blob/digest/path adversarial cases pass; no implicit source discovery exists |
| P3 | Implement PEMS selector + semantic closure | Selected projections pass PEMS schema/semantic validation; provenance and required graph structure are unchanged |
| P4 | Implement COVE adapter | Exact structural round-trip and repeated-byte determinism pass |
| P5 | Implement canonical pack builder + ledger | Every output item has deterministic inclusion causes; plane collisions fail |
| P6 | Reproducibility and environment-variance gate | Repeated builds across order/locale/filesystem enumeration perturbations are byte-identical |
| P7 | Authority and memory isolation gate | Role labels, ambient memory, prior candidates, and authority-like knowledge cannot be promoted or auto-selected |
| P8 | Bounds/failure gate | Missing/stale/ambiguous inputs and closure-limit cases fail closed with stable codes |
| P9 | Activation-rendering adapter | Rendering is a pure deterministic function of the pack and does not discover extra context |
| P10 | Production integration design, only if still needed | Separate reviewed versioned contract preserves `rd-distill` fixed-evidence and source-registry semantics |

No production behavior change is authorized by completion of P0-P9. P10 itself requires the later proposal-review and project-governance disposition applicable at that time.

# Implementation sequence

1. Commit pressure-case fixture specification first.
2. Define JSON Schemas for profile, request, pack, result, and failure envelope.
3. Define the PEMS/2 reference-closure descriptor and negative fixtures for every ID-bearing field.
4. Implement a pure source-resolution library over exact commit/path/digest and exact canonical snapshot identities.
5. Implement the PEMS selector/closure projector without mutation or inference.
6. Reuse or extract the package-owned deterministic PEMS normalization and COVE encoding primitives behind explicit versioned interfaces rather than duplicating semantics.
7. Implement the canonical pack builder and outer inclusion ledger.
8. Add reproducibility, plane-separation, memory-isolation, authority-boundary, stale-state, and output-collision tests.
9. Add a provider-neutral deterministic renderer from an already-built pack to activation material.
10. Only after separate review/reconciliation, decide whether a new production invocation contract should natively consume a pack or whether explicit ordinary evidence is sufficient.

# Alternatives considered

## A. Include the entire canonical PEMS snapshot

Advantages: simple and deterministic; no selector semantics.

Rejected as the default because it is not task-bounded and may expose large amounts of irrelevant canonical knowledge. It also avoids rather than solves explicit inclusion provenance.

## B. Semantic search or embeddings over canonical memory

Advantages: potentially high recall and convenient task relevance.

Rejected inside the deterministic stage because relevance becomes model/index/version dependent and inclusion is no longer replayable from explicit syntactic rules. A semantic system may propose selectors upstream, but its output must become explicit request bytes before packaging.

## C. Model-authored summaries of canonical records

Advantages: compact model context.

Rejected as the normative pack payload because summarization rewrites semantics and provenance. A later non-normative presentation layer may summarize only after the exact pack is preserved, and such a summary cannot substitute for the canonical packed evidence.

## D. Flatten PEMS records into prompt snippets

Rejected because graph, lifecycle, provenance, and proposition semantics can be lost or subtly reassigned.

## E. Use COVE as the sole semantic representation

Rejected. COVE/1 is a deterministic encoding of PEMS/2, not an alternate semantic authority or selection ontology.

## F. Make `rd-distill prepare` automatically read canonical memory

Rejected because current `reasoning-distiller-invocation/1` explicitly fixes evidence before activation and forbids autonomous discovery/implicit canonical interpretation.

## G. Hand-author one activation bundle per task

Useful for experiments but insufficient as the protocol because inclusion provenance, replayability, closure semantics, and consistent failure behavior remain informal.

# Risks and failure modes

1. **Selector under-specification:** the dangerous failure is not only selecting too much, but producing a schema-valid subgraph that has silently lost meaningful references. P1 must classify all PEMS ID-bearing fields.
2. **Control-plane overreach:** selecting a directive or contract could be mistaken by a consumer for authority. Plane labeling and explicit non-authority semantics must survive rendering.
3. **Operational-evidence staleness:** an activation artifact can be carried while downstream authority state changes. Downstream authority primitives must revalidate at operation time.
4. **Source-registry compression:** packaging many sources into one file can hide original source identities from current `rd-distill` provenance. Native production integration must not proceed until this is solved explicitly.
5. **Closure explosion:** strongly connected canonical graphs can exceed useful activation bounds. V1 needs explicit hard limits and failure, not hidden truncation.
6. **Protocol duplication:** reimplementing PEMS normalization or COVE encoding in the packer could fork package-owned semantics. Implementation should reuse/extract accepted primitives behind versioned interfaces.
7. **Canonical/backend generalization:** current canonical state is repository-local. A future external backend needs an immutable snapshot identity interface without changing selection semantics.
8. **False reproducibility:** recording only a branch name or path is insufficient. Pack identity must bind immutable bytes/digests.

# Unresolved questions

1. **Declarative COVE/1 contract:** no standalone COVE JSON Schema/specification was found in the inspected schema/backend inventories. Is the executable encoder plus normative admission round-trip contract the intended complete V1 definition, or should implementation first extract a standalone declarative COVE/1 specification?
2. **Complete PEMS closure policy:** which ID-bearing fields require transitive inclusion versus explicit external-reference preservation? This must be decided field-by-field before P2/P3 and cannot be left to implementation intuition.
3. **Profile governance:** which repository process makes a task profile eligible for use? A profile must not become authority merely because it exists at a path.
4. **Canonical backend abstraction:** what immutable snapshot locator/digest interface should replace repository-local `project-knowledge/canonical/pems2.jcs.json` for external backends?
5. **Production provenance:** if a pack becomes one `rd-distill` evidence file, how should candidate provenance address the original packed sources without weakening the existing source-registry contract?
6. **Pack persistence:** should generated packs be ephemeral build artifacts, invocation-owned project evidence, or a dedicated immutable project-knowledge evidence class? This proposal requires immutability/content identity but does not assign canonical-memory standing.
7. **Operational evidence validation depth:** V1 can verify exact artifact contract/digest while downstream RIL primitives revalidate authority. Whether the packer should call read-only RIL validators as a profile precondition should be reviewed separately to avoid coupling packaging to authority semantics.
8. **Rendering size policy:** byte/record limits should be deterministic, but task families may need different bounds. Profiles need explicit limits rather than one hidden global heuristic.

# Acceptance criteria

Stage 1 recommends the mechanism only if implementation can eventually demonstrate all of the following:

- identical immutable inputs produce byte-identical canonical pack output;
- no successful build depends on ambient chat memory, prior assistant context, semantic search, embedding retrieval, model relevance, or hidden reasoning;
- every root inclusion has an explicit profile/request cause and every closure inclusion has a deterministic traceable cause;
- control-plane material, canonical PEMS knowledge, and operational authority evidence remain separately typed;
- selected canonical knowledge remains valid PEMS/2 with record/relation semantics and PEMS provenance unchanged;
- all required PEMS references are closed according to a versioned explicit descriptor, with undefined closure failing closed;
- COVE/1, when emitted, round-trips exactly to the selected PEMS object and is deterministic;
- repository commits, blobs, canonical snapshots, request/profile bytes, builder version, and output digests are sufficient for replay;
- role labels, directives, authority-like prose, dispositions, and activation artifacts cannot be promoted beyond their contract-defined meaning;
- the builder never performs reconciliation, admission, canonical mutation, role mutation, authorization, or activation creation;
- stale or missing required authority/activation evidence is not inferred or repaired;
- current production `rd-distill` behavior and fixed evidence boundary remain unchanged unless a later explicit versioned integration is accepted;
- pressure cases are executable before semantic expansion and all required gates pass before production implementation;
- generated artifacts are immutable by content identity and conflicting overwrites fail closed.

# Stage 1 recommendation

Proceed with a read-only deterministic task context-pack primitive built around explicit versioned profiles and requests, exact immutable source identities, a PEMS-preserving semantic closure algorithm, a separate selection-provenance ledger, and optional lossless COVE/1 encoding.

Keep model relevance outside the deterministic boundary. Keep ambient chat outside the source model. Keep control bytes, canonical knowledge, and operational evidence in separate planes. Keep activation, reconciliation, and admission in their existing primitives. Keep current production `rd-distill` evidence behavior unchanged until a later explicit integration contract is independently reviewed and reconciled.

This proposal is now ready for independent Stage 2 Engineer review under `proposal-review-synthesis/1`. Stage 2 should challenge the architecture and produce a separate review/synthesis artifact rather than editing this Stage 1 file.