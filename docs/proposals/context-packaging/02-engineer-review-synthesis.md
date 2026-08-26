# Deterministic Task Context Packaging - Stage 2 Review/Synthesis

Status: **Independent review complete; compatible with required revisions**
Method: `proposal-review-synthesis/1`
Repository: `loteque/reasoning-distiller`
Live `main` observed before review write: `58b99891e116b5a06dd603810c2b98ea83e328c3`
Independent evidence revision: `58b99891e116b5a06dd603810c2b98ea83e328c3`
Stage 1 proposal commit: `0030d502db2304e9d3a865372baba74d5910bf22`
Stage 1 proposal path: `docs/proposals/context-packaging/01-engineer-proposal.md`
Stage 1 proposal blob: `0561c42d0fa8a913d8e8665c21d4a79d74fb19ad`
Stage: **Stage 2 independent Engineer review/synthesis**

Authority posture: this artifact is a bounded technical review. It does not establish registered role identity, Steward authorization, accepted RIL activation, reconciliation, admission, canonical project knowledge, implementation approval, or project approval. The Engineer role label is coordination metadata for this review. This artifact does not edit Stage 1 and does not perform a Steward decision.

## Review method and independence record

The Stage 2 review followed the ordering required by `docs/governance/PROPOSAL_REVIEW_METHOD.md`:

1. resolve the live repository revision;
2. inspect the live Engineer directive and task-relevant governance, production, RIL, PEMS, COVE, project-package, and project-owned state at that revision;
3. independently reconstruct the problem, invariants, dependency direction, failure posture, and adversarial cases before opening Stage 1;
4. only then inspect the complete immutable Stage 1 proposal at `0030d502db2304e9d3a865372baba74d5910bf22` and verify its blob identity;
5. compare Stage 1 against the already-formed independent view;
6. record agreements, disagreements, missing cases, required revisions, unresolved questions, and a Stage 2 disposition for later Steward reconciliation.

The adjacent provider-neutral workflow-efficiency plan and Boundary Retro proposal were not consumed during the independent reconstruction and are not evidence for this Stage 2 review.

## Evidence basis

Mutable repository evidence was bound to `58b99891e116b5a06dd603810c2b98ea83e328c3`. Task-relevant evidence inspected before Stage 1 included:

- `agents/engineer/DIRECTIVE.md`;
- `docs/governance/PROPOSAL_REVIEW_METHOD.md`;
- `docs/operations/CHATGPT_PROJECT_CONTRACT.md`;
- `docs/operations/PRODUCTION_INVOCATION_CONTRACT.md`;
- `docs/operations/RIL_ACTIVATION_EVIDENCE_CONTRACT.md`;
- `docs/operations/RIL_RECONCILIATION_CONTRACT.md`;
- `docs/operations/RIL_ADMISSION_CONTRACT.md`;
- `docs/operations/RIL_STEWARD_AUTHORIZATION_CONTRACT.md`;
- `docs/design/RIL_ARCHITECTURE_SYNTHESIS.md`;
- `docs/design/RIL_PROVENANCE_DESIGN_CONTRACT.md`;
- `protocols/rgp/SUBMISSION_PROTOCOL.md`;
- `backends/pems-cove/pems-v2.schema.json`;
- `backends/pems-cove/validate_pems2_contract.py`;
- the package-owned COVE/admission implementation surface;
- `schemas/project-package.schema.json`;
- `project-knowledge/project.json`;
- the distinct `project-knowledge/canonical`, `project-knowledge/admission`, `project-knowledge/reconciliation`, and `project-knowledge/steward-authorization` stores.

Important observed repository facts:

- PEMS/2 structural validity and semantic graph validity are distinct. The executable PEMS validator enforces reference resolution and graph invariants beyond JSON Schema.
- Registration, Steward authorization, activation, reconciliation, and admission are separate lifecycle states. A context pack must not collapse those states into one trust bit.
- Admission is the canonical mutation boundary. Context packaging must remain read-only.
- Canonical bytes and admission evidence are stored separately. A canonical-looking path or valid PEMS digest does not, by itself, prove admitted standing.
- The current project descriptor, `project-knowledge/project.json`, identifies the project and selected operational paths but does not itself establish a complete immutable canonical-backend snapshot binding.
- No standalone declarative COVE/1 schema was found in the inspected backend inventory. Concrete COVE/1 behavior exists in package-owned executable admission/encoding surfaces.
- No standalone `SCHEMA_VERSION` or `VALIDATOR_VERSION` files exist in `backends/pems-cove` at the inspected revision. Version/replay identity therefore must be bound to the actual schema, validator, and implementation artifacts or to a later explicit package contract.
- Current production `rd-distill prepare` evidence behavior remains governed by `docs/operations/PRODUCTION_INVOCATION_CONTRACT.md`. This review does not alter or broaden that evidence set.

## Independent reconstruction formed before Stage 1 inspection

The following position was formed before the Stage 1 proposal was opened.

### Required architecture

1. Context packaging should be a separate deterministic, read-only preparation primitive, not an alternate evidence-discovery mode inside current `rd-distill prepare`.
2. The deterministic boundary must accept only explicit, versioned, mechanically inspectable inputs. Ambient chat/session history, assistant recollection, hidden model state, semantic relevance judgment, embeddings, and implicit repository discovery are not valid deterministic inputs.
3. Package-owned controls and project-owned admitted canonical knowledge are distinct source classes and must remain distinguishable after packaging and rendering.
4. Context packaging must never create or infer registration, authorization, activation, reconciliation, admission, or canonical standing.
5. Source inclusion must preserve authority and evidence semantics rather than amplifying them. A directive remains directive bytes; an activation artifact remains an artifact; a reconciliation disposition remains a disposition; a proposition that claims authority remains a proposition.
6. Every mutable source must first be resolved to an immutable identity. Same explicit request, policy, immutable sources, validator/toolchain identity, and rendering contract must produce byte-identical canonical output.
7. Deterministic selection may use exact selectors and versioned syntactic closure rules, but not model judgment. Upstream judgment is permitted only if it is frozen into explicit request/profile bytes before the deterministic boundary.
8. A PEMS/2 projection needs a formal semantic closure policy. JSON Schema validity is not sufficient to establish a semantically usable projection.
9. Missing, stale, ambiguous, conflicting, unsupported, or unverifiable required state must fail closed. The primitive must not silently skip, repair, replace, rebind, or reinterpret required inputs.
10. Mutable external locators are insufficient source identities. An external-backend contract needs an immutable snapshot identity and observed content digest or equivalent immutable binding.
11. COVE/1, if emitted, must be treated only as a deterministic lossless encoding of selected PEMS semantics, not as an alternate truth source or selection ontology.
12. A task profile must be explicit and versioned. Eligibility to use a profile is a separate governance/consumer-policy question and must not arise from file presence, path naming, or model choice.
13. Rendering must itself be deterministic. Ordering, encoding, escaping, payload representation, limits, truncation policy, newline behavior, and error behavior must be specified rather than delegated to model or host judgment.
14. Operational evidence must retain explicit validation status and contract meaning. Presence is not acceptance, and acceptance for an authority-bearing operation remains the responsibility of the applicable RIL validator/primitive.
15. Context packs are derived operational artifacts. Their persistence class must not silently become canonical PEMS/COVE, admission evidence, reconciliation evidence, or authority evidence.
16. A multiplexed pack must preserve a deterministic source registry or equivalent provenance manifest sufficient to identify each item, immutable origin, source digest, validation result, and inclusion cause.
17. The generic packer should consume project-owned descriptors/registries/adapters rather than hard-code one consuming project, one provider, or one repository-local backend layout.
18. Pack construction must be side-effect free with respect to project knowledge and RIL stores. Cache or output writes, if any, must be outside authority/canonical stores and governed by an explicit artifact contract.
19. Any future production integration requires its own explicit, versioned, reviewed integration contract. Packaging cannot silently alter current fixed production evidence behavior.
20. Canonical pack identity must have a non-circular digest domain. Inputs, validation artifacts, payload bytes, metadata, and any excluded receipt fields must have an explicitly defined hashing boundary.

