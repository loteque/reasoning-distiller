# P10 Production Integration - Stage 1 RPG Engineer Proposal

Status: **Proposed**

Method: `proposal-review-synthesis/1`

Repository: `loteque/reasoning-distiller`

Coordination control ref: `main`

Coordination revision inspected and re-resolved before this Stage 1 write: `80b6e89ad2efe84b088ca06b908a257c449fac15`

Semantic basis for this proposal: P9 Steward reconciliation `1b1be8f60f2eef0ddc7a91a91c352cf4018012d3`

Closed P9 candidate: `cc14721725949a560b52f0a5d80808e95c2d6ad0`

P9 Engineer evidence: `a2d1ee4af973bc44d80d60f19c54d391b51f9aa2`

P9 independent review: `d7b123570ef56ba8e0d9468cbcb0d4216d6f6c6c`

P9 disposition: `P9_STEWARD_RECONCILIATION_ACCEPTED`

Governing context-packaging plan: commit `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`, blob `8474d2da42f863f0a190fd80292085176d3f97f0`

Governing P9 renderer-identity amendment: commit `373667be85521e6f0f83bf19fed3378357e51118`, blob `90142ffe6b6652faceb3e8347f33fa71c8dc3ed9`

Stage: **Stage 1 independent proposal**

Proposal-author scope: **Reasoning Graph Protocol Engineer**

Authority posture: this artifact is a technical proposal only. The Engineer directive permits protocol and framework design but does not confer Project Steward authority, canonical semantic identity, admission authority, or RIL authority. No Steward or RIL activation is claimed by this Stage 1 artifact. This proposal does not authorize P10 implementation, production behavior changes, admission, canonical mutation, authority mutation, or activation mutation.

## 1. Problem and decision requested

P0 through P9 established a deterministic context-packaging pipeline whose final renderer preserves structural control, knowledge, and operational-evidence planes and binds the behavior actually executed by the renderer. P9 is closed for exact candidate `cc14721725949a560b52f0a5d80808e95c2d6ad0` under the evidence chain named above.

The current production `rd-distill` contract, `reasoning-distiller-invocation/1`, predates native context packs. Its model-side evidence consists of the installed Distiller directive plus an explicit list of project-local evidence files, a caller-supplied source registry, and optional source context. The evidence list is fixed before model activation, and `rd-distill` must not silently add project state, prior candidates, canonical interpretations, memory, or hidden reasoning.

The governing context-packaging plan deliberately left P10 unapproved until P0 through P9 had durable evidence. The decision now requested is:

> Define the narrowest production integration architecture that allows `rd-distill` to consume a deterministic P0-P9 context pack natively while preserving the fixed production evidence boundary, exact provenance resolution, renderer plane separation, raw candidate preservation, RGP validation, immutable submission behavior, legacy compatibility, and all authority and canonical-state boundaries.

The architecture must make it impossible for native context integration to become an implicit evidence-discovery channel.

## 2. Governing observations and constraints

### 2.1 Current production boundary

The current production contract fixes these semantics:

1. `rd-distill` is the stable operation.
2. `prepare` validates fixed inputs and emits the exact model activation bundle.
3. The model runner may use any provider transport, but it may not broaden the prepared evidence.
4. `finalize` preserves raw model bytes before parsing or validation.
5. Candidate provenance may reference only source IDs in the invocation source registry.
6. A valid candidate is wrapped in the existing immutable RGP submission envelope.
7. `rd-distill` performs no reconciliation, admission, canonical mutation, authority mutation, or role activation.
8. An installed project-local copy must work without the generic source repository.
9. Unknown major invocation or RGP contracts fail rather than being coerced.

P10 must preserve those properties rather than treating context packaging as permission to widen them.

### 2.2 P0-P9 context-pack boundary

The closed context-pack architecture provides:

- explicit immutable source bindings;
- a versioned context profile and request identity;
- an optional explicit profile-eligibility decision produced outside the packer;
- distinct control, knowledge, and operational-evidence planes;
- exact source bytes or exact selected PEMS/2 semantics;
- unchanged PEMS provenance within selected canonical knowledge;
- an outer inclusion ledger describing deterministic selection causes;
- explicit operational-evidence validation status;
- a behavior-bound toolchain record;
- deterministic pack identity;
- optional immutable persistence separate from semantic build;
- a deterministic `/2` renderer with runtime-derived execution binding under the accepted P9 threat model;
- a rendered activation whose frames preserve structural plane identity and fail instead of truncating or summarizing.

P10 should consume these results. It should not rebuild their semantics inside the production adapter.

### 2.3 Two incompatible source-registry models currently meet at P10

The current invocation source registry uses opaque production source IDs with simple `{source_id, type, locator, digest}` records.

A context pack instead contains full `reasoning-distiller-context-source-binding/1` entries. Those bindings preserve source class, logical identity, immutable snapshot identity, canonical standing evidence where applicable, operational validation status, and exact content digests. They intentionally do not contain the opaque production `source_id` that an RGP candidate must emit.

