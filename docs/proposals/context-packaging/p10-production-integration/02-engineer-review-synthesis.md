# P10 Production Integration - Stage 2 Engineer Review/Synthesis

Status: **Independent review complete; compatible with required revisions**

Disposition: **`P10_PRODUCTION_INTEGRATION_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`**

Method: `proposal-review-synthesis/1`

Repository: `loteque/reasoning-distiller`

Coordination control ref: `main`

Coordination revision resolved before review and re-resolved immediately before this Stage 2 write: `80b6e89ad2efe84b088ca06b908a257c449fac15`

Semantic basis: P9 Steward reconciliation `1b1be8f60f2eef0ddc7a91a91c352cf4018012d3`

Closed P9 candidate: `cc14721725949a560b52f0a5d80808e95c2d6ad0`

Stage 1 proposal commit: `0a2909d5a88c9a7d8f7abbf1b2c59f2abd34b723`

Stage 1 proposal blob: `cd9dd25c9209dbb066e8017c2256f4647037dec7`

Stage: **Stage 2 independent Engineer review and synthesis**

Authority posture: this artifact is a bounded technical review. It establishes no Project Steward authority, no accepted RIL activation, no reconciliation, no admission, no canonical standing, no production authorization, no implementation authorization, and no canonical, authority, or activation mutation. The Engineer role is the operational review role selected by the governing proposal-review workflow; that role does not acquire Steward authority by reviewing or synthesizing Stage 1.

## 1. Review scope and method

This Stage 2 review is scoped only to the P10 production-integration architecture proposed in Stage 1.

The review reconstructed the governing boundary independently from live repository state rather than treating Stage 1 conclusions as established facts. It inspected, at minimum:

- `agents/engineer/DIRECTIVE.md` from exact coordination revision `80b6e89ad2efe84b088ca06b908a257c449fac15`;
- `docs/operations/PROJECT_CHAT_TRANSITION_AMENDMENT.md` from that same coordination revision;
- `docs/governance/PROPOSAL_REVIEW_METHOD.md` from that same coordination revision;
- `docs/operations/PRODUCTION_INVOCATION_CONTRACT.md` from that same coordination revision;
- the governing context-packaging plan, commit `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`, blob `8474d2da42f863f0a190fd80292085176d3f97f0`;
- P9 renderer-identity amendment, commit `373667be85521e6f0f83bf19fed3378357e51118`, blob `90142ffe6b6652faceb3e8347f33fa71c8dc3ed9`;
- closed P9 candidate `cc14721725949a560b52f0a5d80808e95c2d6ad0`, including renderer blob `a88168c59de3235be92881bf1655416f0f1099e8`;
- P9 Steward reconciliation `1b1be8f60f2eef0ddc7a91a91c352cf4018012d3`;
- current RGP Submission Protocol;
- current package build configuration and deterministic package builder;
- current installed package record for Reasoning Distiller `0.5.3`;
- the complete immutable Stage 1 proposal at commit/blob above.

The required Stage 2 posture is challenge plus synthesis. The review therefore asks whether Stage 1's architecture is actually implementable while preserving the production fixed-evidence invariant, provenance resolution, P9 execution identity, installed-package isolation, provider-plane semantics, legacy compatibility, and downstream Steward handoff.

No P10 implementation or production-contract mutation is performed here.

## 2. Independent reconstruction of the P10 problem

The governing P0-P9 work now provides one deterministic, digest-bound context pack with explicit source bindings, separated planes, deterministic selection provenance, an exact renderer profile, and a P9 `/2` renderer whose accepted success is bound to the behavior it actually executes under a deliberately narrow runtime threat model.

The current production invocation contract is materially different. `reasoning-distiller-invocation/1` receives an explicit evidence file list and a caller-supplied source registry. `prepare` emits the model activation bundle; a provider-neutral runner transports it; `finalize` preserves raw bytes, validates `rgp/1`, checks provenance against the request source registry, and creates an immutable ordinary RGP submission.

P10 therefore has two distinct integration jobs, not one:

1. **model-evidence integration:** turn one exact sealed context pack into the exact model-visible evidence without reopening original sources or silently discovering more context; and
2. **durable provenance/toolchain handoff:** make the resulting candidate and its opaque provenance IDs reconstructible after `prepare`, after the provider boundary, after `finalize`, and later during Steward reconciliation.