## Stage 1 agreements

Stage 1 strongly agrees with the independent reconstruction on the central architecture. The following elements should be retained unless later Steward reconciliation finds conflicting evidence.

### A1. Separate planning from deterministic packaging

Stage 1 correctly places judgment before the deterministic boundary and requires it to become explicit profile/request bytes. The builder itself excludes semantic search, embeddings, model calls, hidden query expansion, summarization, and model relevance ranking.

### A2. Explicit versioned profile and request contracts

The proposed `reasoning-distiller-context-profile/1` and `reasoning-distiller-context-pack-request/1` split is sound as a protocol direction. It provides a reviewable place to freeze selection intent, source requirements, limits, closure semantics, and output policy.

### A3. Three-plane separation

Separating control, canonical knowledge, and operational evidence is preferable to flattening all context into one untyped evidence bundle. Stage 1 correctly states that plane inclusion does not upgrade authority.

### A4. PEMS semantic projection plus explicit closure

Stage 1 correctly recognizes that PEMS selection is not ordinary document slicing. Its closure treatment for project identity, relation endpoints, provenance observations, source records, derivation premises, uniqueness, and contradiction invariants aligns with the live PEMS validator.

### A5. Distinct semantic and selection provenance

Keeping PEMS semantic provenance unchanged while maintaining an outer deterministic inclusion ledger is a strong design choice. Packaging provenance answers a different question and should not be written back into PEMS provenance.

### A6. Optional lossless COVE encoding

Treating COVE/1 as a deterministic encoding of the selected PEMS object, with round-trip equality and repeated-byte checks, preserves semantic ownership in PEMS and avoids a second truth model.

### A7. Authority and lifecycle separation

Stage 1 correctly prohibits registration, authorization, activation creation, reconciliation, admission, canonical mutation, role mutation, and authority reinterpretation. This is consistent with the live RIL contracts.

### A8. Fixed production boundary

Stage 1 correctly refuses to make context packaging an invisible current `rd-distill prepare` discovery mechanism. A later production integration must be explicit, versioned, and separately reviewed.

### A9. Fail-closed and immutable-output posture

Stable failure classes, stale-state checks, exact replay, and collision refusal fit the repository's deterministic-executor posture.

### A10. Pressure cases before implementation

Freezing adversarial fixtures before semantic expansion is appropriate and should remain an implementation gate.

## Stage 1 disagreements and required revisions

The Stage 1 architecture is compatible, but the following issues are material enough that Stage 2 does not recommend implementation against the current proposal text without reconciliation and revision.

### R1. Prove admitted canonical standing, not merely PEMS validity plus a canonical-looking locator

**Severity: blocking before P1 schema freeze.**

The proposed request can name a `snapshot_locator` and `snapshot_digest`, and the resolver can validate exact PEMS bytes. That proves identity and PEMS validity. It does not by itself prove that the snapshot has admitted canonical standing for the project.

The live repository separates canonical bytes from admission plans/receipts and other lifecycle stores. The RIL admission contract makes admission the canonical mutation boundary. Therefore a schema-valid PEMS file with a correct digest cannot become knowledge-plane input merely because a request calls it canonical or points at a canonical-looking path.

Required change:

- Replace the loose concept of `snapshot_locator + snapshot_digest` as sufficient canonical evidence with a **canonical-state binding** supplied by the project-owned backend/package contract.
- The binding must identify the project, backend contract/type, immutable snapshot identity, semantic tuple, content digest, and whatever admission/backend evidence is required to establish that this snapshot is the admitted canonical state being consumed.
- Repository-local canonical files can be one backend implementation, but path naming must not be the generic proof of canonical standing.
- The builder may validate that existing binding read-only. It must not create admission evidence or infer admission from file placement.

This also resolves part of Stage 1 unresolved question 4 by making external backend identity an interface requirement rather than a later storage detail.

### R2. Define byte-preserving payload representation

**Severity: blocking before pack schema freeze.**