Therefore native context integration requires an explicit deterministic provenance bridge. Treating the pack itself as one ordinary evidence file would erase the source-level provenance distinctions P0-P9 were designed to preserve.

## 3. Proposed architecture

### 3.1 Decision summary

Adopt an **opt-in, versioned sealed-context invocation path**.

The proposed public contract family is:

```text
reasoning-distiller-invocation/2
reasoning-distiller-activation-bundle/2
reasoning-distiller-invocation-result/2
reasoning-distiller-context-provenance-registry/1
```

`reasoning-distiller-invocation/1` remains supported and unchanged for legacy explicit-file evidence.

The `/2` path accepts one already-built immutable context pack plus one exact renderer profile and one explicit profile-eligibility binding. It does not accept ambient evidence discovery and does not silently translate a legacy evidence request into a context pack.

The model-visible project evidence boundary for `/2` is exactly the semantic content already sealed inside the validated context pack. The renderer profile and eligibility binding are explicit operational inputs that govern whether and how that sealed evidence may be rendered, but they are not themselves proposition evidence unless some future contract explicitly says otherwise.

### 3.2 Pipeline

```text
explicit governed profile/source preparation
                 |
                 v
        P0-P9 context-pack build
                 |
                 v
       immutable context-pack/2
                 |
                 +---- exact renderer-profile/2
                 |
                 +---- exact profile-eligibility/1
                 |
                 v
      reasoning-distiller-invocation/2
                 |
                 v
              prepare
   validate exact sealed inputs
   derive provenance registry
   render exact pack with P9 renderer
   emit activation-bundle/2
                 |
                 v
       model runner/provider boundary
                 |
                 v
          raw rgp/1 candidate
                 |
                 v
              finalize
   revalidate exact sealed inputs
   preserve raw bytes
   validate rgp/1 + provenance
   persist immutable submission
                 |
                 v
                STOP
                 |
                 v
   separately authorized Steward workflow
```

The pack-build operation remains outside `rd-distill prepare`. A convenience orchestrator may later run context-pack build followed by invocation preparation, but those remain two explicit phases with an immutable boundary between them.

### 3.3 Why the context pack must be prebuilt

`rd-distill prepare` must not search canonical state, repository files, Project memory, installation metadata, prior chats, prior candidates, or other ambient sources to decide what belongs in the model activation.

The evidence choice occurs before the production invocation and is frozen into the context pack by P0-P9. Once `/2` begins, the pack is a sealed evidence capsule. The production adapter validates and renders it but does not re-resolve the original sources represented by it.

This preserves a simple invariant:

> For `reasoning-distiller-invocation/2`, changing any project state that is not already represented by the exact digest-bound pack cannot change the prepared model evidence.

## 4. Proposed invocation `/2` contract

### 4.1 Request shape

The proposed request is intentionally smaller than `/1` in its evidence surface:

```json
{
  "contract": "reasoning-distiller-invocation/2",
  "invocation_id": "opaque-unique-id",
  "created_at": "2026-08-25T00:00:00-07:00",
  "project_root": ".",
  "input": {
    "mode": "context_pack",
    "context_pack": {
      "locator": "derived/context/example.pack.json",
      "digest": "sha256:<64-lowercase-hex>",
      "pack_identity_sha256": "sha256:<64-lowercase-hex>"
    },
    "renderer_profile": {
      "locator": "derived/context/example.renderer.json",
      "digest": "sha256:<64-lowercase-hex>"
    },
    "profile_eligibility": {
      "locator": "derived/context/example.eligibility.json",
      "digest": "sha256:<64-lowercase-hex>"
    }
  },
  "output": {
    "raw_candidate_path": "project-knowledge/invocations/example.raw.json",
    "submission_path": "project-knowledge/submissions/RGP-example.json"
  }
}
```

Normative design requirements:

- `input.mode` is exactly `context_pack` for `/2`.
- `/2` does not accept an independent caller-supplied `evidence` array.
- `/2` does not accept an independent caller-supplied production `source_registry`.
- `/2` does not accept free-form `source_context` as a back door for model-visible project facts.
- all three input locators are explicit project-local regular-file paths and carry exact SHA-256 digests;
- `context_pack.pack_identity_sha256` must exactly match the validated pack identity;
- outputs retain the existing immutable raw-candidate and submission semantics.

A later major contract may add another explicit mode. `/2` should not contain an open-ended mode string that invites undeclared semantics.

### 4.2 Initial compatibility floor

Native `/2` integration should initially require:

```text
context pack:       reasoning-distiller-context-pack/2
renderer profile:   reasoning-distiller-context-renderer-profile/2
rendered activation: reasoning-distiller-context-rendered-activation/2
renderer binding:   reasoning-distiller-renderer-execution-binding/1
eligibility:         reasoning-distiller-context-profile-eligibility/1
candidate output:    rgp/1
submission:          existing RGP Submission Protocol
```

