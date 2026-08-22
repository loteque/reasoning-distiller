# Deterministic Task Context Packaging - Steward Final Plan

Status: **APPROVED FOR IMPLEMENTATION OF P0-P9; P10 REQUIRES SEPARATE REVIEW**
Method: `proposal-review-synthesis/1`
Repository: `loteque/reasoning-distiller`
Evidence revision: `58b99891e116b5a06dd603810c2b98ea83e328c3`
Stage 1 commit: `0030d502db2304e9d3a865372baba74d5910bf22`
Stage 1 blob: `0561c42d0fa8a913d8e8665c21d4a79d74fb19ad`
Stage 2 commit: `7c54f0f44f137e0ccda02ff3632eaefd235ac5af`
Stage 2 blob: `a9f44ed4107325db08ed186cbb9d1a58a1c8f4ee`

## Authority and activation record

Operational role for this Stage 3 reconciliation: `steward:default`.

Requested authority scope: `semantic_reconciliation`.

Live project-owned authorization history at the evidence revision replays to `steward:default` for `semantic_reconciliation`. The package-provided default Steward is available and protected. This Stage 3 invocation used the accepted v1 `explicit_declaration` activation method with:

```text
invocation_id: chatgpt-project-stage3-58b99891-20260822T1100-0700
source: chatgpt-project
activation_digest: sha256:656b256ff7eecdb2b17ae432658891cc718c8bc8968804db0b74e2d9afbd4ff1
validation: PASS/ACTIVATION_ACCEPTED
```

This record establishes the authority posture for this bounded proposal-review reconciliation only. It does not create role registration, change Steward authorization, perform admission, or mutate canonical PEMS/COVE.

This final plan is the Stage 3 artifact required by `docs/governance/PROPOSAL_REVIEW_METHOD.md`. It is not an R12 candidate-bound reconciliation disposition under `docs/operations/RIL_RECONCILIATION_CONTRACT.md`, because Stage 1 and Stage 2 are proposal-review artifacts rather than Distiller submissions beneath `project-knowledge/submissions/`. No R12 disposition, admission transaction, or canonical-state mutation is authorized or performed by this plan.

## 1. Decision

Adopt the Stage 1 deterministic task context-pack architecture **with the Stage 2 required revisions incorporated as normative implementation requirements**.

The approved mechanism is a separate, deterministic, read-only context-packaging primitive that receives explicit versioned intent and immutable source bindings, produces a bounded context pack with preserved source identity and plane semantics, and performs no model-driven relevance selection, reconciliation, admission, authority creation, or implicit production evidence discovery.

The approved architecture retains:

- explicit versioned task profiles and pack requests;
- deterministic exact-source resolution;
- strict separation of control, canonical knowledge, and operational-evidence planes;
- PEMS/2 semantic projection using a complete versioned closure descriptor;
- unchanged PEMS semantic provenance plus a separate outer selection-provenance ledger;
- optional lossless COVE/1 encoding of the selected PEMS object;
- immutable, replayable output identity;
- fail-closed behavior for missing, stale, conflicting, unsupported, or ambiguous state;
- no silent integration into current production `rd-distill` behavior.

Stage 1's illustrative request/envelope schemas are not themselves approved as frozen protocol bytes. They are design sketches to be replaced by the reconciled contracts and identity rules below before implementation proceeds past the protocol-freeze gates.

## 2. Review disposition

| Input | Recommendation | Steward disposition |
|---|---|---|
| Stage 1 Reasoning Graph Protocol Engineer proposal | Adopt deterministic task context packaging with explicit intent, exact sources, separated planes, PEMS closure, selection provenance, optional lossless COVE, and no silent production integration | **Accepted as architectural base** |
| Stage 2 independent Engineer review/synthesis | `COMPATIBLE_WITH_REQUIRED_REVISIONS`; retain the core architecture but require R1-R10 and expanded pressure cases | **Accepted; required revisions incorporated below** |

There is no remaining disagreement about the central architecture. The material Stage 2 objections are not treated as optional recommendations. They are implementation requirements and gates.

## 3. Amendment reconciliation

