# P5 Selection-Provenance Representation Amendment - Stage 1 RPG Engineer Proposal

Status: **Proposed**
Method: `proposal-review-synthesis/1`
Repository: `loteque/reasoning-distiller`
Coordination control ref: `main`
Coordination revision inspected and re-resolved before this Stage 1 write: `40241e24ecca2dacf0848ee28cf1ddc1410d15f1`
Stage: **Stage 1 independent proposal**
Proposal-author scope: **Reasoning Graph Protocol Engineer**

Authority posture: this artifact is a technical proposal only. It does not establish registered role identity, Project Steward authorization, accepted RIL activation, reconciliation, admission, canonical standing, implementation approval, or project authority. It does not authorize P5 remediation, P6 persistence, or any successor work unit.

## 1. Problem and decision requested

P5 cannot currently represent the full valid P1d/P3 projection domain in the outer selection-provenance ledger.

The frozen P1d closure descriptor defines PEMS semantic identity as:

```text
(namespace, id)
```

where the established namespaces are `record` and `relation`. P3 preserves that identity in every `ProjectionCause(namespace, semantic_id, kind, cause_id)` and can validly project a PEMS document in which a record and a relation share the same string ID.

The frozen P1b pack schema instead gives a knowledge-ledger subject only an optional scalar `semantic_id`. P5 therefore cannot distinguish these two valid subjects:

```text
(record,   "shared")
(relation, "shared")
```

Candidate `a8a0592a69b325d411b36bbc97deadee796c3fd7` detects the collision and rejects the otherwise valid P3 result as `PEMS_SEMANTIC_INVALID`. Independent review `0df24253d653725686a616e3cb4ddbd581a4bd13` correctly classifies this as a protocol-representation mismatch rather than invalid PEMS.

The decision requested is:

> Define a governed, deterministic outer-ledger representation that can identify every P1d/P3 PEMS semantic item without ambiguity, including record/relation string-ID collisions, while preserving P1d/P3 semantics and explicitly resolving the P1b/P1c schema, versioning, compatibility, digest, toolchain, eligibility, and migration consequences.

This proposal does **not** presuppose that adding a namespace member to the existing `/1` object is the correct solution.

## 2. Bound evidence and semantic basis

The proposal is based on these immutable inputs:

| Evidence | Identity | Relevance |
|---|---|---|
| Governing implementation plan | commit `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`, blob `8474d2da42f863f0a190fd80292085176d3f97f0` | Requires deterministic outer selection provenance, protocol freeze before later implementation, and no silent semantic truncation |
| P1b reviewed schema basis | candidate `cffc2c27da64f052380a1a5a26a42bb7621b0335` | Freezes the `/1` profile/request/pack/result schemas and closed-world ledger subject |
| P1b pack schema | blob `4b240a5698294ce1a217ad758b4031830740fc29` | `knowledgeLedgerSubject` has `source_ref` plus optional scalar `semantic_id`; unknown members are rejected |
| P1c accepted remediation basis | candidate `ec5fe4c6c7e8678c3ead0ac629d97d04022b914c` | Freezes bytes, digest preimages, builder ordering, toolchain identity, and exact P1b schema basis |
| P1c base contract | blob `97cd7bce6be427e8ae0703d3c0a086abf7ad7a67` | States that later intentional schema revision requires a new reviewed basis and cannot silently inherit P1c identity |
| P1d accepted semantic basis | candidate `945ff72ccee87310642ff78c4b4c8e01c46fb551` | Freezes PEMS visited identity as `(namespace,id)` |
| P1d closure descriptor | blob `43dd9fe88e2953d12ed0630cf6a33e53a0ecf7a3` | Declares record and relation identifier namespaces independently |
| P1e eligibility basis | candidate `e6e9d318724a2d13e3b820f8208bdb623d61e482` | Eligibility binds the exact `(profile_id, profile_version, raw_sha256)` requested profile |
| P3 semantic candidate | `197956138e6181ed9f9aae1d6a40b9f5084695a8` | Preserves namespace on `ProjectionCause`; indexes and visits records and relations separately |
| P3 projection implementation | blob `b984552d9f7da9f5c1001ebabce810fa27cafc4c` | Uses `(namespace, semantic_id)` as the semantic item key |
| P4 semantic base | `c5e265aa2c572b6156c987bfa75e3740c097f2ec` | Direct parent of P5; no relevant identity change |
| P5 candidate | `a8a0592a69b325d411b36bbc97deadee796c3fd7` | Groups outer knowledge provenance by scalar semantic ID and rejects namespace collisions |
| P5 independent review | `0df24253d653725686a616e3cb4ddbd581a4bd13` | Disposition `P5_INDEPENDENT_REVIEW_CHANGES_REQUIRED`; blocker 2 requires governed earlier-protocol revision |