Stage 1 solves most of the first job. Its main weakness is that it treats the second job as largely reconstructible from the three request input files. That is insufficient because production execution has mutable behavior and artifact boundaries of its own.

The decisive missing relation is:

```text
exact bytes + toolchain identity prepared for the model
                    |
                    X  not durably bound by Stage 1
                    |
raw candidate later accepted by finalize/submission
```

A P10 design is not complete until that relation is explicit and immutable.

## 3. Stage 1 agreements

The review agrees with the following core Stage 1 decisions.

### A1. Native context integration requires a new opt-in invocation major

`reasoning-distiller-invocation/1` should remain unchanged. Native sealed-context invocation changes evidence representation, provenance-registry construction, renderer requirements, and compatibility semantics. A side-by-side `/2` family is appropriate and avoids hidden migration.

### A2. The pack must be built before production invocation

`rd-distill prepare` must not become a context-pack builder or evidence-discovery engine. The exact pack, renderer profile, and eligibility binding must be selected and frozen before `/2` begins.

### A3. Original sources must not be reopened by `/2`

The pack is the production evidence root. Repository files, canonical state, Project memory, prior candidates, caches, network discovery, and source-repository state must not be consulted to add or repair evidence.

### A4. The P9 renderer must remain the structural plane authority

P10 should consume the closed P9 renderer rather than flattening context planes into an ad hoc prompt format. Control, knowledge, and operational-evidence membership must survive as structure rather than text heuristics.

### A5. `/2` should derive its production provenance registry

A caller-supplied production registry would create a second truth source and permit divergence from the sealed pack. Deriving opaque production IDs from exact pack bindings is the right dependency direction.

### A6. Raw candidate preservation and ordinary RGP validation remain unchanged in principle

The raw model output must still be written immutably before parse or validation. P10 must not repair the graph after return. Successful output should remain `rgp/1` unless a concrete protocol incompatibility is established.

### A7. Migration should be additive and explicit

A `/1` caller should remain a `/1` caller. Pack presence, package version, directory naming, or installer state must never auto-select `/2`.

## 4. Required Stage 2 revisions

The Stage 1 architecture is compatible with implementation only if all revisions R1-R8 below are incorporated by Stage 3. These are required amendments, not optional hardening suggestions.

## R1. Introduce an immutable prepared-invocation identity spanning `prepare -> runner -> finalize`

### Finding

Stage 1 revalidates the three `/2` input files during `finalize`, but those files do not identify the complete behavior or exact activation that was prepared.

Between `prepare` and `finalize`, any of the following can change independently of the request's three input digests:

- the installed `rd_distill` implementation;
- provenance-bridge implementation behavior;
- installed Distiller directive bytes;
- installed RGP validator bytes;
- installed schemas/resources;
- package content identity;
- the exact activation bundle handed to the runner;
- runner transformation of that bundle.

P9's renderer binding closes only the renderer execution relation. It does not bind all P10 production behavior.

Re-reading pack/profile/eligibility during `finalize` can prove that those three files still match the request. It cannot prove that the candidate being finalized came from the exact activation bundle and installed P10 toolchain that `prepare` produced.

### Required amendment

Add a deterministic immutable prepared-invocation artifact, tentatively:

```text
reasoning-distiller-prepared-invocation/1
```

The exact name is Stage 3/gate-owned, but the semantic object is mandatory.

It must bind at least:

- invocation contract and invocation ID;
- canonical request digest/identity;
- exact pack file digest and pack identity;
- exact renderer-profile digest and identity;
- exact eligibility artifact digest and decision identity;
- exact installed package `content_identity`;
- exact installed Distiller directive digest;
- exact installed RGP validator identity/digest;
- exact provenance-registry identity/digest;
- exact P9 rendered-activation identity/digest;
- exact P9 renderer execution binding and accepted runtime ABI;
- exact activation-bundle identity/digest;
- any frozen provider-transport contract identity required by R4.

`prepare` must produce this artifact from the exact bytes it uses. If it is persisted, persistence must be immutable and outside canonical/admission/authority state.

`finalize` must consume and verify the exact prepared-invocation identity rather than reconstructing success solely from the request and current installation. Installation/toolchain drift between prepare and finalize must fail closed.

A candidate cannot be called an ordinary successful `/2` production result unless it is bound to one exact prepared invocation.

### Synthesis consequence