| Stage 2 amendment | Steward disposition | Normative resolution |
|---|---|---|
| R1 Canonical standing | **Accepted, protocol-freeze blocker** | Knowledge-plane input requires a project/backend canonical-state binding. A path, filename, request label, schema-valid PEMS object, or content digest alone does not prove admitted canonical standing. |
| R2 Byte-preserving payloads | **Accepted, protocol-freeze blocker** | Canonical pack payloads preserve exact source bytes using a frozen byte representation. V1 uses RFC 4648 standard Base64 with padding and no whitespace inside JCS objects. Digests cover original source bytes. |
| R3 Digest domains | **Accepted, protocol-freeze blocker** | Pack identity uses explicit non-circular digest domains. Whole-file receipts are outside their own preimage. No digest field hashes bytes containing itself. |
| R4 Profile eligibility | **Accepted, governed-consumer blocker** | Profile validation and profile eligibility are separate. The packer validates bytes and compatibility only. A governed consumer supplies an explicit eligible profile binding or policy result. |
| R5 Operational-evidence status | **Accepted, authority-sensitive blocker** | Carried evidence records validation status explicitly and never becomes `trusted`, `authorized`, or `activated` merely by presence. Authority-bearing consumers revalidate under their own contracts. |
| R6 Renderer trust-channel separation | **Accepted, renderer blocker** | Rendering preserves structural plane boundaries. Knowledge or operational-evidence text cannot be promoted into a control/instruction channel because it resembles instructions. |
| R7 Toolchain identity | **Accepted, reproducibility blocker** | Replay identity binds the schema, semantic validator, closure descriptor, COVE adapter when used, serializer contract, builder contract, and renderer contract when used, either directly by immutable artifact digest or through a package content identity that contractually fixes those bytes. |
| R8 Bounds and empty results | **Accepted** | Source-resolution, projection/closure, canonical-pack, and rendered-activation bounds are distinct and measured explicitly. Empty-result behavior is profile-defined. No semantic truncation, ranking, or summarization is permitted inside deterministic build/render stages. |
| R9 Source conflicts and consistency | **Accepted** | Logical source identity is distinct from immutable snapshot identity. Conflicting bindings fail unless the profile explicitly models multiple snapshots. Cross-source consistency requirements are explicit profile/request constraints. |
| R10 Side effects and persistence | **Accepted** | The semantic builder is pure and side-effect free. Persistence is a separate immutable artifact-write operation. Cache presence or absence cannot alter successful pack bytes or source discovery. |

No Stage 2 required amendment is rejected.

## 4. Resolved questions and remaining uncertainty

### 4.1 Canonical-state binding

**Resolved for implementation direction.** V1 must define a read-only canonical-source binding contract, tentatively `reasoning-distiller-canonical-state-binding/1` until schema freeze chooses final naming.

The binding must identify at least:

- project identity;
- logical canonical source identity;
- canonical backend type/contract and immutable configuration identity;
- immutable snapshot identity;
- semantic tuple, including `pems/2` and serializer identity;
- exact PEMS content digest and optional COVE content digest;
- immutable evidence sufficient for the backend/project contract to establish that the snapshot is the admitted canonical state being consumed;
- any declared relationship to the repository/control snapshot when the selected profile requires one.

A repository-local path may be an implementation detail of one backend adapter. Path spelling is never the generic proof of canonical standing.

The packer may validate an existing binding read-only. It must not create admission evidence, repair canonical state, or infer admission from placement.

### 4.2 COVE/1 public dependency

**Resolved with a bounded V1 approach.** A new full standalone COVE JSON Schema is not required before work begins. Before COVE is exposed as a public context-pack dependency, P1 must freeze a thin immutable adapter contract that identifies the supported `cove/1 | pems/2 | jcs/1` tuple and binds the exact package-owned encode/decode behavior used for replay.

Implementation should reuse or extract the existing package-owned COVE primitives. It must not duplicate or reinterpret COVE semantics. If a stable adapter contract cannot immutably fix the behavior, direct implementation/artifact digests are required in toolchain identity.

### 4.3 Complete PEMS closure

**Blocking implementation requirement, not an open implementation choice.** P1d must enumerate every semantically relevant ID-bearing field in the supported PEMS/2 contract and assign exactly one versioned rule: include transitively, preserve as an explicitly defined external reference, or reject. Undefined closure semantics fail closed.

### 4.4 Profile governance