Context pack `/1` and renderer profile `/1` are rejected on the `/2` production path rather than silently upgraded. This reduces compatibility state during the first native integration and preserves version honesty.

## 5. Eligibility boundary

P1e deliberately separates profile validity from profile eligibility. P10 becomes a governed consumer of that distinction.

The `/2` preflight must require an explicit `reasoning-distiller-context-profile-eligibility/1` artifact whose exact profile identity matches the pack profile and whose decision is `eligible`.

The proposed initial production consumer identity is:

```text
consumer_contract: reasoning-distiller-invocation/2
consumer_id: rd-distill
```

The eligibility artifact must also carry its existing immutable policy-snapshot identity and policy-evidence digest.

`rd-distill` validates the supplied eligibility artifact. It does not create an eligibility decision, infer eligibility from profile placement or naming, choose the newest profile, or treat a pack's existence as authorization to use it.

If the pack also contains its optional reduced eligibility summary, that summary must be consistent with the full supplied eligibility binding. A conflict fails closed.

## 6. Deterministic provenance bridge

### 6.1 Required new bridge contract

Introduce `reasoning-distiller-context-provenance-registry/1` as a deterministic derived object created by `prepare` from the exact validated pack.

It exists because RGP candidate provenance uses opaque production source IDs while context-pack source bindings use richer immutable source identities.

The bridge does not create authority or canonical standing. It only gives each exact packed source binding an opaque production source ID and maps rendered frames back to those IDs.

### 6.2 Source-ID derivation

For each complete source binding in `pack.source_registry`, derive a binding identity:

```text
binding_bytes = JCS(full context-source-binding/1 object)

binding_sha256 = sha256(
    "reasoning-distiller-context-provenance-binding/1\0"
    || binding_bytes
)

source_id = "src:ctx:" + lowercase_hex(binding_sha256)
```

The prefix is bookkeeping only. No source type, authority, or standing may be inferred from it.

The bridge serializer and digest domains are part of the `/2` production integration toolchain and must be frozen and tested. If the exact validated binding changes, its source ID changes. Identical complete bindings derive identical IDs across invocations.

A full 256-bit digest is retained in the source ID. Any duplicate source ID derived from different canonical binding bytes is a fail-closed internal/provenance error rather than an invitation to choose one.

### 6.3 Registry entry semantics

Each derived source entry should preserve at least:

```json
{
  "source_id": "src:ctx:<64hex>",
  "type": "canonical_state",
  "locator": "context-pack:<pack-identity>#source/<ordinal>",
  "digest": "sha256:<exact underlying payload digest>"
}
```

`type` is the pack binding's exact `source_class`:

```text
repository_control
package_control
canonical_state
operational_evidence
```

P10 must not remap these classes to `owner_instruction` or `governed_artifact`. Such a remapping could manufacture normative standing that the pack never established.

The derived `locator` is a stable logical location inside the sealed pack. It is not a filesystem location and is never dereferenced by the model-side activation or finalizer.

### 6.4 Frame-to-source mapping

The bridge also records a deterministic mapping from each rendered plane-item frame to its derived source ID.

This sidecar mapping is required because the rendered frame contains the exact pack item and its context source reference, while the RGP candidate must emit the derived opaque production source ID.

Conceptually:

```json
{
  "contract": "reasoning-distiller-context-provenance-registry/1",
  "pack_identity_sha256": "sha256:...",
  "sources": [
    {
      "source_id": "src:ctx:...",
      "source_class": "canonical_state",
      "binding_sha256": "sha256:..."
    }
  ],
  "frame_sources": [
    {
      "frame_index": 3,
      "source_id": "src:ctx:..."
    }
  ],
  "identity": {
    "registry_sha256": "sha256:..."
  }
}
```

The bridge must prove each plane item's source reference resolves to exactly one pack source binding. Missing, ambiguous, or contradictory mappings fail before activation.

The bridge does not rewrite the rendered activation or the pack. It is a deterministic sidecar used by the activation bundle and final provenance validator.

## 7. Activation bundle `/2`

### 7.1 Model-visible contents

`reasoning-distiller-activation-bundle/2` should contain only:

1. the exact installed Distiller directive;
2. the stable instruction to return only raw `rgp/1` candidate JSON;
3. the exact P9 rendered activation `/2` derived from the validated sealed pack and exact renderer profile;
4. the deterministic provenance registry derived from that same pack;
5. invocation identity needed for the operation.

It must not add:

- the raw original files represented by the pack;
- unrelated repository files;
- ambient Project context or memory;
- prior candidates or dispositions;
- canonical-state interpretations created by the runner;
- assistant summaries;
- hidden reasoning;
- implicit `source_context`.

The activation bundle therefore has one project-evidence root: the exact validated context pack.

### 7.2 Plane preservation

