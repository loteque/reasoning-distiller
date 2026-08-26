# P5 Selection-Provenance Representation Amendment - Stage 2 Independent Engineer Review/Synthesis

Disposition: **COMPATIBLE_WITH_REQUIRED_REVISIONS**
Method: `proposal-review-synthesis/1`
Repository: `loteque/reasoning-distiller`
Coordination control ref: `main`
Coordination revision independently inspected and re-resolved before this Stage 2 write: `40241e24ecca2dacf0848ee28cf1ddc1410d15f1`
Stage: **Stage 2 independent review/synthesis**
Reviewer scope: **independent Reasoning Graph Protocol Engineer**

Authority posture: this artifact is technical review evidence only. It does not establish registered role identity, Project Steward authorization, accepted RIL activation, reconciliation, admission, canonical standing, implementation approval, or project authority. It does not authorize P5 remediation, P6 persistence, or successor work.

## 1. Review basis and independence

This Stage 2 review independently reconstructed the protocol mismatch from the live coordination contracts and immutable implementation bases before inspecting the complete Stage 1 proposal.

Bound inputs:

- governing plan: commit `0803bcca5343224d6feefa53c2f1b8baf1d4a8cd`, blob `8474d2da42f863f0a190fd80292085176d3f97f0`;
- P1b reviewed schema basis: `cffc2c27da64f052380a1a5a26a42bb7621b0335`;
- P1c accepted remediation basis: `ec5fe4c6c7e8678c3ead0ac629d97d04022b914c`;
- P1d accepted semantic basis: `945ff72ccee87310642ff78c4b4c8e01c46fb551`;
- P1e eligibility basis: `e6e9d318724a2d13e3b820f8208bdb623d61e482`;
- P3 semantic candidate: `197956138e6181ed9f9aae1d6a40b9f5084695a8`;
- P4 semantic base: `c5e265aa2c572b6156c987bfa75e3740c097f2ec`;
- P5 semantic candidate: `a8a0592a69b325d411b36bbc97deadee796c3fd7`;
- P5 independent review: `0df24253d653725686a616e3cb4ddbd581a4bd13`, disposition `P5_INDEPENDENT_REVIEW_CHANGES_REQUIRED`;
- Stage 1 proposal: commit `a29806386bf493e5005b19633876e7035da51460`, blob `6bcd8b148fa2de805100599b7914a1a8f693667d`.

The separate lowercase-SHA P5 blocker remains P5-local and is not reclassified by this protocol review.

## 2. Independently reconstructed problem

The P1b `reasoning-distiller-context-pack/1` schema gives a knowledge-ledger subject a canonical snapshot `source_ref` plus an optional scalar `semantic_id`. The object is closed-world. It has no namespace member.

P1d and P3 use the semantic item key `(namespace,id)`, with distinct `record` and `relation` namespaces. P3 preserves namespace on every `ProjectionCause`. Therefore a record and relation may validly share the same string ID without sharing semantic identity.

P5 consumes those namespaced causes but groups canonical outer-ledger provenance by scalar `semantic_id`. Candidate `a8a0592a...` consequently rejects any projected PEMS object whose record-ID set intersects its relation-ID set. That rejection narrows the valid P1d/P3 domain and cannot be repaired honestly inside the immutable P1b `/1` wire representation.

The version boundary also extends beyond the pack schema. The frozen `/1` profile hard-binds request/pack/result `/1`; the frozen `/1` request hard-binds `output.pack_contract = reasoning-distiller-context-pack/1`; and the frozen `/1` result success form hard-binds pack `/1`. P1c additionally binds its `/1` bytes/digests/toolchain contract to the exact P1b schema blobs and requires a new reviewed basis for an intentional later schema revision.

By contrast, failure `/1`, source-binding `/1`, eligibility `/1`, and receipt `/1` do not structurally depend on the pack wire version. Eligibility binds the exact profile identity tuple rather than the profile contract string. Receipt `/1` is an out-of-band digest receipt and contains no interpretation of ledger subjects.

## 3. Stage 1 verdict

Stage 1 Alternative D is the strongest architecture considered: preserve immutable `/1`, introduce a side-by-side `/2` family, and structurally represent the PEMS item key as a pair rather than encoding namespace into an opaque scalar.

No architectural blocker was found against that direction. The proposal is **compatible with required revisions** below. Those revisions should be incorporated before Stage 3 reconciliation can accept a final amendment.

## 4. Finding classification

### 4.1 Blockers

**No blocker to the side-by-side `/2` architecture itself.**

The original P5 protocol blocker remains real, and P5 remains blocked until a governed amendment is reconciled. This Stage 2 review does not convert the proposal into an approved protocol.