**Resolved at the boundary level.** The packer does not decide whether a profile is allowed for a governed task. The consuming project/workflow supplies an explicit profile-eligibility binding or validation result that names the exact profile identity/digest. Repository presence, filename, role label, newest version, task similarity, or model choice cannot establish eligibility.

### 4.5 Production provenance

**Deferred and blocked.** Native `rd-distill` consumption of a context pack is not authorized by this plan. Current `reasoning-distiller-invocation/1` fixed-evidence behavior remains unchanged. P10 may begin only after P0-P9 pass and must use a separate proposal/review/reconciliation cycle that preserves source-registry provenance and the fixed-evidence invariant.

### 4.6 Pack persistence

**Resolved for V1.** The pure builder returns deterministic bytes/results and performs no persistence. An optional persistence adapter may write an immutable derived artifact to a caller-selected location that is explicitly outside canonical, admission, reconciliation, authorization, role, and activation-evidence stores. Storage does not grant evidence or canonical standing. A future dedicated artifact class requires its own contract.

### 4.7 Operational-evidence validation depth

**Resolved.** V1 distinguishes carrying from accepting. Each item records one of a frozen set of statuses such as:

```text
carried_unvalidated
shape_and_digest_validated
accepted_validation_result
```

`accepted_validation_result` means the pack carries an immutable result produced by a separately identified validator under its own contract. It does not mean the packer performed or owns the authority-bearing operation. Downstream RIL primitives still validate or revalidate as their contracts require.

### 4.8 Rendering size and trust policy

**Resolved at the contract level.** Rendering is a deterministic transformation of an already-built pack under an explicit renderer profile. It has its own byte bound and stable failure result. It never discovers, ranks, summarizes, truncates, or promotes content between planes.

The renderer contract must provide structural framing that lets the consumer distinguish control material from knowledge data and operational evidence. If the selected consumer cannot preserve that separation, rendering fails rather than flattening the planes.

## 5. Approved architecture and dependency direction

```text
explicit task intent
        +
exact profile bytes
        +
explicit profile-eligibility binding when governed
        +
immutable repository/control source bindings
        +
validated canonical-state binding
        +
optional exact operational-evidence bindings
        +
explicit source-consistency constraints
        |
        v
read-only deterministic resolver
        |
        v
exact selectors + versioned PEMS closure
        |
        v
validated PEMS/2 projection
        +
optional lossless COVE/1 encoding
        |
        v
pure canonical context-pack builder
        |
        +--> source registry / immutable identities
        +--> separated control plane
        +--> separated knowledge plane
        +--> separated operational-evidence plane
        +--> selection-provenance ledger
        +--> toolchain identity
        +--> non-circular digest domains
        |
        v
optional immutable persistence adapter
        |
        v
explicit deterministic renderer / activation consumer
```

Forbidden dependencies remain:

```text
ambient chat/model memory      -X-> source selection
model relevance/embeddings     -X-> deterministic packer
path/name/role prose           -X-> canonical or authority standing
context pack                   -X-> role authorization or activation creation
context pack                   -X-> reconciliation or admission
context pack                   -X-> canonical PEMS/COVE mutation
COVE adapter                   -X-> PEMS semantic redefinition
renderer                       -X-> plane promotion
cache/persistence state        -X-> source discovery or semantic output
context packaging              -X-> implicit current rd-distill evidence expansion
```

## 6. Protocol and identity decisions

### 6.1 Contracts to freeze before resolver implementation

P1 must define, with final names chosen during schema freeze:

- context profile contract;
- context-pack request contract;
- canonical/source binding contract(s);
- governed profile-eligibility binding contract;
- context-pack/result/failure contracts;
- PEMS/2 closure descriptor contract;
- COVE adapter contract when COVE output is supported;
- build receipt/persistence result contract;
- deterministic renderer contract.

Semantics-bearing schemas must reject unknown fields through `additionalProperties: false` or an equivalent closed-world rule.

### 6.2 Exact byte representation

For JSON/JCS V1 packs, opaque source payloads are represented as RFC 4648 Base64 using the standard alphabet, required `=` padding, and no embedded whitespace.

The source digest is SHA-256 of the original bytes before Base64 encoding. No newline conversion, Unicode normalization, locale conversion, or host text decoding enters canonical source identity.