The P9 rendered activation remains structurally authoritative for plane classification inside the prepared bundle:

```text
control
knowledge
operational_evidence
```

P10 must not flatten these frames into an untyped list of strings before the model boundary.

Provider transport remains a runner concern, as in invocation `/1`. A runner may encode or deliver the prepared bundle using provider-specific mechanisms, but it must preserve the complete prepared bundle and may not promote knowledge or operational-evidence text into the control plane because the text resembles instructions.

A provider adapter that cannot preserve the logical structure without reinterpretation is non-conforming for `/2` and must fail rather than silently merge or reorder the planes.

This proposal does not require P10 to standardize every provider's message-channel API. It requires semantic preservation of the prepared structured bundle.

### 7.3 Precedence

The installed Distiller directive remains the Distiller's governing protocol instruction. The context pack control plane is explicit project task/control evidence carried inside the model activation. It does not acquire repository authority merely because it is in the control plane.

No P10 component may reinterpret plane membership as RIL role authority, canonical standing, admission approval, or Steward activation.

## 8. `prepare` behavior

For invocation `/2`, `prepare` should perform this ordered fail-closed sequence:

1. validate the strict `/2` request schema;
2. resolve `project_root` and each explicit input locator beneath it;
3. require regular non-symlink files and verify exact request digests;
4. verify installed framework completeness for the P10 runtime, context-pack schemas, renderer, renderer schemas, provenance-bridge logic, Distiller directive, and RGP validator;
5. parse and validate `context-pack/2` without discovering additional project sources;
6. verify the request's expected pack identity equals the pack's validated `pack_identity_sha256`;
7. parse and validate `renderer-profile/2`;
8. parse and validate the full profile-eligibility binding;
9. require eligibility `decision: eligible` for exact consumer `reasoning-distiller-invocation/2` / `rd-distill` and exact pack profile identity;
10. require any reduced eligibility data already carried by the pack to be consistent with the full binding;
11. require renderer profile `pack_profile` identity to match the exact pack profile;
12. call the installed P9 renderer with the exact pack and renderer profile;
13. require successful runtime-derived renderer execution binding under the accepted P9 runtime ABI and same-bundle rules;
14. derive the exact context provenance registry and frame-source mapping from the same validated pack and rendered activation;
15. build the exact activation bundle `/2`;
16. enforce the existing immutable artifact rules for prepared invocation artifacts where the CLI persists them;
17. return the bundle without any source discovery or semantic repair.

No original source represented by the pack is re-opened during this sequence.

## 9. `finalize` behavior

`finalize` retains the current critical ordering: raw candidate bytes are preserved before parse or RGP validation.

For `/2`, finalization should additionally re-establish that the exact sealed production inputs still match the request before creating a submission:

1. re-resolve only the three explicit `/2` input files and verify their request digests;
2. revalidate pack/profile/eligibility compatibility and exact identities;
3. deterministically rederive the provenance registry and, where required to prove the same model-side evidence identity, the rendered activation identity;
4. preserve the raw model bytes immutably;
5. parse raw JSON;
6. validate `rgp/1` with the installed validator;
7. reject every candidate provenance ID absent from the rederived context provenance registry;
8. construct the existing immutable RGP submission envelope without modifying the candidate graph;
9. persist the submission immutably;
10. stop before reconciliation or admission.

If any sealed input changes between `prepare` and `finalize`, finalization fails before an ordinary submission is produced. It never reconstructs the missing state from repository HEAD, caches, or current canonical state.

## 10. Versioning and compatibility

### 10.1 Legacy invocation `/1`

`reasoning-distiller-invocation/1` remains semantically and behaviorally unchanged.

Regression requirements must prove that a legacy `/1` request still produces the same request validation, evidence loading, activation-bundle `/1` shape, candidate validation behavior, result contract, and submission behavior as before P10.

No context-pack behavior is selected merely because a context-pack file exists in the project.

### 10.2 New invocation `/2`

`/2` is opt-in by explicit request contract only.

Unknown major contracts fail closed. There is no automatic downgrade from `/2` to `/1`, and no automatic upgrade of `/1` to `/2`.

### 10.3 RGP and submission compatibility

P10 does not require a new RGP semantic version. The Distiller still returns raw `rgp/1` candidate graph JSON, and the existing RGP Submission Protocol remains the submission boundary unless independent review establishes a concrete incompatibility.

This minimizes downstream migration and isolates the new semantics to production input preparation and provenance registration.

### 10.4 Context contract compatibility

The first native production path intentionally accepts only context pack `/2` plus renderer/profile `/2`.

Supporting pack `/1`, renderer `/1`, or another context family should require explicit compatibility evidence and an approved amendment rather than an opportunistic adapter inside P10.

### 10.5 Package compatibility

A P10-capable installation must ship every implementation and schema needed for `/2` preparation and finalization. It must succeed with the generic source repository unavailable.

