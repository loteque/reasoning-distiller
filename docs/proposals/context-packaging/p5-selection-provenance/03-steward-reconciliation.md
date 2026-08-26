# P5 Selection-Provenance Representation Amendment - Stage 3 Steward Reconciliation

Disposition: **PROPOSAL_ACCEPTED_WITH_REVISIONS**
Method: `proposal-review-synthesis/1`
Repository: `loteque/reasoning-distiller`
Coordination control ref: `main`
Coordination revision inspected and re-resolved immediately before this Stage 3 write: `40241e24ecca2dacf0848ee28cf1ddc1410d15f1`
Stage: **Stage 3 Steward reconciliation/finalization**
Steward scope: **semantic reconciliation only**

This artifact reconciles the exact Stage 1 proposal and Stage 2 independent review identified below. It does not perform P5 implementation, P6 persistence, admission, canonical PEMS/COVE mutation, role registration, Steward authorization mutation, or any other successor operation.

## 1. Bound evidence and authority posture

### 1.1 Governing evidence

- governing implementation plan: commit `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`, blob `8474d2da42f863f0a190fd80292085176d3f97f0`;
- live coordination revision: `main@40241e24ecca2dacf0848ee28cf1ddc1410d15f1`;
- Steward directive: `agents/steward/DIRECTIVE.md` at the live coordination revision;
- proposal-review contract: `docs/governance/PROPOSAL_REVIEW_METHOD.md` at the live coordination revision;
- activation contract: `docs/operations/RIL_ACTIVATION_EVIDENCE_CONTRACT.md` at the live coordination revision;
- Steward-authorization contract: `docs/operations/RIL_STEWARD_AUTHORIZATION_CONTRACT.md` at the live coordination revision;
- role-registry contract: `docs/operations/RIL_ROLE_REGISTRY_CONTRACT.md` at the live coordination revision;
- chat-transition amendment: `docs/operations/PROJECT_CHAT_TRANSITION_AMENDMENT.md` at the live coordination revision.

### 1.2 Exact Stage 1 and Stage 2 artifacts

- Stage 1 proposal: commit `a29806386bf493e5005b19633876e7035da51460`, path `docs/proposals/context-packaging/p5-selection-provenance/01-rpg-engineer-proposal.md`, blob `6bcd8b148fa2de805100599b7914a1a8f693667d`;
- Stage 2 independent review: commit `0ef9faca7d830951d7170ef83a44f850423003ef`, path `docs/proposals/context-packaging/p5-selection-provenance/02-independent-engineer-review.md`, blob `2970e4b7eca727b16e9cca4001923617aa43a676`, disposition `COMPATIBLE_WITH_REQUIRED_REVISIONS`.

### 1.3 Steward authorization

The authoritative Steward-authorization history at the live coordination revision contains two contiguous events. Replay produces:

```json
{"assignments":{"admission":"steward:default","semantic_reconciliation":"steward:default"},"contract":"reasoning-distiller-steward-authorization-state/1"}
```

That replay digest is `sha256:0313b8cbad7058d0d88e10d97cca9926d9fc06e90a4b692fd99899c10406b1c9`, and `project-knowledge/steward-authorization/current.json` matches that replay exactly.

For role availability, the live R6 implementation defines `steward:default` as the package-provided, protected, always-available default role. No project role-event store is required for that default state; replay from the package initial state yields the available `steward:default` role and a missing projection is rebuildable rather than conflicting.

Therefore `steward:default` is currently registered/available and is the exact role assigned to `semantic_reconciliation`.

### 1.4 Fresh activation evidence

This Stage 3 invocation uses a fresh explicit declaration rather than inheriting activation from a prior chat:

```json
{"context":{"invocation_id":"chatgpt-stage3-a29806386bf4-0ef9faca7d83-20260823T2044-0700","source":"chatgpt-project-chat"},"contract":"reasoning-distiller-role-activation/1","method":"explicit_declaration","role_id":"steward:default"}
```

Canonical activation digest:

```text
sha256:21ebc67efaed7faccaa22cfdfd08feb172b3e5bdb6ec527b8b3cb580bebb863f
```