Stage 1's proposed activation-bundle `/2` remains useful, but it becomes one member of the prepared-invocation identity rather than an ephemeral value that later finalization merely attempts to reproduce.

## R2. Persist the exact derived provenance registry and make downstream resolution normative

### Finding

The current RGP Submission Protocol requires the Steward to resolve provenance under project policy, but the ordinary submission envelope does not contain the invocation source registry. Stage 1 acknowledges this uncertainty but leaves open whether deterministic re-derivation is sufficient.

That is not implementation-ready.

For `/2`, provenance IDs are newly derived opaque identifiers. If the exact registry is not durably retained and normatively linked to the successful invocation/submission handoff, a later Steward can receive a structurally valid candidate whose source IDs cannot be resolved without reconstructing undocumented invocation context.

The current submission protocol also states that optional `source_context` is not proposition provenance and must not silently become a second evidence system. Therefore P10 must not smuggle the registry through an informal `source_context.refs` convention and call the handoff solved.

### Required amendment

The exact `reasoning-distiller-context-provenance-registry/1` object must be an immutable invocation artifact for successful `/2` preparation.

Stage 3 must choose and freeze one explicit downstream handoff model:

**Option A: companion provenance artifact without changing the candidate graph.**

- the prepared-invocation artifact and `/2` result carry the exact registry locator plus digest/identity;
- the project/Steward reconciliation entrypoint normatively receives the successful `/2` result or prepared-invocation receipt together with the ordinary RGP submission;
- the RGP submission envelope remains unchanged;
- the companion artifact is resolver metadata, not a second proposition-provenance field.

**Option B: honestly version the submission handoff envelope.**

- introduce a new submission-envelope contract/major that contains an immutable provenance-registry reference;
- preserve the `rgp/1` candidate graph unchanged;
- keep the registry reference metadata separate from proposition provenance semantics.

Stage 2 prefers Option A because it minimizes RGP/submission churn, but only if the receiving Steward workflow contract is explicitly amended to require and verify the companion artifact. If that explicit handoff cannot be established, Option B becomes required.

### Acceptance requirement

There must be a machine-testable path from a successful `/2` submission to the exact registry that resolves every candidate provenance ID, without using chat history, ambient filesystem search, repository HEAD, or heuristics.

## R3. Make provenance-registry source identity semantically stable and separate pack-local occurrence data

### Finding

Stage 1 derives:

```text
source_id = src:ctx:<sha256(full source-binding bytes)>
```

but illustrates a registry `locator` containing:

```text
context-pack:<pack-identity>#source/<ordinal>
```

It also requires the same complete source binding to derive the same `source_id` across independent packs.

Those two rules conflict at the registry-record level. The same source ID can then map to different pack identities or ordinals even though its semantic source binding is identical.

A production source ID may be opaque, but an opaque ID must not ambiguously name materially different registry records.

### Required amendment

Keep the binding-derived source ID direction, but separate these two identities:

1. **stable source-binding identity**
   - `source_id`;
   - exact canonical binding digest;
   - exact source class;
   - exact immutable source/snapshot identity fields needed for later resolution;
   - exact underlying payload digest represented by the binding.

2. **pack-local occurrence/frame mapping**
   - exact pack identity;
   - plane and item/frame identity or index;
   - mapping from that occurrence to the stable `source_id`.

A pack-local ordinal must not be the only locator semantics for a source ID that is intentionally stable across packs.

Different canonical binding bytes must never resolve to the same accepted source ID. Same binding bytes may occur in many packs, but all accepted stable source records for that ID must be semantically equivalent.

The frame-source mapping remains part of the exact registry/prepared invocation and must prove every model-visible context frame resolves to exactly one stable source ID.

## R4. Freeze a minimal provider-transport and plane-preservation conformance contract

### Finding

Stage 1 says provider transport is a runner concern while also requiring the runner to preserve structural planes, not promote text based on instruction-like content, and not broaden evidence.

That is an important invariant but currently only a prose obligation. P10 adds a stronger requirement than `/1`: it now matters not only that all bytes arrive, but also that project control, knowledge, and operational-evidence structures are not translated into provider authority semantics incorrectly.

The context pack `control` plane is not equivalent to a provider's system/developer authority channel. Conversely, flattening all frames into one untyped string destroys the P9 structure P10 is supposed to preserve.