The install package content identity must therefore cover the P10 behavior-bearing runtime, context renderer and its required execution-binding artifacts, bridge logic, required schemas/resources, Distiller directive, and RGP validator through the repository's package/install contracts.

A release/package version change is required when P10 is shipped because new public production contracts and installed behavior are added. The exact release version is a release-governance decision, not a Stage 1 architectural decision.

## 11. Failure behavior

P10 should preserve the existing process exit-class meanings while adding stable reason codes for the new preflight and activation checks.

| Exit | Stage | Proposed P10 examples |
|---:|---|---|
| `2` | preflight | missing/unsafe pack, digest mismatch, unsupported pack/profile contract, eligibility missing/ineligible/mismatched, pack/profile mismatch, invalid provenance bridge input |
| `3` | activation | renderer execution-binding mismatch, unsupported P9 runtime ABI, rendered activation overflow, provider runner cannot preserve the prepared bundle |
| `4` | parse | raw candidate is not valid UTF-8 JSON |
| `5` | validation | RGP validation fails or candidate cites an ID absent from the derived context provenance registry |
| `6` | persistence | immutable output collision or persistence failure |
| `1` | internal | unexpected implementation failure |

Suggested stable reason-code vocabulary for review:

```text
CONTEXT_PACK_UNRESOLVED
CONTEXT_PACK_DIGEST_MISMATCH
UNSUPPORTED_CONTEXT_PACK
RENDERER_PROFILE_UNRESOLVED
RENDERER_PROFILE_DIGEST_MISMATCH
UNSUPPORTED_RENDERER_PROFILE
PROFILE_ELIGIBILITY_REQUIRED
PROFILE_ELIGIBILITY_DIGEST_MISMATCH
PROFILE_INELIGIBLE
PROFILE_ELIGIBILITY_MISMATCH
RENDERER_PROFILE_PACK_MISMATCH
RENDERER_RUNTIME_INCOMPATIBLE
TOOLCHAIN_IDENTITY_MISMATCH
ACTIVATION_LIMIT_EXCEEDED
PROVENANCE_BRIDGE_INVALID
PROVENANCE_SOURCE_COLLISION
UNRESOLVED_PROVENANCE
```

Exact code names should be frozen at the protocol gate. Existing reason codes should be reused where their semantics are already exact rather than duplicated under P10-only aliases.

A failed parse or RGP/provenance validation still leaves the exact raw model bytes preserved. No ordinary submission is written after those failures.

## 12. Authority, standing, and mutation invariants

P10 must preserve all of these invariants:

1. **Fixed evidence:** model-visible project evidence is exactly the validated sealed context pack selected by the `/2` request.
2. **No re-resolution:** original sources represented by the pack are never re-opened by `/2` prepare/finalize.
3. **No discovery:** repository search, canonical lookup, Project memory, semantic search, prior candidates, caches, and network discovery cannot add evidence.
4. **Explicit eligibility:** `rd-distill` consumes an exact eligibility result but never creates or infers eligibility.
5. **Plane preservation:** control, knowledge, and operational evidence remain structurally distinct through the model boundary.
6. **No text promotion:** instruction-like knowledge or operational-evidence text cannot become control because of content.
7. **Source-class preservation:** the provenance bridge preserves context source class and does not translate it into authority-bearing source types.
8. **Opaque IDs:** production source-ID spelling has no semantics.
9. **Provenance closure:** candidate provenance references only the exact derived registry.
10. **Raw-byte preservation:** model output is persisted exactly before parse/validation.
11. **No post-hoc repair:** P10 never edits the returned candidate graph.
12. **Submission continuity:** successful output remains an ordinary immutable RGP candidate submission.
13. **No authority creation:** context inclusion, control-plane placement, renderer success, eligibility, or structural validity grants no role authority or activation.
14. **No canonical mutation:** pack build, prepare, render, bridge derivation, finalize, and submission do not mutate canonical PEMS/COVE.
15. **No reconciliation/admission:** successful `/2` completion stops before Steward reconciliation or admission.
16. **Installed isolation:** the complete path works from the installed package without generic-repository fallback.
17. **Legacy isolation:** `/1` behavior is unchanged unless the caller explicitly requests `/2`.
18. **Fail-closed versioning:** unsupported major contracts are rejected rather than coerced.
19. **Input immutability across phases:** changed sealed inputs between prepare and finalize cannot yield an ordinary successful submission.
20. **Deterministic mechanics:** fixed request bytes, installed behavior identity, and sealed inputs produce the same prepared bundle and provenance registry.

## 13. Migration and rollout

### 13.1 Migration sequence

A safe rollout is additive:

1. ship a P10-capable Reasoning Distiller package containing the approved `/2` contracts and implementation;
2. keep `/1` as the default behavior for existing callers and existing request files;
3. upstream of production invocation, explicitly select an eligible context profile and build `context-pack/2` through the accepted P0-P9 pipeline;
4. persist or otherwise place the exact pack at a caller-selected immutable project-local path outside canonical/authority stores;
5. supply an exact renderer-profile `/2` compatible with that pack and runtime;
6. supply a full profile-eligibility `/1` binding for the `/2` production consumer;
7. create an explicit invocation `/2` request carrying exact digests and expected pack identity;
8. run `rd-distill prepare`, the model runner, and `finalize` under the new contract;
9. continue all existing Steward reconciliation/admission steps separately.

### 13.2 Rollback

Rollback is contract-selective rather than state-rewriting:

- existing `/1` invocation remains usable when its legacy evidence workflow is desired;
- `/2` artifacts remain immutable evidence of attempted `/2` operations;
- an older runtime that does not understand `/2` must report unsupported contract rather than attempting a downgrade;
- rollback does not rewrite candidate submissions, context packs, or canonical state.

### 13.3 No automatic migration

P10 should not scan old invocation requests, detect packs in directories, or rewrite legacy evidence selections. Migration is explicit per invocation or via a separately governed outer workflow.

## 14. Alternatives considered

### A. Pass the entire context pack as one ordinary `/1` evidence file

**Reject.** This would make the pack file itself the only production provenance source unless extra ad hoc logic were added. It would erase source-level provenance and invite the model or adapter to treat structurally distinct planes as undifferentiated file content.

### B. Let `rd-distill prepare` build a context pack by searching current project state

**Reject.** It would turn production preparation into an evidence-discovery mechanism and make model evidence depend on mutable ambient state not named by the invocation.

### C. Send both the context pack and every original source file to the model

**Reject.** It duplicates evidence, creates drift between packed and raw forms, weakens the sealed-pack identity, and broadens the production evidence set.

### D. Accept a pre-rendered activation as the sole context input

**Reject for initial P10.** A pre-rendered artifact alone does not prove that the current installed P9 renderer behavior produced it under the expected execution binding. It could be supported later only with a separate immutable production artifact/attestation contract that preserves the same proof obligations.

### E. Redefine `reasoning-distiller-invocation/1` in place

**Reject.** Native context integration changes evidence and provenance semantics materially. Reusing `/1` would violate version honesty and make legacy callers depend on hidden compatibility branches.

### F. Automatically convert a legacy `/1` evidence request into `/2`

**Reject.** It silently changes the evidence representation, selection semantics, provenance IDs, and eligibility requirements. Explicit contract selection is safer and reproducible.

### G. Map context `canonical_state` or `package_control` to `governed_artifact`

**Reject.** Source classification is not a license to manufacture normative authority. The bridge preserves exact source class and leaves authority resolution to the contracts that actually own it.

## 15. Pressure cases for independent review

The P10 design should not advance to implementation until at least these pressure cases are machine-specifiable with stable expected outcomes.