### 4.2 Required amendments

#### R1. Do not make public `/1` to `/2` migration part of this amendment

Stage 1 permits a compatibility adapter to infer a `/2` namespace when a legacy scalar `semantic_id` occurs in exactly one namespace of the referenced PEMS object. That operation is deterministic, but determinism alone is not sufficient to make it a canonical protocol migration.

The frozen `/1` schema does not establish a general namespaced meaning for every accepted scalar `semantic_id`, and there is no accepted P5 `/1` implementation whose emitted scalar provenance creates a compatibility obligation. The motivating collision has no valid P5 `/1` output to migrate in the first place.

The amendment should therefore define **no canonical public `/1` to `/2` migration adapter**. Immutable `/1` packs remain `/1`. New `/2` packs are rebuilt from the exact governed profile/request, source bindings, P3 projection, and other required inputs. Any future legacy-conversion utility must be separately specified, scoped to proven producer semantics, and must not masquerade as identity-preserving migration.

Recast Stage 1 SP-08/SP-09 accordingly: ordinary canonical upgrade is unsupported; ambiguous legacy provenance must never be guessed.

#### R2. Retain `reasoning-distiller-context-pack-identity-preimage/1` only under an explicit version-neutral reuse rule

Stage 1 correctly requires a successor P1c contract such as `reasoning-distiller-context-pack-bytes-digests-toolchain/2`, because P1c `/1` is bound to the exact P1b schema basis.

The inner `reasoning-distiller-context-pack-identity-preimage/1` label does **not** need a version bump solely because the pack wire version changes. Its member set and the meaning of each member remain unchanged, while the `/2` profile, request, manifest, and toolchain changes already enter those member digests and therefore change `pack_identity_sha256`.

However, this reuse must be made normative rather than left as an informal possibility. P1c `/2` must explicitly declare the identity-preimage `/1` sub-contract version-neutral across pack families so long as its field set, field meanings, hash framing, and domain semantics remain unchanged. If any of those change, the preimage contract must version independently.

This separates wire-version evolution from digest-algorithm evolution and avoids a redundant version bump while preserving version honesty.

#### R3. Keep receipt `/1` shared, but freeze that it is version-neutral and not a version discriminator

`reasoning-distiller-context-pack-receipt/1` may remain shared. Its build and persist forms bind request ID, pack identity digest, serialized-pack digest, and optional artifact locator. They do not interpret pack fields or ledger semantics.

The reconciled amendment must state that receipt `/1` **cannot by itself establish the pack contract version**. A consumer needing version dispatch must inspect or otherwise possess the referenced pack contract under its governing operation. This amendment must not add P6 persistence semantics merely to solve that future lookup question.

If a later persistence protocol requires standalone receipts to carry pack contract identity, that is a separate reviewed receipt revision.

#### R4. The new `/2` schema basis must not silently reproduce the known mutable PEMS schema reference

The accepted `/1` pack schema contains the inherited runtime-isolation red in which the PEMS schema `$ref` points at `.../blob/main/backends/pems-cove/pems-v2.schema.json`, and the PEMS schema itself carries that mutable `main` `$id`.

This Stage 2 review does not authorize editing those immutable `/1` bytes or broadening into an unrelated PEMS semantic revision. But a newly frozen `/2` schema family must not silently claim a clean immutable basis while copying the same mutable retrieval identity as though it were immutable.

Before `/2` schema freeze, the reconciled amendment must require one of two explicit outcomes: either a separately governed immutable/package-owned PEMS schema resource identity is available and the `/2` basis binds it, or the inherited dependency remains an explicit unresolved prerequisite and `/2` conformance cannot claim runtime-isolated schema closure. The known `/1` red stays separate.

### 4.3 Recommendations

#### N1. Keep the minimum honest version boundary proposed by Stage 1

The smallest coherent contract boundary is:

- `reasoning-distiller-context-profile/2`;
- `reasoning-distiller-context-pack-request/2`;
- `reasoning-distiller-context-pack/2`;
- `reasoning-distiller-context-pack-result/2`;
- successor P1c bytes/digests/toolchain contract `/2` bound to the exact new schema basis;
- pack-builder behavior contract `/2`.

Continue sharing unchanged:

- context-pack-failure `/1`;
- context-source-binding `/1`;
- context-profile-eligibility `/1`;
- context-pack-receipt `/1` under R3.

No P1d or P3 semantic version change is warranted.

Trying to keep profile, request, or result at `/1` would require mutating a frozen contract that explicitly hard-binds pack `/1`, so it is not a smaller honest boundary.

