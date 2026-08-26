# P10 Production Integration - Stage 3 Steward Final Plan

Status: **APPROVED FOR IMPLEMENTATION WITH REQUIRED GATES**

Disposition: **`P10_PRODUCTION_INTEGRATION_STAGE3_RECONCILED_ACCEPTED_WITH_GATES`**

Method: `proposal-review-synthesis/1`

Repository: `loteque/reasoning-distiller`

Coordination control ref: `main`

Coordination revision resolved before consequential Stage 3 work and re-resolved immediately before this write: `80b6e89ad2efe84b088ca06b908a257c449fac15`

Semantic basis: P9 Steward reconciliation `1b1be8f60f2eef0ddc7a91a91c352cf4018012d3`

Closed P9 candidate: `cc14721725949a560b52f0a5d80808e95c2d6ad0`

P9 disposition: `P9_STEWARD_RECONCILIATION_ACCEPTED`

Governing context-packaging plan: commit `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`, blob `8474d2da42f863f0a190fd80292085176d3f97f0`

Governing P9 renderer-identity amendment: commit `373667be85521e6f0f83bf19fed3378357e51118`, blob `90142ffe6b6652faceb3e8347f33fa71c8dc3ed9`

Stage 1 proposal: commit `0a2909d5a88c9a7d8f7abbf1b2c59f2abd34b723`, blob `cd9dd25c9209dbb066e8017c2256f4647037dec7`

Stage 2 review/synthesis: commit `0b9ac2c4ce63e97e1fa1f185f352e7b1e0bc8513`, blob `00421e221f1b1ba6a852a235e1c3678150a08810`

Stage 2 disposition: `P10_PRODUCTION_INTEGRATION_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`

Stage: **Stage 3 Project Engineering Steward reconciliation**

## Authority and activation record

Operational role: `steward:default`.

Authority scope: `semantic_reconciliation`.

At exact coordination revision `80b6e89ad2efe84b088ca06b908a257c449fac15`, live project-owned Steward authorization assigns `semantic_reconciliation` to `steward:default`. No project role-registry override exists at that coordination revision, so the package-provided protected default Steward remains the available registry basis.

This bounded Stage 3 work uses the accepted `reasoning-distiller-role-activation/1` `explicit_declaration` method with:

```json
{"context":{"invocation_id":"chat-20260825-p10-stage3-steward-reconciliation","source":"chatgpt-project-chat:p10-stage3"},"contract":"reasoning-distiller-role-activation/1","method":"explicit_declaration","role_id":"steward:default"}
```

Canonical activation digest:

```text
sha256:7c82040a754dd340eb951a37d0f1be81cc7065a54256e4e69e7cf0dae3ddaefe
```

Validation against the live role and authorization state:

```text
PASS/ACTIVATION_ACCEPTED
scope: semantic_reconciliation
role_id: steward:default
invocation_id: chat-20260825-p10-stage3-steward-reconciliation
activation_digest: sha256:7c82040a754dd340eb951a37d0f1be81cc7065a54256e4e69e7cf0dae3ddaefe
```

This activation evidence is read-only and invocation-local. It does not register a role, mutate Steward authorization, activate admission, admit canonical knowledge, or persist activation state.

This document is the Stage 3 artifact required by `docs/governance/PROPOSAL_REVIEW_METHOD.md`. It is an authoritative proposal-review reconciliation and implementation plan. It is not a candidate-bound RIL reconciliation disposition under `docs/operations/RIL_RECONCILIATION_CONTRACT.md`, does not mutate the current `reasoning-distiller-invocation/1` production contract merely by existing, and does not itself perform P10 implementation.

## 1. Steward decision

Adopt the Stage 1 sealed-context `/2` production-integration direction **with every Stage 2 required revision R1-R8 incorporated as mandatory**.

The approved architecture has two independent identities that must never be collapsed:

```text
sealed context pack
    = the sole project-evidence root selected before production invocation

prepared invocation
    = the immutable identity of the exact installed production behavior,
      renderer execution, provenance registry, activation bundle, and
      logical provider transport selected for one prepare -> runner -> finalize flow
```

The sealed pack answers **what project evidence may be used**.

The prepared invocation answers **which exact production transformation is permitted to act on that evidence and which finalization is permitted to accept the returned raw candidate**.

Stage 1 is accepted as the architectural base for evidence sealing, explicit `/2` opt-in, deterministic provenance derivation, P9 plane preservation, raw-byte preservation, `rgp/1` continuity, immutable submission behavior, and authority isolation.

Stage 1 is not accepted where it relies on re-reading the three request inputs during `finalize` as sufficient prepare-to-finalize continuity, where a stable source ID is coupled to a pack-local ordinal locator, where provider transport is only a prose obligation, where package closure is deferred until after production integration, or where rollback is treated only as contract selection.

## 2. Input recommendations and Steward disposition