A renderer may decode payload bytes only when the renderer profile explicitly permits the media/content type and defines the decoding/escaping behavior. Any rendering transformation remains separate from raw source-byte identity.

### 6.3 Digest domains

P1c must freeze named digest domains and exact preimages. At minimum the design distinguishes:

- raw source-byte digest;
- canonical profile digest;
- canonical request digest;
- canonical-state-binding digest;
- selected PEMS projection digest;
- optional COVE payload digest;
- canonical manifest/metadata digest;
- payload-set digest;
- canonical pack identity digest;
- out-of-band serialized-pack/build-receipt digest when persisted.

Protocol-specific digest preimages must be domain separated. A whole-file receipt may hash the final serialized pack bytes, but the receipt is not embedded inside the bytes it hashes.

### 6.4 Toolchain identity

A successful build records immutable behavior identity for:

- PEMS schema;
- PEMS semantic validator;
- PEMS closure descriptor;
- COVE adapter/implementation when used;
- JCS/canonical serializer contract;
- pack builder contract/implementation;
- renderer contract/implementation when rendering is performed.

A package content identity may replace individual implementation digests only when a normative package contract guarantees that the content identity immutably binds every relevant artifact and behavior version.

## 7. Source and plane semantics

### Control plane

Contains only explicitly selected exact control artifacts. Inclusion conveys bytes and source identity. It does not create role registration, authority, or activation.

### Knowledge plane

Contains only a PEMS/2 semantic projection from a proven canonical-state binding. Selected semantic content and PEMS provenance remain unchanged. The builder does not rewrite propositions, infer lifecycle transitions, repair provenance, manufacture relations, or reinterpret source authority.

### Operational-evidence plane

Contains only explicitly selected exact governed artifacts and their explicit validation-status metadata. Artifact presence never becomes a generic trust bit.

### Selection provenance

The outer inclusion ledger records every deterministic root or closure cause independently of PEMS semantic provenance. If one item has multiple inclusion causes, all causes are preserved in canonical order. Items are never deduplicated across planes by textual similarity.

## 8. Approved invariants

1. **Immutable source invariant:** every mutable source is resolved to an immutable identity before semantic packaging.
2. **Canonical-standing invariant:** knowledge-plane material is accepted only through a validated project/backend canonical-state binding, never by path or self-description.
3. **Explicit-intent invariant:** every root inclusion originates from explicit profile/request bytes.
4. **No-hidden-relevance invariant:** deterministic packaging performs no model call, embedding lookup, semantic search, hidden query expansion, or relevance ranking.
5. **Plane invariant:** control, canonical knowledge, and operational evidence remain separately typed through build and rendering.
6. **Byte-preservation invariant:** canonical source identity is based on exact source bytes; host text normalization cannot alter identity.
7. **PEMS integrity invariant:** selected knowledge remains valid PEMS/2 with unchanged selected semantics and PEMS provenance.
8. **Closure invariant:** every supported semantic reference follows a frozen closure rule; undefined references fail closed.
9. **Selection-provenance invariant:** every packed item has one or more reproducible inclusion causes outside PEMS provenance.
10. **Authority invariant:** a pack never registers, authorizes, activates, reconciles, admits, or approves.
11. **Operational-status invariant:** carrying authority-related evidence is mechanically distinguishable from accepted validation of that evidence.
12. **Read-only invariant:** semantic build performs no project-knowledge or RIL mutation.
13. **COVE losslessness invariant:** COVE is emitted only when exact structural round-trip and repeated-byte determinism pass.
14. **Digest invariant:** pack identity uses named non-circular domain-separated preimages.
15. **Toolchain invariant:** replay binds the behavior-defining validation/build toolchain.
16. **Boundedness invariant:** source, closure/projection, pack, and renderer limits are explicit; deterministic stages never silently truncate or summarize.
17. **Source-consistency invariant:** conflicting logical-source bindings or unmet required cross-source relationships fail closed.
18. **Persistence invariant:** persistence is separate from pure build; caches and output locations cannot change semantic bytes or standing.
19. **Determinism invariant:** fixed contracted inputs and toolchain identity produce byte-identical canonical output.
20. **Production-boundary invariant:** current `rd-distill` evidence behavior is unchanged unless a later explicit integration contract is accepted.
21. **Unknown-state invariant:** missing authority, activation, canonical-standing, compatibility, or replay evidence remains unknown/missing rather than inferred.
22. **Immutability invariant:** different existing output bytes are never overwritten; exact replay is idempotent.