Stage 1 requires exact source bytes, canonical JCS metadata, and byte-identical replay, but it does not specify how arbitrary control or operational-evidence bytes are represented inside a JSON/JCS pack. Decoding files as text can normalize or reject bytes, alter newline sequences, or introduce Unicode normalization differences.

Required change:

- Define item payloads as byte strings with an explicit deterministic representation, for example base64 with a frozen alphabet/padding rule, or define a separate binary container with a canonical manifest.
- Hash original source bytes, not host-decoded text.
- Record media/content type only as metadata unless a contract explicitly requires text decoding.
- Specify whether text rendering normalizes anything. If rendering changes representation, retain the exact source-byte digest and make the transformation contract explicit.

### R3. Define digest domains and avoid self-referential pack identity

**Severity: blocking before pack schema freeze.**

The illustrative envelope contains a `digests` object while acceptance criteria require an output digest. A digest cannot naively cover bytes that contain that same digest value.

Required change:

- Define named digest domains, for example `manifest_digest`, `payload_digest`, and `pack_identity_digest`.
- State exactly which fields are included/excluded from each digest.
- Prefer an out-of-band build receipt for whole-file digest if necessary, or define a canonical preimage that excludes the self-reference field.
- Domain-separate hashes so the same bytes used in different protocol roles cannot be confused.

### R4. Separate profile existence from profile eligibility

**Severity: blocking for governed consumers; primitive schema may proceed only with the boundary explicit.**

Stage 1 correctly says a profile is not authority, but leaves profile governance unresolved. A deterministic primitive can faithfully execute a malicious or inappropriate profile. For a governed activation workflow, the consumer must have an explicit rule for which profile identity/digest is eligible for the task.

Required change:

- The packer validates profile bytes and compatibility only.
- The consuming governed workflow supplies or validates profile eligibility through an explicit contract/registry/policy input.
- Do not infer eligibility from repository path, filename, role label, latest version, or model-selected task similarity.
- Record both profile identity/digest and the eligibility-binding identity when the consumer requires one.

### R5. Give operational evidence an explicit validation-status model

**Severity: blocking before authority-sensitive profiles are accepted.**

Stage 1 deliberately avoids full authority validation and says downstream RIL primitives must revalidate. That separation is correct, but `required operational evidence` can otherwise be misread as `accepted operational evidence`.

Required change:

- Every operational-evidence item must carry an explicit status such as `carried_unvalidated`, `shape_and_digest_validated`, or a reference to a separately produced accepted validation result with its own immutable identity.
- The packer must never emit a generic boolean like `trusted`, `authorized`, or `activated` from artifact presence.
- If a profile requires an accepted validation result as a precondition, the exact validator contract and validation artifact must be an explicit source. The packer still does not perform the authority-bearing operation.
- Downstream RIL operations continue to revalidate as their own contracts require.

### R6. Make renderer trust-channel separation normative

**Severity: blocking before P9 rendering acceptance.**

Stage 1 correctly keeps planes separate in the pack, but plane separation can be destroyed during rendering. Admitted canonical knowledge can legitimately contain quoted instructions, role claims, adversarial text, or text such as `ignore prior controls`. Exact canonical standing does not make that text a control instruction.

Required change:

- The renderer contract must preserve plane boundaries in the activation material using a deterministic structural framing understood by the consumer.
- Knowledge and operational-evidence payloads must never be rendered into a control/instruction slot merely because their contents resemble instructions.
- The renderer must not parse authority-like prose and promote it.
- Add explicit injection/confused-deputy pressure cases before P9.

This is a semantic safety property, not a model-specific prompt-engineering heuristic.

### R7. Bind validation and builder toolchain identity sufficiently for replay

**Severity: required before reproducibility gate.**

Stage 1 records a `builder_contract` and calls package-owned PEMS/COVE logic, but the inspected backend does not expose separate `SCHEMA_VERSION` or `VALIDATOR_VERSION` files. A future replay can therefore use different executable validation semantics while claiming the same protocol name unless identities are bound more concretely.

Required change:

- Record immutable identities/digests for the PEMS schema, semantic validator contract/implementation, COVE encoder/decoder contract or implementation, closure descriptor, JCS implementation contract, and builder contract used for the build.
- A contract version may replace a code digest only when that version itself immutably fixes the relevant behavior.
- Reproducibility tests should replay with intentionally changed validator/toolchain components and require either identical contracted behavior or explicit incompatibility/failure.

### R8. Define total bounds, empty-result semantics, and render bounds separately

**Severity: required before limit schemas are frozen.**

Stage 1 covers closure record/byte/depth limits and later mentions rendering size policy, but a bounded activation protocol needs separate deterministic limits for source resolution, semantic projection, canonical pack bytes, and rendered activation bytes.

Required change:

- Define each limit domain and the point at which it is measured.
- Define whether an empty explicit selection is valid for a profile or fails with a stable code.
- Never truncate semantic closure or silently drop equal-priority items to fit a budget.
- If rendering cannot fit a valid pack under the selected rendering profile, fail deterministically or require a different explicit request/profile. Do not summarize or rank inside the renderer.

### R9. Make source-registry conflicts and snapshot consistency first-class

**Severity: required before external/multiplexed sources are supported.**

Stage 1 records multiple immutable source identities, but it does not fully specify conflict behavior when two descriptors claim the same logical source with different immutable identities, or when repository controls and canonical backend state are resolved at different moments without a declared relationship.

Required change:

- Define logical source identity separately from immutable snapshot identity.
- Reject conflicting bindings for the same logical source unless the profile explicitly models multiple snapshots.
- Let a profile require a cross-source consistency relation, and fail if that relation cannot be established.
- Do not silently pick the newest, first, or path-local source.

### R10. Specify side-effect and persistence boundaries for generated artifacts

**Severity: required before implementation writes files.**

Stage 1 says the primitive is read-only with respect to canonical state and asks whether packs are ephemeral or persisted. The implementation contract should go further before file-writing behavior is introduced.

Required change:

- Treat the pure build function as side-effect free.
- Define output persistence as a separate deterministic artifact-write operation with collision semantics.
- Generated pack or receipt locations must not live in admission, reconciliation, authorization, activation-evidence, or canonical stores unless a later governing contract explicitly defines that role.
- Caches must not be part of source discovery or successful semantic output, and cache presence/absence must not change pack bytes.

## Missing pressure cases

Stage 1 PC-01 through PC-30 provide a strong starting envelope. Add at least the following cases before P0 is considered complete.

| ID | Missing pressure case | Required outcome |
|---|---|---|
| PC-31 | Request points to a schema-valid PEMS/2 file with correct digest that is not proven as admitted canonical state | Reject as non-canonical/unproven canonical binding; path or request label is insufficient |
| PC-32 | Canonical PEMS bytes are present but the project/backend admission binding or receipt chain identifies a different snapshot | Fail stale/conflicting canonical-state validation |
| PC-33 | Admitted canonical proposition contains `ignore controls`, `act as Steward`, or other instruction-like text | Preserve as knowledge data; renderer must not promote it to control/instruction semantics |
| PC-34 | Exact control artifact contains CRLF, non-ASCII, non-UTF-8, or bytes that a text decoder would normalize/reject | Pack preserves exact source-byte identity through a specified byte representation or rejects unsupported media by explicit contract |
| PC-35 | Whole-pack digest field is included in its own hash preimage | Schema/algorithm makes self-reference impossible by a defined digest domain or out-of-band receipt |
| PC-36 | Same request and sources are replayed with a different PEMS validator/COVE encoder/closure descriptor | Toolchain identity mismatch is visible and either fails compatibility or uses explicitly compatible contracted behavior |
| PC-37 | Explicit selectors produce an empty knowledge set | Profile-defined deterministic empty-result rule applies; no model-driven fallback or broader search occurs |
| PC-38 | Profile/request contains an unknown selector, closure rule, or limit field | Fail closed under schema/version rules; do not ignore a field that could alter semantics |
| PC-39 | Host-local absolute path or temporary directory differs across machines | Local path does not enter canonical identity/rendered context unless explicitly contracted; replay remains environment-independent |
| PC-40 | Builder implementation attempts to update a cache, canonical PEMS/COVE, admission store, reconciliation store, or authority store during build | Pure build fails/tests detect side effect; semantic result is never contingent on mutation |
| PC-41 | External backend locator resolves once, then content changes or backend becomes unavailable before read | Immutable snapshot binding controls the read; change/missing snapshot fails, never silently re-resolves latest state |
| PC-42 | Two source descriptors claim the same logical source but bind different immutable digests | Reject conflict unless multi-snapshot semantics are explicitly part of the profile |
| PC-43 | Operational-evidence artifact has correct bytes/digest but is expired, invalidly bound, or otherwise not accepted by its RIL validator | Pack records carried/validation status without inferring acceptance; authority-bearing downstream operation revalidates |
| PC-44 | Canonical pack is valid but deterministic renderer exceeds its activation-byte limit | Renderer fails with stable limit result; it does not summarize, rank, or silently omit context |
| PC-45 | Same semantic text appears in control and knowledge sources under different identities | Preserve distinct source/plane identities; do not deduplicate by text similarity or content alone |
| PC-46 | Unicode normalization form, locale, path separator, dictionary insertion order, or filesystem order differs across hosts | Contracted canonical byte representation and ordering remain identical |