Applying the exact live R8 validation rules to this artifact and the replayed live role/authorization state yields:

```text
PASS/ACTIVATION_ACCEPTED
scope = semantic_reconciliation
role_id = steward:default
invocation_id = chatgpt-stage3-a29806386bf4-0ef9faca7d83-20260823T2044-0700
activation_digest = sha256:21ebc67efaed7faccaa22cfdfd08feb172b3e5bdb6ec527b8b3cb580bebb863f
```

This activation is used only for this Stage 3 semantic-reconciliation decision. The fact that the same role is separately assigned to `admission` does not activate or invoke admission here.

## 2. Problem being reconciled

P1d and P3 define PEMS semantic-item identity as `(namespace,id)`, with independent `record` and `relation` namespaces. A valid PEMS projection may therefore contain record `shared` and relation `shared` as two distinct semantic items.

The frozen P1b `reasoning-distiller-context-pack/1` knowledge-ledger subject carries only `source_ref` plus optional scalar `semantic_id`. P5 candidate `a8a0592a69b325d411b36bbc97deadee796c3fd7` cannot represent the valid record/relation collision without conflation and rejects it instead. P5 review `0df24253d653725686a616e3cb4ddbd581a4bd13` correctly identified that as a protocol-representation mismatch requiring governed revision of the earlier frozen packaging basis.

Stage 1 recommends preserving immutable `/1` and introducing a side-by-side `/2` packaging family with a structural namespaced PEMS reference. Stage 2 finds that architecture compatible, subject to four required revisions.

## 3. Stage 1 and Stage 2 recommendations

### RPG Engineer recommendation

Accept Stage 1 Alternative D in substance: preserve accepted `/1` bytes, introduce a distinct `/2` profile/request/pack/result family, and replace the scalar semantic-item shortcut in canonical `/2` knowledge provenance with a structured representation of the existing P1d/P3 `(namespace,id)` identity.

### Independent Engineer recommendation

Accept the side-by-side `/2` architecture only after these material revisions:

1. remove canonical public `/1` to `/2` migration from the amendment;
2. explicitly define the version-neutral reuse condition for `reasoning-distiller-context-pack-identity-preimage/1`;
3. keep receipt `/1` shared only as a version-neutral opaque digest receipt, never as a pack-version discriminator;
4. require the new `/2` schema basis to avoid silently inheriting the known mutable PEMS `main` schema identity.

## 4. Issue-by-issue Steward reconciliation

| Stage 2 item | Steward classification | Reconciliation |
|---|---|---|
| Architecture blocker | **Accepted: none** | No blocker exists to immutable `/1` plus side-by-side `/2`. The original P5 representation blocker remains real until the amendment is implemented and proven. |
| R1: remove public `/1` to `/2` migration | **Accepted** | This amendment defines no canonical upgrade adapter. Existing `/1` packs remain `/1`. Canonical `/2` packs are rebuilt from exact governed inputs. Stage 1 SP-08/SP-09 are revised accordingly. |
| R2: explicit identity-preimage `/1` reuse rule | **Accepted** | `reasoning-distiller-context-pack-identity-preimage/1` may be reused by `/2` only while its field set, field meanings, framing, hashing rule, and domain semantics are unchanged. Any change to those properties requires an independently versioned preimage contract. |
| R3: shared receipt `/1` is not a version discriminator | **Accepted** | Receipt `/1` remains shared because it does not interpret pack fields. It cannot establish the referenced pack contract version by itself. This reconciliation does not add P6 lookup/persistence semantics. |
| R4: `/2` must not silently inherit mutable PEMS schema identity | **Accepted** | `/2` schema freeze is gated on an explicit immutable/package-owned PEMS schema resource identity. If no such governed identity is available, the dependency remains an explicit unresolved prerequisite and `/2` runtime-isolated schema closure cannot be claimed. Immutable `/1` bytes remain unchanged. |
| N1: minimum honest version boundary | **Accepted** | Version profile/request/pack/result, successor P1c bytes/digests/toolchain, and pack-builder behavior to `/2`. Continue sharing unchanged failure/source-binding/eligibility/receipt `/1` under the stated constraints. No P1d/P3 version change. |
| N2: prefer `pems_ref` | **Accepted** | The final `/2` field name is `pems_ref`, not `semantic_ref`, because the pair is specifically a PEMS semantic-item reference rather than a universal semantic-reference abstraction. |
| N3: schema filenames are locators, not protocol identity | **Accepted** | Existing `/1` schema files remain byte-identical and are not repointed. New `/2` schema files are added side by side. Dispatch is by explicit contract/schema identity, not filename recency. |
| N4: preserve Stage 1 digest stability classification | **Accepted** | Digest domains remain as already defined. Values whose exact preimages are unchanged may remain stable; profile/request/manifest/pack identity/serialized-pack digests change where their canonical preimages change. No new digest domain is introduced solely for `pems_ref`. |
| O1: add contract-dispatch matrix | **Accepted** | Included below as a normative implementation requirement. |
| O2: assert `/2` never contains both legacy and new semantic identity forms | **Accepted** | Canonical `/2` knowledge semantic subjects contain `pems_ref` and never `semantic_id`. Closed-world validation rejects mixed forms. |
| O3: retain source-only snapshot subject | **Accepted** | Snapshot-level source inclusion remains a distinct closed subject shape containing only `source_ref`. |
| O4: do not invent duplicate-cause semantics | **Accepted** | Existing frozen ordering/set behavior governs duplicate causes. This amendment introduces no new deduplication rule. |