The P5 review also contains a separate lowercase-SHA blocker. That blocker is locally remediable in P5 and remains outside this Stage 1 protocol decision.

## 3. Required invariants

Any accepted representation must preserve all of the following:

1. **PEMS identity invariant:** outer provenance identifies a PEMS item by the same `(namespace,id)` identity already frozen by P1d/P3.
2. **No semantic rewrite:** PEMS records, relations, provenance, closure rules, PEMS schema semantics, and P3 projection semantics are unchanged.
3. **Exact source invariant:** the canonical snapshot reference remains part of the outer subject, so equal PEMS IDs in different snapshots remain distinct subjects.
4. **Cause preservation invariant:** multiple deterministic causes for one exact namespaced item are all preserved and canonically ordered.
5. **Closed-world invariant:** malformed or unknown semantic identity members fail rather than being ignored.
6. **No tagged-string ambiguity:** representation must not depend on an ad hoc delimiter or escaping convention inside arbitrary PEMS IDs.
7. **Version honesty:** incompatible wire/schema meaning must not be published under an indistinguishable contract identity.
8. **P1c replay invariant:** the revised protocol must define exactly which canonical digests remain stable and which must change.
9. **Eligibility invariant:** a revised profile is not silently treated as eligible merely because its predecessor was eligible.
10. **Migration invariant:** immutable `/1` packs are not rewritten in place, and ambiguous legacy provenance is never guessed.
11. **P5 boundary invariant:** the amendment enables a later fresh P5 remediation; it does not itself implement or approve that remediation.
12. **No successor expansion:** P6 persistence, rendering, production integration, authority, reconciliation, admission, and activation remain out of scope.

## 4. Pressure cases

These pressure cases should be materialized before the amendment is implemented.

| ID | Pressure case | Required outcome |
|---|---|---|
| SP-01 | A selected record and selected relation in one snapshot both have ID `shared` | Both produce distinct ledger subjects and retain their own causes |
| SP-02 | Record `shared` is a request root while relation `shared` is reached by PEMS closure | Both remain distinct; cause kinds are preserved without collision |
| SP-03 | One namespaced item is reached by multiple selectors/closure paths | One exact subject, all deterministic causes |
| SP-04 | Two canonical snapshots contain the same `(namespace,id)` | `source_ref` keeps them distinct |
| SP-05 | PEMS IDs contain `:`, `/`, `#`, JSON-looking text, or strings beginning with `record:`/`relation:` | No escaping/tag parsing is required; IDs remain exact opaque strings |
| SP-06 | Namespace is missing, misspelled, or outside `{record,relation}` | Closed schema rejection |
| SP-07 | A `/2` knowledge semantic subject uses legacy `semantic_id` instead of the new representation | Closed schema rejection |
| SP-08 | A legacy `/1` pack has scalar `semantic_id` that occurs in exactly one namespace of the referenced PEMS | An explicit compatibility/migration adapter may resolve it deterministically |
| SP-09 | A legacy `/1` pack's scalar `semantic_id` occurs in both namespaces | Migration from the pack alone fails as ambiguous; no guessing |
| SP-10 | `/1` input is presented to a `/2` builder or `/2` output to a `/1` validator | Fail by explicit contract/schema mismatch |
| SP-11 | Equivalent PEMS/source payloads are rebuilt under `/1` and `/2` protocol families | Stable and changed digest domains match the table in Section 9 |
| SP-12 | Host iteration order changes for projection causes and ledger construction | Canonical `/2` bytes remain identical |
| SP-13 | Snapshot-level knowledge inclusion has no PEMS semantic item | The source-only snapshot ledger subject remains valid and distinct from semantic-item subjects |
| SP-14 | The same namespaced item has duplicate identical causes | Exact duplicate causes may be coalesced only under an explicitly frozen rule; distinct causes must never be lost |