## Recommended changes to Stage 1 before implementation

For later reconciliation, the cleanest synthesis is to retain Stage 1's architecture but revise the protocol freeze sequence as follows:

1. **P0 pressure cases:** extend PC-01 through PC-30 with PC-31 through PC-46 above.
2. **P1a source identity:** freeze repository-source identity, project/backend canonical-state binding, operational-evidence identity, logical-source identity, and cross-source consistency rules.
3. **P1b protocol schemas:** freeze profile/request/pack/result/failure schemas with `additionalProperties: false` or equivalent fail-closed unknown-field behavior where semantics require it.
4. **P1c byte and digest contract:** freeze payload byte representation, JCS usage, digest algorithms/domains, toolchain identities, and whole-pack receipt semantics.
5. **P1d PEMS closure:** complete the field-by-field PEMS/2 closure descriptor and negative fixtures.
6. **P1e consumer/profile eligibility:** define the boundary by which a governed consumer binds an eligible profile identity/digest without turning the packer into an authority engine.
7. **P2 source resolver:** implement immutable resolution only after the above identities exist.
8. **P3 projection:** implement PEMS selection/closure and semantic validation.
9. **P4 COVE:** reuse/extract the package-owned deterministic encoding behind an explicit versioned interface and retain exact round-trip tests.
10. **P5 pure pack build:** build canonical manifest/payloads/ledger without persistence side effects.
11. **P6 persistence adapter:** optional immutable artifact write with collision behavior, outside authority/canonical lifecycle stores.
12. **P7 reproducibility:** include changed host environment and changed toolchain identity cases.
13. **P8 authority/memory isolation:** include operational-evidence status and non-promotion tests.
14. **P9 deterministic renderer:** require structural plane preservation and instruction-like-data pressure cases as well as size limits.
15. **P10 production integration:** remain a separate future reviewed contract, not an automatic consequence of P0-P9.

The numbering above is a Stage 2 recommendation, not an implementation authorization.

## Stage 1 unresolved questions: Stage 2 synthesis

### Q1. Declarative COVE/1 contract

**Stage 2 view:** unresolved, but it should be resolved before COVE becomes a public context-pack contract dependency. Reusing package-owned executable primitives is preferable to duplicate implementation. A stable declarative or otherwise immutable versioned interface should define exactly what `cove/1 | pems/2 | jcs/1` means for callers.

### Q2. Complete PEMS closure policy

**Stage 2 view:** blocking before PEMS projection implementation. Every semantically relevant ID-bearing PEMS/2 field must have a versioned closure rule: include transitively, preserve as an explicit external reference under a defined rule, or reject. Undefined means fail.

### Q3. Profile governance