| Input | Recommendation | Steward disposition |
|---|---|---|
| Stage 1 RPG Engineer proposal | Adopt an explicit sealed-context `reasoning-distiller-invocation/2` using one prebuilt digest-bound `context-pack/2`, exact renderer profile `/2`, external eligibility `/1`, deterministic provenance IDs, preserved planes, unchanged raw-candidate/RGP submission semantics, explicit migration, and no ambient discovery | **Accepted as architectural base, subject to R1-R8 below** |
| Stage 2 independent Engineer review/synthesis | Retain the Stage 1 direction only with immutable prepared-invocation identity, durable provenance handoff, stable source identity separated from pack occurrence, transport conformance, exact P9 runtime compatibility, early package closure, frozen version/failure ownership, and stronger migration/rollback gates | **Accepted in full; R1-R8 are mandatory** |

There is no remaining disagreement over whether a sealed-context `/2` path is the correct direction.

There were material disagreements over how much identity and durability that path requires. Those disagreements are resolved below by rejecting the weaker Stage 1 forms and adopting the Stage 2 requirements. They are not described as prior consensus.

## 3. Stage 2 amendment reconciliation

### R1 - Prepared invocation identity

**Disposition: ACCEPTED.**

Freeze the public contract:

```text
reasoning-distiller-prepared-invocation/1
```

`prepare` must produce and immutably persist one exact prepared-invocation artifact before provider execution. The artifact must bind at least:

- invocation contract and invocation ID;
- canonical request digest/identity;
- exact context-pack file digest and validated pack identity;
- exact renderer-profile file digest and profile identity;
- exact eligibility artifact digest and decision identity;
- exact installed package `content_identity`;
- exact installed Distiller directive digest;
- exact installed RGP validator identity/digest;
- exact provenance-registry locator and digest/identity;
- exact P9 rendered-activation identity/digest;
- exact P9 renderer execution binding;
- exact accepted P9 runtime ABI;
- exact activation-bundle identity/digest;
- exact logical model-transport contract/version;
- exact selected transport-adapter identity when the adapter is outside the installed package content identity;
- a domain-separated prepared-invocation identity over the frozen semantic fields.

The persisted prepared invocation is an immutable derived production artifact outside canonical, admission, reconciliation, authorization, role, and activation-state stores.

`finalize` must receive and validate the exact prepared invocation. It must not establish continuity by re-reading only the request pack/profile/eligibility files or by trusting the current installation.

Installation, directive, validator, renderer, bridge, registry, activation-bundle, runtime, or transport identity drift from the prepared invocation fails closed.

A successful `/2` candidate is therefore bound to one exact prepared invocation.

### R2 - Durable provenance handoff

**Disposition: ACCEPTED, WITH OPTION A SELECTED AND FROZEN.**

The existing RGP submission envelope remains unchanged.

The exact `reasoning-distiller-context-provenance-registry/1` object is an immutable companion invocation artifact. `prepare` must persist it before provider execution.

A successful `/2` downstream Steward handoff is the following exact logical tuple:

```text
ordinary immutable RGP submission
+
reasoning-distiller-invocation-result/2
+
reasoning-distiller-prepared-invocation/1
+
reasoning-distiller-context-provenance-registry/1
```

`reasoning-distiller-invocation-result/2` must carry immutable locator plus digest/identity references to:

- the exact ordinary RGP submission;
- the exact prepared invocation;
- the exact provenance registry;
- the preserved raw candidate artifact.

For a `/2` candidate, a project Steward reconciliation entrypoint must receive the ordinary submission together with the exact successful result `/2` and must follow its prepared-invocation and provenance-registry references. It must verify the complete identity chain before resolving proposition provenance.

A `/2` ordinary submission presented without the required companion chain is **not a complete production handoff**. Reconciliation must stop with an explicit incomplete-provenance-handoff failure rather than searching repository HEAD, invocation directories, chat history, memory, current canonical state, or heuristics.

`source_context` remains operational context only and must not carry or stand in for the provenance registry.

Option B, a new RGP submission-envelope major, is not approved for initial P10. It becomes a new governance question only if Option A proves impossible to implement as a deterministic required Steward handoff.

### R3 - Stable source identity versus pack occurrence

**Disposition: ACCEPTED, WITH THE STAGE 1 PACK-ORDINAL LOCATOR MODEL REVISED.**

Keep the Stage 1 binding-derived production ID:

```text
binding_bytes = JCS(full reasoning-distiller-context-source-binding/1 object)

binding_sha256 = sha256(
    "reasoning-distiller-context-provenance-binding/1\0"
    || binding_bytes
)

source_id = "src:ctx:" + lowercase_hex(binding_sha256)
```

The provenance registry must separate:

1. **stable source records**, keyed by `source_id`, containing the source ID, exact `binding_sha256`, the exact immutable `reasoning-distiller-context-source-binding/1` object or equivalently complete canonical representation, exact source class, exact immutable source/snapshot identity, exact underlying payload digest, and all binding fields required for later project-policy provenance resolution;
2. **pack-local occurrences**, containing exact pack identity, exact plane, exact item/frame identity or index, and the stable `source_id`.

A pack identity, ordinal, frame index, or pack-local pseudo-locator is never part of the stable semantic meaning of a `source_id`.

Same complete binding bytes may occur in many packs and must yield the same `source_id` and semantically equivalent stable source record. Different binding bytes resolving to the same accepted source ID or conflicting stable source fields fail closed.

Every model-visible context frame must resolve to exactly one stable source ID before provider execution.

### R4 - Provider transport and plane preservation