## 5. Alternatives considered

### A. Add `semantic_namespace` beside `semantic_id` in the existing `/1` schema

Shape:

```json
{
  "source_ref": {"...": "..."},
  "semantic_id": "shared",
  "semantic_namespace": "record"
}
```

**Advantages**

- Smallest source-code patch.
- Directly mirrors the P1d tuple.

**Problems**

- P1b `/1` has `additionalProperties: false`; old `/1` validators reject the new member.
- P1c binds the exact P1b schema blobs and explicitly requires a new reviewed basis for later schema revision.
- Publishing changed wire bytes under the same `reasoning-distiller-context-pack/1` contract would create two non-equivalent `/1` dialects.
- The current toolchain record does not independently identify the context-pack schema blob, so the outer contract string is an important compatibility discriminator.

**Disposition:** reject as an in-place `/1` change. The two-field shape remains technically viable only inside an honestly versioned new contract.

### B. Encode the namespace inside the existing scalar `semantic_id`

Examples:

```text
record:shared
relation:shared
```

or a length-framed/tagged string.

**Advantages**

- Could preserve P1b schema bytes.
- Avoids adding a member.

**Problems**

- Silently changes `semantic_id` from the exact PEMS ID into a compound serialization.
- Requires new escaping/framing semantics for arbitrary PEMS IDs.
- Existing consumers can accept the bytes structurally while interpreting the field incorrectly, which is worse than a clean version mismatch.
- The P1d tuple becomes hidden in a string codec rather than structurally represented.

**Disposition:** reject.

### C. Add sibling `semantic_namespace` and `semantic_id` in a new `/2` pack family

**Advantages**

- Straightforward.
- Minimal difference from the `/1` ledger shape.

**Problems**

- Preserves a legacy field name whose old standalone meaning is no longer sufficient.
- Creates avoidable partial states at the object-model level unless the schema carefully requires both together.
- Represents one semantic identity as two loosely associated sibling fields.

**Disposition:** acceptable fallback, but not preferred.

### D. Replace scalar `semantic_id` with a structured semantic reference in a new `/2` pack family

Proposed shape:

```json
{
  "source_ref": {"...": "..."},
  "semantic_ref": {
    "namespace": "record",
    "id": "shared"
  }
}
```

**Advantages**

- Represents the already-frozen P1d identity tuple directly.
- Keeps arbitrary PEMS IDs opaque; no delimiter convention exists.
- Namespace and ID are structurally atomic and independently validated.
- Cleanly removes the misleading `/1` scalar shortcut from `/2` canonical output.
- Extends naturally if a future governed PEMS version introduces another established semantic namespace, through an explicit later version rather than string parsing.

**Costs**

- Requires a real wire-version revision and compatibility handling.
- Produces expected identity churn in canonical `/2` packs.

**Disposition:** **recommended**.

### E. Identify PEMS items by JSON Pointer or array position

**Disposition:** reject. Array position is representation order, not PEMS semantic identity; it would couple provenance to ordering and weaken replay/migration semantics.

### F. Put namespace information only in causes

**Disposition:** reject. Causes answer *why* an item was included. They must not become the only way to infer *which* subject the causes belong to.

## 6. Proposed protocol architecture

### 6.1 Preserve `/1` bytes; introduce side-by-side `/2` schemas

Do not edit the accepted `/1` schema files while claiming `/1` compatibility.

Introduce side-by-side schema artifacts with distinct `$id` values, for example:

```text
schemas/context-profile-v2.schema.json
schemas/context-pack-request-v2.schema.json
schemas/context-pack-v2.schema.json
schemas/context-pack-result-v2.schema.json
```

with contract values:

```text
reasoning-distiller-context-profile/2
reasoning-distiller-context-pack-request/2
reasoning-distiller-context-pack/2
reasoning-distiller-context-pack-result/2
```