#### N2. Prefer `pems_ref` over `semantic_ref` for the nested pair

The structured pair is not a generic semantic-reference system. In this amendment its namespaces are exactly PEMS `record` and `relation`, and its correctness is inherited from P1d/P3. Naming the nested field `pems_ref` makes that scope visible and reduces the risk that later consumers treat `{namespace,id}` as a universal cross-encoding semantic identifier.

Recommended `/2` shape:

```json
{
  "source_ref": {"...": "canonical snapshot ref"},
  "pems_ref": {
    "namespace": "record",
    "id": "shared"
  }
}
```

This is a naming recommendation, not a semantic disagreement with Stage 1. Whatever name Stage 3 chooses must be singular, closed-world, and must fully replace legacy scalar `semantic_id` in canonical `/2` output.

#### N3. Treat schema filenames as repository locators, not protocol identity

The contract strings and schema `$id`/immutable basis are normative. Current P1b conformance code and fixtures are coupled to the existing unversioned filenames, so those files should remain byte-identical and new `/2` files should be added side by side. Readers and test registries that support both families should dispatch explicitly by contract rather than by whichever filename happens to be newest.

The rollout should not overwrite `schemas/context-pack.schema.json` or repoint it to `/2`.

#### N4. Preserve the Stage 1 digest stability table

The Stage 1 stable/changed digest classification is coherent under R2. Source byte digests, canonical-state-binding digest, selected PEMS digest, COVE payload-set digest, and payload-set digest may remain stable when their exact preimages are unchanged. Profile/request digests, manifest digest, pack identity, and serialized-pack digest change for `/2` because the corresponding canonical values change.

No new digest domain is required solely for the namespaced PEMS reference.

### 4.4 Optional improvements

1. Add a small contract-dispatch matrix to the final amendment showing accepted profile/request/pack/result tuples and explicit cross-version rejection cases.
2. Add a conformance assertion that canonical `/2` output never contains both `semantic_id` and the new structured PEMS reference.
3. Keep the snapshot-level knowledge-ledger subject as a distinct closed shape so source inclusion remains representable independently of semantic-item provenance.
4. Preserve duplicate-cause behavior only if it is already frozen by the applicable P1c ordering/set rules; do not invent a new deduplication semantic while implementing the namespaced subject.

## 5. Synthesized acceptance criteria

A Stage 3 reconciliation should not authorize fresh P5 implementation until the amendment requires all of the following:

1. accepted `/1` schema blobs remain byte-identical;
2. `/2` profile/request/pack/result contract identities are distinct and cross-version combinations fail closed;
3. `/2` knowledge provenance structurally carries exact PEMS `{namespace,id}` identity plus the exact canonical snapshot reference;
4. a record and relation sharing one string ID produce distinct ledger subjects and preserve their own causes;
5. P1d/P3 semantics and artifacts are not reinterpreted to fit packaging;
6. the successor P1c contract binds the exact `/2` schema basis and explicitly freezes the R2 identity-preimage reuse rule;
7. the `/2` builder/toolchain behavior identity is versioned and immutable;
8. receipt `/1` sharing follows R3 and is not used alone for pack-version inference;
9. no public canonical `/1` to `/2` migration adapter is introduced by this amendment; canonical `/2` output is rebuilt from exact governed inputs;
10. migrated `/2` profiles require eligibility evidence naming their exact new `(profile_id,profile_version,raw_sha256)` identity whenever governed eligibility is required;
11. the `/2` schema basis resolves R4 explicitly rather than silently copying the mutable PEMS `main` reference;
12. P5's lowercase-SHA blocker remains a separate P5-local remediation with its own tests;
13. the three inherited reds from the P5 review remain separately classified unless independently remediated under appropriate scope;
14. P6, rendering, production integration, canonical mutation, authority, activation, reconciliation, and admission remain outside this amendment.

## 6. Stage 2 disposition

**`COMPATIBLE_WITH_REQUIRED_REVISIONS`**

The Stage 1 core recommendation survives independent challenge: immutable `/1` plus a side-by-side `/2` family with a structured namespaced PEMS subject is the smallest robust representation that preserves the already-frozen P1d/P3 identity model.

Required changes are limited but material: remove public migration from the amendment, make identity-preimage `/1` reuse explicitly version-neutral, constrain shared receipt `/1` to opaque digest receipt semantics, and prevent the new `/2` schema basis from silently inheriting the known mutable PEMS schema reference.

This completes Stage 2 review/synthesis only. It is not a Stage 3 reconciliation or protocol decision, does not approve P5 implementation, and does not begin P6.