**Disposition: ACCEPTED.**

Freeze the public logical contract:

```text
reasoning-distiller-model-transport/1
```

This contract is provider-neutral. It must define the logical mapping every conforming runner preserves, including:

- the installed Distiller directive remains the framework/protocol instruction surface defined by production invocation;
- the P9 rendered context remains explicit model evidence with structural `control`, `knowledge`, and `operational_evidence` labels intact;
- context `control` is project control evidence and is not automatically mapped to provider system/developer authority;
- knowledge and operational evidence cannot be promoted because their text resembles instructions;
- exact frame payload bytes and frame order are preserved;
- the provenance registry source IDs and frame mappings are preserved exactly;
- no project facts, prior chats, prior candidates, canonical interpretations, memory, hidden evidence, or unrelated repository state are added;
- the runner is bound to the exact prepared-invocation identity it received;
- a provider representation that cannot preserve the logical distinction fails before a valid `/2` result may be claimed.

The contract may define an out-of-band deterministic transport receipt that echoes the exact prepared-invocation and activation-bundle identities used by the runner. Such a receipt is consistency evidence, not cryptographic attestation.

P10's accepted threat model is a non-hostile/reference runner plus deterministic conformance testing. P10 does not claim detection of a malicious provider or runner that lies about what it transmitted. Stronger hostile-runner assurance is outside this P10 plan and requires a separately governed execution/attestation design.

### R5 - P9 runtime ABI compatibility

**Disposition: ACCEPTED.**

The initial `/2` support matrix is pinned to the exact accepted P9 execution ABI proven by the closed P9 evidence:

```text
implementation: cpython
version: 3.12.0
cache tag: cpython-312
binding scheme: python-closed-bundle/1
```

P10 must invoke the P9 renderer without broadening the P9 execution boundary.

`prepare` must fail closed before provider execution when the executing runtime is outside that exact accepted tuple.

CPython 3.12.1, 3.13.x, patch-floating `3.12`, another interpreter, or an unproven runtime equivalence is unsupported for initial `/2`.

Broader runtime support requires separately governed P9 compatibility evidence or amendment. P10 implementation may not declare nearby runtimes equivalent for production convenience.

### R6 - Installed-package closure

**Disposition: ACCEPTED. PACKAGE CLOSURE MOVES BEFORE PROVENANCE/PREPARE IMPLEMENTATION.**

The current release package managed roots do not include `context_packaging`. Therefore the current installed Reasoning Distiller `0.5.3` surface is not sufficient for native `/2`.

Before P10 behavior implementation proceeds beyond protocol freeze, the deterministic release/install surface must be changed so that package `content_identity` binds the complete P9/P10 behavior required by `/2`, including:

- the exact accepted P9 renderer and required closed-bundle resources;
- P10 invocation `/2` runtime;
- provenance-bridge logic;
- provenance-registry schema and serializer;
- prepared-invocation schema and identity logic;
- activation-bundle `/2` logic;
- invocation-result `/2` logic;
- logical model-transport contract and any package-owned reference adapter;
- required context schemas/resources;
- installed Distiller directive;
- installed RGP validator;
- all behavior-bearing helpers required by the `/2` path.

`context_packaging` may become a managed root, or the exact required P9 surface may move into another explicitly managed root without semantic change. Either way, the deterministic manifest must close over all required behavior.

The package builder and installer must prove generic source-repository absence does not affect successful installed `/2`, package replacement between prepare/finalize is detected through R1, explicit downgrade installs exactly the older manifest payload without orphan P10/P9 managed files, and package content identity changes when any bound behavior changes.

A release version/content identity change is required to ship P10. The exact release version number remains release-governance owned and is not invented by this Stage 3 plan.

### R7 - Versioning and failure ownership

**Disposition: ACCEPTED.**

The approved initial public P10 contract family is:

```text
reasoning-distiller-invocation/2
reasoning-distiller-activation-bundle/2
reasoning-distiller-invocation-result/2
reasoning-distiller-context-provenance-registry/1
reasoning-distiller-prepared-invocation/1
reasoning-distiller-model-transport/1
```

The required P0-P9 compatibility floor is:

```text
context pack:        reasoning-distiller-context-pack/2
renderer profile:    reasoning-distiller-context-renderer-profile/2
rendered activation: reasoning-distiller-context-rendered-activation/2
renderer binding:    reasoning-distiller-renderer-execution-binding/1
binding scheme:      python-closed-bundle/1
eligibility:         reasoning-distiller-context-profile-eligibility/1
candidate:           rgp/1
submission:          existing RGP Submission Protocol semantics
```

The following are explicitly not changed by this Stage 3 artifact: `reasoning-distiller-invocation/1`, `reasoning-distiller-activation-bundle/1`, `reasoning-distiller-invocation-result/1`, `rgp/1`, the generic RGP Submission Protocol envelope, and the current production invocation contract's `/1` semantics.

Unknown major contracts fail rather than downgrade, coerce, or auto-upgrade.

Failure-class ownership is frozen as:

| Exit | Class | P10 ownership |
|---:|---|---|
| `2` | preflight | malformed/unsafe request, input/path/digest mismatch, unsupported context/profile/eligibility contract, ineligible/mismatched profile, unsupported installed contract set, missing package closure, exact runtime ABI incompatibility discovered before rendering |
| `3` | activation | P9 execution-binding mismatch, renderer/activation-limit failure, inability to construct exact activation from a valid request/toolchain, logical transport nonconformance before model output |
| `4` | parse | invalid raw UTF-8/JSON after exact raw preservation |
| `5` | validation | invalid `rgp/1`, unresolved source ID, provenance-registry mismatch discovered after raw output, or candidate provenance outside the exact prepared registry |
| `6` | persistence | immutable raw/prepared/registry/submission/result collision or write failure |
| `1` | internal | unexpected implementation failure not belonging to a frozen fail-closed semantic state |

Exact reason-code tokens must be frozen at P10-G1. Existing reason codes must be reused when their semantics are already exact. New tokens may be introduced only for genuinely new P10 states. The semantic states above may not be reassigned during implementation.

When model output exists, raw candidate bytes are preserved before parse, RGP, or provenance rejection.

### R8 - Migration and rollback

**Disposition: ACCEPTED.**

Three different compatibility operations must remain distinct:

1. **Legacy `/1` request under a P10-capable package:** `/1` request validation, activation-bundle `/1`, source-registry behavior, deterministic mechanics, raw preservation, result contract, submission envelope, reason classes, and exit semantics remain unchanged for fixed inputs. Context files present in the project do not affect `/1`.
2. **Contract-selective rollback under a P10-capable package:** callers explicitly choose `/1`; `/2` artifacts remain immutable history; no conversion, deletion, reinterpretation, or canonical rewriting occurs.
3. **Package downgrade:** downgrade is explicit under the installer/update contract; the resulting installed tree equals the older deterministic manifest; no orphan P10/P9 managed file may continue to influence `/1`; an older `/1`-only runtime receiving `/2` fails unsupported rather than approximating it.

No automatic migration scans, context-pack discovery, legacy request rewriting, or contract coercion are permitted.

## 4. Approved architecture

```text
explicit governed source/profile/eligibility selection
                    |
                    v
           accepted P0-P9 pack build
                    |
                    v
     immutable context-pack/2 + profile/2
              + eligibility/1
                    |
                    v
          invocation/2 request
                    |
                    v
                 prepare
        validate exact request inputs
        validate exact installed package identity
        validate exact P9 runtime ABI
        render through closed P9 renderer
        derive stable provenance registry
        persist exact provenance registry
        build activation-bundle/2
        persist prepared-invocation/1
                    |
                    v
      model-transport/1 conforming runner
        bound to prepared invocation
                    |
                    v
           exact raw rgp/1 bytes
                    |
                    v
                 finalize
       consume exact prepared invocation
       verify exact registry and toolchain identity
       preserve raw bytes immutably first
       parse and validate rgp/1
       resolve candidate provenance against
           exact persisted prepared registry
       persist ordinary immutable RGP submission
       emit invocation-result/2 bound to:
           raw + submission + prepared + registry
                    |
                    v
                   STOP
                    |
                    v
 separately authorized Steward reconciliation
 receiving the complete /2 companion handoff
```

The pack build remains outside `rd-distill prepare`. No original source represented by the pack is reopened by `/2`.

The context pack is the sole **project-evidence root**. The renderer profile, eligibility binding, installed framework artifacts, provenance registry, prepared invocation, and transport metadata are explicit operational/toolchain inputs and do not become proposition evidence merely because they are required to execute production.

## 5. Ownership and authority boundaries

| Concern | Owner/boundary |
|---|---|
| Root source/profile selection | Explicit upstream governed workflow or caller before `/2` |
| Profile eligibility | Existing governed eligibility producer; `rd-distill` consumes, never creates or infers |
| Context-pack build and source binding | Accepted P0-P9 context-pack contracts |
| Renderer plane semantics and execution identity | Closed P9 renderer `/2` and execution-binding contract |
| Invocation `/2` prepare/finalize mechanics | P10 production adapter implementation under this plan |
| Stable provenance derivation | P10 deterministic bridge from exact pack bindings |
| Provenance standing/truth | Underlying source binding plus later project Steward policy; source ID spelling grants none |
| Installed behavior identity | Deterministic release package and installation content identity |
| Provider transport mapping | `reasoning-distiller-model-transport/1` conforming adapter |
| Raw model output | Provider returns bytes; framework preserves unchanged |
| RGP meaning/validation | Existing `rgp/1` and installed validator |
| Candidate submission | Existing immutable RGP Submission Protocol envelope |
| `/2` provenance handoff | `invocation-result/2` + prepared invocation + provenance registry companion chain |
| Semantic reconciliation | Separately authorized activated Steward after production STOP |
| Admission/canonical mutation | Separate governed operations; never P10 prepare/runner/finalize |

P10 does not create role authority, activation, canonical standing, admission approval, or reconciliation authority. Plane membership does not create provider authority. Eligibility does not create canonical standing. Package identity does not create project authority. A successful `/2` invocation creates an immutable candidate handoff only.

## 6. Approved invariants