Without a narrow transport contract, two provider adapters can both claim conformance while assigning materially different provider precedence to the same prepared bundle.

### Required amendment

Freeze a provider-neutral logical transport contract before implementation, tentatively:

```text
reasoning-distiller-model-transport/1
```

It need not standardize every provider API. It must standardize the semantic mapping that every conforming runner preserves:

- the installed Distiller directive remains the framework instruction surface defined by production invocation;
- the P9 rendered context remains model evidence with its structural frame/plane labels intact;
- context `control` is project control evidence, not automatic provider-system authority;
- knowledge and operational evidence cannot be promoted based on text content;
- frame order and exact frame payload bytes are preserved;
- the derived provenance registry is transported without altering source IDs or frame mapping;
- the runner adds no project facts, chat memory, prior candidates, canonical interpretation, or hidden evidence;
- a provider that cannot represent the required logical separation fails before a valid `/2` result can be claimed.

The prepared-invocation artifact must bind the exact logical transport contract/version and activation-bundle digest.

### Threat-model clarification

This contract establishes deterministic conformance for a non-hostile/reference runner. It is not cryptographic proof against a malicious provider or a runner that lies about what it sent. If stronger hostile-runner assurance is later required, that is a new execution/attestation boundary and must not be implied by P10 conformance tests.

## R5. Freeze the exact P9 runtime ABI as an initial `/2` compatibility requirement

### Finding

The closed P9 renderer is not generically compatible with "Python 3.12" or with arbitrary installed Python. Its implementation binds exactly:

```text
implementation: cpython
major: 3
minor: 12
micro: 0
cache tag: cpython-312
scheme: python-closed-bundle/1
```

The current installed Reasoning Distiller record declares an installer runtime of generic `python3`; it does not provide or pin an embedded CPython 3.12.0 execution environment.

Therefore P10 cannot claim general installed `/2` compatibility while directly invoking the current P9 renderer unless this runtime constraint is made explicit.

### Required amendment

For the first P10 production release, choose one of these before implementation:

**Preferred narrow initial rule:** `/2` is supported only when the process executing the P9 renderer has the exact accepted P9 ABI tuple. `prepare` checks it and fails closed before provider execution if it does not match.

**Alternative:** package and verify a separately qualified execution environment capable of satisfying P9's runtime contract. This is a materially larger packaging/execution design and would require separate review if it changes the accepted P9 execution boundary.

Stage 2 recommends the narrow initial rule. P10 must not broaden P9's accepted ABI by calling a nearby Python version equivalent.

The supported ABI tuple must be visible in `/2` compatibility documentation, pressure cases, and prepared-invocation identity.

## R6. Move installed-package closure earlier and bind all P9/P10 behavior in package content identity

### Finding

The current deterministic release package managed roots are:

```text
admission
agents
backends
protocols
runtime
schemas
validators
```

`context_packaging` is not currently managed. The installed Reasoning Distiller `0.5.3` therefore does not contain the closed P9 renderer package surface needed by Stage 1.

The package builder's `content_identity` can correctly bind installed behavior only for files included in its canonical manifest. Stage 1 notices this, but places installed-package isolation at P10-G5, after prepare/finalize implementation work.

That ordering is too late because package identity is part of R1's production behavior identity and because source-repository fallback is forbidden from the beginning.

### Required amendment

Before prepare/provenance implementation proceeds:

1. add `context_packaging` to the deterministic release package managed roots, or move the required P9 implementation into another explicitly managed package root without changing its semantics;
2. ensure all P9 renderer code and required behavior-bearing resources needed by `/2` appear in the package manifest;
3. ensure all new P10 runtime code, schemas, provenance-registry schema/logic, prepared-invocation contract, and transport contract resources are managed;
4. bind the resulting install package `content_identity` into the prepared-invocation artifact;
5. prove the full `/2` path operates with the generic source repository absent;
6. prove installation drift or package replacement between prepare/finalize fails under R1.

The existing `reasoning-distiller-install-package/1` content-identity mechanism appears structurally capable of binding a newly managed `context_packaging` root; a new package major is not required merely to add that root. A release version/content identity change is required.

## R7. Tighten versioning and failure-class ownership

### Finding

Stage 1's major-version direction is correct, but several new failures cross the current preflight/activation boundary ambiguously.

Examples:

- unsupported exact P9 runtime ABI is knowable before successful rendering;
- installed package identity drift is a prepared-invocation/toolchain mismatch;
- prepared bundle identity mismatch is not the same as provider/model failure;
- transport-plane nonconformance may be detected by runner validation before a model call;
- unresolved provenance after raw output remains validation failure;
- raw-byte persistence must still occur before parse/RGP/provenance rejection when model output exists.

### Required amendment

Freeze the exact `/2` contract matrix and failure ownership before implementation:

```text
reasoning-distiller-invocation/2
reasoning-distiller-activation-bundle/2
reasoning-distiller-invocation-result/2
reasoning-distiller-context-provenance-registry/1
reasoning-distiller-prepared-invocation/1        # exact final name may differ
reasoning-distiller-model-transport/1            # if Stage 3 accepts R4 naming/direction
```

Required classification principles:

- malformed request, unsafe paths, input digest mismatch, unsupported context contract, eligibility mismatch, unsupported installed contract set, or incompatible local runtime discovered before rendering/provider execution: **preflight / exit 2**;
- P9 execution-binding mismatch, renderer limit failure, or inability to construct the exact activation under a valid request/toolchain: **activation / exit 3** unless an existing P9 failure contract already assigns a stricter stable class;
- runner/provider inability to preserve the logical transport contract before returning model output: **activation / exit 3**;
- invalid raw JSON after raw preservation: **parse / exit 4**;
- invalid RGP or unresolved candidate source IDs after raw preservation: **validation / exit 5**;
- immutable raw/prepared/registry/submission collision or write failure: **persistence / exit 6**;
- unexpected implementation failure: **internal / exit 1**.

Existing exact reason codes should be reused where semantics match. New reason codes should be frozen only for genuine new states.

Unknown majors continue to fail rather than downgrade or coerce.

## R8. Strengthen migration, rollback, and legacy non-interference gates

### Finding

Stage 1 correctly makes `/2` opt-in, but compatibility needs to cover more than request-schema acceptance.

P10 changes the installed package content and `rd_distill.py` implementation even for projects that continue to use `/1`. A release may therefore preserve `/1` semantics while still accidentally changing exact bundle bytes, reason classification, path handling, or installer behavior.

Rollback also needs to distinguish contract rollback from package downgrade. Selecting a `/1` request under a P10-capable package is not the same operation as installing an older release.

### Required amendment

The final plan must define and test three separate compatibility cases:

1. **Legacy request under new package**
   - `/1` strict request validation remains unchanged;
   - activation-bundle `/1` shape and deterministic mechanics remain byte-compatible for fixed inputs where the current contract promises determinism;
   - source registry, raw preservation, submission envelope, reason codes, and exit classes remain unchanged.

2. **Contract-selective rollback under new package**
   - callers may intentionally use `/1` instead of `/2`;
   - `/2` artifacts remain immutable history;
   - no conversion or deletion is performed.

3. **Package downgrade**
   - installer downgrade remains explicit under the installer contract;
   - the resulting installed tree contains exactly the older manifest payload, with no orphaned P10/P9 package files influencing `/1` behavior;
   - an older runtime receiving `/2` fails unsupported rather than approximating it.

P10 should not claim rollback safety until all three are proven.

## 5. Synthesis architecture

With R1-R8 incorporated, the recommended P10 architecture is:

```text
explicit upstream source/profile/eligibility selection
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
        validate exact installed package
        validate exact P9 runtime ABI
        render through closed P9 renderer
        derive stable provenance registry
        build activation-bundle/2
        build immutable prepared-invocation/1
                    |
                    v
      conforming model-transport/1 runner
                    |
                    v
          exact raw rgp/1 bytes
                    |
                    v
                 finalize
      verify exact prepared invocation
      preserve raw bytes immutably
      parse + validate rgp/1
      resolve provenance against exact registry
      persist ordinary immutable submission
      emit result/2 bound to prepared invocation
                    |
                    v
                   STOP
                    |
                    v
 separately authorized Steward reconciliation
 receiving submission + exact provenance handoff
```

The important refinement is that the production evidence root and the production execution identity are separate concepts:

```text
sealed context pack
    = sole project-evidence root

prepared invocation
    = immutable identity of the exact production transformation/toolchain
      that rendered and transported that evidence boundary
```

P10 must preserve both.

## 6. Provenance synthesis

The recommended provenance model is:

```text
context source binding
        |
        v
stable binding digest
        |
        v
opaque production source_id
        |
        +--> stable source record
        |
        `--> pack-local frame occurrences
                    |
                    v
          model-visible framed evidence
                    |
                    v
           candidate provenance IDs
```

Rules:

1. `source_id` semantics remain opaque to the model and Steward policy.
2. The ID is derived from exact canonical source-binding bytes, not caller naming.
3. A stable source record does not depend on which pack ordinal happened to contain it.
4. Pack identity and frame occurrence remain separately bound in the exact registry.
5. Every model-visible context frame maps to exactly one source ID before activation.
6. Every candidate provenance ID must resolve to the exact prepared registry before submission.
7. The registry grants no canonical standing or authority beyond what the underlying source binding already records.
8. Downstream reconciliation must receive the exact registry through a normative handoff, not ambient reconstruction.

## 7. Provider-plane synthesis

The runner boundary should preserve the following logical precedence without equating repository planes with provider privilege:

```text
installed Distiller directive
    -> framework/protocol instruction

rendered context control plane
    -> explicit project control evidence

rendered knowledge plane
    -> project knowledge evidence

rendered operational_evidence plane
    -> operational evidence
```

A provider adapter may choose different native message APIs, but the adapter must prove a semantic mapping that preserves this distinction. In particular:

- instruction-like text in knowledge remains knowledge;
- instruction-like text in operational evidence remains operational evidence;
- context `control` does not automatically become provider system/developer authority;
- the adapter does not reorder or omit frames;
- the adapter does not add extra project state.

If a provider API cannot represent a conforming mapping, that provider is unsupported for `/2` until a reviewed adapter exists.

## 8. Runtime and package synthesis

The initial production support matrix should deliberately be narrow:

```text
invocation:       reasoning-distiller-invocation/2
pack:             reasoning-distiller-context-pack/2
renderer profile: reasoning-distiller-context-renderer-profile/2
renderer:         reasoning-distiller-context-renderer/2
activation:       reasoning-distiller-context-rendered-activation/2
binding:          reasoning-distiller-renderer-execution-binding/1
binding scheme:   python-closed-bundle/1
runtime ABI:      cpython 3.12.0 / cpython-312
candidate:        rgp/1
submission:       existing RGP submission semantics, subject to R2 handoff decision
```

Broader Python support is a later compatibility amendment unless separately proven under the P9 identity contract.

The package must include `context_packaging` or the exact equivalent closed runtime surface in its deterministic manifest before `/2` implementation evidence is considered valid.

## 9. Additional pressure cases required by Stage 2

Stage 1 PI-01 through PI-40 remain useful. Add at least the following before protocol freeze.

| ID | Pressure case | Required outcome |
|---|---|---|
| PI-41 | Installed package content identity changes after `prepare` but before `finalize`, while pack/profile/eligibility bytes stay unchanged | `finalize` rejects prepared-invocation/toolchain drift; no ordinary submission |
| PI-42 | Provenance-bridge implementation changes after `prepare` but input files do not | prepared-invocation identity mismatch or installed-package drift fails; no rederived substitute registry accepted |
| PI-43 | Distiller directive bytes change after `prepare` | `finalize` rejects drift from exact prepared invocation |
| PI-44 | RGP validator bytes/identity change after `prepare` | `finalize` rejects drift unless a separately frozen prepared/finalize rule explicitly permits and proves equivalence |
| PI-45 | Runner receives activation bundle B but `finalize` is given request for activation bundle A | no valid `/2` success can be claimed; exact prepared-invocation identity must match |
| PI-46 | Same stable source binding occurs at different ordinals in two packs | same `source_id`; stable source record remains equivalent; pack-local occurrence mapping differs without changing source semantics |
| PI-47 | Same `source_id` is paired with materially different stable source-record fields | fail registry validation as provenance identity collision/inconsistency |
| PI-48 | Successful `/2` submission is handed to Steward without the exact companion provenance artifact required by R2 Option A | provenance handoff is incomplete; reconciliation must stop rather than search ambient state |
| PI-49 | Provider adapter maps context `control` to provider system authority without an approved transport rule | adapter non-conforming; no valid `/2` result claimed |
| PI-50 | Provider adapter flattens all context planes into one untyped prompt string | adapter non-conforming or activation failure |
| PI-51 | Provider adapter preserves logical planes using a provider-specific representation | conformance passes only when exact frame bytes/order and non-promotion invariants are proven |
| PI-52 | `/2` executes on CPython 3.12.1 or 3.13.x | fail closed under initial exact P9 runtime compatibility; no silent equivalence |
| PI-53 | Installed release package omits `context_packaging` while `/2` request is supplied | fail preflight; no source-repository fallback |
| PI-54 | Generic repository exists and contains a usable renderer while installed package lacks it | still fail; installed package remains the only production framework source |
| PI-55 | Fixed `/1` request executes under P10-capable package | `/1` deterministic bundle/result/submission mechanics remain unchanged |
| PI-56 | P10-capable package is explicitly downgraded to an older `/1`-only package | installed tree equals older manifest; P10/P9 managed files do not remain as behavior-affecting orphans |
| PI-57 | `/2` raw output is invalid JSON after a successful provider call | raw bytes persist first; parse failure follows; prepared/provenance artifacts remain immutable evidence |
| PI-58 | `/2` raw output cites only registered source IDs but registry artifact on disk differs from prepared-invocation digest | fail closed; do not accept current-file reconstruction |
| PI-59 | Pack/profile/eligibility are changed and then restored byte-for-byte before finalize | success may proceed only because exact prepared identities are unchanged; no history inference is required |
| PI-60 | Provider/runner is malicious and lies about transport | conformance contract explicitly does not claim cryptographic detection; stronger assurance is classified outside current P10 threat model |

Stage 3 may add more cases but should not weaken these to fit an implementation shortcut.

## 10. Revised implementation sequence and gates

Stage 1's gate sequence should be reordered so identity and packaging foundations exist before production adapter behavior.

| Gate | Required work | Exit criterion |
|---|---|---|
| **P10-G0 Threat/pressure freeze** | Freeze PI-01 through PI-60 with exact expected outcomes and explicit trusted-boundary assumptions | fixed-evidence, toolchain-drift, provenance-durability, provider-plane, runtime-ABI, and rollback attacks are machine-specifiable |
| **P10-G1 Protocol and handoff freeze** | Freeze invocation `/2`, activation-bundle `/2`, result `/2`, provenance-registry `/1`, prepared-invocation identity, transport conformance, downstream provenance handoff, exact reason codes, and compatibility matrix | no durable provenance or prepare/finalize identity rule remains implicit |
| **P10-G2 Installed-package closure** | Add the exact P9/P10 runtime surface to deterministic package managed roots; produce package identity covering renderer, bridge, schemas, directive, validator, and adapter; freeze exact CPython ABI support | installed package is a complete source-repository-independent `/2` execution surface |
| **P10-G3 Provenance bridge** | Implement stable binding-derived source IDs, stable source records, pack-local frame mappings, registry identity, and immutable registry persistence | every frame resolves exactly; same source ID cannot map to conflicting stable records; downstream registry artifact is durable |
| **P10-G4 Prepare integration** | Validate sealed inputs, package identity/runtime compatibility, eligibility, P9 renderer binding, provenance registry, activation bundle, and prepared-invocation identity | exact sealed pack is sole project-evidence root and exact production toolchain/activation identity is frozen before provider execution |
| **P10-G5 Provider transport conformance** | Implement/reference-test provider-neutral logical transport mapping and at least one conforming runner path | exact bundle/plane semantics are preserved; unsupported providers fail rather than reinterpret |
| **P10-G6 Finalize integration** | Consume exact prepared invocation, preserve raw bytes, validate `rgp/1`, resolve against exact registry, persist submission/result, and reject all drift | candidate is provably bound to the exact prepared invocation; changed installation/registry/bundle cannot be substituted |
| **P10-G7 Legacy/migration/rollback** | Prove `/1` exact non-interference, contract-selective rollback, explicit package downgrade, old-runtime `/2` rejection, and no orphan behavior | no silent migration or legacy drift |
| **P10-G8 Candidate-bound evidence** | Run the complete P10 suite plus unaffected production and P0-P9 regressions on one immutable candidate/package/runtime tuple | exact candidate/package/runtime-bound evidence exists for fresh independent implementation review |

No gate begins from this Stage 2 review alone. Stage 3 Steward reconciliation must first establish the authoritative P10 implementation plan and exact next authorized action.

## 11. Required acceptance criteria for the reconciled architecture

A Stage 3 plan should not authorize implementation unless it requires all of the following:

- `/1` remains unchanged and explicitly selected;
- `/2` accepts one prebuilt `context-pack/2` plus exact renderer profile and eligibility binding;
- original source files are never reopened by `/2` prepare/finalize;
- the exact installed package identity is part of production execution identity;
- the package deterministically contains the entire required P9/P10 runtime surface with no source-repository fallback;
- initial `/2` runtime support is exactly compatible with the closed P9 ABI or a separately reviewed execution environment;
- `prepare` creates an immutable prepared-invocation identity over request, sealed inputs, installed toolchain, registry, rendered activation, and activation bundle;
- `finalize` verifies that exact prepared invocation rather than trusting current-file reconstruction;
- the provenance registry is durably persisted and normatively handed to downstream Steward reconciliation;
- stable source IDs cannot map to conflicting source records across packs;
- pack-local frame occurrence data remains distinct from stable source-binding identity;
- every model-visible context frame resolves to exactly one derived source ID;
- candidate provenance references only the exact prepared registry;
- provider transport has a frozen logical conformance contract preserving planes, frame bytes/order, and non-promotion semantics;
- context `control` is not silently promoted to provider system/developer authority;
- knowledge or operational evidence cannot be promoted by text shape;
- provider/runner conformance is not mislabeled as cryptographic hostile-provider attestation;
- raw model bytes are preserved before parse/RGP/provenance validation;
- no returned candidate is repaired into success;
- successful output remains an ordinary immutable `rgp/1` candidate graph;
- any required provenance companion artifact is explicit in the successful downstream handoff rather than hidden in chat or ambient state;
- no P10 operation reconciles, admits, activates, authorizes, or mutates canonical/authority state;
- package/runtime/request rollback semantics are explicitly distinguished and tested;
- exact candidate/package/runtime-bound evidence plus fresh independent implementation review are required before P10 closure.

## 12. Stage 2 recommendation

The Stage 1 **sealed-context `/2` direction should be retained**, but it is not implementation-ready as written.

The central architecture is sound:

- keep `/1` unchanged;
- make `/2` explicit;
- use one sealed pack as the sole project-evidence root;
- use the P9 renderer to preserve structural planes;
- derive production provenance from the pack;
- preserve raw output and ordinary RGP validation/submission boundaries;
- keep reconciliation/admission separate.

The required synthesis adds one missing production identity layer:

> The sealed pack fixes **what project evidence may be used**. A prepared-invocation artifact must separately fix **which installed production behavior transformed that evidence, which exact registry and activation were handed across the model boundary, and what finalization is allowed to accept**.

Without that second identity, `/2` can preserve source selection while still losing reproducibility and provenance closure between `prepare` and `finalize`.

Therefore the Stage 2 disposition is:

**`P10_PRODUCTION_INTEGRATION_STAGE2_COMPATIBLE_WITH_REQUIRED_REVISIONS`**

R1-R8 are mandatory inputs to Stage 3 reconciliation.

## 13. Terminal boundary and receiving role

This document completes only **P10 Stage 2 independent Engineer review and synthesis** under `proposal-review-synthesis/1`.

No P10 implementation, production contract mutation, package release, Steward reconciliation, admission, canonical mutation, authority mutation, or activation mutation has been performed.

A meaningful chat/workflow boundary is reached here because the next consequential action belongs to a different role and requires authoritative reconciliation rather than continued independent review.

Receiving role: **fresh Project Engineering Steward**, scoped only to **P10 Stage 3 reconciliation**.

The receiving Steward should independently establish whatever Steward authorization and accepted activation evidence the live repository requires, then reconcile:

1. the original P10 problem and constraints;
2. Stage 1 proposal commit `0a2909d5a88c9a7d8f7abbf1b2c59f2abd34b723`, blob `cd9dd25c9209dbb066e8017c2256f4647037dec7`;
3. this complete Stage 2 review/synthesis;
4. governing production invocation contract;
5. governing context-packaging plan;
6. closed P9 candidate/reconciliation and renderer-identity amendment;
7. current package/install and RGP submission contracts relevant to the required amendments.

The Steward must explicitly disposition R1-R8, preserve any disagreement rather than describing it as consensus, freeze the authoritative ordered implementation gates and acceptance criteria, and identify the exact next authorized action.

Stop before P10 implementation, production mutation, admission, canonical mutation, authority mutation, or any successor work unit.