**Stage 2 view:** separate eligibility from execution. The packer should not decide governance. Governed consumers must bind allowed profile identities/digests through explicit project or workflow policy.

### Q4. External canonical backend abstraction

**Stage 2 view:** promote this from a future convenience to part of V1 canonical-source identity. The primitive is supposed to consume admitted canonical project knowledge, so it needs a generic read-only canonical-state binding rather than repository-path semantics baked into the request.

### Q5. Production source-registry provenance

**Stage 2 view:** unresolved and correctly deferred from current production. A multiplexed pack must not erase original source identity. No native production integration should proceed until a versioned invocation/source-registry contract specifies how packed source provenance is addressed.

### Q6. Pack persistence

**Stage 2 view:** generated packs should default to derived operational artifacts with no canonical-memory standing. Persistence should be a separate immutable artifact-write layer. Any stronger evidence class requires its own contract and must not be inferred from storage location.

### Q7. Operational-evidence validation depth

**Stage 2 view:** carrying and accepting evidence must be mechanically distinguishable. V1 may remain decoupled from full RIL validation if it records `carried_unvalidated` or limited validation status explicitly. A profile that requires accepted validation must name the exact read-only validation artifact/contract rather than letting the packer infer authority.

### Q8. Rendering size policy

**Stage 2 view:** profile-specific explicit bounds are appropriate. Separate semantic-pack bounds from renderer bounds and fail rather than summarize or silently truncate.

## Additional unresolved questions introduced by Stage 2

1. What project-owned contract is the authoritative source of the canonical-backend binding for this repository? The current `project-knowledge/project.json` does not itself expose the full generic `project-knowledge-package/1` canonical-backend structure shown in `schemas/project-package.schema.json`.
2. What exact evidence chain establishes that an immutable PEMS snapshot is the admitted canonical state for a read-only consumer? The packer needs a validation contract, not an inferred path convention.
3. Should arbitrary control artifacts be supported as opaque bytes in V1, or should V1 intentionally support only UTF-8 text controls and fail all other media? Either choice can be deterministic, but it must be explicit.
4. What are the canonical hash domains and domain-separation labels for source bytes, request/profile objects, PEMS projection, optional COVE, manifest, whole pack, and build receipt?
5. Which package-owned artifacts are sufficient to identify the PEMS validator and COVE implementation semantics for replay if there is no standalone validator-version file?
6. What structural rendering contract guarantees that knowledge-plane text cannot become an instruction/control channel for a consumer while remaining provider-neutral?

## Disposition for later Steward reconciliation

**Stage 2 disposition: `COMPATIBLE_WITH_REQUIRED_REVISIONS`.**

The central Stage 1 architecture should be retained: explicit versioned intent, deterministic exact-source resolution, separate planes, PEMS-preserving semantic closure, outer selection provenance, optional lossless COVE encoding, strict read-only authority boundaries, and no silent production integration.

However, Stage 2 recommends that Steward reconciliation require R1 through R10, with R1 through R7 treated as protocol-freeze blockers, before approving implementation. In particular, the protocol must not accept a request-declared PEMS snapshot as admitted canonical knowledge without a project/backend canonical-state binding, and the pack schema must explicitly solve byte preservation and digest-domain semantics.

This is not project approval. It is an Engineer review recommendation for the next governance stage.

## Governance boundary and handoff

Stage 2 review/synthesis is complete at this artifact. The next consequential stage under `docs/governance/PROPOSAL_REVIEW_METHOD.md` is **Steward reconciliation** of Stage 1 plus this independent Stage 2 review.

The receiving Steward should independently verify required Steward authorization and accepted RIL activation/evidence as required by the live repository contracts before making any authority-bearing reconciliation decision. A fresh chat or isolated context is appropriate for that distinct governance role and decision boundary. Neither this handoff, a fresh chat, a role label, nor the existence of these proposal artifacts establishes Steward authority or activation.

Do not implement the protocol, mutate canonical PEMS/COVE, admit knowledge, or change current production `rd-distill` evidence behavior on the basis of this Stage 2 review alone.