1. **Explicit `/2` selection:** `/2` runs only because the request contract explicitly names `/2`.
2. **Legacy isolation:** `/1` remains behaviorally unchanged.
3. **Sealed evidence:** one validated digest-bound `context-pack/2` is the sole project-evidence root.
4. **Prebuilt pack:** pack construction occurs before production invocation.
5. **No original-source re-resolution:** `/2` never reopens original sources represented by the pack.
6. **No ambient discovery:** repository search, canonical lookup, Project memory, chat history, prior candidates, caches, network discovery, or hidden reasoning cannot add project evidence.
7. **Explicit eligibility:** exact external eligibility is mandatory and never inferred by `rd-distill`.
8. **P9 plane preservation:** control, knowledge, and operational evidence remain structural through the prepared model boundary.
9. **No text promotion:** instruction-shaped knowledge or operational evidence cannot become control because of text shape.
10. **No provider-authority promotion:** context `control` is not automatically provider system/developer authority.
11. **Stable source identity:** source IDs derive only from complete canonical context source bindings.
12. **Occurrence separation:** pack/frame location is separate from stable source identity.
13. **Provenance closure:** every model-visible frame maps to exactly one stable source ID before execution.
14. **Durable provenance:** the exact registry is persisted and normatively handed downstream.
15. **Prepared identity:** exact request, sealed inputs, installed behavior, directive, validator, registry, P9 activation/binding/runtime, activation bundle, and transport contract are bound before provider execution.
16. **No current-install reconstruction:** `finalize` consumes prepared identity rather than trusting current files to reproduce it.
17. **Toolchain drift fail closed:** package/directive/validator/bridge/registry/renderer/activation drift cannot yield ordinary `/2` success.
18. **P9 runtime honesty:** only exact accepted CPython 3.12.0 / `cpython-312` is initial production support.
19. **Installed isolation:** complete `/2` path works from installed package with generic repository unavailable.
20. **Raw-byte preservation:** exact model bytes are persisted before parse/RGP/provenance rejection.
21. **No candidate repair:** P10 never edits returned graph semantics into success.
22. **Ordinary RGP continuity:** successful candidate remains `rgp/1` in existing immutable submission envelope.
23. **Companion handoff requirement:** `/2` submission alone is insufficient for downstream provenance resolution.
24. **No source_context provenance:** `source_context` is never repurposed as proposition provenance or registry transport.
25. **No authority creation:** pack inclusion, plane membership, eligibility, renderer success, package identity, or structural validity grants no role authority or activation.
26. **No canonical mutation:** build, prepare, render, bridge, transport, finalize, and submission do not mutate PEMS/COVE canonical state.
27. **Production STOP:** successful `/2` completion stops before reconciliation or admission.
28. **Fail-closed versioning:** unsupported majors are rejected, never coerced.
29. **Immutable artifacts:** different existing raw/prepared/registry/submission/result bytes are never overwritten.
30. **Deterministic mechanics:** fixed request bytes, installed behavior identity, sealed inputs, and frozen transport mapping produce the same deterministic prepared artifacts even though the reasoning model itself may vary.

## 7. Public contract and compatibility matrix

The Stage 3-approved public P10 family is exactly:

```text
reasoning-distiller-invocation/2
reasoning-distiller-activation-bundle/2
reasoning-distiller-invocation-result/2
reasoning-distiller-context-provenance-registry/1
reasoning-distiller-prepared-invocation/1
reasoning-distiller-model-transport/1
```

P10-G1 must freeze closed-world schemas, canonical serialization, digest domains, field sets, and negative fixtures for those contracts before behavior implementation.

Initial compatibility is intentionally narrow:

| Surface | Accepted |
|---|---|
| Invocation | `reasoning-distiller-invocation/2` |
| Context pack | `reasoning-distiller-context-pack/2` |
| Renderer profile | `reasoning-distiller-context-renderer-profile/2` |
| Rendered activation | `reasoning-distiller-context-rendered-activation/2` |
| Renderer execution binding | `reasoning-distiller-renderer-execution-binding/1` |
| Binding scheme | `python-closed-bundle/1` |
| Runtime ABI | CPython `3.12.0`, cache tag `cpython-312` |
| Eligibility | `reasoning-distiller-context-profile-eligibility/1` |
| Candidate | `rgp/1` |
| Submission | existing RGP Submission Protocol envelope plus required P10 companion handoff |

Context pack `/1`, renderer profile `/1`, unsupported P9 ABI tuples, unknown P10 majors, and automatic `/1` to `/2` conversions are rejected.

## 8. Prepared-invocation identity model

The prepared invocation is a first-class immutable artifact, not a cache.

Its identity must be derived from a frozen canonical semantic object. Exact schema bytes and digest domain are P10-G1 freeze items, but the semantic preimage is fixed by this plan and may not omit:

```text
invocation identity
canonical request identity
pack file digest + pack identity
renderer-profile file digest + profile identity
eligibility file digest + decision identity
installed package content identity
Distiller directive digest
RGP validator identity/digest
provenance registry locator + digest/identity
P9 rendered activation digest/identity
P9 renderer execution binding
P9 accepted runtime ABI
activation-bundle digest/identity
model-transport/1 contract identity
selected transport-adapter identity when not package-bound
```