No Stage 2 item is rejected or deferred. R4 is accepted as a mandatory gate whose concrete immutable PEMS resource identity remains to be established before `/2` schema freeze.

## 5. Final reconciled protocol decision

### 5.1 Preserve immutable `/1`

Accepted `/1` schema and contract bytes remain historical immutable contracts. This amendment must not edit those bytes, repoint their files, or publish changed semantics under the same `/1` identities.

### 5.2 Introduce the minimum coherent `/2` family

The new family contains:

```text
reasoning-distiller-context-profile/2
reasoning-distiller-context-pack-request/2
reasoning-distiller-context-pack/2
reasoning-distiller-context-pack-result/2
reasoning-distiller-context-pack-bytes-digests-toolchain/2
reasoning-distiller-context-pack-builder/2
```

The following remain shared `/1` contracts because this amendment does not change their wire semantics:

```text
reasoning-distiller-context-pack-failure/1
reasoning-distiller-context-source-binding/1
reasoning-distiller-context-profile-eligibility/1
reasoning-distiller-context-pack-receipt/1
reasoning-distiller-context-pack-identity-preimage/1
```

The identity-preimage and receipt reuse rules in Sections 5.5 and 5.6 are mandatory conditions of that sharing.

No P1d or P3 semantic contract is versioned by this amendment.

### 5.3 `/2` knowledge-ledger subject

Canonical `/2` knowledge provenance has two closed subject shapes.

Snapshot-level subject:

```json
{
  "source_ref": {"...": "canonical snapshot reference"}
}
```

PEMS semantic-item subject:

```json
{
  "source_ref": {"...": "canonical snapshot reference"},
  "pems_ref": {
    "namespace": "record",
    "id": "shared"
  }
}
```

Normative rules:

- `pems_ref.namespace` is exactly one of `record` or `relation` for this protocol version;
- `pems_ref.id` is the exact opaque PEMS identifier and is never delimiter-encoded;
- `semantic_id` is not a `/2` field;
- `source_ref` remains part of the subject identity;
- snapshot-only subjects remain valid and distinct from PEMS-item subjects;
- malformed, unknown, mixed, or partial subject forms fail closed.

### 5.4 Builder grouping and cause preservation

For `/2`, semantic provenance is grouped by the lossless identity:

```text
(JCS(canonical_snapshot_ref), namespace, id)
```

A record and relation sharing one string ID are distinct subjects. Every expected `(namespace,id)` in the P3 projection must have exact outer-ledger coverage under the applicable cause rules. Multiple distinct deterministic causes for one exact namespaced item are preserved and canonically ordered by the existing frozen rules.