The following contracts can remain `/1` because this amendment does not change their wire semantics:

```text
reasoning-distiller-context-pack-failure/1
reasoning-distiller-context-profile-eligibility/1
reasoning-distiller-context-source-binding/1
reasoning-distiller-context-pack-receipt/1
```

The `/2` profile must bind the `/2` request/pack/result family explicitly while continuing to bind the unchanged shared contracts by their existing versions.

The `/2` request must require:

```text
contract = reasoning-distiller-context-pack-request/2
output.pack_contract = reasoning-distiller-context-pack/2
```

The `/2` result success form must identify:

```text
contract = reasoning-distiller-context-pack-result/2
pack.contract = reasoning-distiller-context-pack/2
```

### 6.2 `/2` knowledge-ledger subject

Define a closed semantic reference:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["namespace", "id"],
  "properties": {
    "namespace": {"enum": ["record", "relation"]},
    "id": {"type": "string", "minLength": 1}
  }
}
```

Define the knowledge subject as exactly one of two closed shapes:

1. snapshot subject:

```json
{
  "source_ref": {"...": "canonical snapshot ref"}
}
```

2. PEMS semantic-item subject:

```json
{
  "source_ref": {"...": "canonical snapshot ref"},
  "semantic_ref": {
    "namespace": "record | relation",
    "id": "exact PEMS id"
  }
}
```

`semantic_id` is not a `/2` field.

This preserves the existing snapshot-level inclusion record while making every semantic-item ledger entry unambiguous.

### 6.3 Builder grouping semantics

For `/2`, P5 must group semantic causes by the exact key:

```text
(JCS(canonical_snapshot_ref), namespace, id)
```

or an equivalent lossless internal tuple.

A record and relation with the same string ID are therefore independent keys.

Before emission, every semantic subject must be proven present in the P3 projection in the named namespace. The complete expected subject set is:

```text
{("record", record.id) for record in pems.records}
union
{("relation", relation.id) for relation in pems.relations}
```

Coverage is exact against P3 causes. A namespace collision is no longer an error because it is not an identity collision.

### 6.4 Cause semantics remain unchanged

The existing cause vocabulary remains:

```text
profile_slot
request_selector
pems_closure
```

No namespace is moved into `cause_id` semantics. Existing P3 cause IDs may remain unchanged. Multiple causes are associated with the exact namespaced subject and canonically ordered under the existing P1c rule.

## 7. P1d and P3 preservation

This amendment should require **no P1d semantic revision** and **no P3 semantic revision**.

P1d already contains the needed identity model:

```text
visited_identity = (namespace,id)
```

and separately declares:

```text
record.id   -> namespace record
relation.id -> namespace relation
```

P3 already carries namespace in `ProjectionCause` and uses `(namespace,id)` internally for selection, cycle termination, and cause aggregation.

The amendment therefore changes only the outer packaging representation that consumes P3 output. Any implementation proposal that rewrites P1d or removes P3 namespace information to fit the old ledger would invert the dependency direction and should be rejected.

## 8. P1b and P1c versioning consequences

### 8.1 P1b schema family

The accepted `/1` schemas remain immutable historical contracts.

The `/2` family is a new reviewed schema basis, not an edit that claims the old blob identities. Conformance must mechanically prove the accepted `/1` blobs remain unchanged.

### 8.2 P1c bytes/digests/toolchain contract

Introduce a reviewed successor contract, for example:

```text
reasoning-distiller-context-pack-bytes-digests-toolchain/2
```

It should inherit the `/1` byte representation, RFC 8785 JCS behavior, digest framing, domain names, ordering principles, lowercase canonical SHA-256 rule, and non-circular identity construction except where this proposal explicitly changes the bound schema family and pack-builder identity.

The `/2` P1c basis must bind the exact new `/2` schema blobs. It must not claim the old P1c schema-basis identity.

The canonical inclusion-ledger ordering remains:

```text
(plane_rank, JCS(subject))
```

No new namespace-specific sort rank is necessary because namespace and ID are inside the canonical subject value.

### 8.3 Pack-builder toolchain identity

A builder that emits the new pack representation has changed externally observable behavior. Its contract should therefore become, for example:

```text
reasoning-distiller-context-pack-builder/2
```

The corresponding toolchain component must bind the `/2` builder contract and exact implementation artifact identity.

The following behavior artifacts remain unchanged unless later evidence independently requires revision:

```text
pems_schema
pems_validator
closure_descriptor
jcs_serializer
cove_adapter (when used)
```

This amendment should not expand the toolchain role vocabulary merely to solve the provenance subject mismatch.

## 9. Digest and identity consequences

For identical immutable source bindings and identical selected PEMS/COVE payloads, an explicit `/1` to `/2` rebuild has the following expected identity behavior.

| Value | Expected across equivalent `/1` and `/2` semantic inputs | Reason |
|---|---|---|
| Raw source `raw_sha256` | **Stable** | Source bytes unchanged |
| Canonical source `pems_sha256` | **Stable** | Canonical PEMS source bytes unchanged |
| Canonical-state-binding digest | **Stable** if the binding object is unchanged | Binding preimage does not contain pack contract |
| `selected_pems_sha256` | **Stable** if snapshot refs and selected PEMS objects are unchanged | PEMS projection digest does not include outer ledger |
| `cove_payload_sha256` | **Stable** when COVE payloads are unchanged | COVE payload-set body unchanged |
| `payload_set_sha256` | **Stable** when plane payloads and source refs are unchanged | Payload-set preimage does not include inclusion ledger or top-level pack contract |
| Profile raw digest | **Changes** for a migrated `/2` profile | Profile bytes and contract bindings change |
| `identity.profile_sha256` | **Changes** | Canonical profile value changes |
| Request raw digest | **Changes** for a `/2` request | Request contract/output pack contract and profile binding change |
| `identity.request_sha256` | **Changes** | Canonical request value changes |
| `manifest_sha256` | **Changes** | Manifest retains pack contract, profile/request identities, inclusion ledger, and toolchain |
| `pack_identity_sha256` | **Changes** | Its component digests include changed profile/request/manifest identities |
| Receipt `serialized_pack_sha256` | **Changes** | Canonical serialized pack bytes change |

No new digest domain is required solely for the structured semantic reference. Existing domain separation remains valid because the changed canonical values enter the existing framed preimages.

The existing `reasoning-distiller-context-pack-identity-preimage/1` shape may remain if its member set is unchanged. The `/2` pack identity differs naturally through its changed component digests. Stage 2 should specifically challenge whether retaining that preimage contract label is sufficiently explicit; this Stage 1 proposal sees no semantic need to bump it.

## 10. Compatibility and migration

### 10.1 Reader compatibility

A consumer that supports both versions should dispatch on the explicit top-level contract and validate against the corresponding immutable schema family.

It must not:

- validate `/2` bytes with the `/1` schema;
- treat `/1` scalar `semantic_id` as if it were already a `/2` semantic reference;
- accept a mixed ledger containing both canonical forms;
- auto-upgrade bytes before identity verification.

### 10.2 Builder compatibility

A `/2` builder should consume a `/2` profile/request family and emit only `/2` pack/results. It should not silently coerce `/1` inputs.

Supporting `/1` build behavior, if retained, should be a separate explicit compatibility entry point or implementation path with its own frozen behavior identity.

### 10.3 Existing immutable `/1` packs

Existing `/1` bytes remain `/1` bytes. They are never rewritten in place.

An explicit compatibility adapter may derive a `/2` semantic subject from a `/1` scalar `semantic_id` only when the referenced PEMS object proves that the ID occurs in exactly one of the two established namespaces.

If the same legacy scalar occurs in both namespaces, migration from that pack alone is ambiguous and must fail. No cause text, array order, heuristic, or model judgment may choose the namespace.

The motivating record/relation collision cannot be represented by the reviewed P5 `/1` candidate at all, so the correct path for that case is a fresh `/2` build from the exact P3 projection/source inputs, not migration from nonexistent canonical `/1` output.

### 10.4 Profile migration and eligibility

A `/2` profile is a new profile artifact because its contract and bound protocol-family values differ from `/1`.

Migration should produce a distinct `profile_version` value rather than mutating an existing profile version in place.

P1e binds eligibility to the exact requested tuple:

```text
(profile_id, profile_version, raw_sha256)
```

Therefore an eligibility binding that names the old `/1` profile does **not** automatically establish eligibility for the migrated `/2` profile. A governed consumer must supply an eligibility binding that names the exact `/2` profile identity. Whether the same underlying policy-evidence snapshot can support that new binding is a consumer-policy decision; the packer must not infer it.

This requirement is a compatibility consequence, not a new authority rule.

## 11. Failure and recovery behavior

The new canonical representation removes the current false `PEMS_SEMANTIC_INVALID` outcome for namespace collisions.

The `/2` builder should continue to fail when:

- a P3 cause names an unsupported namespace;
- a cause names an ID absent from that namespace in the projection;
- one or more projected semantic items lack deterministic provenance coverage;
- the `/2` wire object is malformed;
- profile/request/pack contract versions are incompatible.

A compatibility/migration adapter should fail separately when a `/1` scalar semantic ID is ambiguous. This proposal does not require that adapter-local migration failure to be added to the generic context-pack failure vocabulary unless Stage 2/Stage 3 decide the adapter is itself a public protocol surface.

## 12. Implementation sequence and gates after reconciliation

No step below is authorized merely by this Stage 1 proposal. It is the proposed sequence for a later reconciled plan.

1. **Pressure-case freeze**
   - Materialize SP-01 through SP-14.
   - Prove the original P1d/P3 collision case independently before changing pack code.

2. **Schema-family freeze**
   - Add side-by-side `/2` profile/request/pack/result schemas.
   - Keep every accepted `/1` schema blob byte-identical.
   - Add positive and negative `/2` fixtures for `semantic_ref`.

3. **P1c successor freeze**
   - Add the `/2` exact schema basis.
   - Freeze unchanged JCS/digest domains and expected changed/stable digest behavior.
   - Freeze `/2` pack-builder toolchain contract identity.

4. **Eligibility compatibility gate**
   - Add conformance evidence that old profile-eligibility bindings do not match migrated `/2` profile identities unless a new exact binding is supplied.
   - Do not change P1e's acceptance predicate.

5. **Fresh P5 implementation activation**
   - Begin only after Stage 2 review and separately authorized Stage 3 reconciliation approve the amendment.
   - Apply the already identified lowercase-SHA remediation.
   - Replace scalar semantic grouping with exact namespaced subjects.
   - Remove the false record/relation collision rejection.
   - Emit `/2` canonical pack/result behavior only as approved.

6. **P5 regression/evidence gate**
   - Exact P5 suite including SP-01/SP-02 collision cases.
   - P1-P4 unaffected regressions.
   - Explicit `/1` immutability/compatibility checks.
   - Preserve the three inherited reds from the prior P5 review separately unless independently remediated under their own scope.
   - Produce a new immutable P5 candidate with candidate-bound execution evidence.

7. **Stop at P5**
   - P6 does not begin merely because a new P5 candidate passes.

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Version-family expansion creates maintenance overhead | Bump only the contracts whose current schemas hard-bind the old pack family; share unchanged failure/source/eligibility/receipt contracts |
| Consumers accidentally accept both ledger shapes in one canonical schema | `/2` uses closed-world `oneOf` subject shapes and excludes legacy `semantic_id` |
| Hidden migration inference reintroduces ambiguity | Migration is explicit, deterministic, and fails on a legacy ID present in both namespaces |
| Unnecessary P1d/P3 churn | Treat their existing `(namespace,id)` semantics as the invariant to preserve, not code to rewrite |
| Identity churn surprises caches/artifact stores | Freeze the digest consequence table and require version-aware cache keys/receipt handling |
| Old eligibility is copied to new profiles | Require exact `/2` profile identity in a newly applicable P1e binding |
| Tagged IDs tempt a schema-free shortcut | SP-05 forces arbitrary opaque IDs and forbids delimiter-based semantics |
| Amendment accidentally absorbs P5 blocker 1 or P6 work | Keep blocker 1 as later P5-local remediation and stop the governed amendment before implementation/P6 |

## 14. Acceptance criteria for the amendment

A final reconciled amendment should not authorize P5 implementation until it makes all of these statements mechanically testable:

1. `/1` accepted schema blobs remain unchanged.
2. `/2` canonical knowledge semantic subjects structurally carry exact `{namespace,id}` identity.
3. `/2` rejects the legacy scalar `semantic_id` form.
4. P1d and P3 semantic artifacts require no semantic reinterpretation.
5. A record and relation with the same string ID in one snapshot produce two distinct canonical ledger subjects.
6. Multiple causes for one exact namespaced subject are preserved.
7. Equivalent host iteration orders produce byte-identical `/2` output.
8. `/1` and `/2` contract families fail closed when crossed at validation/build boundaries.
9. Stable versus changed digest expectations match Section 9.
10. The `/2` builder/toolchain behavior identity is explicit.
11. Existing immutable `/1` packs are never rewritten in place.
12. Legacy ambiguous scalar provenance cannot be migrated by guesswork.
13. A migrated `/2` profile requires an eligibility binding for its exact new identity when the governed consumer requires eligibility.
14. P5's lowercase-SHA blocker remains separately remediated and tested.
15. No P6, renderer, production integration, canonical mutation, authority, activation, reconciliation, or admission work is included.

## 15. Stage 1 recommendation

**Recommend Alternative D: a side-by-side `/2` context-pack protocol family whose knowledge semantic ledger subject replaces scalar `semantic_id` with a structured `semantic_ref = {namespace,id}`.**

The decisive reason is not cosmetic schema preference. P1d/P3 already established a two-part semantic identity. A structured `/2` reference preserves that existing semantic truth directly, while an in-place `/1` member addition would create two incompatible `/1` dialects and a tagged-string workaround would hide a protocol tuple inside an ad hoc codec.

The amendment should preserve P1d/P3 bytes and semantics, preserve unchanged P1c digest machinery, introduce a new exact P1b/P1c schema basis for `/2`, bump the pack-builder behavior contract, define explicit version-aware compatibility/migration rules, and require exact re-binding of governed profile eligibility for migrated `/2` profiles.

## 16. Unresolved questions for independent Stage 2 challenge

Stage 2 should independently challenge at least these points rather than merely endorsing this proposal:

1. Is bumping profile/request/result alongside pack the smallest honest version boundary, or is there a better contract-family partition that preserves exact compatibility without mutating `/1` meanings?
2. Should the nested field be named `semantic_ref`, `pems_ref`, or another term that better constrains its scope without creating unnecessary coupling?
3. Is retaining `reasoning-distiller-context-pack-identity-preimage/1` appropriate when the preimage shape is unchanged, or should the outer version boundary also bump that label for operational clarity?
4. Can `reasoning-distiller-context-pack-receipt/1` safely remain shared across pack versions, or should receipts carry/bind pack contract explicitly in a later reviewed revision?
5. Should a public `/1` to `/2` migration adapter exist at all, given that the motivating collision requires a rebuild from P3/source inputs rather than migration of a valid `/1` pack?
6. Are any current readers, fixture generators, or persistence assumptions coupled to the unversioned schema filenames in a way that changes the rollout sequence?

## 17. Stage boundary

This artifact completes **Stage 1 independent proposal** only.

A meaningful independence boundary is now reached. The next activation should be a **fresh independent Engineer Stage 2 review and synthesis** under `proposal-review-synthesis/1`, receiving:

- the original problem and constraints;
- coordination revision `40241e24ecca2dacf0848ee28cf1ddc1410d15f1`;
- governing plan `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd` / blob `8474d2da42f863f0a190fd80292085176d3f97f0`;
- P5 candidate `a8a0592a69b325d411b36bbc97deadee796c3fd7`;
- P5 review `0df24253d653725686a616e3cb4ddbd581a4bd13`;
- this complete immutable Stage 1 proposal.

Stage 2 must independently reconstruct the constraints and challenge the architecture, especially the version-family boundary, digest/migration consequences, and whether the structured reference is the smallest robust representation.

Do not begin Stage 3 Steward reconciliation, P5 implementation remediation, P6 persistence, admission, authority, or activation from this Stage 1 artifact.