## 9. Pressure-case gate

P0 adopts Stage 1 PC-01 through PC-30 and Stage 2 PC-31 through PC-46 as the minimum adversarial fixture set.

P0 is complete only when every case exists as an executable or machine-checkable fixture with a stable expected result before semantic implementation expands.

No pressure case may be weakened merely to accommodate an implementation shortcut. New implementation-discovered boundary cases must be added before the affected semantic code is accepted.

## 10. Ordered implementation plan and gates

| Gate | Required work | Exit criterion |
|---|---|---|
| **P0 Pressure cases** | Materialize PC-01 through PC-46 with expected PASS/FAIL outcomes and stable failure classes | Fixture corpus exists before semantic implementation and covers authority, canonical standing, byte identity, digest circularity, toolchain variance, source conflicts, side effects, and renderer isolation |
| **P1a Source identity** | Freeze repository/control source identities, logical-source identity, canonical-state binding, operational-evidence identity, and cross-source consistency semantics | A source can be proven immutable and correctly classified without path/name inference; unproven canonical standing fails |
| **P1b Protocol schemas** | Freeze profile, request, pack, result, failure, eligibility, source-binding, and receipt schemas | Unknown semantics-bearing fields fail closed; examples and negative fixtures validate deterministically |
| **P1c Bytes/digests/toolchain** | Freeze Base64 byte representation, canonical serialization, digest domains/preimages, receipt rules, and toolchain identity | Same raw inputs produce same canonical identities across hosts; self-referential digest construction is impossible |
| **P1d PEMS closure** | Freeze exhaustive field-by-field PEMS/2 closure descriptor and negative fixtures | Every supported ID-bearing reference has a deterministic rule; undefined closure fails |
| **P1e Consumer/profile eligibility** | Freeze the interface by which a governed consumer binds an eligible profile identity/digest | Packer cannot infer eligibility from repository placement, role labels, or model choice |
| **P2 Resolver** | Implement read-only immutable source resolution | Missing, unsafe, mutable, digest-mismatched, conflicting, or inconsistent sources fail; no implicit discovery exists |
| **P3 Projection** | Implement exact PEMS selection, semantic closure, and package-owned validation | Projection remains valid PEMS/2 with unchanged selected semantics/provenance; closure causes are reproducible |
| **P4 COVE adapter** | Reuse/extract package-owned COVE implementation behind frozen adapter contract | Exact PEMS round-trip and repeated-byte determinism pass for every supported tuple |
| **P5 Pure pack build** | Build canonical separated planes, source registry, ledger, toolchain record, and digest structure with no persistence side effects | Every item has deterministic causes and identity; plane conflicts fail; repeated build bytes match |
| **P6 Persistence adapter** | Add optional immutable write operation outside authority/canonical lifecycle stores | Exact replay is `NO_CHANGE`; different existing bytes fail collision; storage location grants no semantic standing |
| **P7 Reproducibility** | Perturb locale, ordering, filesystem enumeration, path separators, Unicode environment, temporary paths, and toolchain identities | Contracted equivalent inputs remain byte-identical; incompatible toolchain changes fail visibly |
| **P8 Authority/memory isolation** | Exercise role labels, ambient memory, prior candidates, authority-like knowledge, operational-evidence status, and canonical-standing attacks | No source is auto-selected or promoted; no authority/activation/canonical standing is inferred |
| **P9 Deterministic renderer** | Freeze and implement provider-neutral structural plane framing, deterministic escaping/decoding, and renderer byte limits | Renderer is a pure function of pack + renderer profile, discovers nothing, preserves planes, and fails instead of truncating/summarizing |
| **P10 Production integration** | Separate future design for native `rd-distill` use, if still needed | **Not authorized by this plan.** Requires a new proposal/review/reconciliation artifact after P0-P9 evidence exists |

P1a through P1e are protocol-freeze prerequisites for P2. R1 through R7 are therefore blockers, not work that may be postponed until after a resolver or pack schema has shipped.

## 11. Ownership boundaries