No namespace information is moved into `cause_id`, and no new cause vocabulary is introduced.

### 5.5 Version-neutral identity-preimage reuse

`reasoning-distiller-context-pack-identity-preimage/1` is explicitly version-neutral across the `/1` and `/2` pack families only if all of these remain identical:

1. member set;
2. meaning of every member;
3. canonical serialization/framing of the preimage;
4. hash algorithm and framing rule;
5. domain semantics of the resulting identity.

The `/2` profile/request/manifest/toolchain values already enter the existing preimage through their component digests, so `/2` pack identity changes naturally without renaming the inner preimage contract. If any rule above changes, the preimage contract must version independently before use.

### 5.6 Receipt `/1` sharing

`reasoning-distiller-context-pack-receipt/1` remains shared because it binds opaque request/pack/serialized-pack digest values and optional artifact location without interpreting ledger semantics.

Receipt `/1` alone is not evidence of the referenced pack contract version. Any operation requiring version dispatch must inspect or otherwise possess the referenced pack contract under its own governing protocol. No P6 persistence or receipt-revision work is authorized here.

### 5.7 No canonical public `/1` to `/2` migration

This amendment defines no public canonical adapter that converts accepted `/1` pack provenance into `/2` provenance.

- immutable `/1` packs remain `/1`;
- `/2` packs are rebuilt from the exact governed `/2` profile/request, source bindings, P3 projection, and other required inputs;
- no namespace is inferred from legacy scalar `semantic_id` as a canonical upgrade operation;
- ambiguous legacy provenance is never guessed;
- any future legacy-conversion utility requires a separate reviewed specification bound to proven producer semantics.

Stage 1 pressure cases SP-08 and SP-09 are therefore replaced by:

```text
SP-08: ordinary canonical /1 -> /2 pack upgrade is unsupported; fresh /2 rebuild is required.
SP-09: no legacy scalar semantic_id may be guessed into a namespace by canonical amendment behavior, including ambiguous cases.
```

### 5.8 `/2` PEMS schema-resource basis

Before any `/2` schema family is frozen, the implementation must bind an explicitly governed immutable/package-owned PEMS schema resource identity. It must not copy the known mutable `.../blob/main/backends/pems-cove/pems-v2.schema.json` retrieval identity or mutable `main` `$id` and then describe the resulting basis as immutable/runtime-isolated.

Two outcomes are permitted at this gate:

1. an immutable/package-owned PEMS schema resource identity is separately established and `/2` binds it; or
2. the dependency remains unresolved, `/2` schema freeze stops, and runtime-isolated schema closure is not claimed.

This gate does not edit or reclassify the inherited `/1` runtime-isolation red.

### 5.9 Schema locator and dispatch rule

Existing unversioned `/1` schema files remain byte-identical and are not overwritten or repointed to `/2`. New `/2` schema files are added side by side with distinct contract values and immutable schema identities.

Normative dispatch matrix:

| Profile | Request | Requested pack | Result success pack | Outcome |
|---|---|---|---|---|
| `/1` | `/1` | `/1` | `/1` | existing `/1` path only |
| `/2` | `/2` | `/2` | `/2` | accepted `/2` path after `/2` gates pass |
| `/1` | `/2` | any | any | reject contract mismatch |
| `/2` | `/1` | any | any | reject contract mismatch |
| `/2` | `/2` | `/1` | any | reject contract mismatch |
| `/1` | `/1` | `/2` | any | reject contract mismatch |
| any family | any family | family X | success pack family Y != X | reject contract mismatch |

Readers supporting both families dispatch on explicit top-level contract identity and the bound immutable schema family. They do not validate `/2` bytes as `/1`, reinterpret `/1` scalar provenance as `/2`, or auto-upgrade bytes before identity verification.

### 5.10 Digest and identity consequences

The Stage 1 digest-stability model survives with the R2 clarification:

- raw immutable source byte digests remain stable when source bytes are unchanged;
- canonical-state-binding digest remains stable when its exact preimage is unchanged;
- selected PEMS digest remains stable when the selected PEMS canonical value is unchanged;
- COVE/payload-set digests may remain stable when their exact preimages are unchanged;
- `/2` profile digest changes because profile contract/bindings change;
- `/2` request digest changes because request contract/output binding changes;
- manifest digest changes where versioned canonical manifest inputs change;
- pack identity changes through changed component digests under the shared identity-preimage rule;
- serialized-pack digest changes because `/2` wire bytes change.

No new digest domain is required solely for `pems_ref`.

### 5.11 Eligibility

A `/2` profile is a distinct exact profile artifact. Governed eligibility for `/1` does not imply eligibility for `/2`.

Where eligibility is required, the consumer must provide evidence naming the exact new `/2` `(profile_id, profile_version, raw_sha256)` identity. The packer must not infer that an old eligibility decision transfers to the new profile.

## 6. Approved invariants

The implementation must preserve all of these invariants:

1. outer semantic provenance uses the same `(namespace,id)` identity already frozen by P1d/P3;
2. P1d/P3 semantics and artifacts are not reinterpreted to fit packaging;
3. the exact canonical snapshot reference remains part of outer subject identity;
4. record/relation equal-string IDs remain distinct subjects;
5. distinct deterministic causes are preserved and canonically ordered;
6. closed-world validation rejects unknown, partial, or mixed `/2` subject shapes;
7. arbitrary PEMS IDs remain opaque strings with no namespace-tag codec;
8. accepted `/1` bytes and blob identities remain unchanged;
9. `/1` and `/2` contract families are explicitly distinguishable and cross-version combinations fail closed;
10. digest changes follow exact preimage changes rather than informal version assumptions;
11. `/2` profile eligibility is exact and is not inherited from `/1`;
12. no canonical public `/1` to `/2` migration exists in this amendment;
13. the `/2` schema basis does not silently claim mutable PEMS `main` identity as immutable;
14. the P5 lowercase-SHA blocker remains a separate P5-local remediation;
15. the three inherited P5-review reds remain separately classified unless independently remediated under their own scope;
16. P6, rendering, production integration, canonical mutation, admission, and successor authority operations remain outside this amendment.

## 7. Ordered implementation plan and gates

This Stage 3 decision reconciles the protocol plan. It does not itself perform these implementation steps.

1. **R4 prerequisite resolution**
   - identify or separately establish an immutable/package-owned PEMS schema resource identity suitable for the `/2` schema basis;
   - if it cannot be established under the receiving role's authority, stop and escalate rather than copying the mutable `main` identity.

2. **Pressure-case freeze**
   - materialize Stage 1 SP-01 through SP-07 and SP-10 through SP-14;
   - replace SP-08/SP-09 with the no-canonical-migration cases in Section 5.7;
   - include explicit record/relation same-string-ID coverage and mixed-form rejection.

3. **`/2` schema-family freeze**
   - add side-by-side profile/request/pack/result `/2` schemas;
   - freeze `pems_ref` as the only semantic-item identity form in canonical `/2` knowledge subjects;
   - preserve source-only snapshot subjects;
   - bind the exact immutable PEMS resource identity from Gate 1;
   - mechanically prove accepted `/1` schema blobs are unchanged.

4. **Successor P1c contract freeze**
   - define `reasoning-distiller-context-pack-bytes-digests-toolchain/2` against the exact `/2` schema basis;
   - normatively freeze the identity-preimage `/1` reuse rule;
   - freeze canonical ordering/grouping and exact digest expectations;
   - freeze `/2` builder/toolchain behavior identity.

5. **Profile/request/result and eligibility integration**
   - ensure `/2` profile hard-binds `/2` request/pack/result;
   - ensure `/2` request hard-binds output pack `/2`;
   - ensure `/2` result success hard-binds pack `/2`;
   - preserve shared failure/source-binding/eligibility/receipt `/1` semantics under this reconciliation;
   - require exact `/2` eligibility evidence wherever governed eligibility applies.