`prepare` persists the registry and prepared invocation before provider execution. A conforming runner receives the exact activation bundle together with exact prepared-invocation identity. `finalize` receives the exact prepared-invocation artifact and verifies all identity-bearing artifacts needed for the accepted non-hostile/reference runner model.

The prepared invocation does not prove cryptographic provider honesty. It proves deterministic orchestration continuity and prevents current-install/current-file reconstruction from silently substituting a different production transformation.

## 9. Provenance durability model

`reasoning-distiller-context-provenance-registry/1` is both the exact validation set for candidate provenance IDs and the durable resolver metadata handed to the later Steward.

Its stable records retain enough of each exact context-source binding to permit project-policy source resolution without reopening ambient invocation state. Its occurrence section proves which source ID backs every model-visible frame in the exact pack/rendered activation.

The registry is immutable, digest-bound, and referenced by both prepared invocation and result `/2`.

The successful result `/2` is the downstream anchor linking:

```text
submission
<-> raw candidate
<-> prepared invocation
<-> provenance registry
```

The later Steward verifies the chain before semantic reconciliation. No file search is an accepted provenance resolver for `/2`.

## 10. Provider-transport boundary

`reasoning-distiller-model-transport/1` freezes logical semantics, not one vendor API.

A conforming provider adapter must prove, through fixtures/reference tests, that every prepared frame is transmitted exactly once and in order; frame payload bytes are unchanged; logical plane labels remain reconstructible and are not collapsed by text heuristics; framework directive material remains distinct from project context; context `control` is not assigned stronger provider privilege merely because it is control; knowledge and operational evidence remain data/evidence even when instruction-shaped; provenance registry IDs and frame mappings are not rewritten; no extra project context is added; returned raw model bytes are passed unchanged to finalization; and the run is explicitly associated with exact prepared-invocation identity.

At least one provider/reference-runner mapping must pass conformance before `/2` can claim production support. Other providers are unsupported until their mapping passes the same contract.

Hostile-provider cryptographic attestation is outside the approved P10 threat model.

## 11. Package and installation closure

The live package build at the Stage 3 coordination revision currently manages:

```text
admission
agents
backends
protocols
runtime
schemas
validators
```

and does not manage `context_packaging`.

That current surface is insufficient for `/2`.

P10-G2 must establish a deterministic installed closure that contains all required P9/P10 behavior and resources. Package content identity must be part of every prepared invocation.

Package/install tests must prove build manifest includes all required behavior; installed `/2` succeeds with generic source repository absent; package change after prepare causes finalization failure; explicit downgrade removes all P10/P9 managed artifacts absent from older manifest; fixed `/1` behavior remains unaffected under the new package; and an old package rejects `/2` rather than partially executing it.

The exact future release version is not decided here.

## 12. Failure classes

The current production exit classes remain the public classification skeleton.

### Preflight / exit 2

Occurs before successful rendering/provider execution for malformed `/2` request, unsafe or unresolved input paths, pack/profile/eligibility digest or identity mismatch, unsupported pack/profile/eligibility contract, missing/ineligible eligibility, profile/pack/consumer mismatch, unsupported installed contract set, incomplete installed package closure, unsupported exact P9 runtime ABI, or invalid prepared output configuration discoverable before activation.

### Activation / exit 3

Occurs before valid model output for P9 renderer execution-binding mismatch, P9 rendering incompatibility, activation byte-limit failure, inability to build exact activation bundle from an otherwise valid request/toolchain, provider adapter inability to preserve `model-transport/1`, or runner/prepared identity mismatch before a model result is accepted.

### Parse / exit 4

Occurs after raw preservation when returned bytes cannot be parsed as required raw JSON.

### Validation / exit 5

Occurs after raw preservation for invalid `rgp/1`, candidate provenance ID absent from exact prepared registry, registry artifact mismatch with prepared digest, or provenance collision/inconsistency discovered during candidate validation.

### Persistence / exit 6

Occurs for immutable raw, provenance-registry, prepared-invocation, submission, or result write collision/failure.

### Internal / exit 1

Reserved for unexpected implementation failures after all frozen semantic failures have stable classifications.

P10-G1 freezes exact reason-code tokens and must reuse existing codes when semantics already match.

## 13. Migration and rollback rules

Migration is additive and per invocation. No package installation, context-pack presence, filename, profile presence, or directory layout may auto-select `/2`. A caller chooses `/2` only by submitting `reasoning-distiller-invocation/2`.

A caller may continue to choose `/1` under a P10-capable package. `/2` artifacts are immutable history and are not rewritten when a caller later chooses `/1`.

Package downgrade is a separate installer operation and must restore exact older managed manifest without orphan P10/P9 behavior. An older runtime that does not support `/2` fails unsupported. No automatic downgrade or best-effort execution exists.

## 14. Frozen pressure cases

Stage 1 PI-01 through PI-40 and Stage 2 PI-41 through PI-60 are adopted unchanged as mandatory P10 pressure cases by immutable reference to the exact Stage 1 and Stage 2 commits/blobs identified at the top of this document. Their expected outcomes are frozen by those artifacts and may not be weakened or reinterpreted during implementation.

For implementation indexing, the mandatory set covers all of these classes:

- PI-01 through PI-14: deterministic replay, sealed-input validation, eligibility, context-version rejection, renderer-profile matching, stale binding, exact runtime ABI;
- PI-15 through PI-22: stable source identity, snapshot distinction, collision failure, frame-to-source closure, candidate provenance closure, no authority remapping;
- PI-23 through PI-31: trust-channel/plane preservation, activation bounds, ambient-memory isolation, strict `/2` schema, provider evidence broadening and flattening rejection;
- PI-32 through PI-40: installed isolation, `/1` non-interference, prepare/finalize input drift, raw preservation, immutable collisions, authority-store nonmutation, invocation identity, old-runtime rejection;
- PI-41 through PI-48: package/toolchain/directive/validator/prepared-bundle drift, stable source records across packs, conflicting registry records, mandatory downstream companion provenance handoff;
- PI-49 through PI-54: provider authority promotion, flattening, conforming provider-specific representation, exact CPython 3.12.0 enforcement, package closure, no generic-repository fallback;
- PI-55 through PI-60: `/1` non-interference under new package, true package downgrade, raw-first failure behavior, exact registry digest enforcement, byte-restored input identity, explicit hostile-runner threat-model limit.

No pressure case may be weakened to accommodate implementation. Additional implementation-discovered boundary cases must be added before affected behavior is accepted, but may not replace or relax PI-01 through PI-60.

## 15. Ordered implementation plan and gates

| Gate | Required work | Exit criterion |
|---|---|---|
| **P10-G0 Threat/pressure freeze** | Materialize PI-01 through PI-60 with stable PASS/FAIL outcomes, failure classes, and explicit non-hostile-runner threat assumptions | All current attacks are executable or mechanically checkable before production behavior changes |
| **P10-G1 Protocol/handoff freeze** | Freeze closed-world schemas and canonical identities for invocation `/2`, activation-bundle `/2`, result `/2`, registry `/1`, prepared-invocation `/1`, model-transport `/1`, exact downstream companion-handoff rules, digest domains, exact reason codes, and compatibility matrix | No prepare/finalize identity, provenance durability, transport mapping, or failure ownership remains implicit |
| **P10-G2 Installed-package closure** | Close deterministic package/install surface over exact P9/P10 runtime/resources; bind package identity; pin exact CPython 3.12.0 / `cpython-312`; prove generic-repository isolation and downgrade cleanup | Installed package is a complete `/2` execution surface before bridge/prepare implementation |
| **P10-G3 Provenance bridge** | Implement stable binding-derived source IDs, complete stable source records, pack-local occurrences, registry identity, immutable registry persistence | Every frame resolves exactly; same ID cannot map to conflicting stable records; registry is durable |
| **P10-G4 Prepare integration** | Validate sealed inputs/package/runtime/eligibility/P9 binding; derive registry; render; build activation bundle; persist exact prepared invocation | Pack is sole project-evidence root and exact production identity is frozen before provider execution |
| **P10-G5 Provider transport conformance** | Implement/reference-test `model-transport/1` mapping and at least one conforming runner path bound to prepared identity | Exact frames/order/non-promotion preserved; unsupported providers fail |
| **P10-G6 Finalize integration** | Consume exact prepared invocation; verify registry/toolchain/transport continuity; preserve raw first; parse/validate RGP/provenance; persist ordinary submission and result `/2` companion links | Candidate is bound to exact prepared invocation; no current-file/toolchain substitution succeeds |
| **P10-G7 Legacy/migration/rollback** | Prove `/1` non-interference, explicit `/2` opt-in, contract-selective rollback, explicit package downgrade, old-runtime `/2` rejection, and no orphan behavior | No silent migration, legacy drift, or partial downgrade |
| **P10-G8 Candidate-bound evidence** | Run complete P10 suite plus unaffected production `/1` and P0-P9 regressions on one immutable candidate/package/runtime tuple | Exact candidate/package/runtime-bound evidence exists |
| **P10-G9 Fresh independent implementation review** | Fresh independent Engineer challenges exact P10 candidate and bound evidence, including PI-01 through PI-60, package closure, `/1` compatibility, prepared identity, and provenance handoff | `P10_INDEPENDENT_REVIEW_PASS` or equivalent exact PASS; blockers return to implementation |
| **P10-G10 P10 Steward closure** | Fresh activated Steward reconciles only exact implementation candidate against independent PASS evidence and this final plan | P10 may be closed only here; no admission/canonical mutation is implied |

G0, G1, and G2 are prerequisites to provenance/prepare/finalize behavior implementation.

Implementation must not silently revise a frozen architecture fact discovered to be wrong. A material contradiction with this plan returns to governance.

## 16. Definition of done

P10 is not complete merely because `/2` can call a model.

Durable candidate-bound evidence must prove all of the following:

- Stage 3 public contract family is frozen exactly as approved;
- PI-01 through PI-60 have stable expected outcomes and pass;
- `/1` remains behaviorally unchanged under the P10-capable package;
- `/2` is explicit opt-in and rejects unknown/legacy context majors rather than translating them;
- one exact `context-pack/2` is sole project-evidence root;
- original sources represented by pack are never reopened by `/2`;
- profile eligibility is exact, external, and mandatory;
- P9 renderer `/2` preserves structural planes and exact accepted execution binding;
- initial runtime support is exactly CPython 3.12.0 / `cpython-312`;
- installed package content identity closes over complete P9/P10 behavior surface;
- generic source repository absence does not affect installed `/2`;
- deterministic source IDs derive from complete source-binding bytes;
- stable source records are independent of pack ordinals;
- every rendered frame resolves to exactly one source ID;
- provenance registry is immutable, persisted, digest-bound, and downstream-resolvable;
- prepared invocation binds complete request/input/toolchain/renderer/registry/activation/transport identity;
- finalization consumes exact prepared identity rather than reconstructing from current files;
- package/directive/validator/bridge/registry/runtime drift fails closed;
- provider transport preserves exact logical planes, bytes, order, and non-promotion semantics;
- at least one conforming runner path is proven;
- no hostile-runner cryptographic guarantee is falsely claimed;
- raw model bytes persist before parse/RGP/provenance failure;
- invalid output is never repaired into a submission;
- successful output remains an ordinary immutable `rgp/1` candidate submission;
- successful result `/2` durably links raw, submission, prepared invocation, and provenance registry;
- a `/2` submission without its required companion chain cannot be reconciled by ambient search;
- `source_context` is not proposition provenance;
- prepare/runner/finalize do not reconcile, admit, activate, authorize, or mutate canonical/authority state;
- package downgrade restores exact older manifest with no behavior-affecting P10/P9 orphans;
- exact candidate/package/runtime-bound evidence exists;
- fresh independent implementation review passes;
- a later fresh Steward performs candidate-bound P10 closure.

## 17. Resolved disagreement and remaining uncertainty

### Resolved against the weaker Stage 1 form

1. **Prepare/finalize continuity:** re-reading only pack/profile/eligibility is insufficient. Prepared-invocation identity is mandatory.
2. **Provenance durability:** deterministic re-derivation alone is insufficient for downstream Steward resolution. Exact registry persistence and companion handoff are mandatory.
3. **Stable locator semantics:** a pack ordinal cannot define stable source identity. Occurrence metadata is separate.
4. **Provider transport:** prose-only semantic preservation is insufficient. `model-transport/1` is mandatory.
5. **Runtime compatibility:** generic or patch-floating Python support is rejected for initial `/2`. Exact P9 ABI is mandatory.
6. **Package ordering:** package closure after prepare/finalize implementation is rejected. Closure moves to G2.
7. **Rollback:** contract selection alone is not package downgrade. All three compatibility cases must pass.

### Remaining, intentionally gate-owned or out-of-scope facts

1. **Exact schema field spellings and digest preimages** for the six P10 contracts are G1 freeze items. Their required semantics are fixed by this plan.
2. **Exact stable reason-code tokens** are G1 freeze items and must reuse existing codes where exact.
3. **Exact release version number** is release-governance owned. A version/content-identity change is required, but this plan does not invent the number.
4. **Provider-specific mappings beyond the first conforming reference path** remain unsupported until independently shown conforming.
5. **Hostile-provider/runner attestation** is outside current P10 threat model.
6. **Broader P9 runtime ABI support** is outside P10 and requires separately governed P9 compatibility evidence/amendment.
7. **Option B submission-envelope versioning** remains unapproved and unnecessary unless frozen Option A companion handoff proves impossible.

These uncertainties are not implementation permission to guess past a failed gate.

## 18. Exact next authorized action

The next authorized action after this Stage 3 reconciliation is:

> **Fresh Reasoning Graph Protocol / implementation Engineer: use exact closed P9 candidate `cc14721725949a560b52f0a5d80808e95c2d6ad0` as the semantic code base, bind this P10 Stage 3 final-plan commit as the governing production-integration plan, and begin P10-G0 only by materializing PI-01 through PI-60 with stable expected outcomes, failure classes, and the explicit non-hostile-runner threat boundary. Then freeze P10-G1 and establish P10-G2 package closure in the ordered sequence above before implementing the provenance bridge, prepare, transport, or finalize behavior. Do not begin admission, canonical mutation, authority mutation, role registration, or activation-state mutation.**

The proposal/review history branch is governance evidence. It is not the semantic code base merely because it contains this plan.

This Stage 3 activation does not begin the Engineer work unit.

## 19. Final Steward disposition and terminal boundary

**`P10_PRODUCTION_INTEGRATION_STAGE3_RECONCILED_ACCEPTED_WITH_GATES`**

Stage 1's sealed-context `/2` core direction is accepted.

Stage 2's `P10_PRODUCTION_INTEGRATION_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS` is reconciled by accepting every required revision R1-R8, selecting Option A for durable provenance handoff, freezing the prepared-invocation and provider-transport identity layers, preserving exact P9 runtime compatibility, moving package closure before production behavior implementation, and strengthening compatibility/rollback gates.

No P10 implementation, current `/1` production-contract mutation, admission, canonical mutation, role registration, Steward-authorization mutation, authority mutation, or activation-state mutation is performed by this Stage 3 reconciliation.

The P10 Stage 3 bounded work unit is complete only when this final plan is durably committed unchanged.

At that point a terminal chat/workflow boundary is reached. The next consequential work belongs to the fresh implementation Engineer described in Section 18 and must not begin in this Steward activation.