| Concern | Owner/boundary |
|---|---|
| Generic context-pack protocol/schema implementation | Reasoning Distiller Engineer/Architect technical surfaces under this reconciled plan |
| RGP/PEMS/COVE normative semantics | Existing package-owned contracts; this plan does not redefine them |
| Project canonical standing | Consuming project/backend admission and canonical-state contracts |
| Profile eligibility for a governed workflow | Consuming project/workflow policy or explicit governing binding |
| Semantic source selection roots | Explicit profile/request author before deterministic boundary |
| Deterministic source resolution/build | Context-pack primitive, read-only |
| Authority validation | Applicable RIL primitive, not context packaging |
| Reconciliation/admission | Authorized activated Steward operations, separate from context packaging |
| Pack persistence | Separate derived-artifact adapter with no implicit semantic standing |
| Activation rendering | Deterministic renderer under explicit renderer contract |
| Current production Distiller evidence | `docs/operations/PRODUCTION_INVOCATION_CONTRACT.md`; unchanged by P0-P9 |

The Steward disposition authorizes implementation of the reconciled plan. It does not independently redefine RGP/PEMS/COVE semantics or transfer technical ownership away from the Engineer/Architect contracts.

## 12. Definition of done for the approved implementation scope

P0-P9 are complete only when all of the following are demonstrated by durable tests/evidence:

- PC-01 through PC-46 have stable expected outcomes and pass;
- identical immutable inputs and behavior identity produce byte-identical canonical pack bytes;
- ambient ChatGPT/agent memory, prior conversations, hidden reasoning, semantic search, embeddings, and model relevance cannot enter the deterministic source set;
- canonical knowledge cannot enter the knowledge plane without a validated canonical-state binding;
- exact source bytes survive canonical packaging without newline or Unicode normalization drift;
- digest domains are explicit, non-circular, and reproducible;
- every root and closure inclusion has deterministic selection provenance;
- selected PEMS remains structurally and semantically valid with unchanged selected PEMS provenance;
- every supported PEMS reference has a versioned closure rule and undefined references fail;
- optional COVE round-trips exactly and deterministically;
- control, knowledge, and operational evidence remain distinct through rendering;
- instruction-like knowledge text cannot be promoted into the control channel;
- operational evidence carries explicit validation status and is not converted into authority by presence;
- authority, activation, reconciliation, admission, role state, and canonical state are never created or mutated by build/render operations;
- source, closure, pack, and renderer limits fail deterministically without hidden truncation or summarization;
- source-registry conflicts and unmet cross-source consistency requirements fail closed;
- pure build has no semantic side effects and cache/persistence state cannot alter pack bytes;
- persistence is immutable/idempotent and collisions fail closed;
- replay under changed host conditions is stable and changed behavior/toolchain identity is visible;
- current production `rd-distill` fixed-evidence behavior remains unchanged.

Completion of P0-P9 is **not** evidence that P10 has been approved.

## 13. Exact next authorized action

The next authorized action is:

> **Reasoning Graph Protocol Engineer / implementation Engineer: create a fresh implementation branch from the durable commit containing this final plan and implement P0 only, materializing PC-01 through PC-46 with machine-checkable expected outcomes and stable failure classifications. Do not implement the resolver, pack schemas, canonical-state binding, renderer, or production integration until P0 is reviewed as complete. Then proceed to P1a under this final plan.**

No production `rd-distill` behavior change, canonical PEMS/COVE mutation, RIL admission, or authority-state mutation is authorized by this next action.

## 14. Final Steward disposition

**Stage 1 is accepted with Stage 2 revisions incorporated. Stage 2 `COMPATIBLE_WITH_REQUIRED_REVISIONS` is reconciled to an implementation-ready plan for P0-P9.**

The decisive changes from the original Stage 1 text are that admitted canonical standing must be proven through a backend/project binding, exact arbitrary source bytes must have a frozen representation, pack identity must use non-circular digest domains, profile eligibility must remain external to the packer, operational evidence must preserve validation status rather than imply authority, rendering must preserve trust-channel separation, and replay must bind the behavior-defining toolchain.

P10 remains a separate future governance boundary. Native production integration cannot be inferred from implementation success, test success, pack persistence, or this plan's approval of P0-P9.