6. **Protocol conformance execution**
   - prove cross-version combinations fail closed;
   - prove same-string record/relation IDs produce distinct subjects with preserved causes;
   - prove canonical `/2` output never contains `semantic_id` and never mixes identity forms;
   - prove deterministic bytes across host iteration variation;
   - prove digest stability/churn matches Section 5.10;
   - preserve the known inherited reds as separately classified evidence.

7. **Close the amendment basis before P5 remediation**
   - preserve immutable evidence for the exact `/2` schema and P1c successor basis;
   - independently review that implementation under the repository's normal role/evidence boundaries;
   - do not begin fresh P5 remediation until the governed amendment basis and required conformance evidence are closed.

8. **Stop before P6**
   - even after a later P5 remediation succeeds, P6 does not begin from this Stage 3 decision.

## 8. Definition of done / acceptance criteria

The reconciled amendment is implementation-complete only when all of the following are proven against immutable evidence:

1. accepted `/1` schema blobs are byte-identical to their frozen basis;
2. `/2` profile/request/pack/result identities are distinct and cross-version combinations fail closed;
3. `/2` knowledge provenance carries exact PEMS `{namespace,id}` identity through `pems_ref` plus exact canonical snapshot reference;
4. a record and relation sharing one string ID produce distinct ledger subjects and preserve their own causes;
5. P1d/P3 semantics and artifacts are unchanged;
6. successor P1c `/2` binds the exact `/2` schema basis and freezes the identity-preimage `/1` reuse rule;
7. `/2` builder/toolchain behavior identity is versioned and immutable;
8. receipt `/1` remains opaque/version-neutral and is never used alone for pack-version inference;
9. no public canonical `/1` to `/2` migration adapter is introduced; canonical `/2` is rebuilt from exact governed inputs;
10. new `/2` profiles require eligibility evidence naming their exact new `(profile_id,profile_version,raw_sha256)` identity wherever eligibility is required;
11. `/2` schema freeze binds an explicitly governed immutable/package-owned PEMS resource identity and does not silently reproduce the mutable `main` reference;
12. P5's lowercase-SHA blocker remains separate and unmodified by the protocol amendment;
13. the three inherited P5-review reds remain separately classified unless independently remediated;
14. P6, rendering, production integration, canonical mutation, admission, and successor authority operations remain outside this amendment;
15. the Stage 2 issue classifications in Section 4 are preserved without hidden disagreement or silent deferral.

## 9. Remaining uncertainty and blocked decisions

The architecture itself has no unresolved disagreement after reconciliation.

One implementation prerequisite remains intentionally open: the exact immutable/package-owned PEMS schema resource identity required by R4 has not been selected by Stage 1 or Stage 2. That identity must be independently established under the receiving implementation/governance scope before `/2` schema freeze. Until then, `/2` conformance must not claim runtime-isolated schema closure.

This is a gate, not permission to broaden into PEMS semantic redesign or to edit accepted `/1` schema bytes.

## 10. Steward disposition

**`PROPOSAL_ACCEPTED_WITH_REVISIONS`**

The Stage 1 core architecture survives independent review and Steward reconciliation. The final project-scoped design is immutable `/1` plus a side-by-side `/2` packaging family whose canonical knowledge semantic subject uses `pems_ref {namespace,id}`. All four Stage 2 required revisions are incorporated as normative constraints, with R4 preserved as a pre-schema-freeze prerequisite.

There is no consensus claim beyond the evidence: Stage 2's material amendments changed Stage 1 in the places recorded above. Those changes are accepted explicitly rather than being erased from the review history.

## 11. Exact next action

The next bounded action is a **fresh Reasoning Graph Protocol / implementation Engineer activation for the reconciled protocol-amendment basis only**.

That activation should independently read this Stage 3 artifact and the live implementation contracts, then begin with the R4 immutable PEMS schema-resource prerequisite and the revised pressure-case freeze. It may implement the `/2` protocol basis only within its established authority and evidence boundaries.

It must **not** begin P5 remediation until the amended protocol basis is implemented, independently reviewed, and closed. It must not begin P6, admission, canonical mutation, or any successor operation from this reconciliation.