| ID | Pressure case | Required outcome |
|---|---|---|
| PI-01 | Same `/2` request, pack, renderer profile, eligibility, and installed behavior repeated | Byte-identical prepared activation bundle and provenance registry |
| PI-02 | Original repository/canonical source files are unavailable after the pack was built | `/2` prepare still succeeds from the sealed pack; no original-source lookup occurs |
| PI-03 | Pack bytes differ from request digest | Fail preflight before rendering |
| PI-04 | Pack's internal identity differs from request expected identity | Fail preflight |
| PI-05 | Renderer-profile bytes differ from request digest | Fail preflight |
| PI-06 | Eligibility artifact is missing | Fail preflight |
| PI-07 | Eligibility decision is `ineligible` | Fail preflight |
| PI-08 | Eligibility names a different pack profile | Fail preflight |
| PI-09 | Eligibility names a different consumer contract/id | Fail preflight |
| PI-10 | Pack `/1` supplied to invocation `/2` | Reject unsupported context contract; no upgrade |
| PI-11 | Renderer profile `/1` supplied to invocation `/2` | Reject unsupported renderer profile; no reinterpretation |
| PI-12 | Renderer profile's pack-profile identity differs from pack | Fail preflight |
| PI-13 | Old/stale renderer execution binding supplied after behavior changes | P9 renderer fails before successful activation |
| PI-14 | Runtime ABI is outside the accepted P9 binding | Fail activation; no silent equivalence |
| PI-15 | One exact source binding appears in two independent packs | Same deterministic production source ID is derived |
| PI-16 | Two different immutable snapshots share one logical source identity | Distinct production source IDs are derived |
| PI-17 | Different canonical binding bytes somehow collide under one derived source ID | Fail closed; do not choose a winner |
| PI-18 | Rendered plane item source ref resolves to no pack source binding | Fail before model activation |
| PI-19 | Rendered plane item source ref resolves ambiguously | Fail before model activation |
| PI-20 | Candidate cites a source ID absent from the derived registry | Preserve raw bytes, fail provenance validation, write no submission |
| PI-21 | Candidate cites a valid exact derived source ID | Provenance check accepts it subject to ordinary RGP validation |
| PI-22 | Context source class looks authority-like by name | No remapping to `owner_instruction` or `governed_artifact`; no authority inference |
| PI-23 | Knowledge payload contains instruction-shaped text | Remains knowledge plane through prepared activation |
| PI-24 | Operational-evidence payload contains instruction-shaped text | Remains operational-evidence plane |
| PI-25 | Rendered activation exceeds explicit byte limit | Fail with no truncation, ranking, summarization, or omission |
| PI-26 | Project memory, prior chats, prior candidates, or unrelated repository files vary | Prepared `/2` bundle is unchanged |
| PI-27 | `/2` request attempts to add `source_context` | Strict schema rejection |
| PI-28 | `/2` request attempts to add a legacy `evidence` array | Strict schema rejection |
| PI-29 | `/2` request attempts to add a caller-supplied production `source_registry` | Strict schema rejection |
| PI-30 | Provider runner attempts to add extra project context | Runner is non-conforming; no valid `/2` production result may be claimed |
| PI-31 | Provider adapter flattens/promotes frames based on text | Runner is non-conforming or fails before model activation |
| PI-32 | Generic source repository is unavailable | Installed `/2` path still prepares, validates, and finalizes successfully |
| PI-33 | Legacy `/1` request executes under P10-capable package | Existing `/1` behavior and contract shape remain unchanged |
| PI-34 | Sealed pack/profile/eligibility change after prepare but before finalize | Finalize fails before submission |
| PI-35 | Model returns invalid JSON | Exact raw bytes preserved; parse failure; no submission |
| PI-36 | Model returns invalid RGP | Exact raw bytes preserved; validation failure; no submission |
| PI-37 | Raw-candidate or submission path collides with different existing bytes | Immutable collision; existing bytes unchanged |
| PI-38 | P10 operation is run with canonical, admission, role, or authority stores present | Those stores remain byte-for-byte unchanged |
| PI-39 | Two invocations use the same sealed pack but different invocation IDs | Context/provenance identities remain the same; candidate submissions retain distinct invocation-derived submission identities |
| PI-40 | Older `/1`-only runtime receives a `/2` request | Unsupported contract; no downgrade or best-effort execution |

Stage 2 should add pressure cases for any new weakness it finds rather than limiting review to this list.

## 16. Proposed implementation sequence and gates

This is a proposal for later reconciliation. It is not current implementation authorization.

| Gate | Proposed work | Exit criterion |
|---|---|---|
| **P10-G0 Pressure-case freeze** | Freeze PI-01 through PI-40 plus Stage-2 additions with stable outcomes and failure classes | Native-integration threat model exists before production code changes |
| **P10-G1 Protocol freeze** | Freeze invocation `/2`, activation-bundle `/2`, result `/2`, provenance-registry `/1`, exact reason codes, and supported contract matrix | Unknown fields/versions fail closed; schemas and negative fixtures are deterministic |
| **P10-G2 Provenance bridge** | Implement and validate deterministic binding identity, source-ID derivation, registry identity, and frame-source mapping | Every model-visible plane item resolves to exactly one opaque production source ID; no authority remapping exists |
| **P10-G3 Prepare integration** | Add sealed-pack `/2` preflight, eligibility validation, renderer `/2` invocation, and activation-bundle `/2` construction | Exact pack is the sole project-evidence root; no ambient/original-source discovery; P9 execution binding and limits enforced |
| **P10-G4 Finalize integration** | Add exact input revalidation and derived-registry provenance validation while preserving raw-byte and submission semantics | Changed inputs fail; invalid raw output is preserved; valid RGP produces unchanged submission semantics |
| **P10-G5 Installed-package isolation** | Package all required P10/P9 code and schemas and test with generic repository unavailable | Full `/2` path works from project-local installation alone |
| **P10-G6 Compatibility/migration** | Prove `/1` regressions, explicit `/2` opt-in, rollback behavior, and unsupported-version failures | No silent migration or legacy behavior drift |
| **P10-G7 Candidate-bound production evidence** | Run complete P10 suite plus unaffected production/P0-P9 regressions on one immutable candidate | Exact candidate-bound evidence exists for independent implementation review |

No implementation gate begins from this Stage 1 proposal alone. Stage 2 independent review and Stage 3 Steward reconciliation must first produce an authoritative P10 plan and exact next authorized action.

## 17. Acceptance criteria for the proposed architecture

A reconciled P10 design should not be implementation-ready unless it can require and later prove all of the following:

- invocation `/1` remains unchanged and usable;
- invocation `/2` is explicit and fail-closed;
- one digest-bound `context-pack/2` is the sole project-evidence root for `/2`;
- the pack is built before production invocation and original sources are not re-resolved by `/2`;
- a full exact profile-eligibility binding is mandatory and externally produced;
- renderer profile `/2` matches the pack and P9 runtime-derived execution binding;
- P9 structural planes survive into the prepared model activation without text-driven promotion;
- the production adapter derives, rather than accepts, the context provenance registry;
- each derived source ID is a deterministic opaque identity of one complete context source binding;
- every model-visible plane item maps to exactly one derived source ID;
- the bridge preserves source class and does not manufacture authority-bearing source types;
- candidate provenance is restricted to the exact derived registry;
- ambient Project context, prior candidates, hidden reasoning, unrelated files, caches, and network discovery cannot change the prepared bundle;
- changed sealed inputs between prepare and finalize fail before submission;
- raw candidate bytes are preserved exactly before parse/validation;
- invalid candidate output is never repaired into a submission;
- valid output remains an ordinary `rgp/1` candidate under the existing submission protocol;
- no P10 operation reconciles, admits, activates, authorizes, or mutates canonical state;
- installed `/2` operation works with the generic repository absent;
- migration is explicit and reversible by contract choice, not by rewriting immutable artifacts;
- exact candidate-bound implementation evidence and fresh independent implementation review are required before P10 can be closed.

## 18. Risks and unresolved questions for Stage 2

### 18.1 Provenance-registry persistence and downstream resolution

The proposal derives the registry deterministically at prepare/finalize and includes it in activation-bundle `/2`. Stage 2 should challenge whether downstream reconciliation tooling needs the exact derived registry persisted as a separately named immutable invocation artifact, referenced from submission metadata, or whether the retained invocation/bundle artifacts plus sealed pack are sufficient under existing provenance-resolution workflows.

This proposal does not authorize changing the RGP submission envelope merely for convenience. If durable downstream resolution cannot be reconstructed without such a change, that is a required Stage-2 finding and versioning decision.

### 18.2 Provider transport conformance

The existing production contract intentionally leaves model transport provider-neutral. This proposal retains that boundary and requires semantic preservation of the structured `/2` bundle.

Stage 2 should challenge whether this is testable enough without a separate `reasoning-distiller-model-transport/1` conformance contract. If a separate transport contract is required, it should remain narrow and must not become a new evidence-discovery layer.

### 18.3 Runtime compatibility of the P9 renderer

The closed P9 `/2` renderer currently binds an exact accepted CPython runtime ABI. P10 inherits that constraint if it invokes the renderer directly.

Stage 2 should determine whether the first production release should intentionally require that exact ABI, package a qualifying execution environment, or require a separately reviewed P9 compatibility amendment before general release. P10 must not silently weaken P9 execution identity to gain broader runtime support.

### 18.4 Installation content identity

The P10 installed package must include behavior not present in the earlier production-only installation surface. Stage 2 should verify that existing installation/package contracts can bind all P10 and P9 behavior-bearing files and schema resources without introducing source-repository fallback.

### 18.5 Context-control semantics versus provider channels

The pack's control plane is a structural context plane, not a claim of provider system/developer-channel authority. Stage 2 should challenge the exact runner guidance so that a provider adapter neither demotes required structural context nor promotes it into authority not granted by repository contracts.

## 19. Recommendation

Proceed with the sealed-context `/2` architecture as the Stage 1 proposal basis:

- keep `reasoning-distiller-invocation/1` unchanged;
- introduce explicit invocation/activation/result `/2` contracts for native context use;
- require one prebuilt digest-bound `context-pack/2` as the sole project-evidence root;
- require exact renderer-profile `/2` and external profile-eligibility `/1` artifacts;
- invoke the closed P9 renderer rather than flattening pack planes;
- derive a deterministic opaque production provenance registry from exact pack source bindings;
- keep raw-byte preservation, RGP/1 validation, immutable submission, and authority boundaries unchanged;
- make migration additive and opt-in;
- fail on unsupported versions, changed inputs, runtime incompatibility, provenance ambiguity, or any attempt to broaden evidence.

The key architectural rule is:

> Native context integration may transform and validate one explicitly selected sealed context pack, but it may never use production invocation as an opportunity to discover, select, reinterpret, or silently add project evidence.

## 20. Stage 1 terminal boundary

This document completes only **P10 Stage 1 independent proposal** under `proposal-review-synthesis/1`.

No P10 implementation, production contract mutation, package release, canonical mutation, admission, authority mutation, or Steward reconciliation has been performed by this Stage 1 activation.

The next consequential work belongs to a **separate independent Engineer activation for Stage 2 review and synthesis**. That activation should receive the original P10 problem and constraints, this complete immutable Stage 1 proposal, the governing production invocation contract, the governing context-packaging plan, the closed P9 evidence chain, and any additional live contracts it independently determines are relevant. It should challenge rather than endorse this proposal, with special scrutiny on provenance-registry durability, provider transport semantics, runtime ABI compatibility, installation/package identity, versioning consequences, migration, failure classes, and whether the sealed-pack boundary is sufficient to preserve the current fixed production evidence invariant.
